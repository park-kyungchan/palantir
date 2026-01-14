"""
Orion ODA v3.0 - Evidence Collector

Automatic evidence tracking system for anti-hallucination enforcement.

Features:
- Decorator-based evidence capture (@track_evidence)
- Thread-safe context storage
- Automatic files_viewed tracking
- Lines referenced tracking
- Code snippet capture
- Evidence persistence support

Environment Variables:
    ORION_EVIDENCE_MODE: Evidence mode (persist|memory|off)

Usage:
    ```python
    from lib.oda.ontology.evidence import track_evidence, get_current_evidence

    @track_evidence
    def read_file(path: str) -> str:
        with open(path) as f:
            return f.read()

    content = read_file("/path/to/file.py")
    evidence = get_current_evidence()
    print(evidence.files_viewed)  # ["/path/to/file.py"]
    ```
"""
from __future__ import annotations

import contextvars
import functools
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
from uuid import uuid4

logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


# =============================================================================
# EVIDENCE MODE
# =============================================================================

class EvidenceMode(str, Enum):
    """Evidence collection mode."""
    PERSIST = "persist"   # Persist to database
    MEMORY = "memory"     # Keep in memory only
    OFF = "off"           # No evidence collection

    @classmethod
    def from_env(cls) -> "EvidenceMode":
        """Get evidence mode from environment."""
        mode = os.environ.get("ORION_EVIDENCE_MODE", "memory").lower()
        if mode == "persist":
            return cls.PERSIST
        elif mode == "off":
            return cls.OFF
        return cls.MEMORY


# =============================================================================
# EVIDENCE RECORD
# =============================================================================

@dataclass
class EvidenceRecord:
    """
    Single evidence record for a specific operation.

    Captures:
    - file_path: The file that was accessed
    - lines: Specific line numbers referenced
    - snippet: Code snippet if captured
    - operation: Type of operation (read, grep, etc.)
    - timestamp: When the evidence was collected
    """
    file_path: str
    lines: List[int] = field(default_factory=list)
    snippet: Optional[str] = None
    operation: str = "read"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "lines": self.lines,
            "snippet": self.snippet,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# EVIDENCE CONTEXT
# =============================================================================

