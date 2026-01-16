from __future__ import annotations

from typing import Any, Dict, List, TypeVar
from scripts.ontology.ontology_types import OntologyObject
from scripts.ontology.actions import ActionType, ActionResult, ActionContext

T = TypeVar("T", bound=OntologyObject)


class ActionClient:
    """
    Client for executing Ontology Actions.
    Provides type-safe execution and validation wrapper.
    """

    def __init__(self, actor_id: str = "osdk_client"):
        self.default_actor_id = actor_id

    def validate(self, action: ActionType[T], params: Dict[str, Any], actor_id: str = None) -> List[str]:
        """
        Validate parameters against the action's constraints without executing.
        """
        context = ActionContext(actor_id=actor_id or self.default_actor_id)
        return action.validate(params, context)

    async def apply(self, action: ActionType[T], params: Dict[str, Any], actor_id: str = None) -> ActionResult:
        """
        Execute an action.
        
        Args:
            action: The ActionType instance to execute
            params: Dictionary of parameters matching submission criteria
            actor_id: Optional overide for actor ID
            
        Returns:
            ActionResult object containing success status and edits
        """
        context = ActionContext(actor_id=actor_id or self.default_actor_id)
        
        # Determine execution policy (Simple check for now, can be expanded to check GovernanceEngine)
        # Note: In a full implementation, we might check with GovernanceEngine here explicitly.
        # But ActionType.execute() handles validation logic internally too.
        
        return await action.execute(params, context)
