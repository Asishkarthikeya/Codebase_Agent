"""
Code Chatbot - AI-powered codebase assistant.

Core modules:
- rag: Chat engine with RAG
- indexer: Vector database indexing
- chunker: AST-aware code chunking
- merkle_tree: Incremental change detection
- mcp_server/mcp_client: Code search & refactoring tools
- agents/crews: Multi-agent workflows
"""

# Core
from .rag import ChatEngine
from .config import get_default_config

# Indexing
from .indexer import Indexer
from .chunker import CodeChunker

# Tools
from .mcp_client import MCPClient

__all__ = [
    # Core
    'ChatEngine',
    'get_default_config',
    # Indexing
    'Indexer',
    'CodeChunker',
    # Tools
    'MCPClient',
]

__version__ = "2.0.0"
