import ast
import os
import networkx as nx
from typing import List, Dict, Set, Any

class DependencyAnalyzer:
    """
    Static Analysis Engine using AST and NetworkX.
    Builds a dependency graph of the codebase to support Impact Analysis.
    """
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.graph = nx.DiGraph()
        self.file_map = {} # Map module name to file path

    def build_graph(self):
        """Scans the codebase and builds the dependency graph."""
        self.graph.clear()
        self.file_map.clear()
        
        # 1. First pass: Map all files and modules
        for root, _, files in os.walk(self.root_dir):
            if ".venv" in root or "__pycache__" in root or ".git" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    module_name = self._get_module_name(file_path)
                    self.file_map[module_name] = file_path
                    self.graph.add_node(file_path, type="file", module=module_name)

        # 2. Second pass: Parse imports and add edges
        for file_path in self.graph.nodes():
            try:
                self._analyze_file(file_path)
            except Exception as e:
                print(f"⚠️ Error analyzing {file_path}: {e}")

    def _get_module_name(self, file_path: str) -> str:
        """Converts file path to dotted module name."""
        rel_path = os.path.relpath(file_path, self.root_dir)
        return rel_path.replace(".py", "").replace(os.sep, ".")

    def _analyze_file(self, file_path: str):
        """Parses a file and extracts imports."""
        with open(file_path, "r") as f:
            try:
                tree = ast.parse(f.read(), filename=file_path)
            except SyntaxError:
                return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._add_dependency(file_path, alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._add_dependency(file_path, node.module)

    def _add_dependency(self, source_file: str, target_module: str):
        """Adds a directed edge from source_file to the file defining target_module."""
        # Resolve target_module to file path
        # 1. Exact match
        if target_module in self.file_map:
            target_file = self.file_map[target_module]
            self.graph.add_edge(source_file, target_file)
            return

        # 2. Package match (e.g., scripts.ontology -> scripts/ontology.py)
        # Try to find the longest matching prefix in file_map
        best_match = None
        for mod_name, path in self.file_map.items():
            if target_module == mod_name or target_module.startswith(mod_name + "."):
                 # Prefer exact or closer match
                 if best_match is None or len(mod_name) > len(best_match):
                     best_match = mod_name
        
        if best_match:
            self.graph.add_edge(source_file, self.file_map[best_match])

    def get_impact_set(self, changed_file: str) -> List[str]:
        """
        Returns a list of files that depend on the changed_file (Reverse Dependency).
        If A imports B, and B changes, A is impacted.
        Graph edge: A -> B (A depends on B).
        Impact: Predecessors of B.
        """
        abs_path = os.path.abspath(changed_file)
        if abs_path not in self.graph:
            return []
        
        # Find all files that depend on this file (Ancestors in dependency graph)
        # Since Edge is Source -> Target (Importing -> Imported),
        # We need to find nodes that have an edge TO this node.
        # networkx.ancestors returns all nodes having a path to the target.
        impacted = nx.ancestors(self.graph, abs_path)
        return list(impacted)

    def get_dependencies(self, file_path: str) -> List[str]:
        """Returns a list of files that the given file depends on."""
        abs_path = os.path.abspath(file_path)
        if abs_path not in self.graph:
            return []
        return list(nx.descendants(self.graph, abs_path))

if __name__ == "__main__":
    # Self-Test
    analyzer = DependencyAnalyzer(".")
    analyzer.build_graph()
    print(f"Graph Nodes: {len(analyzer.graph.nodes)}")
    print(f"Graph Edges: {len(analyzer.graph.edges)}")
    
    # Check impact of ontology.py
    ontology_path = os.path.abspath("scripts/ontology.py")
    if ontology_path in analyzer.graph:
        impact = analyzer.get_impact_set(ontology_path)
        print(f"\nImpact of changing scripts/ontology.py ({len(impact)} files):")
        for f in impact:
            print(f" - {os.path.relpath(f)}")
