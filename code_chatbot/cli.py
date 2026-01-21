#!/usr/bin/env python3
"""
🕷️ Code Crawler CLI
Command-line interface for the Code Crawler engine.
"""

import argparse
import os
import sys
import logging
import shutil
import json
from dotenv import load_dotenv

# Rich Imports
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

# Local Imports
from .indexer import Indexer
from .rag import ChatEngine
from .ast_analysis import ASTGraphBuilder
from .graph_rag import GraphEnhancedRetriever
from .universal_ingestor import process_source
from .agent_workflow import create_agent_graph

# Configure Console
console = Console()
logging.basicConfig(level=logging.ERROR)
# Suppress noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)
logging.getLogger("code_chatbot.chunker").setLevel(logging.ERROR)

logger = logging.getLogger("CodeCrawlerCLI")
logger.setLevel(logging.INFO)

BANNER = """
[bold cyan]    🕷️  Code Crawler CLI  🕷️[/bold cyan]
[dim]    Index. Chat. Understand.[/dim]
"""

def setup_env():
    load_dotenv()

def print_banner():
    console.print(Panel(BANNER, subtitle="v2.0", border_style="cyan"))

def handle_index(args):
    """
    Handles the indexing command.
    """
    console.print(f"[bold blue][INFO][/bold blue] Starting indexing for source: [green]{args.source}[/green]")

    # 1. Setup Environment
    if args.provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            console.print("[bold red][ERROR][/bold red] GOOGLE_API_KEY not found in .env")
            sys.exit(1)
        embedding_provider = "gemini"
        embedding_api_key = api_key
    elif args.provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        embedding_api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key: 
            console.print("[bold red][ERROR][/bold red] GROQ_API_KEY not found in .env")
            sys.exit(1)
        if not embedding_api_key:
            console.print("[bold red][ERROR][/bold red] GOOGLE_API_KEY (for embeddings) not found in .env")
            sys.exit(1)
        embedding_provider = "gemini"
    else:
        console.print(f"[bold red]Unknown provider:[/bold red] {args.provider}")
        sys.exit(1)
        
    try:
        # 2. Extract & Ingest
        extract_to = "data/extracted"
        # Optional: Clean previous data
        if args.clean and os.path.exists(extract_to):
            console.print("[bold yellow][WARN][/bold yellow] Cleaning previous data...")
            shutil.rmtree(extract_to)
            
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Processing source...", total=None)
            documents, local_path = process_source(args.source, extract_to)
            progress.update(task, completed=True, description="[bold green]Source Processed[/bold green]")
        
        console.print(f"[bold green][SUCCESS][/bold green] Ingested {len(documents)} documents.")
        
        # Save metadata for Chat to find the path
        os.makedirs("data", exist_ok=True)
        with open("data/cli_meta.json", "w") as f:
            json.dump({"repo_path": local_path}, f)
        
        # 3. AST Analysis
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Building AST Knowledge Graph...", total=None)
            ast_builder = ASTGraphBuilder()
            for doc in documents:
                # doc.metadata['file_path'] is absolute
                ast_builder.add_file(doc.metadata['file_path'], doc.page_content)
            
            # Web sources might not create the directory
            os.makedirs(local_path, exist_ok=True)
            graph_path = os.path.join(local_path, "ast_graph.graphml")
            ast_builder.save_graph(graph_path)
            progress.update(task, completed=True, description="[bold green]AST Graph Built[/bold green]")

        console.print(f"[bold green][SUCCESS][/bold green] AST Graph ready ({ast_builder.graph.number_of_nodes()} nodes).")
        
        # 4. Vector Indexing
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task(f"Indexing into {args.vector_db}...", total=None)
            indexer = Indexer(
                provider=embedding_provider, 
                api_key=embedding_api_key
            )
            # Clear old data if requested
            if args.clean:
                indexer.clear_collection()
                
            indexer.index_documents(documents, vector_db_type=args.vector_db)
            progress.update(task, completed=True, description=f"[bold green]Indexed into {args.vector_db}[/bold green]")
            
        console.print(f"[bold green][SUCCESS][/bold green] Indexing Complete! You can now run `code-crawler chat`.")
        
    except Exception as e:
        console.print(f"[bold red][ERROR][/bold red] Indexing failed: {e}") 
        # import traceback
        # traceback.print_exc()

