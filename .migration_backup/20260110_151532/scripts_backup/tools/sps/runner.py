"""
Orion ODA V3 - Simple Prompt System (SPS) - Runner
===================================================
Prompt execution against LLM.

Maps to IndyDevDan's idt sps run command.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from scripts.tools.sps.prompts import Prompt, PromptManager

logger = logging.getLogger(__name__)


class PromptRunner:
    """
    Executes prompts against LLM.
    
    Maps to IndyDevDan's sps run command.
    
    Usage:
        runner = PromptRunner()
        result = await runner.run("greeting", {"name": "World"})
    """
    
    def __init__(
        self,
        manager: PromptManager = None,
        llm = None,
    ):
        self.manager = manager or PromptManager()
        self._llm = llm
    
    @property
    def llm(self):
        """Lazy-load InstructorClient."""
        if self._llm is None:
            try:
                from scripts.llm.instructor_client import InstructorClient
                self._llm = InstructorClient()
            except ImportError:
                logger.warning("InstructorClient not available")
        return self._llm
    
    async def run(
        self,
        prompt_name: str,
        variables: Dict[str, Any] = None,
        stream: bool = False,
    ) -> str:
        """
        Run a prompt by name.
        
        Args:
            prompt_name: Name of the prompt to run
            variables: Variables to substitute
            stream: Stream output to console
            
        Returns:
            LLM response string
        """
        prompt = self.manager.get(prompt_name)
        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_name}")
        
        # Check required variables
        variables = variables or {}
        missing = set(prompt.variables) - set(variables.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        # Render prompt
        rendered = prompt.render(**variables)
        
        logger.info(f"Running prompt: {prompt_name}")
        logger.debug(f"Rendered ({len(rendered)} chars):\n{rendered[:200]}...")
        
        # Execute against LLM
        if stream:
            return await self._run_streaming(rendered)
        else:
            return await self._run_sync(rendered)
    
    async def _run_sync(self, prompt: str) -> str:
        """Run prompt synchronously."""
        if self.llm is None:
            # Fallback: echo mode
            return f"[Echo Mode - LLM not configured]\n\n{prompt}"
        
        result = await self.llm.generate_text(prompt)
        return result
    
    async def _run_streaming(self, prompt: str) -> str:
        """Run prompt with streaming output."""
        if self.llm is None:
            print(f"[Echo Mode]\n{prompt}")
            return prompt
        
        full_response = ""
        
        async for chunk in self.llm.stream_text(prompt):
            print(chunk, end="", flush=True)
            full_response += chunk
        
        print()  # Newline at end
        return full_response
    
    async def run_inline(
        self,
        template: str,
        variables: Dict[str, Any] = None,
    ) -> str:
        """
        Run an inline prompt (not saved).
        
        Args:
            template: Prompt template string
            variables: Variables to substitute
        """
        prompt = Prompt(name="_inline", template=template)
        rendered = prompt.render(**(variables or {}))
        return await self._run_sync(rendered)
    
    async def run_batch(
        self,
        prompt_name: str,
        variable_sets: list[Dict[str, Any]],
        max_concurrent: int = 5,
    ) -> list[str]:
        """
        Run a prompt with multiple variable sets in parallel.
        
        Args:
            prompt_name: Name of the prompt
            variable_sets: List of variable dictionaries
            max_concurrent: Maximum concurrent executions
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_one(variables: Dict[str, Any]) -> str:
            async with semaphore:
                return await self.run(prompt_name, variables)
        
        results = await asyncio.gather(
            *[run_one(vs) for vs in variable_sets],
            return_exceptions=True
        )
        
        return [
            r if isinstance(r, str) else f"Error: {r}"
            for r in results
        ]
