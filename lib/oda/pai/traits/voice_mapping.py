"""
Orion ODA PAI - Voice Mapping ObjectTypes

Defines ObjectTypes for TTS voice configuration and trait-to-voice mapping:
- VoiceRegistry: Defines available TTS voices with their characteristics
- TraitVoiceMapping: Maps trait combinations to appropriate voices

Voice Resolution Algorithm:
1. Check explicit combination mappings (full match wins)
2. Check fallbacks (single trait wins)
3. Default voice
"""

from __future__ import annotations

from typing import List, Optional, Dict

from pydantic import Field, ConfigDict, field_validator

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.registry import register_object_type


@register_object_type
class VoiceRegistry(OntologyObject):
    """
    TTS voice configuration entry.

    Defines a single voice available for agent TTS synthesis, including
    its ID, characteristics, and synthesis parameters.

    Example:
        ```python
        authoritative_voice = VoiceRegistry(
            voice_name="Authoritative",
            voice_id="eleven_voice_123",
            characteristics=["authoritative", "measured", "intellectual"],
            description="Deep authoritative voice for serious analysis",
            stability=0.70,
            similarity_boost=0.85
        )
        ```
    """

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
    )

    voice_name: str = Field(
        ...,
        description="Unique name for this voice (e.g., 'Authoritative', 'Warm')",
        min_length=1,
        max_length=50,
    )

    voice_id: str = Field(
        ...,
        description="TTS provider's voice ID (e.g., ElevenLabs voice ID)",
        min_length=1,
    )

    characteristics: List[str] = Field(
        default_factory=list,
        description="Voice characteristics (e.g., 'warm', 'professional', 'energetic')",
    )

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of voice qualities",
        max_length=500,
    )

    # Synthesis parameters
    stability: float = Field(
        default=0.5,
        description="Voice stability parameter (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    similarity_boost: float = Field(
        default=0.75,
        description="Voice similarity boost parameter (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    # Provider metadata
    provider: str = Field(
        default="elevenlabs",
        description="TTS provider name",
    )

    is_default: bool = Field(
        default=False,
        description="Whether this is the default fallback voice",
    )

    def has_characteristic(self, characteristic: str) -> bool:
        """Check if voice has a specific characteristic."""
        return characteristic.lower() in [c.lower() for c in self.characteristics]

    def get_synthesis_params(self) -> Dict[str, float]:
        """Return synthesis parameters as a dictionary."""
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
        }


