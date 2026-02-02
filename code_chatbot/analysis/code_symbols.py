"""Utilities to extract code symbols (class and method names) from code files."""

import logging
from typing import List, Tuple, Optional
from tree_sitter import Node

from code_chatbot.ingestion.chunker import StructuralChunker

logger = logging.getLogger(__name__)


def _extract_classes_and_methods(node: Node, acc: List[Tuple[Optional[str], Optional[str]]], parent_class: Optional[str] = None, content: str = ""):
    """Extracts classes and methods from a tree-sitter node and places them in the `acc` accumulator.
    
    Args:
        node: The tree-sitter node to traverse
        acc: Accumulator list to store (class_name, method_name) tuples
        parent_class: Name of the parent class (if any)
        content: The file content as string (for extracting names)
    """
    if node.type in ["class_definition", "class_declaration"]:
        class_name_node = node.child_by_field_name("name")
        if class_name_node:
            class_name = content[class_name_node.start_byte:class_name_node.end_byte]
            if class_name:
                acc.append((class_name, None))
                # Recursively process children with this class as parent
                for child in node.children:
                    _extract_classes_and_methods(child, acc, class_name, content)
        return
    elif node.type in ["function_definition", "method_definition"]:
        function_name_node = node.child_by_field_name("name")
        if function_name_node:
            method_name = content[function_name_node.start_byte:function_name_node.end_byte]
            if method_name:
                acc.append((parent_class, method_name))
                # Don't go deeper into method bodies (we're not extracting nested functions)
        return
    else:
        # Recursively process children
        for child in node.children:
            _extract_classes_and_methods(child, acc, parent_class, content)


def get_code_symbols(file_path: str, content: str) -> List[Tuple[Optional[str], Optional[str]]]:
    """Extracts code symbols from a file.

    Code symbols are tuples of the form (class_name, method_name). 
    For classes, method_name is None. 
    For methods that do not belong to a class, class_name is None.
    
    Args:
        file_path: Path to the file
        content: Content of the file as a string
        
    Returns:
        List of (class_name, method_name) tuples
    """
    if not StructuralChunker.is_code_file(file_path):
        return []

    if not content:
        return []

    logger.debug(f"Extracting code symbols from {file_path}")
    
    # Try to parse the file using the chunker's parsing logic
    try:
        ext = file_path.split('.')[-1].lower()
        chunker = StructuralChunker()
        
        if ext not in chunker.parsers:
            return []
        
        parser = chunker.parsers[ext]
        tree = parser.parse(bytes(content, "utf8"))
        
        if not tree or not tree.root_node.children:
            return []
        
        classes_and_methods = []
        _extract_classes_and_methods(tree.root_node, classes_and_methods, None, content)
        return classes_and_methods
        
    except Exception as e:
        logger.warning(f"Failed to extract code symbols from {file_path}: {e}")
        return []

