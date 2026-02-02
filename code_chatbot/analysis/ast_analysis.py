"""
Enhanced Code Analysis with AST + Call Graph + Control Flow

This module provides comprehensive code analysis using:
1. AST (Abstract Syntax Tree) - Code structure
2. Call Graph - Function-to-function relationships  
3. Import Graph - Module dependencies
4. Class Hierarchy - Inheritance relationships

Uses tree-sitter for multi-language support.
"""

import logging
import networkx as nx
import os
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_javascript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Information about a function/method"""
    name: str
    file_path: str
    start_line: int
    end_line: int
    is_method: bool = False
    class_name: Optional[str] = None
    calls: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    
    @property
    def full_name(self) -> str:
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        return self.name
    
    @property
    def node_id(self) -> str:
        return f"{self.file_path}::{self.full_name}"


@dataclass  
class ClassInfo:
    """Information about a class"""
    name: str
    file_path: str
    start_line: int
    end_line: int
    bases: List[str] = field(default_factory=list)  # Parent classes
    methods: List[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Information about an import"""
    module: str
    names: List[str] = field(default_factory=list)  # Specific names imported
    is_from_import: bool = False


class EnhancedCodeAnalyzer:
    """
    Enhanced code analyzer that builds:
    - AST-based structure graph
    - Function call graph
    - Import dependency graph
    - Class hierarchy graph
    """
    
    def __init__(self):
        # Main knowledge graph
        self.graph = nx.DiGraph()
        
        # Specialized indices for faster lookups
        self.functions: Dict[str, FunctionInfo] = {}  # node_id -> FunctionInfo
        self.classes: Dict[str, ClassInfo] = {}  # node_id -> ClassInfo
        self.imports: Dict[str, List[ImportInfo]] = {}  # file_path -> imports
        self.definitions: Dict[str, List[str]] = {}  # name -> [node_ids]
        
        # Track unresolved calls for later resolution
        self.unresolved_calls: List[Tuple[str, str, int]] = []  # (caller_id, callee_name, line)
        
        # Parsers
        self.parsers = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        try:
            # Python
            py_language = Language(tree_sitter_python.language())
            py_parser = Parser(py_language)
            self.parsers['python'] = py_parser
            self.parsers['py'] = py_parser
            
            # JavaScript
            js_language = Language(tree_sitter_javascript.language())
            js_parser = Parser(js_language)
            self.parsers['javascript'] = js_parser  
            self.parsers['js'] = js_parser
            self.parsers['jsx'] = js_parser
            
        except Exception as e:
            logger.error(f"Error initializing parsers: {e}")
    
    def add_file(self, file_path: str, content: str):
        """Parse a file and add it to the knowledge graph."""
        ext = file_path.split('.')[-1].lower()
        parser = self.parsers.get(ext)
        
        if not parser:
            return
        
        try:
            tree = parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node
            
            # Add file node
            self.graph.add_node(
                file_path, 
                type="file", 
                name=os.path.basename(file_path),
                language=ext
            )
            
            # Extract all symbols
            self._extract_symbols(root_node, file_path, content)
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
    
    def _extract_symbols(self, node, file_path: str, content: str, 
                         current_class: Optional[str] = None,
                         current_function: Optional[str] = None):
        """Recursively extract symbols from AST node."""
        
        # ========== IMPORTS ==========
        if node.type == "import_statement":
            self._process_import(node, file_path, content)
        
        elif node.type == "import_from_statement":
            self._process_from_import(node, file_path, content)
        
        # ========== CLASSES ==========
        elif node.type == "class_definition":
            class_info = self._process_class(node, file_path, content)
            if class_info:
                # Recurse into class body with class context
                for child in node.children:
                    if child.type == "block":
                        self._extract_symbols(child, file_path, content, 
                                            current_class=class_info.name)
                return  # Don't recurse again below
        
        # ========== FUNCTIONS/METHODS ==========
        elif node.type == "function_definition":
            func_info = self._process_function(node, file_path, content, current_class)
            if func_info:
                # Recurse into function body to find calls
                for child in node.children:
                    if child.type == "block":
                        self._extract_symbols(child, file_path, content,
                                            current_class=current_class,
                                            current_function=func_info.node_id)
                return  # Don't recurse again below
        
        # ========== FUNCTION CALLS ==========
        elif node.type == "call":
            self._process_call(node, file_path, content, current_function or file_path)
        
        # Recurse into children
        for child in node.children:
            self._extract_symbols(child, file_path, content, 
                                current_class, current_function)
    
    def _process_import(self, node, file_path: str, content: str):
        """Process import statement."""
        # import module1, module2
        for child in node.children:
            if child.type == "dotted_name":
                module_name = self._get_text(child, content)
                import_info = ImportInfo(module=module_name)
                
                if file_path not in self.imports:
                    self.imports[file_path] = []
                self.imports[file_path].append(import_info)
                
                # Add import edge
                self.graph.add_edge(file_path, module_name, relation="imports")
    
    def _process_from_import(self, node, file_path: str, content: str):
        """Process from X import Y statement."""
        module_name = None
        names = []
        
        for child in node.children:
            if child.type == "dotted_name" and module_name is None:
                module_name = self._get_text(child, content)
            elif child.type == "import_from_list":
                for name_node in child.children:
                    if name_node.type == "aliased_import":
                        name = self._get_text(name_node.children[0], content)
                        names.append(name)
                    elif name_node.type == "identifier":
                        names.append(self._get_text(name_node, content))
        
        if module_name:
            import_info = ImportInfo(module=module_name, names=names, is_from_import=True)
            if file_path not in self.imports:
                self.imports[file_path] = []
            self.imports[file_path].append(import_info)
            
            # Add import edge
            self.graph.add_edge(file_path, module_name, relation="imports")
            
            # Register imported names as potential definitions
            for name in names:
                if name not in self.definitions:
                    self.definitions[name] = []
                self.definitions[name].append(f"{module_name}.{name}")
    
    def _process_class(self, node, file_path: str, content: str) -> Optional[ClassInfo]:
        """Process class definition."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
        
        class_name = self._get_text(name_node, content)
        node_id = f"{file_path}::{class_name}"
        
        # Get base classes
        bases = []
        for child in node.children:
            if child.type == "argument_list":
                for arg in child.children:
                    if arg.type == "identifier":
                        bases.append(self._get_text(arg, content))
        
        class_info = ClassInfo(
            name=class_name,
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            bases=bases
        )
        
        self.classes[node_id] = class_info
        
        # Add to graph
        self.graph.add_node(
            node_id,
            type="class",
            name=class_name,
            start_line=class_info.start_line,
            end_line=class_info.end_line
        )
        
        self.graph.add_edge(file_path, node_id, relation="defines")
        
        # Add inheritance edges
        for base in bases:
            self.graph.add_edge(node_id, base, relation="inherits_from")
        
        # Register definition
        if class_name not in self.definitions:
            self.definitions[class_name] = []
        self.definitions[class_name].append(node_id)
        
        return class_info
    
    def _process_function(self, node, file_path: str, content: str, 
                         current_class: Optional[str] = None) -> Optional[FunctionInfo]:
        """Process function/method definition."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
        
        func_name = self._get_text(name_node, content)
        
        # Get parameters
        params = []
        params_node = node.child_by_field_name("parameters")
        if params_node:
            for child in params_node.children:
                if child.type == "identifier":
                    params.append(self._get_text(child, content))
                elif child.type == "typed_parameter":
                    name = child.child_by_field_name("name")
                    if name:
                        params.append(self._get_text(name, content))
        
        func_info = FunctionInfo(
            name=func_name,
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            is_method=current_class is not None,
            class_name=current_class,
            parameters=params
        )
        
        node_id = func_info.node_id
        self.functions[node_id] = func_info
        
        # Add to graph
        self.graph.add_node(
            node_id,
            type="function" if not current_class else "method",
            name=func_name,
            full_name=func_info.full_name,
            start_line=func_info.start_line,
            end_line=func_info.end_line,
            parameters=",".join(params)
        )
        
        # Link to parent (file or class)
        if current_class:
            class_id = f"{file_path}::{current_class}"
            self.graph.add_edge(class_id, node_id, relation="has_method")
        else:
            self.graph.add_edge(file_path, node_id, relation="defines")
        
        # Register definition
        if func_name not in self.definitions:
            self.definitions[func_name] = []
        self.definitions[func_name].append(node_id)
        
        return func_info
    
    def _process_call(self, node, file_path: str, content: str, caller_id: str):
        """Process function call."""
        func_node = node.child_by_field_name("function")
        if not func_node:
            return
        
        callee_name = self._get_text(func_node, content)
        call_line = node.start_point[0] + 1
        
        # Track call in function info
        if caller_id in self.functions:
            self.functions[caller_id].calls.append(callee_name)
        
        # Store for later resolution
        self.unresolved_calls.append((caller_id, callee_name, call_line))
    
    def _get_text(self, node, content: str) -> str:
        """Get text content of a node."""
        return content[node.start_byte:node.end_byte]
    
    def resolve_call_graph(self):
        """Resolve all function calls to their definitions."""
        resolved_count = 0
        
        for caller_id, callee_name, line in self.unresolved_calls:
            # Handle method calls like "self.method" or "obj.method"
            simple_name = callee_name.split(".")[-1]
            
            # Try to find definition
            target_ids = []
            
            # Check direct match
            if callee_name in self.definitions:
                target_ids.extend(self.definitions[callee_name])
            
            # Check simple name (for methods)
            if simple_name in self.definitions and simple_name != callee_name:
                target_ids.extend(self.definitions[simple_name])
            
            # Add call edges
            for target_id in target_ids:
                self.graph.add_edge(
                    caller_id, 
                    target_id, 
                    relation="calls",
                    line=line
                )
                resolved_count += 1
        
        logger.info(f"Resolved {resolved_count} function calls in call graph")
    
    def get_callers(self, function_name: str) -> List[str]:
        """Find all functions that call the specified function."""
        callers = []
        
        # Find the function's node_id
        target_ids = self.definitions.get(function_name, [])
        
        for target_id in target_ids:
            # Find incoming "calls" edges
            for pred in self.graph.predecessors(target_id):
                edge_data = self.graph.get_edge_data(pred, target_id)
                if edge_data and edge_data.get("relation") == "calls":
                    callers.append(pred)
        
        return callers
    
    def get_callees(self, function_name: str) -> List[str]:
        """Find all functions called by the given function."""
        callees = []
        
        # Find the function's node_id
        caller_ids = self.definitions.get(function_name, [])
        
        for caller_id in caller_ids:
            # Find outgoing "calls" edges
            for succ in self.graph.successors(caller_id):
                edge_data = self.graph.get_edge_data(caller_id, succ)
                if edge_data and edge_data.get("relation") == "calls":
                    callees.append(succ)
        
        return callees
    
    def get_call_chain(self, start_func: str, end_func: str, max_depth: int = 5) -> List[List[str]]:
        """Find call paths from start_func to end_func."""
        paths = []
        
        start_ids = self.definitions.get(start_func, [])
        end_ids = self.definitions.get(end_func, [])
        
        for start_id in start_ids:
            for end_id in end_ids:
                try:
                    for path in nx.all_simple_paths(self.graph, start_id, end_id, cutoff=max_depth):
                        # Filter to only show call edges
                        call_path = [start_id]
                        for i in range(len(path) - 1):
                            edge = self.graph.get_edge_data(path[i], path[i+1])
                            if edge and edge.get("relation") == "calls":
                                call_path.append(path[i+1])
                        if len(call_path) > 1:
                            paths.append(call_path)
                except nx.NetworkXNoPath:
                    continue
        
        return paths
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, List[str]]:
        """Get all dependencies of a file (imports, calls to other files)."""
        deps = {
            "imports": [],
            "calls_to": [],
            "called_by": []
        }
        
        # Direct imports
        deps["imports"] = [imp.module for imp in self.imports.get(file_path, [])]
        
        # Functions in this file that call functions in other files
        for func_id, func_info in self.functions.items():
            if func_info.file_path == file_path:
                for callee in self.get_callees(func_info.name):
                    callee_file = callee.split("::")[0]
                    if callee_file != file_path and callee_file not in deps["calls_to"]:
                        deps["calls_to"].append(callee_file)
        
        # Functions in other files that call functions in this file
        for func_id, func_info in self.functions.items():
            if func_info.file_path == file_path:
                for caller in self.get_callers(func_info.name):
                    caller_file = caller.split("::")[0]
                    if caller_file != file_path and caller_file not in deps["called_by"]:
                        deps["called_by"].append(caller_file)
        
        return deps
    
    def get_related_nodes(self, node_id: str, depth: int = 2) -> List[str]:
        """Get nodes related to the given node via graph traversal."""
        if node_id not in self.graph:
            # Try to find by name
            if node_id in self.definitions:
                node_ids = self.definitions[node_id]
                all_related = []
                for nid in node_ids:
                    all_related.extend(list(nx.bfs_tree(self.graph, nid, depth_limit=depth)))
                return list(set(all_related))
            return []
        
        return list(nx.bfs_tree(self.graph, node_id, depth_limit=depth))
    
    def get_statistics(self) -> Dict:
        """Get analysis statistics."""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "files": len([n for n, d in self.graph.nodes(data=True) if d.get("type") == "file"]),
            "classes": len(self.classes),
            "functions": len([f for f in self.functions.values() if not f.is_method]),
            "methods": len([f for f in self.functions.values() if f.is_method]),
            "imports": sum(len(imps) for imps in self.imports.values()),
            "call_edges": len([1 for _, _, d in self.graph.edges(data=True) if d.get("relation") == "calls"])
        }
    
    def save_graph(self, path: str):
        """Save the graph to a GraphML file."""
        # Resolve call graph first
        self.resolve_call_graph()
        
        # Log statistics
        stats = self.get_statistics()
        logger.info(f"Graph Statistics: {stats}")
        
        nx.write_graphml(self.graph, path)
        logger.info(f"Graph saved to {path}")


# Backward compatibility alias
class ASTGraphBuilder(EnhancedCodeAnalyzer):
    """Alias for backward compatibility with existing code."""
    pass
