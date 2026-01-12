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
    lines: Set[int] = field(default_factory=set)
    snippet: Optional[str] = None
    operation: str = "read"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Ensure lines is a Set for O(1) deduplication."""
        if isinstance(self.lines, list):
            self.lines = set(self.lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "lines": sorted(self.lines),  # Convert set to sorted list for JSON
            "snippet": self.snippet,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
        }

    def add_lines(self, lines: Union[List[int], Set[int], int]) -> None:
        """Add lines to evidence with O(1) deduplication."""
        if isinstance(lines, int):
            self.lines.add(lines)
        else:
            self.lines.update(lines)


# =============================================================================
# EVIDENCE CONTEXT
# =============================================================================

@dataclass
class EvidenceContext:
    """
    Context for evidence collection during a session.

    Aggregates all evidence records for a protocol execution
    or analysis session.

    Uses Set for O(1) deduplication of files_viewed.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    protocol_id: Optional[str] = None
    stage: Optional[str] = None
    records: List[EvidenceRecord] = field(default_factory=list)
    _files_viewed_set: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def files_viewed(self) -> List[str]:
        """Get list of unique files viewed (O(1) lookup via internal Set)."""
        return list(self._files_viewed_set)

    def add_file_viewed(self, file_path: Union[str, Path]) -> None:
        """Add a file to files_viewed with O(1) deduplication."""
        self._files_viewed_set.add(str(file_path))

    def has_file_viewed(self, file_path: Union[str, Path]) -> bool:
        """Check if file has been viewed with O(1) lookup."""
        return str(file_path) in self._files_viewed_set

    @property
    def lines_referenced(self) -> Dict[str, List[int]]:
        """Get lines referenced per file (already deduplicated via Set)."""
        result: Dict[str, Set[int]] = {}
        for record in self.records:
            if record.lines:
                if record.file_path not in result:
                    result[record.file_path] = set()
                result[record.file_path].update(record.lines)
        # Convert to sorted list for output
        return {path: sorted(lines) for path, lines in result.items()}

    def add_lines_referenced(
        self, file_path: Union[str, Path], lines: Union[List[int], Set[int], int]
    ) -> None:
        """Add lines referenced for a specific file."""
        path_str = str(file_path)
        # Find existing record or create new one
        for record in self.records:
            if record.file_path == path_str:
                record.add_lines(lines)
                return
        # Create new record if not found
        if isinstance(lines, int):
            lines_set = {lines}
        elif isinstance(lines, list):
            lines_set = set(lines)
        else:
            lines_set = lines
        self.records.append(EvidenceRecord(
            file_path=path_str,
            lines=lines_set,
            operation="reference",
        ))
        self.add_file_viewed(path_str)

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
        lines: Optional[Union[List[int], Set[int]]] = None,
        snippet: Optional[str] = None,
        operation: str = "read",
    ) -> None:
        """Add a file to evidence."""
        path_str = str(file_path)
        self.records.append(EvidenceRecord(
            file_path=path_str,
            lines=set(lines) if lines else set(),
            snippet=snippet,
            operation=operation,
        ))
        # Also update the files_viewed set for O(1) lookup
        self.add_file_viewed(path_str)

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
        self._files_viewed_set.clear()


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
    - File read tracking with O(1) deduplication
    - Line reference tracking
    - Snippet capture
    - Evidence persistence
    - Cached evidence lookup
    """

    _instance: Optional["EvidenceCollector"] = None
    _lock = threading.Lock()
    _lookup_cache: Dict[str, bool] = {}  # Cache for file lookup

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
        self._files_viewed: Set[str] = set()  # O(1) deduplication
        self._lines_referenced: Dict[str, Set[int]] = {}  # O(1) line deduplication
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

    def add_file_viewed(self, file_path: Union[str, Path]) -> None:
        """
        Add a file to files_viewed with O(1) deduplication.

        Args:
            file_path: Path to the file
        """
        if not self.is_enabled():
            return

        path_str = str(file_path)
        self._files_viewed.add(path_str)

        # Also add to current evidence context
        context = get_current_evidence()
        context.add_file_viewed(path_str)

        # Invalidate cache for this path
        self._invalidate_cache(path_str)

        logger.debug(f"Evidence: file_viewed {path_str}")

    def add_lines_referenced(
        self,
        file_path: Union[str, Path],
        lines: Union[List[int], Set[int], int],
    ) -> None:
        """
        Add lines referenced for a file with O(1) deduplication.

        Args:
            file_path: Path to the file
            lines: Line numbers to add (int, list, or set)
        """
        if not self.is_enabled():
            return

        path_str = str(file_path)

        # Ensure file is in files_viewed
        self.add_file_viewed(path_str)

        # Initialize set if needed
        if path_str not in self._lines_referenced:
            self._lines_referenced[path_str] = set()

        # Add lines with O(1) deduplication
        if isinstance(lines, int):
            self._lines_referenced[path_str].add(lines)
        else:
            self._lines_referenced[path_str].update(lines)

        # Also add to context
        context = get_current_evidence()
        context.add_lines_referenced(path_str, lines)

        logger.debug(f"Evidence: lines_referenced {path_str} {lines}")

    @functools.lru_cache(maxsize=1000)
    def has_file_viewed(self, file_path: str) -> bool:
        """
        Check if a file has been viewed with O(1) cached lookup.

        Args:
            file_path: Path to check

        Returns:
            True if file has been viewed
        """
        return file_path in self._files_viewed

    def _invalidate_cache(self, file_path: str) -> None:
        """Invalidate cache for a specific file path."""
        # Clear the lru_cache entry for this path
        self.has_file_viewed.cache_clear()

    def get_files_viewed(self) -> List[str]:
        """Get list of all files viewed."""
        return list(self._files_viewed)

    def get_lines_referenced(self) -> Dict[str, List[int]]:
        """Get all lines referenced, sorted by file."""
        return {path: sorted(lines) for path, lines in self._lines_referenced.items()}

    def to_dict(self) -> Dict[str, Any]:
        """Convert collector state to dictionary."""
        return {
            "files_viewed": self.get_files_viewed(),
            "lines_referenced": self.get_lines_referenced(),
            "mode": self._mode.value,
            "enabled": self.is_enabled(),
        }

    def record_file_read(
        self,
        file_path: Union[str, Path],
        lines: Optional[Union[List[int], Set[int]]] = None,
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

        path_str = str(file_path)
        self.add_file_viewed(path_str)

        if lines:
            self.add_lines_referenced(path_str, lines)

        context = get_current_evidence()
        context.add_file(
            file_path=path_str,
            lines=lines,
            snippet=snippet,
            operation="read",
        )

        logger.debug(f"Evidence: read {file_path}, lines={lines}")

    def record_grep(
        self,
        file_path: Union[str, Path],
        lines: Union[List[int], Set[int]],
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

        path_str = str(file_path)
        self.add_file_viewed(path_str)
        self.add_lines_referenced(path_str, lines)

        context = get_current_evidence()
        context.add_file(
            file_path=path_str,
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
            self.add_file_viewed(file_path)
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

    def clear(self) -> None:
        """Clear all evidence from collector."""
        self._files_viewed.clear()
        self._lines_referenced.clear()
        self.has_file_viewed.cache_clear()
        clear_evidence()


# =============================================================================
# DECORATORS
# =============================================================================

def auto_evidence(method: F) -> F:
    """
    Decorator that auto-captures files_viewed on Read/Grep/Glob operations.

    Designed for use with class methods where `self` has an `_evidence_collector`
    attribute. Automatically extracts file path from args/kwargs.

    Usage:
        ```python
        class FileReader:
            def __init__(self):
                self._evidence_collector = EvidenceCollector()

            @auto_evidence
            def read_file(self, path: str) -> str:
                with open(path) as f:
                    return f.read()
        ```
    """
    @functools.wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        result = method(self, *args, **kwargs)
        # Extract file path from args/kwargs and add to evidence
        if hasattr(self, "_evidence_collector"):
            path = args[0] if args else kwargs.get("path", kwargs.get("file_path"))
            if path:
                self._evidence_collector.add_file_viewed(path)
        return result

    return wrapper  # type: ignore


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
