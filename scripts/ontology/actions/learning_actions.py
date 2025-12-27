from typing import Any, Dict, Optional
from scripts.ontology.actions import ActionType, ActionContext, ActionResult, SubmissionCriterion, RequiredField
from scripts.ontology.objects.learning import Learner
from scripts.ontology.storage.learner_repository import LearnerRepository
from scripts.ontology.storage import get_database

class SaveLearnerStateAction(ActionType):
    """
    Action to persist Learner State/Knowledge.
    """
    api_name = "learning.save_state"
    submission_criteria = [
        RequiredField("user_id"),
        RequiredField("theta")
    ]

    async def apply_edits(self, params: Dict[str, Any], context: ActionContext) -> ActionResult:
        user_id = params["user_id"]
        
        learner = Learner(
            user_id=user_id,
            theta=params.get("theta", 0.0),
            knowledge_state=params.get("knowledge_state", {}),
            last_active=params.get("last_active", "")
        )
        # ID might be assigned by repo if new, or passed if existing?
        # LearnerRepository handles lookup by user_id, so we don't strictly need ID in params for update.
        
        session = context.metadata.get("session")
        
        repo = LearnerRepository(get_database())
        saved_learner = await repo.save(learner, session=session)
        
        return ActionResult(
             action_type=self.api_name,
             success=True,
             created_ids=[saved_learner.id] if saved_learner.id else [],
             modified_ids=[saved_learner.id] if saved_learner.id else [],
             message=f"Learner state for {user_id} saved."
        )
