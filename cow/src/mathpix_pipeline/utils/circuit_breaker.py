"""
Circuit Breaker Pattern Implementation for External API Resilience.

This module provides a circuit breaker pattern implementation to handle
failures in external API calls (e.g., Mathpix API) gracefully. The circuit
breaker prevents cascading failures by temporarily blocking requests to
failing services.

Usage:
    from mathpix_pipeline.utils.circuit_breaker import get_breaker, CircuitOpenError

    breaker = get_breaker("mathpix_api")

    @breaker.protect
    async def call_mathpix_api(image_data: bytes) -> dict:
        # API call implementation
        pass

    try:
        result = await call_mathpix_api(image_data)
    except CircuitOpenError:
        # Handle circuit open state (use fallback, retry later, etc.)
        pass
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """
    Represents the state of a circuit breaker.

    States:
        CLOSED: Normal operation, requests pass through.
        OPEN: Circuit is tripped, requests are blocked.
        HALF_OPEN: Testing if the service has recovered.
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """
    Exception raised when attempting to execute a request while the circuit is open.

    Attributes:
        breaker_name: The name of the circuit breaker that blocked the request.
        retry_after: Estimated seconds until the circuit may close.
    """

    def __init__(
        self, breaker_name: str, retry_after: Optional[float] = None
    ) -> None:
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        message = f"Circuit breaker '{breaker_name}' is OPEN"
        if retry_after is not None:
            message += f" (retry after {retry_after:.1f}s)"
        super().__init__(message)


