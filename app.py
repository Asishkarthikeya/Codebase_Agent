import streamlit as st
import os
import shutil
import time
from code_chatbot.universal_ingestor import process_source
from code_chatbot.indexer import Indexer
from code_chatbot.rag import ChatEngine
from code_chatbot.ast_analysis import ASTGraphBuilder
from code_chatbot.graph_rag import GraphEnhancedRetriever
import logging
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Basic Setup
st.set_page_config(page_title="Code Chatbot", page_icon="💻", layout="wide")
logging.basicConfig(level=logging.INFO)

# --- Custom CSS for Premium Slate UI ---
import base64
def get_base64_logo():
    try:
        with open("assets/logo.png", "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

logo_b64 = get_base64_logo()

css = """
<style>
    /* -------------------------------------------------------------------------- */
    /*                               CORE ANIMATIONS                              */
    /* -------------------------------------------------------------------------- */
    @keyframes gradient-xy {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* -------------------------------------------------------------------------- */
    /*                            GLOBAL THEME ENGINE                             */
    /* -------------------------------------------------------------------------- */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --primary-glow: 56, 189, 248; /* Sky Blue */
        --secondary-glow: 139, 92, 246; /* Violet */
        --bg-deep: #050608;
        --glass-border: rgba(255, 255, 255, 0.08);
        --glass-bg: rgba(15, 23, 42, 0.6);
    }

    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(13, 17, 28, 1) 0%, rgba(5, 6, 8, 1) 90%);
        font-family: 'Outfit', sans-serif;
    }

    /* BACKGROUND WATERMARK */
    .stApp::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 70vh; /* Slightly smaller to fit nicely */
        height: 70vh;
        background-image: url("data:image/png;base64,LOGO_BASE64_PLACEHOLDER");
        background-position: center;
        background-repeat: no-repeat;
        background-size: contain;
        opacity: 0.08; /* Subtle but visible color */
        pointer-events: none;
        z-index: 0;
        border-radius: 50%; /* Force Circular Shape */
    }
    
    /* Sidebar Logo - Standard Shape */
    [data-testid="stSidebar"] img {
        border-radius: 12px; /* Slight rounded corners for better aesthetics, but not circular */
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.3); /* Neon Glow */
        border: 1px solid rgba(56, 189, 248, 0.5);
    }
    
    /* Global Text Override */
    p, div, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #E2E8F0 !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }

    /* -------------------------------------------------------------------------- */
    /*                                   SIDEBAR                                  */
    /* -------------------------------------------------------------------------- */
    section[data-testid="stSidebar"] {
        background: rgba(11, 12, 16, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid var(--glass-border);
        box-shadow: 5px 0 30px rgba(0,0,0,0.5);
    }
    
    section[data-testid="stSidebar"] h1 {
        background: linear-gradient(to right, #38BDF8, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2rem !important;
        padding-bottom: 0.5rem;
    }

    /* -------------------------------------------------------------------------- */
    /*                                INPUTS & FORMS                              */
    /* -------------------------------------------------------------------------- */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
        background-color: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid var(--glass-border) !important;
        color: #F8FAFC !important;
        border-radius: 12px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 15px rgba(var(--primary-glow), 0.3);
        transform: translateY(-1px);
    }

    /* -------------------------------------------------------------------------- */
    /*                                MEDIA UPLOADS                               */
    /* -------------------------------------------------------------------------- */
    [data-testid="stFileUploader"] {
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px dashed var(--glass-border);
        border-radius: 12px;
        padding: 20px;
    }
    
    /* FORCE TEXT COLOR FOR FILE UPLOADER */
    [data-testid="stFileUploader"] section > div, 
    [data-testid="stFileUploader"] section > div > span,
    [data-testid="stFileUploader"] section > div > small,
    [data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] p {
        color: #E2E8F0 !important; /* Bright Slate */
        opacity: 1 !important;
        -webkit-text-fill-color: #E2E8F0 !important;
    }

    [data-testid="stFileUploader"] button {
        background: rgba(56, 189, 248, 0.2);
        color: #38BDF8 !important;
        border: 1px solid #38BDF8;
    }

    /* -------------------------------------------------------------------------- */
    /*                             DROPDOWN & SELECT                              */
    /* -------------------------------------------------------------------------- */
    
    /* 1. The Box Itself */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1E293B !important; /* Solid Slate-800 for contrast */
        border: 1px solid #475569 !important;
        color: white !important;
    }

    /* 2. The Text INSIDE the Box (Critical Fix) */
    .stSelectbox div[data-baseweb="select"] div[data-testid="stMarkdownContainer"] > p {
        color: #F8FAFC !important; /* White */
        font-weight: 500 !important;
    }
    
    /* 3. The Dropdown Menu (Popup) */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] {
        background-color: #0F172A !important;
        border: 1px solid #334155 !important;
    }
    
    /* 4. Options in the Menu */
    li[data-baseweb="option"], div[data-baseweb="option"] {
        color: #CBD5E1 !important; /* Light Slate */
    }
    
    /* 5. Start/Icons in Menu */
    li[data-baseweb="option"] *, div[data-baseweb="option"] * {
        color: #CBD5E1 !important; 
    }

    /* 6. Selected/Hovered Option */
    li[data-baseweb="option"][aria-selected="true"],
    li[data-baseweb="option"]:hover,
    div[data-baseweb="option"]:hover {
        background-color: #38BDF8 !important;
        color: white !important;
    }
    
    /* 7. SVG Arrow Icon */
    .stSelectbox svg {
        fill: #94A3B8 !important;
    }

    /* -------------------------------------------------------------------------- */
    /*                                   BUTTONS                                  */
    /* -------------------------------------------------------------------------- */
    .stButton button {
        background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(14, 165, 233, 0.3);
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.5);
    }
    .stButton button:active {
        transform: translateY(0);
    }

    /* -------------------------------------------------------------------------- */
    /*                                CHAT BUBBLES                                */
    /* -------------------------------------------------------------------------- */
    .stChatMessage {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        animation: fadeInUp 0.4s ease-out forwards;
    }
    
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        border-left: 3px solid #38BDF8;
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.05) 0%, rgba(15, 23, 42, 0.6) 100%);
    }
    
    /* -------------------------------------------------------------------------- */
    /*                                CODE & CHIPS                                */
    /* -------------------------------------------------------------------------- */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        background: #0B0E14 !important;
        border: 1px solid #1E293B;
        border-radius: 6px;
        color: #7DD3FC !important;
    }
    
    /* Source Chips with Glow */
    .source-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    
    .source-chip {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.8rem;
        color: #94A3B8;
        display: flex;
        align-items: center;
        transition: all 0.3s ease;
        cursor: pointer;
        backdrop-filter: blur(5px);
    }
    
    .source-chip:hover {
        background: rgba(56, 189, 248, 0.15);
        border-color: #38BDF8;
        color: #38BDF8;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
        transform: translateY(-1px);
    }
    
    .source-icon {
        margin-right: 8px;
        opacity: 0.7;
    }
    
    /* Hiding Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
"""

st.markdown(css.replace("LOGO_BASE64_PLACEHOLDER", logo_b64), unsafe_allow_html=True)

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None
if "processed_files" not in st.session_state:
    st.session_state.processed_files = False

# Sidebar
with st.sidebar:
    # Logo
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_column_width=True)
    
    st.title("🔧 Configuration")
    
    # Provider Selection (Gemini & Groq only as requested)
    provider = st.radio("LLM Provider", ["gemini", "groq"])
    
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
    
    # Agentic Mode Toggle
    use_agent = st.checkbox("Enable Agentic Reasoning 🤖", value=True, help="Allows the AI to browse files and reason multiple steps.")
    
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

    # Vector Database Selection
    vector_db_type = st.selectbox("Vector Database", ["faiss", "chroma", "qdrant"])
    
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

    st.divider()
    
    # Ingestion Section
    st.header("Import Codebase")
    source_type = st.radio("Source Type", ["ZIP File", "GitHub Repository", "Web Documentation"])
    
    source_input = None
    if source_type == "ZIP File":
        uploaded_file = st.file_uploader("Upload .zip file", type="zip")
        if uploaded_file:
            # Use /tmp for Hugging Face compatibility (they only allow writes to /tmp)
            import tempfile
            upload_dir = tempfile.gettempdir()
            source_input = os.path.join(upload_dir, "uploaded.zip")
            with open(source_input, "wb") as f:
                f.write(uploaded_file.getbuffer())
    elif source_type == "GitHub Repository":
        source_input = st.text_input("GitHub URL", placeholder="https://github.com/owner/repo")
    elif source_type == "Web Documentation":
        source_input = st.text_input("Web URL", placeholder="https://docs.python.org/3/")
    
    if source_input and not st.session_state.processed_files:
        if st.button("Process & Index"):
            if not api_key:
                st.error(f"Please provide {provider} API Key.")
            elif provider == "groq" and not embedding_api_key:
                 st.error(f"Please provide {embedding_provider} API Key for embeddings.")
            else:
                # Use the new progress-tracked indexer
                from code_chatbot.indexing_progress import index_with_progress
                
                chat_engine, success, repo_files, workspace_root = index_with_progress(
                    source_input=source_input,
                    source_type=source_type,
                    provider=provider,
                    embedding_provider=embedding_provider,
                    embedding_api_key=embedding_api_key,
                    vector_db_type=vector_db_type,
                    use_agent=use_agent,
                    api_key=api_key,
                    gemini_model=gemini_model  # Pass selected model
                )
                
                if success:
                    st.session_state.chat_engine = chat_engine
                    st.session_state.processed_files = True
                    st.session_state.indexed_files = repo_files  # For file tree
                    st.session_state.workspace_root = workspace_root  # For relative paths
                    time.sleep(0.5)  # Brief pause to show success
                    st.rerun()

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