@dataclass
class EvidenceContext:
    """
    Context for evidence collection during a session.

    Aggregates all evidence records for a protocol execution
    or analysis session.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    protocol_id: Optional[str] = None
    stage: Optional[str] = None
    records: List[EvidenceRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def files_viewed(self) -> List[str]:
        """Get list of unique files viewed."""
        seen = set()
        result = []
        for record in self.records:
            if record.file_path not in seen:
                seen.add(record.file_path)
                result.append(record.file_path)
        return result

    @property
    def lines_referenced(self) -> Dict[str, List[int]]:
        """Get lines referenced per file."""
        result: Dict[str, List[int]] = {}
        for record in self.records:
            if record.lines:
                if record.file_path not in result:
                    result[record.file_path] = []
                result[record.file_path].extend(record.lines)
        # Deduplicate and sort
        for path in result:
            result[path] = sorted(set(result[path]))
        return result

    @property
    def code_snippets(self) -> List[Dict[str, Any]]:
        """Get all captured code snippets."""
        return [
            {
                "file": r.file_path,
                "lines": r.lines,
                "snippet": r.snippet,
            }
            for r in self.records
            if r.snippet
        ]

    def add_file(
        self,
        file_path: str,
        lines: Optional[List[int]] = None,
        snippet: Optional[str] = None,
        operation: str = "read",
    ) -> None:
        """Add a file to evidence."""
        self.records.append(EvidenceRecord(
            file_path=str(file_path),
            lines=lines or [],
            snippet=snippet,
            operation=operation,
        ))

    def has_evidence(self) -> bool:
        """Check if any evidence has been collected."""
        return len(self.records) > 0

    def validate(self, strict: bool = False) -> bool:
        """
        Validate that evidence is sufficient.

        Args:
            strict: If True, requires at least one file_viewed

        Returns:
            True if valid, False otherwise
        """
        if strict:
            return len(self.files_viewed) > 0
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "stage": self.stage,
            "files_viewed": self.files_viewed,
            "lines_referenced": self.lines_referenced,
            "code_snippets": self.code_snippets,
            "record_count": len(self.records),
            "created_at": self.created_at.isoformat(),
        }

    def merge(self, other: "EvidenceContext") -> None:
        """Merge evidence from another context."""
        self.records.extend(other.records)

    def clear(self) -> None:
        """Clear all evidence."""
        self.records.clear()


# =============================================================================
# CONTEXT VAR STORAGE (Thread-Safe)
# =============================================================================

# Context variable for thread-safe evidence storage
_evidence_context: contextvars.ContextVar[Optional[EvidenceContext]] = contextvars.ContextVar(
    "evidence_context",
    default=None,
)


def get_current_evidence() -> EvidenceContext:
    """
    Get the current evidence context.

    Creates a new context if none exists.
    """
    context = _evidence_context.get()
    if context is None:
        context = EvidenceContext()
        _evidence_context.set(context)
    return context


def set_evidence_context(context: EvidenceContext) -> None:
    """Set the current evidence context."""
    _evidence_context.set(context)


def clear_evidence() -> None:
    """Clear the current evidence context."""
    context = _evidence_context.get()
    if context:
        context.clear()


def new_evidence_context(
    protocol_id: Optional[str] = None,
    stage: Optional[str] = None,
) -> EvidenceContext:
    """
    Create and set a new evidence context.

    Args:
        protocol_id: Optional protocol execution ID
        stage: Optional stage name (e.g., "stage_a_scan")

    Returns:
        The new evidence context
    """
    context = EvidenceContext(protocol_id=protocol_id, stage=stage)
    _evidence_context.set(context)
    return context


# =============================================================================
# EVIDENCE COLLECTOR
# =============================================================================

class EvidenceCollector:
    """
    Evidence collector singleton for managing evidence across operations.

    Provides:
    - File read tracking
    - Line reference tracking
    - Snippet capture
    - Evidence persistence
    """

    _instance: Optional["EvidenceCollector"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EvidenceCollector":
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the collector."""
        if getattr(self, "_initialized", False):
            return

        self._mode = EvidenceMode.from_env()
        self._initialized = True

    @property
    def mode(self) -> EvidenceMode:
        """Current evidence mode."""
        return self._mode

    @mode.setter
    def mode(self, value: EvidenceMode) -> None:
        """Set evidence mode."""
        self._mode = value

    def is_enabled(self) -> bool:
        """Check if evidence collection is enabled."""
        return self._mode != EvidenceMode.OFF

    def record_file_read(
        self,
        file_path: Union[str, Path],
        lines: Optional[List[int]] = None,
        snippet: Optional[str] = None,
    ) -> None:
        """
        Record a file read operation.

        Args:
            file_path: Path to the file
            lines: Specific lines referenced
            snippet: Code snippet if captured
        """
        if not self.is_enabled():
            return

        context = get_current_evidence()
        context.add_file(
            file_path=str(file_path),
            lines=lines,
            snippet=snippet,
            operation="read",
        )

        logger.debug(f"Evidence: read {file_path}, lines={lines}")

    def record_grep(
        self,
        file_path: Union[str, Path],
        lines: List[int],
        pattern: str,
    ) -> None:
        """
        Record a grep operation.

        Args:
            file_path: Path to the file
            lines: Matching line numbers
            pattern: Search pattern used
        """
        if not self.is_enabled():
            return

        context = get_current_evidence()
        context.add_file(
            file_path=str(file_path),
            lines=lines,
            snippet=f"Pattern: {pattern}",
            operation="grep",
        )

        logger.debug(f"Evidence: grep {file_path}, lines={lines}, pattern={pattern}")

    def record_glob(
        self,
        pattern: str,
        matched_files: List[str],
    ) -> None:
        """
        Record a glob operation.

        Args:
            pattern: Glob pattern used
            matched_files: List of matched file paths
        """
        if not self.is_enabled():
            return

        context = get_current_evidence()
        for file_path in matched_files:
            context.add_file(
                file_path=file_path,
                operation="glob",
                snippet=f"Pattern: {pattern}",
            )

        logger.debug(f"Evidence: glob {pattern}, {len(matched_files)} matches")

    def get_evidence_dict(self) -> Dict[str, Any]:
        """Get current evidence as dictionary."""
        return get_current_evidence().to_dict()

    def validate_evidence(self, strict: bool = False) -> bool:
        """
        Validate current evidence.

        Args:
            strict: If True, requires at least one file_viewed

        Returns:
            True if valid
        """
        return get_current_evidence().validate(strict)


# =============================================================================
# DECORATOR
# =============================================================================

def track_evidence(func: F) -> F:
    """
    Decorator to automatically track evidence for file operations.

    Inspects function arguments for file paths and records them.

    Usage:
        ```python
        @track_evidence
        def read_file(path: str) -> str:
            with open(path) as f:
                return f.read()
        ```
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        collector = EvidenceCollector()

        # Try to extract file path from args or kwargs
        file_path = None

        # Check common parameter names
        for name in ("path", "file_path", "filepath", "file", "filename"):
            if name in kwargs:
                file_path = kwargs[name]
                break

        # Check first positional arg if it looks like a path
        if file_path is None and args:
            first_arg = args[0]
            if isinstance(first_arg, (str, Path)):
                potential_path = str(first_arg)
                if "/" in potential_path or "\\" in potential_path:
                    file_path = potential_path

        # Execute the function
        result = func(*args, **kwargs)

        # Record evidence if file path was found
        if file_path:
            collector.record_file_read(file_path)

        return result

    return wrapper  # type: ignore


# =============================================================================
# CONTEXT MANAGER
# =============================================================================

class evidence_scope:
    """
    Context manager for scoped evidence collection.

    Usage:
        ```python
        with evidence_scope(protocol_id="p123", stage="stage_a"):
            # All file operations here are tracked
            content = read_file("/path/to/file.py")

        # After scope, evidence is available
        ```
    """

    def __init__(
        self,
        protocol_id: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> None:
        self.protocol_id = protocol_id
        self.stage = stage
        self._previous_context: Optional[EvidenceContext] = None

    def __enter__(self) -> EvidenceContext:
        """Enter the scope and create new context."""
        self._previous_context = _evidence_context.get()
        context = new_evidence_context(
            protocol_id=self.protocol_id,
            stage=self.stage,
        )
        return context

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the scope and restore previous context."""
        if self._previous_context is not None:
            _evidence_context.set(self._previous_context)


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

def get_collector() -> EvidenceCollector:
    """Get the global EvidenceCollector instance."""
    return EvidenceCollector()
