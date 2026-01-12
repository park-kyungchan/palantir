"""
Orion ODA v4.0 - Reasoning Trace Logging (Phase 7.3.2)
=======================================================

Structured logging for agent decision traces:
- ReasoningTrace model for logging agent decisions
- TraceLogger for structured logging with export
- Integration with audit trail for governance

Trace Format:
    Each trace captures:
    - Session context (goal, actor, timestamps)
    - Iteration traces (observations, thoughts, actions)
    - Decision rationale (why actions were selected)
    - Outcome metrics (success rate, timing)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from lib.oda.ontology.ontology_types import utc_now
from lib.oda.paths import get_agent_root

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class TraceLevel(str, Enum):
    """Verbosity level for trace logging."""
    MINIMAL = "minimal"     # Only final outcomes
    STANDARD = "standard"   # Actions and key decisions
    DETAILED = "detailed"   # All thoughts and observations
    DEBUG = "debug"         # Everything including internal state


class TraceEventType(str, Enum):
    """Types of events in a trace."""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"
    OBSERVATION = "observation"
    THOUGHT = "thought"
    ACTION_PLANNED = "action_planned"
    ACTION_EXECUTED = "action_executed"
    GOVERNANCE_CHECK = "governance_check"
    ERROR = "error"
    WARNING = "warning"
    CUSTOM = "custom"


# =============================================================================
# TRACE MODELS
# =============================================================================

class TraceEvent(BaseModel):
    """A single event in a reasoning trace."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: TraceEventType
    timestamp: datetime = Field(default_factory=utc_now)
    iteration: Optional[int] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    level: TraceLevel = TraceLevel.STANDARD

    class Config:
        arbitrary_types_allowed = True

    def to_log_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "iteration": self.iteration,
            "content": self.content,
            "metadata": self.metadata,
        }


