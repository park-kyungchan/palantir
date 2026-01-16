from __future__ import annotations
from typing import TypeVar, Generic, Type, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict
from lib.oda.llm.instructor_client import InstructorClient
from lib.oda.llm.config import get_default_model

Input = TypeVar("Input", bound=BaseModel)
Output = TypeVar("Output", bound=BaseModel)

class LogicContext(BaseModel):
    """Execution context for a Logic Function (e.g. current user, loaded objects)."""
    llm: Optional[InstructorClient] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

class LogicFunction(ABC, Generic[Input, Output]):
    """
    Abstract Base Class for AIP Logic Functions.
    Encapsulates a unit of LLM-driven logic with strictly typed inputs and outputs.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the logic function."""
        pass

    @property
    @abstractmethod
    def input_type(self) -> Type[Input]:
        """Pydantic model class for input."""
        pass

    @property
    @abstractmethod
    def output_type(self) -> Type[Output]:
        """Pydantic model class for output."""
        pass

    @property
    def model_name(self) -> str:
        """Default LLM model to use."""
        return get_default_model()

    @abstractmethod
    async def run(self, input_data: Input, context: LogicContext) -> Output:
        """
        Execute the logic function.
        Override this to define custom pre-processing or multi-step logic.
        Default implementation handles simple prompt rendering and LLM call.
        """
        pass
