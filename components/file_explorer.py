"""
File Explorer Component - Renders file tree sidebar for indexed files.
"""
import streamlit as st
import os
from pathlib import Path
from typing import Dict, List, Optional


def build_file_tree(file_paths: List[str], base_path: str = "") -> Dict:
    """
    Build a nested dictionary representing the file tree from a list of file paths.
    
    Args:
        file_paths: List of file paths (relative or absolute)
        base_path: Base path to make paths relative to
        
    Returns:
        Nested dictionary representing folder structure
    """
    tree = {}
    
    for file_path in file_paths:
        # Make path relative if base_path is provided
        if base_path:
            try:
                rel_path = os.path.relpath(file_path, base_path)
            except ValueError:
                rel_path = file_path
        else:
            rel_path = file_path
        
        # Split path into parts
        parts = Path(rel_path).parts
        
        # Navigate/create tree structure
        current = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # It's a file
                current[part] = {"_type": "file", "_path": file_path}
            else:
                # It's a directory
                if part not in current:
                    current[part] = {"_type": "dir"}
                current = current[part]
    
    return tree


def get_file_icon(filename: str) -> str:
    """Get an appropriate icon for a file based on its extension."""
    ext = Path(filename).suffix.lower()
    
    icons = {
        ".py": "🐍",
        ".js": "📜",
        ".ts": "📘",
        ".jsx": "⚛️",
        ".tsx": "⚛️",
        ".html": "🌐",
        ".css": "🎨",
        ".json": "📋",
        ".md": "📝",
        ".txt": "📄",
        ".yaml": "⚙️",
        ".yml": "⚙️",
        ".toml": "⚙️",
        ".sql": "🗃️",
        ".sh": "🖥️",
        ".bash": "🖥️",
        ".env": "🔐",
        ".gitignore": "🚫",
    }
    
    return icons.get(ext, "📄")


def render_tree_node(name: str, node: Dict, path_prefix: str = "", depth: int = 0):
    """Recursively render a tree node (file or directory)."""
    
    if node.get("_type") == "file":
        # Render file
        icon = get_file_icon(name)
        file_path = node.get("_path", "")
        
        # Create button for file selection
        indent = "&nbsp;" * (depth * 4)
        if st.button(f"{icon} {name}", key=f"file_{file_path}", use_container_width=True):
            st.session_state.selected_file = file_path
            st.rerun()
    else:
        # Render directory
        dir_key = f"dir_{path_prefix}/{name}"
        
        # Check if directory is expanded
        if "expanded_dirs" not in st.session_state:
            st.session_state.expanded_dirs = set()
        
        is_expanded = dir_key in st.session_state.expanded_dirs
        
        # Toggle button for directory
        icon = "📂" if is_expanded else "📁"
        if st.button(f"{icon} {name}", key=dir_key, use_container_width=True):
            if is_expanded:
                st.session_state.expanded_dirs.discard(dir_key)
            else:
                st.session_state.expanded_dirs.add(dir_key)
            st.rerun()
        
        # Render children if expanded
        if is_expanded:
            # Get children (excluding metadata keys)
            children = {k: v for k, v in node.items() if not k.startswith("_")}
            
            # Sort: directories first, then files
            sorted_children = sorted(
                children.items(),
                key=lambda x: (x[1].get("_type") == "file", x[0].lower())
            )
            
            for child_name, child_node in sorted_children:
                with st.container():
                    render_tree_node(
                        child_name, 
                        child_node, 
                        f"{path_prefix}/{name}", 
                        depth + 1
                    )


def render_file_tree(indexed_files: List[str], base_path: str = ""):
    """
    Render the file tree sidebar.
    
    Args:
        indexed_files: List of indexed file paths
        base_path: Base path to make paths relative to
    """
    st.markdown("### 📁 Files")
    
    if not indexed_files:
        st.caption("No files indexed yet")
        return
    
    st.caption(f"{len(indexed_files)} files indexed")
    
    # Build tree structure
    tree = build_file_tree(indexed_files, base_path)
    
    # Sort root level: directories first, then files
    sorted_root = sorted(
        tree.items(),
        key=lambda x: (x[1].get("_type") == "file", x[0].lower())
    )
    
    # Render tree
    for name, node in sorted_root:
        render_tree_node(name, node)


def get_indexed_files_from_session() -> List[str]:
    """Get the list of indexed files from session state."""
    return st.session_state.get("indexed_files", [])
