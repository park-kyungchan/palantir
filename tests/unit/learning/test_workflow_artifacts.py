from __future__ import annotations

from pathlib import Path

from lib.oda.ontology.learning.engine import TutoringEngine
from lib.oda.ontology.learning.prompt_scope import build_prompt_scope
from lib.oda.ontology.learning.workflow_artifacts import scan_workflow_artifacts


def test_scan_workflow_artifacts_extracts_github_run_and_references(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(
        "name: CI\n"
        "on: [push]\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: Run\n"
        "        run: python src/main.py\n",
        encoding="utf-8",
    )

    artifacts = scan_workflow_artifacts(tmp_path)
    assert artifacts, "expected at least one artifact"
    gh = next(a for a in artifacts if a["type"] == "github_workflow")
    assert "ci" in gh["signals"]
    assert "src/main.py" in gh["referenced_files"]


def test_prompt_scope_seeds_files_from_workflow_artifacts(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(
        "jobs:\n"
        "  test:\n"
        "    steps:\n"
        "      - run: python src/main.py\n",
        encoding="utf-8",
    )

    engine = TutoringEngine(str(tmp_path))
    engine.scan_codebase()
    engine.calculate_scores()

    artifacts = scan_workflow_artifacts(tmp_path)

    scope = build_prompt_scope(
        prompt="workflow entrypoint",
        tutor=engine,
        entrypoints=[],
        workflow_artifacts=artifacts,
        limit=5,
    )

    allowlist = set(scope["allowlist"])
    assert "src/main.py" in allowlist
    assert scope.get("workflow_artifact_hits"), "expected artifact hits in prompt scope"

