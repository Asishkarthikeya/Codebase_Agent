"""
Chat endpoint - Ask questions about the indexed codebase
"""
import time
from fastapi import APIRouter, HTTPException
from api.schemas import ChatRequest, ChatResponse, SourceInfo

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Ask a question about the indexed codebase.
    
    Args:
        request: ChatRequest with question and settings
        
    Returns:
        ChatResponse with answer, sources, and metadata
    """
    from api.state import app_state
    
    # Check if codebase is indexed
    if app_state.chat_engine is None:
        raise HTTPException(
            status_code=400,
            detail="No codebase indexed. Use POST /api/index first."
        )
    
    start_time = time.time()
    
    try:
        # Update chat engine settings if needed
        if request.provider.value != app_state.provider:
            # Would need to reinitialize with new provider
            raise HTTPException(
                status_code=400,
                detail=f"Provider mismatch. Current: {app_state.provider}, Requested: {request.provider.value}. Re-index to change provider."
            )
        
        # Get response from chat engine
        result = app_state.chat_engine.query(
            request.question,
            use_agent=request.use_agent
        )
        
        processing_time = time.time() - start_time
        
        # Extract sources from result
        sources = []
        if hasattr(result, 'source_documents'):
            for doc in result.source_documents[:5]:  # Limit to 5 sources
                sources.append(SourceInfo(
                    file_path=doc.metadata.get('file_path', 'unknown'),
                    relevance_score=doc.metadata.get('score', None)
                ))
        
        # Determine mode used
        mode = "agent" if request.use_agent else "linear"
        if hasattr(result, 'mode'):
            mode = result.mode
        
        # Get answer text
        answer = str(result) if isinstance(result, str) else result.get('answer', str(result))
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            mode=mode,
            processing_time=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