# ============================================================================
# MAIN 3-PANEL LAYOUT
# ============================================================================

st.title("🕷️ Code Crawler")

if not st.session_state.processed_files:
    # Show onboarding message when no files are processed
    st.info("👈 Please upload and index a codebase (ZIP, GitHub, or Web URL) to start.")
    st.markdown("""
    ### 🚀 Getting Started
    1. **Configure** your API key in the sidebar
    2. **Upload** a ZIP file, enter a GitHub URL, or Web documentation URL
    3. **Index** your codebase with one click
    4. **Explore** your code with the file explorer and chat interface
    """)
else:
    # 3-Panel Layout: File Tree | Code Viewer | Chat/Tools
    from components.file_explorer import render_file_tree, get_indexed_files_from_session
    from components.code_viewer import render_code_viewer_simple
    from components.multi_mode import (
        render_mode_selector,
        render_chat_mode,
        render_search_mode,
        render_refactor_mode,
        render_generate_mode
    )
    
    # Initialize session state for file explorer
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = None
    if "indexed_files" not in st.session_state:
        st.session_state.indexed_files = []
    
    # Create 3 columns: File Tree (15%) | Code Viewer (45%) | Chat/Tools (40%)
    col_tree, col_viewer, col_chat = st.columns([0.15, 0.45, 0.40])
    
    # --- LEFT PANEL: File Tree ---
    with col_tree:
        render_file_tree(
            st.session_state.get("indexed_files", []),
            st.session_state.get("workspace_root", "")
        )
    
    # --- CENTER PANEL: Code Viewer ---
    with col_viewer:
        render_code_viewer_simple(st.session_state.get("selected_file"))
    
    # --- RIGHT PANEL: Chat/Tools ---
    with col_chat:
        # Mode selector at the top
        selected_mode = render_mode_selector()
        
        st.divider()
        
        # Render appropriate interface based on mode
        if selected_mode == "search":
            render_search_mode()
        elif selected_mode == "refactor":
            render_refactor_mode()
        elif selected_mode == "generate":
            render_generate_mode(st.session_state.chat_engine)
        else:  # chat mode
            # Show chat mode UI
            render_chat_mode(st.session_state.chat_engine)
            st.caption(f"Using {provider}, Enhanced with AST")
            
            # Display History
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    # Render Sources if available
                    if "sources" in msg and msg["sources"]:
                        unique_sources = {}
                        for s in msg["sources"]:
                            if isinstance(s, dict):
                                fp = s.get('file_path', 'Unknown')
                            else:
                                fp = str(s)
                            if fp not in unique_sources:
                                unique_sources[fp] = s

                        chips_html = '<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;">'
                        for fp in unique_sources:
                            basename = os.path.basename(fp) if "/" in fp else fp
                            chips_html += f"""
                            <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 6px; padding: 4px 10px; font-size: 0.85em; color: #cbd5e1;">
                                📄 {basename}
                            </div>
                            """
                        chips_html += '</div>'
                        st.markdown(chips_html, unsafe_allow_html=True)
                    
                    st.markdown(msg["content"], unsafe_allow_html=True)

            # Handle pending prompt from suggestion buttons
            prompt = None
            if st.session_state.get("pending_prompt"):
                prompt = st.session_state.pending_prompt
                st.session_state.pending_prompt = None

            # Input
            if not prompt:
                prompt = st.chat_input("Ask about your code...")

            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    if st.session_state.chat_engine:
                        with st.spinner("Analyzing..."):
                            answer_payload = st.session_state.chat_engine.chat(prompt)
                            
                            if isinstance(answer_payload, tuple):
                                answer, sources = answer_payload
                            else:
                                answer = answer_payload
                                sources = []
                            
                            if sources:
                                unique_sources = {}
                                for s in sources:
                                    fp = s.get('file_path', 'Unknown')
                                    if fp not in unique_sources:
                                        unique_sources[fp] = s
                                
                                chips_html = '<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;">'
                                for fp in unique_sources:
                                    basename = os.path.basename(fp)
                                    chips_html += f"""
                                    <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 6px; padding: 4px 10px; font-size: 0.85em; color: #cbd5e1;">
                                        📄 {basename}
                                    </div>
                                    """
                                chips_html += '</div>'
                                st.markdown(chips_html, unsafe_allow_html=True)

                            st.markdown(answer)
                            
                            msg_data = {
                                "role": "assistant",
                                "content": answer,
                                "sources": sources if sources else []
                            }
                            st.session_state.messages.append(msg_data)
                    else:
                        st.error("Chat engine not initialized. Please re-index.")

