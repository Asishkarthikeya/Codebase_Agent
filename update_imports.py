import os
import re

# Mapping of old imports to new imports
# Format: "old_module": "new_module"
# We'll use regex to match "from old_module" and "import old_module"
replacements = {
    # Services
    "code_chatbot.ast_analysis": "backend.app.services.ast_analysis",
    "code_chatbot.rag": "backend.app.services.rag_engine",
    "code_chatbot.indexer": "backend.app.services.indexer",
    "code_chatbot.agent_workflow": "backend.app.services.agent_workflow",
    "code_chatbot.llm_retriever": "backend.app.services.llm_retriever",
    "code_chatbot.graph_rag": "backend.app.services.graph_rag",
    "code_chatbot.db_connection": "backend.app.services.db_connection",
    "code_chatbot.mcp_server": "backend.app.services.mcp_server",
    "code_chatbot.mcp_client": "backend.app.services.mcp_client",
    
    # Utils
    "code_chatbot.chunker": "backend.app.utils.chunking",
    "code_chatbot.tools": "backend.app.utils.tools",
    "code_chatbot.universal_ingestor": "backend.app.utils.universal_ingestor",
    "code_chatbot.rate_limiter": "backend.app.utils.rate_limiter",
    "code_chatbot.prompts": "backend.app.utils.prompts",
    "code_chatbot.path_obfuscator": "backend.app.utils.path_obfuscator",
    "code_chatbot.merkle_tree": "backend.app.utils.merkle_tree",
    "code_chatbot.indexing_progress": "backend.app.utils.indexing_progress",
    "code_chatbot.reranker": "backend.app.utils.reranker",
    "code_chatbot.retriever_wrapper": "backend.app.utils.retriever_wrapper",
    
    # Models
    "code_chatbot.code_symbols": "backend.app.models.code_symbols",
    
    # Config
    "code_chatbot.config": "backend.app.config",
    
    # Routers - careful with regex here
    "api.routes.chat": "backend.app.routers.chat",
    "api.routes.health": "backend.app.routers.health",
    "api.routes.index": "backend.app.routers.index",
    
    # Catch-all for other api/code_chatbot imports if any remain
    # "code_chatbot": "backend.app", # Too risky? Maybe specific modules first
    
    # Internal Relative Imports Fix (harder, but let's try absolute first)
}

# Directories to scan
scan_dirs = ["backend/app", "tests"] 
if os.path.exists("app.py"):
    scan_dirs.append("app.py")

for root_path in scan_dirs:
    if os.path.isfile(root_path):
        files = [root_path]
        root = os.path.dirname(root_path)
    else:
        files = []
        for r, d, f in os.walk(root_path):
            for file in f:
                if file.endswith(".py"):
                    files.append(os.path.join(r, file))

    for file_path in files:
        with open(file_path, "r") as f:
            content = f.read()
        
        original_content = content
        
        for old, new in replacements.items():
            # Replace "from X import Y"
            content = re.sub(f"from {old}([ .])", f"from {new}\\1", content)
            content = re.sub(f"from {old}$", f"from {new}", content) # End of line
            
            # Replace "import X"
            content = re.sub(f"import {old}([ .])", f"import {new}\\1", content)
            content = re.sub(f"import {old}$", f"import {new}", content)
            
        if content != original_content:
            print(f"Updating imports in {file_path}")
            with open(file_path, "w") as f:
                f.write(content)

print("Import update script completed.")
