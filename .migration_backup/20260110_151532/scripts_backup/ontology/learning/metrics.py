"""
Orion Phase 5 - Metric Analysis Engine
Implements AST visitors to calculate Cognitive Complexity and Code Metrics.
"""

import ast
import re
from pathlib import Path
from typing import Set, List
from .types import CodeMetric

_JS_TS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"}

_C_LIKE_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_C_LIKE_LINE_COMMENT_RE = re.compile(r"//.*?$", re.MULTILINE)

_JS_TS_IMPORT_RE = re.compile(
    r"""(?x)
    \b(?:import|export)\s+
    (?:type\s+)? # TS: import type
    (?:[^'"]*?\s+from\s+)? # import ... from
    ['"]([^'"]+)['"]
    """
)
_JS_TS_DYNAMIC_IMPORT_RE = re.compile(r"""\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)""")
_JS_TS_REQUIRE_RE = re.compile(r"""\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)""")

_GO_IMPORT_BLOCK_RE = re.compile(r"(?ms)^\s*import\s*\((.*?)\)\s*$")
_GO_IMPORT_SINGLE_RE = re.compile(r"""(?m)^\s*import\s+(?:[._]\s+)?\"([^\"]+)\"""")
_QUOTED_PATH_RE = re.compile(r"\"([^\"]+)\"")

_JS_TS_CONTROL_FLOW_RE = re.compile(r"\b(if|for|while|switch|case|catch|finally)\b")
_GO_CONTROL_FLOW_RE = re.compile(r"\b(if|for|switch|select|case)\b")

_JS_TS_SYMBOL_RE = re.compile(
    r"""(?mx)
    ^\s*export\s+(?:default\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z0-9_]+)\b
    |^\s*export\s+(?:const|let|var)\s+([A-Za-z0-9_]+)\b
    |^\s*export\s+(?:type|interface|enum)\s+([A-Za-z0-9_]+)\b
    """
)

_GO_SYMBOL_RE = re.compile(
    r"""(?mx)
    ^\s*func\s+(?:\([^)]+\)\s*)?([A-Za-z0-9_]+)\s*\(
    |^\s*type\s+([A-Za-z0-9_]+)\s+
    |^\s*var\s+([A-Za-z0-9_]+)\b
    |^\s*const\s+([A-Za-z0-9_]+)\b
    """
)


def _strip_c_like_comments(text: str) -> str:
    text = _C_LIKE_BLOCK_COMMENT_RE.sub("", text)
    text = _C_LIKE_LINE_COMMENT_RE.sub("", text)
    return text


def _compute_c_like_nesting_and_complexity(text: str, keyword_re: re.Pattern[str]) -> tuple[int, int]:
    """
    Very lightweight cognitive complexity approximation for brace-delimited languages.
    Complexity = Σ (1 + current_brace_depth) for each control-flow keyword.
    """
    keyword_positions = [m.start() for m in keyword_re.finditer(text)]
    keyword_positions.sort()

    depth = 0
    max_depth = 0
    complexity = 0
    pos_idx = 0

    for i, ch in enumerate(text):
        while pos_idx < len(keyword_positions) and keyword_positions[pos_idx] == i:
            complexity += 1 + depth
            pos_idx += 1

        if ch == "{":
            depth += 1
            if depth > max_depth:
                max_depth = depth
        elif ch == "}":
            depth = max(depth - 1, 0)

    # Any keyword at EOF (rare) counts with current depth
    while pos_idx < len(keyword_positions):
        complexity += 1 + depth
        pos_idx += 1

    return max_depth, complexity


def _extract_js_ts_imports(text: str) -> List[str]:
    imports: Set[str] = set()
    for match in _JS_TS_IMPORT_RE.finditer(text):
        imports.add(match.group(1))
    for match in _JS_TS_DYNAMIC_IMPORT_RE.finditer(text):
        imports.add(match.group(1))
    for match in _JS_TS_REQUIRE_RE.finditer(text):
        imports.add(match.group(1))
    return sorted(imports)


def _extract_go_imports(text: str) -> List[str]:
    imports: Set[str] = set()

    for match in _GO_IMPORT_SINGLE_RE.finditer(text):
        imports.add(match.group(1))

    for match in _GO_IMPORT_BLOCK_RE.finditer(text):
        block = match.group(1)
        for quoted in _QUOTED_PATH_RE.finditer(block):
            imports.add(quoted.group(1))

    return sorted(imports)

