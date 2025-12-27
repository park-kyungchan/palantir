import asyncio
from typing import Dict, Any, List
from pathlib import Path

from scripts.cognitive.types import LearnerState, ScopedLesson
from scripts.cognitive.learner import LearnerManager
from scripts.ontology.learning.scoping import ScopingEngine
from scripts.cognitive.generator import LessonGenerator, LessonInput, LessonContent
from scripts.aip_logic.engine import LogicEngine
from scripts.llm.instructor_client import InstructorClient

class AdaptiveTutoringEngine:
    """
    Phase 5 Cognitive Engine.
    Orchestrates the loop: State -> Scoping -> Content Generation -> Update.
    """
    
    def __init__(self, root_path: str):
        self.learner_manager = LearnerManager()
        self.scoping_engine = ScopingEngine(root_path)
        self.llm_client = InstructorClient() # Shared client
        self.logic_engine = LogicEngine(self.llm_client)
        
    async def initialize_session(self, user_id: str) -> Dict[str, Any]:
        """
        Start a learning session: Load state, scope curriculum.
        """
        # 1. Load Learner
        state = await self.learner_manager.get_state(user_id)
        
        # 2. Scope Curriculum
        recommendations = await self.scoping_engine.recommend_next(state)
        
        return {
            "session_id": "session_v5_dynamic", # Gen UUID in prod
            "learner": state.model_dump(),
            "recommendations": [rec.model_dump() for rec in recommendations]
        }
        
    async def generate_lesson(self, user_id: str, file_path: str) -> LessonContent:
        """
        Generate specific lesson content for a selected file.
        """
        state = await self.learner_manager.get_state(user_id)
        
        # We need the score from cache or re-analyze
        # Scoping engine has cache, let's peek or re-run
        # Simplification: re-analyze quickly or expose cache
        # For now, we trust ScopingEngine is hot or we re-analyze
        
        from scripts.ontology.learning.metrics import analyze_file
        score = analyze_file(file_path)
        
        full_path = Path(file_path) # Assuming absolute or we resolve relative
        # Fix: ScopingEngine used relative paths. We need to resolve.
        # Assuming file_path passed here is usable.
        
        if not full_path.exists():
             # Try relative to root?
             full_path = self.scoping_engine.root / file_path
             
        code_content = full_path.read_text(encoding="utf-8")
        
        input_data = LessonInput(
            file_name=full_path.name,
            code_content=code_content,
            complexity=score,
            learner_state=state
        )
        
        # Execute AIP Logic
        return await self.logic_engine.execute(LessonGenerator, input_data)
