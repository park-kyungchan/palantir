"""
Orion ODA v3.0 - Stage C Quality Actions
=========================================

ActionTypes for Stage C quality verification in the 3-Stage Protocol.
Provides actions for running tests, lint, build, and typecheck.

Actions:
    - stage_c.run_tests: Execute test suite with optional coverage
    - stage_c.run_lint: Run linting with optional auto-fix
    - stage_c.run_build: Execute build command
    - stage_c.run_typecheck: Run type checking
    - stage_c.verify: Orchestrate all quality checks

Reference: .claude/references/3-stage-protocol.md
"""

from __future__ import annotations

import asyncio
import logging
import shlex
import time
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Type

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    CustomValidator,
    EditOperation,
    EditType,
    RequiredField,
    register_action,
)
from lib.oda.ontology.evidence.quality_checks import (
    CheckStatus,
    Finding,
    FindingSeverity,
    QualityCheck,
    StageCEvidence,
)
from lib.oda.ontology.ontology_types import OntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# SUBPROCESS EXECUTION UTILITIES
# =============================================================================

class SubprocessResult:
    """Result of async subprocess execution."""

    def __init__(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        duration_ms: int,
        command: str,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.duration_ms = duration_ms
        self.command = command

    @property
    def output(self) -> str:
        """Combined stdout and stderr, truncated if large."""
        combined = f"{self.stdout}\n{self.stderr}".strip()
        max_length = 10000  # Truncate large outputs
        if len(combined) > max_length:
            return combined[:max_length] + "\n... [truncated]"
        return combined

    @property
    def success(self) -> bool:
        return self.exit_code == 0


async def run_subprocess(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 300,
    env: Optional[Dict[str, str]] = None,
) -> SubprocessResult:
    """
    Execute a shell command asynchronously.

    Args:
        command: Shell command to execute
        cwd: Working directory (defaults to current)
        timeout: Timeout in seconds (default 5 minutes)
        env: Additional environment variables

    Returns:
        SubprocessResult with stdout, stderr, exit_code, duration
    """
    import os

    start_time = time.monotonic()

    # Merge environment
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=run_env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return SubprocessResult(
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                exit_code=-1,
                duration_ms=duration_ms,
                command=command,
            )

        duration_ms = int((time.monotonic() - start_time) * 1000)

        return SubprocessResult(
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            exit_code=process.returncode or 0,
            duration_ms=duration_ms,
            command=command,
        )

    except Exception as e:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        return SubprocessResult(
            stdout="",
            stderr=str(e),
            exit_code=-1,
            duration_ms=duration_ms,
            command=command,
        )


# =============================================================================
# QUALITY CHECK ACTIONS
# =============================================================================

@register_action
class RunTestsAction(ActionType[QualityCheck]):
    """
    Execute test suite and return QualityCheck result.

    Runs pytest (or specified test command) and captures results.
    Supports coverage reporting when enabled.

    Parameters:
        test_path: Path to test directory or file (default: "tests")
        test_pattern: Pattern for test discovery (default: "test_*.py")
        coverage: Enable coverage reporting (default: False)
        extra_args: Additional arguments to pass to test runner

    Returns:
        QualityCheck object with test results
    """

    api_name: ClassVar[str] = "stage_c.run_tests"
    object_type: ClassVar[Type[OntologyObject]] = QualityCheck  # type: ignore
    requires_proposal: ClassVar[bool] = False
    submission_criteria = []  # All parameters optional

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """Execute pytest and return QualityCheck with test results."""
        test_path = params.get("test_path", "tests")
        test_pattern = params.get("test_pattern", "test_*.py")
        coverage = params.get("coverage", False)
        extra_args = params.get("extra_args", "")
        cwd = params.get("cwd")

        # Build pytest command
        cmd_parts = ["pytest", test_path]

        if test_pattern != "test_*.py":
            cmd_parts.extend(["-k", test_pattern])

        if coverage:
            cmd_parts.extend(["--cov", "--cov-report=term-missing"])

        cmd_parts.append("-v")  # Verbose output

        if extra_args:
            cmd_parts.append(extra_args)

        command = " ".join(cmd_parts)

        logger.info(f"Running tests: {command}")
        result = await run_subprocess(command, cwd=cwd)

        # Determine status
        if result.exit_code == -1:
            status = CheckStatus.TIMEOUT
        elif result.exit_code == 0:
            status = CheckStatus.PASSED
        else:
            status = CheckStatus.FAILED

        # Extract coverage if available
        coverage_pct = None
        if coverage and "TOTAL" in result.stdout:
            # Parse coverage from output
            for line in result.stdout.split("\n"):
                if "TOTAL" in line:
                    parts = line.split()
                    for part in parts:
                        if part.endswith("%"):
                            coverage_pct = part
                            break

        quality_check = QualityCheck(
            name="tests",
            status=status,
            command=command,
            output=result.output,
            coverage=coverage_pct,
            duration_ms=result.duration_ms,
            exit_code=result.exit_code,
            timestamp=datetime.now(),
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=quality_check,
            message=f"Tests {status.value}: exit_code={result.exit_code}",
        )


@register_action
class RunLintAction(ActionType[QualityCheck]):
    """
    Run linting and return QualityCheck result.

    Uses ruff by default, supports auto-fix mode.

    Parameters:
        path: Path to lint (default: ".")
        fix_mode: Enable auto-fix (default: False)
        extra_args: Additional arguments to pass to linter

    Returns:
        QualityCheck object with lint results
    """

    api_name: ClassVar[str] = "stage_c.run_lint"
    object_type: ClassVar[Type[OntologyObject]] = QualityCheck  # type: ignore
    requires_proposal: ClassVar[bool] = False
    submission_criteria = []

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """Execute ruff linter and return QualityCheck with lint results."""
        path = params.get("path", ".")
        fix_mode = params.get("fix_mode", False)
        extra_args = params.get("extra_args", "")
        cwd = params.get("cwd")

        # Build ruff command
        cmd_parts = ["ruff", "check", path]

        if fix_mode:
            cmd_parts.append("--fix")

        cmd_parts.append("--output-format=text")

        if extra_args:
            cmd_parts.append(extra_args)

        command = " ".join(cmd_parts)

        logger.info(f"Running lint: {command}")
        result = await run_subprocess(command, cwd=cwd)

        # Determine status
        if result.exit_code == -1:
            status = CheckStatus.TIMEOUT
        elif result.exit_code == 0:
            status = CheckStatus.PASSED
        else:
            status = CheckStatus.FAILED

        quality_check = QualityCheck(
            name="lint",
            status=status,
            command=command,
            output=result.output,
            duration_ms=result.duration_ms,
            exit_code=result.exit_code,
            timestamp=datetime.now(),
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=quality_check,
            message=f"Lint {status.value}: exit_code={result.exit_code}",
        )


@register_action
class RunBuildAction(ActionType[QualityCheck]):
    """
    Execute build command and return QualityCheck result.

    Parameters:
        build_command: Build command to execute (required)
        cwd: Working directory for build

    Returns:
        QualityCheck object with build results
    """

    api_name: ClassVar[str] = "stage_c.run_build"
    object_type: ClassVar[Type[OntologyObject]] = QualityCheck  # type: ignore
    requires_proposal: ClassVar[bool] = False
    submission_criteria = [
        RequiredField("build_command"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """Execute build command and return QualityCheck with build results."""
        build_command = params["build_command"]
        cwd = params.get("cwd")

        logger.info(f"Running build: {build_command}")
        result = await run_subprocess(build_command, cwd=cwd)

        # Determine status
        if result.exit_code == -1:
            status = CheckStatus.TIMEOUT
        elif result.exit_code == 0:
            status = CheckStatus.PASSED
        else:
            status = CheckStatus.FAILED

        quality_check = QualityCheck(
            name="build",
            status=status,
            command=build_command,
            output=result.output,
            duration_ms=result.duration_ms,
            exit_code=result.exit_code,
            timestamp=datetime.now(),
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=quality_check,
            message=f"Build {status.value}: exit_code={result.exit_code}",
        )


@register_action
class RunTypecheckAction(ActionType[QualityCheck]):
    """
    Run type checking and return QualityCheck result.

    Uses mypy by default for Python type checking.

    Parameters:
        path: Path to typecheck (default: ".")
        extra_args: Additional arguments to pass to type checker

    Returns:
        QualityCheck object with typecheck results
    """

    api_name: ClassVar[str] = "stage_c.run_typecheck"
    object_type: ClassVar[Type[OntologyObject]] = QualityCheck  # type: ignore
    requires_proposal: ClassVar[bool] = False
    submission_criteria = []

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """Execute mypy type checker and return QualityCheck with typecheck results."""
        path = params.get("path", ".")
        extra_args = params.get("extra_args", "")
        cwd = params.get("cwd")

        # Build mypy command
        cmd_parts = ["mypy", path, "--no-error-summary"]

        if extra_args:
            cmd_parts.append(extra_args)

        command = " ".join(cmd_parts)

        logger.info(f"Running typecheck: {command}")
        result = await run_subprocess(command, cwd=cwd)

        # Determine status
        if result.exit_code == -1:
            status = CheckStatus.TIMEOUT
        elif result.exit_code == 0:
            status = CheckStatus.PASSED
        else:
            status = CheckStatus.FAILED

        quality_check = QualityCheck(
            name="typecheck",
            status=status,
            command=command,
            output=result.output,
            duration_ms=result.duration_ms,
            exit_code=result.exit_code,
            timestamp=datetime.now(),
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=quality_check,
            message=f"Typecheck {status.value}: exit_code={result.exit_code}",
        )


# =============================================================================
# STAGE C ORCHESTRATOR
# =============================================================================

@register_action
class StageCVerifyAction(ActionType[StageCEvidence]):
    """
    Orchestrate all Stage C quality checks and aggregate results.

    This is the main entry point for Stage C verification in the 3-Stage Protocol.
    Runs selected quality checks in parallel and aggregates results into
    StageCEvidence for the verification gate.

    Parameters:
        path: Root path for quality checks (default: ".")
        checks_to_run: List of checks to run (default: ["build", "tests", "lint"])
                       Valid values: "build", "tests", "lint", "typecheck"
        build_command: Build command (default: "python -m py_compile")
        test_path: Test directory (default: "tests")
        coverage: Enable test coverage (default: False)
        fix_mode: Enable lint auto-fix (default: False)

    Returns:
        StageCEvidence with all quality check results
    """

    api_name: ClassVar[str] = "stage_c.verify"
    object_type: ClassVar[Type[OntologyObject]] = StageCEvidence  # type: ignore
    requires_proposal: ClassVar[bool] = False

    # Valid check names for validation
    VALID_CHECKS = {"build", "tests", "lint", "typecheck"}

    submission_criteria = [
        CustomValidator(
            name="ValidChecks",
            validator_fn=lambda params, ctx: all(
                c in StageCVerifyAction.VALID_CHECKS
                for c in params.get("checks_to_run", [])
            ),
            error_message="checks_to_run must only contain: build, tests, lint, typecheck"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """Run all quality checks in parallel and aggregate into StageCEvidence."""
        path = params.get("path", ".")
        checks_to_run = params.get("checks_to_run", ["build", "tests", "lint"])
        build_command = params.get("build_command", f"python -m py_compile {path}")
        test_path = params.get("test_path", "tests")
        coverage = params.get("coverage", False)
        fix_mode = params.get("fix_mode", False)
        cwd = params.get("cwd")

        # Initialize evidence
        evidence = StageCEvidence(
            stage_started_at=datetime.now(),
            execution_context={
                "path": path,
                "checks_requested": checks_to_run,
                "actor_id": context.actor_id,
            }
        )

        # Prepare check tasks
        check_tasks = []
        check_names = []

        for check in checks_to_run:
            if check == "build":
                action = RunBuildAction()
                task = action.execute(
                    {"build_command": build_command, "cwd": cwd},
                    context
                )
                check_tasks.append(task)
                check_names.append("build")

            elif check == "tests":
                action = RunTestsAction()
                task = action.execute(
                    {"test_path": test_path, "coverage": coverage, "cwd": cwd},
                    context
                )
                check_tasks.append(task)
                check_names.append("tests")

            elif check == "lint":
                action = RunLintAction()
                task = action.execute(
                    {"path": path, "fix_mode": fix_mode, "cwd": cwd},
                    context
                )
                check_tasks.append(task)
                check_names.append("lint")

            elif check == "typecheck":
                action = RunTypecheckAction()
                task = action.execute(
                    {"path": path, "cwd": cwd},
                    context
                )
                check_tasks.append(task)
                check_names.append("typecheck")

        # Run all checks in parallel
        if check_tasks:
            results = await asyncio.gather(*check_tasks, return_exceptions=True)

            for name, result in zip(check_names, results):
                if isinstance(result, Exception):
                    # Handle exception as failed check
                    failed_check = QualityCheck(
                        name=name,
                        status=CheckStatus.FAILED,
                        command=f"[{name}]",
                        output=str(result),
                        exit_code=-1,
                        timestamp=datetime.now(),
                    )
                    evidence.add_quality_check(failed_check)
                    logger.error(f"Check '{name}' failed with exception: {result}")
                elif isinstance(result, ActionResult) and result.success:
                    # Add successful check
                    quality_check = result.data
                    if isinstance(quality_check, QualityCheck):
                        evidence.add_quality_check(quality_check)

                        # Extract findings from failed checks
                        if quality_check.status == CheckStatus.FAILED:
                            self._extract_findings(evidence, quality_check)
                else:
                    # Handle action failure
                    logger.warning(f"Check '{name}' returned unsuccessful result")

        evidence.stage_completed_at = datetime.now()

        # Determine overall status
        can_pass = evidence.can_pass_stage()
        summary = evidence.to_summary()

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=evidence,
            message=f"Stage C: {summary['status']} - {summary['checks_passed']}/{summary['checks_executed']} checks passed",
        )

    def _extract_findings(self, evidence: StageCEvidence, check: QualityCheck) -> None:
        """Extract findings from check output."""
        if not check.output:
            return

        # Parse ruff/lint output for findings
        if check.name == "lint":
            for line in check.output.split("\n"):
                # Ruff format: path/file.py:line:col: CODE message
                if ":" in line and any(c.isupper() for c in line):
                    parts = line.split(":", 3)
                    if len(parts) >= 4:
                        try:
                            file_path = parts[0].strip()
                            line_num = int(parts[1]) if parts[1].isdigit() else 1
                            col_num = int(parts[2]) if parts[2].isdigit() else None
                            message = parts[3].strip()

                            # Extract error code
                            code = None
                            if " " in message:
                                potential_code = message.split()[0]
                                if potential_code[0].isalpha() and any(c.isdigit() for c in potential_code):
                                    code = potential_code

                            finding = Finding(
                                severity=FindingSeverity.WARNING,
                                category="lint",
                                message=message,
                                file=file_path,
                                line=line_num,
                                column=col_num,
                                code=code,
                                auto_fixable=True,
                            )
                            evidence.add_finding(finding)
                        except (ValueError, IndexError):
                            continue

        # Parse pytest output for test failures
        elif check.name == "tests":
            if "FAILED" in check.output:
                for line in check.output.split("\n"):
                    if "FAILED" in line:
                        finding = Finding(
                            severity=FindingSeverity.ERROR,
                            category="test",
                            message=line.strip(),
                            file="tests",
                            line=1,
                        )
                        evidence.add_finding(finding)

        # Parse mypy output for type errors
        elif check.name == "typecheck":
            for line in check.output.split("\n"):
                if ": error:" in line:
                    parts = line.split(":", 3)
                    if len(parts) >= 4:
                        try:
                            file_path = parts[0].strip()
                            line_num = int(parts[1]) if parts[1].isdigit() else 1
                            message = parts[3].strip() if len(parts) > 3 else parts[2].strip()

                            finding = Finding(
                                severity=FindingSeverity.ERROR,
                                category="type",
                                message=message,
                                file=file_path,
                                line=line_num,
                            )
                            evidence.add_finding(finding)
                        except (ValueError, IndexError):
                            continue


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RunTestsAction",
    "RunLintAction",
    "RunBuildAction",
    "RunTypecheckAction",
    "StageCVerifyAction",
    "run_subprocess",
    "SubprocessResult",
]
