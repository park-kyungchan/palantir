"""
Orion ODA PAI - Traits Module

Composable Agent Traits for Dynamic Agent Composition.

This module provides the infrastructure for building dynamic agents through
trait composition. Agents are composed by combining:
- Expertise: Domain knowledge (security, legal, technical, etc.)
- Personality: Behavioral style (skeptical, analytical, empathetic, etc.)
- Approach: Working methodology (thorough, rapid, adversarial, etc.)

Key Components:
- Dimensions: Enum definitions for the three trait dimensions
- TraitDefinition: ObjectType for trait metadata and keywords
- VoiceMapping: ObjectTypes for TTS voice configuration
- CompositionFactory: Factory for composing agents from traits
- NamedAgents: Pre-configured named agent definitions

Usage:
    ```python
    from lib.oda.pai.traits import (
        ExpertiseType,
        PersonalityDimension,
        ApproachStyle,
        AgentCompositionFactory,
        AgentPersona,
    )

    # Create a security auditor persona
    factory = AgentCompositionFactory(context)
    persona = factory.compose(
        traits=["security", "skeptical", "thorough", "adversarial"],
        name="Security Auditor"
    )

    # Or infer traits from a task
    persona = factory.compose_from_task(
        task="Review the authentication system for vulnerabilities"
    )
    ```

Version: 1.0.0
"""

from lib.oda.pai.traits.dimensions import (
    ExpertiseType,
    PersonalityDimension,
    ApproachStyle,
    get_all_trait_values,
    classify_trait,
)

from lib.oda.pai.traits.trait_definition import (
    TraitDefinition,
    create_expertise_trait,
    create_personality_trait,
    create_approach_trait,
)

from lib.oda.pai.traits.voice_mapping import (
    VoiceRegistry,
    TraitVoiceMapping,
    VoiceResolver,
)

from lib.oda.pai.traits.composition_factory import (
    AgentPersona,
    AgentCompositionFactory,
    CompositionContext,
    ComposeAgentAction,
    InferTraitsAction,
    ResolveVoiceAction,
)

from lib.oda.pai.traits.named_agents import (
    NamedAgentDefinition,
    NamedAgentRegistry,
    RegisterNamedAgentAction,
)


__all__ = [
    # Dimensions (Enums)
    "ExpertiseType",
    "PersonalityDimension",
    "ApproachStyle",
    "get_all_trait_values",
    "classify_trait",

    # TraitDefinition ObjectType
    "TraitDefinition",
    "create_expertise_trait",
    "create_personality_trait",
    "create_approach_trait",

    # Voice Mapping ObjectTypes
    "VoiceRegistry",
    "TraitVoiceMapping",
    "VoiceResolver",

    # Composition Factory
    "AgentPersona",
    "AgentCompositionFactory",
    "CompositionContext",

    # Named Agents
    "NamedAgentDefinition",
    "NamedAgentRegistry",

    # Actions
    "ComposeAgentAction",
    "InferTraitsAction",
    "ResolveVoiceAction",
    "RegisterNamedAgentAction",
]


__version__ = "1.0.0"
