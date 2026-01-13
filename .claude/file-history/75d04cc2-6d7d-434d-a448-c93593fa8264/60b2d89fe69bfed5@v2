"""
Sandbox Runner: Execute Commands in Isolated Docker Container

Security: Boris Cherny Pattern 3 - Permission Bypass via Sandbox
Purpose: Run Claude Code commands with dangerously-skip-permissions equivalent
         in a secure, isolated Docker container environment.

Usage:
    from lib.oda.claude.sandbox_runner import SandboxRunner

    runner = SandboxRunner()
    result = runner.run("python scripts/analyze.py --input data/test.xlsx")

    # Or with async:
    result = await runner.run_async("python scripts/analyze.py")
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shlex
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_workspace_root() -> Path:
    """Get workspace root from centralized paths module."""
    from lib.oda.paths import get_workspace_root
    return get_workspace_root()


class SandboxProfile(Enum):
    """Security profiles for sandbox execution."""

    # Default: Maximum isolation, no network
    DEFAULT = "sandbox"

    # Networked: Limited external network access
    NETWORKED = "sandbox-networked"

    # Database: SQLite operations allowed
    DATABASE = "sandbox-db"

    # Custom: User-defined profile
    CUSTOM = "custom"


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""

    # Container settings
    profile: SandboxProfile = SandboxProfile.DEFAULT
    timeout_seconds: int = 300  # 5 minutes default
    memory_limit: str = "2G"
    cpu_limit: str = "2.0"

    # Security settings
    read_only: bool = True
    network_disabled: bool = True
    drop_capabilities: bool = True

    # Paths - use centralized path management
    workspace_root: Path = field(default_factory=lambda: _get_workspace_root())
    output_dir: Path = field(default_factory=lambda: Path(".agent/sandbox-output"))

    # Environment
    extra_env: dict[str, str] = field(default_factory=dict)

    # Docker settings
    docker_compose_file: str = "docker-compose.sandbox.yml"
    container_name_prefix: str = "oda-sandbox-exec"


@dataclass
class SandboxResult:
    """Result of sandbox command execution."""

    # Execution status
    success: bool
    exit_code: int

    # Output
    stdout: str
    stderr: str

    # Metadata
    execution_id: str
    duration_seconds: float
    container_id: Optional[str] = None

    # Evidence for ODA protocol
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_id": self.execution_id,
            "duration_seconds": self.duration_seconds,
            "container_id": self.container_id,
            "evidence": self.evidence,
        }


class SandboxRunner:
    """
    Execute commands in isolated Docker sandbox container.

    Implements Boris Cherny Pattern 3: Permission Bypass via Sandbox
    - Commands run in isolated container with dropped privileges
    - Network access disabled by default
    - Read-only filesystem with specific writable paths
    - Resource limits enforced
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        """Initialize sandbox runner with configuration."""
        self.config = config or SandboxConfig()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        output_path = self.config.workspace_root / self.config.output_dir
        output_path.mkdir(parents=True, exist_ok=True)

        # Ensure memory directory exists
        memory_path = self.config.workspace_root / ".agent" / "memory"
        memory_path.mkdir(parents=True, exist_ok=True)

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID."""
        return f"sandbox-{uuid.uuid4().hex[:12]}"

    def _build_docker_command(
        self,
        command: str,
        execution_id: str,
        profile: Optional[SandboxProfile] = None,
    ) -> list[str]:
        """Build Docker run command with security options."""
        profile = profile or self.config.profile
        container_name = f"{self.config.container_name_prefix}-{execution_id}"

        docker_cmd = [
            "docker", "run",
            "--rm",  # Remove container after execution
            "--name", container_name,

            # Security: Run as non-root user
            "--user", "1001:1001",

            # Security: Resource limits
            "--memory", self.config.memory_limit,
            "--cpus", self.config.cpu_limit,
            "--pids-limit", "100",

            # Security: Drop all capabilities
            "--cap-drop", "ALL",

            # Security: No new privileges
            "--security-opt", "no-new-privileges:true",

            # Security: Read-only root filesystem
            "--read-only",

            # Temporary filesystems for writable areas
            "--tmpfs", "/tmp:size=100M,mode=1777",
            "--tmpfs", "/app/.agent/tmp:size=50M,mode=0755,uid=1001,gid=1001",
        ]

        # Network configuration
        if self.config.network_disabled and profile == SandboxProfile.DEFAULT:
            docker_cmd.extend(["--network", "none"])
        elif profile == SandboxProfile.NETWORKED:
            docker_cmd.extend(["--network", "bridge"])

        # Volume mounts
        workspace = self.config.workspace_root
        docker_cmd.extend([
            # Scripts (read-only)
            "-v", f"{workspace}/scripts:/app/scripts:ro",
            # Data (read-only)
            "-v", f"{workspace}/data:/app/data:ro",
            # Output directory (writable)
            "-v", f"{workspace / self.config.output_dir}:/app/sandbox-output:rw",
            # Memory persistence (writable)
            "-v", f"{workspace}/.agent/memory:/app/.agent/memory:rw",
        ])

        # Database mount if needed
        if profile == SandboxProfile.DATABASE:
            db_path = workspace / ".agent" / "tmp" / "ontology.db"
            if db_path.exists():
                docker_cmd.extend([
                    "-v", f"{db_path}:/app/.agent/tmp/ontology.db:rw",
                ])

        # Environment variables
        env_vars = {
            "SANDBOX_MODE": "true",
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "ODA_WORKSPACE": "/app",
            "ODA_OUTPUT_DIR": "/app/sandbox-output",
            "EXECUTION_ID": execution_id,
            **self.config.extra_env,
        }
        for key, value in env_vars.items():
            docker_cmd.extend(["-e", f"{key}={value}"])

        # Working directory
        docker_cmd.extend(["-w", "/app"])

        # Image (use the built image from Dockerfile)
        docker_cmd.append("oda-sandbox:latest")

        # Command to execute
        docker_cmd.extend(["sh", "-c", command])

        return docker_cmd

    def run(
        self,
        command: str,
        profile: Optional[SandboxProfile] = None,
        timeout: Optional[int] = None,
        capture_evidence: bool = True,
    ) -> SandboxResult:
        """
        Execute command in sandbox container (synchronous).

        Args:
            command: Shell command to execute
            profile: Security profile to use
            timeout: Timeout in seconds (overrides config)
            capture_evidence: Whether to capture ODA evidence

        Returns:
            SandboxResult with execution details
        """
        execution_id = self._generate_execution_id()
        timeout = timeout or self.config.timeout_seconds
        start_time = time.time()

        docker_cmd = self._build_docker_command(command, execution_id, profile)

        logger.info(f"[{execution_id}] Executing in sandbox: {command[:100]}...")
        logger.debug(f"[{execution_id}] Docker command: {' '.join(docker_cmd)}")

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.config.workspace_root),
            )

            duration = time.time() - start_time

            # Build evidence for ODA protocol
            evidence = {}
            if capture_evidence:
                evidence = {
                    "sandbox_execution": True,
                    "execution_id": execution_id,
                    "profile": (profile or self.config.profile).value,
                    "command_hash": hash(command),
                    "duration_seconds": duration,
                    "exit_code": result.returncode,
                    "security_options": {
                        "read_only": self.config.read_only,
                        "network_disabled": self.config.network_disabled,
                        "capabilities_dropped": self.config.drop_capabilities,
                        "memory_limit": self.config.memory_limit,
                        "cpu_limit": self.config.cpu_limit,
                    },
                }

            return SandboxResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_id=execution_id,
                duration_seconds=duration,
                evidence=evidence,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"[{execution_id}] Command timed out after {timeout}s")
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                execution_id=execution_id,
                duration_seconds=duration,
                evidence={"sandbox_execution": True, "timeout": True},
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"[{execution_id}] Sandbox execution failed: {e}")
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_id=execution_id,
                duration_seconds=duration,
                evidence={"sandbox_execution": True, "error": str(e)},
            )

    async def run_async(
        self,
        command: str,
        profile: Optional[SandboxProfile] = None,
        timeout: Optional[int] = None,
        capture_evidence: bool = True,
    ) -> SandboxResult:
        """
        Execute command in sandbox container (asynchronous).

        Args:
            command: Shell command to execute
            profile: Security profile to use
            timeout: Timeout in seconds (overrides config)
            capture_evidence: Whether to capture ODA evidence

        Returns:
            SandboxResult with execution details
        """
        execution_id = self._generate_execution_id()
        timeout = timeout or self.config.timeout_seconds
        start_time = time.time()

        docker_cmd = self._build_docker_command(command, execution_id, profile)

        logger.info(f"[{execution_id}] Executing in sandbox (async): {command[:100]}...")

        try:
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.config.workspace_root),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                duration = time.time() - start_time
                return SandboxResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Command timed out after {timeout} seconds",
                    execution_id=execution_id,
                    duration_seconds=duration,
                    evidence={"sandbox_execution": True, "timeout": True},
                )

            duration = time.time() - start_time

            # Build evidence
            evidence = {}
            if capture_evidence:
                evidence = {
                    "sandbox_execution": True,
                    "execution_id": execution_id,
                    "profile": (profile or self.config.profile).value,
                    "async": True,
                    "duration_seconds": duration,
                    "exit_code": process.returncode,
                }

            return SandboxResult(
                success=process.returncode == 0,
                exit_code=process.returncode or 0,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                execution_id=execution_id,
                duration_seconds=duration,
                evidence=evidence,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"[{execution_id}] Async sandbox execution failed: {e}")
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_id=execution_id,
                duration_seconds=duration,
                evidence={"sandbox_execution": True, "error": str(e)},
            )

    def run_python(
        self,
        script_path: str,
        args: Optional[list[str]] = None,
        profile: Optional[SandboxProfile] = None,
    ) -> SandboxResult:
        """
        Execute Python script in sandbox.

        Args:
            script_path: Path to Python script (relative to workspace)
            args: Additional arguments to pass to script
            profile: Security profile to use

        Returns:
            SandboxResult with execution details
        """
        args = args or []
        args_str = " ".join(shlex.quote(arg) for arg in args)
        command = f"python {script_path} {args_str}".strip()
        return self.run(command, profile=profile)

    def run_shell(
        self,
        script: str,
        profile: Optional[SandboxProfile] = None,
    ) -> SandboxResult:
        """
        Execute shell script in sandbox.

        Args:
            script: Shell script content
            profile: Security profile to use

        Returns:
            SandboxResult with execution details
        """
        # Write script to temporary file in output directory
        script_name = f"sandbox_script_{uuid.uuid4().hex[:8]}.sh"
        script_path = self.config.workspace_root / self.config.output_dir / script_name

        try:
            script_path.write_text(script)
            command = f"sh /app/sandbox-output/{script_name}"
            return self.run(command, profile=profile)
        finally:
            # Clean up script file
            if script_path.exists():
                script_path.unlink()

    def build_image(self) -> bool:
        """
        Build sandbox Docker image.

        Returns:
            True if build succeeded, False otherwise
        """
        logger.info("Building sandbox Docker image...")

        try:
            result = subprocess.run(
                ["docker", "build", "-t", "oda-sandbox:latest", "."],
                capture_output=True,
                text=True,
                cwd=str(self.config.workspace_root),
                timeout=600,  # 10 minutes for build
            )

            if result.returncode != 0:
                logger.error(f"Docker build failed: {result.stderr}")
                return False

            logger.info("Sandbox Docker image built successfully")
            return True

        except Exception as e:
            logger.exception(f"Failed to build Docker image: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up any remaining sandbox containers."""
        try:
            # Find and remove any sandbox containers
            result = subprocess.run(
                ["docker", "ps", "-a", "-q", "--filter", f"name={self.config.container_name_prefix}"],
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                container_ids = result.stdout.strip().split("\n")
                subprocess.run(
                    ["docker", "rm", "-f"] + container_ids,
                    capture_output=True,
                )
                logger.info(f"Cleaned up {len(container_ids)} sandbox containers")

        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


# =============================================================================
# Convenience Functions
# =============================================================================

def run_in_sandbox(
    command: str,
    profile: SandboxProfile = SandboxProfile.DEFAULT,
    timeout: int = 300,
) -> SandboxResult:
    """
    Convenience function to run command in sandbox.

    Args:
        command: Shell command to execute
        profile: Security profile to use
        timeout: Timeout in seconds

    Returns:
        SandboxResult with execution details
    """
    runner = SandboxRunner()
    return runner.run(command, profile=profile, timeout=timeout)


async def run_in_sandbox_async(
    command: str,
    profile: SandboxProfile = SandboxProfile.DEFAULT,
    timeout: int = 300,
) -> SandboxResult:
    """
    Async convenience function to run command in sandbox.

    Args:
        command: Shell command to execute
        profile: Security profile to use
        timeout: Timeout in seconds

    Returns:
        SandboxResult with execution details
    """
    runner = SandboxRunner()
    return await runner.run_async(command, profile=profile, timeout=timeout)


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run commands in isolated Docker sandbox"
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="Command to execute in sandbox",
    )
    parser.add_argument(
        "--profile",
        choices=["default", "networked", "database"],
        default="default",
        help="Security profile to use",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build sandbox Docker image",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up sandbox containers",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    args = parser.parse_args()

    runner = SandboxRunner()

    if args.build:
        success = runner.build_image()
        exit(0 if success else 1)

    if args.cleanup:
        runner.cleanup()
        exit(0)

    if not args.command:
        parser.print_help()
        exit(1)

    profile_map = {
        "default": SandboxProfile.DEFAULT,
        "networked": SandboxProfile.NETWORKED,
        "database": SandboxProfile.DATABASE,
    }

    result = runner.run(
        args.command,
        profile=profile_map[args.profile],
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Exit Code: {result.exit_code}")
        print(f"Success: {result.success}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        if result.stdout:
            print(f"\n--- STDOUT ---\n{result.stdout}")
        if result.stderr:
            print(f"\n--- STDERR ---\n{result.stderr}")

    exit(0 if result.success else 1)
