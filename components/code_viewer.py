"""
Code Viewer Component - Displays file content with syntax highlighting.
"""
import streamlit as st
from pathlib import Path
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
from typing import Optional


def get_language_from_extension(filename: str) -> str:
    """Get language name from file extension for display."""
    ext = Path(filename).suffix.lower()
    
    languages = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React JSX",
        ".tsx": "React TSX",
        ".html": "HTML",
        ".css": "CSS",
        ".json": "JSON",
        ".md": "Markdown",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".sql": "SQL",
        ".sh": "Shell",
        ".bash": "Bash",
        ".txt": "Plain Text",
    }
    
    return languages.get(ext, "Code")


def read_file_content(file_path: str) -> Optional[str]:
    """Read and return file content."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def render_code_with_syntax_highlighting(content: str, filename: str):
    """Render code with Pygments syntax highlighting."""
    try:
        lexer = get_lexer_for_filename(filename)
    except:
        lexer = TextLexer()
    
    # Custom CSS for dark theme
    formatter = HtmlFormatter(
        style='monokai',
        linenos=True,
        lineanchors='line',
        cssclass='source',
        wrapcode=True
    )
    
    highlighted = highlight(content, lexer, formatter)
    
    # Custom CSS
    css = """
    <style>
    .source {
        background-color: #1E1E1E !important;
        padding: 10px;
        border-radius: 8px;
        overflow-x: auto;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 13px;
        line-height: 1.5;
    }
    .source pre {
        margin: 0;
        background-color: transparent !important;
    }
    .source .linenos {
        color: #6e7681;
        padding-right: 15px;
        border-right: 1px solid #3d3d3d;
        margin-right: 15px;
        user-select: none;
    }
    .source .code {
        color: #e6e6e6;
    }
    </style>
    """
    
    st.markdown(css + highlighted, unsafe_allow_html=True)


def render_code_viewer(file_path: Optional[str] = None):
    """
    Render the code viewer panel.
    
    Args:
        file_path: Path to the file to display
    """
    if not file_path:
        # Show placeholder when no file is selected
        st.markdown("### 📝 Code Viewer")
        st.info("👈 Select a file from the tree to view its contents")
        return
    
    # File header
    filename = Path(file_path).name
    language = get_language_from_extension(filename)
    
    st.markdown(f"### 📝 {filename}")
    st.caption(f"📂 {file_path} • {language}")
    
    # Read and display content
    content = read_file_content(file_path)
    
    if content:
        # Add line count
        line_count = content.count('\n') + 1
        st.caption(f"{line_count} lines")
        
        # Render with syntax highlighting
        render_code_with_syntax_highlighting(content, filename)
    else:
        st.error("Could not read file contents")


def render_code_viewer_simple(file_path: Optional[str] = None):
    """
    Simpler code viewer using Streamlit's built-in code component.
    More reliable than custom HTML rendering.
    """
    if not file_path:
        st.markdown("### 📝 Code Viewer")
        st.info("👈 Select a file from the tree to view its contents")
        return
    
    filename = Path(file_path).name
    language = get_language_from_extension(filename)
    ext = Path(filename).suffix.lower().lstrip('.')
    
    st.markdown(f"### 📝 {filename}")
    st.caption(f"📂 `{file_path}` • {language}")
    
    content = read_file_content(file_path)
    
    if content:
        line_count = content.count('\n') + 1
        st.caption(f"{line_count} lines")
        
        # Use Streamlit's native code component
        # Map extensions to language names for st.code
        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "jsx": "javascript",
            "tsx": "typescript",
            "json": "json",
            "md": "markdown",
            "yaml": "yaml",
            "yml": "yaml",
            "sh": "bash",
            "bash": "bash",
            "sql": "sql",
            "html": "html",
            "css": "css",
        }
        
        lang = lang_map.get(ext, "")
        st.code(content, language=lang, line_numbers=True)
    else:
        st.error("Could not read file contents")
