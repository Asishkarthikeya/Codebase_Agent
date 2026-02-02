"""
Incremental indexing methods for the Indexer class.

This module extends the Indexer with methods for efficient incremental indexing
using Merkle trees for change detection.
"""

from pathlib import Path
from typing import Optional
from langchain_core.documents import Document
import logging
import os

logger = logging.getLogger(__name__)


def add_incremental_indexing_methods(indexer_class):
    """
    Add incremental indexing methods to the Indexer class.
    
    This is a helper module to extend the Indexer without modifying the original file too much.
    """
    
    def incremental_index(
        self,
        source_path: str,
        collection_name: str = "codebase",
        vector_db_type: str = "chroma"
    ):
        """
        Perform incremental indexing using Merkle tree change detection.
        
        Only re-indexes files that have changed since the last indexing.
        
        Args:
            source_path: Path to the codebase directory
            collection_name: Name of the vector store collection
            vector_db_type: Type of vector database ('chroma', 'faiss', 'qdrant')
            
        Returns:
            ChangeSet describing what was indexed
        """
        if not self.config.indexing.enable_incremental_indexing:
            logger.info("Incremental indexing disabled, performing full index")
            # Fall back to full indexing
            from code_chatbot.ingestion.universal_ingestor import UniversalIngestor
            ingestor = UniversalIngestor(source_path)
            ingestor.download()
            
            documents = []
            for content, metadata in ingestor.walk():
                documents.append(Document(page_content=content, metadata=metadata))
            
            return self.index_documents(documents, collection_name, vector_db_type)
        
        # Get snapshot path for this collection
        snapshot_dir = Path(self.config.indexing.merkle_snapshot_dir)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / f"{collection_name}_snapshot.json"
        
        # Load previous snapshot
        old_tree = self.merkle_tree.load_snapshot(str(snapshot_path))
        
        # Build current tree
        logger.info(f"Building Merkle tree for {source_path}...")
        new_tree = self.merkle_tree.build_tree(source_path)
        
        # Compare trees to find changes
        changes = self.merkle_tree.compare_trees(old_tree, new_tree)
        
        logger.info(f"Change detection: {changes.summary()}")
        
        if not changes.has_changes():
            logger.info("No changes detected, skipping indexing")
            self.merkle_tree.save_snapshot(new_tree, str(snapshot_path))
            return changes
        
        # Remove embeddings for deleted and modified files
        files_to_remove = changes.deleted + changes.modified
        if files_to_remove:
            logger.info(f"Removing embeddings for {len(files_to_remove)} files...")
            for file_path in files_to_remove:
                self._remove_file_embeddings(file_path, collection_name, vector_db_type)
        
        # Index new and modified files
        files_to_index = changes.added + changes.modified
        if files_to_index:
            logger.info(f"Indexing {len(files_to_index)} files...")
            documents = []
            
            for relative_path in files_to_index:
                full_path = Path(source_path) / relative_path
                
                if not full_path.exists() or not full_path.is_file():
                    continue
                
                # Check file size
                file_size_mb = full_path.stat().st_size / (1024 * 1024)
                if file_size_mb > self.config.indexing.max_file_size_mb:
                    logger.warning(f"Skipping {relative_path}: file too large ({file_size_mb:.1f} MB)")
                    continue
                
                try:
                    content = full_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Apply path obfuscation if enabled
                    display_path = relative_path
                    if self.path_obfuscator:
                        display_path = self.path_obfuscator.obfuscate_path(relative_path)
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={"file_path": display_path, "_original_path": relative_path}
                    ))
                except Exception as e:
                    logger.error(f"Failed to read {relative_path}: {e}")
            
            if documents:
                self.index_documents(documents, collection_name, vector_db_type)
        
        # Save new snapshot
        self.merkle_tree.save_snapshot(new_tree, str(snapshot_path))
        
        logger.info(f"Incremental indexing complete: {changes.summary()}")
        return changes
    
    def _remove_file_embeddings(
        self,
        file_path: str,
        collection_name: str = "codebase",
        vector_db_type: str = "chroma"
    ):
        """
        Remove all embeddings for a specific file.
        
        Args:
            file_path: Relative path to the file
            collection_name: Name of the collection
            vector_db_type: Type of vector database
        """
        from code_chatbot.core.db_connection import get_chroma_client
        
        try:
            if vector_db_type == "chroma":
                chroma_client = get_chroma_client(self.persist_directory)
                collection = chroma_client.get_collection(collection_name)
                
                # Query for documents with this file_path
                results = collection.get(
                    where={"file_path": file_path}
                )
                
                if results and results['ids']:
                    collection.delete(ids=results['ids'])
                    logger.info(f"Removed {len(results['ids'])} chunks for {file_path}")
            
            elif vector_db_type == "faiss":
                logger.warning("FAISS does not support selective deletion, full re-index required")
            
            elif vector_db_type == "qdrant":
                from qdrant_client import QdrantClient
                
                url = os.getenv("QDRANT_URL")
                api_key = os.getenv("QDRANT_API_KEY")
                
                client = QdrantClient(url=url, api_key=api_key)
                
                client.delete(
                    collection_name=collection_name,
                    points_selector={
                        "filter": {
                            "must": [{"key": "file_path", "match": {"value": file_path}}]
                        }
                    }
                )
                logger.info(f"Removed chunks for {file_path} from Qdrant")
        
        except Exception as e:
            logger.error(f"Failed to remove embeddings for {file_path}: {e}")
    
    def get_indexing_stats(self, collection_name: str = "codebase") -> dict:
        """
        Get statistics about the indexed codebase.
        
        Returns:
            Dictionary with stats (total_chunks, unique_files, etc.)
        """
        from code_chatbot.core.db_connection import get_chroma_client
        
        try:
            chroma_client = get_chroma_client(self.persist_directory)
            collection = chroma_client.get_collection(collection_name)
            
            # Get all documents
            results = collection.get()
            
            total_chunks = len(results['ids']) if results and results['ids'] else 0
            
            # Count unique files
            unique_files = set()
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    if 'file_path' in metadata:
                        unique_files.add(metadata['file_path'])
            
            return {
                'total_chunks': total_chunks,
                'unique_files': len(unique_files),
                'collection_name': collection_name,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get indexing stats: {e}")
            return {}
    
    # Add methods to the class
    indexer_class.incremental_index = incremental_index
    indexer_class._remove_file_embeddings = _remove_file_embeddings
    indexer_class.get_indexing_stats = get_indexing_stats
    
    return indexer_class
