import os
from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from code_chatbot.chunker import StructuralChunker
import shutil
import logging

logger = logging.getLogger(__name__)

# Global ChromaDB client cache to avoid "different settings" error
_chroma_clients = {}

def get_chroma_client(persist_directory: str):
    """Get or create a shared ChromaDB client for a given path."""
    global _chroma_clients
    
    if persist_directory not in _chroma_clients:
        import chromadb
        from chromadb.config import Settings
        
        _chroma_clients[persist_directory] = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    
    return _chroma_clients[persist_directory]


class Indexer:
    """
    Indexes code files into a Vector Database.
    Now uses StructuralChunker for semantic splitting.
    """
    def __init__(self, persist_directory: str = "chroma_db", embedding_function=None, provider: str = "gemini", api_key: str = None):
        self.persist_directory = persist_directory
        self.provider = provider
        
        # Initialize Structural Chunker
        self.chunker = StructuralChunker()

        # Setup Embeddings (only Gemini supported)
        if embedding_function:
            self.embedding_function = embedding_function
        else:
            if provider == "gemini":
                api_key = api_key or os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("Google API Key is required for Gemini Embeddings")
                self.embedding_function = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004",
                    google_api_key=api_key
                )
            else:
                raise ValueError(f"Unsupported embedding provider: {provider}. Only 'gemini' is supported.")
                
    def clear_collection(self, collection_name: str = "codebase"):
        """
        Safely clears a collection from the vector database.
        """
        try:
             client = get_chroma_client(self.persist_directory)
             try:
                 client.delete_collection(collection_name)
                 logger.info(f"Deleted collection '{collection_name}'")
             except ValueError:
                 # Collection doesn't exist
                 pass
        except Exception as e:
            logger.warning(f"Failed to clear collection: {e}")


    def index_documents(self, documents: List[Document], collection_name: str = "codebase", vector_db_type: str = "chroma"):
        """
        Splits documents structurally and generates embeddings.
        Supports 'chroma' and 'faiss'.
        """
        if not documents:
            logger.warning("No documents to index.")
            return

        all_chunks = []
        for doc in documents:
            # chunker.chunk returns List[Document]
            file_chunks = self.chunker.chunk(doc.page_content, doc.metadata["file_path"])
            all_chunks.extend(file_chunks)
            
        if not all_chunks:
             pass

        # Create/Update Vector        # Filter out complex metadata and potential None values that slip through
        from langchain_community.vectorstores.utils import filter_complex_metadata
        
        # Ensure metadata is clean
        for doc in all_chunks:
             # Double check for None values in metadata values and remove them
             doc.metadata = {k:v for k,v in doc.metadata.items() if v is not None}
             
        all_chunks = filter_complex_metadata(all_chunks)

        if vector_db_type == "chroma":
            # Use shared client to avoid "different settings" error
            chroma_client = get_chroma_client(self.persist_directory)
            
            vectordb = Chroma(
                client=chroma_client,
                embedding_function=self.embedding_function,
                collection_name=collection_name
            )
        elif vector_db_type == "faiss":
            from langchain_community.vectorstores import FAISS
            # FAISS is in-memory by default, we'll save it to disk later
            vectordb = None # We build it in the loop
        elif vector_db_type == "qdrant":
             vectordb = None # Built in bulk later
        else:
             raise ValueError(f"Unsupported Vector DB: {vector_db_type}")
        
        # Batch processing
        batch_size = 100
        total_chunks = len(all_chunks)
        
        logger.info(f"Indexing {total_chunks} chunks in batches of {batch_size}...")
        
        from tqdm import tqdm
        import time
        
        # FAISS handles batching poorly if we want to save incrementally, so we build a list first for FAISS or use from_documents
        if vector_db_type == "faiss":
             from langchain_community.vectorstores import FAISS
             # For FAISS, it's faster to just do it all at once or in big batches
             vectordb = FAISS.from_documents(all_chunks, self.embedding_function)
             vectordb.save_local(folder_path=self.persist_directory, index_name=collection_name)
             return vectordb

        elif vector_db_type == "qdrant":
            from langchain_qdrant import QdrantVectorStore
            from qdrant_client import QdrantClient
            
            url = os.getenv("QDRANT_URL")
            api_key = os.getenv("QDRANT_API_KEY")
            
            if not url:
                 # Fallback to local
                 logger.info("No QDRANT_URL found, using local Qdrant memory/disk")
                 location = ":memory:" # or path
            
            vectordb = QdrantVectorStore.from_documents(
                documents=all_chunks,
                embedding=self.embedding_function,
                url=url,
                api_key=api_key,
                collection_name=collection_name,
                prefer_grpc=True
            )
            return vectordb

        # Loop for Chroma (existing logic)
        for i in range(0, total_chunks, batch_size):
            batch = all_chunks[i:i + batch_size]
            try:
                vectordb.add_documents(documents=batch)
                logger.info(f"Indexed batch {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size}")
                # Optional: slight delay to be nice to API
                time.sleep(0.5) 
            except Exception as e:
                logger.error(f"Error indexing batch {i}: {e}")
                # Try one by one if batch fails??
                continue
                
        
        # PersistentClient auto-persists
        logger.info(f"Indexed {len(all_chunks)} chunks into collection '{collection_name}' at {self.persist_directory}")
        return vectordb

    def get_retriever(self, collection_name: str = "codebase", k: int = 10, vector_db_type: str = "chroma"):
        """Get a retriever for the specified collection. Default k=10 for comprehensive results."""
        logger.info(f"Creating retriever for collection '{collection_name}' from {self.persist_directory}")
        
        if vector_db_type == "chroma":
            # Use shared client to avoid "different settings" error
            chroma_client = get_chroma_client(self.persist_directory)
            
            # Load existing vector store
            vector_store = Chroma(
                client=chroma_client,
                collection_name=collection_name,
                embedding_function=self.embedding_function,
            )
            
            # Log collection info
            try:
                collection = vector_store._collection
                count = collection.count()
                logger.info(f"Collection '{collection_name}' has {count} documents")
            except Exception as e:
                logger.warning(f"Could not get collection count: {e}")
                
        elif vector_db_type == "faiss":
            from langchain_community.vectorstores import FAISS
            try:
                vector_store = FAISS.load_local(
                    folder_path=self.persist_directory, 
                    embeddings=self.embedding_function,
                    index_name=collection_name,
                    allow_dangerous_deserialization=True # Codebase trust assumed for local use
                )
                logger.info(f"Loaded FAISS index from {self.persist_directory}")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}")
                # Create empty store if failed? Or raise?
                raise e
        elif vector_db_type == "qdrant":
             from langchain_qdrant import QdrantVectorStore
             
             url = os.getenv("QDRANT_URL")
             api_key = os.getenv("QDRANT_API_KEY")
             
             vector_store = QdrantVectorStore(
                 client=None, # It will create one from url/api_key
                 collection_name=collection_name,
                 embedding=self.embedding_function,
                 url=url,
                 api_key=api_key,
             )
             logger.info(f"Connected to Qdrant at {url}")

        else:
             raise ValueError(f"Unsupported Vector DB: {vector_db_type}")
        
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        logger.info(f"Retriever created with k={k}")
        return retriever
