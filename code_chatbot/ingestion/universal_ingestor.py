"""Universal ingestor that handles multiple input types: ZIP files, GitHub URLs, local directories, etc."""

import logging
import os
import zipfile
import requests
import tempfile
import shutil
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Tuple, Optional
from urllib.parse import urlparse
from pathlib import Path

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class DataManager(ABC):
    """Abstract base class for data managers."""
    
    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
    
    @abstractmethod
    def download(self) -> bool:
        """Downloads/prepares the data."""
        pass
    
    @abstractmethod
    def walk(self, get_content: bool = True) -> Generator[Tuple[Any, Dict], None, None]:
        """Yields (content, metadata) tuples for each file."""
        pass


class UniversalIngestor(DataManager):
    """Factory class to ingest data from various sources."""
    
    def __init__(self, source: str, local_dir: Optional[str] = None, **kwargs):
        """
        Args:
            source: Can be:
                - GitHub URL (e.g., "https://github.com/owner/repo")
                - GitHub repo ID (e.g., "owner/repo")
                - Local directory path
                - ZIP file path
                - Web URL
            local_dir: Directory to store/clone/download data
            **kwargs: Additional arguments for specific managers
        """
        super().__init__(dataset_id=source)
        self.source = source
        self.kwargs = kwargs
        self.local_dir = local_dir or os.path.join(tempfile.gettempdir(), "code_chatbot")
        self.delegate = self._detect_handler()
    
    
    def _detect_handler(self) -> DataManager:
        """Detects the type of input and returns the appropriate handler."""
        # Aggressive cleaning: strip whitespace, backslashes, and trailing slashes
        # FIXED: Use rstrip for slashes/backslashes to avoid stripping leading '/' from absolute paths like /tmp/file.zip
        source = self.source.strip().rstrip('\\').rstrip('/')
        
        # Smart Extraction: If input looks like garbage (has spaces, long text), try to find a URL inside it
        if "github.com" in source and (" " in source or "\n" in source or "Error" in source):
            import re
            # Regex to find https://github.com/owner/repo
            match = re.search(r'(https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_\-\.]+)', source)
            if match:
                logger.info(f"Extracted GitHub URL from text: {match.group(1)}")
                source = match.group(1).strip().strip('\\').strip('/')
        
        # Check if it's a URL
        if self._is_url(source):
            if "github.com" in source or (source.count("/") == 1 and "/" in source):
                # GitHub URL or repo ID (owner/repo)
                if "github.com" in source:
                    # Remove .git suffix if present
                    if source.endswith(".git"):
                        source = source[:-4]
                        
                    # Extract repo_id from URL
                    parts = urlparse(source).path.strip("/").split("/")
                    # Handle cases like https://github.com/owner/repo/tree/main/...
                    if len(parts) >= 2:
                        repo_id = f"{parts[0]}/{parts[1]}"
                    else:
                        raise ValueError(f"Invalid GitHub URL: {source}")
                else:
                    # Assume it's owner/repo format
                    repo_id = source
                
                return GitHubRepoManager(
                    repo_id=repo_id,
                    local_dir=self.local_dir,
                    **self.kwargs
                )
            
            # Other web URLs
            return WebDocManager(source, local_dir=self.local_dir)
        
        # Check if it's a ZIP file
        if source.lower().endswith('.zip') and os.path.isfile(source):
            return ZIPFileManager(source, local_dir=self.local_dir)
        
        # Check if it's a local directory
        if os.path.isdir(source):
            return LocalDirectoryManager(source)
        
        # Check if it's a local file
        if os.path.isfile(source):
            return LocalFileManager(source)
        
        raise ValueError(f"Unable to determine source type for: {source}")
    
    def _is_url(self, s: str) -> bool:
        """Checks if a string is a URL."""
        try:
            result = urlparse(s)
            return bool(result.scheme and result.netloc)
        except Exception:
            # Check if it looks like owner/repo (GitHub format)
            if "/" in s and s.count("/") == 1 and not os.path.exists(s):
                return True
            return False
    
    @property
    def local_path(self) -> str:
        """Returns the local path where data is stored."""
        if hasattr(self.delegate, "local_path"):
            return self.delegate.local_path
        if hasattr(self.delegate, "path"):
            return self.delegate.path
        return self.local_dir
    
    def download(self) -> bool:
        """Downloads/prepares the data."""
        success = self.delegate.download()
        if success:
            self._clean_extracted_files()
        return success
    
    def _clean_extracted_files(self):
        """Removes unnecessary files/directories from the extracted data."""
        path = self.local_path
        if not os.path.exists(path):
            return
            
        logger.info(f"Cleaning execution artifacts from {path}")
        
        # Directories to remove completely
        DIRS_TO_REMOVE = {'.git', '__pycache__', 'node_modules', '.ipynb_checkpoints', '.pytest_cache', '.dart_tool'}
        
        # Files to remove
        FILES_TO_REMOVE = {'.DS_Store', 'Thumbs.db', '.gitignore', '.gitattributes'}
        
        for root, dirs, files in os.walk(path, topdown=False):
            # Remove directories
            for name in dirs:
                if name in DIRS_TO_REMOVE:
                    dir_path = os.path.join(root, name)
                    try:
                        shutil.rmtree(dir_path)
                        logger.info(f"Removed directory: {dir_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {dir_path}: {e}")
            
            # Remove files
            for name in files:
                if name in FILES_TO_REMOVE:
                    file_path = os.path.join(root, name)
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")

    def walk(self, get_content: bool = True) -> Generator[Tuple[Any, Dict], None, None]:
        """Yields (content, metadata) tuples."""
        yield from self.delegate.walk(get_content)


