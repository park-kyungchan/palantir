"""
Orion Phase 5 - Dependency Graph Engine
Parses imports to build a directed graph and calculate topological depth.
Deep Context Awareness: Resolves relative imports and mapping to file system.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional

from .types import CodeMetric

_JS_TS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"}
_JS_TS_RESOLVE_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".mjs", ".cjs"]

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


def _strip_c_like_comments(text: str) -> str:
    text = _C_LIKE_BLOCK_COMMENT_RE.sub("", text)
    text = _C_LIKE_LINE_COMMENT_RE.sub("", text)
    return text


class PythonImportVisitor(ast.NodeVisitor):
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
        self._go_module_path = self._read_go_module_path()

    def _read_go_module_path(self) -> Optional[str]:
        go_mod = self.root / "go.mod"
        if not go_mod.exists():
            return None
        try:
            for line in go_mod.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("module "):
                    parts = stripped.split()
                    return parts[1] if len(parts) > 1 else None
        except OSError:
            return None
        return None

    def _module_to_path_py(self, module_name: str, current_file: str) -> Optional[str]:
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

    def _extract_imports(self, rel_path: str, content: str) -> List[str]:
        ext = Path(rel_path).suffix.lower()
        if ext == ".py":
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return []
            visitor = PythonImportVisitor()
            visitor.visit(tree)
            return visitor.imports

        stripped = _strip_c_like_comments(content)

        if ext in _JS_TS_EXTENSIONS:
            imports: Set[str] = set()
            for match in _JS_TS_IMPORT_RE.finditer(stripped):
                imports.add(match.group(1))
            for match in _JS_TS_DYNAMIC_IMPORT_RE.finditer(stripped):
                imports.add(match.group(1))
            for match in _JS_TS_REQUIRE_RE.finditer(stripped):
                imports.add(match.group(1))
            return sorted(imports)

        if ext == ".go":
            imports: Set[str] = set()
            for match in _GO_IMPORT_SINGLE_RE.finditer(stripped):
                imports.add(match.group(1))
            for match in _GO_IMPORT_BLOCK_RE.finditer(stripped):
                block = match.group(1)
                for quoted in _QUOTED_PATH_RE.finditer(block):
                    imports.add(quoted.group(1))
            return sorted(imports)

        return []

    def _module_to_path_js_ts(self, module_name: str, current_file: Path) -> Optional[str]:
        module_name = module_name.split("?", 1)[0].split("#", 1)[0].strip()
        if not module_name:
            return None
        if not (module_name.startswith(".") or module_name.startswith("/")):
            return None

        if module_name.startswith("/"):
            target = (self.root / module_name.lstrip("/")).resolve()
        else:
            target = (current_file.parent / module_name).resolve()

        candidates: List[Path] = []
        if target.suffix:
            candidates.append(target)
            # TS projects often import JS extension while source is TS/TSX.
            if target.suffix in {".js", ".jsx", ".mjs", ".cjs"}:
                candidates.append(target.with_suffix(".ts"))
                candidates.append(target.with_suffix(".tsx"))
        else:
            for ext in _JS_TS_RESOLVE_EXTENSIONS:
                candidates.append(Path(str(target) + ext))
                candidates.append(Path(str(target) + ".d" + ext))  # allow foo.d.ts patterns
            for ext in _JS_TS_RESOLVE_EXTENSIONS:
                candidates.append(target / ("index" + ext))
                candidates.append(target / ("index.d" + ext))

        for cand in candidates:
            try:
                rel = cand.resolve().relative_to(self.root)
            except ValueError:
                continue
            if cand.exists() and cand.is_file():
                return str(rel)
        return None

    def _pick_go_file_in_dir(self, directory: Path) -> Optional[Path]:
        if not directory.exists() or not directory.is_dir():
            return None
        preferred = ["doc.go", "main.go"]
        for name in preferred:
            cand = directory / name
            if cand.exists() and cand.is_file():
                return cand
        go_files = sorted(p for p in directory.glob("*.go") if not p.name.endswith("_test.go"))
        return go_files[0] if go_files else None

    def _module_to_path_go(self, module_name: str, current_file: Path) -> Optional[str]:
        module_name = module_name.strip()
        if not module_name:
            return None

        # Relative imports are uncommon in module mode, but handle defensively.
        if module_name.startswith("."):
            target_dir = (current_file.parent / module_name).resolve()
            picked = self._pick_go_file_in_dir(target_dir)
            if picked is None:
                return None
            try:
                return str(picked.relative_to(self.root))
            except ValueError:
                return None

        if not self._go_module_path:
            return None
        if not module_name.startswith(self._go_module_path):
            return None

        rel_pkg = module_name[len(self._go_module_path):].lstrip("/")
        target_dir = (self.root / rel_pkg).resolve()

        if target_dir.is_file() and target_dir.suffix == ".go":
            try:
                return str(target_dir.relative_to(self.root))
            except ValueError:
                return None

        picked = self._pick_go_file_in_dir(target_dir)
        if picked is None:
            return None
        try:
            return str(picked.relative_to(self.root))
        except ValueError:
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
                mods = self._extract_imports(f, content)

                ext = Path(f).suffix.lower()
                for mod in mods:
                    if ext == ".py":
                        resolved = self._module_to_path_py(mod, str(full_path))
                    elif ext in _JS_TS_EXTENSIONS:
                        resolved = self._module_to_path_js_ts(mod, full_path)
                    elif ext == ".go":
                        resolved = self._module_to_path_go(mod, full_path)
                    else:
                        resolved = None

                    if resolved and resolved in self.adj_list:
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
