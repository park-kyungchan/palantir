"""
Orion ODA PAI - Trait Dimensions

Defines the three composable trait dimensions for agent composition:
- ExpertiseType: Domain knowledge and specialization
- PersonalityDimension: How the agent thinks and behaves
- ApproachStyle: How the agent works on tasks

These enums enable type-safe trait selection when composing dynamic agents.
"""

from enum import Enum


class ExpertiseType(str, Enum):
    """
    Domain expertise areas for agent specialization.

    Each expertise type represents deep knowledge in a specific domain,
    with associated keywords for automatic trait inference from task descriptions.

    Examples:
        - SECURITY: Vulnerabilities, threat models, OWASP, CVE
        - TECHNICAL: Software architecture, debugging, APIs
        - FINANCE: Valuation, ROI, investment analysis
    """
    SECURITY = "security"
    LEGAL = "legal"
    FINANCE = "finance"
    MEDICAL = "medical"
    TECHNICAL = "technical"
    RESEARCH = "research"
    CREATIVE = "creative"
    BUSINESS = "business"
    DATA = "data"
    COMMUNICATIONS = "communications"

    @classmethod
    def values(cls) -> list[str]:
        """Return all expertise type values as strings."""
        return [e.value for e in cls]


class PersonalityDimension(str, Enum):
    """
    Personality traits that define how an agent thinks and behaves.

    Personality dimensions affect the agent's cognitive style, including
    how they approach problems, evaluate evidence, and communicate findings.

    Examples:
        - SKEPTICAL: Questions assumptions, demands evidence
        - ANALYTICAL: Data-driven, logical, systematic breakdown
        - EMPATHETIC: Considers human impact, user-centered
    """
    SKEPTICAL = "skeptical"
    ENTHUSIASTIC = "enthusiastic"
    CAUTIOUS = "cautious"
    BOLD = "bold"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    EMPATHETIC = "empathetic"
    CONTRARIAN = "contrarian"
    PRAGMATIC = "pragmatic"
    METICULOUS = "meticulous"

    @classmethod
    def values(cls) -> list[str]:
        """Return all personality dimension values as strings."""
        return [e.value for e in cls]


class ApproachStyle(str, Enum):
    """
    Working styles that define how an agent approaches tasks.

    Approach styles affect the methodology and pacing of analysis,
    from exhaustive thorough review to rapid key-point assessment.

    Examples:
        - THOROUGH: Exhaustive analysis, no stone unturned
        - RAPID: Quick assessment, key points, efficiency-focused
        - ADVERSARIAL: Red team approach, find weaknesses
    """
    THOROUGH = "thorough"
    RAPID = "rapid"
    SYSTEMATIC = "systematic"
    EXPLORATORY = "exploratory"
    COMPARATIVE = "comparative"
    SYNTHESIZING = "synthesizing"
    ADVERSARIAL = "adversarial"
    CONSULTATIVE = "consultative"

    @classmethod
    def values(cls) -> list[str]:
        """Return all approach style values as strings."""
        return [e.value for e in cls]


def get_all_trait_values() -> list[str]:
    """
    Return all valid trait values across all dimensions.

    Useful for validation and trait inference algorithms.

    Returns:
        Combined list of all expertise, personality, and approach values.
    """
    return (
        ExpertiseType.values() +
        PersonalityDimension.values() +
        ApproachStyle.values()
    )


def classify_trait(trait: str) -> str | None:
    """
    Classify a trait value into its dimension category.

    Args:
        trait: The trait value to classify.

    Returns:
        One of "expertise", "personality", "approach", or None if not found.
    """
    trait_lower = trait.lower()

    if trait_lower in ExpertiseType.values():
        return "expertise"
    elif trait_lower in PersonalityDimension.values():
        return "personality"
    elif trait_lower in ApproachStyle.values():
        return "approach"

    return None
