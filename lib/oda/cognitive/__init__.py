"""
ODA Cognitive Layer
===================
Adaptive tutoring engine with complexity analysis, learner tracking, and ZPD scoping.

Modules:
- types: Core data types (ComplexityScore, LearnerState, KnowledgeComponent, ScopedLesson)
- engine: Cognitive processing engine
- generator: Content generation
- learner: Learner state management
"""

from lib.oda.cognitive.types import (
    ComplexityScore,
    LearnerState,
    KnowledgeComponent,
    ScopedLesson,
)

__all__ = [
    "ComplexityScore",
    "LearnerState",
    "KnowledgeComponent",
    "ScopedLesson",
]
