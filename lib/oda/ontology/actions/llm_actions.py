
import asyncio
import logging
import json
import os
from typing import Dict, Any, Optional, List
from lib.oda.ontology.actions import (
    ActionType,
    ActionContext,
    ActionResult,
    RequiredField,
    register_action,
)
from lib.oda.ontology.plan import Plan
from lib.oda.ontology.ontology_types import ObjectStatus
# We might need to import the InstructorClient for the implementation detail
# But to avoid circular imports, we might instantiate it inside apply_edits

logger = logging.getLogger(__name__)

@register_action
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
        Generate a Plan using either an LLM (Instructor) or a deterministic parser.
        """
        prompt = params["goal"]
        model = params.get("model")

        mode = os.environ.get("ORION_PLAN_MODE", "auto").strip().lower()
        if mode not in {"auto", "llm", "deterministic"}:
            mode = "auto"

        def _generate_deterministic() -> Plan:
            from lib.oda.planning.deterministic_planner import generate_deterministic_plan

            result = generate_deterministic_plan(prompt)
            return result.plan

        def _llm_configured() -> bool:
            from lib.oda.llm.config import load_llm_config

            cfg = load_llm_config()
            if cfg.requires_api_key and not cfg.api_key:
                return False
            if cfg.provider_type.value == "antigravity" and not cfg.base_url:
                return False
            return True

        plan: Plan
        if mode == "deterministic":
            plan = _generate_deterministic()
        else:
            llm_ready = _llm_configured()
            if not llm_ready and mode == "llm":
                return ActionResult(
                    action_type=self.api_name,
                    success=False,
                    error="LLM plan generation requested but LLM backend is not configured (missing base_url/api_key).",
                )

            if llm_ready:
                # Lazy import to avoid circular dependency
                from lib.oda.llm.instructor_client import InstructorClient

                client = InstructorClient()  # Use defaults or env vars
                try:
                    plan = await client.generate_async(prompt, Plan, model_name=model)
                except Exception as e:
                    if mode == "llm":
                        return ActionResult(
                            action_type=self.api_name,
                            success=False,
                            error=f"LLM Generation Failed: {e}",
                        )
                    plan = _generate_deterministic()
                    plan.research_context = {
                        **(plan.research_context or {}),
                        "llm_error_fallback": str(e),
                    }
            else:
                plan = _generate_deterministic()

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

@register_action
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
        model = params.get("model")
        
        client = InstructorClient()
        route = await client.generate_async(
            f"Route this request: {req}",
            RouterOutput,
            model_name=model,
        )
        
        return route, [] # No ontology edits, just a decision

@register_action
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
        model = params.get("model")
        
        from lib.oda.llm.instructor_client import InstructorClient
        client = InstructorClient()
        
        # We assume generic dict output for "Process"
        # Or generic string?
        # Let's say we expect a 'Response' object.
        # For now, let's treat it as a Raw Completion wrapper.
        
        def _call_llm():
            if client.client is None:
                raise RuntimeError(
                    "ProcessLLMPromptAction requires an OpenAI-compatible backend. "
                    "Set ORION_LLM_PROVIDER=antigravity|openai."
                )
            response = client.client.chat.completions.create(
                model=model or client.default_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        content = await asyncio.to_thread(_call_llm)
        
        return content, []
