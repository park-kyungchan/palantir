"""
Orion ODA PAI - Agent Composition Factory

Provides the AgentCompositionFactory for dynamically composing agents from traits,
and the AgentPersona ObjectType representing a composed agent's full configuration.

Actions:
- ComposeAgentAction: Compose an agent from explicit traits
- InferTraitsAction: Infer traits from a task description
- ResolveVoiceAction: Resolve voice for a set of traits
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable

from pydantic import Field, ConfigDict

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.registry import register_object_type
from lib.oda.pai.traits.dimensions import (
    ExpertiseType,
    PersonalityDimension,
    ApproachStyle,
    get_all_trait_values,
    classify_trait,
)
from lib.oda.pai.traits.trait_definition import TraitDefinition
from lib.oda.pai.traits.voice_mapping import VoiceRegistry, VoiceResolver


@register_object_type
class AgentPersona(OntologyObject):
    """
    A composed agent persona with all configuration resolved.

    AgentPersona represents the complete output of agent composition,
    including the selected traits, voice assignment, and full system prompt.

    This is the "compiled" result that can be used directly to instantiate
    an agent for task execution.

    Example:
        ```python
        persona = AgentPersona(
            name="Security Auditor",
            traits=["security", "skeptical", "thorough", "adversarial"],
            assigned_voice="Intense",
            voice_id="eleven_voice_123",
            full_prompt="You are a security expert who approaches..."
        )
        ```
    """

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
    )

    name: str = Field(
        ...,
        description="Generated or assigned name for this persona",
        min_length=1,
        max_length=100,
    )

    traits: List[str] = Field(
        default_factory=list,
        description="List of trait IDs composing this persona",
    )

    assigned_voice: Optional[str] = Field(
        default=None,
        description="Name of the assigned TTS voice",
    )

    voice_id: Optional[str] = Field(
        default=None,
        description="TTS provider's voice ID for synthesis",
    )

    full_prompt: str = Field(
        default="",
        description="Complete system prompt for the agent",
    )

    # Trait breakdown
    expertise_traits: List[str] = Field(
        default_factory=list,
        description="Expertise traits in this persona",
    )

    personality_traits: List[str] = Field(
        default_factory=list,
        description="Personality traits in this persona",
    )

    approach_traits: List[str] = Field(
        default_factory=list,
        description="Approach traits in this persona",
    )

    # Metadata
    task_description: Optional[str] = Field(
        default=None,
        description="Original task description if traits were inferred",
    )

    inference_scores: Optional[Dict[str, float]] = Field(
        default=None,
        description="Trait inference scores if auto-inferred",
    )

    voice_resolution_reason: Optional[str] = Field(
        default=None,
        description="Explanation for voice selection",
    )

    @property
    def trait_count(self) -> int:
        """Return total number of traits."""
        return len(self.traits)

    @property
    def has_voice(self) -> bool:
        """Check if voice is assigned."""
        return self.voice_id is not None

    def get_traits_by_dimension(self) -> Dict[str, List[str]]:
        """Return traits grouped by dimension."""
        return {
            "expertise": self.expertise_traits,
            "personality": self.personality_traits,
            "approach": self.approach_traits,
        }


@dataclass
class CompositionContext:
    """
    Context for agent composition operations.

    Holds all the data needed for trait inference, voice resolution,
    and prompt generation.
    """
    trait_definitions: Dict[str, TraitDefinition] = field(default_factory=dict)
    voice_resolver: Optional[VoiceResolver] = None
    prompt_template: str = ""
    default_expertise: Optional[str] = None
    default_personality: Optional[str] = None
    default_approach: Optional[str] = None


class AgentCompositionFactory:
    """
    Factory for composing agents from traits.

    The factory supports two modes:
    1. Explicit composition: Provide traits directly
    2. Inferred composition: Derive traits from task description

    Voice assignment is automatic based on trait mappings.

    Example:
        ```python
        factory = AgentCompositionFactory(context)

        # Explicit composition
        persona = factory.compose(
            traits=["security", "skeptical", "thorough"]
        )

        # Inferred composition
        persona = factory.compose_from_task(
            task="Review the authentication system for vulnerabilities"
        )
        ```
    """

    # Default prompt template with placeholders
    DEFAULT_PROMPT_TEMPLATE = """You are an AI assistant with the following characteristics:

