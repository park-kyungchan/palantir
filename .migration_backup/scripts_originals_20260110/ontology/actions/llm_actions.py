
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from lib.oda.ontology.actions import ActionType, ActionContext, ActionResult, SubmissionCriterion, RequiredField
from lib.oda.ontology.plan import Plan
from lib.oda.ontology.ontology_types import ObjectStatus
# We might need to import the InstructorClient for the implementation detail
# But to avoid circular imports, we might instantiate it inside apply_edits

logger = logging.getLogger(__name__)

class GeneratePlanAction(ActionType[Plan]):
    """
    Action to generate a Plan using an LLM.
    Audited and Governed.
    """
    api_name = "llm.generate_plan"
    submission_criteria = [
        RequiredField("goal")
    ]
    
    async def apply_edits(self, params: Dict[str, Any], context: ActionContext) -> ActionResult:
        """
        Uses Instructor to generate a Plan.
        """
        prompt = params["goal"]
        model = params.get("model", "gpt-4o") # Default to high intelligence
        
        # Lazy import to avoid circular dependency
        from lib.oda.llm.instructor_client import InstructorClient
        
        client = InstructorClient() # Use defaults or env vars
        
        try:
            # For strict compliance, let's call the low-level generate directly 
            # so we don't recurse if client uses Actions (which we plan to do).
            # We want THIS Action to be the source of truth.
            plan = await client.generate_async(prompt, Plan, model_name=model)
            
        except Exception as e:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=f"LLM Generation Failed: {e}"
            )

        # We don't necessarily "Save" the plan to DB here (PlanRepository).
        # But we DO record the generation in the Audit Log via this Action.
        
        # ODA Pattern: Action returns the object.
        # We can also return the JSON representation in 'changes'
        

        # Actually, Plan IS an Ontology Object.
        
        # If we want to persist the Plan, we should.
        # But commonly Plans are proposed first.
        # Let's return the Plan object.
        
        # Changes dict for audit
        changes = plan.model_dump(mode='json')
        
        # Construct ActionResult manually since ActionType.apply_edits signature returns (T, edits)
        # But wait, execute() wrapper creates ActionResult.
        # We need to return (T, [EditOperation]).
        
        from lib.oda.ontology.actions import EditOperation, EditType
        
        edit = EditOperation(
             edit_type=EditType.CREATE,
             object_type="Plan",
             object_id=plan.id,
             changes=changes
        )
        
        return plan, [edit]

class RouteTaskAction(ActionType):
    """
    Action to route a user request to a specific Agent or Tool.
    """
    api_name = "llm.route_task"
    submission_criteria = [
        RequiredField("request")
    ]
    
    async def apply_edits(self, params: Dict[str, Any], context: ActionContext) -> ActionResult:
        from lib.oda.llm.instructor_client import InstructorClient
        from pydantic import BaseModel, Field
        
        class RouterOutput(BaseModel):
            agent: str = Field(..., description="Target Agent (e.g. 'Planner', 'Coder', 'Researcher')")
            confidence: float = Field(..., ge=0, le=1)
            reasoning: str
        
        req = params["request"]
        model = params.get("model", "llama3.2")
        
        client = InstructorClient()
        route = await client.generate_async(
            f"Route this request: {req}",
            RouterOutput,
            model_name=model,
        )
        
        return route, [] # No ontology edits, just a decision

class ProcessLLMPromptAction(ActionType):
    """
    Generic audited LLM call.
    """
    api_name = "llm.process_prompt"
    submission_criteria = [RequiredField("prompt")]
    
    async def apply_edits(self, params: Dict[str, Any], context: ActionContext) -> ActionResult:
        # Generic Passthrough
        # This is hard because 'response_model' is a Type, hard to pass in params (JSON).
        # This action might just return raw text or dict.
        
        prompt = params["prompt"]
        model = params.get("model", "llama3.2")
        
        from lib.oda.llm.instructor_client import InstructorClient
        client = InstructorClient()
        
        # We assume generic dict output for "Process"
        # Or generic string?
        # Let's say we expect a 'Response' object.
        # For now, let's treat it as a Raw Completion wrapper.
        
        def _call_llm():
            response = client.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        content = await asyncio.to_thread(_call_llm)
        
        return content, []
