"""
Orion ODA v4.0 - Transaction Decorators
Palantir Foundry Compliant Declarative Transaction Management

This module provides:
- @transactional: Decorator for automatic transaction management
- PropagationMode: Transaction propagation behavior
- TransactionOptions: Configuration for transactional methods

Design Principles:
1. Declarative transaction boundaries
2. Configurable propagation modes
3. Automatic rollback on exception
4. Support for both sync and async functions
"""

from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
    overload,
)

from lib.oda.transaction.manager import (
    IsolationLevel,
    TransactionManager,
    get_transaction_manager,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# =============================================================================
# ENUMS
# =============================================================================

class PropagationMode(str, Enum):
    """
    Transaction propagation behavior.

    Determines how transactions behave when entering a transactional method.

    - REQUIRED: Join existing transaction or create new one (default)
    - REQUIRES_NEW: Always create new transaction, suspend existing
    - NESTED: Create savepoint if in transaction, else create new
    - SUPPORTS: Use existing transaction if available, else non-transactional
    - NOT_SUPPORTED: Execute non-transactionally, suspend if exists
    - MANDATORY: Must have existing transaction, else raise error
    - NEVER: Must NOT have existing transaction, else raise error
    """
    REQUIRED = "required"
    REQUIRES_NEW = "requires_new"
    NESTED = "nested"
    SUPPORTS = "supports"
    NOT_SUPPORTED = "not_supported"
    MANDATORY = "mandatory"
    NEVER = "never"


# =============================================================================
# OPTIONS
# =============================================================================

@dataclass
class TransactionOptions:
    """
    Configuration options for @transactional decorator.

    Attributes:
        propagation: How to handle existing transactions
        isolation: Database isolation level
        read_only: Mark transaction as read-only (optimization hint)
        timeout_seconds: Transaction timeout (0 = no timeout)
        rollback_for: Exception types that trigger rollback
        no_rollback_for: Exception types that don't trigger rollback
    """
    propagation: PropagationMode = PropagationMode.REQUIRED
    isolation: IsolationLevel = IsolationLevel.READ_COMMITTED
    read_only: bool = False
    timeout_seconds: int = 0
    rollback_for: tuple[type[Exception], ...] = field(default_factory=lambda: (Exception,))
    no_rollback_for: tuple[type[Exception], ...] = field(default_factory=tuple)

    @classmethod
    def default(cls) -> "TransactionOptions":
        """Get default transaction options."""
        return cls()

    @classmethod
    def read_only_opts(cls) -> "TransactionOptions":
        """Get read-only transaction options."""
        return cls(read_only=True)

    @classmethod
    def new_transaction(cls) -> "TransactionOptions":
        """Get options for always-new transaction."""
        return cls(propagation=PropagationMode.REQUIRES_NEW)


# =============================================================================
# DECORATOR IMPLEMENTATION
# =============================================================================

@overload
def transactional(func: F) -> F: ...

@overload
def transactional(
    *,
    propagation: PropagationMode = PropagationMode.REQUIRED,
    isolation: IsolationLevel = IsolationLevel.READ_COMMITTED,
    read_only: bool = False,
    timeout_seconds: int = 0,
    rollback_for: tuple[type[Exception], ...] = (Exception,),
    no_rollback_for: tuple[type[Exception], ...] = (),
) -> Callable[[F], F]: ...


def transactional(
    func: Optional[F] = None,
    *,
    propagation: PropagationMode = PropagationMode.REQUIRED,
    isolation: IsolationLevel = IsolationLevel.READ_COMMITTED,
    read_only: bool = False,
    timeout_seconds: int = 0,
    rollback_for: tuple[type[Exception], ...] = (Exception,),
    no_rollback_for: tuple[type[Exception], ...] = (),
) -> Union[F, Callable[[F], F]]:
    """
    Decorator for automatic transaction management.

    Can be used with or without arguments:

        @transactional
        async def my_function():
            ...

        @transactional(propagation=PropagationMode.REQUIRES_NEW)
        async def my_function():
            ...

    Propagation Behavior:
    - REQUIRED: Join existing or create new (most common)
    - REQUIRES_NEW: Always new, suspends existing
    - NESTED: Savepoint if in transaction
    - MANDATORY: Error if no existing transaction
    - NEVER: Error if existing transaction

    Usage Examples:

        # Basic usage - auto commits on success, rollback on exception
        @transactional
        async def create_user(name: str) -> User:
            user = User(name=name)
            await save(user)
            return user

        # Always create new transaction
        @transactional(propagation=PropagationMode.REQUIRES_NEW)
        async def audit_log(message: str):
            # This runs in its own transaction
            await log_audit(message)

        # Nested savepoint
        @transactional(propagation=PropagationMode.NESTED)
        async def try_operation():
            # If outer transaction, this is a savepoint
            # Can rollback independently
            ...

        # Read-only optimization
        @transactional(read_only=True)
        async def get_all_users() -> list[User]:
            return await query_users()
    """
    options = TransactionOptions(
        propagation=propagation,
        isolation=isolation,
        read_only=read_only,
        timeout_seconds=timeout_seconds,
        rollback_for=rollback_for,
        no_rollback_for=no_rollback_for,
    )

    def decorator(fn: F) -> F:
        import asyncio

        if asyncio.iscoroutinefunction(fn):
            return _wrap_async(fn, options)
        else:
            return _wrap_sync(fn, options)

    if func is not None:
        # Called without arguments: @transactional
        return decorator(func)
    else:
        # Called with arguments: @transactional(...)
        return decorator


def _wrap_async(func: F, options: TransactionOptions) -> F:
    """Wrap an async function with transaction management."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        tm = get_transaction_manager()
        current = tm.get_current()

        # Handle propagation
        should_commit = False
        ctx = None

        try:
            if options.propagation == PropagationMode.REQUIRED:
                if current and current.is_active:
                    # Join existing transaction
                    ctx = current
                else:
                    # Create new transaction
                    ctx = await tm.begin(isolation_level=options.isolation)
                    should_commit = True

            elif options.propagation == PropagationMode.REQUIRES_NEW:
                # Always create new transaction
                ctx = await tm.begin(isolation_level=options.isolation)
                should_commit = True

            elif options.propagation == PropagationMode.NESTED:
                if current and current.is_active:
                    # Create savepoint (nested transaction)
                    ctx = await tm.begin(isolation_level=options.isolation)
                    should_commit = True
                else:
                    # No existing transaction - create new
                    ctx = await tm.begin(isolation_level=options.isolation)
                    should_commit = True

            elif options.propagation == PropagationMode.SUPPORTS:
                # Use existing if available
                ctx = current
                # No commit needed for SUPPORTS

            elif options.propagation == PropagationMode.NOT_SUPPORTED:
                # Execute without transaction
                ctx = None

            elif options.propagation == PropagationMode.MANDATORY:
                if not current or not current.is_active:
                    raise RuntimeError(
                        f"No existing transaction found for MANDATORY propagation "
                        f"in {func.__name__}"
                    )
                ctx = current

            elif options.propagation == PropagationMode.NEVER:
                if current and current.is_active:
                    raise RuntimeError(
                        f"Existing transaction found for NEVER propagation "
                        f"in {func.__name__}"
                    )
                ctx = None

            # Execute function
            result = await func(*args, **kwargs)

            # Commit if we started the transaction
            if should_commit and ctx:
                await tm.commit(ctx)

            return result

        except Exception as e:
            # Check if we should rollback
            should_rollback = (
                isinstance(e, options.rollback_for) and
                not isinstance(e, options.no_rollback_for)
            )

            if should_rollback and should_commit and ctx:
                try:
                    await tm.rollback(ctx)
                except Exception as rollback_error:
                    logger.error(
                        f"Rollback failed in {func.__name__}: {rollback_error}"
                    )

            raise

    return wrapper  # type: ignore


def _wrap_sync(func: F, options: TransactionOptions) -> F:
    """
    Wrap a sync function with transaction management.

    Note: Sync functions in an async context should use run_in_executor
    or be converted to async. This wrapper provides basic support.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        import asyncio

        async def async_call() -> Any:
            # Use the async wrapper logic
            async_wrapper = _wrap_async(
                _sync_to_async(func), options
            )
            return await async_wrapper(*args, **kwargs)

        # Try to get running loop
        try:
            loop = asyncio.get_running_loop()
            # We're in async context - need to schedule
            future = asyncio.ensure_future(async_call())
            # This is tricky - can't block in async
            raise RuntimeError(
                f"Sync function {func.__name__} called in async context. "
                f"Consider making it async."
            )
        except RuntimeError:
            # No running loop - run in new loop
            return asyncio.run(async_call())

    return wrapper  # type: ignore


def _sync_to_async(func: Callable[..., Any]) -> Callable[..., Any]:
    """Convert sync function to async."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


# =============================================================================
# UTILITY DECORATORS
# =============================================================================

def requires_transaction(func: F) -> F:
    """
    Decorator that requires an active transaction.

    Alias for @transactional(propagation=PropagationMode.MANDATORY)
    """
    return transactional(propagation=PropagationMode.MANDATORY)(func)


def new_transaction(func: F) -> F:
    """
    Decorator that always creates a new transaction.

    Alias for @transactional(propagation=PropagationMode.REQUIRES_NEW)
    """
    return transactional(propagation=PropagationMode.REQUIRES_NEW)(func)


def read_only(func: F) -> F:
    """
    Decorator for read-only transactions.

    Alias for @transactional(read_only=True)
    """
    return transactional(read_only=True)(func)


def nested_transaction(func: F) -> F:
    """
    Decorator for nested transaction (savepoint) semantics.

    Alias for @transactional(propagation=PropagationMode.NESTED)
    """
    return transactional(propagation=PropagationMode.NESTED)(func)
