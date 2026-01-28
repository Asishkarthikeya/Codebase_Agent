#!/usr/bin/env python3
"""
Quick integration script for multi-mode interface.

This script will help you integrate the multi-mode interface into app.py.
"""

import sys

def show_integration_steps():
    """Display integration steps"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                  Multi-Mode Interface Integration                        ║
╚══════════════════════════════════════════════════════════════════════════╝

✅ Components Created:
   - components/multi_mode.py (Chat, Search, Refactor, Generate modes)
   - Verified imports work correctly

📋 Integration Steps:

STEP 1: Add Import to app.py
────────────────────────────────────────────────────────────────────────────
Add this import after line 11 in app.py:

    from components.multi_mode import (
        render_mode_selector,
        render_chat_mode,
        render_search_mode,
        render_refactor_mode,
        render_generate_mode
    )


STEP 2: Add Mode Selector
────────────────────────────────────────────────────────────────────────────
Replace lines 489-491 in app.py with:

    # Main Chat Interface
    st.title("🕷️ Code Crawler")
    
    # Multi-Mode Interface
    if st.session_state.processed_files:
        selected_mode = render_mode_selector()
        st.divider()
        
        # Render appropriate interface based on mode
        if selected_mode == "search":
            render_search_mode()
        elif selected_mode == "refactor":
            render_refactor_mode()
        elif selected_mode == "generate":
            render_generate_mode(st.session_state.chat_engine)
        else:  # chat mode
            render_chat_mode(st.session_state.chat_engine)
            st.caption(f"Ask questions about your uploaded project. (Using {provider}, Enhanced with AST)")
    else:
        st.caption(f"Configure and index your codebase to get started. (Using {provider}, Enhanced with AST)")


STEP 3: Wrap Chat Interface
────────────────────────────────────────────────────────────────────────────
Add this check before line 526 (before "# Display History"):

    # Only show chat history in chat mode
    selected_mode = st.session_state.get("mode_selector", "💬 Chat")
    if selected_mode == "💬 Chat":


And indent all the chat code (lines 526-614) by 4 spaces.


STEP 4: Test the Integration
────────────────────────────────────────────────────────────────────────────
Run your Streamlit app:

    streamlit run app.py

You should see:
✅ Mode selector with 4 buttons: 💬 Chat | 🔍 Search | 🔧 Refactor | ✨ Generate
✅ Chat mode works as before
✅ Search mode shows MCP code search interface
✅ Refactor mode shows MCP refactoring interface
✅ Generate mode shows CrewAI feature generation interface


🎯 Quick Test Commands:
────────────────────────────────────────────────────────────────────────────
1. Chat Mode: Ask "Explain how authentication works"
2. Search Mode: Pattern "class\\s+(\\w+)", File Pattern "**/*.py"
3. Refactor Mode: Search "print\\((.*)\)", Replace "logger.info(\\1)", Dry Run ✓
4. Generate Mode: "Create a REST API endpoint for user management"


📚 Documentation:
────────────────────────────────────────────────────────────────────────────
See the walkthrough for detailed usage:
    multimode_walkthrough.md


💡 Need Help?
────────────────────────────────────────────────────────────────────────────
If you encounter issues:
1. Check that components/multi_mode.py exists
2. Verify imports work: python3 -c "from components.multi_mode import render_mode_selector"
3. Check Streamlit logs for errors
4. Ensure MCP and CrewAI dependencies are installed

""")

if __name__ == "__main__":
    show_integration_steps()
