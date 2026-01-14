"""
Planning Pre-Hook: Enforces /01_plan execution before major tasks.
Part of Mandatory Planning Protocol (v1.0).

V3.1: User-Level Integration
- Supports both User-Level and Project-Level paths
- Loads Kernel v5.0 rules from ~/.agent/rules/kernel_v5/
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger("PlanningHook")

# User-Level paths (primary) - applies to all projects
USER_LEVEL_AGENT = Path.home() / ".agent"
USER_LEVEL_PLANS = USER_LEVEL_AGENT / "plans"
USER_LEVEL_RULES = USER_LEVEL_AGENT / "rules"
KERNEL_V5_RULES = USER_LEVEL_RULES / "kernel_v5"

# Project-Level paths (fallback)
PROJECT_LEVEL_AGENT = Path("/home/palantir/park-kyungchan/palantir/.agent")

# Use User-Level as primary
PLANS_DIR = USER_LEVEL_PLANS
PLAN_VALIDITY_HOURS = 24  # Plans are valid for 24 hours


@dataclass
class PlanningGateResult:
    """Result of planning gate check."""
    passed: bool
    reason: str
    active_plan: Optional[str] = None
    requires_planning: bool = False


def is_simple_task(intent: str) -> bool:
    """
    Determine if a task is simple enough to skip /01_plan.
    
    Simple tasks:
    - Questions (starts with "what", "how", "why", etc.)
    - Single file edits explicitly mentioned
    - Status checks
    """
    simple_patterns = [
        "what is", "what are", "how do", "how does", "why is", "why does",
        "explain", "describe", "list", "show", "status", "check",
        "find", "search", "grep", "where is",
    ]
    intent_lower = intent.lower().strip()
    return any(intent_lower.startswith(p) for p in simple_patterns)


def is_complex_task(intent: str) -> bool:
    """
    Determine if a task requires /01_plan.
    
    Complex tasks:
    - Multi-file changes
    - Feature implementation
    - Architecture modifications
    - Refactoring
    """
    complex_patterns = [
        "implement", "create", "build", "add feature", "refactor",
        "migrate", "upgrade", "integrate", "setup", "configure",
        "modify", "change", "update", "fix bug", "enhance",
        "전체", "기능", "구현", "리팩토링", "마이그레이션",
    ]
    intent_lower = intent.lower()
    return any(p in intent_lower for p in complex_patterns)


def get_active_plan() -> Optional[Dict[str, Any]]:
    """
    Get the most recent valid plan.
    
    Returns:
        Plan dict if valid plan exists, None otherwise.
    """
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    
    plan_files = list(PLANS_DIR.glob("plan_*.json"))
    if not plan_files:
        return None
    
    # Get most recent plan
    latest_plan = max(plan_files, key=lambda p: p.stat().st_mtime)
    
    # Check validity (24 hours)
    plan_age = datetime.now() - datetime.fromtimestamp(latest_plan.stat().st_mtime)
    if plan_age > timedelta(hours=PLAN_VALIDITY_HOURS):
        logger.info(f"Plan {latest_plan.name} expired ({plan_age} old)")
        return None
    
    try:
        return json.loads(latest_plan.read_text())
    except (json.JSONDecodeError, IOError):
        return None


def check_planning_gate(intent: str, force_plan: bool = False) -> PlanningGateResult:
    """
    Check if task can proceed based on planning requirements.
    
    Args:
        intent: User's task description/intent
        force_plan: If True, always require a plan
    
    Returns:
        PlanningGateResult indicating if task can proceed
    """
    # Simple tasks bypass planning
    if not force_plan and is_simple_task(intent):
        return PlanningGateResult(
            passed=True,
            reason="Simple task - planning not required",
            requires_planning=False,
        )
    
    # Check if complex task
    needs_plan = force_plan or is_complex_task(intent)
    
    if not needs_plan:
        return PlanningGateResult(
            passed=True,
            reason="Task type does not require formal planning",
            requires_planning=False,
        )
    
    # Complex task - check for active plan
    active_plan = get_active_plan()
    
    if active_plan:
        return PlanningGateResult(
            passed=True,
            reason="Valid active plan exists",
            active_plan=active_plan.get("id"),
            requires_planning=False,
        )
    
    # No valid plan - BLOCK and require /01_plan
    return PlanningGateResult(
        passed=False,
        reason="Complex task requires /01_plan execution first",
        requires_planning=True,
    )


def create_quick_plan(intent: str, actor_id: str = "kernel") -> Dict[str, Any]:
    """
    Create a minimal plan for tracking purposes.
    Called when /01_plan workflow starts.
    """
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    
    plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    plan = {
        "id": plan_id,
        "intent": intent[:500],
        "created_at": datetime.now().isoformat(),
        "created_by": actor_id,
        "status": "active",
        "phases": [],
    }
    
    plan_path = PLANS_DIR / f"{plan_id}.json"
    plan_path.write_text(json.dumps(plan, indent=2))
    
    logger.info(f"Created plan: {plan_id}")
    return plan


# Kernel integration hook
async def pre_execute_hook(
    action_name: str,
    params: Dict[str, Any],
    intent: Optional[str] = None
) -> PlanningGateResult:
    """
    Pre-execution hook for Kernel.
    
    Called before any action execution to enforce planning gate.
    """
    # Some actions bypass planning
    bypass_actions = [
        "list_workflows", "list_",  # Query operations
        "execute_workflow",  # Already going through workflow
        "save_memory", "sync_memory",  # Memory operations
    ]
    
    if any(action_name.startswith(b) for b in bypass_actions):
        return PlanningGateResult(passed=True, reason="Action type bypasses planning")
    
    # Use intent from params if not provided
    if not intent:
        intent = params.get("intent", params.get("description", str(params)[:100]))
    
    return check_planning_gate(intent)
