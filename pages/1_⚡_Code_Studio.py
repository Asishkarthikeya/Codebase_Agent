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
    initial_sidebar_state="expanded" 
)

apply_custom_css()

# --- State Management ---
if "processed_files" not in st.session_state or not st.session_state.processed_files:
    st.warning("⚠️ Please index a codebase first.")
    if st.button("Go Home"):
        st.switch_page("app.py")
    st.stop()

# --- Sidebar: Navigation & Explorer ---
with st.sidebar:
    # 1. View Settings
    st.header("⚙️ View")
    layout_mode = st.radio("Layout Mode", ["Tabs (Full Width)", "Split View"], horizontal=True)
    
    st.divider()
    
    # 2. File Explorer
    render_file_tree(
        st.session_state.get("indexed_files", []),
        st.session_state.get("workspace_root", "")
    )
    
    st.divider()
    
    # 3. Actions
    if st.button("🏠 New Codebase", use_container_width=True):
        st.session_state.processed_files = False
        st.session_state.chat_engine = None
        st.session_state.indexed_files = None
        st.session_state.workspace_root = None
        st.session_state.selected_file = None
        st.switch_page("app.py")

# --- Main Workspace ---

if layout_mode == "Tabs (Full Width)":
    # TABBED LAYOUT (Default)
    # Renamed "Agent" to "Refactor" for clarity
    tab_chat, tab_code, tab_refactor, tab_search = st.tabs(["💬 Chat", "📝 Code Editor", "✨ Refactor", "🔍 Search"])
    
    with tab_chat:
        chat_engine = st.session_state.get("chat_engine")
        if chat_engine:
            render_chat_panel(chat_engine)
        else:
            st.error("Chat engine unavailable.")
            
    with tab_code:
        selected_file = st.session_state.get("selected_file")
        if selected_file:
            filename = os.path.basename(selected_file)
            st.caption(f"Editing: {filename}")
            render_code_viewer_simple(selected_file)
        else:
            st.info("👈 Select a file from the sidebar to view code.")
            
    with tab_refactor:
        chat_engine = st.session_state.get("chat_engine")
        if chat_engine:
            render_generate_panel(chat_engine, st.session_state.get("indexed_files", []))
            
    with tab_search:
        render_search_panel(st.session_state.get("indexed_files", []))

else:
    # SPLIT VIEW (Legacy)
    split_ratio = st.slider("Panel Width (%)", 20, 80, 40, step=5)
    panel_width = split_ratio / 100.0
    editor_width = 1.0 - panel_width
    
    col_panel, col_editor = st.columns([panel_width, editor_width])
    
    with col_panel:
        tab_sub_chat, tab_sub_search, tab_sub_agent = st.tabs(["💬 Chat", "🔍 Search", "✨ Agent"])
        
        with tab_sub_chat:
            chat_engine = st.session_state.get("chat_engine")
            if chat_engine:
                render_chat_panel(chat_engine)
        
        with tab_sub_search:
            render_search_panel(st.session_state.get("indexed_files", []))
            
        with tab_sub_agent:
            chat_engine = st.session_state.get("chat_engine")
            if chat_engine:
                render_generate_panel(chat_engine, st.session_state.get("indexed_files", []))
    
    with col_editor:
        selected_file = st.session_state.get("selected_file")
        if selected_file:
            st.caption(f"Editing: {os.path.basename(selected_file)}")
            render_code_viewer_simple(selected_file)
        else:
            st.info("👈 Select a file from the sidebar.")
