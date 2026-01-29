import os
import networkx as nx
import logging
from typing import List, Optional, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class GraphEnhancedRetriever(BaseRetriever):
    """Wraps a base retriever and augments results using an AST knowledge graph."""
    
    base_retriever: BaseRetriever
    graph: Optional[Any] = None
    repo_dir: str

    def __init__(self, base_retriever: BaseRetriever, repo_dir: str, **kwargs):
        # Initialize Pydantic fields
        super().__init__(base_retriever=base_retriever, repo_dir=repo_dir, **kwargs)
        self.graph = self._load_graph()

    def _load_graph(self):
        graph_path = os.path.join(self.repo_dir, "ast_graph.graphml")
        if os.path.exists(graph_path):
            try:
                logger.info(f"Loading AST Graph from {graph_path}")
                return nx.read_graphml(graph_path)
            except Exception as e:
                logger.error(f"Failed to load AST graph: {e}")
        else:
            logger.warning(f"No AST graph found at {graph_path}")
        return None

    def _rerank_by_file_type(self, docs: List[Document]) -> List[Document]:
        """Rerank documents to prioritize source code over config/text files."""
        
        # Priority weights: higher = more important
        def get_priority(doc: Document) -> int:
            file_path = doc.metadata.get("file_path", "").lower()
            
            # Highest priority: Main entry points
            main_files = ["main.py", "app.py", "index.js", "index.ts", "server.py", "api.py"]
            if any(file_path.endswith(f) for f in main_files):
                return 100
            
            # High priority: Source code files
            code_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".cpp", ".c"]
            if any(file_path.endswith(ext) for ext in code_extensions):
                return 80
            
            # Medium priority: Config files (still useful)
            config_extensions = [".json", ".yaml", ".yml", ".toml"]
            if any(file_path.endswith(ext) for ext in config_extensions):
                return 50
            
            # Lower priority: Text/doc files (often too generic)
            text_extensions = [".txt", ".md", ".rst"]
            if any(file_path.endswith(ext) for ext in text_extensions):
                return 30
            
            # Default
            return 40
        
        # Sort by priority (descending), keeping relative order for same priority
        ranked = sorted(docs, key=lambda d: get_priority(d), reverse=True)
        logger.info(f"Reranked docs: top files are {[d.metadata.get('file_path', '?').split('/')[-1] for d in ranked[:3]]}")
        return ranked

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        # 1. Standard Retrieval
        logger.info(f"GraphEnhancedRetriever: Querying base retriever with: '{query}'")
        docs = self.base_retriever.invoke(query)
        logger.info(f"GraphEnhancedRetriever: Base retriever returned {len(docs)} documents")
        
        # 2. Rerank: Prioritize source code over config/text files
        docs = self._rerank_by_file_type(docs)
        
        if not self.graph:
            logger.warning("No AST graph available for enhancement")
            return docs

        # 2. Graph Expansion
        augmented_docs = list(docs)
        seen_files = {d.metadata.get("file_path") for d in docs}
        
        # We also want to see what files are already in the docs to avoid duplicating content
        # But here we are looking for RELATED files that might not be in the vector search results.

        for doc in docs:
            file_path = doc.metadata.get("file_path")
            if not file_path: continue
            
            # Normalize path if needed (relative vs absolute)
            # The graph was built with paths relative to extracting location or absolute? 
            # We need to ensure consistency. 
            # In ingestor we use: rel_path for source, but file_path for absolute.
            # In ast_analysis we used file_path passed to add_file. 
            # We need to verify how we call add_file in app.py.
            
            # Let's try to find the node in the graph
            target_node = None
            if file_path in self.graph:
                target_node = file_path
            else:
                # Try checking if just filename match
                # Or try absolute path match (depends on how we built the graph)
                pass

            if target_node and target_node in self.graph:
                neighbors = list(self.graph.neighbors(target_node))
                for neighbor in neighbors:
                    # Neighbor could be a file or a symbol (file::symbol)
                    if "::" in neighbor:
                        neighbor_file = neighbor.split("::")[0]
                    else:
                        neighbor_file = neighbor
                    
                    # Skip if we've already seen this file
                    if neighbor_file in seen_files:
                        continue
                    
                    # Check if file exists (handle both relative and absolute paths)
                    if os.path.exists(neighbor_file):
                        try:
                            # Limit expansion to small files to avoid context overflow
                            if os.path.getsize(neighbor_file) < 20000:  # 20KB limit
                                with open(neighbor_file, "r", errors='ignore') as f:
                                    content = f.read()
                                
                                # Get relationship type from edge
                                edge_data = self.graph.get_edge_data(target_node, neighbor, {})
                                relation = edge_data.get("relation", "related") if edge_data else "related"
                                
                                new_doc = Document(
                                    page_content=f"--- Graph Context ({relation} from {os.path.basename(file_path)}) ---\n{content}",
                                    metadata={
                                        "file_path": neighbor_file, 
                                        "source": "ast_graph",
                                        "relation": relation,
                                        "related_to": file_path
                                    }
                                )
                                augmented_docs.append(new_doc)
                                seen_files.add(neighbor_file)
                                logger.debug(f"Added graph-related file: {neighbor_file} (relation: {relation})")
                        except Exception as e:
                            logger.warning(f"Failed to add graph-related file {neighbor_file}: {e}")
        
        return augmented_docs
