"""
💬 Chat Page - Chat with your codebase
"""
import streamlit as st
import os
from components.style import apply_custom_css

st.set_page_config(page_title="Chat | Code Crawler", page_icon="💬", layout="wide")
apply_custom_css()

# Check if codebase is indexed
if not st.session_state.get("processed_files"):
    st.warning("⚠️ No codebase indexed yet. Go to **Home** to upload and index a codebase.")
    st.stop()

chat_engine = st.session_state.get("chat_engine")
if not chat_engine:
    st.error("Chat engine not initialized. Please re-index your codebase.")
    st.stop()

st.title("💬 Chat with Your Codebase")

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Suggestion buttons (only if no messages)
if not st.session_state.messages:
    st.markdown("### 💡 Try asking:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Explain project structure", use_container_width=True):
            st.session_state.pending_prompt = "Explain the project structure and main components"
            st.rerun()
        if st.button("⚡ Generate utility function", use_container_width=True):
            st.session_state.pending_prompt = "Generate a new utility function for this project"
            st.rerun()
    with col2:
        if st.button("📝 List main functions", use_container_width=True):
            st.session_state.pending_prompt = "List all the main functions and their purpose"
            st.rerun()
        if st.button("🔧 Suggest improvements", use_container_width=True):
            st.session_state.pending_prompt = "What improvements would you suggest for this code?"
            st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Render Sources if available
        if "sources" in message and message["sources"]:
            unique_sources = {}
            for s in message["sources"]:
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
        
        st.markdown(message["content"])

# Handle pending prompt from suggestion buttons
prompt = st.session_state.pop("pending_prompt", None)

# Chat input
if user_input := st.chat_input("Ask about your code..."):
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
                # Revert to blocking chat for stability
                answer_payload = chat_engine.chat(prompt)
                
                # Handle response format
                if isinstance(answer_payload, tuple):
                    response, sources = answer_payload
                else:
                    response = answer_payload
                    sources = []
                
                # Render sources
                if sources:
                    unique_sources = {}
                    for s in sources:
                        fp = s.get('file_path', 'Unknown')
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
                
                st.markdown(response)
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "sources": sources
                })
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

