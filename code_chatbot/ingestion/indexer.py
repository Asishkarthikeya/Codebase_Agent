import os
from typing import List, Optional
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from code_chatbot.ingestion.chunker import StructuralChunker
from code_chatbot.ingestion.merkle_tree import MerkleTree, ChangeSet
from code_chatbot.core.path_obfuscator import PathObfuscator
from code_chatbot.core.config import get_config
import shutil
import logging

logger = logging.getLogger(__name__)

from code_chatbot.core.db_connection import (
    get_chroma_client, 
    reset_chroma_clients, 
    set_active_vector_db, 
    get_next_fallback_db,
    VECTOR_DB_FALLBACK_ORDER
)


class Indexer:
    """
    Indexes code files into a Vector Database.
    Now uses StructuralChunker for semantic splitting.
    """
    def __init__(self, persist_directory: str = None, embedding_function=None, provider: str = "gemini", api_key: str = None):
        # Use /tmp for Hugging Face compatibility (they only allow writes to /tmp)
        import tempfile
        self.persist_directory = persist_directory or os.path.join(tempfile.gettempdir(), "vector_db")
        os.makedirs(self.persist_directory, exist_ok=True)
        self.provider = provider
        
        # Load configuration
        self.config = get_config()
        
        # Initialize Structural Chunker
        self.chunker = StructuralChunker(max_tokens=self.config.chunking.max_chunk_tokens)
        
        # Initialize Merkle tree for change detection
        self.merkle_tree = MerkleTree(ignore_patterns=self.config.indexing.ignore_patterns)
        
        # Initialize path obfuscator if enabled
        self.path_obfuscator: Optional[PathObfuscator] = None
        if self.config.privacy.enable_path_obfuscation:
            self.path_obfuscator = PathObfuscator(
                secret_key=self.config.privacy.obfuscation_key,
                mapping_file=self.config.privacy.obfuscation_mapping_file
            )
            logger.info("Path obfuscation enabled")

        # Setup Embeddings - supports Gemini (API) and local HuggingFace
        if embedding_function:
            self.embedding_function = embedding_function
        else:
            if provider == "local" or provider == "huggingface":
                # Use local embeddings - NO RATE LIMITS!
                from langchain_huggingface import HuggingFaceEmbeddings
                self.embedding_function = HuggingFaceEmbeddings(
                    model_name="all-MiniLM-L6-v2",  # Fast & good quality
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info("Using LOCAL embeddings (no rate limits)")
            elif provider == "gemini":
                api_key = api_key or os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("Google API Key is required for Gemini Embeddings")
                self.embedding_function = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-001",
                    google_api_key=api_key
                )
                logger.info("Using Gemini embeddings (API rate limits apply)")
            else:
                raise ValueError(f"Unsupported embedding provider: {provider}. Use 'local', 'huggingface', or 'gemini'.")
                
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

        # Attempt indexing with fallback support
        attempted_db = vector_db_type
        fallback_triggered = False
        
        try:
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
        except Exception as e:
            error_str = str(e).lower()
            is_chroma_error = any(indicator in error_str for indicator in [
                'tenant', 'default_tenant', 'sqlite', 'corrupt', 
                'no such table', 'locked', 'database'
            ])
            
            if is_chroma_error and vector_db_type == "chroma":
                logger.warning(f"Chroma indexing failed: {e}. Falling back to FAISS...")
                fallback_triggered = True
                attempted_db = "faiss"
                # Clear the corrupted chroma first
                reset_chroma_clients()
                vectordb = None  # Will use FAISS path
            else:
                raise
        
        # Batch processing - smaller batches to avoid rate limits
        batch_size = 20  # Reduced for free tier rate limits
        total_chunks = len(all_chunks)
        
        logger.info(f"Indexing {total_chunks} chunks in batches of {batch_size}...")
        
        from tqdm import tqdm
        import time
        
        # FAISS handles batching poorly if we want to save incrementally, so we build a list first for FAISS or use from_documents
        if vector_db_type == "faiss" or (fallback_triggered and attempted_db == "faiss"):
             from langchain_community.vectorstores import FAISS
             # For FAISS, it's faster to just do it all at once or in big batches
             logger.info(f"Indexing with FAISS (fallback={fallback_triggered})...")
             vectordb = FAISS.from_documents(all_chunks, self.embedding_function)
             vectordb.save_local(folder_path=self.persist_directory, index_name=collection_name)
             set_active_vector_db("faiss")
             logger.info(f"Saved FAISS index to {self.persist_directory}/{collection_name}")
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
            # Retry logic for rate limits
            max_retries = 5
            for retry in range(max_retries):
                try:
                    vectordb.add_documents(documents=batch)
                    logger.info(f"Indexed batch {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size}")
                    # Delay to avoid rate limits (free tier is ~15 req/min)
                    time.sleep(4)  # 4 seconds between batches = ~15/min
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    if 'rate' in error_str or '429' in error_str or 'quota' in error_str or 'resource_exhausted' in error_str:
                        wait_time = 30 * (retry + 1)  # 30s, 60s, 90s, 120s, 150s
                        logger.warning(f"Rate limit hit, waiting {wait_time}s... (retry {retry+1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Error indexing batch {i}: {e}")
                        break
                
        
        # PersistentClient auto-persists
        logger.info(f"Indexed {len(all_chunks)} chunks into collection '{collection_name}' at {self.persist_directory}")
        return vectordb

    def get_retriever(self, collection_name: str = "codebase", k: int = 10, vector_db_type: str = "chroma"):
        """Get a retriever for the specified collection with automatic fallback.
        
        When the primary vector database fails, automatically attempts the next
        database in the fallback order (chroma -> faiss).
        
        Args:
            collection_name: Name of the collection to retrieve from
            k: Number of results to return (default 10)
            vector_db_type: Primary vector database type to try
            
        Returns:
            Configured retriever with fallback protection
        """
        logger.info(f"Creating retriever for collection '{collection_name}' from {self.persist_directory}")
        
        # Track attempts for fallback
        attempted_dbs = []
        last_error = None
        current_db = vector_db_type
        
        while current_db and current_db not in attempted_dbs:
            attempted_dbs.append(current_db)
            
            try:
                vector_store = self._create_vector_store(current_db, collection_name)
                
                if vector_store:
                    # Success! Update active DB and return retriever
                    set_active_vector_db(current_db)
                    retriever = vector_store.as_retriever(search_kwargs={"k": k})
                    logger.info(f"Retriever created with k={k} using {current_db}")
                    return retriever
                    
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if this is a recoverable error that warrants fallback
                is_chroma_error = any(indicator in error_str for indicator in [
                    'tenant', 'default_tenant', 'sqlite', 'corrupt', 
                    'no such table', 'locked', 'database'
                ])
                
                if is_chroma_error or 'chroma' in error_str:
                    logger.warning(f"Vector DB '{current_db}' failed: {e}")
                    
                    # Try next fallback
                    next_db = get_next_fallback_db(current_db)
                    if next_db:
                        logger.info(f"Attempting fallback to '{next_db}'...")
                        current_db = next_db
                        continue
                
                # Non-recoverable error
                logger.error(f"Vector DB '{current_db}' failed with non-recoverable error: {e}")
                break
        
        # All fallbacks exhausted
        if last_error:
            raise RuntimeError(
                f"All vector database options failed. Attempted: {attempted_dbs}. "
                f"Last error: {last_error}"
            )
        else:
            raise ValueError(f"No valid vector database available. Attempted: {attempted_dbs}")
    
    def _create_vector_store(self, vector_db_type: str, collection_name: str):
        """Create a vector store instance for the given database type.
        
        Args:
            vector_db_type: Type of vector database (chroma, faiss, qdrant)
            collection_name: Name of the collection
            
        Returns:
            Vector store instance
            
        Raises:
            Exception: If vector store creation fails
        """
        if vector_db_type == "chroma":
            # Use shared client to avoid "different settings" error
            chroma_client = get_chroma_client(self.persist_directory)
            
            # Load existing vector store
            vector_store = Chroma(
                client=chroma_client,
                collection_name=collection_name,
                embedding_function=self.embedding_function,
            )
            
            # Verify the store works by getting count
            try:
                collection = vector_store._collection
                count = collection.count()
                logger.info(f"Collection '{collection_name}' has {count} documents")
                
                if count == 0:
                    logger.warning(f"Chroma collection '{collection_name}' is empty!")
                    
            except Exception as e:
                # Re-raise to trigger fallback
                raise RuntimeError(f"Chroma verification failed: {e}")
                
            return vector_store
                
        elif vector_db_type == "faiss":
            from langchain_community.vectorstores import FAISS
            
            faiss_index_path = os.path.join(self.persist_directory, f"{collection_name}.faiss")
            faiss_pkl_path = os.path.join(self.persist_directory, f"{collection_name}.pkl")
            
            # Check if FAISS index exists
            if not os.path.exists(faiss_index_path) and not os.path.exists(faiss_pkl_path):
                # Try default naming convention
                faiss_index_path = os.path.join(self.persist_directory, "index.faiss")
                faiss_pkl_path = os.path.join(self.persist_directory, "index.pkl")
            
            if not os.path.exists(faiss_index_path):
                logger.warning(f"No FAISS index found at {self.persist_directory}, will need to re-index")
                # We could trigger re-indexing here or raise to try next fallback
                raise FileNotFoundError(f"FAISS index not found at {self.persist_directory}")
            
            vector_store = FAISS.load_local(
                folder_path=self.persist_directory, 
                embeddings=self.embedding_function,
                index_name=collection_name,
                allow_dangerous_deserialization=True
            )
            logger.info(f"Loaded FAISS index from {self.persist_directory}")
            return vector_store
            
        elif vector_db_type == "qdrant":
            from langchain_qdrant import QdrantVectorStore
            
            url = os.getenv("QDRANT_URL")
            api_key = os.getenv("QDRANT_API_KEY")
            
            vector_store = QdrantVectorStore(
                client=None,
                collection_name=collection_name,
                embedding=self.embedding_function,
                url=url,
                api_key=api_key,
            )
            logger.info(f"Connected to Qdrant at {url}")
            return vector_store
        
        else:
            raise ValueError(f"Unsupported Vector DB: {vector_db_type}")
    
    def get_retriever_with_reindex_fallback(
        self, 
        documents: List[Document] = None,
        collection_name: str = "codebase", 
        k: int = 10, 
        vector_db_type: str = "chroma"
    ):
        """Get retriever with automatic re-indexing fallback.
        
        If the primary vector DB fails and fallback also fails to load,
        this method will automatically re-index the documents using
        the fallback database.
        
        Args:
            documents: Documents to re-index if needed (optional)
            collection_name: Collection name
            k: Number of results
            vector_db_type: Primary DB type
            
        Returns:
            Configured retriever
        """
        try:
            return self.get_retriever(collection_name, k, vector_db_type)
        except (RuntimeError, FileNotFoundError) as e:
            if documents:
                logger.warning(f"Retriever creation failed, attempting re-index with fallback DB: {e}")
                
                # Get fallback DB
                fallback_db = get_next_fallback_db(vector_db_type) or "faiss"
                
                # Re-index with fallback
                logger.info(f"Re-indexing {len(documents)} documents with {fallback_db}...")
                self.index_documents(documents, collection_name, fallback_db)
                
                # Try getting retriever again
                return self.get_retriever(collection_name, k, fallback_db)
            else:
                raise

# Add incremental indexing methods to the Indexer class
from code_chatbot.ingestion.incremental_indexing import add_incremental_indexing_methods
Indexer = add_incremental_indexing_methods(Indexer)
