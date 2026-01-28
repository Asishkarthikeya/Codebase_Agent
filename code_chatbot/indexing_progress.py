"""
Optimized indexing with progress tracking for Streamlit UI
"""

import os
import time
import shutil
import logging
from typing import List, Tuple
from langchain_core.documents import Document
import streamlit as st

logger = logging.getLogger(__name__)

def index_with_progress(
    source_input: str,
    source_type: str,
    provider: str,
    embedding_provider: str,
    embedding_api_key: str,
    vector_db_type: str,
    use_agent: bool,
    api_key: str,
    gemini_model: str = None
) -> Tuple[object, bool]:
    """
    Index a codebase with detailed progress tracking.
    Returns (chat_engine, success)
    """
    from code_chatbot.universal_ingestor import process_source
    from code_chatbot.ast_analysis import ASTGraphBuilder
    from code_chatbot.indexer import Indexer
    from code_chatbot.graph_rag import GraphEnhancedRetriever
    from code_chatbot.rag import ChatEngine
    from code_chatbot.chunker import StructuralChunker
    from langchain_community.vectorstores import Chroma, FAISS
    from langchain_community.vectorstores.utils import filter_complex_metadata
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Stage 1: Extract & Ingest (0-20%)
        status_text.text("📦 Stage 1/4: Extracting and ingesting files...")
        progress_bar.progress(0.05)
        
        extract_to = os.path.join("data", "extracted")
        
        if os.path.exists(extract_to):
            status_text.text("🧹 Cleaning previous data...")
            shutil.rmtree(extract_to)
        
        progress_bar.progress(0.10)
        
        documents, local_path = process_source(source_input, extract_to)
        progress_bar.progress(0.20)
        status_text.text(f"✅ Stage 1 Complete: Ingested {len(documents)} files")
        
        # Stage 2: AST Analysis (20-40%)
        status_text.text("🧠 Stage 2/4: Building AST Knowledge Graph...")
        progress_bar.progress(0.25)
        
        ast_builder = ASTGraphBuilder()
        total_docs = len(documents)
        
        for idx, doc in enumerate(documents):
            if idx % 10 == 0:
                progress = 0.25 + (0.15 * (idx / total_docs))
                progress_bar.progress(progress)
                status_text.text(f"🧠 Stage 2/4: Analyzing file {idx+1}/{total_docs}...")
            
            ast_builder.add_file(doc.metadata['file_path'], doc.page_content)
        
        os.makedirs(local_path, exist_ok=True)
        graph_path = os.path.join(local_path, "ast_graph.graphml")
        ast_builder.save_graph(graph_path)
        
        progress_bar.progress(0.40)
        status_text.text(f"✅ Stage 2 Complete: Graph with {ast_builder.graph.number_of_nodes()} nodes")
        
        # Stage 3: Chunking (40-50%)
        status_text.text("✂️ Stage 3/4: Chunking documents...")
        progress_bar.progress(0.42)
        
        indexer = Indexer(
            provider=embedding_provider, 
            api_key=embedding_api_key
        )
        
        indexer.clear_collection(collection_name="codebase")
        progress_bar.progress(0.45)
        
        chunker = StructuralChunker()
        all_chunks = []
        
        for idx, doc in enumerate(documents):
            if idx % 5 == 0:
                progress = 0.45 + (0.05 * (idx / total_docs))
                progress_bar.progress(progress)
                status_text.text(f"✂️ Stage 3/4: Chunking file {idx+1}/{total_docs}...")
            
            file_chunks = chunker.chunk(doc.page_content, doc.metadata["file_path"])
            all_chunks.extend(file_chunks)
        
        progress_bar.progress(0.50)
        status_text.text(f"✅ Stage 3 Complete: {len(all_chunks)} chunks from {len(documents)} files")
        
        # Stage 4: Generate Embeddings & Index (50-100%)
        status_text.text(f"🔮 Stage 4/4: Generating embeddings for {len(all_chunks)} chunks...")
        if len(all_chunks) > 500:
            status_text.text("⚠️ Large codebase detected. This may take 2-5 minutes...")
        progress_bar.progress(0.55)
        
        # Clean metadata
        for doc in all_chunks:
            doc.metadata = {k:v for k,v in doc.metadata.items() if v is not None}
        all_chunks = filter_complex_metadata(all_chunks)
        
        # Index with progress
        batch_size = 100
        total_chunks = len(all_chunks)
        
        if vector_db_type == "faiss":
            status_text.text(f"🔮 Generating {total_chunks} embeddings (FAISS - one batch)...")
            vectordb = FAISS.from_documents(all_chunks, indexer.embedding_function)
            vectordb.save_local(folder_path=indexer.persist_directory, index_name="codebase")
            progress_bar.progress(1.0)
            
        elif vector_db_type == "qdrant":
            from langchain_qdrant import QdrantVectorStore
            status_text.text(f"🔮 Generating {total_chunks} embeddings (Qdrant)...")
            
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
            progress_bar.progress(1.0)
            
        else:  # Chroma
            from code_chatbot.indexer import get_chroma_client, reset_chroma_clients
            
            # Reset client cache to avoid stale/corrupt connections
            reset_chroma_clients()
            chroma_client = get_chroma_client(indexer.persist_directory)
            
            vectordb = Chroma(
                client=chroma_client,
                embedding_function=indexer.embedding_function,
                collection_name="codebase"
            )
            
            for i in range(0, total_chunks, batch_size):
                batch = all_chunks[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_chunks + batch_size - 1) // batch_size
                
                progress = 0.55 + (0.45 * (i / total_chunks))
                progress_bar.progress(progress)
                status_text.text(f"🔮 Batch {batch_num}/{total_batches} ({i+batch_size}/{total_chunks} chunks)")
                
                # Retry logic for rate limits
                max_retries = 3
                retry_count = 0
                success = False
                
                while retry_count < max_retries and not success:
                    try:
                        vectordb.add_documents(documents=batch)
                        time.sleep(0.2)  # Rate limit protection
                        success = True
                    except Exception as e:
                        error_msg = str(e).lower()
                        
                        # Check if it's a rate limit error
                        if "rate" in error_msg or "quota" in error_msg or "429" in error_msg or "resource_exhausted" in error_msg:
                            retry_count += 1
                            if retry_count < max_retries:
                                wait_time = 30 * retry_count  # 30s, 60s, 90s
                                status_text.text(f"⚠️ Rate limit hit. Waiting {wait_time}s before retry {retry_count}/{max_retries}...")
                                st.warning(f"⏰ Embedding API rate limit. Pausing {wait_time}s... (Retry {retry_count}/{max_retries})")
                                
                                # Show countdown
                                for remaining in range(wait_time, 0, -5):
                                    status_text.text(f"⏰ Waiting {remaining}s for rate limit to reset...")
                                    time.sleep(5)
                                
                                status_text.text(f"🔄 Retrying batch {batch_num}/{total_batches}...")
                            else:
                                st.error(f"❌ Failed after {max_retries} retries. Wait 5-10 minutes and try again.")
                                raise Exception(f"Rate limit exceeded after {max_retries} retries. Please wait and try again.")
                        else:
                            # Not a rate limit error, just warn and continue
                            st.warning(f"⚠️ Batch {batch_num} error: {str(e)[:50]}...")
                            break  # Skip this batch and continue
            
            # PersistentClient auto-persists, no need to call vectordb.persist()
            progress_bar.progress(1.0)
        
        status_text.text(f"✅ Stage 4 Complete: Indexed {len(all_chunks)} chunks!")
        
        # Stage 5: Initialize Chat Engine
        status_text.text("🚀 Initializing chat engine...")
        
        base_retriever = indexer.get_retriever(vector_db_type=vector_db_type)
        
        graph_retriever = GraphEnhancedRetriever(
            base_retriever=base_retriever,
            repo_dir=local_path 
        )
        
        repo_files = list(set([doc.metadata['file_path'] for doc in documents]))
        
        # Use selected model or fallback to defaults
        model_name = None
        if provider == "gemini": 
            model_name = gemini_model if gemini_model else "gemini-2.0-flash-exp"
        elif provider == "groq": 
            model_name = "llama-3.3-70b-versatile"
        
        chat_engine = ChatEngine(
            retriever=graph_retriever,
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            repo_files=repo_files,
            repo_name=os.path.basename(source_input) if source_input else "Codebase",
            use_agent=use_agent,
            repo_dir=local_path
        )
        
        # Final success
        st.success(f"""
        🎉 **Indexing Complete!** 
        - Files: {len(documents)}
        - Chunks: {len(all_chunks)}
        - Graph Nodes: {ast_builder.graph.number_of_nodes()}
        - Ready to chat!
        """)
        
        progress_bar.empty()
        status_text.empty()
        
        return chat_engine, True
        
    except Exception as e:
        st.error(f"❌ Error during indexing: {e}")
        logger.error(f"Indexing failed: {e}", exc_info=True)
        progress_bar.empty()
        status_text.empty()
        return None, False
