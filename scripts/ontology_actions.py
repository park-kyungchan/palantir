
import os
import json
from pydantic import BaseModel
from typing import List, Optional, Any
from scripts.governance import OrionAction, OntologyContext, UserFacingError
from scripts.ontology import Plan  # The generated model

class PersistPlanParams(BaseModel):
    plan: Plan
    is_new: bool = False

class PersistPlanAction(OrionAction[PersistPlanParams]):
    action_type = "persist_plan"

    def validate(self, ctx: OntologyContext) -> None:
        # Rule 1.2: Determinism & Validity
        if not self.params.plan.plan_id:
            raise UserFacingError("Plan ID is required", "InvalidPlan")
        
        # In a real system, we'd check if the user has permission to create plans
        # or if the plan ID conflicts with an existing one (if is_new=True)

    def _apply_side_effects(self, ctx: OntologyContext) -> dict:
        # Define the physical path (The "Backing Dataset")
        plans_dir = os.path.join(ctx.workspace_root, ".agent", "plans")
        os.makedirs(plans_dir, exist_ok=True)
        
        file_path = os.path.join(plans_dir, f"plan_{self.params.plan.plan_id}.json")
        
        # Serialize
        data = self.params.plan.model_dump_json(indent=2)
        
        # Write (The Mutation)
        with open(file_path, 'w') as f:
            f.write(data)
            
        return {"path": file_path, "bytes": len(data)}
