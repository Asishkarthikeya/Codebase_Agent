import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Database, Code, Brain, Search, FileText, GitBranch, Layers, Workflow, Server, Cpu, ArrowRight, Zap } from 'lucide-react';

const ArchitectureViz = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedSections, setExpandedSections] = useState({});

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const tabs = [
    { id: 'overview', label: 'System Overview', icon: Layers },
    { id: 'rag', label: 'RAG Pipeline', icon: Search },
    { id: 'ast', label: 'AST & Graphs', icon: GitBranch },
    { id: 'chunking', label: 'Code Chunking', icon: Code },
    { id: 'agent', label: 'Agentic Workflow', icon: Brain },
    { id: 'retrieval', label: 'Retrieval System', icon: Database },
  ];

  const ComponentCard = ({ title, description, icon: Icon, color, children }) => (
    <div className={`bg-slate-800 rounded-lg p-4 border-l-4 ${color} hover:bg-slate-750 transition-all`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-5 h-5 text-slate-300" />
        <h3 className="font-semibold text-white">{title}</h3>
      </div>
      <p className="text-slate-400 text-sm mb-2">{description}</p>
      {children}
    </div>
  );

  const FlowArrow = () => (
    <div className="flex justify-center py-2">
      <ArrowRight className="w-6 h-6 text-slate-500" />
    </div>
  );

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-xl p-6 border border-purple-500/30">
        <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
          <Zap className="w-6 h-6 text-yellow-400" />
          Code Crawler Architecture
        </h2>
        <p className="text-slate-300">
          An AI-powered codebase assistant combining RAG, AST analysis, Graph databases, and Agentic workflows.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ComponentCard
          title="Data Ingestion"
          description="Universal ingestor supporting ZIP, GitHub, Local, Web"
          icon={FileText}
          color="border-green-500"
        >
          <div className="mt-2 space-y-1">
            <div className="text-xs bg-slate-700 rounded px-2 py-1">ZIPFileManager</div>
            <div className="text-xs bg-slate-700 rounded px-2 py-1">GitHubRepoManager</div>
            <div className="text-xs bg-slate-700 rounded px-2 py-1">LocalDirectoryManager</div>
            <div className="text-xs bg-slate-700 rounded px-2 py-1">WebDocManager</div>
          </div>
        </ComponentCard>

        <ComponentCard
          title="Processing"
          description="AST parsing, chunking, embeddings, graph building"
          icon={Cpu}
          color="border-blue-500"
        >
          <div className="mt-2 space-y-1">
            <div className="text-xs bg-slate-700 rounded px-2 py-1">StructuralChunker (tree-sitter)</div>
            <div className="text-xs bg-slate-700 rounded px-2 py-1">EnhancedCodeAnalyzer</div>
            <div className="text-xs bg-slate-700 rounded px-2 py-1">Gemini/HuggingFace Embeddings</div>
          </div>
        </ComponentCard>

        <ComponentCard
          title="Storage"
          description="Vector DB and AST knowledge graph"
          icon={Database}
          color="border-purple-500"
        >
          <div className="mt-2 space-y-1">
            <div className="text-xs bg-slate-700 rounded px-2 py-1">Chroma / FAISS / Qdrant</div>
            <div className="text-xs bg-slate-700 rounded px-2 py-1">GraphML (NetworkX)</div>
            <div className="text-xs bg-slate-700 rounded px-2 py-1">Merkle Tree Snapshots</div>
          </div>
        </ComponentCard>
      </div>

      <div className="bg-slate-800 rounded-lg p-4">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <Workflow className="w-5 h-5" />
          Data Flow
        </h3>
        <div className="flex flex-wrap items-center justify-center gap-2 text-sm">
          <span className="bg-green-600/30 text-green-300 px-3 py-1 rounded-full">Input Source</span>
          <ArrowRight className="w-4 h-4 text-slate-500" />
          <span className="bg-blue-600/30 text-blue-300 px-3 py-1 rounded-full">Ingestor</span>
          <ArrowRight className="w-4 h-4 text-slate-500" />
          <span className="bg-purple-600/30 text-purple-300 px-3 py-1 rounded-full">Chunker</span>
          <ArrowRight className="w-4 h-4 text-slate-500" />
          <span className="bg-pink-600/30 text-pink-300 px-3 py-1 rounded-full">Embeddings</span>
          <ArrowRight className="w-4 h-4 text-slate-500" />
          <span className="bg-orange-600/30 text-orange-300 px-3 py-1 rounded-full">Vector DB</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ComponentCard
          title="Retrieval Layer"
          description="Multi-stage retrieval with reranking"
          icon={Search}
          color="border-yellow-500"
        >
          <div className="mt-2 text-xs space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
              <span className="text-slate-300">Vector Retriever (60%)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
              <span className="text-slate-300">LLM Retriever (40%)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
              <span className="text-slate-300">Graph Enhancement</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
              <span className="text-slate-300">Cross-Encoder Reranker</span>
            </div>
          </div>
        </ComponentCard>

        <ComponentCard
          title="Chat Engine"
          description="Dual-mode: Linear RAG or Agentic"
          icon={Brain}
          color="border-red-500"
        >
          <div className="mt-2 text-xs space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              <span className="text-slate-300">Linear RAG (simple Q&A)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              <span className="text-slate-300">Agentic Workflow (LangGraph)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              <span className="text-slate-300">Tools: search, read, list, call_graph</span>
            </div>
          </div>
        </ComponentCard>
      </div>
    </div>
  );

  const renderRAG = () => (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">RAG Pipeline Implementation</h2>
        <p className="text-slate-400 mb-4">
          The RAG (Retrieval-Augmented Generation) system combines vector search with LLM-based file selection
          and cross-encoder reranking for high-precision code retrieval.
        </p>

        <div className="space-y-4">
          <div className="bg-slate-700/50 rounded-lg p-4">
            <h3 className="font-semibold text-green-400 mb-2">1. Query Processing</h3>
            <code className="text-sm text-slate-300 block bg-slate-900 p-3 rounded">
              {`query = "How does authentication work?"
# Optionally expand with multi-query
expanded_queries = multi_query_expander(query)`}
            </code>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <h3 className="font-semibold text-blue-400 mb-2">2. Hybrid Retrieval</h3>
            <code className="text-sm text-slate-300 block bg-slate-900 p-3 rounded">
              {`# Vector similarity search (60% weight)
vector_docs = chroma_db.similarity_search(query, k=10)

# LLM-based file selection (40% weight)
llm_docs = llm_retriever.select_files(query, file_tree)

# Combine with EnsembleRetriever
combined = ensemble([vector_docs, llm_docs], weights=[0.6, 0.4])`}
            </code>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <h3 className="font-semibold text-purple-400 mb-2">3. Graph Enhancement</h3>
            <code className="text-sm text-slate-300 block bg-slate-900 p-3 rounded">
              {`# For each retrieved doc, find related files via AST graph
for doc in combined:
    neighbors = ast_graph.neighbors(doc.file_path)
    for neighbor in neighbors:
        if relation == "imports" or relation == "calls":
            augmented_docs.append(read_file(neighbor))`}
            </code>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <h3 className="font-semibold text-yellow-400 mb-2">4. Cross-Encoder Reranking</h3>
            <code className="text-sm text-slate-300 block bg-slate-900 p-3 rounded">
              {`# Score each (query, document) pair with cross-encoder
pairs = [[query, doc.content] for doc in augmented_docs]
scores = cross_encoder.predict(pairs)

# Return top 5 by score
final_docs = sorted(zip(docs, scores), by=score)[:5]`}
            </code>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <h3 className="font-semibold text-red-400 mb-2">5. Generation</h3>
            <code className="text-sm text-slate-300 block bg-slate-900 p-3 rounded">
              {`# Build context from retrieved docs
context = format_docs(final_docs)

# Generate answer with LLM
prompt = system_prompt.format(context=context)
answer = llm.invoke([SystemMessage(prompt), HumanMessage(query)])`}
            </code>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-3">Key Files</h3>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="bg-slate-700 rounded p-2">
            <span className="text-blue-400">code_chatbot/rag.py</span>
            <p className="text-slate-400 text-xs">ChatEngine class</p>
          </div>
          <div className="bg-slate-700 rounded p-2">
            <span className="text-blue-400">code_chatbot/retriever_wrapper.py</span>
            <p className="text-slate-400 text-xs">RerankingRetriever</p>
          </div>
          <div className="bg-slate-700 rounded p-2">
            <span className="text-blue-400">code_chatbot/llm_retriever.py</span>
            <p className="text-slate-400 text-xs">LLM-based file selection</p>
          </div>
          <div className="bg-slate-700 rounded p-2">
            <span className="text-blue-400">code_chatbot/reranker.py</span>
            <p className="text-slate-400 text-xs">Cross-encoder reranking</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAST = () => (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">AST Analysis & Knowledge Graph</h2>
        <p className="text-slate-400 mb-4">
          Uses <span className="text-green-400">tree-sitter</span> to parse code into Abstract Syntax Trees,
          then builds a <span className="text-blue-400">NetworkX</span> directed graph capturing code relationships.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-slate-700/50 rounded-lg p-4">
            <h3 className="font-semibold text-purple-400 mb-2">Node Types</h3>
            <ul className="text-sm text-slate-300 space-y-1">
              <li className="flex items-center gap-2">
                <span className="w-3 h-3 bg-green-500 rounded"></span> file
              </li>
              <li className="flex items-center gap-2">
                <span className="w-3 h-3 bg-blue-500 rounded"></span> class
              </li>
              <li className="flex items-center gap-2">
                <span className="w-3 h-3 bg-purple-500 rounded"></span> function
              </li>
              <li className="flex items-center gap-2">
                <span className="w-3 h-3 bg-yellow-500 rounded"></span> method
              </li>
            </ul>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <h3 className="font-semibold text-purple-400 mb-2">Edge Types (Relations)</h3>
            <ul className="text-sm text-slate-300 space-y-1">
              <li><span className="text-green-400">defines</span> - file → class/function</li>
              <li><span className="text-blue-400">has_method</span> - class → method</li>
              <li><span className="text-purple-400">calls</span> - function → function</li>
              <li><span className="text-yellow-400">imports</span> - file → module</li>
              <li><span className="text-red-400">inherits_from</span> - class → class</li>
            </ul>
          </div>
        </div>

        <div className="bg-slate-900 rounded-lg p-4 overflow-x-auto">
          <h3 className="font-semibold text-white mb-2">Example: Parsing Python Code</h3>
          <pre className="text-sm text-slate-300">
{`# Source Code
class UserService:
    def get_user(self, user_id):
        return self.db.find(user_id)  # calls db.find

# Generated Graph
(file: user_service.py)
    │
    └──defines──▶ (class: UserService)
                      │
                      └──has_method──▶ (method: get_user)
                                           │
                                           └──calls──▶ (function: db.find)`}
          </pre>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-3">Call Graph Tools</h3>
        <div className="space-y-3">
          <div className="bg-slate-700 rounded p-3">
            <code className="text-green-400">find_callers("authenticate")</code>
            <p className="text-slate-400 text-sm mt-1">→ Returns all functions that call authenticate()</p>
          </div>
          <div className="bg-slate-700 rounded p-3">
            <code className="text-blue-400">find_callees("process_request")</code>
            <p className="text-slate-400 text-sm mt-1">→ Returns all functions called by process_request()</p>
          </div>
          <div className="bg-slate-700 rounded p-3">
            <code className="text-purple-400">find_call_chain("main", "save_to_db")</code>
            <p className="text-slate-400 text-sm mt-1">→ Returns execution paths from main() to save_to_db()</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderChunking = () => (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">Structural Code Chunking</h2>
        <p className="text-slate-400 mb-4">
          Unlike naive text splitting, this system uses <span className="text-green-400">tree-sitter</span> to
          chunk code at semantic boundaries (functions, classes) while respecting token limits.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-4">
            <h3 className="font-semibold text-red-400 mb-2">❌ Naive Text Chunking</h3>
            <pre className="text-xs text-slate-300 bg-slate-900 p-2 rounded">
{`def process_data():
    data = load()
    # ──────────────── CHUNK BREAK ────
    result = transform(data)
    return result  # Broken mid-function!`}
            </pre>
          </div>

          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-4">
            <h3 className="font-semibold text-green-400 mb-2">✓ Structural Chunking</h3>
            <pre className="text-xs text-slate-300 bg-slate-900 p-2 rounded">
{`# CHUNK 1 - Complete function
def process_data():
    data = load()
    result = transform(data)
    return result

# CHUNK 2 - Complete function
def another_func():
    ...`}
            </pre>
          </div>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-4">
          <h3 className="font-semibold text-blue-400 mb-2">Chunking Algorithm</h3>
          <ol className="text-sm text-slate-300 space-y-2">
            <li className="flex items-start gap-2">
              <span className="bg-blue-500 text-white w-5 h-5 rounded-full flex items-center justify-center text-xs">1</span>
              <span>Parse file into AST using tree-sitter</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="bg-blue-500 text-white w-5 h-5 rounded-full flex items-center justify-center text-xs">2</span>
              <span>Recursively visit nodes (functions, classes, etc.)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="bg-blue-500 text-white w-5 h-5 rounded-full flex items-center justify-center text-xs">3</span>
              <span>If node fits in max_tokens (800) → return as chunk</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="bg-blue-500 text-white w-5 h-5 rounded-full flex items-center justify-center text-xs">4</span>
              <span>If too large → split into children, recurse</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="bg-blue-500 text-white w-5 h-5 rounded-full flex items-center justify-center text-xs">5</span>
              <span>Merge neighboring small chunks to avoid fragments</span>
            </li>
          </ol>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-3">Rich Chunk Metadata</h3>
        <div className="bg-slate-900 rounded-lg p-4">
          <pre className="text-sm text-slate-300">
{`FileChunk {
  file_path: "src/auth/login.py",
  start_byte: 245,
  end_byte: 892,
  line_range: "L12-L45",
  language: "python",
  chunk_type: "function_definition",
  name: "authenticate",

  // Enhanced metadata
  symbols_defined: ["authenticate", "verify_token"],
  imports_used: ["from jwt import decode"],
  complexity_score: 7,  // Cyclomatic complexity
  parent_context: "AuthService"  // Parent class
}`}
          </pre>
        </div>
      </div>
    </div>
  );

  const renderAgent = () => (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">Agentic Workflow (LangGraph)</h2>
        <p className="text-slate-400 mb-4">
          The agent can perform multi-step reasoning using tools, enabling complex analysis that
          simple RAG cannot handle.
        </p>

        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-purple-400 mb-3">Agent State Machine</h3>
          <div className="flex flex-col items-center space-y-2">
            <div className="bg-green-600/30 text-green-300 px-4 py-2 rounded-lg">START</div>
            <ArrowRight className="w-4 h-4 text-slate-500 rotate-90" />
            <div className="bg-blue-600/30 text-blue-300 px-6 py-3 rounded-lg text-center">
              <div className="font-semibold">AGENT NODE</div>
              <div className="text-xs mt-1">Process messages → Call LLM → Decide action</div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex flex-col items-center">
                <span className="text-xs text-slate-400">tool_call?</span>
                <ArrowRight className="w-4 h-4 text-slate-500 rotate-90" />
                <div className="bg-yellow-600/30 text-yellow-300 px-4 py-2 rounded-lg text-center">
                  <div className="font-semibold">TOOLS NODE</div>
                  <div className="text-xs">Execute tools</div>
                </div>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-xs text-slate-400">final answer?</span>
                <ArrowRight className="w-4 h-4 text-slate-500 rotate-90" />
                <div className="bg-red-600/30 text-red-300 px-4 py-2 rounded-lg">END</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="bg-slate-700 rounded-lg p-3">
            <code className="text-green-400 text-sm">search_codebase</code>
            <p className="text-xs text-slate-400 mt-1">Vector search in codebase</p>
          </div>
          <div className="bg-slate-700 rounded-lg p-3">
            <code className="text-blue-400 text-sm">read_file</code>
            <p className="text-xs text-slate-400 mt-1">Read complete file content</p>
          </div>
          <div className="bg-slate-700 rounded-lg p-3">
            <code className="text-purple-400 text-sm">list_files</code>
            <p className="text-xs text-slate-400 mt-1">Directory listing</p>
          </div>
          <div className="bg-slate-700 rounded-lg p-3">
            <code className="text-yellow-400 text-sm">find_callers</code>
            <p className="text-xs text-slate-400 mt-1">Who calls this function?</p>
          </div>
          <div className="bg-slate-700 rounded-lg p-3">
            <code className="text-red-400 text-sm">find_callees</code>
            <p className="text-xs text-slate-400 mt-1">What does this call?</p>
          </div>
          <div className="bg-slate-700 rounded-lg p-3">
            <code className="text-pink-400 text-sm">find_call_chain</code>
            <p className="text-xs text-slate-400 mt-1">Trace execution path</p>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-3">Example Agent Execution</h3>
        <div className="space-y-3 text-sm">
          <div className="bg-slate-700 rounded p-3">
            <span className="text-blue-400">User:</span>
            <span className="text-slate-300 ml-2">"How does login handle invalid passwords?"</span>
          </div>
          <div className="bg-slate-700 rounded p-3">
            <span className="text-purple-400">Agent Thought:</span>
            <span className="text-slate-300 ml-2">I need to find the login function first.</span>
            <div className="mt-1">
              <span className="text-yellow-400">→ Tool Call:</span>
              <code className="text-green-300 ml-2">search_codebase("login authentication")</code>
            </div>
          </div>
          <div className="bg-slate-700 rounded p-3">
            <span className="text-purple-400">Agent Thought:</span>
            <span className="text-slate-300 ml-2">Found authenticate(). Let me see full implementation.</span>
            <div className="mt-1">
              <span className="text-yellow-400">→ Tool Call:</span>
              <code className="text-green-300 ml-2">read_file("src/auth/login.py")</code>
            </div>
          </div>
          <div className="bg-slate-700 rounded p-3">
            <span className="text-purple-400">Agent Thought:</span>
            <span className="text-slate-300 ml-2">It calls verify_password(). Let me check that.</span>
            <div className="mt-1">
              <span className="text-yellow-400">→ Tool Call:</span>
              <code className="text-green-300 ml-2">find_callees("authenticate")</code>
            </div>
          </div>
          <div className="bg-green-700/50 rounded p-3">
            <span className="text-green-400">Final Answer:</span>
            <span className="text-slate-300 ml-2">The login handles invalid passwords by...</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderRetrieval = () => (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">Multi-Stage Retrieval System</h2>

        <div className="space-y-4">
          <div className="bg-green-900/30 border-l-4 border-green-500 rounded-r-lg p-4">
            <h3 className="font-semibold text-green-400">Stage 1: Vector Retrieval (k=10)</h3>
            <p className="text-slate-300 text-sm">Semantic similarity search in Chroma/FAISS using embeddings</p>
          </div>

          <div className="bg-blue-900/30 border-l-4 border-blue-500 rounded-r-lg p-4">
            <h3 className="font-semibold text-blue-400">Stage 2: LLM File Selection</h3>
            <p className="text-slate-300 text-sm">LLM analyzes file tree structure and selects relevant files</p>
          </div>

          <div className="bg-purple-900/30 border-l-4 border-purple-500 rounded-r-lg p-4">
            <h3 className="font-semibold text-purple-400">Stage 3: Ensemble Combination</h3>
            <p className="text-slate-300 text-sm">Weighted merge: 60% vector + 40% LLM selection</p>
          </div>

          <div className="bg-yellow-900/30 border-l-4 border-yellow-500 rounded-r-lg p-4">
            <h3 className="font-semibold text-yellow-400">Stage 4: Graph Enhancement</h3>
            <p className="text-slate-300 text-sm">Add related files from AST graph (imports, calls)</p>
          </div>

          <div className="bg-red-900/30 border-l-4 border-red-500 rounded-r-lg p-4">
            <h3 className="font-semibold text-red-400">Stage 5: Cross-Encoder Reranking</h3>
            <p className="text-slate-300 text-sm">Score each (query, doc) pair, return top 5</p>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-3">Vector DB Support</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-slate-700 rounded-lg p-4 text-center">
            <Database className="w-8 h-8 text-green-400 mx-auto mb-2" />
            <div className="font-semibold text-white">Chroma</div>
            <div className="text-xs text-slate-400">Default, local</div>
          </div>
          <div className="bg-slate-700 rounded-lg p-4 text-center">
            <Database className="w-8 h-8 text-blue-400 mx-auto mb-2" />
            <div className="font-semibold text-white">FAISS</div>
            <div className="text-xs text-slate-400">Fallback, fast</div>
          </div>
          <div className="bg-slate-700 rounded-lg p-4 text-center">
            <Database className="w-8 h-8 text-purple-400 mx-auto mb-2" />
            <div className="font-semibold text-white">Qdrant</div>
            <div className="text-xs text-slate-400">Cloud option</div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-2">🕷️ Code Crawler Architecture</h1>
        <p className="text-slate-400 text-center mb-6">Interactive System Documentation</p>

        <div className="flex flex-wrap gap-2 mb-6 justify-center">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                activeTab === tab.id
                  ? 'bg-purple-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        <div className="transition-all">
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'rag' && renderRAG()}
          {activeTab === 'ast' && renderAST()}
          {activeTab === 'chunking' && renderChunking()}
          {activeTab === 'agent' && renderAgent()}
          {activeTab === 'retrieval' && renderRetrieval()}
        </div>
      </div>
    </div>
  );
};

export default ArchitectureViz;
