#!/usr/bin/env python3
"""
Sync .agent/workflows to a Codex CLI slash-command registry.

This creates a simple registry under ~/.codex/commands that can be referenced
by agent instructions for slash command routing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List


def _workspace_root() -> Path:
    env_root = os.environ.get("ORION_WORKSPACE_ROOT")
    if env_root:
        return Path(env_root)
    return Path(__file__).resolve().parents[2]


def _extract_description(lines: List[str]) -> str:
    in_front_matter = False
    for line in lines[:40]:
        stripped = line.strip()
        if stripped == "---":
            in_front_matter = not in_front_matter
            continue
        if in_front_matter and stripped.startswith("description:"):
            return stripped.split(":", 1)[1].strip().strip('"')
    return ""


def sync_codex_commands() -> Dict[str, object]:
    root = _workspace_root()
    workflows_dir = root / ".agent" / "workflows"
    codex_commands_dir = Path.home() / ".codex" / "commands"
    codex_commands_dir.mkdir(parents=True, exist_ok=True)

    workflow_files = sorted(workflows_dir.glob("*.md"))
    commands: List[Dict[str, str]] = []

    for wf in workflow_files:
        lines = wf.read_text(encoding="utf-8").splitlines()
        commands.append(
            {
                "name": wf.stem,
                "description": _extract_description(lines),
                "path": str(wf),
                "run": f"python {root}/scripts/workflow_runner.py {wf.stem}",
            }
        )

    registry_path = codex_commands_dir / "workflows.json"
    registry_path.write_text(json.dumps(commands, indent=2), encoding="utf-8")

    readme_path = codex_commands_dir / "README.md"
    readme_lines = [
        "# Codex Workflow Slash Commands",
        "",
        "This directory is generated from `.agent/workflows`.",
        "Invoke a workflow with `/<workflow_name>` in Codex CLI.",
        "",
        "## Available Commands",
        "",
    ]
    for item in commands:
        description = f" - {item['description']}" if item["description"] else ""
        readme_lines.append(f"- `/{item['name']}`{description}")
    readme_lines.append("")
    readme_path.write_text("\n".join(readme_lines), encoding="utf-8")

    return {
        "workflows_dir": str(workflows_dir),
        "commands_dir": str(codex_commands_dir),
        "count": len(commands),
        "registry": str(registry_path),
    }


if __name__ == "__main__":
    result = sync_codex_commands()
    print(json.dumps(result, indent=2))
