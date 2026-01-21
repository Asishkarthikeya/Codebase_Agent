"""
Pydantic schemas for FastAPI request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ProviderEnum(str, Enum):
    gemini = "gemini"
    groq = "groq"


class VectorDBEnum(str, Enum):
    chroma = "chroma"
    faiss = "faiss"
    qdrant = "qdrant"


# ============================================================================
# Chat Schemas
# ============================================================================

class ChatRequest(BaseModel):
    """Request body for chat endpoint"""
    question: str = Field(..., description="The question to ask about the codebase")
    use_agent: bool = Field(default=True, description="Use agentic mode with tool calls")
    provider: ProviderEnum = Field(default=ProviderEnum.gemini, description="LLM provider")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What does this codebase do?",
                "use_agent": True,
                "provider": "gemini"
            }
        }


class SourceInfo(BaseModel):
    """Information about a source file used in the response"""
    file_path: str
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    answer: str = Field(..., description="The generated answer")
    sources: List[SourceInfo] = Field(default=[], description="Source files used")
    mode: str = Field(..., description="Mode used: 'agent' or 'linear'")
    processing_time: float = Field(..., description="Time taken in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "This codebase implements a RAG-based code chatbot...",
                "sources": [{"file_path": "code_chatbot/rag.py", "relevance_score": 0.95}],
                "mode": "agent",
                "processing_time": 2.5
            }
        }


# ============================================================================
# Index Schemas
# ============================================================================

class IndexRequest(BaseModel):
    """Request body for index endpoint"""
    source: str = Field(..., description="GitHub URL, local path, or ZIP file path")
    provider: ProviderEnum = Field(default=ProviderEnum.gemini, description="Embedding provider")
    vector_db: VectorDBEnum = Field(default=VectorDBEnum.chroma, description="Vector database type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "https://github.com/user/repo",
                "provider": "gemini",
                "vector_db": "chroma"
            }
        }


class IndexResponse(BaseModel):
    """Response from index endpoint"""
    status: str = Field(..., description="'success' or 'error'")
    message: str = Field(..., description="Status message")
    files_indexed: int = Field(default=0, description="Number of files indexed")
    chunks_created: int = Field(default=0, description="Number of chunks created")
    graph_nodes: int = Field(default=0, description="Number of AST graph nodes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Successfully indexed repository",
                "files_indexed": 45,
                "chunks_created": 1200,
                "graph_nodes": 350
            }
        }


# ============================================================================
# Health Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="'healthy' or 'unhealthy'")
    indexed: bool = Field(..., description="Whether a codebase is currently indexed")
    provider: Optional[str] = Field(None, description="Current LLM provider")
    vector_db: Optional[str] = Field(None, description="Current vector database")
    documents_count: int = Field(default=0, description="Number of indexed documents")
