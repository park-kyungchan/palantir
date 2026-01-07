from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from scripts.ontology.actions import ActionType, ActionContext, ActionMetadata, register_action, EditOperation
from scripts.ontology.ontology_types import OntologyObject
from scripts.aip_logic.engine import LogicEngine
from scripts.aip_logic.registry import get_logic_function
from scripts.llm.instructor_client import InstructorClient

logger = logging.getLogger(__name__)

# Note: We need a mechanism to define/load LogicFunctions.
# For now, we allow executing dynamic prompts essentially via a Generic Logic Function?
# Or we just provide the connection point.

@register_action(requires_proposal=False)
class ExecuteLogicAction(ActionType):
    """
    Executes a LogicFunction via the AIP Logic Engine.
    Used for cognitive tasks that need audit logging and governance.
    """
    api_name = "execute_logic"
    object_type = None # No specific ontology object mutation directly (result is data)
    
    def __init__(self):
        self.client = InstructorClient()
        self.engine = LogicEngine(self.client)

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Dict[str, Any], List[EditOperation]]:
        """
        Params:
            function_name: str (e.g., "AnalyzeCode")
            input_data: Dict (Input payload)
        """
        function_name = params.get("function_name")
        input_data = params.get("input_data", {})
        
        if not function_name:
            raise ValueError("function_name is required")

        logger.info(f"[ExecuteLogicAction] Requesting {function_name} execution.")

        function_cls = get_logic_function(function_name)
        input_model = function_cls.input_type.model_validate(input_data)
        result = await self.engine.execute(function_cls, input_model)

        # Logic execution doesn't inherently mutate ontology unless the function *returns* edits.
        # We return the output model for auditability.
        return result, []

# Register explicitly if decorator didn't work (imports etc)
# action_registry.register(ExecuteLogicAction)
