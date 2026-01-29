"""
File Explorer Component - VS Code style file tree.
"""
import streamlit as st
import os
from pathlib import Path
from typing import Dict, List


def build_file_tree(file_paths: List[str], base_path: str = "") -> Dict:
    """Build a nested dictionary representing the file tree."""
    tree = {}
    
    for file_path in file_paths:
        if base_path:
            try:
                rel_path = os.path.relpath(file_path, base_path)
            except ValueError:
                rel_path = file_path
        else:
            rel_path = file_path
        
        parts = Path(rel_path).parts
        current = tree
        
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = {"_type": "file", "_path": file_path}
            else:
                if part not in current:
                    current[part] = {"_type": "dir", "_children": {}}
                current = current.get(part, {}).get("_children", current.get(part, {}))
                if "_children" not in current:
                    current = current
    
    return tree


def get_file_icon(filename: str) -> str:
    """Get icon for file based on extension."""
    ext = Path(filename).suffix.lower()
    icons = {
        ".py": "🐍", ".js": "📜", ".ts": "📘", ".jsx": "⚛️", ".tsx": "⚛️",
        ".html": "🌐", ".css": "🎨", ".json": "📋", ".md": "📝",
        ".yaml": "⚙️", ".yml": "⚙️", ".toml": "⚙️", ".sql": "🗃️",
        ".env": "🔐", ".gitignore": "🚫", ".txt": "📄",
    }
    return icons.get(ext, "📄")


def render_file_tree(indexed_files: List[str], base_path: str = ""):
    """Render VS Code style file tree."""
    
    if not indexed_files:
        st.caption("No files indexed")
        return
    
    # Custom CSS for tree styling
    st.markdown("""
    <style>
    .tree-item {
        padding: 2px 0;
        cursor: pointer;
        font-size: 13px;
        font-family: 'Segoe UI', sans-serif;
        color: #ccc;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .tree-item:hover {
        background: rgba(255,255,255,0.1);
    }
    .tree-dir {
        font-weight: 500;
    }
    .tree-file {
        font-weight: 400;
    }
    .tree-selected {
        background: rgba(56, 189, 248, 0.2) !important;
        color: #38bdf8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**📁 Files** ({len(indexed_files)})")
    
    # Build and render tree
    tree = build_file_tree(indexed_files, base_path)
    
    # Initialize expanded state
    if "tree_expanded" not in st.session_state:
        st.session_state.tree_expanded = set()
    
    # Render tree items
    render_tree_items(tree, 0)


def render_tree_items(tree: Dict, depth: int):
    """Render tree items with proper indentation."""
    
    # Sort: directories first, then files
    items = [(k, v) for k, v in tree.items() if not k.startswith("_")]
    sorted_items = sorted(items, key=lambda x: (x[1].get("_type") == "file", x[0].lower()))
    
    for name, node in sorted_items:
        is_file = node.get("_type") == "file"
        indent = "│  " * depth
        
        if is_file:
            # File item
            file_path = node.get("_path", "")
            icon = get_file_icon(name)
            is_selected = st.session_state.get("selected_file") == file_path
            
            # Compact button
            btn_label = f"{indent}├─ {icon} {name}"
            if st.button(btn_label, key=f"tree_{file_path}", use_container_width=True,
                        type="primary" if is_selected else "secondary"):
                st.session_state.selected_file = file_path
                st.rerun()
        else:
            # Directory item
            dir_key = f"dir_{depth}_{name}"
            is_expanded = dir_key in st.session_state.tree_expanded
            arrow = "▼" if is_expanded else "▶"
            
            btn_label = f"{indent}{arrow} 📁 {name}"
            if st.button(btn_label, key=dir_key, use_container_width=True, type="secondary"):
                if is_expanded:
                    st.session_state.tree_expanded.discard(dir_key)
                else:
                    st.session_state.tree_expanded.add(dir_key)
                st.rerun()
            
            # Render children if expanded
            if is_expanded:
                children = {k: v for k, v in node.items() if not k.startswith("_")}
                render_tree_items(children, depth + 1)


def get_indexed_files_from_session() -> List[str]:
    """Get indexed files from session state."""
    return st.session_state.get("indexed_files", [])
