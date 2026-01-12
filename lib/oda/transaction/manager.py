"""
Orion ODA v4.0 - Transaction Manager
Palantir Foundry Compliant ACID Transaction Management

This module implements:
- TransactionManager: Central transaction coordination
- IsolationLevel: SQLite/SQLAlchemy isolation configuration
- Savepoint: Nested transaction support
- TransactionContext: Transaction state and metadata

Design Principles:
1. ACID compliance through SQLAlchemy session management
2. Nested transactions via savepoints
3. Configurable isolation levels
4. Async-first with context manager support
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class IsolationLevel(str, Enum):
    """
    Database isolation levels.

    SQLite supports:
    - READ_UNCOMMITTED: No isolation (dirty reads possible)
    - READ_COMMITTED: Default for most databases
    - REPEATABLE_READ: Snapshot isolation
    - SERIALIZABLE: Highest isolation (potential deadlocks)

    Note: SQLite in WAL mode effectively provides SERIALIZABLE isolation.
    """
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class TransactionState(str, Enum):
    """Transaction lifecycle state."""
    PENDING = "pending"           # Not yet started
    ACTIVE = "active"             # Transaction in progress
    COMMITTED = "committed"       # Successfully committed
    ROLLED_BACK = "rolled_back"   # Rolled back
    FAILED = "failed"             # Failed with error
    SUSPENDED = "suspended"       # Suspended for nested transaction


# =============================================================================
# DATA CLASSES
# =============================================================================

def _utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def _generate_id() -> str:
    """Generate unique identifier."""
    return uuid.uuid4().hex[:16]


@dataclass
class Savepoint:
    """
    Represents a savepoint within a transaction.

    Savepoints allow partial rollback within a transaction,
    enabling nested transaction semantics.
    """
    id: str = field(default_factory=_generate_id)
    name: str = ""
    created_at: datetime = field(default_factory=_utc_now)
    released: bool = False
    rolled_back: bool = False
    parent_savepoint_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"sp_{self.id}"


@dataclass
class TransactionContext:
    """
    Transaction context containing state and metadata.

    Tracks:
    - Transaction ID and state
    - Isolation level
    - Savepoints for nested transactions
    - Timing information
    - Actor and correlation IDs for audit
    """
    id: str = field(default_factory=_generate_id)
    state: TransactionState = TransactionState.PENDING
    isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED

    # Timing
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    # Audit
    actor_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Savepoints
    savepoints: List[Savepoint] = field(default_factory=list)
    current_savepoint: Optional[Savepoint] = None

    # Nesting
    parent_transaction_id: Optional[str] = None
    nesting_level: int = 0

    # Session reference
    _session: Optional[AsyncSession] = None

    @property
    def is_active(self) -> bool:
        """Check if transaction is active."""
        return self.state == TransactionState.ACTIVE

    @property
    def duration_ms(self) -> Optional[float]:
        """Get transaction duration in milliseconds."""
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds() * 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "id": self.id,
            "state": self.state.value,
            "isolation_level": self.isolation_level.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "savepoint_count": len(self.savepoints),
            "nesting_level": self.nesting_level,
            "parent_transaction_id": self.parent_transaction_id,
        }


# =============================================================================
# TRANSACTION MANAGER
# =============================================================================

# Context variable for current transaction
_current_transaction: ContextVar[Optional[TransactionContext]] = ContextVar(
    "current_transaction", default=None
)


class TransactionManager:
    """
    Central transaction coordinator providing ACID guarantees.

    Features:
    - Async context manager for automatic commit/rollback
    - Nested transaction support via savepoints
    - Configurable isolation levels
    - Transaction lifecycle management (begin, commit, rollback)
    - Savepoint creation and release

    Usage:
        ```python
        from lib.oda.ontology.storage.database import DatabaseManager

        db = DatabaseManager.get()
        tm = TransactionManager(db)

        async with tm.transaction() as ctx:
            # All operations within this block are atomic
            await some_operation()

        # Nested transaction
        async with tm.transaction() as outer:
            await operation1()
            async with tm.transaction() as inner:
                await operation2()
                # Inner savepoint can be rolled back independently
        ```

    Palantir Pattern:
    - All state modifications should go through TransactionManager
    - Use correlation_id for distributed tracing
    - Audit all transaction outcomes
    """

    def __init__(
        self,
        database: Any,  # Database instance
        default_isolation: IsolationLevel = IsolationLevel.READ_COMMITTED,
    ):
        """
        Initialize TransactionManager.

        Args:
            database: Database instance with session_factory
            default_isolation: Default isolation level for new transactions
        """
        self._database = database
        self._default_isolation = default_isolation
        self._active_transactions: Dict[str, TransactionContext] = {}

    @staticmethod
    def get_current() -> Optional[TransactionContext]:
        """Get the current transaction context from context var."""
        return _current_transaction.get()

    @staticmethod
    def set_current(ctx: Optional[TransactionContext]) -> Token[Optional[TransactionContext]]:
        """Set the current transaction context."""
        return _current_transaction.set(ctx)

    def _get_session_factory(self) -> Any:
        """Get session factory from database."""
        return self._database.session_factory

    async def _set_isolation_level(
        self,
        session: AsyncSession,
        level: IsolationLevel
    ) -> None:
        """
        Set isolation level for SQLite session.

        Note: SQLite isolation is set via PRAGMA statements.
        """
        # SQLite doesn't support standard SET TRANSACTION ISOLATION LEVEL
        # Instead, use PRAGMA for read_uncommitted
        if level == IsolationLevel.READ_UNCOMMITTED:
            await session.execute(text("PRAGMA read_uncommitted = 1"))
        else:
            # Default to committed reads (WAL mode provides this)
            await session.execute(text("PRAGMA read_uncommitted = 0"))

    async def begin(
        self,
        isolation_level: Optional[IsolationLevel] = None,
        actor_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> TransactionContext:
        """
        Begin a new transaction.

        If there's already an active transaction, creates a savepoint
        for nested transaction semantics.

        Args:
            isolation_level: Override default isolation level
            actor_id: Actor performing the transaction (for audit)
            correlation_id: Trace ID for distributed tracing

        Returns:
            TransactionContext for the new transaction
        """
        current = self.get_current()

        if current and current.is_active:
            # Nested transaction - create savepoint
            return await self._begin_nested(current, actor_id, correlation_id)

        # New top-level transaction
        ctx = TransactionContext(
            isolation_level=isolation_level or self._default_isolation,
            actor_id=actor_id,
            correlation_id=correlation_id or _generate_id(),
        )

        # Create session
        session_factory = self._get_session_factory()
        session = session_factory()
        ctx._session = session

        # Set isolation level
        await self._set_isolation_level(session, ctx.isolation_level)

        # Begin transaction
        ctx.state = TransactionState.ACTIVE
        ctx.started_at = _utc_now()

        # Register
        self._active_transactions[ctx.id] = ctx
        self.set_current(ctx)

        logger.debug(
            f"Transaction started: id={ctx.id}, isolation={ctx.isolation_level.value}"
        )

        return ctx

    async def _begin_nested(
        self,
        parent: TransactionContext,
        actor_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> TransactionContext:
        """
        Begin a nested transaction using savepoint.

        Args:
            parent: Parent transaction context
            actor_id: Actor for the nested transaction
            correlation_id: Correlation ID (inherits from parent if not provided)

        Returns:
            TransactionContext for the nested transaction
        """
        if not parent._session:
            raise RuntimeError("Parent transaction has no active session")

        # Create savepoint
        savepoint = Savepoint(
            parent_savepoint_id=parent.current_savepoint.id if parent.current_savepoint else None
        )

        # Execute savepoint SQL
        await parent._session.execute(text(f"SAVEPOINT {savepoint.name}"))

        # Create nested context
        ctx = TransactionContext(
            isolation_level=parent.isolation_level,
            actor_id=actor_id or parent.actor_id,
            correlation_id=correlation_id or parent.correlation_id,
            parent_transaction_id=parent.id,
            nesting_level=parent.nesting_level + 1,
        )
        ctx._session = parent._session
        ctx.state = TransactionState.ACTIVE
        ctx.started_at = _utc_now()
        ctx.current_savepoint = savepoint

        # Add savepoint to parent
        parent.savepoints.append(savepoint)
        parent.current_savepoint = savepoint

        # Register
        self._active_transactions[ctx.id] = ctx
        self.set_current(ctx)

        logger.debug(
            f"Nested transaction started: id={ctx.id}, "
            f"savepoint={savepoint.name}, level={ctx.nesting_level}"
        )

        return ctx

    async def commit(self, ctx: Optional[TransactionContext] = None) -> None:
        """
        Commit the transaction.

        For nested transactions, releases the savepoint.
        For top-level transactions, commits the session.

        Args:
            ctx: Transaction context (uses current if not provided)
        """
        ctx = ctx or self.get_current()
        if not ctx:
            raise RuntimeError("No active transaction to commit")

        if not ctx.is_active:
            raise RuntimeError(f"Transaction {ctx.id} is not active: {ctx.state.value}")

        try:
            if ctx.parent_transaction_id:
                # Nested transaction - release savepoint
                if ctx.current_savepoint:
                    await ctx._session.execute(
                        text(f"RELEASE SAVEPOINT {ctx.current_savepoint.name}")
                    )
                    ctx.current_savepoint.released = True
            else:
                # Top-level transaction - commit session
                await ctx._session.commit()

            ctx.state = TransactionState.COMMITTED
            ctx.ended_at = _utc_now()

            logger.debug(
                f"Transaction committed: id={ctx.id}, "
                f"duration={ctx.duration_ms:.2f}ms"
            )

        except Exception as e:
            ctx.state = TransactionState.FAILED
            ctx.ended_at = _utc_now()
            logger.error(f"Transaction commit failed: id={ctx.id}, error={e}")
            raise

        finally:
            self._cleanup_transaction(ctx)

    async def rollback(
        self,
        ctx: Optional[TransactionContext] = None,
        to_savepoint: Optional[str] = None,
    ) -> None:
        """
        Rollback the transaction.

        For nested transactions, rolls back to the savepoint.
        For top-level transactions, rolls back the session.

        Args:
            ctx: Transaction context (uses current if not provided)
            to_savepoint: Optional savepoint name to rollback to
        """
        ctx = ctx or self.get_current()
        if not ctx:
            raise RuntimeError("No active transaction to rollback")

        if ctx.state in (TransactionState.COMMITTED, TransactionState.ROLLED_BACK):
            logger.warning(f"Transaction {ctx.id} already ended: {ctx.state.value}")
            return

        try:
            if to_savepoint:
                # Rollback to specific savepoint
                await ctx._session.execute(text(f"ROLLBACK TO SAVEPOINT {to_savepoint}"))
                # Mark all savepoints after this as rolled back
                for sp in ctx.savepoints:
                    if sp.name == to_savepoint:
                        break
                    sp.rolled_back = True

            elif ctx.parent_transaction_id and ctx.current_savepoint:
                # Nested transaction - rollback savepoint
                await ctx._session.execute(
                    text(f"ROLLBACK TO SAVEPOINT {ctx.current_savepoint.name}")
                )
                ctx.current_savepoint.rolled_back = True
            else:
                # Top-level transaction - rollback session
                await ctx._session.rollback()

            ctx.state = TransactionState.ROLLED_BACK
            ctx.ended_at = _utc_now()

            logger.debug(f"Transaction rolled back: id={ctx.id}")

        except Exception as e:
            ctx.state = TransactionState.FAILED
            ctx.ended_at = _utc_now()
            logger.error(f"Transaction rollback failed: id={ctx.id}, error={e}")
            raise

        finally:
            self._cleanup_transaction(ctx)

    async def savepoint(
        self,
        name: Optional[str] = None,
        ctx: Optional[TransactionContext] = None,
    ) -> Savepoint:
        """
        Create a savepoint within the current transaction.

        Args:
            name: Optional savepoint name (auto-generated if not provided)
            ctx: Transaction context (uses current if not provided)

        Returns:
            Created Savepoint
        """
        ctx = ctx or self.get_current()
        if not ctx or not ctx.is_active:
            raise RuntimeError("No active transaction for savepoint")

        savepoint = Savepoint(
            name=name or f"sp_{_generate_id()}",
            parent_savepoint_id=ctx.current_savepoint.id if ctx.current_savepoint else None,
        )

        await ctx._session.execute(text(f"SAVEPOINT {savepoint.name}"))

        ctx.savepoints.append(savepoint)
        ctx.current_savepoint = savepoint

        logger.debug(f"Savepoint created: {savepoint.name} in transaction {ctx.id}")

        return savepoint

    async def release(
        self,
        savepoint: Savepoint,
        ctx: Optional[TransactionContext] = None,
    ) -> None:
        """
        Release (commit) a savepoint.

        Args:
            savepoint: Savepoint to release
            ctx: Transaction context (uses current if not provided)
        """
        ctx = ctx or self.get_current()
        if not ctx or not ctx.is_active:
            raise RuntimeError("No active transaction for savepoint release")

        await ctx._session.execute(text(f"RELEASE SAVEPOINT {savepoint.name}"))
        savepoint.released = True

        # Update current savepoint to parent
        if ctx.current_savepoint == savepoint and savepoint.parent_savepoint_id:
            for sp in ctx.savepoints:
                if sp.id == savepoint.parent_savepoint_id:
                    ctx.current_savepoint = sp
                    break

        logger.debug(f"Savepoint released: {savepoint.name}")

    def _cleanup_transaction(self, ctx: TransactionContext) -> None:
        """Clean up transaction resources."""
        # Remove from active transactions
        self._active_transactions.pop(ctx.id, None)

        # Reset current if this was current
        current = self.get_current()
        if current and current.id == ctx.id:
            # If nested, restore parent
            if ctx.parent_transaction_id:
                parent = self._active_transactions.get(ctx.parent_transaction_id)
                self.set_current(parent)
            else:
                self.set_current(None)

    @asynccontextmanager
    async def transaction(
        self,
        isolation_level: Optional[IsolationLevel] = None,
        actor_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AsyncGenerator[TransactionContext, None]:
        """
        Async context manager for transaction scope.

        Automatically commits on success, rolls back on exception.

        Usage:
            ```python
            async with tm.transaction() as ctx:
                await do_something()
            # Committed if no exception
            # Rolled back if exception raised
            ```
        """
        ctx = await self.begin(
            isolation_level=isolation_level,
            actor_id=actor_id,
            correlation_id=correlation_id,
        )

        try:
            yield ctx
            await self.commit(ctx)
        except Exception:
            await self.rollback(ctx)
            raise
        finally:
            # Ensure session is closed for top-level transactions
            if not ctx.parent_transaction_id and ctx._session:
                await ctx._session.close()

    def get_active_transactions(self) -> List[TransactionContext]:
        """Get list of all active transactions."""
        return [
            ctx for ctx in self._active_transactions.values()
            if ctx.is_active
        ]

    @property
    def has_active_transaction(self) -> bool:
        """Check if there's an active transaction in current context."""
        current = self.get_current()
        return current is not None and current.is_active


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_transaction_manager: Optional[TransactionManager] = None


def get_transaction_manager() -> TransactionManager:
    """
    Get the global TransactionManager instance.

    Raises:
        RuntimeError: If not initialized
    """
    if _transaction_manager is None:
        raise RuntimeError(
            "TransactionManager not initialized. "
            "Call initialize_transaction_manager() first."
        )
    return _transaction_manager


async def initialize_transaction_manager(
    database: Any = None,
    default_isolation: IsolationLevel = IsolationLevel.READ_COMMITTED,
) -> TransactionManager:
    """
    Initialize the global TransactionManager.

    Args:
        database: Database instance (uses DatabaseManager if not provided)
        default_isolation: Default isolation level

    Returns:
        Initialized TransactionManager
    """
    global _transaction_manager

    if database is None:
        from lib.oda.ontology.storage.database import DatabaseManager
        database = DatabaseManager.get()

    _transaction_manager = TransactionManager(
        database=database,
        default_isolation=default_isolation,
    )

    return _transaction_manager
