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
from typing import Any, Dict, Type

from scripts.ontology.actions import (
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
        logger.info(f"Marshaling execution for action: {action_name}")
        
        # 0. Context Integrity Check
        if not context or not context.actor_id:
            msg = "Invalid ActionContext: Missing actor_id"
            logger.error(msg)
            return ActionResult(
                action_type=action_name,
                success=False,
                error=msg,
                error_details={"code": "INVALID_CONTEXT"}
            )
        
        # 1. Lookup Action
        action_cls: Type[ActionType] = self.registry.get(action_name)
        if not action_cls:
            error_msg = f"Action '{action_name}' not found in registry."
            logger.error(error_msg)
            return ActionResult(
                action_type=action_name,
                success=False,
                error=error_msg,
                error_details={"code": "ACTION_NOT_FOUND"}
            )
            
        # 2. Instantiate (Stateless)
        try:
            action_instance = action_cls()
        except Exception as e:
            logger.exception(f"Failed to instantiate action {action_name}")
            return ActionResult(
                action_type=action_name,
                success=False,
                error=f"Instantiation failed: {e}",
                error_details={"exception": str(e)}
            )

        # 3. Execute (Delegates to ActionType.execute which handles validation/side-effects)
        try:
            result = await action_instance.execute(params, context)
            
            if result.success:
                logger.info(f"Action {action_name} succeeded.")
            else:
                logger.warning(f"Action {action_name} failed: {result.error}")
                
            return result
            
        except Exception as e:
            # Catch-all for unhandled exceptions during execution wrapper
            logger.exception(f"Unhandled error during action {action_name} execution")
            return ActionResult(
                action_type=action_name,
                success=False,
                error=f"System Error: {e}",
                error_details={"exception": str(e)}
            )
