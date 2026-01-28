"""
Base agent classes and utilities for CrewAI integration.
"""

from crewai import Agent
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def create_analyst_agent(llm=None, tools: Optional[List] = None) -> Agent:
    """
    Create a Code Analyst agent.
    
    Specializes in understanding codebase architecture and identifying patterns.
    """
    return Agent(
        role="Senior Code Analyst",
        goal="Understand codebase architecture, identify patterns, and analyze code quality",
        backstory="""You are an expert software architect with 15 years of experience.
        You specialize in identifying design patterns, anti-patterns, and technical debt.
        You have a deep understanding of software architecture principles and best practices.
        You can quickly analyze codebases and provide insightful observations about their structure.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools or []
    )


def create_refactor_agent(llm=None, tools: Optional[List] = None) -> Agent:
    """
    Create a Refactoring Specialist agent.
    
    Specializes in proposing and executing safe code refactorings.
    """
    return Agent(
        role="Refactoring Specialist",
        goal="Improve code quality through safe, well-reasoned refactorings",
        backstory="""You are a master of code refactoring with deep knowledge of design patterns.
        You have refactored thousands of codebases and know how to improve code without breaking functionality.
        You always ensure refactorings are safe, well-tested, and improve maintainability.
        You understand the trade-offs between different refactoring approaches.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools or []
    )


def create_reviewer_agent(llm=None, tools: Optional[List] = None) -> Agent:
    """
    Create a Code Review Expert agent.
    
    Specializes in reviewing code changes and catching potential issues.
    """
    return Agent(
        role="Code Review Expert",
        goal="Ensure code quality, catch bugs, and identify security issues",
        backstory="""You are a veteran code reviewer who has reviewed over 10,000 pull requests.
        You have an eagle eye for bugs, security vulnerabilities, and maintainability issues.
        You provide constructive feedback that helps developers improve their code.
        You understand the importance of balancing perfectionism with pragmatism.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools or []
    )


def create_documentation_agent(llm=None, tools: Optional[List] = None) -> Agent:
    """
    Create a Documentation Specialist agent.
    
    Specializes in creating clear, comprehensive documentation.
    """
    return Agent(
        role="Documentation Specialist",
        goal="Create clear, comprehensive, and helpful documentation",
        backstory="""You are a technical writer with deep programming knowledge.
        You excel at explaining complex code in simple, understandable terms.
        You know how to write documentation that developers actually want to read.
        You understand the importance of examples, diagrams, and clear explanations.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools or []
    )


# Export all agent creators
__all__ = [
    'create_analyst_agent',
    'create_refactor_agent',
    'create_reviewer_agent',
    'create_documentation_agent'
]