def _extract_symbols_from_regex(text: str, symbol_re: re.Pattern[str]) -> List[str]:
    symbols: List[str] = []
    for m in symbol_re.finditer(text):
        for g in m.groups():
            if g:
                symbols.append(g)
    # De-dupe preserving order
    seen = set()
    out: List[str] = []
    for s in symbols:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _analyze_js_ts(file_path: str, content: str) -> CodeMetric:
    stripped = _strip_c_like_comments(content)
    imports = _extract_js_ts_imports(stripped)
    symbols = _extract_symbols_from_regex(stripped, _JS_TS_SYMBOL_RE)

    nesting_max, complexity = _compute_c_like_nesting_and_complexity(stripped, _JS_TS_CONTROL_FLOW_RE)

    class_count = len(re.findall(r"\bclass\b", stripped))
    function_keyword_count = len(re.findall(r"\bfunction\b", stripped))
    arrow_count = len(re.findall(r"=>", stripped))

    async_count = len(re.findall(r"\basync\b", stripped)) + len(re.findall(r"\bawait\b", stripped))

    patterns: List[str] = []
    import_blob = " ".join(imports)
    if Path(file_path).suffix.lower() in {".jsx", ".tsx"} or "from 'react'" in stripped or 'from "react"' in stripped:
        patterns.append("react_component")
    if re.search(r"\buse(State|Effect|Memo|Callback|Ref|Reducer|Context)\s*\(", stripped):
        patterns.append("react_hook")
        patterns.append("react_component")
    if "@blueprintjs" in import_blob:
        patterns.append("blueprint_ui")
    if "osdk" in import_blob.lower() or "@osdk" in import_blob.lower():
        patterns.append("osdk_client")
    if "graphql" in import_blob.lower() or re.search(r"\bgql\s*`", stripped):
        patterns.append("graphql")
    if "WebSocket" in stripped:
        patterns.append("websocket")
    if "new Worker(" in stripped or "worker_threads" in import_blob:
        patterns.append("worker_thread")

    return CodeMetric(
        file_path=file_path,
        loc=len(content.splitlines()),
        nesting_max=nesting_max,
        control_flow_count=complexity,
        unique_imports=len(set(imports)),
        imports=imports,
        classes=class_count,
        functions=function_keyword_count + arrow_count,
        async_patterns=async_count,
        pydantic_models=0,
        identified_patterns=sorted(set(patterns)),
        symbols=symbols,
    )


def _analyze_go(file_path: str, content: str) -> CodeMetric:
    stripped = _strip_c_like_comments(content)
    imports = _extract_go_imports(stripped)
    symbols = _extract_symbols_from_regex(stripped, _GO_SYMBOL_RE)

    nesting_max, complexity = _compute_c_like_nesting_and_complexity(stripped, _GO_CONTROL_FLOW_RE)

    func_count = len(re.findall(r"\bfunc\b", stripped))
    struct_count = len(re.findall(r"\btype\s+\w+\s+struct\b", stripped))
    interface_count = len(re.findall(r"\btype\s+\w+\s+interface\b", stripped))

    go_stmt_count = len(re.findall(r"\bgo\b", stripped))
    chan_count = len(re.findall(r"\bchan\b", stripped))
    async_count = go_stmt_count + chan_count

    patterns: List[str] = []
    if go_stmt_count:
        patterns.append("goroutine")
    if chan_count:
        patterns.append("channel")
    if any(i == "net/http" for i in imports):
        patterns.append("http_server")
    if any(i.startswith("google.golang.org/grpc") for i in imports):
        patterns.append("grpc")

    return CodeMetric(
        file_path=file_path,
        loc=len(content.splitlines()),
        nesting_max=nesting_max,
        control_flow_count=complexity,
        unique_imports=len(set(imports)),
        imports=imports,
        classes=struct_count + interface_count,
        functions=func_count,
        async_patterns=async_count,
        pydantic_models=0,
        identified_patterns=sorted(set(patterns)),
        symbols=symbols,
    )

def _extract_python_symbols(tree: ast.AST) -> List[str]:
    symbols: List[str] = []
    if not isinstance(tree, ast.Module):
        return symbols
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.append(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                symbols.append(node.target.id)
    # De-dupe preserving order
    seen = set()
    out: List[str] = []
    for s in symbols:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _analyze_python(file_path: str, content: str) -> CodeMetric:
    """Parses Python file content and returns collected metrics."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return CodeMetric(file_path=file_path, loc=len(content.splitlines()))

    symbols = _extract_python_symbols(tree)

    cog_visitor = CognitiveComplexityVisitor()
    cog_visitor.visit(tree)

    con_visitor = ConceptVisitor()
    con_visitor.visit(tree)

    return CodeMetric(
        file_path=file_path,
        loc=len(content.splitlines()),
        nesting_max=cog_visitor.max_nesting,
        control_flow_count=cog_visitor.complexity,
        unique_imports=len(con_visitor.imports),
        imports=list(con_visitor.imports),
        classes=con_visitor.classes,
        functions=con_visitor.functions,
        async_patterns=con_visitor.async_counts,
        pydantic_models=con_visitor.pydantic_counts,
        identified_patterns=list(set(con_visitor.patterns)),
        symbols=symbols,
    )

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
            elif isinstance(base, ast.Name) and base.id == 'ActionType':
                self.patterns.append("action_type")
            elif isinstance(base, ast.Attribute) and base.attr == 'ActionType':
                self.patterns.append("action_type")
        
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
    """Parse source content and return collected metrics (Python / TS/JS / Go)."""
    ext = Path(file_path).suffix.lower()
    if ext == ".py":
        return _analyze_python(file_path, content)
    if ext in _JS_TS_EXTENSIONS:
        return _analyze_js_ts(file_path, content)
    if ext == ".go":
        return _analyze_go(file_path, content)

    return CodeMetric(file_path=file_path, loc=len(content.splitlines()))
