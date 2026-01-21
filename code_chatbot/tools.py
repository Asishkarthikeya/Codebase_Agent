import os
import glob
from typing import List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Define Input Schemas
class ListFilesInput(BaseModel):
    path: str = Field(description="Directory path to list files from. Use '.' for root.")

class ReadFileInput(BaseModel):
    file_path: str = Field(description="Path to the file to read.")

# Define Tools Factory
def get_filesystem_tools(root_dir: str = "."):
    """Returns a list of tools bound to the specified root directory."""
    
    # Ensure root_dir is absolute
    root_dir = os.path.abspath(root_dir)

    @tool("list_files", args_schema=ListFilesInput)
    def list_files(path: str = ".") -> str:
        """Lists files in the specified directory."""
        try:
            # Resolve target path relative to root_dir
            if path == ".":
                target_path = root_dir
            else:
                target_path = os.path.abspath(os.path.join(root_dir, path))
            
            # Security check: ensure we are inside the codebase
            if not target_path.startswith(root_dir):
                return f"Error: Access denied. Path must be within the codebase: {root_dir}"
            
            if not os.path.exists(target_path):
                return f"Error: Path does not exist: {path}"

            files = []
            for item in os.listdir(target_path):
                if item.startswith(".") and item != ".gitignore": continue
                
                full_item_path = os.path.join(target_path, item)
                
                if os.path.isdir(full_item_path):
                    files.append(f"{item}/")
                else:
                    files.append(item)
            
            # Sort for stability
            files.sort()
            return "\n".join(files)
        except Exception as e:
            return f"Error listing files: {e}"

    @tool("read_file", args_schema=ReadFileInput)
    def read_file(file_path: str) -> str:
        """Reads the content of a file."""
        try:
            # Resolve full path
            full_path = os.path.abspath(os.path.join(root_dir, file_path))
            
            # Security check
            if not full_path.startswith(root_dir):
                return "Error: Access denied. File must be within the codebase."
            
            if not os.path.exists(full_path):
                 return f"Error: File not found: {file_path}"

            # Check file size to avoid overloading context
            # Groq TPM limit is ~12k tokens. 12000 chars is roughly 3k tokens.
            # We strictly prevent reading massive files to keep the agent alive.
            if os.path.getsize(full_path) > 12000:
                 return f"Error: File '{file_path}' is too large ({os.path.getsize(full_path)} bytes). Read specific lines or functions instead."
                 
            with open(full_path, "r", errors='ignore') as f:
                content = f.read()
                return content
        except Exception as e:
            return f"Error reading file: {e}"

    return [list_files, read_file]


# ============================================================================
# Call Graph Tools
# ============================================================================

class FindCallersInput(BaseModel):
    function_name: str = Field(description="Name of the function to find callers for")

class FindCalleesInput(BaseModel):
    function_name: str = Field(description="Name of the function to find callees for")

class FindCallChainInput(BaseModel):
    start_function: str = Field(description="Name of the starting function")
    end_function: str = Field(description="Name of the target function to trace to")


def get_call_graph_tools(analyzer):
    """Returns tools for querying the call graph."""
    
    @tool("find_callers", args_schema=FindCallersInput)
    def find_callers(function_name: str) -> str:
        """Find all functions that call the specified function.
        Useful for understanding: "Who uses this function?" or "What depends on this?"
        """
        if analyzer is None:
            return "Error: No code analysis available. Index a codebase first."
        
        try:
            callers = analyzer.get_callers(function_name)
            
            if not callers:
                return f"No callers found for '{function_name}'. It may be unused or called dynamically."
            
            result = f"Functions that call '{function_name}':\n"
            for caller in callers:
                parts = caller.split("::")
                if len(parts) == 2:
                    result += f"  - {parts[1]} (in {parts[0]})\n"
                else:
                    result += f"  - {caller}\n"
            
            return result
        except Exception as e:
            return f"Error finding callers: {e}"
    
    @tool("find_callees", args_schema=FindCalleesInput)
    def find_callees(function_name: str) -> str:
        """Find all functions that are called by the specified function.
        Useful for understanding: "What does this function do?" or "What are its dependencies?"
        """
        if analyzer is None:
            return "Error: No code analysis available. Index a codebase first."
        
        try:
            callees = analyzer.get_callees(function_name)
            
            if not callees:
                return f"No callees found for '{function_name}'. It may not call any other tracked functions."
            
            result = f"Functions called by '{function_name}':\n"
            for callee in callees:
                parts = callee.split("::")
                if len(parts) == 2:
                    result += f"  - {parts[1]} (in {parts[0]})\n"
                else:
                    result += f"  - {callee}\n"
            
            return result
        except Exception as e:
            return f"Error finding callees: {e}"
    
    @tool("find_call_chain", args_schema=FindCallChainInput)
    def find_call_chain(start_function: str, end_function: str) -> str:
        """Find the call path from one function to another.
        Useful for: "How does execution flow from main() to save_to_db()?"
        """
        if analyzer is None:
            return "Error: No code analysis available. Index a codebase first."
        
        try:
            chains = analyzer.get_call_chain(start_function, end_function)
            
            if not chains:
                return f"No call path found from '{start_function}' to '{end_function}'."
            
            result = f"Call paths from '{start_function}' to '{end_function}':\n\n"
            for i, chain in enumerate(chains[:5], 1):
                result += f"Path {i}:\n"
                for j, node in enumerate(chain):
                    parts = node.split("::")
                    func_name = parts[1] if len(parts) == 2 else node
                    indent = "  " * j
                    arrow = "-> " if j > 0 else ""
                    result += f"{indent}{arrow}{func_name}\n"
                result += "\n"
            
            return result
        except Exception as e:
            return f"Error finding call chain: {e}"
    
    return [find_callers, find_callees, find_call_chain]
