"""
Tests for SDK Hooks.
"""
import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch

from cow_cli.claude import (
    HookAction,
    HookResult,
    ToolMetrics,
    QuotaManager,
    HookManager,
    get_hook_manager,
    configure_hooks,
    pre_tool_use,
    post_tool_use,
    post_tool_use_failure,
)


class TestHookAction:
    """Tests for HookAction enum."""

    def test_action_values(self):
        """Test all action values."""
        assert HookAction.ALLOW.value == "allow"
        assert HookAction.BLOCK.value == "block"
        assert HookAction.RETRY.value == "retry"
        assert HookAction.FAIL.value == "fail"


class TestHookResult:
    """Tests for HookResult dataclass."""

    def test_allow_result(self):
        """Test creating allow result."""
        result = HookResult.allow(message="OK", custom="data")

        assert result.action == HookAction.ALLOW
        assert result.message == "OK"
        assert result.metadata["custom"] == "data"

    def test_block_result(self):
        """Test creating block result."""
        result = HookResult.block(message="Quota exceeded", reason="daily_limit")

        assert result.action == HookAction.BLOCK
        assert result.message == "Quota exceeded"
        assert result.metadata["reason"] == "daily_limit"

    def test_retry_result(self):
        """Test creating retry result."""
        result = HookResult.retry(message="Transient error", attempt=1)

        assert result.action == HookAction.RETRY
        assert result.message == "Transient error"
        assert result.metadata["attempt"] == 1

    def test_fail_result(self):
        """Test creating fail result."""
        result = HookResult.fail(message="Fatal error", error_code="E001")

        assert result.action == HookAction.FAIL
        assert result.message == "Fatal error"
        assert result.metadata["error_code"] == "E001"

    def test_modified_params(self):
        """Test modified_params field."""
        result = HookResult(
            action=HookAction.ALLOW,
            modified_params={"key": "value"},
        )

        assert result.modified_params == {"key": "value"}


class TestToolMetrics:
    """Tests for ToolMetrics dataclass."""

    def test_initial_metrics(self):
        """Test initial metrics values."""
        metrics = ToolMetrics(tool_name="test_tool")

        assert metrics.tool_name == "test_tool"
        assert metrics.call_count == 0
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.retry_count == 0
        assert metrics.total_duration_ms == 0.0
        assert metrics.last_called is None

    def test_success_rate_no_calls(self):
        """Test success rate with no calls."""
        metrics = ToolMetrics(tool_name="test_tool")
        assert metrics.success_rate == 0.0

    def test_success_rate_with_calls(self):
        """Test success rate calculation."""
        metrics = ToolMetrics(
            tool_name="test_tool",
            call_count=10,
            success_count=8,
            failure_count=2,
        )
        assert metrics.success_rate == 0.8

    def test_average_duration_no_success(self):
        """Test average duration with no successful calls."""
        metrics = ToolMetrics(tool_name="test_tool")
        assert metrics.average_duration_ms == 0.0

    def test_average_duration_with_calls(self):
        """Test average duration calculation."""
        metrics = ToolMetrics(
            tool_name="test_tool",
            success_count=5,
            total_duration_ms=1000.0,
        )
        assert metrics.average_duration_ms == 200.0


class TestQuotaManager:
    """Tests for QuotaManager class."""

    def test_initial_quota(self):
        """Test initial quota status."""
        manager = QuotaManager(mathpix_monthly_limit=100, mathpix_daily_limit=10)
        quota = manager.check_mathpix_quota()

        assert quota["monthly_limit"] == 100
        assert quota["daily_limit"] == 10
        assert quota["monthly_used"] == 0
        assert quota["daily_used"] == 0
        assert quota["monthly_remaining"] == 100
        assert quota["daily_remaining"] == 10
        assert quota["has_quota"] is True

    def test_consume_quota(self):
        """Test quota consumption."""
        manager = QuotaManager(mathpix_monthly_limit=100, mathpix_daily_limit=10)

        assert manager.consume_mathpix_quota(1) is True

        quota = manager.check_mathpix_quota()
        assert quota["monthly_used"] == 1
        assert quota["daily_used"] == 1

    def test_consume_multiple(self):
        """Test consuming multiple quota units."""
        manager = QuotaManager(mathpix_monthly_limit=100, mathpix_daily_limit=10)

        manager.consume_mathpix_quota(5)

        quota = manager.check_mathpix_quota()
        assert quota["monthly_used"] == 5
        assert quota["daily_used"] == 5

    def test_quota_exceeded_daily(self):
        """Test daily quota exceeded."""
        manager = QuotaManager(mathpix_monthly_limit=100, mathpix_daily_limit=5)

        for _ in range(5):
            manager.consume_mathpix_quota(1)

        quota = manager.check_mathpix_quota()
        assert quota["has_quota"] is False
        assert manager.consume_mathpix_quota(1) is False

    def test_quota_exceeded_monthly(self):
        """Test monthly quota exceeded."""
        manager = QuotaManager(mathpix_monthly_limit=3, mathpix_daily_limit=10)

        for _ in range(3):
            manager.consume_mathpix_quota(1)

        quota = manager.check_mathpix_quota()
        assert quota["has_quota"] is False

    def test_daily_reset(self):
        """Test daily quota reset."""
        manager = QuotaManager(mathpix_monthly_limit=100, mathpix_daily_limit=5)
        manager.consume_mathpix_quota(5)

        # Simulate next day
        manager._last_reset_date = date(2020, 1, 1)
        manager._maybe_reset_daily()

        quota = manager.check_mathpix_quota()
        assert quota["daily_used"] == 0
        assert quota["monthly_used"] == 5  # Monthly not reset

    def test_usage_summary(self):
        """Test usage summary."""
        manager = QuotaManager()
        summary = manager.get_usage_summary()

        assert "mathpix" in summary
        assert "has_quota" in summary["mathpix"]