class ZIPFileManager(DataManager):
    """Handles ZIP file ingestion."""
    
    def __init__(self, zip_path: str, local_dir: str):
        super().__init__(dataset_id=zip_path)
        self.zip_path = zip_path
        self.local_dir = local_dir
        self.path = os.path.join(local_dir, "extracted", os.path.basename(zip_path).replace('.zip', ''))
    
    def download(self) -> bool:
        """Extracts the ZIP file."""
        if os.path.exists(self.path):
            logger.info(f"ZIP already extracted to {self.path}")
            return True
        
        os.makedirs(self.path, exist_ok=True)
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.path)
            logger.info(f"Extracted {self.zip_path} to {self.path}")
            return True
        except Exception as e:
            logger.error(f"Failed to extract ZIP: {e}")
            return False
    
    def walk(self, get_content: bool = True) -> Generator[Tuple[Any, Dict], None, None]:
        """Walks extracted files."""
        if not os.path.exists(self.path):
            return
        
        IGNORE_DIRS = {'__pycache__', '.git', 'node_modules', 'venv', '.venv', '.env', 'dist', 'build'}
        IGNORE_EXTENSIONS = {
            '.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.mp4', '.mov', 
            '.zip', '.tar', '.gz', '.pdf', '.exe', '.bin', '.pkl', '.npy', '.pt', '.pth',
            '.lock', '.log', '.sqlite3', '.db', '.min.js', '.min.css', '.map', 
            '.graphml', '.xml', '.toml'
        }
        # Files to ignore by exact name (lock files, etc.)
        IGNORE_FILES = {
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock',
            'Pipfile.lock', 'composer.lock', 'Gemfile.lock', 'Cargo.lock'
        }
        
        for root, dirs, files in os.walk(self.path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                # Skip ignored files by name
                if file in IGNORE_FILES:
                    continue
                
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                if ext.lower() in IGNORE_EXTENSIONS:
                    continue
                
                rel_path = os.path.relpath(file_path, self.path)
                
                if get_content:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        yield content, {
                            "file_path": file_path,
                            "source": rel_path,
                            "file_name": file
                        }
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {e}")
                else:
                    yield {"file_path": file_path, "source": rel_path, "file_name": file}


class LocalDirectoryManager(DataManager):
    """Handles local directory ingestion."""
    
    def __init__(self, path: str):
        super().__init__(dataset_id=path)
        self.path = path
        self.local_dir = path
    
    def download(self) -> bool:
        return os.path.isdir(self.path)
    
    def walk(self, get_content: bool = True) -> Generator[Tuple[Any, Dict], None, None]:
        """Walks local directory."""
        IGNORE_DIRS = {'__pycache__', '.git', 'node_modules', 'venv', '.venv', '.env', 'dist', 'build'}
        IGNORE_EXTENSIONS = {
            '.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.mp4', '.mov', 
            '.zip', '.tar', '.gz', '.pdf', '.exe', '.bin', '.pkl', '.npy', '.pt', '.pth',
            '.lock', '.log', '.sqlite3', '.db', '.min.js', '.min.css', '.map', 
            '.graphml', '.xml', '.toml'
        }
        # Files to ignore by exact name (lock files, etc.)
        IGNORE_FILES = {
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock',
            'Pipfile.lock', 'composer.lock', 'Gemfile.lock', 'Cargo.lock'
        }
        
        for root, dirs, files in os.walk(self.path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                # Skip ignored files by name
                if file in IGNORE_FILES:
                    continue
                
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                if ext.lower() in IGNORE_EXTENSIONS:
                    continue
                
                rel_path = os.path.relpath(file_path, self.path)
                
                if get_content:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        yield content, {
                            "file_path": file_path,
                            "source": rel_path,
                            "url": f"file://{file_path}"
                        }
                    except Exception as e:
                        logger.warning(f"Skipping {file_path}: {e}")
                else:
                    yield {"file_path": file_path, "source": rel_path}


class LocalFileManager(DataManager):
    """Handles single file ingestion."""
    
    def __init__(self, path: str):
        super().__init__(dataset_id=path)
        self.path = path
    
    def download(self) -> bool:
        return os.path.exists(self.path)
    
    def walk(self, get_content: bool = True) -> Generator[Tuple[Any, Dict], None, None]:
        """Yields the single file."""
        if get_content:
            try:
                with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                yield content, {"file_path": self.path, "source": os.path.basename(self.path)}
            except Exception as e:
                logger.error(f"Failed to read {self.path}: {e}")
        else:
            yield {"file_path": self.path, "source": os.path.basename(self.path)}


class GitHubRepoManager(DataManager):
    """Handles GitHub repository cloning and ingestion."""
    
    def __init__(self, repo_id: str, local_dir: str, access_token: Optional[str] = None, commit_hash: Optional[str] = None):
        """
        Args:
            repo_id: GitHub repo in format "owner/repo"
            local_dir: Directory to clone to
            access_token: GitHub token for private repos
            commit_hash: Optional commit hash to checkout
        """
        super().__init__(dataset_id=repo_id)
        self.repo_id = repo_id
        self.local_dir = local_dir
        self.access_token = access_token or os.getenv("GITHUB_TOKEN")
        self.commit_hash = commit_hash
        self.path = os.path.join(local_dir, repo_id.replace("/", "_"))
    
    def download(self) -> bool:
        """Clones the GitHub repository. Falls back to HTTP ZIP download if git fails."""
        if os.path.exists(self.path) and os.listdir(self.path):
            logger.info(f"Repo already cloned at {self.path}")
            return True
        
        # Try git clone first
        try:
            from git import Repo, GitCommandError
            
            if self.access_token:
                clone_url = f"https://{self.access_token}@github.com/{self.repo_id}.git"
            else:
                clone_url = f"https://github.com/{self.repo_id}.git"
            
            os.makedirs(self.local_dir, exist_ok=True)
            
            if self.commit_hash:
                repo = Repo.clone_from(clone_url, self.path)
                repo.git.checkout(self.commit_hash)
            else:
                Repo.clone_from(clone_url, self.path, depth=1, single_branch=True)
            
            logger.info(f"Cloned {self.repo_id} to {self.path}")
            return True
        except ImportError:
            logger.warning("GitPython not available, falling back to HTTP download")
        except Exception as e:
            logger.warning(f"Git clone failed: {e}, falling back to HTTP download")
        
        # Fallback: Download as ZIP via GitHub API
        try:
            return self._download_as_zip()
        except Exception as e:
            logger.error(f"Failed to download {self.repo_id}: {e}")
            return False
    
    def _download_as_zip(self) -> bool:
        """Download repo as ZIP from GitHub API (fallback method)."""
        import io
        
        # Download ZIP from GitHub
        zip_url = f"https://github.com/{self.repo_id}/archive/refs/heads/main.zip"
        logger.info(f"Downloading {self.repo_id} as ZIP from {zip_url}")
        
        try:
            response = requests.get(zip_url, timeout=60)
            if response.status_code == 404:
                # Try 'master' branch if 'main' doesn't exist
                zip_url = f"https://github.com/{self.repo_id}/archive/refs/heads/master.zip"
                response = requests.get(zip_url, timeout=60)
            
            response.raise_for_status()
            
            # Extract ZIP
            os.makedirs(self.path, exist_ok=True)
            
            with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zip_ref:
                # Extract to temp location first
                temp_extract = os.path.join(self.local_dir, "_temp_extract")
                zip_ref.extractall(temp_extract)
                
                # GitHub ZIPs have a top-level folder like "repo-main", move contents up
                extracted_items = os.listdir(temp_extract)
                if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract, extracted_items[0])):
                    # Move contents of the single folder to our target path
                    source_dir = os.path.join(temp_extract, extracted_items[0])
                    for item in os.listdir(source_dir):
                        shutil.move(os.path.join(source_dir, item), os.path.join(self.path, item))
                    shutil.rmtree(temp_extract)
                else:
                    # Move all items directly
                    for item in extracted_items:
                        shutil.move(os.path.join(temp_extract, item), os.path.join(self.path, item))
                    shutil.rmtree(temp_extract)
            
            logger.info(f"Downloaded and extracted {self.repo_id} to {self.path}")
            return True
        except Exception as e:
            logger.error(f"HTTP download failed for {self.repo_id}: {e}")
            return False
    
    def walk(self, get_content: bool = True) -> Generator[Tuple[Any, Dict], None, None]:
        """Walks cloned repository."""
        if not os.path.exists(self.path):
            return
        
        # Use LocalDirectoryManager logic
        manager = LocalDirectoryManager(self.path)
        yield from manager.walk(get_content)


