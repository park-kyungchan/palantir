import pytest
from pydantic import BaseModel
from unittest.mock import MagicMock, patch

from scripts.aip_logic.function import LogicFunction, LogicContext
from scripts.aip_logic.engine import LogicEngine, LLMBasedLogicFunction, FunctionExecutionError

# --- Mock Models ---
class SummarizeInput(BaseModel):
    text: str

class SummarizeOutput(BaseModel):
    summary: str

# --- Mock Implementations ---
class SummarizeFunction(LLMBasedLogicFunction[SummarizeInput, SummarizeOutput]):
    @property
    def name(self) -> str:
        return "summarize_text"

    @property
    def input_type(self):
        return SummarizeInput

    @property
    def output_type(self):
        return SummarizeOutput
    
    @property
    def prompt_template(self) -> str:
        return "Summarize this: {text}"

# --- Tests ---

@pytest.mark.asyncio
async def test_logic_engine_execution_flow():
    """Verify that LogicEngine executes the run method of the function."""
    mock_llm = MagicMock()
    engine = LogicEngine(mock_llm)
    
    # We need to patch the internal run because LLMBasedLogicFunction tries to instantiate a real InstructorClient
    # In a real test we'd mock InstructorClient globally or inject it properly.
    
    with patch("scripts.aip_logic.engine.InstructorClient") as MockClient:
        # Mock the client instance returned by constructor
        mock_instance = MockClient.return_value
        # Mock generate return value
        expected_output = SummarizeOutput(summary="Short summary")
        mock_instance.generate.return_value = expected_output
        
        input_data = SummarizeInput(text="Long text here")
        result = await engine.execute(SummarizeFunction, input_data)
        
        assert result.summary == "Short summary"
        assert result == expected_output
        
        # Verify prompt construction
        mock_instance.generate.assert_called_once()
        call_args = mock_instance.generate.call_args
        assert call_args[0][0] == "Summarize this: Long text here" # prompt
        assert call_args[0][1] == SummarizeOutput # response_model

@pytest.mark.asyncio
async def test_custom_logic_function():
    """Verify a custom logic function that overrides run()."""
    
    class CustomFunc(LogicFunction[SummarizeInput, SummarizeOutput]):
        @property
        def name(self): return "custom"
        @property
        def input_type(self): return SummarizeInput
        @property
        def output_type(self): return SummarizeOutput
        
        async def run(self, input_data, context):
            return SummarizeOutput(summary=f"Processed: {input_data.text}")

    engine = LogicEngine(MagicMock())
    result = await engine.execute(CustomFunc, SummarizeInput(text="test"))
    assert result.summary == "Processed: test"
