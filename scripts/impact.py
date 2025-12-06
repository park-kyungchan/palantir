import os
import ast
import sys
import json
from typing import Dict, List, Set

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_module_name(file_path: str) -> str:
    """Converts file path to python module path (e.g., scripts/engine.py -> scripts.engine)"""
    rel_path = os.path.relpath(file_path, WORKSPACE_ROOT)
    if rel_path.endswith('.py'):
        rel_path = rel_path[:-3]
    return rel_path.replace(os.sep, '.')

def build_dependency_graph() -> Dict[str, Set[str]]:
    """
    Scans workspace for Python files and builds a Reverse Dependency Graph.
    Key: Module Name (Imported)
    Value: Set of Modules that import Key (Importers)
    """
    reverse_deps: Dict[str, Set[str]] = {}
    
    for root, _, files in os.walk(WORKSPACE_ROOT):
        if '.venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                importer_module = get_module_name(file_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                        
                    for node in ast.walk(tree):
                        target_module = None
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                target_module = alias.name
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                target_module = node.module
                                
                        if target_module:
                            # Normalize relative imports
                            if target_module.startswith('.'):
                                # Complex to resolve perfectly statically, but we capture the intent
                                pass 
                            
                            # Add to graph
                            if target_module not in reverse_deps:
                                reverse_deps[target_module] = set()
                            reverse_deps[target_module].add(importer_module)
                            
                except Exception as e:
                    # Skip unparseable files
                    pass
                    
    return reverse_deps

def check_impact(target_file: str):
    """Checks what files depend on the target file."""
    target_module = get_module_name(target_file)
    graph = build_dependency_graph()
    
    # Exact match
    impacted = graph.get(target_module, set())
    
    # Prefix match (e.g. scripts.ontology matches scripts.ontology.plan usage)
    for mod, dependents in graph.items():
        if mod.startswith(target_module + ".") or target_module.startswith(mod + "."):
            impacted.update(dependents)
            
    # Filter self
    if target_module in impacted:
        impacted.remove(target_module)
        
    print(json.dumps({
        "target": target_module,
        "impact_score": len(impacted),
        "impacted_modules": sorted(list(impacted))
    }, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/impact.py <file_path>")
        sys.exit(1)
        
    target = sys.argv[1]
    if not os.path.exists(target):
        # Try relative to root
        target = os.path.join(WORKSPACE_ROOT, target)
        
    check_impact(target)