class TestHookManager:
    """Tests for HookManager class."""

    @pytest.fixture
    def manager(self):
        """Create test hook manager."""
        return HookManager(enable_metrics=True)

    @pytest.mark.asyncio
    async def test_pre_tool_use_default_allow(self, manager):
        """Test default allow for unknown tools."""
        result = await manager.pre_tool_use("unknown_tool", {})
        assert result.action == HookAction.ALLOW

    @pytest.mark.asyncio
    async def test_pre_mathpix_with_quota(self, manager):
        """Test pre-mathpix hook with available quota."""
        result = await manager.pre_tool_use(
            "mathpix_request",
            {"file_path": "/test/image.png"},
        )
        assert result.action == HookAction.ALLOW

    @pytest.mark.asyncio
    async def test_pre_mathpix_no_quota(self):
        """Test pre-mathpix hook with no quota."""
        quota_manager = QuotaManager(mathpix_daily_limit=0)
        manager = HookManager(quota_manager=quota_manager)

        result = await manager.pre_tool_use(
            "mathpix_request",
            {"file_path": "/test/image.png"},
        )
        assert result.action == HookAction.BLOCK

    @pytest.mark.asyncio
    async def test_pre_mathpix_missing_path(self, manager):
        """Test pre-mathpix hook without file path."""
        result = await manager.pre_tool_use("mathpix_request", {})
        assert result.action == HookAction.BLOCK
        assert "Missing file_path" in result.message

    @pytest.mark.asyncio
    async def test_pre_validate_image_missing_path(self, manager):
        """Test pre-validate-image hook without path."""
        result = await manager.pre_tool_use("validate_image", {})
        assert result.action == HookAction.BLOCK

    @pytest.mark.asyncio
    async def test_pre_validate_image_with_path(self, manager):
        """Test pre-validate-image hook with path."""
        result = await manager.pre_tool_use(
            "validate_image",
            {"file_path": "/test/image.png"},
        )
        assert result.action == HookAction.ALLOW

    @pytest.mark.asyncio
    async def test_post_tool_use_metrics(self, manager):
        """Test metrics update on post-tool-use."""
        await manager.post_tool_use("test_tool", {"result": "ok"}, 100.0)

        metrics = manager.get_metrics("test_tool")
        assert metrics["call_count"] == 1
        assert metrics["success_count"] == 1
        assert metrics["average_duration_ms"] == 100.0

    @pytest.mark.asyncio
    async def test_post_tool_use_mathpix_quota(self, manager):
        """Test quota consumption on mathpix post-tool-use."""
        await manager.post_tool_use("mathpix_request", {"result": "ok"})

        quota = manager.quota_manager.check_mathpix_quota()
        assert quota["daily_used"] == 1

    @pytest.mark.asyncio
    async def test_post_tool_use_failure_retry(self, manager):
        """Test retry on transient error."""
        error = Exception("timeout error occurred")
        result = await manager.post_tool_use_failure("test_tool", error, retry_count=0)

        assert result.action == HookAction.RETRY
        assert "1/3" in result.message

    @pytest.mark.asyncio
    async def test_post_tool_use_failure_max_retries(self, manager):
        """Test fail after max retries."""
        error = Exception("timeout error")
        result = await manager.post_tool_use_failure("test_tool", error, retry_count=3)

        assert result.action == HookAction.FAIL

    @pytest.mark.asyncio
    async def test_post_tool_use_failure_non_transient(self, manager):
        """Test fail on non-transient error."""
        error = Exception("permanent error")
        result = await manager.post_tool_use_failure("test_tool", error, retry_count=0)

        assert result.action == HookAction.FAIL

    @pytest.mark.asyncio
    async def test_failure_callback(self):
        """Test failure callback execution."""
        callback = MagicMock()
        manager = HookManager(on_failure=callback)

        error = Exception("test error")
        await manager.post_tool_use_failure("test_tool", error)

        callback.assert_called_once_with("test_tool", error)

    @pytest.mark.asyncio
    async def test_block_callback(self):
        """Test block callback execution."""
        callback = MagicMock()
        quota_manager = QuotaManager(mathpix_daily_limit=0)
        manager = HookManager(quota_manager=quota_manager, on_block=callback)

        await manager.pre_tool_use("mathpix_request", {"file_path": "/test.png"})

        callback.assert_called_once()

    def test_get_all_metrics(self, manager):
        """Test getting all metrics."""
        manager._metrics["tool1"] = ToolMetrics(
            tool_name="tool1",
            call_count=5,
            success_count=4,
            failure_count=1,
        )
        manager._metrics["tool2"] = ToolMetrics(
            tool_name="tool2",
            call_count=3,
            success_count=3,
        )

        all_metrics = manager.get_metrics()

        assert "tool1" in all_metrics
        assert "tool2" in all_metrics
        assert all_metrics["tool1"]["call_count"] == 5
        assert all_metrics["tool2"]["success_count"] == 3

    def test_reset_metrics(self, manager):
        """Test metrics reset."""
        manager._metrics["test"] = ToolMetrics(tool_name="test", call_count=10)
        manager.reset_metrics()

        assert len(manager._metrics) == 0

    def test_transient_error_detection(self, manager):
        """Test transient error detection."""
        transient_errors = [
            Exception("Connection timeout"),
            Exception("rate_limit exceeded"),
            Exception("service_unavailable"),
            Exception("network_error occurred"),
            Exception("connection_refused by server"),
        ]

        for error in transient_errors:
            assert manager._is_transient_error(error) is True

        # Non-transient
        assert manager._is_transient_error(Exception("permanent error")) is False

    @pytest.mark.asyncio
    async def test_mcp_prefixed_tool_names(self, manager):
        """Test MCP-prefixed tool names work."""
        # MCP-prefixed mathpix
        result = await manager.pre_tool_use(
            "mcp__cow-mathpix__mathpix_request",
            {"file_path": "/test.png"},
        )
        assert result.action == HookAction.ALLOW

        # MCP-prefixed validation
        result = await manager.pre_tool_use(
            "mcp__cow-validation__validate_image",
            {"file_path": "/test.png"},
        )
        assert result.action == HookAction.ALLOW


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_get_hook_manager_singleton(self):
        """Test get_hook_manager returns singleton."""
        manager1 = get_hook_manager()
        manager2 = get_hook_manager()

        assert manager1 is manager2

    def test_configure_hooks(self):
        """Test configure_hooks creates new manager."""
        quota = QuotaManager(mathpix_daily_limit=50)
        manager = configure_hooks(
            quota_manager=quota,
            enable_metrics=False,
        )

        assert manager.quota_manager is quota
        assert manager.enable_metrics is False

    @pytest.mark.asyncio
    async def test_pre_tool_use_convenience(self):
        """Test pre_tool_use convenience function."""
        configure_hooks()  # Reset to default
        result = await pre_tool_use("test_tool", {})

        assert result.action == HookAction.ALLOW

    @pytest.mark.asyncio
    async def test_post_tool_use_convenience(self):
        """Test post_tool_use convenience function."""
        configure_hooks()
        result = await post_tool_use("test_tool", {"ok": True}, 50.0)

        assert result.action == HookAction.ALLOW

    @pytest.mark.asyncio
    async def test_post_tool_use_failure_convenience(self):
        """Test post_tool_use_failure convenience function."""
        configure_hooks()
        error = Exception("test error")
        result = await post_tool_use_failure("test_tool", error)

        assert result.action == HookAction.FAIL


class TestMetricsDisabled:
    """Tests with metrics disabled."""

    @pytest.mark.asyncio
    async def test_no_metrics_collected(self):
        """Test no metrics collected when disabled."""
        manager = HookManager(enable_metrics=False)

        await manager.post_tool_use("test_tool", {}, 100.0)

        assert len(manager._metrics) == 0

    @pytest.mark.asyncio
    async def test_failure_no_metrics(self):
        """Test failure without metrics."""
        manager = HookManager(enable_metrics=False)

        await manager.post_tool_use_failure("test_tool", Exception("error"))

        assert len(manager._metrics) == 0
