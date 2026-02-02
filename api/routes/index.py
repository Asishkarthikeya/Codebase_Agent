"""
Index endpoint - Index a codebase from various sources
"""
import os
import shutil
from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.schemas import IndexRequest, IndexResponse

router = APIRouter()


@router.post("/index", response_model=IndexResponse)
async def index_codebase(request: IndexRequest):
    """
    Index a codebase from GitHub URL, local path, or ZIP file.
    
    Args:
        request: IndexRequest with source and settings
        
    Returns:
        IndexResponse with indexing status and statistics
    """
    from api.state import app_state
    
    try:
        # Import required modules
        from code_chatbot.ingestion.universal_ingestor import process_source
        from code_chatbot.analysis.ast_analysis import ASTGraphBuilder
        from code_chatbot.ingestion.indexer import Indexer
        from code_chatbot.retrieval.graph_rag import GraphEnhancedRetriever
        from code_chatbot.retrieval.rag import ChatEngine
        from code_chatbot.ingestion.chunker import StructuralChunker
        from langchain_community.vectorstores import Chroma, FAISS
        from langchain_community.vectorstores.utils import filter_complex_metadata
        
        # Prepare extraction directory
        extract_to = os.path.join("data", "extracted")
        if os.path.exists(extract_to):
            shutil.rmtree(extract_to)
        
        # Stage 1: Extract & Ingest
        documents, local_path = process_source(request.source, extract_to)
        
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No documents found in the source"
            )
        
        # Stage 2: AST Analysis
        ast_builder = ASTGraphBuilder()
        for doc in documents:
            ast_builder.add_file(doc.metadata['file_path'], doc.page_content)
        
        os.makedirs(local_path, exist_ok=True)
        graph_path = os.path.join(local_path, "ast_graph.graphml")
        ast_builder.save_graph(graph_path)
        graph_nodes = ast_builder.graph.number_of_nodes()
        
        # Stage 3: Chunking
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key and request.provider.value == "gemini":
            raise HTTPException(
                status_code=400,
                detail="GOOGLE_API_KEY not set in environment"
            )
        
        indexer = Indexer(
            provider=request.provider.value,
            api_key=api_key
        )
        indexer.clear_collection(collection_name="codebase")
        
        chunker = StructuralChunker()
        all_chunks = []
        for doc in documents:
            file_chunks = chunker.chunk(doc.page_content, doc.metadata["file_path"])
            all_chunks.extend(file_chunks)
        
        # Clean metadata
        for doc in all_chunks:
            doc.metadata = {k: v for k, v in doc.metadata.items() if v is not None}
        all_chunks = filter_complex_metadata(all_chunks)
        
        # Stage 4: Index into vector store
        vector_db_type = request.vector_db.value
        
        if vector_db_type == "faiss":
            vectordb = FAISS.from_documents(all_chunks, indexer.embedding_function)
            vectordb.save_local(folder_path=indexer.persist_directory, index_name="codebase")
        elif vector_db_type == "qdrant":
            from langchain_qdrant import QdrantVectorStore
            url = os.getenv("QDRANT_URL")
            api_key_qdrant = os.getenv("QDRANT_API_KEY")
            vectordb = QdrantVectorStore.from_documents(
                documents=all_chunks,
                embedding=indexer.embedding_function,
                url=url,
                api_key=api_key_qdrant,
                collection_name="codebase",
                prefer_grpc=True
            )
        else:  # Chroma
            vectordb = Chroma(
                persist_directory=indexer.persist_directory,
                embedding_function=indexer.embedding_function,
                collection_name="codebase"
            )
            vectordb.add_documents(documents=all_chunks)
        
        # Stage 5: Initialize Chat Engine
        base_retriever = indexer.get_retriever(vector_db_type=vector_db_type)
        graph_retriever = GraphEnhancedRetriever(
            base_retriever=base_retriever,
            repo_dir=local_path
        )
        
        repo_files = list(set([doc.metadata['file_path'] for doc in documents]))
        
        chat_engine = ChatEngine(
            retriever=graph_retriever,
            provider=request.provider.value,
            model_name="gemini-2.5-flash" if request.provider.value == "gemini" else "llama-3.3-70b-versatile",
            api_key=api_key,
            repo_files=repo_files,
            repo_name=os.path.basename(request.source),
            use_agent=True,
            repo_dir=local_path
        )
        
        # Update app state
        app_state.chat_engine = chat_engine
        app_state.provider = request.provider.value
        app_state.vector_db = vector_db_type
        app_state.documents_count = len(all_chunks)
        
        return IndexResponse(
            status="success",
            message=f"Successfully indexed {len(documents)} files",
            files_indexed=len(documents),
            chunks_created=len(all_chunks),
            graph_nodes=graph_nodes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(e)}"
        )