class ReasoningTrace(BaseModel):
    """
    Complete trace of an agent reasoning session.

    Contains all events from session start to completion,
    organized by iteration with summary metrics.
    """
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str = Field(default="")
    actor_id: str = Field(default="agent")
    goal: str = Field(default="")
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    final_state: str = Field(default="unknown")

    # Events
    events: List[TraceEvent] = Field(default_factory=list)

    # Metrics
    total_iterations: int = Field(default=0)
    successful_actions: int = Field(default=0)
    failed_actions: int = Field(default=0)
    governance_blocks: int = Field(default=0)
    total_thoughts: int = Field(default=0)

    # Tags for filtering
    tags: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def add_event(
        self,
        event_type: TraceEventType,
        content: Dict[str, Any],
        iteration: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: TraceLevel = TraceLevel.STANDARD,
    ) -> TraceEvent:
        """Add an event to the trace."""
        event = TraceEvent(
            event_type=event_type,
            content=content,
            iteration=iteration,
            metadata=metadata or {},
            level=level,
        )
        self.events.append(event)

        # Update metrics
        if event_type == TraceEventType.THOUGHT:
            self.total_thoughts += 1
        elif event_type == TraceEventType.ACTION_EXECUTED:
            if content.get("success", False):
                self.successful_actions += 1
            else:
                self.failed_actions += 1
        elif event_type == TraceEventType.GOVERNANCE_CHECK:
            if content.get("blocked", False):
                self.governance_blocks += 1

        return event

    def complete(self, final_state: str) -> None:
        """Mark the trace as complete."""
        self.completed_at = utc_now()
        self.final_state = final_state

    def get_events_by_iteration(self, iteration: int) -> List[TraceEvent]:
        """Get all events for a specific iteration."""
        return [e for e in self.events if e.iteration == iteration]

    def get_events_by_type(self, event_type: TraceEventType) -> List[TraceEvent]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]

    def to_summary(self) -> Dict[str, Any]:
        """Get a summary of the trace."""
        duration = None
        if self.completed_at and self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()

        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "actor_id": self.actor_id,
            "goal": self.goal[:100] + "..." if len(self.goal) > 100 else self.goal,
            "final_state": self.final_state,
            "duration_seconds": duration,
            "total_iterations": self.total_iterations,
            "total_events": len(self.events),
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "governance_blocks": self.governance_blocks,
            "total_thoughts": self.total_thoughts,
            "tags": self.tags,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Export complete trace as dictionary."""
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "actor_id": self.actor_id,
            "goal": self.goal,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "final_state": self.final_state,
            "events": [e.to_log_dict() for e in self.events],
            "metrics": {
                "total_iterations": self.total_iterations,
                "successful_actions": self.successful_actions,
                "failed_actions": self.failed_actions,
                "governance_blocks": self.governance_blocks,
                "total_thoughts": self.total_thoughts,
            },
            "tags": self.tags,
        }


# =============================================================================
# TRACE LOGGER
# =============================================================================

class TraceLogger:
    """
    Structured trace logger for agent reasoning.

    Manages trace lifecycle and provides export capabilities.

    Usage:
        ```python
        logger = TraceLogger(
            session_id="session-123",
            actor_id="agent-001",
            goal="Create new service",
        )

        # Log events
        logger.log_observation({"source": "ontology", "data": {...}})
        logger.log_thought("Considering action A because...")
        logger.log_action_planned("file.write", {"path": "/tmp/x"})
        logger.log_action_executed({"success": True, ...})

        # Export
        logger.export_json("/path/to/trace.json")
        ```
    """

    def __init__(
        self,
        session_id: str = "",
        actor_id: str = "agent",
        goal: str = "",
        level: TraceLevel = TraceLevel.STANDARD,
        auto_persist: bool = False,
        persist_path: Optional[Path] = None,
    ):
        """
        Initialize the trace logger.

        Args:
            session_id: Unique session identifier
            actor_id: ID of the agent/actor
            goal: The goal being pursued
            level: Logging verbosity level
            auto_persist: If True, persist trace after each event
            persist_path: Path for auto-persistence
        """
        self.level = level
        self.auto_persist = auto_persist
        self.persist_path = persist_path or (get_agent_root() / "logs" / "traces")

        self._trace = ReasoningTrace(
            session_id=session_id or str(uuid4()),
            actor_id=actor_id,
            goal=goal,
        )
        self._current_iteration: int = 0

        # Log session start
        self._trace.add_event(
            TraceEventType.SESSION_START,
            {"goal": goal, "actor_id": actor_id},
            level=TraceLevel.MINIMAL,
        )

    @property
    def trace(self) -> ReasoningTrace:
        """Get the current trace."""
        return self._trace

    @property
    def trace_id(self) -> str:
        """Get the trace ID."""
        return self._trace.trace_id

    def set_iteration(self, iteration: int) -> None:
        """Set the current iteration number."""
        self._current_iteration = iteration

    def start_iteration(self, iteration: int) -> None:
        """Mark the start of a new iteration."""
        self._current_iteration = iteration
        self._trace.total_iterations = max(self._trace.total_iterations, iteration)
        self._log_event(
            TraceEventType.ITERATION_START,
            {"iteration": iteration},
            level=TraceLevel.STANDARD,
        )

    def end_iteration(self, state: str, error: Optional[str] = None) -> None:
        """Mark the end of an iteration."""
        content = {"iteration": self._current_iteration, "state": state}
        if error:
            content["error"] = error
        self._log_event(
            TraceEventType.ITERATION_END,
            content,
            level=TraceLevel.STANDARD,
        )

    def log_observation(
        self,
        observation: Dict[str, Any],
        source: str = "unknown",
    ) -> None:
        """Log an observation event."""
        self._log_event(
            TraceEventType.OBSERVATION,
            {"source": source, "data": observation},
            level=TraceLevel.DETAILED,
        )

    def log_thought(
        self,
        content: str,
        thought_type: str = "reasoning",
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a thought/reasoning event."""
        self._log_event(
            TraceEventType.THOUGHT,
            {
                "content": content,
                "type": thought_type,
                "confidence": confidence,
            },
            metadata=metadata,
            level=TraceLevel.DETAILED,
        )

    def log_action_planned(
        self,
        action_type: str,
        params: Dict[str, Any],
        rationale: str = "",
    ) -> None:
        """Log a planned action event."""
        self._log_event(
            TraceEventType.ACTION_PLANNED,
            {
                "action_type": action_type,
                "params": params,
                "rationale": rationale,
            },
            level=TraceLevel.STANDARD,
        )

    def log_action_executed(
        self,
        action_type: str,
        result: Dict[str, Any],
    ) -> None:
        """Log an action execution result."""
        self._log_event(
            TraceEventType.ACTION_EXECUTED,
            {
                "action_type": action_type,
                "success": result.get("success", False),
                "result": result,
            },
            level=TraceLevel.STANDARD,
        )

    def log_governance_check(
        self,
        action_type: str,
        decision: str,
        reason: str = "",
        blocked: bool = False,
    ) -> None:
        """Log a governance policy check."""
        self._log_event(
            TraceEventType.GOVERNANCE_CHECK,
            {
                "action_type": action_type,
                "decision": decision,
                "reason": reason,
                "blocked": blocked,
            },
            level=TraceLevel.STANDARD,
        )

    def log_error(
        self,
        error: str,
        exception_type: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an error event."""
        self._log_event(
            TraceEventType.ERROR,
            {
                "error": error,
                "exception_type": exception_type,
            },
            metadata=metadata,
            level=TraceLevel.MINIMAL,
        )

    def log_warning(
        self,
        warning: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a warning event."""
        self._log_event(
            TraceEventType.WARNING,
            {"warning": warning},
            metadata=metadata,
            level=TraceLevel.STANDARD,
        )

    def log_custom(
        self,
        event_name: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        level: TraceLevel = TraceLevel.DETAILED,
    ) -> None:
        """Log a custom event."""
        self._log_event(
            TraceEventType.CUSTOM,
            {"name": event_name, **content},
            metadata=metadata,
            level=level,
        )

    def complete(self, final_state: str) -> ReasoningTrace:
        """Mark the trace as complete and return it."""
        self._trace.add_event(
            TraceEventType.SESSION_END,
            {"final_state": final_state},
            level=TraceLevel.MINIMAL,
        )
        self._trace.complete(final_state)

        if self.auto_persist:
            self._persist()

        return self._trace

    def _log_event(
        self,
        event_type: TraceEventType,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        level: TraceLevel = TraceLevel.STANDARD,
    ) -> None:
        """Internal method to log an event."""
        # Check if level is enabled
        if not self._should_log(level):
            return

        self._trace.add_event(
            event_type=event_type,
            content=content,
            iteration=self._current_iteration,
            metadata=metadata,
            level=level,
        )

        if self.auto_persist:
            self._persist()

    def _should_log(self, event_level: TraceLevel) -> bool:
        """Check if an event should be logged based on level."""
        level_order = [
            TraceLevel.MINIMAL,
            TraceLevel.STANDARD,
            TraceLevel.DETAILED,
            TraceLevel.DEBUG,
        ]
        return level_order.index(event_level) <= level_order.index(self.level)

    def _persist(self) -> None:
        """Persist the trace to disk."""
        try:
            self.export_json(
                self.persist_path / f"{self._trace.trace_id}.json"
            )
        except Exception as e:
            logger.warning(f"Failed to persist trace: {e}")

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def export_json(self, path: Union[str, Path]) -> Path:
        """Export trace to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self._trace.to_full_dict(), f, indent=2)

        return path

    def export_jsonl(self, path: Union[str, Path]) -> Path:
        """Export trace events as JSON Lines (one event per line)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            # Write header
            f.write(json.dumps({
                "type": "header",
                "trace_id": self._trace.trace_id,
                "session_id": self._trace.session_id,
                "goal": self._trace.goal,
                "started_at": self._trace.started_at.isoformat(),
            }) + "\n")

            # Write events
            for event in self._trace.events:
                f.write(json.dumps(event.to_log_dict()) + "\n")

            # Write footer
            f.write(json.dumps({
                "type": "footer",
                "summary": self._trace.to_summary(),
            }) + "\n")

        return path

    def export_markdown(self, path: Union[str, Path]) -> Path:
        """Export trace as readable Markdown document."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# Reasoning Trace: {self._trace.trace_id[:8]}",
            "",
            f"**Goal:** {self._trace.goal}",
            f"**Actor:** {self._trace.actor_id}",
            f"**Started:** {self._trace.started_at.isoformat()}",
            f"**State:** {self._trace.final_state}",
            "",
            "## Summary",
            "",
            f"- Total Iterations: {self._trace.total_iterations}",
            f"- Successful Actions: {self._trace.successful_actions}",
            f"- Failed Actions: {self._trace.failed_actions}",
            f"- Governance Blocks: {self._trace.governance_blocks}",
            "",
            "## Events",
            "",
        ]

        current_iteration = None
        for event in self._trace.events:
            if event.iteration != current_iteration:
                current_iteration = event.iteration
                if current_iteration:
                    lines.append(f"\n### Iteration {current_iteration}\n")

            event_str = f"- **{event.event_type.value}** ({event.timestamp.strftime('%H:%M:%S')})"
            if event.content:
                content_preview = str(event.content)[:200]
                event_str += f": {content_preview}"
            lines.append(event_str)

        with open(path, "w") as f:
            f.write("\n".join(lines))

        return path

    def get_summary(self) -> Dict[str, Any]:
        """Get trace summary."""
        return self._trace.to_summary()


# =============================================================================
# TRACE STORE
# =============================================================================

class TraceStore:
    """
    Storage and retrieval for reasoning traces.

    Provides:
    - Trace persistence to disk
    - Query by session, actor, time range
    - Aggregation and analytics
    """

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the trace store."""
        self.base_path = base_path or (get_agent_root() / "logs" / "traces")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, trace: ReasoningTrace) -> Path:
        """Save a trace to the store."""
        path = self.base_path / f"{trace.trace_id}.json"
        with open(path, "w") as f:
            json.dump(trace.to_full_dict(), f, indent=2)
        return path

    def load(self, trace_id: str) -> Optional[ReasoningTrace]:
        """Load a trace by ID."""
        path = self.base_path / f"{trace_id}.json"
        if not path.exists():
            return None

        with open(path) as f:
            data = json.load(f)

        return self._dict_to_trace(data)

    def list_traces(
        self,
        actor_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List available traces with optional filtering."""
        traces = []

        for path in sorted(self.base_path.glob("*.json"), reverse=True):
            if len(traces) >= limit:
                break

            try:
                with open(path) as f:
                    data = json.load(f)

                if actor_id and data.get("actor_id") != actor_id:
                    continue

                traces.append({
                    "trace_id": data.get("trace_id"),
                    "session_id": data.get("session_id"),
                    "actor_id": data.get("actor_id"),
                    "goal": data.get("goal", "")[:100],
                    "final_state": data.get("final_state"),
                    "started_at": data.get("started_at"),
                })

            except Exception as e:
                logger.warning(f"Failed to load trace {path}: {e}")

        return traces

    def _dict_to_trace(self, data: Dict[str, Any]) -> ReasoningTrace:
        """Convert dictionary to ReasoningTrace."""
        events = []
        for e in data.get("events", []):
            events.append(TraceEvent(
                id=e.get("id", str(uuid4())),
                event_type=TraceEventType(e["event_type"]),
                timestamp=datetime.fromisoformat(e["timestamp"]),
                iteration=e.get("iteration"),
                content=e.get("content", {}),
                metadata=e.get("metadata", {}),
            ))

        metrics = data.get("metrics", {})

        return ReasoningTrace(
            trace_id=data["trace_id"],
            session_id=data.get("session_id", ""),
            actor_id=data.get("actor_id", "agent"),
            goal=data.get("goal", ""),
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            final_state=data.get("final_state", "unknown"),
            events=events,
            total_iterations=metrics.get("total_iterations", 0),
            successful_actions=metrics.get("successful_actions", 0),
            failed_actions=metrics.get("failed_actions", 0),
            governance_blocks=metrics.get("governance_blocks", 0),
            total_thoughts=metrics.get("total_thoughts", 0),
            tags=data.get("tags", []),
        )


__all__ = [
    "TraceLevel",
    "TraceEventType",
    "TraceEvent",
    "ReasoningTrace",
    "TraceLogger",
    "TraceStore",
]
