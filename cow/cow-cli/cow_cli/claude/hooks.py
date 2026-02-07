"""
COW CLI - SDK Hooks

Pre/Post Tool Use hooks for validation, logging, and error handling.
"""
from typing import Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio
import json

logger = logging.getLogger("cow-cli.hooks")


class HookAction(str, Enum):
    """Hook action results."""

    ALLOW = "allow"
    BLOCK = "block"
    RETRY = "retry"
    FAIL = "fail"


@dataclass
class HookResult:
    """Result of a hook execution."""

    action: HookAction
    message: Optional[str] = None
    modified_params: Optional[dict] = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def allow(cls, message: Optional[str] = None, **metadata) -> "HookResult":
        """Create an allow result."""
        return cls(action=HookAction.ALLOW, message=message, metadata=metadata)

    @classmethod
    def block(cls, message: str, **metadata) -> "HookResult":
        """Create a block result."""
        return cls(action=HookAction.BLOCK, message=message, metadata=metadata)

    @classmethod
    def retry(cls, message: Optional[str] = None, **metadata) -> "HookResult":
        """Create a retry result."""
        return cls(action=HookAction.RETRY, message=message, metadata=metadata)

    @classmethod
    def fail(cls, message: str, **metadata) -> "HookResult":
        """Create a fail result."""
        return cls(action=HookAction.FAIL, message=message, metadata=metadata)


