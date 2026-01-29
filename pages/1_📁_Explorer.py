"""
📁 Explorer Page - Browse files and view code
"""
import streamlit as st
import os
from pathlib import Path

from components.style import apply_custom_css

st.set_page_config(page_title="Explorer | Code Crawler", page_icon="📁", layout="wide")
apply_custom_css()

# Check if codebase is indexed
if not st.session_state.get("processed_files"):
    st.warning("⚠️ No codebase indexed yet. Go to **Home** to upload and index a codebase.")
    st.stop()

# Get indexed files
indexed_files = st.session_state.get("indexed_files", [])
workspace_root = st.session_state.get("workspace_root", "")

st.title("📁 Code Explorer")
st.caption(f"{len(indexed_files)} files indexed")

# Two-column layout: File tree (25%) | Code viewer (75%)
# CSS is now handled by apply_custom_css


col1, col2 = st.columns([1, 3])

with col1:
    from components.file_explorer import render_file_tree
    
    render_file_tree(
        st.session_state.get("indexed_files", []),
        st.session_state.get("workspace_root", "")
    )

with col2:
    from components.code_viewer import render_code_viewer_simple
    
    render_code_viewer_simple(st.session_state.get("selected_file"))