@dataclass
class CircuitBreakerConfig:
    """
    Configuration for a circuit breaker instance.

    Attributes:
        failure_threshold: Number of consecutive failures before opening the circuit.
        success_threshold: Number of consecutive successes in HALF_OPEN state
            required to close the circuit.
        timeout: Duration in seconds the circuit stays OPEN before transitioning
            to HALF_OPEN.
        half_open_max_calls: Maximum concurrent calls allowed in HALF_OPEN state.
        excluded_exceptions: Exception types that should not count as failures.
    """

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    half_open_max_calls: int = 1
    excluded_exceptions: tuple[type[Exception], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if self.success_threshold < 1:
            raise ValueError("success_threshold must be at least 1")
        if self.timeout < 0:
            raise ValueError("timeout must be non-negative")
        if self.half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be at least 1")


class CircuitBreaker(Generic[T]):
    """
    A generic circuit breaker implementation for protecting external API calls.

    The circuit breaker monitors calls and transitions through states:
    - CLOSED: Normal operation, all calls pass through
    - OPEN: Calls are blocked, returns CircuitOpenError immediately
    - HALF_OPEN: Limited calls are allowed to test if service recovered

    Thread-safe implementation using asyncio locks.

    Example:
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout=30.0,
            success_threshold=2
        )
        breaker = CircuitBreaker("my_service", config)

        @breaker.protect
        async def risky_call() -> str:
            return await external_api.call()
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> None:
        """
        Initialize the circuit breaker.

        Args:
            name: Unique identifier for this circuit breaker instance.
            config: Configuration options. Uses defaults if not provided.
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # State management
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

        # Thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit breaker '{name}' initialized with config: "
            f"failure_threshold={self.config.failure_threshold}, "
            f"timeout={self.config.timeout}s"
        )

    @property
    def state(self) -> CircuitState:
        """Current state of the circuit breaker."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Current consecutive failure count."""
        return self._failure_count

    @property
    def is_closed(self) -> bool:
        """Check if circuit is in CLOSED state."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is in OPEN state."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is in HALF_OPEN state."""
        return self._state == CircuitState.HALF_OPEN

    def _should_attempt(self) -> bool:
        """
        Determine if a call should be attempted based on current state.

        Returns:
            True if the call should proceed, False otherwise.

        Side effects:
            - May transition from OPEN to HALF_OPEN if timeout has elapsed.
            - Increments half_open_calls counter in HALF_OPEN state.
        """
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self._last_failure_time is not None:
                elapsed = time.monotonic() - self._last_failure_time
                if elapsed >= self.config.timeout:
                    logger.info(
                        f"Circuit breaker '{self.name}' transitioning from OPEN to HALF_OPEN "
                        f"after {elapsed:.1f}s timeout"
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
                    # Fall through to HALF_OPEN handling
                else:
                    return False
            else:
                return False

        if self._state == CircuitState.HALF_OPEN:
            # Allow limited concurrent calls in HALF_OPEN state
            if self._half_open_calls < self.config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

        return False

    def _record_success(self) -> None:
        """
        Record a successful call.

        Side effects:
            - Resets failure count in CLOSED state.
            - May transition from HALF_OPEN to CLOSED if success threshold reached.
        """
        if self._state == CircuitState.CLOSED:
            self._failure_count = 0
            return

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            logger.debug(
                f"Circuit breaker '{self.name}' success in HALF_OPEN: "
                f"{self._success_count}/{self.config.success_threshold}"
            )

            if self._success_count >= self.config.success_threshold:
                logger.info(
                    f"Circuit breaker '{self.name}' transitioning from HALF_OPEN to CLOSED "
                    f"after {self._success_count} consecutive successes"
                )
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self._half_open_calls = 0

    def _record_failure(self, exception: Exception) -> None:
        """
        Record a failed call.

        Args:
            exception: The exception that was raised.

        Side effects:
            - Increments failure count.
            - May transition from CLOSED to OPEN if failure threshold reached.
            - Transitions from HALF_OPEN to OPEN immediately on failure.
        """
        # Check if exception should be excluded
        if isinstance(exception, self.config.excluded_exceptions):
            logger.debug(
                f"Circuit breaker '{self.name}' ignoring excluded exception: "
                f"{type(exception).__name__}"
            )
            return

        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._state == CircuitState.CLOSED:
            logger.debug(
                f"Circuit breaker '{self.name}' failure count: "
                f"{self._failure_count}/{self.config.failure_threshold}"
            )

            if self._failure_count >= self.config.failure_threshold:
                logger.warning(
                    f"Circuit breaker '{self.name}' transitioning from CLOSED to OPEN "
                    f"after {self._failure_count} consecutive failures"
                )
                self._state = CircuitState.OPEN
                self._success_count = 0

        elif self._state == CircuitState.HALF_OPEN:
            logger.warning(
                f"Circuit breaker '{self.name}' transitioning from HALF_OPEN to OPEN "
                f"due to failure during recovery test"
            )
            self._state = CircuitState.OPEN
            self._success_count = 0
            self._half_open_calls = 0

    def _get_retry_after(self) -> Optional[float]:
        """
        Calculate the estimated time until the circuit may close.

        Returns:
            Seconds until retry may be attempted, or None if not applicable.
        """
        if self._state != CircuitState.OPEN or self._last_failure_time is None:
            return None

        elapsed = time.monotonic() - self._last_failure_time
        remaining = self.config.timeout - elapsed
        return max(0.0, remaining)

    def protect(
        self, func: Callable[..., T]
    ) -> Callable[..., T]:
        """
        Decorator to protect an async function with the circuit breaker.

        Args:
            func: The async function to protect.

        Returns:
            Wrapped function that respects circuit breaker state.

        Raises:
            CircuitOpenError: If the circuit is OPEN and not allowing calls.

        Example:
            @breaker.protect
            async def call_api():
                return await client.request()
        """

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async with self._lock:
                if not self._should_attempt():
                    retry_after = self._get_retry_after()
                    raise CircuitOpenError(self.name, retry_after)

            try:
                result = await func(*args, **kwargs)
                async with self._lock:
                    self._record_success()
                return result

            except Exception as e:
                async with self._lock:
                    self._record_failure(e)
                raise

        return wrapper

    async def reset(self) -> None:
        """
        Manually reset the circuit breaker to CLOSED state.

        Use this for administrative purposes or testing.
        """
        async with self._lock:
            logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0

    def get_stats(self) -> Dict[str, object]:
        """
        Get current statistics for monitoring.

        Returns:
            Dictionary containing circuit breaker statistics.
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "retry_after": self._get_retry_after(),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
                "half_open_max_calls": self.config.half_open_max_calls,
            },
        }


# Global registry of circuit breakers
_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = asyncio.Lock()


def get_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker instance by name.

    This function provides a global registry of circuit breakers, ensuring
    that the same breaker instance is reused for a given name. This allows
    multiple parts of the application to share circuit breaker state.

    Args:
        name: Unique identifier for the circuit breaker.
        config: Configuration options. Only used when creating a new instance.
            If an instance with the given name already exists, config is ignored.

    Returns:
        The circuit breaker instance for the given name.

    Example:
        # In module A
        breaker = get_breaker("mathpix", CircuitBreakerConfig(timeout=30))

        # In module B (same breaker instance)
        breaker = get_breaker("mathpix")
    """
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name, config)
        logger.debug(f"Created new circuit breaker: '{name}'")
    return _breakers[name]


def get_all_breakers() -> Dict[str, CircuitBreaker]:
    """
    Get all registered circuit breakers.

    Returns:
        Dictionary mapping names to circuit breaker instances.
    """
    return dict(_breakers)


async def reset_all_breakers() -> None:
    """
    Reset all registered circuit breakers to CLOSED state.

    Use this for testing or administrative purposes.
    """
    for breaker in _breakers.values():
        await breaker.reset()


def clear_breakers() -> None:
    """
    Clear all registered circuit breakers.

    Use this for testing purposes only.
    """
    _breakers.clear()
    logger.debug("Cleared all circuit breakers from registry")


# Pre-configured circuit breaker configurations for common use cases
MATHPIX_API_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    success_threshold=2,
    timeout=60.0,
    half_open_max_calls=1,
)

EXTERNAL_SERVICE_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,
    success_threshold=3,
    timeout=30.0,
    half_open_max_calls=2,
)
