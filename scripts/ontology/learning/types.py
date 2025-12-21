"""
Orion Phase 5 - Learning Type Definitions
Defines the Pydantic models for Teaching Complexity and Learner Metrics.
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class MetricType(str, Enum):
    """Types of metrics collected from AST analysis."""
    COGNITIVE_COMPLEXITY = "cognitive_complexity"
    DEPENDENCY_DEPTH = "dependency_depth"
    NOVEL_CONCEPT_DENSITY = "novel_concept_density"
    DOMAIN_PATTERN_WEIGHT = "domain_pattern_weight"
    HALSTEAD_DIFFICULTY = "halstead_difficulty"

class CodeMetric(BaseModel):
    """Raw metric counts for a single file."""
    file_path: str = Field(..., description="Relative path to the source file")
    
    # Raw AST Counters
    loc: int = Field(0, description="Lines of Code")
    nesting_max: int = Field(0, description="Maximum nesting depth observed")
    control_flow_count: int = Field(0, description="Number of branch points (if/for/while)")
    
    # Concept Counters
    unique_imports: int = Field(0, description="Count of unique external modules imported")
    imports: List[str] = Field(default_factory=list, description="List of imported module names")
    classes: int = Field(0, description="Number of class definitions")
    functions: int = Field(0, description="Number of function definitions")
    async_patterns: int = Field(0, description="Count of async/await usages")
    pydantic_models: int = Field(0, description="Count of Pydantic models")
    
    # Domain Specific
    identified_patterns: List[str] = Field(default_factory=list, description="List of detected domain patterns")

class TeachingComplexityScore(BaseModel):
    """
    Composite Teaching Complexity Score (TCS).
    Formula: 0.3*CC + 0.25*DD + 0.2*NC + 0.15*DP + 0.1*HD
    """
    total_score: float = Field(..., description="The final composite TCS (0-100+)")
    
    # Breakdown
    cognitive_component: float = Field(..., description="Weighted Cognitive Complexity component")
    dependency_component: float = Field(..., description="Weighted Dependency Depth component")
    novelty_component: float = Field(..., description="Weighted Novel Concept component")
    pattern_component: float = Field(..., description="Weighted Domain Pattern component")
    halstead_component: float = Field(0.0, description="Weighted Halstead component (optional)")
    
    def __str__(self) -> str:
        return f"TCS: {self.total_score:.1f} (Cognitive: {self.cognitive_component:.1f}, Dependency: {self.dependency_component:.1f})"

# =============================================================================
# LEARNER STATE MODELS (Phase 5.2)
# =============================================================================

class KnowledgeComponentState(BaseModel):
    """
    Represents the mastery state of a single Knowledge Component (KC).
    Uses Bayesian Knowledge Tracing parameters.
    """
    concept_id: str = Field(..., description="Unique ID of the concept (e.g. 'async_patterns')")
    p_mastery: float = Field(0.3, description="Probability of mastery (0.0 to 1.0)", ge=0.0, le=1.0)
    last_assessed: Optional[datetime] = Field(None, description="Timestamp of last interaction")
    evidence_count: int = Field(0, description="Number of interactions derived from")

class LearnerState(BaseModel):
    """
    Global state for a learner.
    """
    user_id: str = Field(..., description="Unique user identifier")
    theta: float = Field(0.0, description="IRT Ability Estimate (-3.0 to +3.0)")
    knowledge_components: Dict[str, KnowledgeComponentState] = Field(default_factory=dict)
    
    def update_mastery(self, concept_id: str, new_p: float) -> None:
        if concept_id not in self.knowledge_components:
            self.knowledge_components[concept_id] = KnowledgeComponentState(concept_id=concept_id)
        
        kc = self.knowledge_components[concept_id]
        kc.p_mastery = new_p
        kc.evidence_count += 1
        kc.last_assessed = datetime.now()

