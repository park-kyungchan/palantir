from __future__ import annotations
from typing import Type
import logging
from pydantic import BaseModel

from scripts.llm.instructor_client import InstructorClient
from scripts.aip_logic.function import LogicFunction, LogicContext, Input, Output

logger = logging.getLogger(__name__)

class FunctionExecutionError(Exception):
    pass

class LogicEngine:
    """
    Engine for executing Logic Functions.
    Manages LLM client lifecycle and execution context.
    """

    def __init__(self, llm_client: InstructorClient):
        self.llm = llm_client

    async def execute(
        self, 
        function_cls: Type[LogicFunction[Input, Output]], 
        input_data: Input,
        context: LogicContext = None
    ) -> Output:
        """
        Instantiate and run a Logic Function.
        """
        if context is None:
            context = LogicContext()

        # [DI] Inject the Engine's LLM client if the context doesn't have one
        if context.llm is None:
            context.llm = self.llm

        function_instance = function_cls() # Assuming no-arg init for now or require factory
        
        try:
            logger.info(f"LogicFunction '{function_instance.name}': Executing...")
            result = await function_instance.run(input_data, context)
            logger.info(f"LogicFunction '{function_instance.name}': Success.")
            return result
        except Exception as e:
            logger.error(f"LogicFunction '{function_instance.name}': Failed - {e}")
            raise FunctionExecutionError(f"Execution of {function_instance.name} failed: {e}") from e

class LLMBasedLogicFunction(LogicFunction[Input, Output]):
    """
    Helper base class for simple Prompt -> LLM Logic Functions.
    """
    
    @property
    def prompt_template(self) -> str:
        """Jinja2-like template string."""
        raise NotImplementedError

    def render_prompt(self, input_data: Input) -> str:
        """Simple property injection into prompt template."""
        # For prototype, we use simple f-string format mapping
        # Production would use Jinja2
        return self.prompt_template.format(**input_data.model_dump())

    def __init__(self, llm_client: InstructorClient = None):
         # If instantiated directly, might need client. 
         # Ideally Engine handles this. For now, we assume run() gets client passed or uses global?
         # Refactoring: run() in ABC takes context. Engine should inject LLM into context or function.
         pass

    async def run(self, input_data: Input, context: LogicContext) -> Output:
        # [DI] Use injected LLM or fallback to new instance (legacy support)
        # In strict mode, we should mandate context.llm is present using LogicEngine
        client = context.llm
        if not client:
             # This fallback exists to support direct instantiation outside of Engine, 
             # but logs a warning in debug mode.
             client = InstructorClient() 

        prompt = self.render_prompt(input_data)
        return await client.generate_async(prompt, self.output_type, model_name=self.model_name)
