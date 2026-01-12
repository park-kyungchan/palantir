from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class KnowledgeComponent(BaseModel):
    """Represents a discrete unit of knowledge (e.g., 'Async/Await', 'list_comprehension')."""
    id: str
    name: str
    mastery_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    slip_probability: float = 0.1
    guess_probability: float = 0.2
    learning_rate: float = 0.1

class LearnerState(BaseModel):
    """Current snapshot of the learner's proficiency."""
    user_id: str
    theta: float = Field(..., description="Global proficiency estimate (-3.0 to +3.0)")
    knowledge_components: Dict[str, KnowledgeComponent] = Field(default_factory=dict)
    last_active: datetime = Field(default_factory=datetime.now)
    session_history: List[str] = Field(default_factory=list)

class ComplexityScore(BaseModel):
    """Multidimensional teaching complexity metric."""
    total_score: float
    cognitive_index: float = Field(..., description="Control flow nesting depth weight")
    dependency_depth: int = Field(..., description="Import chain depth")
    novelty_density: float = Field(..., description="Unique tokens per LOC")
    domain_weight: float = Field(default=1.0, description="Palantir-specific pattern weight")

class ScopedLesson(BaseModel):
    """A file selected for teaching based on ZPD."""
    file_path: str
    score: ComplexityScore
    stretch_index: float = Field(..., description="Calculated ZPD stretch (0.1-0.3 optimal)")
    prerequisites: List[str] = Field(default_factory=list)
    learning_objective: str
