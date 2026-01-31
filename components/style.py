import streamlit as st
import base64
import os

def apply_custom_css():
    """Apply shared CSS styles to the current page."""
    logo_b64 = ""
    if os.path.exists("assets/logo.png"):
        try:
            with open("assets/logo.png", "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
        except:
            pass

    st.markdown("""
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
    /* -------------------------------------------------------------------------- */
        /*                                   BUTTONS                                  */
        /* -------------------------------------------------------------------------- */
        
        /* Primary Actions (Gradient) */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%);
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px rgba(14, 165, 233, 0.3);
            text-transform: uppercase;
            font-size: 0.85rem;
        }
        
        /* Secondary Actions (File Explorer Items) */
        .stButton button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid transparent !important;
            color: #94A3B8 !important; /* Slate 400 */
            text-align: left !important;
            display: flex !important;
            justify-content: flex-start !important;
            padding: 8px 12px !important; /* Bigger padding */
            font-size: 15px !important; /* Bigger Font */
            font-family: 'JetBrains Mono', monospace !important; /* Monospace for files */
            transition: all 0.2s ease;
            box-shadow: none !important;
        }

        .stButton button[kind="secondary"]:hover {
            background: rgba(56, 189, 248, 0.1) !important;
            color: #38BDF8 !important;
            transform: translateX(4px); /* Slide effect */
        }
        
        /* Generic overrides if kind is not caught */
        .stButton button:hover {
             /* Handled by specific kinds above */
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
        
        /* -------------------------------------------------------------------------- */
        /*                         IDE-STYLE PANEL LAYOUT                            */
        /* -------------------------------------------------------------------------- */
        
        /* Main content area - fixed height */
        .main .block-container {
            max-height: calc(100vh - 80px);
            overflow: hidden;
            padding-top: 1rem;
        }
        
        /* Make columns scrollable independently */
        [data-testid="column"] {
            max-height: calc(100vh - 120px);
            overflow-y: auto;
            overflow-x: hidden;
            scrollbar-width: thin;
            scrollbar-color: #475569 transparent;
        }
        
        /* Custom scrollbar for webkit browsers */
        [data-testid="column"]::-webkit-scrollbar {
            width: 6px;
        }
        
        [data-testid="column"]::-webkit-scrollbar-track {
            background: transparent;
        }
        
        [data-testid="column"]::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 3px;
        }
        
        [data-testid="column"]::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }
        
        /* Code viewer specific - scrollable code block */
        .stCode {
            max-height: 60vh;
            overflow-y: auto !important;
        }

        /* -------------------------------------------------------------------------- */
        /*                            HORIZONTAL TABS                                 */
        /* -------------------------------------------------------------------------- */
        /* -------------------------------------------------------------------------- */
        /*                            HORIZONTAL TABS                                 */
        /* -------------------------------------------------------------------------- */
        
        /* Tab List Container */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            padding-bottom: 4px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Individual Tab (Inactive) */
        .stTabs [data-baseweb="tab"] {
            height: 40px;
            white-space: pre-wrap;
            border-radius: 6px;
            gap: 6px;
            padding: 0px 16px;
            color: #94A3B8 !important; /* Slate 400 */
            font-weight: 500;
            background: transparent;
            border: 1px solid transparent;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Tab Hover State */
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #E2E8F0 !important;
        }

        /* Active Tab (Selected) */
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: rgba(56, 189, 248, 0.15) !important;
            color: #38BDF8 !important; /* Sky Blue */
            border: 1px solid rgba(56, 189, 248, 0.3);
            font-weight: 600;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.1);
        }
        
        /* Tab Icons styling fix */
        .stTabs [data-baseweb="tab"] p {
            font-size: 0.95rem;
        }
        
    </style>
    """.replace("LOGO_BASE64_PLACEHOLDER", logo_b64), unsafe_allow_html=True)
