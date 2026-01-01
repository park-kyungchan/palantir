"""
Orion ODA V3 - Plan Orchestrator
=================================
Executes multi-action plans with Saga pattern.

P-04: Orchestrator with automatic compensation on failure.

ODA Alignment:
    - Uses ToolMarshaler for action execution
    - ActionContext for each step
    - Proposal integration for hazardous actions

Usage:
    orchestrator = PlanOrchestrator(marshaler)
    result = await orchestrator.execute(plan)
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from scripts.ontology.plans.models import (
    MultiActionPlan,
    PlanResult,
    PlanStatus,
    PlanStep,
    StepStatus,
)

logger = logging.getLogger(__name__)


class PlanOrchestrator:
    """
    Orchestrator for executing multi-action plans.
    
    Implements the Saga pattern:
        1. Execute steps in order
        2. On failure, compensate completed steps in reverse order
    
    ODA Integration:
        - Each step is executed via ToolMarshaler
        - Hazardous actions create Proposals automatically
        - OCC is handled per-step
    
    Usage:
        orchestrator = PlanOrchestrator()
        result = await orchestrator.execute(plan)
    """
    
    def __init__(self, marshaler=None):
        self._marshaler = marshaler
    
    @property
    def marshaler(self):
        """Lazy-load ToolMarshaler."""
        if self._marshaler is None:
            try:
                from scripts.runtime.marshaler import ToolMarshaler
                self._marshaler = ToolMarshaler()
            except ImportError:
                logger.warning("ToolMarshaler not available")
        return self._marshaler
    
    async def execute(
        self,
        plan: MultiActionPlan,
        actor_id: str = "system",
    ) -> PlanResult:
        """
        Execute a multi-action plan.
        
        Args:
            plan: The plan to execute
            actor_id: Actor performing the plan
            
        Returns:
            PlanResult with execution status
        """
        start_time = time.time()
        completed_steps: List[PlanStep] = []
        
        logger.info(f"▶️ Executing plan: {plan.name} ({len(plan.steps)} steps)")
        
        plan.status = PlanStatus.RUNNING
        plan.started_at = datetime.utcnow()
        
        try:
            # Execute steps in order
            for i, step in enumerate(plan.steps):
                plan.current_step_index = i
                
                # Check dependencies
                if not self._check_dependencies(step, completed_steps):
                    step.status = StepStatus.SKIPPED
                    logger.warning(f"⏭️ Skipped step {step.id}: unmet dependencies")
                    continue
                
                # Execute step
                success = await self._execute_step(step, plan.context, actor_id)
                
                if success:
                    completed_steps.append(step)
                    # Merge step result into plan context
                    if isinstance(step.result, dict):
                        plan.context.update(step.result)
                else:
                    # Step failed - compensate
                    logger.error(f"❌ Step {step.id} failed: {step.error}")
                    await self._compensate(completed_steps, plan.context, actor_id)
                    
                    plan.status = PlanStatus.COMPENSATED
                    plan.completed_at = datetime.utcnow()
                    
                    return PlanResult(
                        plan_id=plan.id,
                        status=plan.status,
                        steps_completed=len(completed_steps),
                        steps_total=len(plan.steps),
                        steps_failed=1,
                        steps_compensated=len(completed_steps),
                        duration_ms=(time.time() - start_time) * 1000,
                        error=step.error,
                        context=plan.context,
                    )
            
            # All steps completed
            plan.status = PlanStatus.COMPLETED
            plan.completed_at = datetime.utcnow()
            
            logger.info(f"✅ Plan completed: {plan.name}")
            
            return PlanResult(
                plan_id=plan.id,
                status=plan.status,
                steps_completed=len(completed_steps),
                steps_total=len(plan.steps),
                steps_failed=0,
                steps_compensated=0,
                duration_ms=(time.time() - start_time) * 1000,
                context=plan.context,
            )
            
        except Exception as e:
            logger.error(f"💥 Plan execution error: {e}")
            
            # Compensate on unexpected error
            await self._compensate(completed_steps, plan.context, actor_id)
            
            plan.status = PlanStatus.FAILED
            plan.completed_at = datetime.utcnow()
            
            return PlanResult(
                plan_id=plan.id,
                status=plan.status,
                steps_completed=len(completed_steps),
                steps_total=len(plan.steps),
                steps_failed=1,
                steps_compensated=len(completed_steps),
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e),
                context=plan.context,
            )
    
    async def _execute_step(
        self,
        step: PlanStep,
        context: Dict[str, Any],
        actor_id: str,
    ) -> bool:
        """Execute a single step."""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()
        
        logger.info(f"⚡ Executing step: {step.action_type}")
        
        try:
            # Merge context into params
            merged_params = {**context, **step.params}
            
            if self.marshaler:
                # Use ToolMarshaler for ODA-compliant execution
                from scripts.ontology.actions import ActionContext
                
                result = await self.marshaler.execute(
                    api_name=step.action_type,
                    params=merged_params,
                    context=ActionContext(actor_id=actor_id),
                )
                step.result = result
            else:
                # Simulated execution
                logger.debug(f"Simulated: {step.action_type}")
                step.result = {"simulated": True}
            
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.utcnow()
            
            logger.info(f"✅ Step completed: {step.action_type}")
            return True
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.utcnow()
            return False
    
    async def _compensate(
        self,
        completed_steps: List[PlanStep],
        context: Dict[str, Any],
        actor_id: str,
    ) -> None:
        """
        Compensate completed steps in reverse order.
        
        Saga pattern: rollback by executing compensation actions.
        """
        if not completed_steps:
            return
        
        logger.info(f"🔄 Compensating {len(completed_steps)} steps...")
        
        # Reverse order
        for step in reversed(completed_steps):
            if not step.compensation_action:
                logger.debug(f"No compensation for: {step.action_type}")
                continue
            
            try:
                merged_params = {**context, **step.compensation_params}
                
                if self.marshaler:
                    from scripts.ontology.actions import ActionContext
                    
                    await self.marshaler.execute(
                        api_name=step.compensation_action,
                        params=merged_params,
                        context=ActionContext(actor_id=actor_id),
                    )
                else:
                    logger.debug(f"Simulated compensation: {step.compensation_action}")
                
                step.status = StepStatus.COMPENSATED
                logger.info(f"↩️ Compensated: {step.action_type}")
                
            except Exception as e:
                logger.error(f"Compensation failed for {step.action_type}: {e}")
        
        logger.info("✅ Compensation complete")
    
    def _check_dependencies(
        self,
        step: PlanStep,
        completed_steps: List[PlanStep],
    ) -> bool:
        """Check if step dependencies are satisfied."""
        if not step.depends_on:
            return True
        
        completed_ids = {s.id for s in completed_steps}
        return all(dep in completed_ids for dep in step.depends_on)
    
    @staticmethod
    def create_plan(
        name: str,
        description: str = "",
        steps: List[Dict[str, Any]] = None,
    ) -> MultiActionPlan:
        """
        Factory method to create a plan.
        
        Usage:
            plan = PlanOrchestrator.create_plan(
                name="order_saga",
                steps=[
                    {"action": "inventory.reserve", "params": {...}},
                    {"action": "payment.charge", "params": {...}},
                ]
            )
        """
        plan = MultiActionPlan(name=name, description=description)
        
        for step_def in (steps or []):
            plan.add_step(
                action_type=step_def.get("action", ""),
                params=step_def.get("params", {}),
                compensation_action=step_def.get("compensation"),
                compensation_params=step_def.get("compensation_params", {}),
            )
        
        return plan
