#!/usr/bin/env python3
"""
ODA-aligned MCP tooling manager.

Goals:
- Keep MCP server definitions consistent across multiple agents (Antigravity/Gemini, Claude, etc.)
- Support installing the GitHub MCP server as a native binary (no Docker dependency)
- Avoid leaking secrets: never print env values, only env keys
- Cross-platform support: Works on Linux, macOS, and Windows

Windows Compatibility:
- Automatically detects Windows and uses appropriate paths (USERPROFILE instead of /home/palantir)
- Supports both .tar.gz (Unix) and .zip (Windows) archive formats
- Handles Windows-specific binary names (.exe extension)
- Use ORION_WORKSPACE_ROOT environment variable to override default workspace location

This module is intentionally stdlib-only so it can run regardless of which LLM/agent invokes it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import tarfile
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.request import Request, urlopen
import logging

logger = logging.getLogger(__name__)


def _get_default_workspace_root() -> str:
    """Get platform-appropriate default workspace root."""
    if platform.system() == "Windows":
        # Use USERPROFILE on Windows (e.g., C:\Users\username)
        return os.environ.get("USERPROFILE", os.path.expanduser("~"))
    else:
        # Unix-like systems
        return "/home/palantir"


WORKSPACE_ROOT = os.environ.get("ORION_WORKSPACE_ROOT", _get_default_workspace_root())

ANTIGRAVITY_MCP_CONFIG_PATH = os.path.join(WORKSPACE_ROOT, ".gemini", "antigravity", "mcp_config.json")
CLAUDE_CONFIG_PATH = os.path.join(WORKSPACE_ROOT, ".claude.json")

MCP_REGISTRY_PATH = os.path.join(WORKSPACE_ROOT, ".agent", "mcp", "registry.json")
MCP_AUDIT_LOG_PATH = os.path.join(WORKSPACE_ROOT, ".agent", "logs", "mcp_audit.jsonl")

DEFAULT_GITHUB_MCP_INSTALL_PATH = os.path.join(WORKSPACE_ROOT, ".local", "bin", "github-mcp-server")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_parent_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    _ensure_parent_dir(path)
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp.", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _append_audit(event: Dict[str, Any]) -> None:
    safe_event = dict(event)
    safe_event.setdefault("timestamp", _utc_now_iso())
    _ensure_parent_dir(MCP_AUDIT_LOG_PATH)
    with open(MCP_AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(safe_event, ensure_ascii=False))
        f.write("\n")


def _redact_env_values(env: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    if not env:
        return env
    redacted: Dict[str, str] = {}
    for k in env.keys():
        redacted[str(k)] = "***REDACTED***"
    return redacted


def _normalize_server_id(server_key: str) -> str:
    # Keep canonical IDs stable across tools.
    if server_key == "github-mcp-server":
        return "github"
    return server_key


def _antigravity_key_for_id(server_id: str) -> str:
    if server_id == "github":
        return "github-mcp-server"
    return server_id


def _load_antigravity_config(path: str = ANTIGRAVITY_MCP_CONFIG_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"mcpServers": {}}
    config = _read_json(path)
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    if not isinstance(config["mcpServers"], dict):
        raise ValueError(f"Invalid Antigravity MCP config: mcpServers must be an object: {path}")
    return config


def _load_claude_config(path: str = CLAUDE_CONFIG_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Claude config not found: {path}")
    return _read_json(path)


def _ensure_claude_project(config: Dict[str, Any], project_path: str) -> Dict[str, Any]:
    projects = config.setdefault("projects", {})
    if not isinstance(projects, dict):
        raise ValueError("Invalid Claude config: projects must be an object")
    project = projects.setdefault(project_path, {})
    if not isinstance(project, dict):
        raise ValueError("Invalid Claude config: projects.<path> must be an object")
    mcp_servers = project.setdefault("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        raise ValueError("Invalid Claude config: projects.<path>.mcpServers must be an object")
    return project


def _detect_github_asset() -> Tuple[str, str]:
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Linux":
        if machine in {"x86_64", "amd64"}:
            return "Linux_x86_64", "tar.gz"
        if machine in {"aarch64", "arm64"}:
            return "Linux_arm64", "tar.gz"
        if machine in {"i386", "i686"}:
            return "Linux_i386", "tar.gz"
    if system == "Darwin":
        if machine in {"arm64", "aarch64"}:
            return "Darwin_arm64", "tar.gz"
        if machine in {"x86_64", "amd64"}:
            return "Darwin_x86_64", "tar.gz"
    if system == "Windows":
        if machine in {"arm64", "aarch64"}:
            return "Windows_arm64", "zip"
        if machine in {"x86_64", "amd64"}:
            return "Windows_x86_64", "zip"
        if machine in {"i386", "i686"}:
            return "Windows_i386", "zip"

    raise RuntimeError(f"Unsupported platform: system={system} machine={machine}")


def _http_get_json(url: str) -> Dict[str, Any]:
    req = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "orion-mcp-manager"})
    with urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object from {url}")
    return data


def _http_download(url: str, dest_path: str) -> None:
    req = Request(url, headers={"User-Agent": "orion-mcp-manager"})
    _ensure_parent_dir(dest_path)
    with urlopen(req, timeout=60) as r, open(dest_path, "wb") as f:
        shutil.copyfileobj(r, f)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_checksums_file(path: str) -> Dict[str, str]:
    checksums: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                continue
            sha, name = parts
            checksums[name] = sha
    return checksums


def install_github_mcp_server(*, install_path: str = DEFAULT_GITHUB_MCP_INSTALL_PATH, tag: str = "latest") -> Dict[str, Any]:
    """
    Download and install GitHub's github-mcp-server as a native binary.
    """
    suffix, ext = _detect_github_asset()
    release_url = "https://api.github.com/repos/github/github-mcp-server/releases/latest"
    if tag != "latest":
        release_url = f"https://api.github.com/repos/github/github-mcp-server/releases/tags/{tag}"

    release = _http_get_json(release_url)
    tag_name = release.get("tag_name") or tag

    asset_name = f"github-mcp-server_{suffix}.{ext}"
    # Release assets use slightly different naming, e.g. github-mcp-server_Linux_x86_64.tar.gz
    if suffix.startswith("Linux") or suffix.startswith("Darwin"):
        asset_name = f"github-mcp-server_{suffix}.tar.gz"
    if suffix.startswith("Windows"):
        asset_name = f"github-mcp-server_{suffix}.zip"

    download_url = f"https://github.com/github/github-mcp-server/releases/download/{tag_name}/{asset_name}"
    checksums_url = f"https://github.com/github/github-mcp-server/releases/download/{tag_name}/github-mcp-server_{tag_name.lstrip('v')}_checksums.txt"

    with tempfile.TemporaryDirectory(prefix="github-mcp-server.") as tmp_dir:
        archive_path = os.path.join(tmp_dir, asset_name)
        checksums_path = os.path.join(tmp_dir, "checksums.txt")
        _http_download(download_url, archive_path)
        _http_download(checksums_url, checksums_path)

        checksums = _parse_checksums_file(checksums_path)
        expected = checksums.get(asset_name)
        if not expected:
            raise RuntimeError(f"Checksum for {asset_name} not found in checksums file")

        actual = _sha256_file(archive_path)
        if actual != expected:
            raise RuntimeError(f"Checksum mismatch for {asset_name}: expected {expected}, got {actual}")

        extracted_binary_path: Optional[str] = None
        binary_name = "github-mcp-server.exe" if platform.system() == "Windows" else "github-mcp-server"

        if asset_name.endswith(".tar.gz"):
            # Extract tar.gz (Unix-like systems)
            with tarfile.open(archive_path, "r:gz") as tar:
                for member in tar.getmembers():
                    base = os.path.basename(member.name)
                    if member.isfile() and (base == "github-mcp-server" or base == "github-mcp-server.exe"):
                        extracted_binary_path = os.path.join(tmp_dir, base)
                        extracted = tar.extractfile(member)
                        if extracted is None:
                            raise RuntimeError(f"Failed to read {base} binary from archive")
                        with extracted, open(extracted_binary_path, "wb") as out:
                            shutil.copyfileobj(extracted, out)
                        break
        elif asset_name.endswith(".zip"):
            # Extract zip (Windows)
            with zipfile.ZipFile(archive_path, "r") as zf:
                for member_name in zf.namelist():
                    base = os.path.basename(member_name)
                    if base == "github-mcp-server.exe" or base == "github-mcp-server":
                        extracted_binary_path = os.path.join(tmp_dir, base)
                        with zf.open(member_name) as extracted, open(extracted_binary_path, "wb") as out:
                            shutil.copyfileobj(extracted, out)
                        break
        else:
            raise RuntimeError(f"Unsupported archive format: {asset_name}")

        if not extracted_binary_path or not os.path.exists(extracted_binary_path):
            raise RuntimeError(f"Failed to extract {binary_name} binary from archive")

        _ensure_parent_dir(install_path)
        shutil.copy2(extracted_binary_path, install_path)
        # Set executable permissions (Unix-like systems only)
        if platform.system() != "Windows":
            os.chmod(install_path, 0o755)

    _append_audit(
        {
            "action": "install_github_mcp_server",
            "tag": tag_name,
            "install_path": install_path,
        }
    )
    return {"status": "ok", "tag": tag_name, "install_path": install_path}


def _load_registry(path: str = MCP_REGISTRY_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"version": 1, "workspaceRoot": WORKSPACE_ROOT, "servers": {}}
    reg = _read_json(path)
    reg.setdefault("version", 1)
    reg.setdefault("workspaceRoot", WORKSPACE_ROOT)
    reg.setdefault("servers", {})
    if not isinstance(reg["servers"], dict):
        raise ValueError(f"Invalid MCP registry: servers must be an object: {path}")
    return reg


def _write_registry(registry: Dict[str, Any], path: str = MCP_REGISTRY_PATH) -> None:
    _atomic_write_json(path, registry)


def init_registry_from_existing(*, write: bool = False) -> Dict[str, Any]:
    """
    Initialize (or update) the canonical MCP registry by introspecting existing tool configs.

    Env values are not stored; only env keys.
    """
    registry = _load_registry()
    servers: Dict[str, Any] = dict(registry.get("servers") or {})

    # Antigravity source
    try:
        ag = _load_antigravity_config()
        for key, server in (ag.get("mcpServers") or {}).items():
            if not isinstance(server, dict):
                continue
            server_id = _normalize_server_id(key)
            entry = servers.get(server_id, {})
            entry.setdefault("type", "stdio")
            if "command" in server:
                entry["command"] = server.get("command")
            if "args" in server:
                entry["args"] = server.get("args")
            env = server.get("env")
            if isinstance(env, dict):
                entry.setdefault("envKeys", sorted(set(map(str, env.keys()))))
            if server.get("disabled") is True:
                entry["disabled"] = True
            servers[server_id] = entry
    except Exception as e:
        # No Antigravity config: log and continue gracefully
        logger.debug("Failed to load Antigravity MCP config: %s", e)

    # Claude source (project scoped)
    try:
        cc = _load_claude_config()
        project = cc.get("projects", {}).get(WORKSPACE_ROOT, {})
        mcp_servers = project.get("mcpServers", {}) if isinstance(project, dict) else {}
        if isinstance(mcp_servers, dict):
            for key, server in mcp_servers.items():
                if not isinstance(server, dict):
                    continue
                server_id = _normalize_server_id(key)
                entry = servers.get(server_id, {})
                entry.setdefault("type", server.get("type") or "stdio")
                entry.setdefault("command", server.get("command"))
                entry.setdefault("args", server.get("args"))
                env = server.get("env")
                if isinstance(env, dict):
                    entry.setdefault("envKeys", sorted(set(map(str, env.keys()))))
                servers[server_id] = entry
    except Exception as e:
        # No Claude config: log and continue gracefully
        logger.debug("Failed to load Claude MCP config: %s", e)

    registry["servers"] = servers
    if write:
        _write_registry(registry)
        _append_audit({"action": "init_registry_from_existing", "registry_path": MCP_REGISTRY_PATH})

    return registry


def _apply_registry_to_antigravity(registry: Dict[str, Any], *, write: bool) -> Dict[str, Any]:
    config = _load_antigravity_config()
    mcp_servers: Dict[str, Any] = config.get("mcpServers", {})

    changes: List[str] = []
    for server_id, entry in (registry.get("servers") or {}).items():
        if not isinstance(entry, dict):
            continue
        key = _antigravity_key_for_id(server_id)
        server = mcp_servers.get(key)
        if not isinstance(server, dict):
            server = {}

        desired_command = entry.get("command")
        desired_args = entry.get("args") or []

        if desired_command:
            if server.get("command") != desired_command:
                server["command"] = desired_command
                changes.append(f"antigravity:{key}:command")
        if isinstance(desired_args, list):
            if server.get("args") != desired_args:
                server["args"] = desired_args
                changes.append(f"antigravity:{key}:args")

        if entry.get("disabled") is True:
            if server.get("disabled") is not True:
                server["disabled"] = True
                changes.append(f"antigravity:{key}:disabled")

        # Never overwrite env values here; preserve existing secrets.
        mcp_servers[key] = server

    config["mcpServers"] = mcp_servers
    if write and changes:
        _atomic_write_json(ANTIGRAVITY_MCP_CONFIG_PATH, config)
        _append_audit(
            {
                "action": "sync_antigravity_config",
                "path": ANTIGRAVITY_MCP_CONFIG_PATH,
                "changes": changes,
            }
        )

    return {"path": ANTIGRAVITY_MCP_CONFIG_PATH, "changed": bool(changes), "changes": changes}


def _apply_registry_to_claude(registry: Dict[str, Any], *, write: bool) -> Dict[str, Any]:
    if not os.path.exists(CLAUDE_CONFIG_PATH):
        return {
            "path": CLAUDE_CONFIG_PATH,
            "skipped": True,
            "reason": "Claude config not found",
            "changed": False,
            "changes": [],
        }

    config = _load_claude_config()
    project = _ensure_claude_project(config, WORKSPACE_ROOT)
    mcp_servers: Dict[str, Any] = project.get("mcpServers", {})

    changes: List[str] = []
    for server_id, entry in (registry.get("servers") or {}).items():
        if not isinstance(entry, dict):
            continue

        key = server_id
        server = mcp_servers.get(key)
        if not isinstance(server, dict):
            server = {"type": entry.get("type") or "stdio"}

        desired_command = entry.get("command")
        desired_args = entry.get("args") or []

        if desired_command and server.get("command") != desired_command:
            server["command"] = desired_command
            changes.append(f"claude:{key}:command")
        if isinstance(desired_args, list) and server.get("args") != desired_args:
            server["args"] = desired_args
            changes.append(f"claude:{key}:args")
        if server.get("type") != (entry.get("type") or server.get("type") or "stdio"):
            server["type"] = entry.get("type") or "stdio"
            changes.append(f"claude:{key}:type")

        # Do not inject env values. Preserve if already present.
        mcp_servers[key] = server

    project["mcpServers"] = mcp_servers
    if write and changes:
        _atomic_write_json(CLAUDE_CONFIG_PATH, config)
        _append_audit(
            {
                "action": "sync_claude_config",
                "path": CLAUDE_CONFIG_PATH,
                "changes": changes,
            }
        )

    return {"path": CLAUDE_CONFIG_PATH, "skipped": False, "changed": bool(changes), "changes": changes}


def sync_from_registry(*, write: bool) -> Dict[str, Any]:
    registry = _load_registry()
    result = {
        "registry_path": MCP_REGISTRY_PATH,
        "antigravity": _apply_registry_to_antigravity(registry, write=write),
        "claude": _apply_registry_to_claude(registry, write=write),
    }
    return result


def set_github_native(*, install_path: str = DEFAULT_GITHUB_MCP_INSTALL_PATH, write: bool) -> Dict[str, Any]:
    """
    Update the canonical registry to point GitHub MCP at the native binary, then sync configs.
    """
    if not os.path.exists(install_path):
        raise FileNotFoundError(f"github-mcp-server not installed at {install_path}")

    registry = _load_registry()
    servers = registry.setdefault("servers", {})
    github = servers.get("github")
    if not isinstance(github, dict):
        github = {"type": "stdio"}

    github["type"] = "stdio"
    github["command"] = install_path
    github["args"] = ["stdio"]
    github.setdefault("envKeys", ["GITHUB_PERSONAL_ACCESS_TOKEN"])
    servers["github"] = github
    registry["servers"] = servers

    if write:
        _write_registry(registry)
        _append_audit({"action": "set_github_native", "install_path": install_path, "registry_path": MCP_REGISTRY_PATH})

    sync_result = sync_from_registry(write=write)
    return {"registry_updated": True, "sync": sync_result}


def status() -> Dict[str, Any]:
    registry = _load_registry()
    reg_servers = registry.get("servers") or {}

    ag = _load_antigravity_config()
    ag_servers = ag.get("mcpServers") or {}

    cc = None
    try:
        cc = _load_claude_config()
    except Exception as e:
        logger.debug("Failed to load Claude config for status: %s", e)
        cc = None

    claude_servers: Dict[str, Any] = {}
    if isinstance(cc, dict):
        project = cc.get("projects", {}).get(WORKSPACE_ROOT, {})
        if isinstance(project, dict) and isinstance(project.get("mcpServers"), dict):
            claude_servers = project.get("mcpServers", {})

    def summarize_server(server: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "command": server.get("command"),
            "args": server.get("args"),
            "serverUrl": server.get("serverUrl"),
            "disabled": server.get("disabled"),
            "env": _redact_env_values(server.get("env") if isinstance(server.get("env"), dict) else None),
        }

    report: Dict[str, Any] = {"registry_path": MCP_REGISTRY_PATH, "workspaceRoot": WORKSPACE_ROOT, "servers": {}}
    for server_id, entry in reg_servers.items():
        if not isinstance(entry, dict):
            continue
        ag_key = _antigravity_key_for_id(server_id)
        report["servers"][server_id] = {
            "registry": {"command": entry.get("command"), "args": entry.get("args"), "envKeys": entry.get("envKeys")},
            "antigravity": summarize_server(ag_servers.get(ag_key, {}) if isinstance(ag_servers.get(ag_key), dict) else {}),
            "claude": summarize_server(claude_servers.get(server_id, {}) if isinstance(claude_servers.get(server_id), dict) else {}),
        }
    return report


def _print_json(data: Dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="ODA MCP manager (multi-agent consistent MCP tooling)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show MCP registry + per-agent config summary (env values redacted)")

    init_p = sub.add_parser("init-registry", help="Create/update canonical registry from existing configs")
    init_p.add_argument("--write", action="store_true", help="Write registry to disk")

    sync_p = sub.add_parser("sync", help="Sync configs from canonical registry")
    sync_p.add_argument("--write", action="store_true", help="Write changes to configs")

    inst_p = sub.add_parser("install-github", help="Install github-mcp-server as native binary")
    inst_p.add_argument("--tag", default="latest", help="Release tag (default: latest)")
    inst_p.add_argument("--install-path", default=DEFAULT_GITHUB_MCP_INSTALL_PATH, help="Install path for binary")

    set_p = sub.add_parser("set-github-native", help="Point registry+configs at native github-mcp-server")
    set_p.add_argument("--install-path", default=DEFAULT_GITHUB_MCP_INSTALL_PATH, help="Path to github-mcp-server binary")
    set_p.add_argument("--write", action="store_true", help="Write registry/config changes")

    args = parser.parse_args(argv)

    if args.cmd == "status":
        _print_json(status())
        return 0

    if args.cmd == "init-registry":
        reg = init_registry_from_existing(write=args.write)
        _print_json(reg)
        return 0

    if args.cmd == "sync":
        _print_json(sync_from_registry(write=args.write))
        return 0

    if args.cmd == "install-github":
        _print_json(install_github_mcp_server(install_path=args.install_path, tag=args.tag))
        return 0

    if args.cmd == "set-github-native":
        _print_json(set_github_native(install_path=args.install_path, write=args.write))
        return 0

    raise RuntimeError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
