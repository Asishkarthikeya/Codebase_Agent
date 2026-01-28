"""
Multi-mode interface components for Codebase Agent.

Provides different interaction modes: Chat, Search, Refactor, Generate
"""

import streamlit as st
from typing import Optional, Dict, Any
import os
from pathlib import Path


def get_workspace_root() -> str:
    """
    Get the workspace root directory for the indexed codebase.
    
    Returns:
        Path to the extracted/processed codebase
    """
    # Check if we have a processed data directory
    data_dir = Path("data")
    if data_dir.exists():
        # Find the extracted folder inside data
        for item in data_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                return str(item)
    
    # Fallback to data directory itself
    return "data"


def render_mode_selector() -> str:
    """
    Render mode selector and return selected mode.
    
    Returns:
        Selected mode: 'chat', 'search', 'refactor', or 'generate'
    """
    # Mode selector with icons
    mode = st.radio(
        "",
        ["💬 Chat", "🔍 Search", "🔧 Refactor", "✨ Generate"],
        horizontal=True,
        key="mode_selector",
        help="Select interaction mode"
    )
    
    # Map display name to mode key
    mode_map = {
        "💬 Chat": "chat",
        "🔍 Search": "search",
        "🔧 Refactor": "refactor",
        "✨ Generate": "generate"
    }
    
    return mode_map[mode]


def render_chat_mode(chat_engine):
    """
    Render standard chat interface.
    
    Args:
        chat_engine: ChatEngine instance
    """
    st.markdown("### 💬 Chat with Your Codebase")
    st.caption("Ask questions about your code, get explanations, and more")
    
    # Show suggested prompts if no history
    if not st.session_state.get("messages", []):
        st.markdown("#### 💡 Try asking:")
        
        suggestions = [
            "Explain how authentication works",
            "Find all database queries",
            "What are the main entry points?",
            "Show me the API endpoints",
            "Explain the data flow"
        ]
        
        cols = st.columns(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            with cols[i]:
                if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                    st.session_state.pending_prompt = suggestion
                    st.rerun()
    
    # Return True to continue with normal chat flow
    return True


def render_search_mode():
    """
    Render MCP code search interface.
    """
    st.markdown("### 🔍 Search Codebase")
    st.caption("Find patterns across your entire codebase using regex")
    
    # Get workspace root
    workspace = get_workspace_root()
    st.info(f"📁 Searching in: `{workspace}`")
    
    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        pattern = st.text_input(
            "Search Pattern",
            placeholder="e.g., class (or def.*login)",
            help="Enter a regex pattern to search for"
        )
    with col2:
        is_regex = st.checkbox("Regex", value=True, help="Use regex pattern matching")
    
    # File pattern filter
    file_pattern = st.text_input(
        "File Pattern",
        value="**/*.py",
        help="Glob pattern for files to search (e.g., **/*.py, src/**/*.js)"
    )
    
    # Context lines
    context_lines = st.slider("Context Lines", 0, 5, 2, help="Number of lines to show before/after match")
    
    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True):
        if not pattern:
            st.warning("Please enter a search pattern")
            return
        
        with st.spinner("Searching codebase..."):
            try:
                from code_chatbot.mcp_client import MCPClient
                
                client = MCPClient(workspace_root=workspace)
                results = client.search_code(
                    pattern=pattern,
                    file_pattern=file_pattern,
                    context_lines=context_lines,
                    is_regex=is_regex
                )
                
                if results:
                    st.success(f"✅ Found {len(results)} matches")
                    
                    # Display results
                    for i, result in enumerate(results[:20], 1):  # Limit to 20 results
                        with st.expander(f"📄 {result.file_path}:L{result.line_number}"):
                            # Show context before
                            if result.context_before:
                                st.code("\n".join(result.context_before), language="python")
                            
                            # Highlight matching line
                            st.markdown(f"**→ Line {result.line_number}:**")
                            st.code(result.line_content, language="python")
                            
                            # Show context after
                            if result.context_after:
                                st.code("\n".join(result.context_after), language="python")
                    
                    if len(results) > 20:
                        st.info(f"Showing first 20 of {len(results)} results")
                else:
                    st.info("No matches found. Try a different pattern.")
                    
            except Exception as e:
                st.error(f"Search failed: {e}")
                st.exception(e)


