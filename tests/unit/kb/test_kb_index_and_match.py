"""
Unit tests for KB indexing + prompt-scope to KB matching.
"""

from __future__ import annotations

from pathlib import Path

from lib.oda.ontology.kb.index import build_kb_index
from lib.oda.ontology.kb.match import match_kbs


def test_build_kb_index_extracts_paths_and_languages(tmp_path: Path) -> None:
    kb_root = tmp_path / "coding" / "knowledge_bases"
    kb_root.mkdir(parents=True)

    (kb_root / "01_go_basics.md").write_text(
        "# Go Basics\n\n```go\npackage main\n```\n",
        encoding="utf-8",
    )
    (kb_root / "02_python_async.md").write_text(
        "# Python Async\n\n```python\nasync def f():\n  return 1\n```\n",
        encoding="utf-8",
    )

    index = build_kb_index(kb_root)
    paths = {d["path"] for d in index["documents"]}
    assert "coding/knowledge_bases/01_go_basics.md" in paths
    assert "coding/knowledge_bases/02_python_async.md" in paths

    langs_by_path = {d["path"]: set(d.get("languages") or []) for d in index["documents"]}
    assert "go" in langs_by_path["coding/knowledge_bases/01_go_basics.md"]
    assert "python" in langs_by_path["coding/knowledge_bases/02_python_async.md"]


def test_match_kbs_prefers_language_and_term_hits(tmp_path: Path) -> None:
    kb_root = tmp_path / "coding" / "knowledge_bases"
    kb_root.mkdir(parents=True)

    (kb_root / "01_go_grpc.md").write_text(
        "# gRPC in Go\n\n```go\nimport \"google.golang.org/grpc\"\n```\n",
        encoding="utf-8",
    )
    (kb_root / "02_react_hooks.md").write_text(
        "# React Hooks\n\n```tsx\nconst [x, setX] = useState(0)\n```\n",
        encoding="utf-8",
    )

    index = build_kb_index(kb_root)

    prompt_scope = {
        "terms": ["go", "grpc", "entrypoint"],
        "intent": {"wants_go": True, "wants_ts_js": False, "wants_python": False},
        "ranked_files": [{"patterns": ["grpc"]}],
    }

    matches = match_kbs(prompt_scope=prompt_scope, kb_index=index, limit=3)
    assert matches, "expected at least one KB match"
    assert matches[0]["path"] == "coding/knowledge_bases/01_go_grpc.md"

