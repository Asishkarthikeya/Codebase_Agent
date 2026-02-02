import os
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Vector database fallback priority order
VECTOR_DB_FALLBACK_ORDER = ["chroma", "faiss"]

# Track which vector DB is currently active (for automatic fallback)
_active_vector_db = {"type": "chroma", "fallback_count": 0}

def get_active_vector_db() -> str:
    """Get the currently active vector database type."""
    return _active_vector_db["type"]

def set_active_vector_db(db_type: str):
    """Set the active vector database type."""
    _active_vector_db["type"] = db_type
    logger.info(f"Active vector database set to: {db_type}")

def get_next_fallback_db(current_db: str) -> Optional[str]:
    """Get the next fallback vector database in the priority order."""
    try:
        current_idx = VECTOR_DB_FALLBACK_ORDER.index(current_db)
        if current_idx + 1 < len(VECTOR_DB_FALLBACK_ORDER):
            return VECTOR_DB_FALLBACK_ORDER[current_idx + 1]
    except ValueError:
        pass
    return None

# Global ChromaDB client cache to avoid "different settings" error
_chroma_clients = {}

def reset_chroma_clients():
    """Reset all cached ChromaDB clients. Call when database corruption is detected."""
    global _chroma_clients
    _chroma_clients = {}
    logger.info("Reset ChromaDB client cache")

def get_chroma_client(persist_directory: str):
    """Get or create a shared ChromaDB client for a given path.
    
    Includes automatic recovery for common ChromaDB errors:
    - tenant default_tenant connection errors
    - Database corruption
    - Version mismatch issues
    """
    global _chroma_clients
    
    # Ensure directory exists
    os.makedirs(persist_directory, exist_ok=True)
    
    if persist_directory not in _chroma_clients:
        import chromadb
        from chromadb.config import Settings
        
        def create_client():
            """Helper to create a new ChromaDB client."""
            return chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        
        def clear_and_recreate():
            """Clear corrupted database and create fresh client."""
            logger.warning(f"Clearing corrupted ChromaDB at {persist_directory} and recreating...")
            if os.path.exists(persist_directory):
                shutil.rmtree(persist_directory)
            os.makedirs(persist_directory, exist_ok=True)
            return create_client()
        
        def is_corruption_error(error: Exception) -> bool:
            """Check if error indicates database corruption."""
            error_str = str(error).lower()
            corruption_indicators = [
                'tenant',           # "Could not connect to tenant default_tenant"
                'default_tenant',
                'sqlite',           # SQLite database issues
                'database',
                'corrupt',
                'no such table',
                'disk i/o error',
                'malformed',
                'locked',
            ]
            return any(indicator in error_str for indicator in corruption_indicators)
        
        try:
            _chroma_clients[persist_directory] = create_client()
            # Verify the client works by attempting a simple operation
            try:
                _chroma_clients[persist_directory].heartbeat()
            except Exception as verify_error:
                if is_corruption_error(verify_error):
                    logger.error(f"ChromaDB verification failed: {verify_error}")
                    del _chroma_clients[persist_directory]
                    _chroma_clients[persist_directory] = clear_and_recreate()
                else:
                    raise
        except Exception as e:
            logger.error(f"Failed to create ChromaDB client: {e}")
            if is_corruption_error(e):
                _chroma_clients[persist_directory] = clear_and_recreate()
            else:
                # For non-corruption errors, still try to recover
                try:
                    _chroma_clients[persist_directory] = clear_and_recreate()
                except Exception as recovery_error:
                    logger.error(f"Recovery also failed: {recovery_error}")
                    raise recovery_error
    
    return _chroma_clients[persist_directory]
