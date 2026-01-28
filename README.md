# 🕷️ Code Crawler - Intelligent Codebase Agent

An AI-powered codebase assistant that understands your code and helps you navigate, analyze, and modify it. Built with RAG (Retrieval-Augmented Generation), MCP (Model Context Protocol), and CrewAI multi-agent workflows.

## ✨ Features

### 💬 Chat Mode
- Ask questions about your codebase
- Get explanations of functions, modules, and workflows
- Understand code architecture and data flow

### 🔍 Search Mode (MCP-Powered)
- Regex pattern matching across your entire codebase
- Context-aware search results with surrounding code
- File pattern filtering (glob)

### 🔧 Refactor Mode (MCP-Powered)
- Automated search-and-replace refactorings
- Dry-run preview before applying changes
- Common refactoring patterns built-in

### ✨ Generate Mode (AI-Powered)
- Generate complete features from descriptions
- Follows your codebase's existing patterns
- Includes tests and documentation

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export GOOGLE_API_KEY="your-api-key"
```
Or create a `.env` file:
```
GOOGLE_API_KEY=your-api-key
```

### 3. Run the App
```bash
streamlit run app.py
```

### 4. Use the App
1. Upload a ZIP file of your codebase
2. Click "Process & Index"
3. Start chatting or switch modes!

## 📁 Project Structure

```
Codebase_Agent/
├── app.py                        # Main Streamlit application
│
├── code_chatbot/                 # Core library
│   │
│   │── Core RAG Engine
│   ├── rag.py                   # Chat engine with RAG
│   ├── prompts.py               # System prompts
│   ├── config.py                # Centralized configuration
│   │
│   │── Indexing & Chunking
│   ├── indexer.py               # Vector database indexing
│   ├── chunker.py               # AST-aware code chunking
│   ├── merkle_tree.py           # Incremental change detection
│   ├── incremental_indexing.py  # Incremental indexing logic
│   ├── indexing_progress.py     # Progress tracking UI
│   ├── path_obfuscator.py       # Privacy-preserving paths
│   │
│   │── Retrieval
│   ├── retriever_wrapper.py     # Enhanced retriever
│   ├── llm_retriever.py         # LLM-based retrieval
│   ├── reranker.py              # Result reranking
│   ├── graph_rag.py             # Graph-enhanced RAG
│   │
│   │── Code Analysis
│   ├── ast_analysis.py          # AST parsing & call graphs
│   ├── code_symbols.py          # Symbol extraction
│   │
│   │── MCP Tools
│   ├── mcp_server.py            # MCP server (search, refactor)
│   ├── mcp_client.py            # MCP client interface
│   │
│   │── Multi-Agent (CrewAI)
│   ├── agents/                  # Agent definitions
│   ├── crews/                   # Crew workflows
│   ├── agent_workflow.py        # Agent orchestration
│   ├── tools.py                 # Agent tools
│   │
│   │── Utilities
│   ├── universal_ingestor.py    # File ingestion (ZIP, GitHub, Web)
│   └── rate_limiter.py          # API rate limiting
│
├── components/                   # Streamlit UI components
│   └── multi_mode.py            # Mode selector & interfaces
│
├── api/                          # FastAPI REST endpoints
│   ├── main.py                  # API entry point
│   ├── routes/                  # Route handlers
│   └── schemas.py               # Pydantic models
│
├── docs/                         # Documentation
│   └── RAG_PIPELINE.md          # Technical documentation
│
├── tests/                        # Test suite
│
└── assets/                       # Static assets (logo, etc.)
```

## 🔧 Configuration

All configuration is centralized in `code_chatbot/config.py`:

```python
from code_chatbot.config import get_default_config

config = get_default_config()
print(config.chunking.max_chunk_size)  # 1000
print(config.retrieval.top_k)          # 10
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **UI** | Streamlit |
| **LLM** | Google Gemini |
| **Embeddings** | gemini-embedding-001 |
| **Vector DB** | ChromaDB / FAISS / Qdrant |
| **RAG** | LangChain |
| **Agents** | CrewAI |
| **Code Tools** | MCP (Model Context Protocol) |

## 📖 Documentation

- [RAG Pipeline](docs/RAG_PIPELINE.md) - Technical deep-dive

## 📄 License

Apache 2.0 - See [LICENSE](LICENSE)
