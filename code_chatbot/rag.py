from typing import List, Tuple, Any, Optional
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.retrievers import BaseRetriever
# Simplified implementation that works with current langchain version
# We'll implement history-aware retrieval manually
from code_chatbot.reranker import Reranker
from code_chatbot.retriever_wrapper import build_enhanced_retriever
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini models fallback list (tried in order)
GEMINI_FALLBACK_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
]

class ChatEngine:
    def __init__(
        self, 
        retriever: BaseRetriever, 
        model_name: str = "gpt-4o", 
        provider: str = "openai", 
        api_key: str = None,
        repo_name: Optional[str] = None,
        use_agent: bool = True,
        use_multi_query: bool = False,
        use_reranking: bool = True,
        repo_files: Optional[List[str]] = None,
        repo_dir: str = ".",  # New Argument
    ):
        self.base_retriever = retriever
        self.model_name = model_name
        self.provider = provider
        self.api_key = api_key
        self.repo_name = repo_name or "codebase"
        self.use_agent = use_agent
        self.use_multi_query = use_multi_query
        self.use_reranking = use_reranking
        self.repo_files = repo_files
        self.repo_dir = repo_dir
        
        # Track current model index for fallback
        self._gemini_model_index = 0
        
        # Initialize LLM
        self.llm = self._get_llm()
        
        # Initialize conversation history
        self.chat_history = []
        
        # Build enhanced vector retriever 
        self.vector_retriever = build_enhanced_retriever(
            base_retriever=retriever,
            llm=self.llm if use_multi_query else None, # Only for query expansion
            use_multi_query=use_multi_query,
            use_reranking=use_reranking,
        )
        
        # Initialize LLM Retriever if files are available
        self.llm_retriever = None
        if self.repo_files:
            try:
                from code_chatbot.llm_retriever import LLMRetriever
                from langchain.retrievers import EnsembleRetriever
                
                logger.info(f"Initializing LLMRetriever with {len(self.repo_files)} files.")
                self.llm_retriever = LLMRetriever(
                    llm=self.llm,
                    repo_files=self.repo_files,
                    top_k=3
                )
                
                # Combine retrievers
                self.retriever = EnsembleRetriever(
                    retrievers=[self.vector_retriever, self.llm_retriever],
                    weights=[0.6, 0.4]
                )
            except ImportError as e:
                logger.warning(f"Could not load EnsembleRetriever or LLMRetriever: {e}")
                self.retriever = self.vector_retriever
        else:
            self.retriever = self.vector_retriever 
            
        # Initialize Agent Graph if enabled
        self.agent_executor = None
        self.code_analyzer = None
        if self.use_agent:
            try:
                from code_chatbot.agent_workflow import create_agent_graph
                from code_chatbot.ast_analysis import EnhancedCodeAnalyzer
                import os
                
                logger.info(f"Building Agentic Workflow Graph for {self.repo_dir}...")
                
                # Try to load code analyzer from saved graph
                graph_path = os.path.join(self.repo_dir, "ast_graph.graphml") if self.repo_dir else None
                if graph_path and os.path.exists(graph_path):
                    try:
                        import networkx as nx
                        self.code_analyzer = EnhancedCodeAnalyzer()
                        self.code_analyzer.graph = nx.read_graphml(graph_path)
                        logger.info(f"Loaded code analyzer with {self.code_analyzer.graph.number_of_nodes()} nodes")
                    except Exception as e:
                        logger.warning(f"Failed to load code analyzer: {e}")
                
                self.agent_executor = create_agent_graph(
                    self.llm, self.retriever, self.repo_name, 
                    self.repo_dir, self.provider, self.code_analyzer
                )
            except Exception as e:
                logger.error(f"Failed to build Agent Graph: {e}")
                self.use_agent = False

    def _get_llm(self):
        """Initialize the LLM based on provider (only Groq and Gemini supported)."""
        api_key = self.api_key or os.getenv(f"{self.provider.upper()}_API_KEY")
        
        if self.provider == "gemini":
            if not api_key:
                if not os.getenv("GOOGLE_API_KEY"):
                    raise ValueError("Google API Key is required for Gemini")
            
            # Fallback list of Gemini models to try in order
            GEMINI_MODELS_TO_TRY = [
                "gemini-3-flash-preview",
                "gemini-3-pro-preview",
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.5-flash-preview-09-2025",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash-lite-preview-09-2025",
                "gemini-2.0-flash",
                "gemini-2.0-flash-lite",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro",
            ]
            
            # If user specified a model, try it first
            if self.model_name:
                model_name = self.model_name
                if model_name.startswith("models/"):
                    model_name = model_name.replace("models/", "")
                if model_name not in GEMINI_MODELS_TO_TRY:
                    GEMINI_MODELS_TO_TRY.insert(0, model_name)
                else:
                    # Move specified model to front
                    GEMINI_MODELS_TO_TRY.remove(model_name)
                    GEMINI_MODELS_TO_TRY.insert(0, model_name)
            
            # Try each model until one works
            last_error = None
            last_working_model = None
            
            for model_name in GEMINI_MODELS_TO_TRY:
                try:
                    logger.info(f"Attempting to use Gemini model: {model_name}")
                    llm = ChatGoogleGenerativeAI(
                        model=model_name,
                        google_api_key=api_key,
                        temperature=0.2,
                        convert_system_message_to_human=True
                    )
                    # Don't test the model here - it uses up quota!
                    # Just return it and let the actual call determine if it works
                    logger.info(f"Initialized Gemini model: {model_name}")
                    return llm
                except Exception as e:
                    error_str = str(e).lower()
                    # Check for specific error types
                    if "not_found" in error_str or "404" in error_str:
                        logger.warning(f"Model {model_name} not found, trying next...")
                    elif "resource_exhausted" in error_str or "429" in error_str or "quota" in error_str:
                        logger.warning(f"Model {model_name} rate limited, trying next...")
                    else:
                        logger.warning(f"Model {model_name} failed: {str(e)[:100]}")
                    last_error = e
                    continue
            
            # If all models failed, raise the last error
            raise ValueError(f"All Gemini models failed. Last error: {last_error}")
        elif self.provider == "groq":
            if not api_key:
                if not os.getenv("GROQ_API_KEY"):
                    raise ValueError("Groq API Key is required")
            
            return ChatGroq(
                model=self.model_name or "llama-3.3-70b-versatile", 
                groq_api_key=api_key,
                temperature=0.2
            )
        else:
            raise ValueError(f"Provider {self.provider} not supported. Only 'groq' and 'gemini' are supported.")

    def _try_next_gemini_model(self) -> bool:
        """
        Try to switch to the next Gemini model in the fallback list.
        Returns True if a new model was set, False if all models exhausted.
        """
        if self.provider != "gemini":
            return False
        
        self._gemini_model_index += 1
        
        if self._gemini_model_index >= len(GEMINI_FALLBACK_MODELS):
            logger.error("All Gemini models exhausted!")
            return False
        
        next_model = GEMINI_FALLBACK_MODELS[self._gemini_model_index]
        logger.info(f"Switching to next Gemini model: {next_model} (index {self._gemini_model_index})")
        
        api_key = self.api_key or os.getenv("GOOGLE_API_KEY")
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=next_model,
                google_api_key=api_key,
                temperature=0.2,
                convert_system_message_to_human=True
            )
            self.model_name = next_model
            
            # Rebuild agent if using agents
            if self.use_agent:
                try:
                    from code_chatbot.agent_workflow import create_agent_graph
                    self.agent_executor = create_agent_graph(
                        llm=self.llm,
                        retriever=self.vector_retriever,
                        code_analyzer=self.code_analyzer
                    )
                except Exception as e:
                    logger.warning(f"Could not rebuild agent: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to switch to model {next_model}: {e}")
            return self._try_next_gemini_model()  # Recursively try next

    def _build_rag_chain(self):
        """Builds a simplified RAG chain with history-aware retrieval."""
        # For compatibility, we'll use a simpler approach that works with current langchain
        # The history-aware retriever will be implemented in the chat method
        return None  # We'll handle retrieval manually in chat()

    def _contextualize_query(self, question: str, history: List) -> str:
        """Contextualize query based on chat history."""
        if not history:
            return question
        
        # Build context from history
        history_text = ""
        for i in range(0, len(history), 2):
            if i < len(history) and isinstance(history[i], HumanMessage):
                history_text += f"User: {history[i].content}\n"
            if i + 1 < len(history) and isinstance(history[i + 1], AIMessage):
                history_text += f"Assistant: {history[i + 1].content}\n"
        
        # Simple contextualization - just use the question for now
        # In a full implementation, you'd use an LLM to rewrite the query
        return question # Simplified
    
    def chat(self, question: str) -> Tuple[str, List[dict]]:
        """
        Ask a question to the chatbot. 
        Uses Agentic Workflow if enabled, otherwise falls back to Linear RAG.
        """
        try:
            # 1. Agentic Mode
            if self.use_agent and self.agent_executor:
                logger.info("Executing Agentic Workflow...")
                
                # Contextualize with history
                # Use comprehensive system prompt for high-quality answers
                from code_chatbot.prompts import get_prompt_for_provider
                sys_content = get_prompt_for_provider("system_agent", self.provider).format(repo_name=self.repo_name)
                system_msg = SystemMessage(content=sys_content)
                
                # Token Optimization: Only pass last 4 messages (2 turns) to keep context light.
                recent_history = self.chat_history[-4:] if self.chat_history else []
                
                inputs = {
                    "messages": [system_msg] + recent_history + [HumanMessage(content=question)]
                }
                
                # Run the graph
                try:
                    final_state = self.agent_executor.invoke(inputs, config={"recursion_limit": 20})
                    
                    # Extract Answer
                    messages = final_state["messages"]
                    raw_content = messages[-1].content
                    
                    # Handle Gemini's multi-part content
                    if isinstance(raw_content, list):
                        answer = ""
                        for block in raw_content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                answer += block.get('text', '')
                            elif isinstance(block, str):
                                answer += block
                        answer = answer.strip() or str(raw_content)
                    else:
                        answer = raw_content
                    
                    # Update history
                    self.chat_history.append(HumanMessage(content=question))
                    self.chat_history.append(AIMessage(content=answer))
                    if len(self.chat_history) > 20: self.chat_history = self.chat_history[-20:]
                    
                    return answer, []
                    
                except Exception as e:
                    # Fallback for Groq/LLM Tool Errors & Rate Limits
                    error_str = str(e)
                    
                    # Check if it's a rate limit error
                    if any(err in error_str for err in ["429", "RESOURCE_EXHAUSTED", "quota"]):
                        logger.warning(f"Rate limit hit on {self.model_name}: {error_str[:100]}")
                        
                        # Try switching to next Gemini model
                        if self.provider == "gemini" and self._try_next_gemini_model():
                            logger.info(f"Switched to {self.model_name}, retrying...")
                            return self.chat(question)  # Retry with new model
                        else:
                            logger.warning("No more models to try, falling back to Linear RAG")
                            return self._linear_chat(question)
                    
                    # Handle tool use errors
                    if any(err in error_str for err in ["tool_use_failed", "invalid_request_error", "400"]):
                        logger.warning(f"Agent failed ({error_str}), falling back to Linear RAG.")
                        return self._linear_chat(question)
                    raise e 

            # 2. Linear RAG Mode (Fallback)
            return self._linear_chat(question)
            
        except Exception as e:
            # Check for rate limits in outer exception too
            error_str = str(e)
            if any(err in error_str for err in ["429", "RESOURCE_EXHAUSTED", "quota"]):
                if self.provider == "gemini" and self._try_next_gemini_model():
                    logger.info(f"Switched to {self.model_name} after outer error, retrying...")
                    return self.chat(question)
            
            logger.error(f"Error during chat: {e}", exc_info=True)
            return f"Error: {str(e)}", []
    
    def _linear_chat(self, question: str) -> Tuple[str, List[dict]]:
        """Legacy Linear RAG implementation."""
        """
        Ask a question to the chatbot with history-aware retrieval.
        
        Returns:
            Tuple of (answer, sources) where sources is a list of dicts with file_path and url
        """
        try:
            # Contextualize query based on history
            contextualized_query = self._contextualize_query(question, self.chat_history)
            
            # Retrieve relevant documents
            docs = self.retriever.invoke(contextualized_query)
            logger.info(f"Retrieved {len(docs)} documents")
            
            if not docs:
                return "I don't have any information about this codebase. Please make sure the codebase has been indexed properly.", []
            
            # Build context from documents
            context_text = "\n\n".join([
                f"File: {doc.metadata.get('file_path', 'unknown')}\n{doc.page_content[:500]}..."
                for doc in docs[:5]  # Limit to top 5 docs
            ])
            
            # Extract sources
            sources = []
            for doc in docs[:5]:
                file_path = doc.metadata.get("file_path") or doc.metadata.get("source", "unknown")
                sources.append({
                    "file_path": file_path,
                    "url": doc.metadata.get("url", f"file://{file_path}"),
                })
            
            # Build prompt with history - use provider-specific prompt
            from code_chatbot.prompts import get_prompt_for_provider
            base_prompt = get_prompt_for_provider("linear_rag", self.provider)
            qa_system_prompt = base_prompt.format(
                repo_name=self.repo_name,
                context=context_text
            )
            
            # Build messages with history
            messages = [SystemMessage(content=qa_system_prompt)]
            
            # Add chat history
            for msg in self.chat_history[-10:]:  # Last 10 messages for context
                messages.append(msg)
            
            # Add current question
            messages.append(HumanMessage(content=question))
            
            # Get response from LLM
            response_msg = self.llm.invoke(messages)
            answer = response_msg.content
            
            # Update chat history
            self.chat_history.append(HumanMessage(content=question))
            self.chat_history.append(AIMessage(content=answer))
            
            # Keep history manageable (last 20 messages)
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            
            return answer, sources
            
        except Exception as e:
            logger.error(f"Error during chat: {e}", exc_info=True)
            return f"Error: {str(e)}", []
    
    def clear_memory(self):
        """Clear the conversation history."""
        self.chat_history.clear()
