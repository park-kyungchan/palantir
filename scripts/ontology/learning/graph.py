"""
Orion Phase 5 - Dependency Graph Engine
Parses imports to build a directed graph and calculate topological depth.
Deep Context Awareness: Resolves relative imports and mapping to file system.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Optional

from .types import CodeMetric

class ImportVisitor(ast.NodeVisitor):
    """Extracts all imports from a file."""
    def __init__(self):
        self.imports: List[str] = []

    def visit_Import(self, node):
        for name in node.names:
            self.imports.append(name.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
            # We don't track the specific names imported, just the module link
        elif node.level > 0:
            # Relative import (e.g. from .types import ...)
            # We store it as a special marker to resolve later
            self.imports.append("." * node.level + (node.module or ""))
        self.generic_visit(node)

class DependencyGraph:
    """
    Builds a dependency graph of the codebase to calculate depth.
    Nodes: File paths (relative to root)
    Edges: Directed (A imports B -> A depends on B)
    """
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.adj_list: Dict[str, Set[str]] = {} # Dependents -> Dependencies
        self.file_map: Dict[str, str] = {} # Module path -> File path

    def _module_to_path(self, module_name: str, current_file: str) -> Optional[str]:
        """
        Resolves a python module name to a file path.
        Handles:
        - Absolute: scripts.ontology.types
        - Relative: .types
        """
        # 1. Handle Relative Imports
        if module_name.startswith("."):
            levels = module_name.count(".")
            parent = Path(current_file).parent
            for _ in range(levels - 1):
                parent = parent.parent
            
            suffix = module_name.lstrip(".")
            if suffix:
                target = parent / suffix
            else:
                target = parent # importing __init__.py
                
            # Try .py
            if (target.with_suffix(".py")).exists():
                return str(target.with_suffix(".py").relative_to(self.root))
            # Try package (__init__.py)
            if (target / "__init__.py").exists():
                return str((target / "__init__.py").relative_to(self.root))
            return None

        # 2. Handle Absolute Imports (internal only)
        # We assume modules start with 'scripts' or known internal roots
        parts = module_name.split(".")
        current_path = self.root
        for part in parts:
            current_path = current_path / part
        
        if (current_path.with_suffix(".py")).exists():
             return str(current_path.with_suffix(".py").relative_to(self.root))
        if (current_path / "__init__.py").exists():
             return str((current_path / "__init__.py").relative_to(self.root))
             
        return None

    def build(self, files: List[str]) -> None:
        """Parses all files and builds the graph."""
        # First pass: map all module paths
        for f in files:
            self.adj_list[f] = set()

        # Second pass: parse imports
        for f in files:
            full_path = self.root / f
            try:
                with open(full_path, "r", encoding="utf-8") as file:
                    content = file.read()
                tree = ast.parse(content)
                visitor = ImportVisitor()
                visitor.visit(tree)
                
                for mod in visitor.imports:
                    resolved = self._module_to_path(mod, str(full_path))
                    if resolved and resolved in self.adj_list:
                        # Dependency confirmed
                        self.adj_list[f].add(resolved)
                        
            except Exception as e:
                # Syntax errors or encoding issues -> Skip dependency tracking for this file
                continue

    def calculate_depths(self) -> Dict[str, int]:
        """
        Calculates topological depth where:
        - Files with 0 internal dependencies = Depth 0
        - Files depending only on Depth 0 = Depth 1
        """
        depths: Dict[str, int] = {node: 0 for node in self.adj_list}
        
        # Simple iterative fix-point algorithm (Bellman-Ford-ish) 
        # to handle the DAG.
        # Max iterations = number of files (longest possible path without cycles)
        changed = True
        iterations = 0
        max_iter = len(self.adj_list) + 5
        
        while changed and iterations < max_iter:
            changed = False
            iterations += 1
            for node, dependencies in self.adj_list.items():
                if not dependencies:
                    continue
                    
                # Depth = 1 + max(depth of all dependencies)
                # Filter out self-cycles or unknown deps? handled by adj_list check logic
                max_dep_depth = 0
                for dep in dependencies:
                    if dep == node: continue # Ignore self-import
                    max_dep_depth = max(max_dep_depth, depths[dep])
                
                new_depth = max_dep_depth + 1
                if 0 < len(dependencies) and new_depth == 1:
                     # Edge case: All dependencies are 0 (foundational)
                     pass

                if new_depth != depths[node]:
                    depths[node] = new_depth
                    changed = True
        
        return depths