{expertise_section}

{personality_section}

{approach_section}

Apply these traits consistently in your analysis and responses.
"""

    def __init__(self, context: Optional[CompositionContext] = None):
        """
        Initialize the composition factory.

        Args:
            context: Optional composition context with trait definitions.
        """
        self.context = context or CompositionContext()
        self._prompt_template = (
            self.context.prompt_template or self.DEFAULT_PROMPT_TEMPLATE
        )

    def compose(
        self,
        traits: List[str],
        name: Optional[str] = None,
    ) -> AgentPersona:
        """
        Compose an agent from explicit traits.

        Args:
            traits: List of trait IDs to compose.
            name: Optional name for the persona.

        Returns:
            Composed AgentPersona.
        """
        # Validate and classify traits
        validated_traits = self._validate_traits(traits)
        classified = self._classify_traits(validated_traits)

        # Generate name if not provided
        if not name:
            name = self._generate_name(classified)

        # Build prompt
        full_prompt = self._build_prompt(validated_traits)

        # Resolve voice
        voice = None
        voice_reason = None
        if self.context.voice_resolver:
            voice = self.context.voice_resolver.resolve(validated_traits)
            if voice:
                # Find the mapping that matched for the reason
                voice_reason = self._get_voice_reason(validated_traits)

        return AgentPersona(
            name=name,
            traits=validated_traits,
            assigned_voice=voice.voice_name if voice else None,
            voice_id=voice.voice_id if voice else None,
            full_prompt=full_prompt,
            expertise_traits=classified.get("expertise", []),
            personality_traits=classified.get("personality", []),
            approach_traits=classified.get("approach", []),
            voice_resolution_reason=voice_reason,
        )

    def compose_from_task(
        self,
        task: str,
        name: Optional[str] = None,
        min_confidence: float = 0.5,
    ) -> AgentPersona:
        """
        Compose an agent by inferring traits from task description.

        Args:
            task: Task description to analyze.
            name: Optional name for the persona.
            min_confidence: Minimum score threshold for trait selection.

        Returns:
            Composed AgentPersona with inference metadata.
        """
        # Infer traits from task
        inferred = self.infer_traits(task, min_confidence)

        # Compose with inferred traits
        persona = self.compose(inferred["traits"], name)

        # Add inference metadata
        persona.task_description = task
        persona.inference_scores = inferred["scores"]

        return persona

    def infer_traits(
        self,
        task: str,
        min_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Infer traits from a task description.

        Analyzes the task text against trait keywords to determine
        appropriate expertise, personality, and approach.

        Args:
            task: Task description to analyze.
            min_confidence: Minimum score threshold.

        Returns:
            Dictionary with 'traits' list and 'scores' mapping.
        """
        scores: Dict[str, float] = {}
        selected: Dict[str, str] = {}  # dimension -> best trait

        for trait_id, definition in self.context.trait_definitions.items():
            score = definition.get_weighted_score(task)
            if score > 0:
                scores[trait_id] = score

                # Track best per dimension
                dimension = definition.dimension
                if dimension not in selected or score > scores.get(selected[dimension], 0):
                    if score >= min_confidence:
                        selected[dimension] = trait_id

        # Collect selected traits
        traits = list(selected.values())

        # Apply defaults if no trait selected for dimension
        if "expertise" not in selected and self.context.default_expertise:
            traits.append(self.context.default_expertise)
        if "personality" not in selected and self.context.default_personality:
            traits.append(self.context.default_personality)
        if "approach" not in selected and self.context.default_approach:
            traits.append(self.context.default_approach)

        return {
            "traits": traits,
            "scores": scores,
            "selected_by_dimension": selected,
        }

    def resolve_voice(self, traits: List[str]) -> Optional[VoiceRegistry]:
        """
        Resolve voice for a set of traits.

        Args:
            traits: List of trait IDs.

        Returns:
            Resolved VoiceRegistry or None.
        """
        if not self.context.voice_resolver:
            return None
        return self.context.voice_resolver.resolve(traits)

    def _validate_traits(self, traits: List[str]) -> List[str]:
        """Validate and normalize trait IDs."""
        valid_traits = get_all_trait_values()
        validated = []

        for trait in traits:
            trait_lower = trait.lower()
            if trait_lower in valid_traits:
                validated.append(trait_lower)
            elif trait_lower in self.context.trait_definitions:
                validated.append(trait_lower)
            # Silently skip invalid traits (could also raise)

        return validated

    def _classify_traits(self, traits: List[str]) -> Dict[str, List[str]]:
        """Classify traits by dimension."""
        classified: Dict[str, List[str]] = {
            "expertise": [],
            "personality": [],
            "approach": [],
        }

        for trait in traits:
            dimension = classify_trait(trait)
            if dimension:
                classified[dimension].append(trait)
            elif trait in self.context.trait_definitions:
                dimension = self.context.trait_definitions[trait].dimension
                classified[dimension].append(trait)

        return classified

    def _generate_name(self, classified: Dict[str, List[str]]) -> str:
        """Generate a name from classified traits."""
        parts = []

        # Add expertise
        if classified.get("expertise"):
            parts.append(classified["expertise"][0].title())

        # Add personality
        if classified.get("personality"):
            parts.append(classified["personality"][0].title())

        # Add approach
        if classified.get("approach"):
            parts.append(classified["approach"][0].title())

        if not parts:
            return "Generic Agent"

        return " ".join(parts) + " Agent"

    def _build_prompt(self, traits: List[str]) -> str:
        """Build the full prompt from traits."""
        sections: Dict[str, List[str]] = {
            "expertise": [],
            "personality": [],
            "approach": [],
        }

        for trait in traits:
            if trait in self.context.trait_definitions:
                definition = self.context.trait_definitions[trait]
                if definition.prompt_fragment:
                    sections[definition.dimension].append(definition.prompt_fragment)

        # Format sections
        expertise_section = ""
        if sections["expertise"]:
            expertise_section = "EXPERTISE:\n" + "\n".join(sections["expertise"])

        personality_section = ""
        if sections["personality"]:
            personality_section = "PERSONALITY:\n" + "\n".join(sections["personality"])

        approach_section = ""
        if sections["approach"]:
            approach_section = "APPROACH:\n" + "\n".join(sections["approach"])

        return self._prompt_template.format(
            expertise_section=expertise_section,
            personality_section=personality_section,
            approach_section=approach_section,
        ).strip()

    def _get_voice_reason(self, traits: List[str]) -> Optional[str]:
        """Get the reason for voice selection."""
        if not self.context.voice_resolver:
            return None

        # Check combinations first
        for mapping in self.context.voice_resolver.combinations:
            if mapping.matches(traits):
                return mapping.reason

        # Check fallbacks
        for mapping in self.context.voice_resolver.fallbacks:
            if mapping.matches(traits):
                return mapping.reason

        return "Default voice assignment"