class WebDocManager(DataManager):
    """Handles web page/document ingestion."""
    
    def __init__(self, url: str, local_dir: str):
        super().__init__(dataset_id=url)
        self.url = url
        self.local_dir = local_dir
    
    def download(self) -> bool:
        """Checks if URL is accessible."""
        try:
            response = requests.get(self.url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Could not reach {self.url}: {e}")
            return False
    
    def walk(self, get_content: bool = True) -> Generator[Tuple[Any, Dict], None, None]:
        """Fetches web page content."""
        try:
            response = requests.get(self.url, timeout=10)
            if get_content:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text(separator='\n')
                yield text, {"file_path": self.url, "url": self.url, "source": "web"}
            else:
                yield {"file_path": self.url, "url": self.url, "source": "web"}
        except Exception as e:
            logger.error(f"Failed to fetch {self.url}: {e}")


def process_source(source: str, extract_to: str) -> Tuple[list, str]:
    """
    Convenience function to process any source type and return documents + local path.
    
    Returns:
        Tuple of (documents, local_path)
    """
    logger.info(f"Processing source: {source}")
    logger.info(f"Extract destination: {extract_to}")
    
    # Ensure the extraction directory exists
    try:
        os.makedirs(extract_to, exist_ok=True)
        logger.info(f"Created/verified extract directory: {extract_to}")
    except Exception as e:
        logger.error(f"Failed to create extract directory {extract_to}: {e}")
        raise ValueError(f"Cannot create extraction directory: {e}")
    
    try:
        ingestor = UniversalIngestor(source, local_dir=extract_to)
        logger.info(f"Ingestor created with handler: {type(ingestor.delegate).__name__}")
    except Exception as e:
        logger.error(f"Failed to create ingestor: {e}")
        raise ValueError(f"Cannot process source '{source}': {e}")
    
    try:
        if not ingestor.download():
            raise ValueError(f"Failed to download/prepare source: {source}")
        logger.info(f"Download complete. Local path: {ingestor.local_path}")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise ValueError(f"Failed to download/prepare source: {source} - {e}")
    
    documents = []
    try:
        for content, metadata in ingestor.walk(get_content=True):
            documents.append(Document(
                page_content=content,
                metadata=metadata
            ))
        logger.info(f"Ingested {len(documents)} documents")
    except Exception as e:
        logger.error(f"Failed to walk documents: {e}")
        raise ValueError(f"Failed to process files: {e}")
    
    return documents, ingestor.local_path