def render_refactor_mode():
    """
    Render MCP refactoring interface.
    """
    st.markdown("### 🔧 Refactor Code")
    st.caption("Perform automated refactorings across your codebase")
    
    # Get workspace root
    workspace = get_workspace_root()
    st.info(f"📁 Refactoring in: `{workspace}`")
    
    # Refactoring type selector
    refactor_type = st.selectbox(
        "Refactoring Type",
        ["Custom Regex", "Common Patterns"],
        help="Choose refactoring approach"
    )
    
    if refactor_type == "Custom Regex":
        # Custom regex refactoring
        col1, col2 = st.columns(2)
        with col1:
            search_pattern = st.text_input(
                "Search Pattern",
                placeholder="e.g., print\\((.*)\\)",
                help="Regex pattern to find"
            )
        with col2:
            replace_pattern = st.text_input(
                "Replace Pattern",
                placeholder="e.g., logger.info(\\1)",
                help="Replacement (supports capture groups like \\1)"
            )
        
        file_pattern = st.text_input(
            "File Pattern",
            value="**/*.py",
            help="Files to process"
        )
        
        dry_run = st.checkbox("Dry Run (Preview Only)", value=True, help="Preview changes without applying")
        
        if st.button("🔧 Refactor", type="primary", use_container_width=True):
            if not search_pattern or not replace_pattern:
                st.warning("Please enter both search and replace patterns")
                return
            
            with st.spinner("Processing refactoring..."):
                try:
                    from code_chatbot.mcp_client import MCPClient
                    
                    client = MCPClient(workspace_root=workspace)
                    result = client.refactor_code(
                        search_pattern=search_pattern,
                        replace_pattern=replace_pattern,
                        file_pattern=file_pattern,
                        dry_run=dry_run
                    )
                    
                    if result.success:
                        mode_text = "Preview" if dry_run else "Applied"
                        st.success(f"✅ Refactoring {mode_text}: {result.files_changed} files, {result.total_replacements} replacements")
                        
                        # Show changes
                        if result.changes:
                            for change in result.changes[:10]:  # Limit to 10 files
                                with st.expander(f"📄 {change['file_path']} ({change['replacements']} replacements)"):
                                    if change.get('preview'):
                                        st.code(change['preview'], language="diff")
                            
                            if len(result.changes) > 10:
                                st.info(f"Showing first 10 of {len(result.changes)} changed files")
                        else:
                            st.info("No matches found for the given pattern")
                        
                        if dry_run and result.files_changed > 0:
                            st.info("💡 Uncheck 'Dry Run' to apply these changes")
                    else:
                        st.error(f"Refactoring failed: {result.error}")
                        
                except Exception as e:
                    st.error(f"Refactoring failed: {e}")
                    st.exception(e)
    
    else:
        # Common patterns
        st.markdown("#### Common Refactoring Patterns")
        
        common_patterns = {
            "print() → logging": {
                "search": r"print\((.*)\)",
                "replace": r"logger.info(\1)",
                "description": "Replace print statements with logging"
            },
            "assertEqual → assert ==": {
                "search": r"assertEqual\(([^,]+),\s*([^)]+)\)",
                "replace": r"assert \1 == \2",
                "description": "Convert unittest to pytest assertions"
            },
            "Remove trailing whitespace": {
                "search": r"[ \t]+$",
                "replace": "",
                "description": "Clean up trailing whitespace"
            }
        }
        
        pattern_choice = st.selectbox(
            "Select Pattern",
            list(common_patterns.keys())
        )
        
        selected = common_patterns[pattern_choice]
        st.info(selected["description"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.code(f"Search: {selected['search']}", language="regex")
        with col2:
            st.code(f"Replace: {selected['replace']}", language="regex")
        
        dry_run = st.checkbox("Dry Run (Preview Only)", value=True, key="common_dry_run")
        
        if st.button("Apply Refactoring", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                try:
                    from code_chatbot.mcp_client import MCPClient
                    
                    client = MCPClient(workspace_root=workspace)
                    result = client.refactor_code(
                        search_pattern=selected["search"],
                        replace_pattern=selected["replace"],
                        file_pattern="**/*.py",
                        dry_run=dry_run
                    )
                    
                    if result.success:
                        st.success(f"✅ {result.files_changed} files, {result.total_replacements} replacements")
                        if result.changes:
                            for change in result.changes[:5]:
                                with st.expander(f"📄 {change['file_path']}"):
                                    st.code(change.get('preview', 'No preview'), language="diff")
                    else:
                        st.error(f"Failed: {result.error}")
                except Exception as e:
                    st.error(f"Failed: {e}")


def render_generate_mode(chat_engine):
    """
    Render code generation interface using ChatEngine.
    
    Args:
        chat_engine: ChatEngine instance
    """
    st.markdown("### ✨ Generate New Features")
    st.caption("Use AI to scaffold complete features from descriptions")
    
    # Feature description
    feature_desc = st.text_area(
        "Describe the feature you want to build",
        placeholder="Example: Create a user authentication system with JWT tokens, login/logout endpoints, password hashing with bcrypt, and session management",
        height=120,
        help="Be as detailed as possible"
    )
    
    # Options
    col1, col2, col3 = st.columns(3)
    with col1:
        include_tests = st.checkbox("Generate Tests", value=True)
    with col2:
        include_docs = st.checkbox("Generate Docs", value=True)
    with col3:
        include_examples = st.checkbox("Include Examples", value=True)
    
    # Framework selection
    framework = st.selectbox(
        "Framework/Stack",
        ["Auto-detect from codebase", "FastAPI", "Flask", "Django", "Express.js", "React", "Vue.js"],
        help="Technology stack for the feature"
    )
    
    if st.button("🚀 Generate Feature", type="primary", use_container_width=True):
        if not feature_desc:
            st.warning("Please describe the feature you want to build")
            return
        
        if not chat_engine:
            st.error("⚠️ Chat engine not initialized. Please index your codebase first.")
            return
        
        with st.spinner("🤖 Generating feature... (this may take 30-60 seconds)"):
            try:
                # Build comprehensive prompt
                prompt = f"""Generate a complete implementation for this feature:

**Feature Request:**
{feature_desc}

**Requirements:**
- Framework: {framework}
- Include tests: {include_tests}
- Include documentation: {include_docs}
- Include examples: {include_examples}

**Please provide:**
1. A clear file structure showing all files to create
2. Complete, production-ready code for each file
3. Clear comments explaining the code
4. Setup/installation instructions
5. Usage examples

Format each file like this:

### `path/to/filename.py`
```python
# Code here
```

Make sure the code follows best practices and matches the existing codebase style."""
                
                # Use chat engine
                answer, sources = chat_engine.chat(prompt)
                
                st.success("✅ Feature generated!")
                
                # Display generated content
                st.markdown("---")
                st.markdown("#### 📝 Generated Feature")
                st.markdown(answer)
                
                # Show sources if available
                if sources:
                    st.markdown("---")
                    with st.expander("📚 Reference Files Used"):
                        for source in sources:
                            if isinstance(source, dict):
                                st.write(f"- `{source.get('file_path', 'Unknown')}`")
                            else:
                                st.write(f"- `{source}`")
                        
            except Exception as e:
                st.error(f"Generation failed: {e}")
                st.exception(e)


# Export functions
__all__ = [
    'render_mode_selector',
    'render_chat_mode',
    'render_search_mode',
    'render_refactor_mode',
    'render_generate_mode'
]
