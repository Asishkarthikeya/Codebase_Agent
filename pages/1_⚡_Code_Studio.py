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
# We use a 2-column layout: Side Panel (with Tabs) | Main Editor
# Ratio: 3.5 : 6.5
col_panel, col_editor = st.columns([3.5, 6.5])

# --- Side Panel (Tabs) ---
with col_panel:
    # Use native Streamlit tabs for horizontal navigation
    tab_explorer, tab_search, tab_chat, tab_generate = st.tabs(["📁 Explorer", "🔍 Search", "💬 Chat", "✨ Generate"])
    
    with tab_explorer:
        st.markdown("### 📁 Project Files")
        render_file_tree(
            st.session_state.get("indexed_files", []),
            st.session_state.get("workspace_root", "")
        )
        
        st.divider()
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")

    with tab_search:
        render_search_panel(st.session_state.get("indexed_files", []))

    with tab_chat:
        chat_engine = st.session_state.get("chat_engine")
        if chat_engine:
            render_chat_panel(chat_engine)
        else:
            st.error("Chat engine unavailable. Please index a codebase first.")

    with tab_generate:
        chat_engine = st.session_state.get("chat_engine")
        if chat_engine:
            render_generate_panel(chat_engine, st.session_state.get("indexed_files", []))
        else:
            st.error("Chat engine unavailable.")

# --- Main Editor ---
with col_editor:
    # If a file is selected, show it. Otherwise show welcome/empty state.
    selected_file = st.session_state.get("selected_file")
    
    if selected_file:
        # We use a container to ensure height consistency
        with st.container():
            # Breadcrumbs / File Header
            filename = os.path.basename(selected_file)
            st.caption(f"Editing: {filename}")
            
            # Code Viewer
            render_code_viewer_simple(selected_file)
            
    else:
        # Empty State
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; opacity: 0.5;">
                <h1>⚡ Code Studio</h1>
                <p>Select a file from the explorer to view context.</p>
                <p>Use the tabs on the left to switch between tools.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
