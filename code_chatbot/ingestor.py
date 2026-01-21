import os
import zipfile
import tempfile
import shutil
from typing import List, Optional
from langchain_core.documents import Document
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Extensions to ignore (binaries, images, etc.)
IGNORE_EXTENSIONS = {
    '.pyc', '.git', '.github', '.idea', '.vscode', '.DS_Store', 
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', 
    '.mp4', '.mov', '.mp3', '.wav', 
    '.zip', '.tar', '.gz', '.pkl', '.bin', '.exe', '.dll', '.so', '.dylib',
    '.pdf', '.docx', '.xlsx', '.pptx'
}

# Directories to ignore
IGNORE_DIRS = {
    '__pycache__', '.git', '.github', '.idea', '.vscode', 'node_modules', 'venv', '.venv', 'env', '.env', 'dist', 'build', 'target'
}

def is_text_file(file_path: str) -> bool:
    """Check if a file is likely a text file based on extension and content."""
    _, ext = os.path.splitext(file_path)
    if ext.lower() in IGNORE_EXTENSIONS:
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False

def process_zip(zip_path: str, extract_to: str) -> List[Document]:
    """
    Extracts a ZIP file and returns a list of LangChain Documents.
    
    Args:
        zip_path: Path to the uploaded ZIP file.
        extract_to: Directory to extract files to.
        
    Returns:
        List[Document]: List of documents with content and metadata.
    """
    documents = []
    
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
        
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            
        logger.info(f"Extracted {zip_path} to {extract_to}")
        
        # Walk through the extracted files
        for root, dirs, files in os.walk(extract_to):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                
                if is_text_file(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        # Create relative path for metadata
                        rel_path = os.path.relpath(file_path, extract_to)
                        
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": rel_path,
                                "file_path": file_path,
                                "file_name": file
                            }
                        )
                        documents.append(doc)
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {e}")
                        
        logger.info(f"Processed {len(documents)} documents from {zip_path}")
        return documents
        
    except zipfile.BadZipFile:
        logger.error(f"Invalid ZIP file: {zip_path}")
        raise ValueError("The provided file is not a valid ZIP archive.")
    except Exception as e:
        logger.error(f"Error processing ZIP: {e}")
        raise e
