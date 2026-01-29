"""
✨ Generate Page - Generate and modify code
"""
import streamlit as st
from components.style import apply_custom_css

st.set_page_config(page_title="Generate | Code Crawler", page_icon="✨", layout="wide")
apply_custom_css()

# Check if codebase is indexed
if not st.session_state.get("processed_files"):
    st.warning("⚠️ No codebase indexed yet. Go to **Home** to upload and index a codebase.")
    st.stop()

chat_engine = st.session_state.get("chat_engine")
if not chat_engine:
    st.error("Chat engine not initialized. Please re-index your codebase.")
    st.stop()

st.title("✨ Code Generation")
st.caption("Generate new code based on your codebase patterns")

# Generation mode
mode = st.radio(
    "What would you like to do?",
    ["Generate new code", "Modify existing code", "Create a new file"],
    horizontal=True
)

if mode == "Generate new code":
    st.markdown("### Generate New Code")
    
    description = st.text_area(
        "Describe what you want to generate:",
        placeholder="e.g., Create a utility function to validate email addresses",
        height=100
    )
    
    context = st.text_input(
        "Additional context (optional):",
        placeholder="e.g., Should follow the style used in utils.py"
    )
    
    if st.button("✨ Generate", type="primary", disabled=not description):
        with st.spinner("Generating code..."):
            prompt = f"""Generate new code based on this request:

**Request:** {description}

**Additional Context:** {context if context else "None"}

Please generate the code following the patterns and style used in this codebase.
Include comments explaining the code."""
            
            try:
                response = chat_engine.chat(prompt)
                st.markdown("### Generated Code")
                st.markdown(response)
                
                # Copy button
                st.download_button(
                    "📋 Download as file",
                    response,
                    file_name="generated_code.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif mode == "Modify existing code":
    st.markdown("### Modify Existing Code")
    
    # File selector
    indexed_files = st.session_state.get("indexed_files", [])
    selected_file = st.selectbox(
        "Select file to modify:",
        options=indexed_files,
        format_func=lambda x: x.split("/")[-1] if "/" in x else x
    )
    
    modification = st.text_area(
        "Describe the modification:",
        placeholder="e.g., Add error handling to the main function",
        height=100
    )
    
    if st.button("🔧 Modify", type="primary", disabled=not modification):
        with st.spinner("Analyzing and modifying..."):
            prompt = f"""Modify the code in the file '{selected_file}' based on this request:

**Modification Request:** {modification}

Show the modified code with explanations of what changed."""
            
            try:
                response = chat_engine.chat(prompt)
                st.markdown("### Modified Code")
                st.markdown(response)
            except Exception as e:
                st.error(f"Error: {str(e)}")

else:  # Create a new file
    st.markdown("### Create New File")
    
    file_name = st.text_input("File name:", placeholder="e.g., utils/helpers.py")
    
    description = st.text_area(
        "Describe the file's purpose:",
        placeholder="e.g., Utility functions for data validation and formatting",
        height=100
    )
    
    if st.button("📄 Create", type="primary", disabled=not (file_name and description)):
        with st.spinner("Creating file..."):
            prompt = f"""Create a new file named '{file_name}' with the following purpose:

**Purpose:** {description}

Generate complete, production-ready code following the patterns in this codebase.
Include proper imports, docstrings, and error handling."""
            
            try:
                response = chat_engine.chat(prompt)
                st.markdown(f"### {file_name}")
                st.markdown(response)
                
                st.download_button(
                    "📋 Download file",
                    response,
                    file_name=file_name.split("/")[-1] if "/" in file_name else file_name,
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")
