"""
Math Image Parsing Pipeline - Alignment Module (Stage D)

Implements text-visual alignment:
- TextVisualMatcher for matching elements
- ConsistencyChecker for validating matches
- InconsistencyDetector for finding mismatches
- AlignmentEngine for orchestrating the process
"""

from .matcher import (
    MatcherConfig,
    SpatialMatcher,
    SemanticMatcher,
    TextVisualMatcher,
)
from .consistency import (
    ConsistencyConfig,
    EquationGraphConsistency,
    CoordinateConsistency,
    LabelConsistency,
    ConsistencyChecker,
)
from .inconsistency import (
    InconsistencyConfig,
    LabelInconsistencyDetector,
    EquationInconsistencyDetector,
    CoordinateInconsistencyDetector,
    InconsistencyDetector,
)
from .engine import (
    AlignmentEngineConfig,
    AlignmentEngine,
    create_alignment_engine,
    align_text_and_vision,
)

__all__ = [
    # Matcher
    "MatcherConfig",
    "SpatialMatcher",
    "SemanticMatcher",
    "TextVisualMatcher",
    # Consistency
    "ConsistencyConfig",
    "EquationGraphConsistency",
    "CoordinateConsistency",
    "LabelConsistency",
    "ConsistencyChecker",
    # Inconsistency
    "InconsistencyConfig",
    "LabelInconsistencyDetector",
    "EquationInconsistencyDetector",
    "CoordinateInconsistencyDetector",
    "InconsistencyDetector",
    # Engine
    "AlignmentEngineConfig",
    "AlignmentEngine",
    "create_alignment_engine",
    "align_text_and_vision",
]
