import asyncio
from typing import Dict, Any, List
from pathlib import Path

from scripts.cognitive.types import LearnerState, ScopedLesson
from scripts.cognitive.learner import LearnerManager
from scripts.ontology.learning.scoping import ScopingEngine
from scripts.ontology.learning.engine import TutoringEngine
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
        self.core_engine = TutoringEngine(root_path)
        self.scoping_engine = ScopingEngine(self.core_engine)
        self.llm_client = InstructorClient() # Shared client
        self.logic_engine = LogicEngine(self.llm_client)
        
    async def initialize_session(self, user_id: str) -> Dict[str, Any]:
        """
        Start a learning session: Load state, scope curriculum.
        """
        # 1. Load Learner
        state = await self.learner_manager.get_state(user_id)

        # 1.5 Scan Codebase & Calculate Scores (Required for Scoping)
        # In prod, this might be cached or incremental
        self.core_engine.scan_codebase()
        self.core_engine.calculate_scores()
        
        # 2. Scope Curriculum
        recommendations = self.scoping_engine.recommend_next_files(state)
        
        return {
            "session_id": "session_v5_dynamic", # Gen UUID in prod
            "learner": state.model_dump(),
            "recommendations": recommendations
        }
        
    async def generate_lesson(self, user_id: str, file_path: str) -> LessonContent:
        """
        Generate specific lesson content for a selected file.
        """
        state = await self.learner_manager.get_state(user_id)
        
        # We need the score from cache or re-analyze
        if file_path in self.core_engine.scores:
             score_obj = self.core_engine.scores[file_path]
             score = score_obj.total_score
        else:
             from scripts.ontology.learning.metrics import analyze_file
             # Fallback if not in graph (e.g. new file)
             score = 50.0 # Default fallback
        
        full_path = self.core_engine.root / file_path
        
        if not full_path.exists():
             raise FileNotFoundError(f"Lesson target not found: {full_path}")
             
        code_content = full_path.read_text(encoding="utf-8")
        
        input_data = LessonInput(
            file_name=full_path.name,
            code_content=code_content,
            complexity=score,
            learner_state=state
        )
        
        # Execute AIP Logic
        return await self.logic_engine.execute(LessonGenerator, input_data)
