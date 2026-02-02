"""
Crew workflows for multi-agent collaboration.
"""

from crewai import Crew, Task, Process
from typing import Dict, Any, Optional
from code_chatbot.agents import (
    create_analyst_agent,
    create_refactor_agent,
    create_reviewer_agent,
    create_documentation_agent
)
import logging

logger = logging.getLogger(__name__)


class RefactoringCrew:
    """
    Crew for automated refactoring tasks.
    
    Workflow:
    1. Analyst examines code and identifies refactoring opportunities
    2. Refactor agent implements the top refactorings
    3. Reviewer checks the refactored code for correctness
    """
    
    def __init__(self, llm=None, mcp_tools: Optional[list] = None):
        """
        Initialize refactoring crew.
        
        Args:
            llm: Language model to use for agents
            mcp_tools: MCP tools to provide to agents
        """
        self.llm = llm
        self.mcp_tools = mcp_tools or []
        
        # Create agents
        self.analyst = create_analyst_agent(llm=llm, tools=self.mcp_tools)
        self.refactor = create_refactor_agent(llm=llm, tools=self.mcp_tools)
        self.reviewer = create_reviewer_agent(llm=llm, tools=self.mcp_tools)
    
    def create_crew(self, file_path: str) -> Crew:
        """
        Create a crew for refactoring a specific file.
        
        Args:
            file_path: Path to file to refactor
            
        Returns:
            Configured Crew instance
        """
        # Define tasks
        analysis_task = Task(
            description=f"""Analyze the file {file_path} and identify refactoring opportunities.
            
            Look for:
            - Long functions that should be split
            - Duplicate code
            - Complex conditionals
            - Code smells
            - Opportunities for better naming
            
            Provide a prioritized list of the top 3-5 refactoring suggestions with rationale.""",
            agent=self.analyst,
            expected_output="A prioritized list of refactoring suggestions with detailed rationale"
        )
        
        refactor_task = Task(
            description=f"""Based on the analysis, implement the top 3 refactorings for {file_path}.
            
            For each refactoring:
            1. Explain what you're changing and why
            2. Show the before and after code
            3. Ensure the refactoring is safe and doesn't break functionality
            
            Focus on high-impact, low-risk refactorings first.""",
            agent=self.refactor,
            expected_output="Detailed refactoring plan with before/after code examples",
            context=[analysis_task]
        )
        
        review_task = Task(
            description=f"""Review the proposed refactorings for {file_path}.
            
            Check for:
            - Correctness: Do the refactorings preserve functionality?
            - Quality: Do they actually improve the code?
            - Safety: Are there any risks or edge cases?
            - Completeness: Is anything missing?
            
            Provide a review report with approval or requested changes.""",
            agent=self.reviewer,
            expected_output="Review report with approval status and any concerns",
            context=[refactor_task]
        )
        
        # Create crew
        crew = Crew(
            agents=[self.analyst, self.refactor, self.reviewer],
            tasks=[analysis_task, refactor_task, review_task],
            process=Process.sequential,
            verbose=True
        )
        
        return crew
    
    def run(self, file_path: str) -> Dict[str, Any]:
        """
        Run the refactoring crew on a file.
        
        Args:
            file_path: Path to file to refactor
            
        Returns:
            Crew execution result
        """
        crew = self.create_crew(file_path)
        result = crew.kickoff()
        
        return {
            'file_path': file_path,
            'result': result,
            'tasks_completed': len(crew.tasks)
        }


class CodeReviewCrew:
    """
    Crew for comprehensive code review.
    
    Workflow:
    1. Analyst examines code structure and patterns
    2. Reviewer performs detailed code review
    3. Documentation agent suggests documentation improvements
    """
    
    def __init__(self, llm=None, mcp_tools: Optional[list] = None):
        """Initialize code review crew."""
        self.llm = llm
        self.mcp_tools = mcp_tools or []
        
        self.analyst = create_analyst_agent(llm=llm, tools=self.mcp_tools)
        self.reviewer = create_reviewer_agent(llm=llm, tools=self.mcp_tools)
        self.documentation = create_documentation_agent(llm=llm, tools=self.mcp_tools)
    
    def create_crew(self, file_path: str) -> Crew:
        """Create a crew for reviewing a specific file."""
        analysis_task = Task(
            description=f"""Analyze the structure and design of {file_path}.
            
            Examine:
            - Overall architecture and design patterns
            - Code organization and modularity
            - Complexity and maintainability
            - Dependencies and coupling
            
            Provide insights about the code's design quality.""",
            agent=self.analyst,
            expected_output="Architectural analysis with insights about design quality"
        )
        
        review_task = Task(
            description=f"""Perform a detailed code review of {file_path}.
            
            Check for:
            - Bugs and potential issues
            - Security vulnerabilities
            - Performance problems
            - Code style and best practices
            - Error handling
            
            Provide specific, actionable feedback.""",
            agent=self.reviewer,
            expected_output="Detailed code review with specific issues and recommendations",
            context=[analysis_task]
        )
        
        documentation_task = Task(
            description=f"""Review and suggest improvements for documentation in {file_path}.
            
            Evaluate:
            - Docstrings and comments
            - Function/class documentation
            - Code clarity and readability
            - Missing documentation
            
            Suggest specific documentation improvements.""",
            agent=self.documentation,
            expected_output="Documentation review with improvement suggestions",
            context=[analysis_task, review_task]
        )
        
        crew = Crew(
            agents=[self.analyst, self.reviewer, self.documentation],
            tasks=[analysis_task, review_task, documentation_task],
            process=Process.sequential,
            verbose=True
        )
        
        return crew
    
    def run(self, file_path: str) -> Dict[str, Any]:
        """Run the code review crew on a file."""
        crew = self.create_crew(file_path)
        result = crew.kickoff()
        
        return {
            'file_path': file_path,
            'result': result,
            'tasks_completed': len(crew.tasks)
        }


# Export crews
__all__ = ['RefactoringCrew', 'CodeReviewCrew']
