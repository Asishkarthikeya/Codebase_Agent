# Codebase Agent 🕷️

**Codebase Agent** is an intelligent, local-first code analysis tool that helps you understand, navigate, and query your codebase using advanced AI agents.

Think of it as a private, super-powered developer assistant that knows your code inside out.

![Screenshot](assets/logo.png)

## ✨ Key Features

- **🛡️ 100% Local option**: Run with Ollama + local embeddings for complete privacy.
- **🧠 Agentic Reasoning**: Uses AST (Abstract Syntax Tree) analysis and Call Graphs to trace execution and dependencies.
- **🕸️ Call Graph Navigation**: Ask questions like "Who calls `database.connect`?" or "What acts as the entry point?".
- **⚡ Multiple Providers**: Support for **Google Gemini** (1M+ context), **Groq** (fast inference), and standard OpenAI-compatible APIs.
- **📂 Universal Ingestion**: Upload ZIP files or point to GitHub repositories.

## 🚀 Advanced Features (Cursor-Inspired)

- **🔄 Incremental Indexing**: Merkle tree-based change detection for 10-100x faster re-indexing
- **🔒 Privacy-Preserving**: Optional HMAC-based path obfuscation for sensitive codebases
- **🧩 Semantic Chunking**: AST-based code splitting that respects function/class boundaries
- **📊 Rich Metadata**: Automatic extraction of symbols, imports, and cyclomatic complexity
- **🎯 Hybrid Search**: Combines semantic similarity with keyword matching
- **⚙️ Highly Configurable**: Fine-tune chunking, retrieval, and privacy settings

**[📖 Read the Technical Deep-Dive](docs/RAG_PIPELINE.md)** to understand how our RAG pipeline works.

## 🚀 Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Asishkarthikeya/Codebase_Agent.git
   cd Codebase_Agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Upload & Chat**:
   - Open `http://localhost:8501`
   - Enter your API Key (e.g., Gemini or Groq) in the sidebar
   - Upload a `.zip` of your code or provide a GitHub URL
   - Start chatting!

## 🔧 Configuration

The agent creates a `.env` file for your configuration, but you can also set these environment variables manually:

- `GOOGLE_API_KEY`: For Gemini models
- `GROQ_API_KEY`: For Groq models
- `QDRANT_API_KEY`: For Qdrant vector DB

## 🤖 Agent Credentials

This project uses:
- **Streamlit** for the UI
- **LangChain** for orchestration
- **ChromaDB** for vector storage
- **NetworkX** for code graph analysis
- **Tree-sitter** for robust parsing

## License

MIT License. See [LICENSE](LICENSE) for details.
