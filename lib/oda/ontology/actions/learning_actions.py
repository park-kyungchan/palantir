from typing import Any, Dict, Optional
from lib.oda.ontology.actions import (
    ActionType,
    ActionContext,
    ActionResult,
    RequiredField,
    register_action,
)
from lib.oda.ontology.objects.learning import Learner
from lib.oda.ontology.storage.learner_repository import LearnerRepository
from lib.oda.ontology.storage.database import DatabaseManager

@register_action
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

        # V3.1: Use DatabaseManager instead of deprecated get_database()
        repo = LearnerRepository(DatabaseManager.get())

        existing = await repo.get_by_user_id(user_id)
        version_param = params.get("version")
        if version_param is None:
            next_version = (existing.version + 1) if existing else 1
        else:
            next_version = int(version_param)

        learner = Learner(
            user_id=user_id,
            theta=params.get("theta", 0.0),
            knowledge_state=params.get("knowledge_state", {}),
            last_active=params.get("last_active", ""),
            version=next_version,  # OCC: repo expects DB version + 1 for updates
        )

        saved_learner = await repo.save(learner, actor_id=context.actor_id)

        created_ids = [saved_learner.id] if (existing is None and saved_learner.id) else []
        modified_ids = [saved_learner.id] if (existing is not None and saved_learner.id) else []

        return ActionResult(
             action_type=self.api_name,
             success=True,
             created_ids=created_ids,
             modified_ids=modified_ids,
             message=f"Learner state for {user_id} saved."
        )
