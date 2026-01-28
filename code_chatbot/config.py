"""
Configuration system for RAG pipeline.

Centralizes all configuration options for chunking, indexing, retrieval,
and privacy features. Loads from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


@dataclass
class ChunkingConfig:
    """Configuration for code chunking."""
    
    max_chunk_tokens: int = 800
    """Maximum tokens per chunk"""
    
    min_chunk_tokens: int = 100
    """Minimum tokens per chunk (for merging small chunks)"""
    
    preserve_imports: bool = True
    """Include relevant import statements with chunks"""
    
    include_parent_context: bool = True
    """Include parent class/module name in chunk metadata"""
    
    calculate_complexity: bool = True
    """Calculate cyclomatic complexity for chunks"""
    
    @classmethod
    def from_env(cls) -> 'ChunkingConfig':
        """Load configuration from environment variables."""
        return cls(
            max_chunk_tokens=int(os.getenv('CHUNK_MAX_TOKENS', '800')),
            min_chunk_tokens=int(os.getenv('CHUNK_MIN_TOKENS', '100')),
            preserve_imports=os.getenv('CHUNK_PRESERVE_IMPORTS', 'true').lower() == 'true',
            include_parent_context=os.getenv('CHUNK_PARENT_CONTEXT', 'true').lower() == 'true',
            calculate_complexity=os.getenv('CHUNK_CALCULATE_COMPLEXITY', 'true').lower() == 'true',
        )


@dataclass
class PrivacyConfig:
    """Configuration for privacy features."""
    
    enable_path_obfuscation: bool = False
    """Enable file path obfuscation for sensitive codebases"""
    
    obfuscation_key: Optional[str] = None
    """Secret key for path obfuscation (auto-generated if not provided)"""
    
    obfuscation_mapping_file: str = "chroma_db/.path_mapping.json"
    """File to store path obfuscation mappings"""
    
    @classmethod
    def from_env(cls) -> 'PrivacyConfig':
        """Load configuration from environment variables."""
        return cls(
            enable_path_obfuscation=os.getenv('ENABLE_PATH_OBFUSCATION', 'false').lower() == 'true',
            obfuscation_key=os.getenv('PATH_OBFUSCATION_KEY'),
            obfuscation_mapping_file=os.getenv('PATH_MAPPING_FILE', 'chroma_db/.path_mapping.json'),
        )


@dataclass
class IndexingConfig:
    """Configuration for indexing operations."""
    
    enable_incremental_indexing: bool = True
    """Use Merkle tree for incremental indexing"""
    
    merkle_snapshot_dir: str = "chroma_db/merkle_snapshots"
    """Directory to store Merkle tree snapshots"""
    
    batch_size: int = 100
    """Number of documents to process in each batch"""
    
    ignore_patterns: List[str] = field(default_factory=lambda: [
        '*.pyc', '__pycache__/*', '.git/*', 'node_modules/*',
        '.venv/*', 'venv/*', '*.egg-info/*', 'dist/*', 'build/*'
    ])
    """File patterns to ignore during indexing"""
    
    max_file_size_mb: int = 10
    """Maximum file size to index (in MB)"""
    
    @classmethod
    def from_env(cls) -> 'IndexingConfig':
        """Load configuration from environment variables."""
        ignore_patterns_str = os.getenv('INDEXING_IGNORE_PATTERNS', '')
        ignore_patterns = ignore_patterns_str.split(',') if ignore_patterns_str else cls().ignore_patterns
        
        return cls(
            enable_incremental_indexing=os.getenv('ENABLE_INCREMENTAL_INDEXING', 'true').lower() == 'true',
            merkle_snapshot_dir=os.getenv('MERKLE_SNAPSHOT_DIR', 'chroma_db/merkle_snapshots'),
            batch_size=int(os.getenv('INDEXING_BATCH_SIZE', '100')),
            ignore_patterns=ignore_patterns,
            max_file_size_mb=int(os.getenv('MAX_FILE_SIZE_MB', '10')),
        )


@dataclass
class RetrievalConfig:
    """Configuration for retrieval operations."""
    
    enable_reranking: bool = True
    """Apply reranking to retrieval results"""
    
    retrieval_k: int = 10
    """Number of documents to retrieve from vector store"""
    
    rerank_top_k: int = 5
    """Number of top documents to return after reranking"""
    
    enable_multi_query: bool = False
    """Use multi-query retriever for query expansion"""
    
    enable_metadata_filtering: bool = True
    """Enable filtering by metadata (language, type, etc.)"""
    
    similarity_threshold: float = 0.5
    """Minimum similarity score for retrieval"""
    
    @classmethod
    def from_env(cls) -> 'RetrievalConfig':
        """Load configuration from environment variables."""
        return cls(
            enable_reranking=os.getenv('ENABLE_RERANKING', 'true').lower() == 'true',
            retrieval_k=int(os.getenv('RETRIEVAL_K', '10')),
            rerank_top_k=int(os.getenv('RERANK_TOP_K', '5')),
            enable_multi_query=os.getenv('ENABLE_MULTI_QUERY', 'false').lower() == 'true',
            enable_metadata_filtering=os.getenv('ENABLE_METADATA_FILTERING', 'true').lower() == 'true',
            similarity_threshold=float(os.getenv('SIMILARITY_THRESHOLD', '0.5')),
        )


@dataclass
class RAGConfig:
    """
    Complete RAG pipeline configuration.
    
    This is the main configuration class that combines all sub-configurations.
    """
    
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    indexing: IndexingConfig = field(default_factory=IndexingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    
    # General settings
    persist_directory: str = "chroma_db"
    """Directory for vector database persistence"""
    
    embedding_provider: str = "gemini"
    """Embedding provider: 'gemini', 'openai', 'huggingface'"""
    
    embedding_model: str = "models/embedding-001"
    """Embedding model name"""
    
    llm_provider: str = "gemini"
    """LLM provider for chat: 'gemini', 'groq', 'openai'"""
    
    llm_model: str = "gemini-2.0-flash-exp"
    """LLM model name"""
    
    log_level: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR"""
    
    @classmethod
    def from_env(cls) -> 'RAGConfig':
        """
        Load complete configuration from environment variables.
        
        Returns:
            RAGConfig instance with all settings loaded
        """
        return cls(
            chunking=ChunkingConfig.from_env(),
            privacy=PrivacyConfig.from_env(),
            indexing=IndexingConfig.from_env(),
            retrieval=RetrievalConfig.from_env(),
            persist_directory=os.getenv('PERSIST_DIRECTORY', 'chroma_db'),
            embedding_provider=os.getenv('EMBEDDING_PROVIDER', 'gemini'),
            embedding_model=os.getenv('EMBEDDING_MODEL', 'models/embedding-001'),
            llm_provider=os.getenv('LLM_PROVIDER', 'gemini'),
            llm_model=os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
        )
    
    def validate(self) -> List[str]:
        """
        Validate configuration settings.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Chunking validation
        if self.chunking.max_chunk_tokens < self.chunking.min_chunk_tokens:
            errors.append("max_chunk_tokens must be >= min_chunk_tokens")
        
        if self.chunking.max_chunk_tokens > 8000:
            errors.append("max_chunk_tokens should not exceed 8000 (model context limits)")
        
        # Privacy validation
        if self.privacy.enable_path_obfuscation and not self.privacy.obfuscation_key:
            errors.append("obfuscation_key required when path obfuscation is enabled")
        
        # Indexing validation
        if self.indexing.batch_size < 1:
            errors.append("batch_size must be at least 1")
        
        if self.indexing.max_file_size_mb < 1:
            errors.append("max_file_size_mb must be at least 1")
        
        # Retrieval validation
        if self.retrieval.retrieval_k < self.retrieval.rerank_top_k:
            errors.append("retrieval_k must be >= rerank_top_k")
        
        if not 0.0 <= self.retrieval.similarity_threshold <= 1.0:
            errors.append("similarity_threshold must be between 0.0 and 1.0")
        
        # Provider validation
        valid_embedding_providers = ['gemini', 'openai', 'huggingface']
        if self.embedding_provider not in valid_embedding_providers:
            errors.append(f"embedding_provider must be one of: {valid_embedding_providers}")
        
        valid_llm_providers = ['gemini', 'groq', 'openai']
        if self.llm_provider not in valid_llm_providers:
            errors.append(f"llm_provider must be one of: {valid_llm_providers}")
        
        return errors
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.indexing.merkle_snapshot_dir).mkdir(parents=True, exist_ok=True)
        
        # Create parent directory for path mapping file
        if self.privacy.enable_path_obfuscation:
            Path(self.privacy.obfuscation_mapping_file).parent.mkdir(parents=True, exist_ok=True)
    
    def summary(self) -> str:
        """Get a human-readable summary of the configuration."""
        return f"""
