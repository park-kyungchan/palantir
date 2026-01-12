"""
Orion ODA PAI - Named Agent Definitions

Defines the NamedAgentDefinition ObjectType for pre-configured, named agents
with persistent identity, backstory, and voice assignment.

Named agents are the "character sheet" equivalent - fully defined agents
that can be instantiated by name rather than composed from traits.

Action:
- RegisterNamedAgentAction: Register a new named agent definition
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from pydantic import Field, ConfigDict, field_validator

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.registry import register_object_type
from lib.oda.pai.traits.dimensions import get_all_trait_values


@register_object_type
class NamedAgentDefinition(OntologyObject):
    """
    Definition for a pre-configured, named agent.

    Named agents are fully-specified agent configurations that can be
    instantiated by name. They combine traits with a persistent identity,
    backstory, and fixed voice assignment.

    Use Cases:
    - Persistent team members with consistent personalities
    - Branded agent personas for customer-facing applications
    - Testing with reproducible agent configurations

    Example:
        ```python
        nova = NamedAgentDefinition(
            agent_id="nova",
            display_name="Nova",
            archetype="security_auditor",
            backstory="A former penetration tester turned security consultant...",
            traits=["security", "skeptical", "adversarial", "thorough"],
            voice_id="eleven_voice_intense_123",
            specializations=["vulnerability assessment", "threat modeling"],
            example_tasks=[
                "Review authentication flow",
                "Audit API endpoints for security issues"
            ]
        )
        ```
    """

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
    )

    # Core identification
    agent_id: str = Field(
        ...,
        description="Unique identifier for this agent (lowercase, snake_case)",
        min_length=1,
        max_length=50,
        pattern=r"^[a-z][a-z0-9_]*$",
    )

    display_name: str = Field(
        ...,
        description="Human-friendly display name",
        min_length=1,
        max_length=100,
    )

    archetype: str = Field(
        ...,
        description="Agent archetype category (e.g., 'security_auditor', 'creative_writer')",
        min_length=1,
        max_length=50,
    )

    # Character definition
    backstory: Optional[str] = Field(
        default=None,
        description="Background story and motivation for the agent persona",
        max_length=2000,
    )

    personality_description: Optional[str] = Field(
        default=None,
        description="Prose description of personality and communication style",
        max_length=1000,
    )

    # Trait composition
    traits: List[str] = Field(
        default_factory=list,
        description="List of trait IDs that define this agent",
    )

    expertise_areas: List[str] = Field(
        default_factory=list,
        description="Specific areas of expertise within the archetype",
    )

    specializations: List[str] = Field(
        default_factory=list,
        description="Narrow specializations (e.g., 'OAuth 2.0', 'React hooks')",
    )

    # Voice configuration
    voice_id: Optional[str] = Field(
        default=None,
        description="Fixed TTS voice ID for this agent",
    )

    voice_name: Optional[str] = Field(
        default=None,
        description="Voice name reference",
    )

    voice_style: Optional[str] = Field(
        default=None,
        description="Voice style instructions (tone, pace, etc.)",
        max_length=500,
    )

    # System prompt components
    system_prompt_prefix: Optional[str] = Field(
        default=None,
        description="Custom prefix for the system prompt",
        max_length=2000,
    )

    system_prompt_suffix: Optional[str] = Field(
        default=None,
        description="Custom suffix for the system prompt",
        max_length=2000,
    )

    # Task guidance
    example_tasks: List[str] = Field(
        default_factory=list,
        description="Example tasks this agent excels at",
    )

    anti_patterns: List[str] = Field(
        default_factory=list,
        description="Tasks or behaviors to avoid",
    )

    # Interaction style
    communication_style: Optional[str] = Field(
        default=None,
        description="How the agent communicates (formal, casual, technical, etc.)",
        max_length=50,
    )

    response_format_preference: Optional[str] = Field(
        default=None,
        description="Preferred response format (structured, narrative, bullet points, etc.)",
        max_length=50,
    )

    # Metadata
    is_public: bool = Field(
        default=True,
        description="Whether this agent is publicly available",
    )

    is_featured: bool = Field(
        default=False,
        description="Whether this agent should be featured/promoted",
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and search",
    )

    @field_validator("traits")
    @classmethod
    def validate_traits(cls, v: List[str]) -> List[str]:
        """Validate that all traits are valid."""
        valid_traits = get_all_trait_values()
        validated = []
        for trait in v:
            trait_lower = trait.lower()
            if trait_lower in valid_traits:
                validated.append(trait_lower)
            else:
                # Allow custom traits but normalize case
                validated.append(trait_lower)
        return validated

    @property
    def has_voice(self) -> bool:
        """Check if voice is configured."""
        return self.voice_id is not None

    @property
    def trait_count(self) -> int:
        """Return number of traits."""
        return len(self.traits)

    def get_full_system_prompt(self, base_prompt: str = "") -> str:
        """
        Build the full system prompt for this agent.

        Args:
            base_prompt: Base prompt to include (usually from trait composition).

        Returns:
            Complete system prompt with prefix, base, and suffix.
        """
        parts = []

        # Add prefix if present
        if self.system_prompt_prefix:
            parts.append(self.system_prompt_prefix)

        # Add backstory if present
        if self.backstory:
            parts.append(f"BACKGROUND:\n{self.backstory}")

        # Add personality description
        if self.personality_description:
            parts.append(f"PERSONALITY:\n{self.personality_description}")

        # Add base prompt (from traits)
        if base_prompt:
            parts.append(base_prompt)

        # Add specializations
        if self.specializations:
            spec_list = ", ".join(self.specializations)
            parts.append(f"SPECIALIZATIONS: {spec_list}")

        # Add suffix if present
        if self.system_prompt_suffix:
            parts.append(self.system_prompt_suffix)

        return "\n\n".join(parts)

    def matches_task(self, task: str) -> bool:
        """
        Check if this agent is suitable for a task.

        Performs simple keyword matching against example_tasks
        and specializations.

        Args:
            task: Task description to match.

        Returns:
            True if the agent seems suitable.
        """
        task_lower = task.lower()

        # Check specializations
        for spec in self.specializations:
            if spec.lower() in task_lower:
                return True

        # Check example tasks (partial match)
        for example in self.example_tasks:
            # Check if significant words overlap
            example_words = set(example.lower().split())
            task_words = set(task_lower.split())
            overlap = example_words & task_words
            if len(overlap) >= 2:  # At least 2 words match
                return True

        # Check expertise areas
        for area in self.expertise_areas:
            if area.lower() in task_lower:
                return True

        return False

    def to_summary_dict(self) -> Dict[str, Any]:
        """
        Return a summary dictionary for display/selection.

        Returns:
            Dictionary with key fields for display.
        """
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "archetype": self.archetype,
            "traits": self.traits,
            "specializations": self.specializations,
            "has_voice": self.has_voice,
            "tags": self.tags,
        }


class NamedAgentRegistry:
    """
    Registry for managing named agent definitions.

    Provides methods for registering, retrieving, and searching
    named agents.
    """

    def __init__(self):
        """Initialize the registry."""
        self._agents: Dict[str, NamedAgentDefinition] = {}
        self._by_archetype: Dict[str, List[str]] = {}

    def register(self, agent: NamedAgentDefinition) -> None:
        """
        Register a named agent.

        Args:
            agent: The agent definition to register.
        """
        self._agents[agent.agent_id] = agent

        # Index by archetype
        if agent.archetype not in self._by_archetype:
            self._by_archetype[agent.archetype] = []
        if agent.agent_id not in self._by_archetype[agent.archetype]:
            self._by_archetype[agent.archetype].append(agent.agent_id)

    def get(self, agent_id: str) -> Optional[NamedAgentDefinition]:
        """
        Get an agent by ID.

        Args:
            agent_id: The agent's unique identifier.

        Returns:
            The agent definition or None.
        """
        return self._agents.get(agent_id)

    def get_by_archetype(self, archetype: str) -> List[NamedAgentDefinition]:
        """
        Get all agents of a specific archetype.

        Args:
            archetype: The archetype to filter by.

        Returns:
            List of matching agent definitions.
        """
        agent_ids = self._by_archetype.get(archetype, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def search(self, query: str) -> List[NamedAgentDefinition]:
        """
        Search for agents matching a query.

        Searches against display_name, archetype, tags, and specializations.

        Args:
            query: Search query string.

        Returns:
            List of matching agent definitions.
        """
        query_lower = query.lower()
        results = []

        for agent in self._agents.values():
            # Check display name
            if query_lower in agent.display_name.lower():
                results.append(agent)
                continue

            # Check archetype
            if query_lower in agent.archetype.lower():
                results.append(agent)
                continue

            # Check tags
            if any(query_lower in tag.lower() for tag in agent.tags):
                results.append(agent)
                continue

            # Check specializations
            if any(query_lower in spec.lower() for spec in agent.specializations):
                results.append(agent)
                continue

        return results

    def find_for_task(self, task: str) -> List[NamedAgentDefinition]:
        """
        Find agents suitable for a task.

        Args:
            task: Task description.

        Returns:
            List of suitable agent definitions.
        """
        return [
            agent for agent in self._agents.values()
            if agent.matches_task(task)
        ]

    def list_all(self) -> List[NamedAgentDefinition]:
        """Return all registered agents."""
        return list(self._agents.values())

    def list_featured(self) -> List[NamedAgentDefinition]:
        """Return all featured agents."""
        return [a for a in self._agents.values() if a.is_featured]

    def list_public(self) -> List[NamedAgentDefinition]:
        """Return all public agents."""
        return [a for a in self._agents.values() if a.is_public]


# =============================================================================
# ACTION DEFINITION
# =============================================================================

@dataclass
class RegisterNamedAgentAction:
    """
    Action to register a new named agent definition.

    Input:
        agent: NamedAgentDefinition to register

    Output:
        The registered agent's ID
    """
    api_name: str = "register_named_agent"
    description: str = "Register a new named agent definition"
    is_hazardous: bool = False

    def execute(
        self,
        registry: NamedAgentRegistry,
        agent: NamedAgentDefinition,
    ) -> str:
        """Execute the registration action."""
        registry.register(agent)
        return agent.agent_id
