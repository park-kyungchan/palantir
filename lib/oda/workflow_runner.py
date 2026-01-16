#!/usr/bin/env python3
"""
Workflow Runner: Executes .agent/workflows/*.md by parsing and running commands.
Part of ODA scripts/ ↔ workflows/ integration.

Security: ODA-RISK-014 Resolved - Command injection protection added.
"""
import re
import shlex
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from lib.oda.paths import get_workflows_dir, get_workspace_root

WORKFLOWS_DIR = get_workflows_dir()
PROJECT_ROOT = get_workspace_root()

# Security: Blocked dangerous patterns (ODA-RISK-014)
BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/",           # Recursive delete from root
    r"rm\s+-rf\s+~",           # Recursive delete from home
    r"sudo\s+rm",              # Sudo removal
    r"chmod\s+777",            # Insecure permissions
    r">\s*/etc/",              # Overwrite system files
    r";\s*rm\s+",              # Command chain with rm
    r"\|\s*sh\b",              # Pipe to shell
    r"\|\s*bash\b",            # Pipe to bash
    r"\$\(.*rm.*\)",           # Command substitution with rm
    r"`.*rm.*`",               # Backtick substitution with rm
    r"eval\s+",                # Eval command
    r"exec\s+",                # Exec command
]
BLOCKED_REGEX = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)


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


def _validate_command(command: str) -> Optional[str]:
    """
    Validate command for dangerous patterns.

    Returns:
        Error message if dangerous pattern found, None if safe.
    """
    if BLOCKED_REGEX.search(command):
        return f"Blocked dangerous pattern in command: {command[:100]}..."
    return None


def _sanitize_param(value: str) -> str:
    """Sanitize parameter value to prevent injection."""
    # Remove shell metacharacters that could enable injection
    dangerous_chars = [";", "|", "&", "$", "`", "(", ")", "{", "}", "<", ">", "\n", "\r"]
    sanitized = value
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    return sanitized


def _render_command(command: str, params: dict[str, str]) -> str:
    """
    Render command with sanitized parameter substitution.

    Security: Parameters are sanitized before substitution (ODA-RISK-014).
    """
    rendered = command
    for key, value in params.items():
        sanitized_value = _sanitize_param(str(value))
        rendered = rendered.replace(f"${{{key}}}", sanitized_value)
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

        # Security: Validate command before execution (ODA-RISK-014)
        validation_error = _validate_command(rendered_command)
        if validation_error:
            results["commands"].append({
                "command": rendered_command[:100],
                "is_turbo": cmd.is_turbo,
                "error": validation_error,
                "blocked": True
            })
            continue

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
                cwd=PROJECT_ROOT,
                timeout=300  # 5 minute timeout for safety
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
