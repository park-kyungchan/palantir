from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import tomllib


_CODE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".go"}

_PATH_IN_COMMAND_RE = re.compile(
    r"""(?x)
    (?P<path>
        (?:\./|\.\./|/)?[A-Za-z0-9_\-./\\]+
        \.(?:py|ts|tsx|js|jsx|mjs|cjs|mts|cts|go)
    )
    """
)
_PYTHON_MODULE_RE = re.compile(r"\bpython(?:\d+(?:\.\d+)*)?\s+-m\s+([A-Za-z0-9_\.]+)")
_NODE_FILE_RE = re.compile(r"\bnode\s+([A-Za-z0-9_\-./\\]+\.(?:js|mjs|cjs))\b")
_TS_RUNNER_FILE_RE = re.compile(r"\b(?:ts-node|tsx|deno\s+run)\s+([A-Za-z0-9_\-./\\]+\.(?:ts|tsx|mts|cts|js|mjs))\b")
_GO_RUN_RE = re.compile(r"\bgo\s+run\s+([^\n\r;]+)")


def _infer_signals(text: str, *, file_type: str) -> list[str]:
    t = text.lower()
    signals: set[str] = set()

    if file_type in {"github_workflow"}:
        signals.add("ci")
    if file_type in {"dockerfile", "compose"}:
        signals.add("deployment")

    if any(k in t for k in ["docker ", "docker\n", "docker-build", "dockerfile", "compose", "buildx"]):
        signals.add("deployment")
        signals.add("build")
    if any(k in t for k in ["kubectl", "helm", "kustomize", "terraform", "pulumi"]):
        signals.add("deployment")
    if any(k in t for k in ["pytest", "go test", "npm test", "pnpm test", "yarn test", "jest", "cypress", "playwright"]):
        signals.add("testing")
    if any(k in t for k in ["npm run build", "pnpm build", "yarn build", "webpack", "vite", "tsc", "go build", "python -m build"]):
        signals.add("build")

    return sorted(signals)


def _safe_relpath(path: Path, root: Path) -> Optional[str]:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return None


def _normalize_command(cmd: str) -> str:
    return cmd.strip().replace("\r\n", "\n").replace("\r", "\n")


def _extract_paths_from_command(cmd: str) -> list[str]:
    paths: list[str] = []
    for m in _PATH_IN_COMMAND_RE.finditer(cmd):
        paths.append(m.group("path"))
    for m in _NODE_FILE_RE.finditer(cmd):
        paths.append(m.group(1))
    for m in _TS_RUNNER_FILE_RE.finditer(cmd):
        paths.append(m.group(1))
    return paths


def _module_to_py_candidates(module: str) -> list[str]:
    p = module.replace(".", "/")
    return [p + ".py", p + "/__init__.py"]


def _extract_python_modules(cmd: str) -> list[str]:
    return [m.group(1) for m in _PYTHON_MODULE_RE.finditer(cmd)]


def _extract_go_run_targets(cmd: str) -> list[str]:
    targets: list[str] = []
    for m in _GO_RUN_RE.finditer(cmd):
        blob = m.group(1)
        # Tokenize crudely; stop at common flags separators.
        for tok in re.split(r"\s+", blob.strip()):
            if not tok or tok.startswith("-"):
                continue
            if tok.startswith("./") or tok.startswith("../"):
                targets.append(tok)
            break
    return targets


def _resolve_referenced_files(root: Path, cmd: str) -> list[str]:
    referenced: set[str] = set()
    cmd = _normalize_command(cmd)

    for raw in _extract_paths_from_command(cmd):
        cleaned = raw.strip().strip("\"'").replace("\\", "/")
        candidate = (root / cleaned).resolve() if not cleaned.startswith("/") else Path(cleaned).resolve()
        rel = _safe_relpath(candidate, root)
        if rel and candidate.exists() and candidate.is_file() and candidate.suffix.lower() in _CODE_EXTS:
            referenced.add(rel)

    for module in _extract_python_modules(cmd):
        for cand in _module_to_py_candidates(module):
            p = (root / cand).resolve()
            rel = _safe_relpath(p, root)
            if rel and p.exists() and p.is_file():
                referenced.add(rel)

    for target in _extract_go_run_targets(cmd):
        t = target.strip().strip("\"'").replace("\\", "/")
        p = (root / t).resolve()
        if p.exists() and p.is_dir():
            main_go = p / "main.go"
            rel = _safe_relpath(main_go, root)
            if rel and main_go.exists():
                referenced.add(rel)
        elif p.exists() and p.is_file() and p.suffix.lower() == ".go":
            rel = _safe_relpath(p, root)
            if rel:
                referenced.add(rel)

    return sorted(referenced)


