
from typing import Callable, Any, Dict, List
from pydantic import BaseModel

class SubmissionCriteria(BaseModel):
    """
    Validation Rule that must pass before Action execution.
    """
    description: str
    validator: Callable[[Any], bool]

class Function(BaseModel):
    """
    Logic: A pure function (or Side-Effect free calculation).
    """
    name: str
    logic: Callable

class ActionType(BaseModel):
    """
    Represents an actionable change in the Ontology.
    Includes: Parameters, Logic, Validation, SideEffects.
    """
    api_name: str
    display_name: str
    parameters: Dict[str, Any] # Name -> Type
    submission_criteria: List[SubmissionCriteria] = []
    
    def validate(self, **kwargs) -> bool:
        """
        Runs all SubmissionCriteria.
        """
        for criteria in self.submission_criteria:
            if not criteria.validator(kwargs):
                print(f"[Validation Failed] {criteria.description}")
                return False
        return True

    def execute(self, **kwargs):
        """
        Conceptual Execution Stub.
        """
        if self.validate(**kwargs):
            self._perform_side_effects(**kwargs)
            print(f"[Action] {self.display_name} Executed Successfully.")
        else:
            raise ValueError("Submission Criteria Failed")

    def _perform_side_effects(self, **kwargs):
        pass # To be overridden
