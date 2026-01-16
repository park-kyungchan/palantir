"""
Unit tests for multi-language Codebase-as-Curriculum (TutoringEngine + DependencyGraph).

These tests validate basic TS/JS and Go parsing without relying on any DB/aiosqlite.
"""

from __future__ import annotations

from pathlib import Path

from lib.oda.ontology.learning.engine import TutoringEngine
from lib.oda.ontology.run_tutor import _is_entrypoint


def test_typescript_relative_import_resolves(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "b.ts").write_text("export const b = 1;\n", encoding="utf-8")
    (tmp_path / "src" / "a.ts").write_text(
        "import { b } from './b';\n"
        "export function f(x: number) {\n"
        "  if (x > b) { return x; }\n"
        "  return b;\n"
        "}\n",
        encoding="utf-8",
    )

    engine = TutoringEngine(str(tmp_path))
    engine.scan_codebase()
    engine.calculate_scores()

    assert "src/a.ts" in engine.dependency_graph.adj_list
    assert "src/b.ts" in engine.dependency_graph.adj_list["src/a.ts"]


def test_typescript_directory_import_resolves_to_index(tmp_path: Path) -> None:
    (tmp_path / "src" / "utils").mkdir(parents=True)
    (tmp_path / "src" / "utils" / "index.ts").write_text("export const x = 1;\n", encoding="utf-8")
    (tmp_path / "src" / "app.ts").write_text(
        "import { x } from './utils';\n"
        "export const y = x + 1;\n",
        encoding="utf-8",
    )

    engine = TutoringEngine(str(tmp_path))
    engine.scan_codebase()
    engine.calculate_scores()

    assert "src/app.ts" in engine.dependency_graph.adj_list
    assert "src/utils/index.ts" in engine.dependency_graph.adj_list["src/app.ts"]


def test_go_internal_import_resolves_via_go_mod(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/proj\n\ngo 1.22\n", encoding="utf-8")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "pkg.go").write_text(
        "package pkg\n\nfunc Add(a int, b int) int { return a + b }\n",
        encoding="utf-8",
    )
    (tmp_path / "main.go").write_text(
        "package main\n\nimport \"example.com/proj/pkg\"\n\nfunc main() { _ = pkg.Add(1, 2) }\n",
        encoding="utf-8",
    )

    engine = TutoringEngine(str(tmp_path))
    engine.scan_codebase()
    engine.calculate_scores()

    assert "main.go" in engine.dependency_graph.adj_list
    assert "pkg/pkg.go" in engine.dependency_graph.adj_list["main.go"]


def test_entrypoint_detection_basic() -> None:
    assert _is_entrypoint("main.go", "package main\n\nfunc main() {}\n") is True
    assert _is_entrypoint("cli.ts", "#!/usr/bin/env node\nconsole.log(process.argv)\n") is True
    assert _is_entrypoint("not_entry.ts", "export const x = 1;\n") is False