# =============================================================================
# ACTION DEFINITIONS
# =============================================================================

@dataclass
class ComposeAgentAction:
    """
    Action to compose an agent from explicit traits.

    Input:
        traits: List of trait IDs
        name: Optional persona name

    Output:
        AgentPersona with resolved configuration
    """
    api_name: str = "compose_agent"
    description: str = "Compose an agent from explicit traits"
    is_hazardous: bool = False

    def execute(
        self,
        factory: AgentCompositionFactory,
        traits: List[str],
        name: Optional[str] = None,
    ) -> AgentPersona:
        """Execute the composition action."""
        return factory.compose(traits=traits, name=name)


@dataclass
class InferTraitsAction:
    """
    Action to infer traits from a task description.

    Input:
        task: Task description text
        min_confidence: Minimum confidence threshold

    Output:
        Dictionary with inferred traits and scores
    """
    api_name: str = "infer_traits"
    description: str = "Infer traits from task description"
    is_hazardous: bool = False

    def execute(
        self,
        factory: AgentCompositionFactory,
        task: str,
        min_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """Execute the inference action."""
        return factory.infer_traits(task=task, min_confidence=min_confidence)


@dataclass
class ResolveVoiceAction:
    """
    Action to resolve voice for a set of traits.

    Input:
        traits: List of trait IDs

    Output:
        VoiceRegistry or None
    """
    api_name: str = "resolve_voice"
    description: str = "Resolve TTS voice for traits"
    is_hazardous: bool = False

    def execute(
        self,
        factory: AgentCompositionFactory,
        traits: List[str],
    ) -> Optional[VoiceRegistry]:
        """Execute the voice resolution action."""
        return factory.resolve_voice(traits=traits)
