"""
Orion ODA V3 - Multi-Action Plan Models
========================================
Saga pattern data structures for multi-step operations.

P-04: Multi-Action Plans with compensation support.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PlanStatus(str, Enum):
    """Multi-action plan execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


class StepStatus(str, Enum):
    """Individual step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """
    Represents a single step in a multi-action plan.
    
    ODA Alignment:
        - action_type: Maps to ActionType.api_name
        - params: Maps to action parameters
        - compensation_action: Rollback action if step fails
    
    Usage:
        step = PlanStep(
            action_type="order.create",
            params={"product_id": "123"},
            compensation_action="order.cancel",
            compensation_params={"reason": "Saga rollback"},
        )
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_type: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    compensation_action: Optional[str] = None
    compensation_params: Dict[str, Any] = field(default_factory=dict)
    
    # Execution state
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Ordering
    order: int = 0
    depends_on: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type,
            "params": self.params,
            "compensation_action": self.compensation_action,
            "compensation_params": self.compensation_params,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "order": self.order,
            "depends_on": self.depends_on,
        }


@dataclass
class MultiActionPlan:
    """
    Multi-step action plan with Saga pattern support.
    
    ODA Alignment:
        - Extends Proposal concept for multi-step operations
        - Each step maps to an ActionType execution
        - Automatic rollback on failure (compensation)
    
    Usage:
        plan = MultiActionPlan(
            name="create_order_saga",
            steps=[
                PlanStep(action_type="inventory.reserve", ...),
                PlanStep(action_type="payment.process", ...),
                PlanStep(action_type="order.confirm", ...),
            ]
        )
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    
    # Execution state
    status: PlanStatus = PlanStatus.PENDING
    current_step_index: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Context shared across steps
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Actor tracking
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_step(
        self,
        action_type: str,
        params: Dict[str, Any] = None,
        compensation_action: str = None,
        compensation_params: Dict[str, Any] = None,
    ) -> PlanStep:
        """Add a step to the plan."""
        step = PlanStep(
            action_type=action_type,
            params=params or {},
            compensation_action=compensation_action,
            compensation_params=compensation_params or {},
            order=len(self.steps),
        )
        self.steps.append(step)
        return step
    
    def get_completed_steps(self) -> List[PlanStep]:
        """Get all completed steps (for compensation)."""
        return [
            s for s in self.steps
            if s.status == StepStatus.COMPLETED
        ]
    
    def get_pending_steps(self) -> List[PlanStep]:
        """Get all pending steps."""
        return [
            s for s in self.steps
            if s.status == StepStatus.PENDING
        ]
    
    @property
    def is_complete(self) -> bool:
        return self.status in [PlanStatus.COMPLETED, PlanStatus.FAILED, PlanStatus.COMPENSATED]
    
    @property
    def success_rate(self) -> float:
        if not self.steps:
            return 0.0
        completed = len(self.get_completed_steps())
        return completed / len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "context": self.context,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class PlanResult:
    """Result of a multi-action plan execution."""
    
    plan_id: str
    status: PlanStatus
    steps_completed: int
    steps_total: int
    steps_failed: int
    steps_compensated: int
    duration_ms: float
    error: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        return self.status == PlanStatus.COMPLETED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "status": self.status.value,
            "success": self.success,
            "steps_completed": self.steps_completed,
            "steps_total": self.steps_total,
            "steps_failed": self.steps_failed,
            "steps_compensated": self.steps_compensated,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "context": self.context,
        }
