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
        :root {
            --glass-bg: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(255, 255, 255, 0.1);
        }
        
        /* Global Text */
        p, div, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown {
            color: #E2E8F0 !important;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: rgba(11, 12, 16, 0.95);
            border-right: 1px solid var(--glass-border);
        }
        
        /* Buttons */
        .stButton button {
            background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%);
            color: white !important;
            border: none;
            border-radius: 8px;
            font-weight: 600;
        }
        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
        }
        
        /* Chat Messages */
        .stChatMessage {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
        }
        .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
            border-left: 3px solid #38BDF8;
            background: linear-gradient(90deg, rgba(56, 189, 248, 0.05) 0%, rgba(15, 23, 42, 0.6) 100%);
        }
        
        /* IDE Layout & Scrolling */
        .main .block-container {
            max-width: 100% !important;
            padding-top: 1rem !important; /* Minimized top padding */
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-height: 100vh;
            overflow: hidden;
        }
        
        /* Align Tabs with Editor */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px 4px 0px 0px;
            gap: 2px;
            padding-top: 0px;
            padding-bottom: 0px;
            color: #f8fafc !important; /* Force white text */
            font-weight: 600;
        }
        
        div[data-testid="column"] {
            max-height: calc(100vh - 60px);
            overflow-y: auto;
            overflow-x: hidden;
            scrollbar-width: thin;
        }
        
        .stCode {
            max-height: 75vh !important;
            overflow-y: auto !important;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 3px;
        }
        
        /* Source Chips */
        .source-chip {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 0.85em;
            color: #cbd5e1;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-right: 8px;
            margin-bottom: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
