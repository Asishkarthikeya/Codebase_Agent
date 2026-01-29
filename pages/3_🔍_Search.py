"""
🔍 Search Page - Search across your codebase
"""
import streamlit as st
import os
import re
import re
from pathlib import Path
from components.style import apply_custom_css

st.set_page_config(page_title="Search | Code Crawler", page_icon="🔍", layout="wide")
apply_custom_css()

# Check if codebase is indexed
if not st.session_state.get("processed_files"):
    st.warning("⚠️ No codebase indexed yet. Go to **Home** to upload and index a codebase.")
    st.stop()

indexed_files = st.session_state.get("indexed_files", [])

st.title("🔍 Search Codebase")
st.caption(f"Search across {len(indexed_files)} indexed files")

# Search inputs
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Search pattern", placeholder="Enter search term or regex...")
with col2:
    use_regex = st.checkbox("Use regex", value=False)

# File type filter
file_types = st.multiselect(
    "Filter by file type",
    options=[".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", ".md"],
    default=[]
)

if query and st.button("🔍 Search", type="primary"):
    results = []
    
    try:
        pattern = re.compile(query, re.IGNORECASE) if use_regex else None
    except re.error as e:
        st.error(f"Invalid regex: {e}")
        st.stop()
    
    with st.spinner("Searching..."):
        for file_path in indexed_files:
            # Filter by file type
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
    
    # Display results
    st.markdown(f"### Found {len(results)} matches")
    
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
            with st.expander(f"📄 **{filename}** ({len(matches)} matches)", expanded=True):
                st.caption(file_path)
                for m in matches[:10]:  # Limit to 10 per file
                    st.markdown(f"**Line {m['line_num']}:** `{m['content'][:100]}...`" if len(m['content']) > 100 else f"**Line {m['line_num']}:** `{m['content']}`")
                
                if len(matches) > 10:
                    st.caption(f"... and {len(matches) - 10} more matches")
                
                # Button to view file
                if st.button(f"View {filename}", key=f"view_{file_path}"):
                    st.session_state.selected_file = file_path
                    st.switch_page("pages/1_📁_Explorer.py")
    else:
        st.info("No matches found. Try a different search term.")
