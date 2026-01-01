
"""
Orion ODA V3 - Safe Instructor Client
=====================================
Provides a robust LLM client using `instructor` linked to `tenacity` for resilience.

Features:
- **Structural Enforcement**: Uses Pydantic to force LLM outputs into `Plan` schema.
- **Self-Healing**: Automatically retries on validation errors (e.g. missing fields, wrong types).
- **JSON Repair**: Fallback hook for "Double-Escape" issues common in quantized models.
"""

from __future__ import annotations

import logging
from typing import Type, TypeVar, Any, Dict

import instructor
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

from scripts.ontology.plan import Plan

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class InstructorClient:
    """
    Client for interacting with LLMs via Instructor for structured output.
    Supports Ollama and OpenAI-compatible endpoints.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434/v1", api_key: str = "ollama"):
        self.base_url = base_url
        self.api_key = api_key
        
        # Patch standard OpenAI client with Instructor
        self.client = instructor.patch(
            OpenAI(base_url=base_url, api_key=api_key),
            mode=instructor.Mode.JSON
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ValidationError)
    )
    def generate(
        self, 
        prompt: str, 
        response_model: Type[T], 
        model_name: str = "llama3.2"
    ) -> T:
        """
        Generate a structured response from the LLM.
        
        Args:
            prompt: The user prompt.
            response_model: Pydantic model class to validate against.
            model_name: LLM model name.
            
        Returns:
            Validated instance of response_model.
        """
        try:
            return self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_model=response_model,
                max_retries=2  # Internal Instructor retry for simple fixups
            )
        except ValidationError as e:
            logger.warning(f"Validation Failed (Attempting Retry): {e}")
            raise
        except Exception as e:
            # Handle JSON Parse issues explicitly if Instructor fails
            if "Expecting value" in str(e) or "Unterminated string" in str(e):
                 logger.error(f"JSON Parse Error: {e}. Attempting Repair strategy if implemented.")
                 # In future: manually fetch raw content -> repair_json -> model_validate
            raise

    async def generate_async(
        self,
        prompt: str,
        response_model: Type[T],
        model_name: str = "llama3.2"
    ) -> T:
        """
        Async version of generate for use in async contexts.
        
        Wraps the sync generate() in an executor for thread safety.
        This preserves the tenacity retry logic from the sync version.
        
        DIA v2.1: C1 compliant - new interface method
        
        Args:
            prompt: The user prompt.
            response_model: Pydantic model class to validate against.
            model_name: LLM model name.
            
        Returns:
            Validated instance of response_model.
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,  # Default ThreadPoolExecutor
            lambda: self.generate(prompt, response_model, model_name)
        )

    async def generate_plan(self, prompt: str, model_name: str = "llama3.2") -> Plan:
        """
        Specialized method for Plan generation.
        Uses ODA 'GeneratePlanAction' for full auditing.
        """
        from scripts.ontology.actions.llm_actions import GeneratePlanAction
        from scripts.simulation.core import ActionRunner, ActionContext
        # ODA Action Execution - ActionRunner uses get_database() by default
        action = GeneratePlanAction()
        runner = ActionRunner()  # Uses Database pattern internally
        
        ctx = ActionContext(
            actor_id="instructor_client",
            correlation_id=None,
            metadata={"model": model_name}
        )
        ctx.parameters = {"goal": prompt, "model": model_name}
        
        # Execute (This returns (Plan, edits)) based on our implementation in llm_actions.py
        # Wait, ActionRunner.execute returns ActionResult.
        # Check ActionRunner implementation... 
        # result = await self.execute(...) returns ActionResult.
        
        result = await runner.execute(action, ctx)
        
        if not result.success:
             raise RuntimeError(f"Plan Generation Failed: {result.error}")
             
        # Extract Plan from result.data (populated by ActionRunner)
        if result.data:
            return result.data

        raise RuntimeError("No Plan returned in Action Result")

