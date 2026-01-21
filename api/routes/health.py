"""
Health check endpoint
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        dict: Health status and basic system info
    """
    from api.state import app_state
    
    return {
        "status": "healthy",
        "indexed": app_state.chat_engine is not None,
        "provider": app_state.provider,
        "vector_db": app_state.vector_db,
        "documents_count": app_state.documents_count
    }
