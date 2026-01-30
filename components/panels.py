import streamlit as st
import os
import re
from pathlib import Path
import logging

def render_chat_panel(chat_engine):
    """
    Renders the Chat interface within the side panel.
    """
    st.markdown("### 💬 Chat")
    
    # Initialize messages for this specific panel usage if needed
    # But we usually share global st.session_state.messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Suggestion buttons (only if no messages)
    if not st.session_state.messages:
        st.markdown("#### 💡 Try asking:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Explain structure", use_container_width=True, key="btn_explain"):
                st.session_state.pending_prompt = "Explain the project structure and main components"
                st.rerun()
            if st.button("⚡ Generate utility", use_container_width=True, key="btn_util"):
                st.session_state.pending_prompt = "Generate a new utility function for this project"
                st.rerun()
        with col2:
            if st.button("📝 List functions", use_container_width=True, key="btn_list"):
                st.session_state.pending_prompt = "List all the main functions and their purpose"
                st.rerun()
            if st.button("🔧 Improvements", use_container_width=True, key="btn_imp"):
                st.session_state.pending_prompt = "What improvements would you suggest for this code?"
                st.rerun()
    
    # Message Container
    # We use a container with fixed height to allow scrolling independent of the editor
    # But standard Streamlit scrolling works best if we just let it flow in the column.
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Render Sources if available
            if "sources" in message and message["sources"]:
                _render_sources(message["sources"])
            
            st.markdown(message["content"])

    # Handle pending prompt
    prompt = st.session_state.pop("pending_prompt", None)

    # Chat input
    # key needs to be unique if we have multiple inputs, but usually only one chat input active
    if user_input := st.chat_input("Ask about your code...", key="chat_panel_input"):
        prompt = user_input

    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Blocking call
                    answer_payload = chat_engine.chat(prompt)
                    
                    if isinstance(answer_payload, tuple):
                        response, sources = answer_payload
                    else:
                        response = answer_payload
                        sources = []
                    
                    if sources:
                        _render_sources(sources)
                    
                    st.markdown(response)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "sources": sources
                    })
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def _render_sources(sources):
    unique_sources = {}
    for s in sources:
        if isinstance(s, dict):
            fp = s.get('file_path', 'Unknown')
        else:
            fp = str(s)
        if fp not in unique_sources:
            unique_sources[fp] = s

    chips_html = '<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;">'
    for fp in unique_sources:
        basename = os.path.basename(fp) if "/" in fp else fp
        chips_html += f"""
        <div class="source-chip">
            📄 {basename}
        </div>
        """
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)


def render_search_panel(indexed_files):
    """
    Renders the Search interface.
    """
    st.markdown("### 🔍 Search")
    
    query = st.text_input("Search pattern", placeholder="Enter search term or regex...", key="search_query")
    use_regex = st.checkbox("Use regex", value=False, key="search_regex")
    
    file_types = st.multiselect(
        "Filter by file type",
        options=[".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", ".md"],
        default=[],
        key="search_types"
    )
    
    if query and st.button("Go", key="search_go", type="primary"):
        results = []
        try:
            pattern = re.compile(query, re.IGNORECASE) if use_regex else None
        except re.error as e:
            st.error(f"Invalid regex: {e}")
            return

        with st.spinner("Searching..."):
            for file_path in indexed_files:
                if file_types:
                    ext = Path(file_path).suffix.lower()
                    if ext not in file_types:
                        continue
                
                try:
                    with open(file_path, "r", errors="ignore") as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        if use_regex:
                            if pattern.search(line):
                                results.append({
                                    "file": file_path,
                                    "line_num": i,
                                    "content": line.strip(),
                                    "match": pattern.search(line).group()
                                })
                        else:
                            if query.lower() in line.lower():
                                results.append({
                                    "file": file_path,
                                    "line_num": i,
                                    "content": line.strip(),
                                    "match": query
                                })
                except Exception:
                    continue
        
        st.markdown(f"**Found {len(results)} matches**")
        
        if results:
            # Group by file
            by_file = {}
            for r in results:
                f = r["file"]
                if f not in by_file:
                    by_file[f] = []
                by_file[f].append(r)
            
            for file_path, matches in by_file.items():
                filename = os.path.basename(file_path)
                with st.expander(f"📄 {filename} ({len(matches)})", expanded=False):
                    for m in matches[:5]:
                        # Make clickable logic? Streamlit doesn't easily support clickable text to trigger state change without rerun
                        # We use buttons
                        if st.button(f"L{m['line_num']}: {m['content'][:40]}...", key=f"nav_{file_path}_{m['line_num']}"):
                            st.session_state.selected_file = file_path
                            # st.rerun() # Might not be needed if this triggers a rerun naturally
        else:
            st.info("No matches.")


def render_generate_panel(chat_engine, indexed_files):
    """
    Renders the Generate/Modify interface.
    """
    st.markdown("### ✨ Generate")
    
    mode = st.radio(
        "Mode",
        ["New Code", "Modify", "New File"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if mode == "New Code":
        st.caption("Generate new code snippet")
        description = st.text_area("Request", placeholder="e.g. Email validator function", height=100, key="gen_desc")
        context = st.text_input("Context", placeholder="e.g. style of utils.py", key="gen_ctx")
        
        if st.button("Generate", type="primary", key="btn_gen_new"):
            with st.spinner("Working..."):
                prompt = f"Generate code: {description}\nContext: {context}"
                try:
                    resp = chat_engine.chat(prompt)
                     # Unwrap if tuple
                    if isinstance(resp, tuple):
                        resp = resp[0]
                    st.code(resp)
                except Exception as e:
                    st.error(str(e))

    elif mode == "Modify":
        st.caption("Modify existing file")
        # Ensure we have files
        if not indexed_files:
            st.error("No files indexed.")
            return

        # Use session state to remember selection if possible, or just default
        # We need a unique key
        selected_file = st.selectbox(
            "File", 
            indexed_files, 
            format_func=lambda x: os.path.basename(x),
            key="mod_file_select"
        )
        
        modification = st.text_area("Instructions", placeholder="Add error handling...", height=100, key="mod_instr")
        
        if st.button("Modify", type="primary", key="btn_mod"):
            with st.spinner("Modifying..."):
                prompt = f"Modify {selected_file}: {modification}"
                try:
                    resp = chat_engine.chat(prompt)
                    if isinstance(resp, tuple):
                        resp = resp[0]
                    st.code(resp)
                except Exception as e:
                    st.error(str(e))

    elif mode == "New File":
        st.caption("Create new file")
        fname = st.text_input("Filename", placeholder="utils/helper.py", key="new_fname")
        desc = st.text_area("Content Description", placeholder="Functions for...", height=100, key="new_fdesc")
        
        if st.button("Create", type="primary", key="btn_create_file"):
            with st.spinner("Creating..."):
                prompt = f"Create file {fname}: {desc}"
                try:
                    resp = chat_engine.chat(prompt)
                    if isinstance(resp, tuple):
                        resp = resp[0]
                    st.code(resp)
                except Exception as e:
                    st.error(str(e))
