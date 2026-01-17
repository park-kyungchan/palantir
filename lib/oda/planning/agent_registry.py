"""
Orion ODA v3.0 - YAML-Based Agent Registry
==========================================

Persistent agent tracking for Resume-Enhanced Orchestration.

This module provides YAML-based persistence for agent IDs, enabling
resume capability across Auto-Compact events and session interruptions.

Features:
- YAML persistence in .agent/config/agent_registry.yaml
- Automatic cleanup of expired agents
- Resume eligibility checks
- Integration with Plan Files

Usage:
    registry = AgentRegistry()

    # Register new agent
    registry.register("a1b2c3d", "Explore", "Phase 1 analysis")

    # After Auto-Compact, get resumable agents
    for agent in registry.get_resumable():
        Task(resume=agent.id, ...)

    # Mark completion
    registry.mark_completed("a1b2c3d")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # Will use JSON fallback

logger = logging.getLogger(__name__)


@dataclass
class AgentEntry:
    """Single agent entry in the registry."""
    id: str
    type: str
    description: str
    status: str  # running | completed | failed | interrupted
    created_at: str
    completed_at: Optional[str] = None
    context_budget: int = 5000
    output_path: str = ""
    resume_eligible: bool = True
    parent_task: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "context_budget": self.context_budget,
            "output_path": self.output_path,
            "resume_eligible": self.resume_eligible,
            "parent_task": self.parent_task,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentEntry":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            description=data.get("description", ""),
            status=data.get("status", "running"),
            created_at=data.get("created_at", ""),
            completed_at=data.get("completed_at"),
            context_budget=data.get("context_budget", 5000),
            output_path=data.get("output_path", ""),
            resume_eligible=data.get("resume_eligible", True),
            parent_task=data.get("parent_task", ""),
        )

    def age_hours(self) -> float:
        """Get age in hours."""
        try:
            created = datetime.fromisoformat(
                self.created_at.replace('Z', '+00:00')
            )
            now = datetime.now(timezone.utc)
            return (now - created).total_seconds() / 3600
        except Exception:
            return float('inf')


class AgentRegistry:
    """
    YAML-based Agent Registry for Resume Support.

    Manages persistent storage of agent IDs for Auto-Compact recovery.
    """

    DEFAULT_PATH = os.path.expanduser("~/.agent/config/agent_registry.yaml")
    MAX_AGE_HOURS = 1
    MAX_ENTRIES = 50

    def __init__(
        self,
        registry_path: Optional[str] = None,
        max_age_hours: int = 1,
        max_entries: int = 50,
    ):
        """
        Initialize AgentRegistry.

        Args:
            registry_path: Path to YAML registry file
            max_age_hours: Maximum age for resumable agents
            max_entries: Maximum number of agents to track
        """
        self.registry_path = registry_path or self.DEFAULT_PATH
        self.max_age_hours = max_age_hours
        self.max_entries = max_entries

        # In-memory cache
        self._agents: Dict[str, AgentEntry] = {}
        self._history: List[Dict[str, Any]] = []
        self._session_id: str = ""

        # Load existing registry
        self._load()

        # Cleanup expired entries
        self._cleanup_expired()

    def _load(self):
        """Load registry from YAML file."""
        if not os.path.exists(self.registry_path):
            return

        try:
            with open(self.registry_path, 'r') as f:
                if yaml:
                    data = yaml.safe_load(f) or {}
                else:
                    import json
                    data = json.load(f)

            # Load agents
            for agent_data in data.get("agents", []):
                entry = AgentEntry.from_dict(agent_data)
                self._agents[entry.id] = entry

            # Load history
            self._history = data.get("history", [])

            # Load session ID
            self._session_id = data.get("session_id", "")

            logger.debug(f"Loaded {len(self._agents)} agents from registry")

        except Exception as e:
            logger.warning(f"Failed to load agent registry: {e}")

    def _save(self):
        """Save registry to YAML file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)

            data = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "session_id": self._session_id,
                "config": {
                    "max_age_hours": self.max_age_hours,
                    "max_entries": self.max_entries,
                    "cleanup_on_load": True,
                },
                "agents": [a.to_dict() for a in self._agents.values()],
                "history": self._history[-20:],  # Keep last 20 in history
            }

            with open(self.registry_path, 'w') as f:
                if yaml:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                else:
                    import json
                    json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"Failed to save agent registry: {e}")

    def _cleanup_expired(self):
        """Remove expired agents."""
        expired = []
        for agent_id, entry in list(self._agents.items()):
            if entry.age_hours() > self.max_age_hours:
                if entry.status in ("running", "interrupted"):
                    # Move to history before removing
                    self._history.append({
                        "id": entry.id,
                        "type": entry.type,
                        "expired_at": datetime.now(timezone.utc).isoformat(),
                        "reason": "max_age_exceeded",
                    })
                del self._agents[agent_id]
                expired.append(agent_id)

        # Limit total entries
        while len(self._agents) > self.max_entries:
            # Remove oldest completed
            oldest = min(
                (a for a in self._agents.values() if a.status == "completed"),
                key=lambda a: a.created_at,
                default=None
            )
            if oldest:
                del self._agents[oldest.id]
            else:
                break

        if expired:
            self._save()
            logger.info(f"Cleaned up {len(expired)} expired agents")

    def register(
        self,
        agent_id: str,
        agent_type: str,
        description: str,
        context_budget: int = 5000,
        parent_task: str = "",
        output_path: str = "",
    ) -> AgentEntry:
        """
        Register a new agent.

        Args:
            agent_id: Agent ID from Task result
            agent_type: Type of subagent (Explore, Plan, etc.)
            description: Task description
            context_budget: Token budget used
            parent_task: Parent plan/task identifier
            output_path: Path to L2 output if available

        Returns:
            Created AgentEntry
        """
        entry = AgentEntry(
            id=agent_id,
            type=agent_type,
            description=description,
            status="running",
            created_at=datetime.now(timezone.utc).isoformat(),
            context_budget=context_budget,
            output_path=output_path,
            resume_eligible=True,
            parent_task=parent_task,
        )

        self._agents[agent_id] = entry
        self._save()

        logger.info(f"Registered agent: {agent_id} ({agent_type})")
        return entry

    def mark_completed(
        self,
        agent_id: str,
        output_path: str = "",
    ):
        """Mark agent as completed."""
        if agent_id in self._agents:
            self._agents[agent_id].status = "completed"
            self._agents[agent_id].completed_at = datetime.now(timezone.utc).isoformat()
            self._agents[agent_id].resume_eligible = False
            if output_path:
                self._agents[agent_id].output_path = output_path
            self._save()

    def mark_failed(
        self,
        agent_id: str,
        resumable: bool = True,
    ):
        """Mark agent as failed, optionally allowing resume."""
        if agent_id in self._agents:
            self._agents[agent_id].status = "failed"
            self._agents[agent_id].resume_eligible = resumable
            self._save()

    def mark_interrupted(self, agent_id: str):
        """Mark agent as interrupted (for Auto-Compact)."""
        if agent_id in self._agents:
            self._agents[agent_id].status = "interrupted"
            self._agents[agent_id].resume_eligible = True
            self._save()

    def get(self, agent_id: str) -> Optional[AgentEntry]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_resumable(self) -> List[AgentEntry]:
        """
        Get list of agents eligible for resume.

        Returns agents that are:
        - Status: running or interrupted
        - Age: < max_age_hours
        - resume_eligible: True
        """
        return [
            entry for entry in self._agents.values()
            if entry.resume_eligible
            and entry.status in ("running", "interrupted")
            and entry.age_hours() < self.max_age_hours
        ]

    def get_by_parent(self, parent_task: str) -> List[AgentEntry]:
        """Get all agents for a parent task."""
        return [
            entry for entry in self._agents.values()
            if entry.parent_task == parent_task
        ]

    def get_by_type(self, agent_type: str) -> List[AgentEntry]:
        """Get all agents of a specific type."""
        return [
            entry for entry in self._agents.values()
            if entry.type == agent_type
        ]

    def can_resume(self, agent_id: str) -> bool:
        """Check if agent can be resumed."""
        entry = self.get(agent_id)
        if not entry:
            return False

        return (
            entry.resume_eligible
            and entry.status in ("running", "interrupted")
            and entry.age_hours() < self.max_age_hours
        )

    def list_all(self) -> List[AgentEntry]:
        """List all tracked agents."""
        return list(self._agents.values())

    def clear_completed(self):
        """Remove all completed agents."""
        to_remove = [
            agent_id for agent_id, entry in self._agents.items()
            if entry.status == "completed"
        ]
        for agent_id in to_remove:
            del self._agents[agent_id]

        if to_remove:
            self._save()
            logger.info(f"Cleared {len(to_remove)} completed agents")

    def update_session(self, session_id: str):
        """Update session ID."""
        self._session_id = session_id
        self._save()

    def to_markdown_table(self) -> str:
        """
        Generate markdown table for Plan File integration.

        Returns table suitable for Plan File's Agent Registry section.
        """
        lines = [
            "| Task | Agent ID | Type | Status | Resume Eligible |",
            "|------|----------|------|--------|-----------------|",
        ]

        for entry in self._agents.values():
            resume = "Yes" if entry.resume_eligible and entry.status in ("running", "interrupted") else "No"
            lines.append(
                f"| {entry.description[:30]} | {entry.id} | {entry.type} | {entry.status} | {resume} |"
            )

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────────────────────

# Module-level singleton
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get or create session-wide AgentRegistry."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def register_agent(
    agent_id: str,
    agent_type: str,
    description: str,
    **kwargs,
) -> AgentEntry:
    """Quick function to register an agent."""
    return get_registry().register(agent_id, agent_type, description, **kwargs)


def get_resumable_agents() -> List[AgentEntry]:
    """Quick function to get resumable agents."""
    return get_registry().get_resumable()


def can_resume_agent(agent_id: str) -> bool:
    """Quick function to check resume eligibility."""
    return get_registry().can_resume(agent_id)
