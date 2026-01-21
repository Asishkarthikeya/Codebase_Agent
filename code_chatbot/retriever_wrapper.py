"""Wrapper retriever that adds reranking and multi-query support."""

import logging
from typing import List, Optional, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from code_chatbot.reranker import Reranker

# Try to import MultiQueryRetriever - may not be available in all versions
try:
    from langchain.retrievers.multi_query import MultiQueryRetriever
except ImportError:
    try:
        from langchain_community.retrievers import MultiQueryRetriever
    except ImportError:
        MultiQueryRetriever = None  # type: ignore

logger = logging.getLogger(__name__)


class RerankingRetriever(BaseRetriever):
    """Wraps a base retriever and applies reranking to results."""
    
    base_retriever: BaseRetriever
    reranker: Any
    top_k: int = 5

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, base_retriever: BaseRetriever, reranker: Reranker, top_k: int = 5):
        super().__init__(base_retriever=base_retriever, reranker=reranker, top_k=top_k)
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Retrieve documents and rerank them."""
        # Get documents from base retriever
        docs = self.base_retriever.invoke(query)
        logger.info(f"Base retriever returned {len(docs)} documents")
        
        if not docs:
            return []
        
        # Rerank
        reranked_docs = self.reranker.rerank(query, docs, top_k=self.top_k)
        logger.info(f"Reranked to {len(reranked_docs)} top documents")
        
        return reranked_docs


def build_enhanced_retriever(
    base_retriever: BaseRetriever,
    llm=None,
    use_multi_query: bool = False,
    use_reranking: bool = True,
    rerank_top_k: int = 5,
) -> BaseRetriever:
    """
    Builds an enhanced retriever with optional multi-query expansion and reranking.
    
    Args:
        base_retriever: The base retriever (e.g., from vector store)
        llm: LLM for multi-query expansion (required if use_multi_query=True)
        use_multi_query: Whether to use multi-query retriever for query expansion
        use_reranking: Whether to apply reranking
        rerank_top_k: Number of top documents to return after reranking
    """
    retriever = base_retriever
    
    # Apply multi-query expansion if requested
    if use_multi_query:
        if MultiQueryRetriever is None:
            logger.warning("MultiQueryRetriever not available, skipping multi-query expansion")
        elif not llm:
            logger.warning("Multi-query retriever requires an LLM, skipping multi-query expansion")
        else:
            retriever = MultiQueryRetriever.from_llm(
                retriever=retriever,
                llm=llm
            )
            logger.info("Applied multi-query retriever for query expansion")
    
    # Apply reranking if requested
    if use_reranking:
        reranker = Reranker()
        retriever = RerankingRetriever(
            base_retriever=retriever,
            reranker=reranker,
            top_k=rerank_top_k
        )
        logger.info("Applied reranking to retriever")
    
    return retriever