RAG Configuration Summary:
==========================
Chunking:
  - Max tokens: {self.chunking.max_chunk_tokens}
  - Min tokens: {self.chunking.min_chunk_tokens}
  - Preserve imports: {self.chunking.preserve_imports}
  - Calculate complexity: {self.chunking.calculate_complexity}

Privacy:
  - Path obfuscation: {self.privacy.enable_path_obfuscation}

Indexing:
  - Incremental indexing: {self.indexing.enable_incremental_indexing}
  - Batch size: {self.indexing.batch_size}
  - Max file size: {self.indexing.max_file_size_mb} MB

Retrieval:
  - Reranking: {self.retrieval.enable_reranking}
  - Retrieval K: {self.retrieval.retrieval_k}
  - Rerank top K: {self.retrieval.rerank_top_k}
  - Multi-query: {self.retrieval.enable_multi_query}

Providers:
  - Embeddings: {self.embedding_provider} ({self.embedding_model})
  - LLM: {self.llm_provider} ({self.llm_model})
  - Persist dir: {self.persist_directory}
""".strip()


# Global configuration instance
_config: Optional[RAGConfig] = None


def get_config() -> RAGConfig:
    """
    Get the global RAG configuration instance.
    
    Loads from environment on first call, then returns cached instance.
    
    Returns:
        RAGConfig instance
    """
    global _config
    
    if _config is None:
        _config = RAGConfig.from_env()
        _config.ensure_directories()
        
        # Validate configuration
        errors = _config.validate()
        if errors:
            raise ValueError(f"Invalid configuration:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return _config


def reset_config():
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