@register_object_type
class TraitVoiceMapping(OntologyObject):
    """
    Mapping from trait combinations to TTS voices.

    Defines which voice should be used when an agent has specific traits.
    Supports both exact combination matches and single-trait fallbacks.

    Resolution Priority:
    1. Exact match: All traits in the mapping match the agent's traits
    2. Partial match: Score by number of matching traits
    3. Fallback: Single trait matches
    4. Default: Global default voice

    Example:
        ```python
        security_mapping = TraitVoiceMapping(
            traits=["security", "adversarial"],
            voice_name="Intense",
            reason="Security adversary suits intensity",
            priority=10
        )
        ```
    """

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
    )

    traits: List[str] = Field(
        ...,
        description="List of traits this mapping applies to",
        min_length=1,
    )

    voice_name: str = Field(
        ...,
        description="Name of the voice to use (must match VoiceRegistry.voice_name)",
        min_length=1,
    )

    reason: Optional[str] = Field(
        default=None,
        description="Explanation for why this mapping was chosen",
        max_length=500,
    )

    priority: int = Field(
        default=0,
        description="Priority for conflict resolution (higher wins)",
        ge=0,
    )

    is_fallback: bool = Field(
        default=False,
        description="Whether this is a single-trait fallback mapping",
    )

    @field_validator("traits")
    @classmethod
    def validate_traits_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure traits list is not empty."""
        if not v:
            raise ValueError("traits list cannot be empty")
        return [t.lower() for t in v]  # Normalize to lowercase

    @property
    def trait_count(self) -> int:
        """Return number of traits in this mapping."""
        return len(self.traits)

    def matches(self, agent_traits: List[str]) -> bool:
        """
        Check if this mapping matches the given agent traits.

        For non-fallback mappings, all mapping traits must be present.
        For fallback mappings, at least one trait must match.

        Args:
            agent_traits: List of traits the agent has.

        Returns:
            True if the mapping matches.
        """
        agent_traits_lower = [t.lower() for t in agent_traits]

        if self.is_fallback:
            # Fallback: at least one trait must match
            return any(t in agent_traits_lower for t in self.traits)
        else:
            # Combination: all mapping traits must be in agent traits
            return all(t in agent_traits_lower for t in self.traits)

    def match_score(self, agent_traits: List[str]) -> int:
        """
        Calculate match score for ranking mappings.

        Score is based on:
        - Number of matching traits
        - Priority boost
        - Bonus for exact match (all traits match both ways)

        Args:
            agent_traits: List of traits the agent has.

        Returns:
            Integer score (higher is better).
        """
        agent_traits_lower = [t.lower() for t in agent_traits]
        matching = sum(1 for t in self.traits if t in agent_traits_lower)

        # Base score from matches
        score = matching * 10

        # Priority boost
        score += self.priority

        # Exact match bonus (all mapping traits match)
        if matching == len(self.traits):
            score += 50

        # Perfect match bonus (bidirectional exact match)
        if set(self.traits) == set(agent_traits_lower):
            score += 100

        return score


class VoiceResolver:
    """
    Resolves traits to voices using the mapping algorithm.

    Resolution Priority:
    1. Check explicit combination mappings (full match wins)
    2. Check fallbacks (single trait wins)
    3. Default voice
    """

    def __init__(
        self,
        voices: List[VoiceRegistry],
        mappings: List[TraitVoiceMapping],
        default_voice_name: str = "Default",
    ):
        """
        Initialize the voice resolver.

        Args:
            voices: List of available voices.
            mappings: List of trait-to-voice mappings.
            default_voice_name: Name of the default voice.
        """
        self.voices = {v.voice_name: v for v in voices}
        self.mappings = sorted(mappings, key=lambda m: -m.priority)
        self.fallbacks = [m for m in mappings if m.is_fallback]
        self.combinations = [m for m in mappings if not m.is_fallback]
        self.default_voice_name = default_voice_name

    def resolve(self, traits: List[str]) -> Optional[VoiceRegistry]:
        """
        Resolve traits to a voice.

        Args:
            traits: List of traits to resolve.

        Returns:
            The matched VoiceRegistry, or None if no match found.
        """
        if not traits:
            return self._get_default_voice()

        # Step 1: Check combination mappings (full match required)
        best_combination = self._find_best_combination(traits)
        if best_combination:
            return self.voices.get(best_combination.voice_name)

        # Step 2: Check fallback mappings (single trait match)
        best_fallback = self._find_best_fallback(traits)
        if best_fallback:
            return self.voices.get(best_fallback.voice_name)

        # Step 3: Default voice
        return self._get_default_voice()

    def _find_best_combination(self, traits: List[str]) -> Optional[TraitVoiceMapping]:
        """Find the best matching combination mapping."""
        matching = [m for m in self.combinations if m.matches(traits)]
        if not matching:
            return None

        # Sort by match score, return best
        matching.sort(key=lambda m: -m.match_score(traits))
        return matching[0]

    def _find_best_fallback(self, traits: List[str]) -> Optional[TraitVoiceMapping]:
        """Find the best matching fallback mapping."""
        matching = [m for m in self.fallbacks if m.matches(traits)]
        if not matching:
            return None

        # Sort by priority, return best
        matching.sort(key=lambda m: -m.priority)
        return matching[0]

    def _get_default_voice(self) -> Optional[VoiceRegistry]:
        """Get the default voice."""
        # First try to find voice by default_voice_name
        if self.default_voice_name in self.voices:
            return self.voices[self.default_voice_name]

        # Then try to find voice marked as default
        for voice in self.voices.values():
            if voice.is_default:
                return voice

        # Return first voice if any exist
        if self.voices:
            return next(iter(self.voices.values()))

        return None

    def get_voice_by_name(self, name: str) -> Optional[VoiceRegistry]:
        """Get a voice by its name."""
        return self.voices.get(name)

    def list_voices(self) -> List[str]:
        """List all available voice names."""
        return list(self.voices.keys())
