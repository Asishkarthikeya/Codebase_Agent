"""
Demo script for MCP and CrewAI integration.

Shows how to use the new refactoring and multi-agent capabilities.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from code_chatbot.mcp_client import MCPClient
from code_chatbot.crews import RefactoringCrew, CodeReviewCrew
from langchain_google_genai import ChatGoogleGenerativeAI


def demo_mcp_search():
    """Demo: Search for code patterns using MCP"""
    print("\n" + "="*60)
    print("DEMO 1: MCP Code Search")
    print("="*60)
    
    # Create MCP client
    client = MCPClient(workspace_root=".")
    
    # Search for all class definitions
    print("\n🔍 Searching for class definitions...")
    results = client.search_code(
        pattern=r"class\s+(\w+)",
        file_pattern="code_chatbot/*.py",
        context_lines=1
    )
    
    # Format and display results
    print(client.format_search_results(results, max_results=5))


def demo_mcp_refactor():
    """Demo: Preview a refactoring using MCP"""
    print("\n" + "="*60)
    print("DEMO 2: MCP Code Refactoring (Dry Run)")
    print("="*60)
    
    # Create MCP client
    client = MCPClient(workspace_root=".")
    
    # Preview refactoring: print -> logger.info
    print("\n🔧 Previewing refactoring: print() -> logger.info()...")
    result = client.refactor_code(
        search_pattern=r'print\((.*)\)',
        replace_pattern=r'logger.info(\1)',
        file_pattern="code_chatbot/mcp_*.py",
        dry_run=True  # Preview only, don't apply
    )
    
    # Format and display result
    print(client.format_refactor_result(result))


def demo_mcp_suggestions():
    """Demo: Get refactoring suggestions using MCP"""
    print("\n" + "="*60)
    print("DEMO 3: MCP Refactoring Suggestions")
    print("="*60)
    
    # Create MCP client
    client = MCPClient(workspace_root=".")
    
    # Get suggestions for a file
    print("\n💡 Analyzing code_chatbot/mcp_server.py for refactoring opportunities...")
    suggestions = client.suggest_refactorings(
        file_path="code_chatbot/mcp_server.py",
        max_suggestions=3
    )
    
    # Format and display suggestions
    print(client.format_suggestions(suggestions))


def demo_crewai_refactoring():
    """Demo: Use CrewAI multi-agent refactoring"""
    print("\n" + "="*60)
    print("DEMO 4: CrewAI Multi-Agent Refactoring")
    print("="*60)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n⚠️  Skipping CrewAI demo: GOOGLE_API_KEY not set")
        print("   Set your API key to run multi-agent workflows")
        return
    
    # Create LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Create refactoring crew
    print("\n🤖 Creating refactoring crew (Analyst + Refactor + Reviewer)...")
    crew = RefactoringCrew(llm=llm)
    
    # Run crew on a file
    print("\n🚀 Running crew on code_chatbot/mcp_client.py...")
    print("   (This may take 30-60 seconds...)\n")
    
    try:
        result = crew.run(file_path="code_chatbot/mcp_client.py")
        
        print("\n✅ Crew execution complete!")
        print(f"   Tasks completed: {result['tasks_completed']}")
        print(f"\n📋 Result:\n{result['result']}")
    
    except Exception as e:
        print(f"\n❌ Crew execution failed: {e}")


def demo_crewai_review():
    """Demo: Use CrewAI multi-agent code review"""
    print("\n" + "="*60)
    print("DEMO 5: CrewAI Multi-Agent Code Review")
    print("="*60)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n⚠️  Skipping CrewAI demo: GOOGLE_API_KEY not set")
        return
    
    # Create LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Create code review crew
    print("\n🤖 Creating code review crew (Analyst + Reviewer + Documentation)...")
    crew = CodeReviewCrew(llm=llm)
    
    # Run crew on a file
    print("\n🚀 Running crew on code_chatbot/mcp_server.py...")
    print("   (This may take 30-60 seconds...)\n")
    
    try:
        result = crew.run(file_path="code_chatbot/mcp_server.py")
        
        print("\n✅ Crew execution complete!")
        print(f"   Tasks completed: {result['tasks_completed']}")
        print(f"\n📋 Result:\n{result['result']}")
    
    except Exception as e:
        print(f"\n❌ Crew execution failed: {e}")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("🚀 MCP + CrewAI Integration Demo")
    print("="*60)
    print("\nThis demo showcases:")
    print("  1. MCP Code Search - Find patterns in your codebase")
    print("  2. MCP Refactoring - Preview/apply code changes")
    print("  3. MCP Suggestions - Get AI-powered refactoring ideas")
    print("  4. CrewAI Refactoring - Multi-agent automated refactoring")
    print("  5. CrewAI Code Review - Multi-agent code review")
    
    # Run MCP demos (no API key needed)
    demo_mcp_search()
    demo_mcp_refactor()
    demo_mcp_suggestions()
    
    # Run CrewAI demos (requires API key)
    demo_crewai_refactoring()
    demo_crewai_review()
    
    print("\n" + "="*60)
    print("✅ Demo Complete!")
    print("="*60)
    print("\nNext steps:")
    print("  - Try the MCP tools in your own code")
    print("  - Customize agent roles and workflows")
    print("  - Integrate with Streamlit UI")
    print("  - Add more specialized agents")


if __name__ == "__main__":
    main()