def _parse_github_workflow_runs(text: str) -> list[str]:
    lines = text.splitlines()
    cmds: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s*)(?:-\s*)?run:\s*(.*)\s*$", line)
        if not m:
            i += 1
            continue
        indent = len(m.group(1))
        rest = m.group(2)
        if rest in {"|", ">", ""}:
            i += 1
            block: list[str] = []
            while i < len(lines):
                l = lines[i]
                if not l.strip():
                    block.append("")
                    i += 1
                    continue
                if len(l) - len(l.lstrip(" ")) <= indent:
                    break
                block.append(l.strip())
                i += 1
            cmd = "\n".join(block).strip()
            if cmd:
                cmds.append(cmd)
            continue
        cmds.append(rest.strip())
        i += 1
    return cmds


def _parse_compose_commands(text: str) -> list[str]:
    cmds: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*(command|entrypoint):\s*(.+?)\s*$", line)
        if not m:
            continue
        cmds.append(m.group(2).strip())
    return cmds


def _parse_dockerfile_commands(text: str) -> list[str]:
    cmds: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(CMD|ENTRYPOINT|RUN)\s+(.+)$", line, flags=re.IGNORECASE)
        if not m:
            continue
        instr = m.group(1).upper()
        rest = m.group(2).strip()
        # JSON array form: CMD ["python","app.py"]
        if rest.startswith("[") and rest.endswith("]"):
            try:
                arr = json.loads(rest)
                if isinstance(arr, list):
                    rest = " ".join(str(x) for x in arr)
            except Exception:
                pass
        cmds.append(f"{instr} {rest}")
    return cmds


def _parse_makefile_commands(text: str) -> list[str]:
    cmds: list[str] = []
    for line in text.splitlines():
        if line.startswith("\t"):
            cmd = line.lstrip("\t").strip()
            if cmd:
                cmds.append(cmd)
    return cmds


def _parse_pyproject_scripts(root: Path, pyproject: Path) -> list[str]:
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except Exception:
        return []

    cmds: list[str] = []
    proj = data.get("project") or {}
    scripts = proj.get("scripts") or {}
    if isinstance(scripts, dict):
        for _, target in scripts.items():
            if isinstance(target, str):
                cmds.append(f"python -m {target.split(':', 1)[0]}")

    poetry = (data.get("tool") or {}).get("poetry") or {}
    poetry_scripts = poetry.get("scripts") or {}
    if isinstance(poetry_scripts, dict):
        for _, target in poetry_scripts.items():
            if isinstance(target, str):
                cmds.append(f"python -m {target.split(':', 1)[0]}")

    return cmds


def scan_workflow_artifacts(root: Path) -> list[dict]:
    """
    Scan common orchestration files (CI/build/deploy) and extract commands + referenced code files.

    Output is designed to be included in the learning context JSON and consumed by any LLM.
    """
    root = root.resolve()
    artifacts: list[dict] = []

    def add_artifact(*, file_type: str, path: Path, commands: list[str]) -> None:
        if not commands:
            return
        rel = _safe_relpath(path, root) or str(path)
        referenced: set[str] = set()
        signals: set[str] = set()
        for cmd in commands:
            cmd_n = _normalize_command(cmd)
            for rf in _resolve_referenced_files(root, cmd_n):
                referenced.add(rf)
            for s in _infer_signals(cmd_n, file_type=file_type):
                signals.add(s)
        artifacts.append(
            {
                "type": file_type,
                "path": rel,
                "signals": sorted(signals),
                "commands": commands[:50],
                "referenced_files": sorted(referenced),
            }
        )

    package_json = root / "package.json"
    if package_json.exists():
        try:
            pkg = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts") or {}
            if isinstance(scripts, dict):
                cmds = [str(v) for v in scripts.values() if isinstance(v, str) and v.strip()]
                add_artifact(file_type="package_json", path=package_json, commands=cmds)
        except Exception:
            pass

    dockerfile = root / "Dockerfile"
    if dockerfile.exists():
        try:
            add_artifact(file_type="dockerfile", path=dockerfile, commands=_parse_dockerfile_commands(dockerfile.read_text(encoding="utf-8")))
        except Exception:
            pass

    makefile = root / "Makefile"
    if makefile.exists():
        try:
            add_artifact(file_type="makefile", path=makefile, commands=_parse_makefile_commands(makefile.read_text(encoding="utf-8")))
        except Exception:
            pass

    for name in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]:
        p = root / name
        if not p.exists():
            continue
        try:
            add_artifact(file_type="compose", path=p, commands=_parse_compose_commands(p.read_text(encoding="utf-8")))
        except Exception:
            pass

    gh_dir = root / ".github" / "workflows"
    if gh_dir.exists() and gh_dir.is_dir():
        for wf in sorted(list(gh_dir.glob("*.yml")) + list(gh_dir.glob("*.yaml"))):
            try:
                cmds = _parse_github_workflow_runs(wf.read_text(encoding="utf-8"))
                add_artifact(file_type="github_workflow", path=wf, commands=cmds)
            except Exception:
                continue

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        cmds = _parse_pyproject_scripts(root, pyproject)
        add_artifact(file_type="pyproject", path=pyproject, commands=cmds)

    return artifacts
