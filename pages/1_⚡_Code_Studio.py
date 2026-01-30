"""
⚡ Code Studio - The Main IDE Interface
"""
import streamlit as st
import os
from components.style import apply_custom_css
from components.file_explorer import render_file_tree
from components.code_viewer import render_code_viewer_simple
from components.panels import render_chat_panel, render_search_panel, render_generate_panel

st.set_page_config(
    page_title="Code Studio", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="collapsed" # Hide standard sidebar
)

apply_custom_css()

# --- State Management ---
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "explorer"
    
if "processed_files" not in st.session_state or not st.session_state.processed_files:
    # If accessed directly without processing, redirect home
    st.warning("⚠️ Please index a codebase first.")
    if st.button("Go Home"):
        st.switch_page("app.py")
    st.stop()

# --- Layout ---
# We use a custom 3-column layout to mimic IDE
# Col 1: Activity Bar (Narrow, just icons)
# Col 2: Side Panel (Resizable-ish via column ratio, contains the active tool)
# Col 3: Main Editor (Wide, contains code)

# Define column ratios
# Activity bar needs to be very narrow. Streamlit cols are proportional.
# Ratio: 0.5 : 3 : 7
col_activity, col_panel, col_editor = st.columns([0.5, 3, 7])

# --- 1. Activity Bar ---
with col_activity:
    # We use a vertical layout of buttons. 
    # To make them look like tabs, we can use a custom component or just buttons that update state.
    # Current limitation: Buttons rerun app. That's fine for Streamlit.
    
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    
    # Explorer Tab
    if st.button("📁", key="tab_explorer", help="Explorer", use_container_width=True):
        st.session_state.active_tab = "explorer"
    
    # Search Tab
    if st.button("🔍", key="tab_search", help="Search", use_container_width=True):
        st.session_state.active_tab = "search"
        
    # Chat Tab
    if st.button("💬", key="tab_chat", help="Chat", use_container_width=True):
        st.session_state.active_tab = "chat"
        
    # Generate Tab
    if st.button("✨", key="tab_generate", help="Generate", use_container_width=True):
        st.session_state.active_tab = "generate"

    # Settings / Home (Exit)
    st.markdown("<div style='margin-top: 50vh;'></div>", unsafe_allow_html=True)
    if st.button("🏠", key="tab_home", help="Back to Home", use_container_width=True):
        st.switch_page("app.py")


# --- 2. Side Panel ---
with col_panel:
    active_tab = st.session_state.active_tab
    
    if active_tab == "explorer":
        st.markdown("### 📁 Explorer")
        render_file_tree(
            st.session_state.get("indexed_files", []),
            st.session_state.get("workspace_root", "")
        )
        
    elif active_tab == "search":
        render_search_panel(st.session_state.get("indexed_files", []))
        
    elif active_tab == "chat":
        chat_engine = st.session_state.get("chat_engine")
        if chat_engine:
            render_chat_panel(chat_engine)
        else:
            st.error("Chat engine unavailable.")
            
    elif active_tab == "generate":
        chat_engine = st.session_state.get("chat_engine")
        if chat_engine:
            render_generate_panel(chat_engine, st.session_state.get("indexed_files", []))
        else:
            st.error("Chat engine unavailable.")


# --- 3. Main Editor ---
with col_editor:
    # If a file is selected, show it. Otherwise show welcome/empty state.
    selected_file = st.session_state.get("selected_file")
    
    if selected_file:
        # We use a container to ensure height consistency
        with st.container():
            # Breadcrumbs / File Header
            filename = os.path.basename(selected_file)
            st.markdown(f"**{filename}**")
            
            # Code Viewer
            render_code_viewer_simple(selected_file)
            
    else:
        # Empty State
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; opacity: 0.5;">
                <h1>⚡ Code Studio</h1>
                <p>Select a file from the explorer to view context.</p>
                <p>Use the activity bar on the left to toggle tools.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
