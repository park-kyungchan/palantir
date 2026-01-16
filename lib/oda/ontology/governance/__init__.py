# Orion ODA V3 - Governance Module
# ==================================
# Declarative Action Governance via YAML + Quality Gates

from .loader import GovernanceLoader, ActionMetadata

# V3.1: Quality Enforcement
from .violations import (
    GovernanceError,
    Violation,
    ViolationReport,
    ViolationSeverity,
    ViolationType,
)
from .quality_gate import CodeQualityGate, QualityGateEnforcement
from .holistic_validator import HolisticValidator

# V3.1 Phase 2: Hallucination Filter (LLM-Agnostic Governance)
from .hallucination_filter import (
    EvidenceValidator,
    HallucinationFilter,
    HallucinationViolationType,
    ParameterSpec,
    ParameterValidator,
    ValidationResult,
    require_evidence,
    validate_action,
)

__all__ = [
    # Legacy
    "GovernanceLoader",
    "ActionMetadata",
    # Violations
    "Violation",
    "ViolationReport",
    "ViolationType",
    "ViolationSeverity",
    "GovernanceError",
    # Quality Gate
    "CodeQualityGate",
    "QualityGateEnforcement",
    # Holistic Validator
    "HolisticValidator",
    # Hallucination Filter (V3.1 Phase 2)
    "HallucinationFilter",
    "EvidenceValidator",
    "ParameterValidator",
    "ValidationResult",
    "ParameterSpec",
    "HallucinationViolationType",
    "validate_action",
    "require_evidence",
]
