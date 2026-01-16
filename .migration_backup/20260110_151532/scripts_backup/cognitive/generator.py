from typing import List, Optional
from pydantic import BaseModel, Field

from scripts.aip_logic.engine import LLMBasedLogicFunction
from scripts.aip_logic.function import LogicContext
from scripts.cognitive.types import ComplexityScore, LearnerState
from scripts.llm.instructor_client import InstructorClient

class LessonInput(BaseModel):
    file_name: str
    code_content: str
    complexity: ComplexityScore
    learner_state: LearnerState

class LessonContent(BaseModel):
    """Structured output for an adaptive lesson."""
    title: str = Field(..., description="Engaging lesson title")
    concept_analogy: str = Field(..., description="Real-world analogy explaining the core concept")
    code_breakdown: List[str] = Field(..., description="Step-by-step logic explanation")
    interactive_exercise: str = Field(..., description="A short coding or thought exercise")
    success_criteria: str = Field(..., description="How to verify the exercise")

class LessonGenerator(LLMBasedLogicFunction[LessonInput, LessonContent]):
    """
    Complex AIP Logic to generate personalized lessons.
    Adapts explanation style based on Learner's Theta.
    """
    
    name = "LessonGenerator"
    description = "Generates adaptive curriculum from source code."
    input_type = LessonInput
    output_type = LessonContent
    # model_name = "llama3.2" # Default

    @property
    def prompt_template(self) -> str:
        return """
You are the Orion Infinite Tutor. Your goal is to teach the code in `{file_name}` to a student.

STUDENT PROFILE:
- Proficiency (Theta): {learner_state.theta} (-3.0=Novice, 3.0=Expert)
- Current Mastery: {learner_state.knowledge_components}

CODE METRICS:
- Cognitive Load: {complexity.cognitive_index}
- Novelty: {complexity.novelty_density}

SOURCE CODE:
```python
{code_content}
```

INSTRUCTIONS:
1. Analyze the code's pattern (e.g., Singleton, Recursion, async/await).
2. Adapt your explanation to the student's Theta:
   - If Theta < -1.0: Use simple, non-coding comparisons (Cooking, Traffic).
   - If Theta > 1.0: Use technical patterns and architecture terms.
3. Generate a structured lesson with:
   - A clear Analogy.
   - A breakdown of the logic effectively.
   - A practice exercise that isolates the *new* concept.

Think step-by-step about what the student likely misunderstands.
"""

    async def run(self, input_data: LessonInput, context: LogicContext) -> LessonContent:
        # Override run to fix async wrapping if needed, or just call super
        # Super 'LLMBasedLogicFunction' handles simple synchronous call for now.
        # We can inject specific client here if we want to change model
        
        # Note: In production, we would use asyncio.to_thread here
        client = InstructorClient() 
        prompt = self.render_prompt(input_data)
        
        # Execute (Synchronous Instructor call)
        return client.generate(prompt, self.output_type, model_name=self.model_name)
