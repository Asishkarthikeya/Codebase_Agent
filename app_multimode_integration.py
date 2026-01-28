"""
Enhanced app.py with multi-mode interface integration.

This file adds the mode selector and conditional rendering.
Add this code after line 520 in app.py (after the caption).
"""

# Add this import at the top of app.py (around line 11)
# from components.multi_mode import render_mode_selector, render_chat_mode, render_search_mode, render_refactor_mode, render_generate_mode

# Replace lines 523-615 with this code:

if not st.session_state.processed_files:
    st.info("👈 Please upload and index a ZIP file to start.")
else:
    # Get selected mode (defaults to chat)
    selected_mode = st.session_state.get("mode_selector", "💬 Chat")
    
    # Only render chat interface in chat mode
    if selected_mode == "💬 Chat":
        # Display History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                # Render Sources if available
                if "sources" in msg and msg["sources"]:
                    unique_sources = {}
                    for s in msg["sources"]:
                        if isinstance(s, dict):
                            fp = s.get('file_path', 'Unknown')
                        else:
                            fp = str(s)
                        if fp not in unique_sources:
                            unique_sources[fp] = s

                    chips_html = '<div class="source-container" style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;">'
                    for fp in unique_sources:
                        basename = os.path.basename(fp) if "/" in fp else fp
                        chips_html += f"""
                        <div class="source-chip" style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 6px; padding: 4px 10px; font-size: 0.85em; color: #cbd5e1; display: flex; align-items: center; gap: 6px;">
                            <span class="source-icon">📄</span> {basename}
                        </div>
                        """
                    chips_html += '</div>'
                    st.markdown(chips_html, unsafe_allow_html=True)
                
                st.markdown(msg["content"], unsafe_allow_html=True)

        # Handle pending prompt from suggestions
        if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
            prompt = st.session_state.pending_prompt
            st.session_state.pending_prompt = None
        else:
            prompt = st.chat_input("How does the authentication work?")
        
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if st.session_state.chat_engine:
                    with st.spinner("Analyzing (Graph+Vector)..."):
                        answer_payload = st.session_state.chat_engine.chat(prompt)
                        
                        if isinstance(answer_payload, tuple):
                            answer, sources = answer_payload
                        else:
                            answer = answer_payload
                            sources = []
                            
                        if sources:
                            unique_sources = {}
                            for s in sources:
                                fp = s.get('file_path', 'Unknown')
                                if fp not in unique_sources:
                                    unique_sources[fp] = s
                            
                            chips_html = '<div class="source-container">'
                            for fp in unique_sources:
                                basename = os.path.basename(fp) 
                                chips_html += f"""
                                <div class="source-chip">
                                    <span class="source-icon">📄</span> {basename}
                                </div>
                                """
                            chips_html += '</div>'
                            st.markdown(chips_html, unsafe_allow_html=True)

                        st.markdown(answer)
                        
                        msg_data = {
                            "role": "assistant", 
                            "content": answer,
                            "sources": sources if sources else []
                        }
                        st.session_state.messages.append(msg_data)
                else:
                    st.error("Chat engine not initialized. Please re-index.")
