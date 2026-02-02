import logging
from typing import List
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class Reranker:
    """
    Uses a Cross-Encoder to re-rank documents retrieved by the vector store.
    This significantly improves precision by scoring the query against each document directly.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"Loading Reranker model: {model_name}")
        self.model = CrossEncoder(model_name)
    
    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        if not documents:
            return []
            
        # Prepare pairs for scoring: [[query, doc_text], ...]
        pairs = [[query, doc.page_content] for doc in documents]
        
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Attach scores to docs and sort
        scored_docs = []
        for i, doc in enumerate(documents):
            # We can store the score in metadata if needed
            doc.metadata["rerank_score"] = float(scores[i])
            scored_docs.append((doc, scores[i]))
            
        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k
        top_docs = [doc for doc, score in scored_docs[:top_k]]
        return top_docs
