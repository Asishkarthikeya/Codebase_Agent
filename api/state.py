"""
Application state management for FastAPI
Stores the chat engine and configuration between requests
"""
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class AppState:
    """Global application state"""
    chat_engine: Optional[object] = None
    provider: Optional[str] = None
    vector_db: Optional[str] = None
    documents_count: int = 0
    repo_name: Optional[str] = None


# Global state instance
app_state = AppState()