def handle_chat(args):
    """
    Handles the chat command.
    """
    console.print(f"[bold blue][INFO][/bold blue] Initializing Chat Engine ({args.provider})...")
    
    # Setup Env & Keys
    if args.provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        embedding_api_key = api_key
        embedding_provider = "gemini"
        model_name = "gemini-2.5-flash"
        llm_provider_lib = "google_genai"
    elif args.provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        embedding_api_key = os.getenv("GOOGLE_API_KEY")
        embedding_provider = "gemini"
        model_name = "llama-3.3-70b-versatile"
        llm_provider_lib = "groq"
    
    if not api_key:
        console.print("[bold red][ERROR][/bold red] API Keys missing. Check .env")
        sys.exit(1)

    try:
        # Load Resources
        meta_file = "data/cli_meta.json"
        if os.path.exists(meta_file):
            with open(meta_file, "r") as f:
                meta = json.load(f)
                local_path = meta.get("repo_path")
        else:
             # Fallback Heuristic
             extract_root = "data/extracted"
             if not os.path.exists(extract_root):
                 console.print("[bold red][ERROR][/bold red] No index info found. Run 'code-crawler index' first.")
                 sys.exit(1)
             
             subdirs = [f.path for f in os.scandir(extract_root) if f.is_dir()]
             if not subdirs:
                 local_path = extract_root
             else:
                 subdirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                 local_path = subdirs[0]
        
        if not local_path or not os.path.exists(local_path):
             console.print(f"[bold red][ERROR][/bold red] Codebase path not found: {local_path}")
             sys.exit(1)

        console.print(f"[dim]Using codebase at: {local_path}[/dim]")
        
        # Initialize Components
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Loading resources...", total=None)
            
            indexer = Indexer(provider=embedding_provider, api_key=embedding_api_key)
            base_retriever = indexer.get_retriever(vector_db_type=args.vector_db)
            
            graph_retriever = GraphEnhancedRetriever(
                base_retriever=base_retriever,
                repo_dir=local_path
            )
            
            repo_files = []
            for root, _, files in os.walk(local_path):
                for file in files:
                    repo_files.append(os.path.join(root, file))
            
            progress.update(task, completed=True, description="[bold green]Resources Loaded[/bold green]")

        # Initialize ChatEngine
        if args.agent:
            console.print("[bold purple]🤖 Agent Mode Enabled[/bold purple]")
        
        chat_engine = ChatEngine(
            retriever=graph_retriever,
            provider=args.provider,
            model_name=model_name,
            api_key=api_key,
            repo_files=repo_files,
            repo_name=os.path.basename(local_path),
            use_agent=args.agent,
            repo_dir=local_path
        )
        
        console.print("\n[bold green]Ready![/bold green] chat initialized. Type 'exit' to quit.\n")
        
        while True:
            try:
                query = Prompt.ask("[bold cyan]User[/bold cyan]")
                if query.strip().lower() in ['exit', 'quit', ':q']:
                    break
                
                if not query.strip():
                    continue
                
                console.print("[dim]🕷️  Thinking...[/dim]")
                
                # Unified Chat Call (Handles Agent & Standard + Fallback)
                response = chat_engine.chat(query)
                
                if isinstance(response, tuple):
                    answer, sources = response
                else:
                    answer = response
                    sources = []
                
                # Render Response
                console.print(Panel(Markdown(answer), title="Spider", border_style="magenta", expand=False))
                
                if sources:
                    console.print("[dim]Sources:[/dim]")
                    seen = set()
                    for s in sources:
                        fp = s.get('file_path', 'unknown')
                        if fp not in seen:
                            console.print(f" - [underline]{os.path.basename(fp)}[/underline]")
                            seen.add(fp)
                console.print("")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[bold red][ERROR][/bold red] {e}")
                
    except Exception as e:
        console.print(f"[bold red][ERROR][/bold red] Chat failed to start: {e}")
        # import traceback
        # traceback.print_exc()

def main():
    setup_env()
    print_banner()
    
    parser = argparse.ArgumentParser(description="Code Crawler CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Index Command
    index_parser = subparsers.add_parser("index", help="Index a codebase (ZIP, URL, or Path)")
    index_parser.add_argument("--source", "-s", required=True, help="Path to ZIP, Folder, or GitHub URL")
    index_parser.add_argument("--provider", "-p", default="gemini", choices=["gemini", "groq"], help="LLM Provider")
    index_parser.add_argument("--vector-db", "-v", default="chroma", choices=["chroma", "faiss"], help="Vector Database")
    index_parser.add_argument("--clean", action="store_true", help="Clean previous index before running")
    
    # Chat Command
    chat_parser = subparsers.add_parser("chat", help="Chat with the indexed codebase")
    chat_parser.add_argument("--provider", "-p", default="gemini", choices=["gemini", "groq"], help="LLM Provider")
    chat_parser.add_argument("--vector-db", "-v", default="chroma", choices=["chroma", "faiss"], help="Vector Database type used during index")
    chat_parser.add_argument("--agent", "-a", action="store_true", help="Enable Agentic Reasoning (LangGraph)")
    
    args = parser.parse_args()
    
    if args.command == "index":
        handle_index(args)
    elif args.command == "chat":
        handle_chat(args)

if __name__ == "__main__":
    main()