@dataclass
class ToolMetrics:
    """Metrics for tool usage."""

    tool_name: str
    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    retry_count: int = 0
    total_duration_ms: float = 0.0
    last_called: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Get success rate."""
        if self.call_count == 0:
            return 0.0
        return self.success_count / self.call_count

    @property
    def average_duration_ms(self) -> float:
        """Get average duration."""
        if self.success_count == 0:
            return 0.0
        return self.total_duration_ms / self.success_count


class QuotaManager:
    """
    Manages API quotas for external services.

    Tracks usage and enforces limits for:
    - Mathpix API calls
    - Claude API tokens
    """

    def __init__(
        self,
        mathpix_monthly_limit: int = 1000,
        mathpix_daily_limit: int = 100,
    ):
        self.mathpix_monthly_limit = mathpix_monthly_limit
        self.mathpix_daily_limit = mathpix_daily_limit

        # Usage counters
        self._mathpix_monthly_usage = 0
        self._mathpix_daily_usage = 0
        self._last_reset_date = datetime.now().date()

    def check_mathpix_quota(self) -> dict:
        """Check Mathpix quota status."""
        self._maybe_reset_daily()

        return {
            "monthly_used": self._mathpix_monthly_usage,
            "monthly_limit": self.mathpix_monthly_limit,
            "monthly_remaining": max(0, self.mathpix_monthly_limit - self._mathpix_monthly_usage),
            "daily_used": self._mathpix_daily_usage,
            "daily_limit": self.mathpix_daily_limit,
            "daily_remaining": max(0, self.mathpix_daily_limit - self._mathpix_daily_usage),
            "has_quota": self._has_mathpix_quota(),
        }

    def _has_mathpix_quota(self) -> bool:
        """Check if Mathpix quota is available."""
        self._maybe_reset_daily()
        return (
            self._mathpix_monthly_usage < self.mathpix_monthly_limit
            and self._mathpix_daily_usage < self.mathpix_daily_limit
        )

    def consume_mathpix_quota(self, count: int = 1) -> bool:
        """Consume Mathpix quota. Returns True if successful."""
        if not self._has_mathpix_quota():
            return False

        self._mathpix_monthly_usage += count
        self._mathpix_daily_usage += count
        return True

    def _maybe_reset_daily(self) -> None:
        """Reset daily counters if needed."""
        today = datetime.now().date()
        if today > self._last_reset_date:
            self._mathpix_daily_usage = 0
            self._last_reset_date = today

    def get_usage_summary(self) -> dict:
        """Get complete usage summary."""
        return {
            "mathpix": self.check_mathpix_quota(),
        }


class HookManager:
    """
    Manages tool hooks for the COW pipeline.

    Provides pre/post tool use hooks for:
    - Quota checking
    - Parameter validation
    - Result logging
    - Error handling
    - Metrics collection
    """

    # Transient errors that should trigger retry
    TRANSIENT_ERRORS = {
        "timeout",
        "rate_limit",
        "service_unavailable",
        "network_error",
        "connection_refused",
    }

    def __init__(
        self,
        quota_manager: Optional[QuotaManager] = None,
        enable_metrics: bool = True,
        on_block: Optional[Callable[[str, str], None]] = None,
        on_failure: Optional[Callable[[str, Exception], None]] = None,
    ):
        """
        Initialize hook manager.

        Args:
            quota_manager: Optional quota manager
            enable_metrics: Enable metrics collection
            on_block: Callback when tool is blocked
            on_failure: Callback when tool fails
        """
        self.quota_manager = quota_manager or QuotaManager()
        self.enable_metrics = enable_metrics
        self.on_block = on_block
        self.on_failure = on_failure

        # Metrics storage
        self._metrics: dict[str, ToolMetrics] = {}

        # Active calls (for timing)
        self._active_calls: dict[str, datetime] = {}

    async def pre_tool_use(
        self,
        tool_name: str,
        params: dict,
    ) -> HookResult:
        """
        Pre-tool-use hook.

        Called before each tool execution to:
        - Check quotas
        - Validate parameters
        - Log the call

        Args:
            tool_name: Name of the tool being called
            params: Parameters passed to the tool

        Returns:
            HookResult with action (allow/block)
        """
        logger.debug(f"PreToolUse: {tool_name}", extra={"params": params})

        # Record start time
        call_id = f"{tool_name}_{datetime.now().timestamp()}"
        self._active_calls[call_id] = datetime.now()

        # Tool-specific checks
        if tool_name in ("mathpix_request", "mcp__cow-mathpix__mathpix_request"):
            return await self._pre_mathpix(tool_name, params)

        if tool_name in ("validate_image", "mcp__cow-validation__validate_image"):
            return await self._pre_validate_image(tool_name, params)

        # Default: allow
        return HookResult.allow()

    async def post_tool_use(
        self,
        tool_name: str,
        result: Any,
        duration_ms: float = 0.0,
    ) -> HookResult:
        """
        Post-tool-use hook (success).

        Called after successful tool execution to:
        - Log results
        - Update metrics
        - Consume quotas

        Args:
            tool_name: Name of the tool
            result: Result returned by the tool
            duration_ms: Execution duration

        Returns:
            HookResult with action
        """
        logger.debug(f"PostToolUse: {tool_name} ({duration_ms:.0f}ms)")

        # Update metrics
        if self.enable_metrics:
            self._update_metrics(tool_name, success=True, duration_ms=duration_ms)

        # Tool-specific post-processing
        if tool_name in ("mathpix_request", "mcp__cow-mathpix__mathpix_request"):
            self.quota_manager.consume_mathpix_quota(1)
            logger.info(f"Mathpix call completed", extra={
                "quota": self.quota_manager.check_mathpix_quota()
            })

        return HookResult.allow()

    async def post_tool_use_failure(
        self,
        tool_name: str,
        error: Exception,
        retry_count: int = 0,
    ) -> HookResult:
        """
        Post-tool-use hook (failure).

        Called when tool execution fails to:
        - Log errors
        - Decide retry strategy
        - Alert if needed

        Args:
            tool_name: Name of the tool
            error: Exception that occurred
            retry_count: Current retry count

        Returns:
            HookResult with action (retry/fail)
        """
        logger.error(f"PostToolUseFailure: {tool_name}", extra={"error": str(error)})

        # Update metrics
        if self.enable_metrics:
            self._update_metrics(tool_name, success=False)

        # Callback if registered
        if self.on_failure:
            self.on_failure(tool_name, error)

        # Decide retry based on error type
        if self._is_transient_error(error) and retry_count < 3:
            self._update_retry_metrics(tool_name)
            return HookResult.retry(
                message=f"Transient error, retrying ({retry_count + 1}/3)",
                retry_count=retry_count + 1,
            )

        return HookResult.fail(message=str(error))

    async def _pre_mathpix(self, tool_name: str, params: dict) -> HookResult:
        """Pre-hook for Mathpix calls."""
        quota = self.quota_manager.check_mathpix_quota()

        if not quota["has_quota"]:
            msg = (
                f"Mathpix quota exceeded: "
                f"monthly={quota['monthly_used']}/{quota['monthly_limit']}, "
                f"daily={quota['daily_used']}/{quota['daily_limit']}"
            )
            logger.warning(msg)

            if self.on_block:
                self.on_block(tool_name, msg)

            return HookResult.block(msg, quota=quota)

        # Validate file path
        file_path = params.get("file_path") or params.get("image_path")
        if not file_path:
            return HookResult.block("Missing file_path parameter")

        logger.info(f"Mathpix request: {file_path}", extra={"quota_remaining": quota["daily_remaining"]})
        return HookResult.allow(quota=quota)

    async def _pre_validate_image(self, tool_name: str, params: dict) -> HookResult:
        """Pre-hook for image validation."""
        file_path = params.get("file_path")
        if not file_path:
            return HookResult.block("Missing file_path parameter")

        return HookResult.allow()

    def _is_transient_error(self, error: Exception) -> bool:
        """Check if error is transient (should retry)."""
        error_str = str(error).lower()
        return any(t in error_str for t in self.TRANSIENT_ERRORS)

    def _update_metrics(
        self,
        tool_name: str,
        success: bool,
        duration_ms: float = 0.0,
    ) -> None:
        """Update tool metrics."""
        if tool_name not in self._metrics:
            self._metrics[tool_name] = ToolMetrics(tool_name=tool_name)

        metrics = self._metrics[tool_name]
        metrics.call_count += 1
        metrics.last_called = datetime.now()

        if success:
            metrics.success_count += 1
            metrics.total_duration_ms += duration_ms
        else:
            metrics.failure_count += 1

    def _update_retry_metrics(self, tool_name: str) -> None:
        """Update retry count in metrics."""
        if tool_name in self._metrics:
            self._metrics[tool_name].retry_count += 1

    def get_metrics(self, tool_name: Optional[str] = None) -> dict:
        """Get tool metrics."""
        if tool_name:
            m = self._metrics.get(tool_name)
            if m:
                return {
                    "tool_name": m.tool_name,
                    "call_count": m.call_count,
                    "success_count": m.success_count,
                    "failure_count": m.failure_count,
                    "retry_count": m.retry_count,
                    "success_rate": m.success_rate,
                    "average_duration_ms": m.average_duration_ms,
                }
            return {}

        return {
            name: {
                "tool_name": m.tool_name,
                "call_count": m.call_count,
                "success_count": m.success_count,
                "failure_count": m.failure_count,
                "retry_count": m.retry_count,
                "success_rate": m.success_rate,
                "average_duration_ms": m.average_duration_ms,
            }
            for name, m in self._metrics.items()
        }

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()


# Global hook manager instance
_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """Get global hook manager instance."""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager


def configure_hooks(
    quota_manager: Optional[QuotaManager] = None,
    enable_metrics: bool = True,
    on_block: Optional[Callable[[str, str], None]] = None,
    on_failure: Optional[Callable[[str, Exception], None]] = None,
) -> HookManager:
    """Configure global hook manager."""
    global _hook_manager
    _hook_manager = HookManager(
        quota_manager=quota_manager,
        enable_metrics=enable_metrics,
        on_block=on_block,
        on_failure=on_failure,
    )
    return _hook_manager


# Convenience functions
async def pre_tool_use(tool_name: str, params: dict) -> HookResult:
    """Global pre-tool-use hook."""
    return await get_hook_manager().pre_tool_use(tool_name, params)


async def post_tool_use(tool_name: str, result: Any, duration_ms: float = 0.0) -> HookResult:
    """Global post-tool-use hook."""
    return await get_hook_manager().post_tool_use(tool_name, result, duration_ms)


async def post_tool_use_failure(tool_name: str, error: Exception, retry_count: int = 0) -> HookResult:
    """Global post-tool-use-failure hook."""
    return await get_hook_manager().post_tool_use_failure(tool_name, error, retry_count)


__all__ = [
    "HookAction",
    "HookResult",
    "ToolMetrics",
    "QuotaManager",
    "HookManager",
    "get_hook_manager",
    "configure_hooks",
    "pre_tool_use",
    "post_tool_use",
    "post_tool_use_failure",
]
