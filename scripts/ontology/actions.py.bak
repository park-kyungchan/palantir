
from typing import Callable, Any, Dict, List
from pydantic import BaseModel
from scripts.ontology.side_effects import SideEffect

class SubmissionCriteria(BaseModel):
    description: str
    validator: Callable[[Any], bool]

class Function(BaseModel):
    name: str
    logic: Callable

class ActionType(BaseModel):
    """
    Represents an actionable change in the Ontology.
    Includes: Parameters, Logic, Validation, SideEffects.
    """
    api_name: str
    display_name: str
    parameters: Dict[str, Any]
    submission_criteria: List[SubmissionCriteria] = []
    side_effects: List[SideEffect] = []
    
    class Config:
        arbitrary_types_allowed = True

    def validate(self, **kwargs) -> bool:
        for criteria in self.submission_criteria:
            if not criteria.validator(kwargs):
                print(f"[Validation Failed] {criteria.description}")
                return False
        return True

    def execute(self, **kwargs):
        # 1. Validation
        if not self.validate(**kwargs):
            raise ValueError(f"Submission Criteria Failed for {self.display_name}")

        # 2. Apply Edits (Ontology Layer)
        self._apply_edits(**kwargs)

        # 3. Side Effects (External Layer)
        for effect in self.side_effects:
            effect.execute(kwargs)
            
        print(f"[Action] {self.display_name} Executed Successfully.")

    def _apply_edits(self, **kwargs):
        print(f"[Ontology] Applied edits for {self.api_name}")
