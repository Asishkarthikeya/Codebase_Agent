"""
MCP Client for interacting with Refactor MCP Server.

Provides async methods to call MCP tools from other parts of the application.
"""

import logging
from typing import List, Dict, Optional
from code_chatbot.mcp.mcp_server import RefactorMCPServer, SearchResult, RefactorResult, RefactorSuggestion

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for Refactor MCP server.
    
    Provides a simple interface to call MCP tools.
    """
    
    def __init__(self, workspace_root: str):
        """
        Initialize MCP client.
        
        Args:
            workspace_root: Root directory of the codebase
        """
        self.server = RefactorMCPServer(workspace_root)
        logger.info(f"MCP Client initialized for workspace: {workspace_root}")
    
    def search_code(
        self,
        pattern: str,
        file_pattern: str = "**/*.py",
        context_lines: int = 2,
        is_regex: bool = True
    ) -> List[SearchResult]:
        """
        Search for patterns in codebase.
        
        Args:
            pattern: Search pattern (regex or literal)
            file_pattern: Glob pattern for files to search
            context_lines: Number of context lines before/after match
            is_regex: Whether pattern is regex
            
        Returns:
            List of search results
        """
        try:
            results = self.server.code_search(
                pattern=pattern,
                file_pattern=file_pattern,
                context_lines=context_lines,
                is_regex=is_regex
            )
            logger.info(f"Code search completed: {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Code search failed: {e}")
            return []
    
    def refactor_code(
        self,
        search_pattern: str,
        replace_pattern: str,
        file_pattern: str = "**/*.py",
        dry_run: bool = True,
        is_regex: bool = True
    ) -> RefactorResult:
        """
        Perform regex-based code refactoring.
        
        Args:
            search_pattern: Pattern to search for
            replace_pattern: Replacement string (supports capture groups)
            file_pattern: Glob pattern for files to process
            dry_run: If True, only show what would change
            is_regex: Whether pattern is regex
            
        Returns:
            RefactorResult with changes made or to be made
        """
        try:
            result = self.server.code_refactor(
                search_pattern=search_pattern,
                replace_pattern=replace_pattern,
                file_pattern=file_pattern,
                dry_run=dry_run,
                is_regex=is_regex
            )
            logger.info(f"Refactoring {'preview' if dry_run else 'complete'}: "
                       f"{result.files_changed} files, {result.total_replacements} replacements")
            return result
        except Exception as e:
            logger.error(f"Refactoring failed: {e}")
            return RefactorResult(
                files_changed=0,
                total_replacements=0,
                changes=[],
                dry_run=dry_run,
                success=False,
                error=str(e)
            )
    
    def suggest_refactorings(
        self,
        file_path: str,
        max_suggestions: int = 5
    ) -> List[RefactorSuggestion]:
        """
        Analyze code and suggest refactorings.
        
        Args:
            file_path: Path to file to analyze
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of refactoring suggestions
        """
        try:
            suggestions = self.server.suggest_refactorings(
                file_path=file_path,
                max_suggestions=max_suggestions
            )
            logger.info(f"Generated {len(suggestions)} refactoring suggestions for {file_path}")
            return suggestions
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            return []
    
    def format_search_results(self, results: List[SearchResult], max_results: int = 10) -> str:
        """
        Format search results for display.
        
        Args:
            results: List of search results
            max_results: Maximum number of results to format
            
        Returns:
            Formatted string
        """
        if not results:
            return "No results found."
        
        output = [f"Found {len(results)} matches:\n"]
        
        for i, result in enumerate(results[:max_results], 1):
            output.append(f"\n{i}. {result.file_path}:{result.line_number}")
            output.append(f"   {result.line_content}")
            
            if result.context_before:
                output.append(f"   Context before:")
                for line in result.context_before[-2:]:
                    output.append(f"     {line}")
        
        if len(results) > max_results:
            output.append(f"\n... and {len(results) - max_results} more results")
        
        return '\n'.join(output)
    
    def format_refactor_result(self, result: RefactorResult) -> str:
        """
        Format refactor result for display.
        
        Args:
            result: Refactor result
            
        Returns:
            Formatted string
        """
        if not result.success:
            return f"❌ Refactoring failed: {result.error}"
        
        mode = "Preview" if result.dry_run else "Applied"
        output = [
            f"✅ Refactoring {mode}:",
            f"   Files changed: {result.files_changed}",
            f"   Total replacements: {result.total_replacements}\n"
        ]
        
        for change in result.changes[:5]:
            output.append(f"\n📄 {change['file_path']}")
            output.append(f"   Replacements: {change['replacements']}")
            if change.get('preview'):
                output.append(f"   Preview:")
                for line in change['preview'].split('\n')[:6]:
                    output.append(f"     {line}")
        
        if len(result.changes) > 5:
            output.append(f"\n... and {len(result.changes) - 5} more files")
        
        return '\n'.join(output)
    
    def format_suggestions(self, suggestions: List[RefactorSuggestion]) -> str:
        """
        Format refactoring suggestions for display.
        
        Args:
            suggestions: List of suggestions
            
        Returns:
            Formatted string
        """
        if not suggestions:
            return "No refactoring suggestions found."
        
        output = [f"💡 Found {len(suggestions)} refactoring suggestions:\n"]
        
        for i, suggestion in enumerate(suggestions, 1):
            impact_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}
            emoji = impact_emoji.get(suggestion.estimated_impact, '⚪')
            
            output.append(f"\n{i}. {emoji} {suggestion.type.replace('_', ' ').title()}")
            output.append(f"   Location: {suggestion.file_path}:L{suggestion.line_start}-L{suggestion.line_end}")
            output.append(f"   Issue: {suggestion.description}")
            output.append(f"   Suggestion: {suggestion.rationale}")
        
        return '\n'.join(output)


# Convenience function
def get_mcp_client(workspace_root: str = ".") -> MCPClient:
    """Get an MCP client instance."""
    return MCPClient(workspace_root)
