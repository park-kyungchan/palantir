"""
Orion ODA PAI - Trait Definition ObjectType

Defines the TraitDefinition ObjectType for storing trait metadata including
keywords for inference and prompt fragments for agent composition.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field, ConfigDict

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.registry import register_object_type
from lib.oda.pai.traits.dimensions import (
    ExpertiseType,
    PersonalityDimension,
    ApproachStyle,
)


@register_object_type
class TraitDefinition(OntologyObject):
    """
    Definition of a composable agent trait.

    TraitDefinition stores the metadata for each trait including:
    - Keywords for automatic trait inference from task descriptions
    - Prompt fragments that get injected into the agent's system prompt
    - Human-readable name and description

    Traits are organized into three dimensions:
    - Expertise: Domain knowledge (security, legal, technical, etc.)
    - Personality: Behavioral style (skeptical, analytical, empathetic, etc.)
    - Approach: Working methodology (thorough, rapid, adversarial, etc.)

    Example:
        ```python
        security_trait = TraitDefinition(
            trait_id="security",
            name="Security Expert",
            dimension="expertise",
            description="Deep knowledge of vulnerabilities and threat models",
            keywords=["vulnerability", "threat", "CVE", "OWASP"],
            prompt_fragment="You approach all systems with security in mind..."
        )
        ```
    """

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
    )

    # Core identification
    trait_id: str = Field(
        ...,
        description="Unique identifier for this trait (e.g., 'security', 'skeptical')",
        min_length=1,
        max_length=50,
    )

    name: str = Field(
        ...,
        description="Human-readable name for display (e.g., 'Security Expert')",
        min_length=1,
        max_length=100,
    )

    dimension: str = Field(
        ...,
        description="Trait dimension: 'expertise', 'personality', or 'approach'",
        pattern="^(expertise|personality|approach)$",
    )

    description: Optional[str] = Field(
        default=None,
        description="Detailed description of what this trait provides",
        max_length=1000,
    )

    # Inference and composition
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that trigger this trait during inference",
    )

    prompt_fragment: str = Field(
        default="",
        description="Prompt text injected when this trait is active",
    )

    # Metadata
    is_default: bool = Field(
        default=False,
        description="Whether this is a default trait for its dimension",
    )

    weight: float = Field(
        default=1.0,
        description="Weighting factor for trait inference scoring",
        ge=0.0,
        le=10.0,
    )

    @property
    def keyword_count(self) -> int:
        """Return the number of keywords for this trait."""
        return len(self.keywords)

    def matches_text(self, text: str) -> int:
        """
        Count how many keywords match in the given text.

        Args:
            text: Text to search for keyword matches.

        Returns:
            Number of keyword matches found.
        """
        text_lower = text.lower()
        return sum(1 for kw in self.keywords if kw.lower() in text_lower)

    def get_weighted_score(self, text: str) -> float:
        """
        Calculate weighted match score for trait inference.

        Args:
            text: Text to score against.

        Returns:
            Weighted score based on keyword matches and trait weight.
        """
        matches = self.matches_text(text)
        return matches * self.weight


# =============================================================================
# FACTORY FUNCTIONS FOR CREATING STANDARD TRAITS
# =============================================================================

def create_expertise_trait(
    expertise: ExpertiseType,
    name: str,
    keywords: List[str],
    description: Optional[str] = None,
    prompt_fragment: str = "",
) -> TraitDefinition:
    """
    Factory function to create an expertise trait definition.

    Args:
        expertise: The ExpertiseType enum value.
        name: Human-readable name.
        keywords: Keywords for inference.
        description: Optional description.
        prompt_fragment: System prompt fragment.

    Returns:
        Configured TraitDefinition for the expertise.
    """
    return TraitDefinition(
        trait_id=expertise.value,
        name=name,
        dimension="expertise",
        description=description,
        keywords=keywords,
        prompt_fragment=prompt_fragment,
    )


def create_personality_trait(
    personality: PersonalityDimension,
    name: str,
    prompt_fragment: str,
    description: Optional[str] = None,
) -> TraitDefinition:
    """
    Factory function to create a personality trait definition.

    Args:
        personality: The PersonalityDimension enum value.
        name: Human-readable name.
        prompt_fragment: System prompt fragment (required for personality).
        description: Optional description.

    Returns:
        Configured TraitDefinition for the personality.
    """
    return TraitDefinition(
        trait_id=personality.value,
        name=name,
        dimension="personality",
        description=description,
        keywords=[],  # Personality traits don't use keyword inference
        prompt_fragment=prompt_fragment,
    )


def create_approach_trait(
    approach: ApproachStyle,
    name: str,
    prompt_fragment: str,
    description: Optional[str] = None,
) -> TraitDefinition:
    """
    Factory function to create an approach trait definition.

    Args:
        approach: The ApproachStyle enum value.
        name: Human-readable name.
        prompt_fragment: System prompt fragment (required for approach).
        description: Optional description.

    Returns:
        Configured TraitDefinition for the approach.
    """
    return TraitDefinition(
        trait_id=approach.value,
        name=name,
        dimension="approach",
        description=description,
        keywords=[],  # Approach traits don't use keyword inference
        prompt_fragment=prompt_fragment,
    )
