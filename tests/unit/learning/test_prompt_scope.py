"""
Unit tests for prompt-scoped decomposition (agile prompt -> relevant files).

These tests are heuristic by design: we validate that key intents and matches
produce stable, useful scoping outputs without requiring external parsers.
"""

from __future__ import annotations

from pathlib import Path

from lib.oda.ontology.learning.engine import TutoringEngine
from lib.oda.ontology.learning.prompt_scope import build_prompt_scope
from lib.oda.ontology.run_tutor import _is_entrypoint


def test_prompt_scope_suggests_entrypoint_for_korean_workflow_prompt(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    app = tmp_path / "src" / "app.ts"
    app.write_text(
        "import React from 'react';\n"
        "import { createRoot } from 'react-dom/client';\n"
        "createRoot(document.getElementById('root')!).render(<div />);\n",
        encoding="utf-8",
    )

    engine = TutoringEngine(str(tmp_path))
    engine.scan_codebase()
    engine.calculate_scores()

    assert _is_entrypoint("src/app.ts", app.read_text(encoding="utf-8")) is True

    scope = build_prompt_scope(
        prompt="ODA 시스템의 워크플로우에 대해서 진입점부터 학습할거야",
        tutor=engine,
        entrypoints=["src/app.ts"],
        limit=5,
    )

    suggested = [s["file"] for s in scope["suggested_entrypoints"]]
    ranked = [r["file"] for r in scope["ranked_files"]]

    assert "src/app.ts" in suggested
    assert "src/app.ts" in ranked


def test_prompt_scope_go_grpc_matches_patterns_and_language(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/proj\n\ngo 1.22\n", encoding="utf-8")
    (tmp_path / "main.go").write_text(
        "package main\n\n"
        "import (\n"
        "  \"net/http\"\n"
        "  \"google.golang.org/grpc\"\n"
        ")\n\n"
        "func main() { _ = http.ListenAndServe(\":0\", nil); _ = grpc.NewServer() }\n",
        encoding="utf-8",
    )

    engine = TutoringEngine(str(tmp_path))
    engine.scan_codebase()
    engine.calculate_scores()

    scope = build_prompt_scope(
        prompt="go grpc server entrypoint",
        tutor=engine,
        entrypoints=["main.go"],
        limit=3,
    )

    assert scope["ranked_files"], "expected at least one ranked file"
    assert scope["ranked_files"][0]["file"] == "main.go"


def test_prompt_scope_expands_to_dependencies(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "lib.ts").write_text("export const x = 1;\n", encoding="utf-8")
    (tmp_path / "src" / "app.ts").write_text(
        "import { x } from './lib';\n"
        "export const y = x + 1;\n",
        encoding="utf-8",
    )

    engine = TutoringEngine(str(tmp_path))
    engine.scan_codebase()
    engine.calculate_scores()

    scope = build_prompt_scope(
        prompt="app",
        tutor=engine,
        entrypoints=[],
        limit=5,
    )

    allowlist = set(scope["allowlist"])
    assert "src/app.ts" in allowlist
    assert "src/lib.ts" in allowlist


def test_prompt_scope_matches_symbol_names(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text(
        "export function startWorkflow() { return 1; }\n",
        encoding="utf-8",
    )

    engine = TutoringEngine(str(tmp_path))
    engine.scan_codebase()
    engine.calculate_scores()

    scope = build_prompt_scope(
        prompt="startWorkflow",
        tutor=engine,
        entrypoints=[],
        limit=5,
    )

    assert "src/app.ts" in set(scope["allowlist"])
