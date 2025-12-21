"""
Orion Phase 5 - Metric Analysis Engine
Implements AST visitors to calculate Cognitive Complexity and Code Metrics.
"""

import ast
from typing import Set, List
from .types import CodeMetric

class CognitiveComplexityVisitor(ast.NodeVisitor):
    """
    Calculates Cognitive Complexity based on SonarSource principles.
    - +1 for each control flow structure (if, for, while, except)
    - +1 per nesting level for these structures
    """
    def __init__(self):
        self.complexity = 0
        self.nesting_level = 0
        self.max_nesting = 0

    def _visit_nesting(self, node):
        self.complexity += 1 + self.nesting_level
        self.nesting_level += 1
        self.max_nesting = max(self.max_nesting, self.nesting_level)
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_If(self, node):
        self._visit_nesting(node)

    def visit_For(self, node):
        self._visit_nesting(node)

    def visit_AsyncFor(self, node):
        self._visit_nesting(node)

    def visit_While(self, node):
        self._visit_nesting(node)

    def visit_Try(self, node):
        # 'try' itself usually doesn't cost, but 'except' does.
        # SonarSource rule: except blocks increment complexity
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self._visit_nesting(node)
    
    def visit_FunctionDef(self, node):
        # Reset nesting for method but keep complexity accumulating
        # Or should we treat function as nesting? 
        # Simpler approach: New scope, but don't reset complexity count.
        # We start nesting at 0 for the function body.
        old_nesting = self.nesting_level
        self.nesting_level = 0
        self.generic_visit(node)
        self.nesting_level = old_nesting
    
    def visit_AsyncFunctionDef(self, node):
        old_nesting = self.nesting_level
        self.nesting_level = 0
        self.generic_visit(node)
        self.nesting_level = old_nesting

class ConceptVisitor(ast.NodeVisitor):
    """Scans for Domain Concepts and Patterns."""
    def __init__(self):
        self.imports: Set[str] = set()
        self.classes = 0
        self.functions = 0
        self.async_counts = 0
        self.pydantic_counts = 0
        self.patterns: List[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.classes += 1
        # Check for Pydantic BaseModel inheritance
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'BaseModel':
                self.pydantic_counts += 1
                self.patterns.append("pydantic_model")
            elif isinstance(base, ast.Attribute) and base.attr == 'BaseModel':
                self.pydantic_counts += 1
                self.patterns.append("pydantic_model")
            elif isinstance(base, ast.Name) and base.id == 'OntologyObject':
                 self.patterns.append("ontology_object")
        
        # Check for Repository pattern by name convention
        if "Repository" in node.name:
            self.patterns.append("repository_pattern")
            
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.functions += 1
        self.async_counts += 1
        self.patterns.append("async_function")
        self.generic_visit(node)

def analyze_file(file_path: str, content: str) -> CodeMetric:
    """Parses file content and returns collected metrics."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Handle non-python or invalid python files gracefully
        return CodeMetric(file_path=file_path, loc=len(content.splitlines()))

    # 1. Cognitive Complexity
    cog_visitor = CognitiveComplexityVisitor()
    cog_visitor.visit(tree)

    # 2. Concept Analysis
    con_visitor = ConceptVisitor()
    con_visitor.visit(tree)
    
    return CodeMetric(
        file_path=file_path,
        loc=len(content.splitlines()),
        nesting_max=cog_visitor.max_nesting,
        control_flow_count=cog_visitor.complexity, # Using complexity as proxy for control flow density
        unique_imports=len(con_visitor.imports),
        imports=list(con_visitor.imports),
        classes=con_visitor.classes,
        functions=con_visitor.functions,
        async_patterns=con_visitor.async_counts,
        pydantic_models=con_visitor.pydantic_counts,
        identified_patterns=list(set(con_visitor.patterns))
    )
