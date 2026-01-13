from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class ActionDefinition(BaseModel):
    """
    Represents a single Action defined in the HWP Manual.
    Derived from the 'ActionTable' PDF.
    """
    action_id: str = Field(..., description="The API Action ID (e.g. 'InsertText')")
    parameter_set_id: Optional[str] = Field(None, description="Required ParameterSet ID (e.g. 'CharShape')")
    description_ko: Optional[str] = Field(None, description="Korean description")
    requires_creation: bool = Field(False, description="If True, requires CreateAction")
    run_blocked: bool = Field(False, description="If True, cannot be run directly via Run()")

class ActionDatabase(BaseModel):
    """
    The Full Knowledge Base of HWP Actions.
    """
    actions: Dict[str, ActionDefinition] = Field(default_factory=dict)
    
    def add_action(self, action: ActionDefinition):
        self.actions[action.action_id] = action

    def get_parameter_set(self, action_id: str) -> Optional[str]:
        action = self.actions.get(action_id)
        if action:
            return action.parameter_set_id
        return None
