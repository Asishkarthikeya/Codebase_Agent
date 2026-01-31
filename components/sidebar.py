import streamlit as st
import os
import shutil
from dotenv import load_dotenv

# Load Env
load_dotenv()

def render_sidebar():
    """
    Renders the sidebar configuration panel.
    Returns:
        dict: A dictionary containing the configuration settings:
            - api_key (str)
            - provider (str)
            - gemini_model (str)
            - use_agent (bool)
            - vector_db_type (str)
            - embedding_provider (str)
            - embedding_api_key (str)
    """
    config = {}
    
    with st.sidebar:
        # Logo
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", use_column_width=True)
        
        st.title("🔧 Configuration")
        
        # Provider Selection (Gemini & Groq only as requested)
        provider = st.radio("LLM Provider", ["gemini", "groq"])
        config["provider"] = provider
        
        # Model Selection for Gemini
        gemini_model = None
        if provider == "gemini":
            gemini_model = st.selectbox(
                "Gemini Model",
                [
                    "gemini-2.5-flash",  # This one was working!
                    "gemini-2.0-flash",
                    "gemini-1.5-pro",
                ],
                index=0,  # Default to 2.5 Flash (confirmed working)
                help="""**Gemini 2.5 Flash** (Recommended): Latest, confirmed working
**Gemini 2.0 Flash**: Newer model
**Gemini 1.5 Pro**: More stable for complex tasks"""
            )
            st.caption(f"✨ Using {gemini_model}")
        config["gemini_model"] = gemini_model
        
        # Agentic Mode Toggle
        use_agent = st.checkbox("Enable Agentic Reasoning 🤖", value=True, help="Allows the AI to browse files and reason multiple steps.")
        config["use_agent"] = use_agent
        
        # Determine Env Key Name
        if provider == "gemini":
            env_key_name = "GOOGLE_API_KEY"
        elif provider == "groq":
            env_key_name = "GROQ_API_KEY"
            
        env_key = os.getenv(env_key_name)
        api_key = env_key
        
        if env_key:
            st.success(f"✅ {env_key_name} loaded from environment.")
        else:
            # API Key Input
            api_key_label = f"{provider.capitalize()} API Key"
            api_key_input = st.text_input(api_key_label, type="password")
            if api_key_input:
                api_key = api_key_input
                os.environ[env_key_name] = api_key
        config["api_key"] = api_key
    
        # Vector Database Selection
        vector_db_type = st.selectbox("Vector Database", ["faiss", "chroma", "qdrant"])
        config["vector_db_type"] = vector_db_type
        
        if vector_db_type == "qdrant":
            st.caption("☁️ connect to a hosted Qdrant cluster")
            qdrant_url = st.text_input("Qdrant URL", placeholder="https://xyz.qdrant.io:6333", value=os.getenv("QDRANT_URL", ""))
            qdrant_key = st.text_input("Qdrant API Key", type="password", value=os.getenv("QDRANT_API_KEY", ""))
            
            if qdrant_url:
                os.environ["QDRANT_URL"] = qdrant_url
            if qdrant_key:
                os.environ["QDRANT_API_KEY"] = qdrant_key
    
        # For Groq, we need an embedding provider
        # Use LOCAL embeddings by default - NO RATE LIMITS!
        embedding_provider = "local"  # Use local HuggingFace embeddings
        embedding_api_key = api_key
        
        if provider == "groq":
            st.info(f"ℹ️ {provider.capitalize()} is used for Chat. Using LOCAL embeddings (no rate limits!).")
            embedding_provider = "local"  # Use local embeddings for Groq too
            
            # Check Embedding Key for Gemini (not needed for local)
            emb_env_key = os.getenv("GOOGLE_API_KEY")
            if not emb_env_key and provider != "gemini":
                 embedding_api_key = emb_env_key  # Optional now
            else:
                 embedding_api_key = emb_env_key
                 
        config["embedding_provider"] = embedding_provider
        config["embedding_api_key"] = embedding_api_key
    
        st.divider()
        
        # Ingestion moved to main area
    
        if st.session_state.processed_files:
            st.success(f"✅ Codebase Ready ({provider}) + AST 🧠")
            
            # Show usage statistics if available
            if st.session_state.chat_engine:
                try:
                    from code_chatbot.rate_limiter import get_rate_limiter
                    limiter = get_rate_limiter(provider)
                    stats = limiter.get_usage_stats()
                    
                    st.divider()
                    st.subheader("📊 API Usage")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Requests/min", stats['requests_last_minute'])
                        st.metric("Cache Hits", stats['cache_size'])
                    with col2:
                        st.metric("Total Tokens", f"{stats['total_tokens']:,}")
                        rpm_limit = 15 if provider == "gemini" else 30
                        usage_pct = (stats['requests_last_minute'] / rpm_limit) * 100
                        st.progress(usage_pct / 100, text=f"{usage_pct:.0f}% of limit")
                except Exception as e:
                    pass  # Stats are optional
            
            st.divider()
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
                st.rerun()
            
            if st.button("Reset"):
                # Clear disk data for a true reset
                try:
                    if os.path.exists("chroma_db"):
                        shutil.rmtree("chroma_db")
                    if os.path.exists("data"):
                        shutil.rmtree("data")
                except Exception as e:
                    st.error(f"Error clearing data: {e}")
                    
                st.session_state.processed_files = False
                st.session_state.messages = []
                st.session_state.chat_engine = None
                st.rerun()
                
    return config
