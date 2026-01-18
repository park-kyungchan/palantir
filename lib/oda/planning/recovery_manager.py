"""
Orion ODA v3.0 - Auto-Compact Recovery Manager
===============================================

Recovery system for maintaining context after Claude Code Auto-Compact events.

Since Claude Code does NOT support SessionStart/PostCompact hooks, this module
provides a hybrid approach:
1. Behavioral injection via CLAUDE.md (advisory triggers)
2. /recover Skill for explicit recovery invocation
3. Persistent state tracking for context restoration

The goal is to ensure Main Agent NEVER operates with incomplete context
by providing mechanisms to detect context loss and recover detailed results.

Key Components:
- RecoveryState: Captures all recoverable state data
- AutoCompactRecoveryManager: Coordinates detection and recovery

Usage:
    manager = AutoCompactRecoveryManager()

    # Check if recovery is needed
    if manager.detect_recovery_needed():
        state = manager.collect_recovery_state()
        prompt = manager.generate_recovery_prompt()
        # Use prompt to restore Main Agent context

References:
- CLAUDE.md Section 2.12: Auto-Compact Recovery
- .claude/commands/recover.md: /recover Skill
- lib/oda/planning/output_layer_manager.py: L2/L3 access
- TodoWrite comprehensive format for agent ID tracking
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# Local imports (lazy to avoid circular dependencies)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

WORKSPACE_ROOT = os.environ.get("ORION_WORKSPACE_ROOT", os.path.expanduser("~"))
PALANTIR_ROOT = os.path.join(WORKSPACE_ROOT, "park-kyungchan/palantir")

RECOVERY_STATE_PATH = os.path.join(PALANTIR_ROOT, ".agent/recovery-state.json")
PLANS_DIR = os.path.join(PALANTIR_ROOT, ".agent/plans")
L2_OUTPUT_DIR = os.path.join(WORKSPACE_ROOT, ".agent/outputs")
TODO_DIR = os.path.join(PALANTIR_ROOT, ".claude/todos")

# Maximum age for considering plan files relevant (hours)
MAX_PLAN_AGE_HOURS = 4

# Recovery trigger keywords (context loss indicators)
CONTEXT_LOSS_INDICATORS = [
    "잘 모르겠",  # "I'm not sure"
    "기억이 없",  # "No memory of"
    "what we were",
    "where we left",
    "context seems",
    "컨텍스트가",
    "요약만",
    "summary only",
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class RecoveryState:
    """
    Captures all recoverable state for Auto-Compact recovery.

    This dataclass holds the complete picture of what can be restored
    after context compaction.
    """
    session_id: str = ""
    timestamp: str = ""

    # Plan files
    active_plan_path: Optional[str] = None
    plan_content: str = ""

    # Agent registry
    resumable_agents: List[Dict[str, Any]] = field(default_factory=list)
    interrupted_agents: List[Dict[str, Any]] = field(default_factory=list)

    # Todo state
    incomplete_todos: List[Dict[str, Any]] = field(default_factory=list)
    in_progress_todo: Optional[str] = None

    # L2 reports available
    l2_reports: List[str] = field(default_factory=list)
    l2_content_preview: Dict[str, str] = field(default_factory=dict)

    # Recovery determination
    recovery_needed: bool = False
    recovery_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "active_plan_path": self.active_plan_path,
            "plan_content": self.plan_content[:1000] if self.plan_content else "",  # Truncate
            "resumable_agents": self.resumable_agents,
            "interrupted_agents": self.interrupted_agents,
            "incomplete_todos": self.incomplete_todos,
            "in_progress_todo": self.in_progress_todo,
            "l2_reports": self.l2_reports,
            "l2_content_preview": self.l2_content_preview,
            "recovery_needed": self.recovery_needed,
            "recovery_reasons": self.recovery_reasons,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecoveryState":
        """Create from dictionary."""
        return cls(
            session_id=data.get("session_id", ""),
            timestamp=data.get("timestamp", ""),
            active_plan_path=data.get("active_plan_path"),
            plan_content=data.get("plan_content", ""),
            resumable_agents=data.get("resumable_agents", []),
            interrupted_agents=data.get("interrupted_agents", []),
            incomplete_todos=data.get("incomplete_todos", []),
            in_progress_todo=data.get("in_progress_todo"),
            l2_reports=data.get("l2_reports", []),
            l2_content_preview=data.get("l2_content_preview", {}),
            recovery_needed=data.get("recovery_needed", False),
            recovery_reasons=data.get("recovery_reasons", []),
        )


@dataclass
class L2ReportInfo:
    """Information about an L2 structured report."""
    path: str
    agent_id: str
    agent_type: str
    created_at: str
    summary: str = ""


# =============================================================================
# Auto-Compact Recovery Manager
# =============================================================================

class AutoCompactRecoveryManager:
    """
    Coordinates Auto-Compact recovery operations.

    This manager provides:
    1. Detection of recovery need (context loss indicators)
    2. Collection of recoverable state (plans, agents, todos, L2)
    3. Generation of recovery prompt for Main Agent
    4. L2 content injection for context restoration
    """

    def __init__(
        self,
        workspace_root: Optional[str] = None,
        plans_dir: Optional[str] = None,
        l2_output_dir: Optional[str] = None,
        todo_dir: Optional[str] = None,
    ):
        """
        Initialize Recovery Manager.

        Args:
            workspace_root: Root workspace path
            plans_dir: Directory containing plan files
            l2_output_dir: Directory containing L2 structured reports
            todo_dir: Directory containing TodoWrite JSON files
        """
        self.workspace_root = workspace_root or WORKSPACE_ROOT
        self.plans_dir = plans_dir or PLANS_DIR
        self.l2_output_dir = l2_output_dir or L2_OUTPUT_DIR
        self.todo_dir = todo_dir or TODO_DIR

        # Cached state
        self._cached_state: Optional[RecoveryState] = None
        self._last_check_time: Optional[datetime] = None

    # ─────────────────────────────────────────────────────────────────────────
    # Detection
    # ─────────────────────────────────────────────────────────────────────────

    def detect_recovery_needed(
        self,
        user_message: str = "",
        check_files: bool = True,
    ) -> bool:
        """
        Detect if context recovery is needed.

        Checks multiple indicators:
        1. User message contains context loss keywords
        2. Recovery state file indicates pending recovery
        3. Agent registry has interrupted agents
        4. Plan files exist with incomplete status

        Args:
            user_message: Current user message to check for keywords
            check_files: Whether to check file-based indicators

        Returns:
            True if recovery appears needed
        """
        reasons = []

        # Check 1: User message keywords
        if user_message:
            message_lower = user_message.lower()
            for indicator in CONTEXT_LOSS_INDICATORS:
                if indicator.lower() in message_lower:
                    reasons.append(f"user_keyword:{indicator}")
                    break

        # Check 2: Recovery state file
        if check_files and os.path.exists(RECOVERY_STATE_PATH):
            try:
                with open(RECOVERY_STATE_PATH, 'r') as f:
                    saved_state = json.load(f)
                if saved_state.get("recovery_needed"):
                    reasons.append("saved_state:recovery_needed")
            except Exception as e:
                logger.debug(f"Failed to read recovery state: {e}")

        # Check 3: TodoWrite state (agent IDs in comprehensive format)
        if check_files:
            incomplete_todos, in_progress = self._get_todo_state()
            pending_agents = self._extract_agent_ids_from_todos(incomplete_todos)
            if pending_agents:
                reasons.append(f"pending_agents_in_todo:{len(pending_agents)}")

        # Check 4: Plan files
        if check_files:
            active_plan = self._find_active_plan()
            if active_plan:
                reasons.append(f"active_plan:{os.path.basename(active_plan)}")

        # Update cached determination
        self._last_check_time = datetime.now(timezone.utc)

        if reasons:
            logger.info(f"Recovery needed: {reasons}")
            return True

        return False

    # ─────────────────────────────────────────────────────────────────────────
    # State Collection
    # ─────────────────────────────────────────────────────────────────────────

    def collect_recovery_state(self) -> RecoveryState:
        """
        Collect all recoverable state information.

        Gathers:
        - Active plan file content
        - Agent registry state (resumable/interrupted)
        - Todo list state (incomplete items)
        - Available L2 reports with previews

        Returns:
            RecoveryState with all collected data
        """
        state = RecoveryState(
            session_id=os.environ.get("CLAUDE_SESSION_ID", "unknown"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Collect plan file
        plan_path = self._find_active_plan()
        if plan_path:
            state.active_plan_path = plan_path
            try:
                with open(plan_path, 'r') as f:
                    state.plan_content = f.read()
            except Exception as e:
                logger.warning(f"Failed to read plan file: {e}")

        # Extract agent IDs from TodoWrite (comprehensive format)
        state.incomplete_todos, state.in_progress_todo = self._get_todo_state()
        state.resumable_agents = self._extract_agent_ids_from_todos(state.incomplete_todos)
        state.interrupted_agents = [a for a in state.resumable_agents if 'pending' not in a.get('id', '')]

        # (Todo state already collected above)

        # Collect L2 reports
        state.l2_reports = self._find_l2_reports()
        state.l2_content_preview = self._get_l2_previews(state.l2_reports[:5])  # Top 5

        # Determine if recovery is needed
        state.recovery_needed = any([
            state.active_plan_path,
            state.resumable_agents,
            state.interrupted_agents,
            state.incomplete_todos,
        ])

        # Build reasons
        if state.active_plan_path:
            state.recovery_reasons.append(f"Plan: {os.path.basename(state.active_plan_path)}")
        if state.interrupted_agents:
            state.recovery_reasons.append(f"Interrupted agents: {len(state.interrupted_agents)}")
        if state.resumable_agents:
            state.recovery_reasons.append(f"Resumable agents: {len(state.resumable_agents)}")
        if state.incomplete_todos:
            state.recovery_reasons.append(f"Incomplete todos: {len(state.incomplete_todos)}")

        # Cache and save
        self._cached_state = state
        self._save_recovery_state(state)

        return state

    # ─────────────────────────────────────────────────────────────────────────
    # Prompt Generation
    # ─────────────────────────────────────────────────────────────────────────

    def generate_recovery_prompt(self, state: Optional[RecoveryState] = None) -> str:
        """
        Generate a recovery prompt for Main Agent context restoration.

        This prompt helps Main Agent understand:
        - What work was in progress
        - Which agents can be resumed
        - What todo items are pending
        - Where to find detailed results (L2/L3)

        Args:
            state: RecoveryState to use (or use cached)

        Returns:
            Formatted prompt string for Main Agent
        """
        state = state or self._cached_state or self.collect_recovery_state()

        lines = [
            "# 🔄 Auto-Compact Recovery Context",
            "",
            f"> Recovered at: {state.timestamp}",
            f"> Session ID: {state.session_id[:8] if state.session_id else 'N/A'}",
            "",
        ]

        # Section 1: Active Plan
        if state.active_plan_path:
            lines.extend([
                "## 📋 Active Plan",
                "",
                f"**File:** `{state.active_plan_path}`",
                "",
                "Plan summary from file:",
                "```markdown",
                self._extract_plan_summary(state.plan_content),
                "```",
                "",
            ])

        # Section 2: Interrupted Agents
        if state.interrupted_agents:
            lines.extend([
                "## ⏸️ Interrupted Agents (Resume Required)",
                "",
                "| Agent ID | Type | Description | Resume Command |",
                "|----------|------|-------------|----------------|",
            ])
            for agent in state.interrupted_agents:
                agent_id = agent.get("id", "")[:7]
                agent_type = agent.get("type", "")
                desc = agent.get("description", "")[:30]
                lines.append(
                    f"| {agent_id} | {agent_type} | {desc} | `Task(resume=\"{agent_id}\")` |"
                )
            lines.append("")

        # Section 3: Resumable Agents
        if state.resumable_agents:
            lines.extend([
                "## 🔁 Resumable Agents",
                "",
                "| Agent ID | Type | Description | Status |",
                "|----------|------|-------------|--------|",
            ])
            for agent in state.resumable_agents:
                agent_id = agent.get("id", "")[:7]
                agent_type = agent.get("type", "")
                desc = agent.get("description", "")[:30]
                status = agent.get("status", "")
                lines.append(f"| {agent_id} | {agent_type} | {desc} | {status} |")
            lines.append("")

        # Section 4: Todo State
        if state.incomplete_todos:
            lines.extend([
                "## ✅ Incomplete Tasks",
                "",
            ])
            if state.in_progress_todo:
                lines.append(f"**Currently in progress:** {state.in_progress_todo}")
                lines.append("")

            lines.append("Pending tasks:")
            for todo in state.incomplete_todos[:10]:  # Max 10
                content = todo.get("content", "")
                status = todo.get("status", "pending")
                marker = "🔄" if status == "in_progress" else "⏳"
                lines.append(f"- {marker} {content}")
            lines.append("")

        # Section 5: L2 Reports
        if state.l2_reports:
            lines.extend([
                "## 📊 Available L2 Reports",
                "",
                "Detailed results available at:",
            ])
            for report_path in state.l2_reports[:5]:
                lines.append(f"- `{report_path}`")
            lines.append("")

            # Include preview if available
            if state.l2_content_preview:
                lines.extend([
                    "### L2 Preview (latest)",
                    "",
                ])
                for path, preview in list(state.l2_content_preview.items())[:2]:
                    lines.extend([
                        f"**{os.path.basename(path)}:**",
                        "```",
                        preview[:500],
                        "```",
                        "",
                    ])

        # Section 6: Recommended Actions
        lines.extend([
            "## 🎯 Recommended Actions",
            "",
        ])

        if state.interrupted_agents:
            lines.append("1. **Resume interrupted agents** to recover full results")
        if state.active_plan_path:
            lines.append("2. **Read plan file** for task context")
        if state.incomplete_todos:
            lines.append("3. **Continue from current task** in todo list")
        if state.l2_reports:
            lines.append("4. **Access L2 reports** for detailed subagent results")

        lines.extend([
            "",
            "---",
            "*Recovery context generated by AutoCompactRecoveryManager*",
        ])

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # L2 Content Injection
    # ─────────────────────────────────────────────────────────────────────────

    def inject_l2_content(
        self,
        agent_ids: Optional[List[str]] = None,
        max_chars: int = 3000,
    ) -> Dict[str, str]:
        """
        Inject L2 structured report content for specified agents.

        Args:
            agent_ids: List of agent IDs to get L2 content for.
                      If None, uses interrupted agents.
            max_chars: Maximum characters per report to include

        Returns:
            Dictionary mapping agent_id to L2 content
        """
        if agent_ids is None:
            # Use interrupted agents from registry
            interrupted = self._get_interrupted_agents()
            agent_ids = [a.get("id", "") for a in interrupted]

        result = {}

        for agent_id in agent_ids:
            if not agent_id:
                continue

            # Find L2 report for this agent
            l2_path = self._find_l2_for_agent(agent_id)
            if l2_path and os.path.exists(l2_path):
                try:
                    with open(l2_path, 'r') as f:
                        content = f.read()

                    # Truncate if needed
                    if len(content) > max_chars:
                        content = content[:max_chars] + "\n... [truncated]"

                    result[agent_id] = content
                    logger.debug(f"Injected L2 for agent {agent_id}")

                except Exception as e:
                    logger.warning(f"Failed to read L2 for {agent_id}: {e}")

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # State Persistence
    # ─────────────────────────────────────────────────────────────────────────

    def _save_recovery_state(self, state: RecoveryState):
        """Save recovery state to file."""
        try:
            os.makedirs(os.path.dirname(RECOVERY_STATE_PATH), exist_ok=True)
            with open(RECOVERY_STATE_PATH, 'w') as f:
                json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save recovery state: {e}")

    def clear_recovery_state(self):
        """Clear saved recovery state after successful recovery."""
        try:
            if os.path.exists(RECOVERY_STATE_PATH):
                os.remove(RECOVERY_STATE_PATH)
                logger.info("Cleared recovery state")
        except Exception as e:
            logger.warning(f"Failed to clear recovery state: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _find_active_plan(self) -> Optional[str]:
        """Find the most recent active plan file."""
        if not os.path.exists(self.plans_dir):
            return None

        # Use os.scandir for better performance
        plan_files = []
        with os.scandir(self.plans_dir) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith('.md'):
                    plan_files.append((entry.path, entry.stat().st_mtime))

        if not plan_files:
            return None

        # Sort by modification time (most recent first)
        plan_files.sort(key=lambda x: x[1], reverse=True)
        plan_files = [p[0] for p in plan_files]

        # Check for active (IN_PROGRESS) plans
        for plan_path in plan_files:
            try:
                with open(plan_path, 'r') as f:
                    content = f.read(500)  # Just check header
                if "IN_PROGRESS" in content or "Status:** IN_PROGRESS" in content:
                    # Check age
                    age_hours = (datetime.now().timestamp() - os.path.getmtime(plan_path)) / 3600
                    if age_hours < MAX_PLAN_AGE_HOURS:
                        return plan_path
            except Exception:
                continue

        return None

    def _extract_agent_ids_from_todos(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract agent IDs from comprehensive TodoWrite format.

        Parses todo content with format:
        "[Phase N] {desc} | Files: {files} | Agent: {type}:{id}"

        Returns list of agent info dicts for resumable agents.
        """
        import re
        agents = []

        agent_pattern = re.compile(r'Agent:\s*(\w+):(\w+)')

        for todo in todos:
            content = todo.get("content", "")
            match = agent_pattern.search(content)
            if match:
                agent_type = match.group(1)
                agent_id = match.group(2)

                # Skip pending agents (not yet executed)
                if agent_id.lower() == "pending":
                    continue

                # Skip completed agents
                if "(done)" in content.lower():
                    continue

                agents.append({
                    "id": agent_id,
                    "type": agent_type,
                    "description": content[:50],
                    "status": todo.get("status", "unknown"),
                    "resume_eligible": True,
                })

        return agents

    def _get_todo_state(self) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get incomplete todos and current in-progress item."""
        # Use os.scandir for better performance
        if not os.path.exists(self.todo_dir):
            return [], None

        todo_paths = []
        with os.scandir(self.todo_dir) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith('.json'):
                    todo_paths.append((entry.path, entry.stat().st_mtime))

        if not todo_paths:
            return [], None

        incomplete = []
        in_progress = None

        # Sort by modification time (most recent first)
        todo_paths.sort(key=lambda x: x[1], reverse=True)

        for todo_path, _ in todo_paths[:1]:  # Just most recent
            try:
                with open(todo_path, 'r') as f:
                    todos = json.load(f)

                for todo in todos:
                    status = todo.get("status", "pending")
                    if status == "in_progress":
                        in_progress = todo.get("content", "")
                        incomplete.append(todo)
                    elif status == "pending":
                        incomplete.append(todo)

            except Exception as e:
                logger.debug(f"Failed to read todo file: {e}")

        return incomplete, in_progress

    def _find_l2_reports(self) -> List[str]:
        """Find available L2 structured reports using os.scandir."""
        if not os.path.exists(self.l2_output_dir):
            return []

        reports = []
        with os.scandir(self.l2_output_dir) as entries:
            for entry in entries:
                if entry.is_dir():
                    with os.scandir(entry.path) as subentries:
                        for subentry in subentries:
                            if subentry.is_file() and subentry.name.endswith('.md'):
                                reports.append((subentry.path, subentry.stat().st_mtime))

        # Sort by modification time (most recent first)
        reports.sort(key=lambda x: x[1], reverse=True)

        return [r[0] for r in reports[:10]]  # Max 10

    def _find_l2_for_agent(self, agent_id: str) -> Optional[str]:
        """Find L2 report for specific agent using os.scandir."""
        if not os.path.exists(self.l2_output_dir):
            return None

        # Search in all subdirectories
        with os.scandir(self.l2_output_dir) as entries:
            for entry in entries:
                if entry.is_dir():
                    # Try exact match first
                    exact_path = os.path.join(entry.path, f"{agent_id}.md")
                    if os.path.exists(exact_path):
                        return exact_path

                    # Try partial match
                    with os.scandir(entry.path) as subentries:
                        for subentry in subentries:
                            if subentry.is_file() and subentry.name.startswith(agent_id[:7]) and subentry.name.endswith('.md'):
                                return subentry.path

        return None

    def _get_l2_previews(self, report_paths: List[str]) -> Dict[str, str]:
        """Get preview content from L2 reports."""
        previews = {}

        for path in report_paths:
            try:
                with open(path, 'r') as f:
                    content = f.read(500)  # First 500 chars
                previews[path] = content
            except Exception:
                continue

        return previews

    def _extract_plan_summary(self, plan_content: str) -> str:
        """Extract summary section from plan content."""
        if not plan_content:
            return "(No plan content)"

        lines = plan_content.split('\n')
        summary_lines = []
        in_overview = False
        in_tasks = False

        for line in lines:
            # Capture title
            if line.startswith('# '):
                summary_lines.append(line)
                continue

            # Capture Overview section
            if line.startswith('## Overview'):
                in_overview = True
                continue
            elif line.startswith('## ') and in_overview:
                in_overview = False
            elif in_overview:
                summary_lines.append(line)

            # Capture Tasks section (first few lines)
            if line.startswith('## Tasks'):
                in_tasks = True
                continue
            elif line.startswith('## ') and in_tasks:
                in_tasks = False
            elif in_tasks and len(summary_lines) < 20:
                summary_lines.append(line)

        return '\n'.join(summary_lines[:20]) or plan_content[:500]


# =============================================================================
# Convenience Functions
# =============================================================================

_manager: Optional[AutoCompactRecoveryManager] = None


def get_recovery_manager() -> AutoCompactRecoveryManager:
    """Get or create session-wide recovery manager."""
    global _manager
    if _manager is None:
        _manager = AutoCompactRecoveryManager()
    return _manager


def check_recovery_needed(user_message: str = "") -> bool:
    """Quick check if recovery is needed."""
    return get_recovery_manager().detect_recovery_needed(user_message)


def get_recovery_prompt() -> str:
    """Quick function to get recovery prompt."""
    manager = get_recovery_manager()
    state = manager.collect_recovery_state()
    return manager.generate_recovery_prompt(state)


def inject_l2_for_agents(agent_ids: List[str]) -> Dict[str, str]:
    """Quick function to inject L2 content."""
    return get_recovery_manager().inject_l2_content(agent_ids)
