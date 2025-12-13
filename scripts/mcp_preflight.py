#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import argparse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ANTIGRAVITY_MCP_CONFIG_PATH = "/home/palantir/.gemini/antigravity/mcp_config.json"


@dataclass(frozen=True)
class McpServerCheckResult:
    name: str
    status: str  # ok | disabled | error | skipped
    reason: Optional[str] = None


def _which(command: str) -> Optional[str]:
    if os.path.isabs(command):
        return command if os.path.exists(command) else None
    return shutil.which(command)


def _is_npx_command(command: str) -> bool:
    return os.path.basename(command) == "npx"


def _check_docker_access(timeout_s: int = 5) -> Tuple[bool, str]:
    docker_path = _which("docker")
    if not docker_path:
        return False, "docker not found in PATH"

    try:
        result = subprocess.run(
            [docker_path, "info"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except Exception as exc:
        return False, f"docker info failed: {exc}"

    if result.returncode == 0:
        return True, "docker daemon reachable"

    msg = (result.stderr or result.stdout or "").strip()
    msg_lower = msg.lower()
    if "permission denied" in msg_lower and "docker.sock" in msg_lower:
        return (
            False,
            "permission denied to docker socket (try adding user to 'docker' group or running with proper privileges)",
        )
    if "cannot connect to the docker daemon" in msg_lower:
        return False, "docker daemon not reachable (is the service running?)"
    return False, msg or "docker info returned non-zero exit code"


def _looks_like_abs_path(value: str) -> bool:
    return value.startswith("/")


def _check_command_and_args(command: str, args: List[str]) -> Tuple[bool, str]:
    resolved = _which(command)
    if not resolved:
        return False, f"command not found: {command}"

    if os.path.isabs(resolved) and not os.access(resolved, os.X_OK):
        return False, f"command not executable: {resolved}"

    missing_paths: List[str] = []
    for arg in args:
        if not isinstance(arg, str):
            continue
        if _looks_like_abs_path(arg) and not os.path.exists(arg):
            missing_paths.append(arg)

    if missing_paths:
        return False, f"missing arg paths: {', '.join(missing_paths[:5])}"

    return True, "command and arg paths look valid"


def _probe_stdio_startup(
    command: str,
    args: List[str],
    *,
    env: Optional[Dict[str, str]] = None,
    timeout_s: float = 1.5,
) -> Tuple[bool, str]:
    """
    Best-effort startup probe:
    - If the process exits quickly -> error (likely to trigger IDE retry loops)
    - If the process is still running after timeout -> ok

    stdout/stderr are discarded to avoid blocking and to avoid accidentally printing secrets.
    """
    resolved = _which(command)
    if not resolved:
        return False, f"command not found: {command}"

    merged_env = os.environ.copy()
    if env:
        merged_env.update({str(k): str(v) for k, v in env.items()})

    try:
        proc = subprocess.Popen(
            [resolved, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=merged_env,
            start_new_session=True,
        )
    except Exception as exc:
        return False, f"failed to start process: {exc}"

    try:
        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return True, "startup probe: process is running"

        code = proc.returncode
        return False, f"startup probe: exited early (code={code})"
    finally:
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=1.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


def _npx_probe_args(args: List[str]) -> List[str]:
    """
    Prevent npx from attempting network installs during preflight.
    If the package isn't already available, the probe should fail quickly so we can disable it.
    """
    if any(a == "--no-install" for a in args):
        return args
    return ["--no-install", *args]


def _check_server(
    name: str,
    server: Dict[str, Any],
    *,
    probe_startup: bool,
    probe_timeout_s: float,
) -> McpServerCheckResult:
    if server.get("disabled") is True:
        return McpServerCheckResult(name=name, status="disabled", reason="explicitly disabled")

    if server.get("serverUrl"):
        return McpServerCheckResult(name=name, status="skipped", reason="remote serverUrl (not checked)")

    command = server.get("command")
    args = server.get("args") or []
    env = server.get("env") if isinstance(server.get("env"), dict) else None

    if not isinstance(command, str) or not command:
        return McpServerCheckResult(name=name, status="error", reason="missing command")
    if not isinstance(args, list) or any(not isinstance(a, str) for a in args):
        return McpServerCheckResult(name=name, status="error", reason="args must be string[]")

    if os.path.basename(command) == "docker":
        ok, msg = _check_docker_access()
        return McpServerCheckResult(name=name, status="ok" if ok else "error", reason=msg)

    ok, msg = _check_command_and_args(command, args)
    if not ok:
        return McpServerCheckResult(name=name, status="error", reason=msg)

    if not probe_startup:
        return McpServerCheckResult(name=name, status="ok", reason=msg)

    probe_args = _npx_probe_args(args) if _is_npx_command(command) else args
    ok2, msg2 = _probe_stdio_startup(command, probe_args, env=env, timeout_s=probe_timeout_s)
    return McpServerCheckResult(name=name, status="ok" if ok2 else "error", reason=msg2)


def preflight_mcp_config(
    config_path: str = DEFAULT_ANTIGRAVITY_MCP_CONFIG_PATH,
    *,
    auto_disable_failed: bool = False,
    write: bool = False,
    probe_startup: bool = True,
    probe_timeout_s: float = 1.5,
) -> Dict[str, Any]:
    """
    Preflight-check an Antigravity MCP config and optionally disable failing servers.

    This is designed as a mitigation for IDE-side retry loops when a configured MCP server
    cannot be started (e.g., docker not reachable).
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    servers: Dict[str, Any] = config.get("mcpServers") or {}
    if not isinstance(servers, dict):
        raise ValueError("Invalid MCP config: 'mcpServers' must be an object")

    results: List[McpServerCheckResult] = []
    changed = False

    for name, server in servers.items():
        if not isinstance(server, dict):
            results.append(McpServerCheckResult(name=name, status="error", reason="server definition must be an object"))
            if auto_disable_failed and servers.get(name, {}).get("disabled") is not True:
                servers[name] = {"disabled": True}
                changed = True
            continue

        result = _check_server(name, server, probe_startup=probe_startup, probe_timeout_s=probe_timeout_s)
        results.append(result)

        if auto_disable_failed and result.status == "error":
            if server.get("disabled") is not True:
                server["disabled"] = True
                changed = True

    if write and changed:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return {
        "config_path": config_path,
        "changed": changed,
        "servers": [
            {"name": r.name, "status": r.status, "reason": r.reason}
            for r in sorted(results, key=lambda r: r.name)
        ],
    }


def _format_human(result: Dict[str, Any]) -> str:
    lines = [f"Config: {result.get('config_path')}"]
    for server in result.get("servers", []):
        name = server.get("name")
        status = server.get("status")
        reason = server.get("reason") or ""
        lines.append(f"- {name}: {status} {('- ' + reason) if reason else ''}".rstrip())
    if result.get("changed"):
        lines.append("Config would change (or was changed) due to auto-disable.")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Preflight Antigravity MCP config and optionally disable failing servers.")
    parser.add_argument("--config", default=DEFAULT_ANTIGRAVITY_MCP_CONFIG_PATH, help="Path to Antigravity mcp_config.json")
    parser.add_argument("--auto-disable-failed", action="store_true", help="Mark failing servers as disabled")
    parser.add_argument("--write", action="store_true", help="Write changes back to the config file")
    parser.add_argument("--no-probe-startup", action="store_false", dest="probe_startup", help="Skip starting processes during preflight")
    parser.add_argument("--probe-timeout-s", type=float, default=1.5, help="Startup probe timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.set_defaults(probe_startup=True)
    args = parser.parse_args(argv)

    result = preflight_mcp_config(
        args.config,
        auto_disable_failed=args.auto_disable_failed,
        write=args.write,
        probe_startup=args.probe_startup,
        probe_timeout_s=args.probe_timeout_s,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_human(result))

    has_errors = any(s.get("status") == "error" for s in result.get("servers", []))
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
