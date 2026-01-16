"""
Orion ODA V3 - Tool Marshaler
=============================
Provides a secure marshaling layer for executing Actions.

- Validates Inputs (Schema Enforcement)
- Captures Outputs (Standardized Result)
- Handles Exceptions (Graceful Failure)
- Audits Execution (Telemetry)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Type

from lib.oda.ontology.actions import (
    ActionContext,
    ActionType,
    ActionResult,
    action_registry,
)

logger = logging.getLogger(__name__)

class ToolMarshaler:
    """
    Secure executor for Ontology Actions.
    Marshals inputs/outputs and ensures consistent execution context.
    """
    
    def __init__(self, registry=action_registry):
        self.registry = registry

    async def execute_action(
        self, 
        action_name: str, 
        params: Dict[str, Any], 
        context: ActionContext
    ) -> ActionResult:
        """
        Execute an action by name with given parameters.
        
        Args:
            action_name: API name of the action (e.g. "deploy_service")
            params: Dictionary of parameters
            context: Execution context (actor, timestamp)
            
        Returns:
            ActionResult object containing success status and edits/errors.
        """
        start = time.perf_counter()
        logger.info(f"Marshaling execution for action: {action_name}")

        audit_status = "FAILURE"
        audit_error: str | None = None
        audit_affected: list[str] = []

        def _jsonable(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, dict):
                return {str(k): _jsonable(v) for k, v in value.items()}
            if isinstance(value, (list, tuple, set)):
                return [_jsonable(v) for v in value]
            if hasattr(value, "model_dump"):
                try:
                    return value.model_dump(mode="json")
                except TypeError:
                    return value.model_dump()
            return str(value)

        async def _best_effort_audit_log() -> None:
            try:
                from lib.oda.ontology.schemas.governance import OrionActionLog
                from lib.oda.ontology.storage.database import DatabaseManager
                from lib.oda.ontology.storage.repositories import ActionLogRepository

                db = DatabaseManager.get()
                repo = ActionLogRepository(db, publish_events=False)

                duration_ms = int((time.perf_counter() - start) * 1000)
                trace_id = context.correlation_id or context.metadata.get("trace_id")

                entry = OrionActionLog(
                    agent_id=context.actor_id or "Orion-Kernel",
                    trace_id=str(trace_id) if trace_id else None,
                    action_type=action_name,
                    parameters=_jsonable(params) if isinstance(params, dict) else {"params": _jsonable(params)},
                    status=audit_status,
                    error=audit_error,
                    affected_ids=audit_affected,
                    duration_ms=duration_ms,
                )
                await repo.save(entry, actor_id=context.actor_id or "system")
            except Exception as e:
                logger.debug(f"Audit log skipped: {e}")

        # 0. Context Integrity Check
        if not context or not context.actor_id:
            msg = "Invalid ActionContext: Missing actor_id"
            logger.error(msg)
            result = ActionResult(
                action_type=action_name,
                success=False,
                error=msg,
                error_details={"code": "INVALID_CONTEXT"}
            )
            audit_status = "FAILURE"
            audit_error = msg
            await _best_effort_audit_log()
            return result
        
        # 1. Lookup Action
        action_cls: Type[ActionType] = self.registry.get(action_name)
        if not action_cls:
            error_msg = f"Action '{action_name}' not found in registry."
            logger.error(error_msg)
            result = ActionResult(
                action_type=action_name,
                success=False,
                error=error_msg,
                error_details={"code": "ACTION_NOT_FOUND"}
            )
            audit_status = "FAILURE"
            audit_error = error_msg
            await _best_effort_audit_log()
            return result
            
        # 2. Instantiate (Stateless)
        try:
            action_instance = action_cls()
        except Exception as e:
            logger.exception(f"Failed to instantiate action {action_name}")
            result = ActionResult(
                action_type=action_name,
                success=False,
                error=f"Instantiation failed: {e}",
                error_details={"exception": str(e)}
            )
            audit_status = "FAILURE"
            audit_error = result.error
            await _best_effort_audit_log()
            return result

        # 3. Execute (Delegates to ActionType.execute which handles validation/side-effects)
        try:
            result = await action_instance.execute(params, context)
            
            if result.success:
                logger.info(f"Action {action_name} succeeded.")
                audit_status = "SUCCESS"
            else:
                logger.warning(f"Action {action_name} failed: {result.error}")
                audit_status = "FAILURE"
                audit_error = result.error

            audit_affected = list(
                dict.fromkeys(
                    [*(result.created_ids or []), *(result.modified_ids or []), *(result.deleted_ids or [])]
                )
            )
            await _best_effort_audit_log()
                
            return result
            
        except Exception as e:
            # Catch-all for unhandled exceptions during execution wrapper
            logger.exception(f"Unhandled error during action {action_name} execution")
            result = ActionResult(
                action_type=action_name,
                success=False,
                error=f"System Error: {e}",
                error_details={"exception": str(e)}
            )
            audit_status = "FAILURE"
            audit_error = result.error
            await _best_effort_audit_log()
            return result
