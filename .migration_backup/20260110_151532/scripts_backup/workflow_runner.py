#!/usr/bin/env python3
"""
Workflow Runner: Executes .agent/workflows/*.md by parsing and running commands.
Part of ODA scripts/ ↔ workflows/ integration.
"""
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass

WORKFLOWS_DIR = Path("/home/palantir/park-kyungchan/palantir/.agent/workflows")
PROJECT_ROOT = WORKFLOWS_DIR.parent.parent


@dataclass
class WorkflowCommand:
    """Extracted command from workflow."""
    command: str
    is_turbo: bool
    description: str


def extract_commands(workflow_path: Path) -> list[WorkflowCommand]:
    """Extract shell commands from workflow markdown."""
    content = workflow_path.read_text()
    commands: list[WorkflowCommand] = []

    # Pattern: optional // turbo comment, then ```bash block
    pattern = r"(// turbo\n)?```bash\n(.*?)\n```"
    matches = re.findall(pattern, content, re.DOTALL)

    for turbo_marker, cmd_block in matches:
        block = cmd_block.strip()
        if "<<'PY'" in block or "<<PY" in block:
            commands.append(WorkflowCommand(
                command=block,
                is_turbo=bool(turbo_marker),
                description=""
            ))
            continue
        for line in block.split("\n"):
            if line.strip() and not line.startswith("#"):
                commands.append(WorkflowCommand(
                    command=line.strip(),
                    is_turbo=bool(turbo_marker),
                    description=""
                ))

    return commands


def _render_command(command: str, params: dict[str, str]) -> str:
    rendered = command
    for key, value in params.items():
        rendered = rendered.replace(f"${{{key}}}", value)
    return rendered


def execute_workflow(name: str, turbo_only: bool = False, params: dict[str, str] | None = None, dry_run: bool = False) -> dict:
    """
    Execute a workflow by name.
    
    Args:
        name: Workflow name (e.g., "01_plan" or "07_memory_sync")
        turbo_only: If True, only execute commands marked with // turbo
    
    Returns:
        Dict with results per command
    """
    workflow_path = WORKFLOWS_DIR / f"{name}.md"
    
    if not workflow_path.exists():
        return {"error": f"Workflow not found: {workflow_path}"}
    
    commands = extract_commands(workflow_path)
    results = {"workflow": name, "commands": []}
    params = params or {}
    
    for cmd in commands:
        if turbo_only and not cmd.is_turbo:
            continue
        rendered_command = _render_command(cmd.command, params)
        try:
            if dry_run:
                results["commands"].append({
                    "command": rendered_command,
                    "is_turbo": cmd.is_turbo,
                    "returncode": 0,
                    "stdout": "DRY_RUN",
                    "stderr": ""
                })
                continue

            result = subprocess.run(
                ["bash", "-lc", rendered_command],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT
            )
            results["commands"].append({
                "command": rendered_command,
                "is_turbo": cmd.is_turbo,
                "returncode": result.returncode,
                "stdout": result.stdout[:500] if result.stdout else "",
                "stderr": result.stderr[:200] if result.stderr else ""
            })
        except Exception as e:
            results["commands"].append({
                "command": cmd.command,
                "error": str(e)
            })
    
    return results


def list_workflows() -> list[str]:
    """List all available workflows."""
    return [p.stem for p in WORKFLOWS_DIR.glob("*.md")]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Available workflows:")
        for wf in list_workflows():
            print(f"  - {wf}")
        print("\nUsage: python workflow_runner.py <workflow_name> [--turbo]")
        sys.exit(0)
    
    name = sys.argv[1]
    turbo_only = "--turbo" in sys.argv
    
    result = execute_workflow(name, turbo_only)
    print(f"Executed workflow: {name}")
    for cmd_result in result.get("commands", []):
        status = "✓" if cmd_result.get("returncode") == 0 else "✗"
        print(f"  {status} {cmd_result['command'][:50]}...")
