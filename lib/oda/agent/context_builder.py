"""
Orion ODA v4.0 - Ontology Context Builder
=========================================

Builds system prompts from ontology definitions for LLM agents.
Provides structured context about ObjectTypes, Actions, and relationships.

This module enables:
- Export ObjectType schemas for agent context
- Export available actions with parameters
- Inject field constraints into context
- Generate link graph descriptions

The output is optimized for LLM consumption with proper markdown formatting.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type

from pydantic import BaseModel, Field

from lib.oda.ontology.registry import (
    get_registry,
    OntologyRegistry,
    ObjectDefinition,
    PropertyDefinition,
    LinkDefinition,
)
from lib.oda.ontology.ontology_types import PropertyType
from lib.oda.ontology.actions import action_registry, ActionRegistry
from lib.oda.ontology.types.link_types import LinkTypeMetadata

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


class ContextOutputFormat(str, Enum):
    """Output format for context generation."""

    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"


@dataclass
class ContextBuilderConfig:
    """Configuration for context builder."""

    # Object types
    include_object_types: bool = True
    object_type_filter: Optional[List[str]] = None
    include_property_descriptions: bool = True
    include_property_constraints: bool = True

    # Actions
    include_actions: bool = True
    action_namespace_filter: Optional[List[str]] = None
    include_hazardous_actions: bool = True
    include_action_parameters: bool = True

    # Links
    include_link_graph: bool = True
    include_link_constraints: bool = True

    # Governance
    include_governance_rules: bool = True
    include_blocked_patterns: bool = True

    # Output
    output_format: ContextOutputFormat = ContextOutputFormat.MARKDOWN
    max_tokens: Optional[int] = None  # Truncate if exceeded


# =============================================================================
# CONTEXT SECTIONS
# =============================================================================


@dataclass
class ObjectTypeContext:
    """Context for a single ObjectType."""

    name: str
    description: str
    properties: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    links: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)


@dataclass
class ActionContext:
    """Context for a single Action."""

    api_name: str
    description: str
    requires_proposal: bool
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)


@dataclass
class LinkGraphContext:
    """Context for the link graph."""

    object_relationships: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    cardinality_summary: Dict[str, int] = field(default_factory=dict)
    link_descriptions: Dict[str, str] = field(default_factory=dict)


@dataclass
class BuiltContext:
    """Complete built context ready for export."""

    object_types: List[ObjectTypeContext] = field(default_factory=list)
    actions: List[ActionContext] = field(default_factory=list)
    link_graph: Optional[LinkGraphContext] = None
    governance_rules: List[str] = field(default_factory=list)
    blocked_patterns: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# ONTOLOGY CONTEXT BUILDER
# =============================================================================


class OntologyContextBuilder:
    """
    Builds LLM context from ontology definitions.

    This builder generates structured context that helps LLM agents understand:
    - What ObjectTypes exist and their properties
    - What Actions are available and their parameters
    - How objects relate to each other via links
    - What governance rules apply

    Example Usage:
        ```python
        builder = OntologyContextBuilder()

        # Build full context
        context = builder.build()

        # Export as markdown for system prompt
        markdown = builder.export_markdown(context)

        # Or get JSON for structured injection
        json_context = builder.export_json(context)
        ```
    """

    def __init__(
        self,
        ontology_registry: Optional[OntologyRegistry] = None,
        action_registry_instance: Optional[ActionRegistry] = None,
        config: Optional[ContextBuilderConfig] = None,
    ) -> None:
        """
        Initialize the context builder.

        Args:
            ontology_registry: OntologyRegistry instance (defaults to global)
            action_registry_instance: ActionRegistry instance (defaults to global)
            config: Configuration options
        """
        self._ontology = ontology_registry or get_registry()
        self._actions = action_registry_instance or action_registry
        self._config = config or ContextBuilderConfig()

    # =========================================================================
    # MAIN BUILD METHOD
    # =========================================================================

    def build(self, config: Optional[ContextBuilderConfig] = None) -> BuiltContext:
        """
        Build the complete context.

        Args:
            config: Optional config override

        Returns:
            BuiltContext with all requested sections
        """
        cfg = config or self._config
        context = BuiltContext()

        if cfg.include_object_types:
            context.object_types = self._build_object_types(cfg)

        if cfg.include_actions:
            context.actions = self._build_actions(cfg)

        if cfg.include_link_graph:
            context.link_graph = self._build_link_graph(cfg)

        if cfg.include_governance_rules:
            context.governance_rules = self._get_governance_rules()

        if cfg.include_blocked_patterns:
            context.blocked_patterns = self._get_blocked_patterns()

        return context

    # =========================================================================
    # OBJECT TYPE CONTEXT
    # =========================================================================

    def _build_object_types(self, cfg: ContextBuilderConfig) -> List[ObjectTypeContext]:
        """Build context for all ObjectTypes."""
        object_contexts = []
        objects = self._ontology.list_objects()

        for name, obj_def in sorted(objects.items()):
            # Apply filter
            if cfg.object_type_filter and name not in cfg.object_type_filter:
                continue

            obj_context = ObjectTypeContext(
                name=name,
                description=obj_def.description or f"ObjectType: {name}",
            )

            # Add properties
            for prop_name, prop_def in obj_def.properties.items():
                prop_info = {
                    "type": prop_def.property_type.value,
                    "required": prop_def.required,
                }

                if cfg.include_property_descriptions and prop_def.description:
                    prop_info["description"] = prop_def.description

                obj_context.properties[prop_name] = prop_info

            # Add links
            for link_name, link_def in obj_def.links.items():
                link_info = {
                    "target": link_def.target,
                    "cardinality": link_def.cardinality,
                }

                if link_def.description:
                    link_info["description"] = link_def.description

                obj_context.links[link_name] = link_info

            # Add constraints
            if cfg.include_property_constraints:
                obj_context.constraints = self._extract_constraints(name)

            object_contexts.append(obj_context)

        return object_contexts

    def _extract_constraints(self, object_type: str) -> List[str]:
        """Extract field constraints for an ObjectType."""
        constraints = []

        # Get the object definition
        objects = self._ontology.list_objects()
        obj_def = objects.get(object_type)
        if not obj_def:
            return constraints

        # Generate constraint descriptions from properties
        for prop_name, prop_def in obj_def.properties.items():
            if prop_def.required:
                constraints.append(f"'{prop_name}' is required")

            # Additional constraints would come from Pydantic Field metadata
            # This is a simplified version - full implementation would
            # introspect the actual class

        return constraints

    # =========================================================================
    # ACTION CONTEXT
    # =========================================================================

    def _build_actions(self, cfg: ContextBuilderConfig) -> List[ActionContext]:
        """Build context for all Actions."""
        action_contexts = []
        all_actions = self._actions.list_actions()
        hazardous = set(self._actions.get_hazardous_actions())

        for action_name in sorted(all_actions):
            # Apply namespace filter
            if cfg.action_namespace_filter:
                namespace = action_name.split(".")[0] if "." in action_name else ""
                if namespace not in cfg.action_namespace_filter:
                    continue

            # Apply hazardous filter
            is_hazardous = action_name in hazardous
            if not cfg.include_hazardous_actions and is_hazardous:
                continue

            metadata = self._actions.get_metadata(action_name)
            action_cls = self._actions.get(action_name)

            action_context = ActionContext(
                api_name=action_name,
                description=metadata.description if metadata else "",
                requires_proposal=is_hazardous,
            )

            # Add parameters
            if cfg.include_action_parameters and action_cls:
                schema = action_cls.get_parameter_schema()
                action_context.parameters = schema.get("properties", {})
                action_context.required_params = schema.get("required", [])

            action_contexts.append(action_context)

        return action_contexts

    # =========================================================================
    # LINK GRAPH CONTEXT
    # =========================================================================

    def _build_link_graph(self, cfg: ContextBuilderConfig) -> LinkGraphContext:
        """Build link graph context."""
        graph = LinkGraphContext()

        # Get all link types
        link_types = self._ontology.list_link_types()

        for link_id, link_type in link_types.items():
            # Build object relationships
            source = link_type.source_type
            target = link_type.target_type

            # Initialize source entry
            if source not in graph.object_relationships:
                graph.object_relationships[source] = {
                    "outgoing_links": [],
                    "incoming_links": [],
                    "targets": [],
                }

            # Initialize target entry
            if target not in graph.object_relationships:
                graph.object_relationships[target] = {
                    "outgoing_links": [],
                    "incoming_links": [],
                    "targets": [],
                }

            # Add relationships
            graph.object_relationships[source]["outgoing_links"].append(link_id)
            graph.object_relationships[source]["targets"].append(target)
            graph.object_relationships[target]["incoming_links"].append(link_id)

            # Track cardinality
            cardinality = link_type.cardinality
            graph.cardinality_summary[cardinality] = (
                graph.cardinality_summary.get(cardinality, 0) + 1
            )

            # Add description
            if link_type.description:
                graph.link_descriptions[link_id] = link_type.description

        return graph

    # =========================================================================
    # GOVERNANCE CONTEXT
    # =========================================================================

    def _get_governance_rules(self) -> List[str]:
        """Get governance rules for context."""
        return [
            "Actions marked as 'requires_proposal' must go through approval workflow",
            "Hazardous actions create a Proposal instead of executing immediately",
            "All mutations are logged for audit compliance",
            "Schema validation is enforced before any action execution",
        ]

    def _get_blocked_patterns(self) -> List[str]:
        """Get blocked patterns for context."""
        return [
            "rm -rf: Dangerous recursive deletion",
            "sudo rm: Privileged deletion not allowed",
            "chmod 777: Insecure permissions",
            "DROP TABLE: Database destruction not allowed",
            "eval(: Code injection risk",
            "exec(: Code execution risk",
        ]

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def export_markdown(self, context: BuiltContext) -> str:
        """
        Export context as markdown for system prompt.

        Args:
            context: Built context

        Returns:
            Markdown formatted string
        """
        sections = []

        # Header
        sections.append("# ODA Ontology Context\n")
        sections.append(f"Generated: {context.generated_at.isoformat()}\n")

        # Object Types
        if context.object_types:
            sections.append("\n## Object Types\n")
            sections.append(
                "These are the domain entities you can work with:\n"
            )

            for obj in context.object_types:
                sections.append(f"\n### {obj.name}\n")
                if obj.description:
                    sections.append(f"{obj.description}\n")

                # Properties table
                if obj.properties:
                    sections.append("\n**Properties:**\n")
                    sections.append("| Field | Type | Required | Description |")
                    sections.append("|-------|------|----------|-------------|")
                    for name, info in obj.properties.items():
                        required = "Yes" if info.get("required") else "No"
                        desc = info.get("description", "-")
                        ptype = info.get("type", "string")
                        sections.append(f"| {name} | {ptype} | {required} | {desc} |")
                    sections.append("")

                # Links
                if obj.links:
                    sections.append("\n**Relationships:**\n")
                    for name, info in obj.links.items():
                        card = info.get("cardinality", "1:N")
                        target = info.get("target", "Unknown")
                        desc = info.get("description", "")
                        sections.append(f"- `{name}` -> {target} ({card}): {desc}")
                    sections.append("")

                # Constraints
                if obj.constraints:
                    sections.append("\n**Constraints:**\n")
                    for constraint in obj.constraints:
                        sections.append(f"- {constraint}")
                    sections.append("")

        # Actions
        if context.actions:
            sections.append("\n## Available Actions\n")
            sections.append(
                "Use these actions to interact with the ontology:\n"
            )

            # Group by namespace
            namespaces: Dict[str, List[ActionContext]] = {}
            for action in context.actions:
                ns = action.api_name.split(".")[0] if "." in action.api_name else "general"
                if ns not in namespaces:
                    namespaces[ns] = []
                namespaces[ns].append(action)

            for ns, actions in sorted(namespaces.items()):
                sections.append(f"\n### {ns.upper()} Actions\n")
                for action in actions:
                    proposal_badge = " [REQUIRES APPROVAL]" if action.requires_proposal else ""
                    sections.append(f"\n#### `{action.api_name}`{proposal_badge}\n")
                    if action.description:
                        sections.append(f"{action.description}\n")

                    if action.parameters:
                        sections.append("\n**Parameters:**\n")
                        for param, info in action.parameters.items():
                            required = "*" if param in action.required_params else ""
                            ptype = info.get("type", "any")
                            sections.append(f"- `{param}{required}`: {ptype}")
                        if action.required_params:
                            sections.append("\n*Required parameters marked with asterisk*")
                        sections.append("")

        # Link Graph
        if context.link_graph:
            sections.append("\n## Object Relationships\n")
            sections.append(
                "This is how objects relate to each other:\n"
            )

            # Relationship summary
            if context.link_graph.cardinality_summary:
                sections.append("\n**Cardinality Summary:**\n")
                for card, count in context.link_graph.cardinality_summary.items():
                    sections.append(f"- {card}: {count} link types")
                sections.append("")

            # Object connections
            sections.append("\n**Object Connections:**\n")
            for obj_type, relationships in context.link_graph.object_relationships.items():
                outgoing = relationships.get("outgoing_links", [])
                incoming = relationships.get("incoming_links", [])
                targets = list(set(relationships.get("targets", [])))

                sections.append(f"\n**{obj_type}:**")
                if targets:
                    sections.append(f"- Connects to: {', '.join(targets)}")
                if outgoing:
                    sections.append(f"- Outgoing links: {len(outgoing)}")
                if incoming:
                    sections.append(f"- Incoming links: {len(incoming)}")

            # Link descriptions
            if context.link_graph.link_descriptions:
                sections.append("\n**Link Descriptions:**\n")
                for link_id, desc in context.link_graph.link_descriptions.items():
                    sections.append(f"- `{link_id}`: {desc}")

        # Governance Rules
        if context.governance_rules:
            sections.append("\n## Governance Rules\n")
            for rule in context.governance_rules:
                sections.append(f"- {rule}")
            sections.append("")

        # Blocked Patterns
        if context.blocked_patterns:
            sections.append("\n## Blocked Patterns\n")
            sections.append(
                "These patterns are NEVER allowed:\n"
            )
            for pattern in context.blocked_patterns:
                sections.append(f"- `{pattern}`")
            sections.append("")

        return "\n".join(sections)

    def export_json(self, context: BuiltContext) -> Dict[str, Any]:
        """
        Export context as JSON for structured injection.

        Args:
            context: Built context

        Returns:
            JSON-serializable dict
        """
        return {
            "generated_at": context.generated_at.isoformat(),
            "object_types": [
                {
                    "name": obj.name,
                    "description": obj.description,
                    "properties": obj.properties,
                    "links": obj.links,
                    "constraints": obj.constraints,
                }
                for obj in context.object_types
            ],
            "actions": [
                {
                    "api_name": action.api_name,
                    "description": action.description,
                    "requires_proposal": action.requires_proposal,
                    "parameters": action.parameters,
                    "required_params": action.required_params,
                }
                for action in context.actions
            ],
            "link_graph": {
                "object_relationships": context.link_graph.object_relationships,
                "cardinality_summary": context.link_graph.cardinality_summary,
                "link_descriptions": context.link_graph.link_descriptions,
            } if context.link_graph else None,
            "governance_rules": context.governance_rules,
            "blocked_patterns": context.blocked_patterns,
        }

    def export_yaml(self, context: BuiltContext) -> str:
        """
        Export context as YAML.

        Args:
            context: Built context

        Returns:
            YAML formatted string
        """
        import yaml
        return yaml.dump(
            self.export_json(context),
            default_flow_style=False,
            allow_unicode=True,
        )

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def build_system_prompt(
        self,
        include_objects: bool = True,
        include_actions: bool = True,
        include_links: bool = True,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Build a complete system prompt with ontology context.

        Args:
            include_objects: Include ObjectType definitions
            include_actions: Include Action definitions
            include_links: Include link graph
            max_tokens: Optional token limit

        Returns:
            Markdown formatted system prompt
        """
        config = ContextBuilderConfig(
            include_object_types=include_objects,
            include_actions=include_actions,
            include_link_graph=include_links,
            max_tokens=max_tokens,
        )

        context = self.build(config)
        markdown = self.export_markdown(context)

        # Truncate if needed
        if max_tokens:
            # Rough estimate: 4 chars per token
            max_chars = max_tokens * 4
            if len(markdown) > max_chars:
                markdown = markdown[:max_chars] + "\n\n... [Truncated for token limit]"

        return markdown

    def get_object_type_summary(self) -> Dict[str, str]:
        """
        Get a summary of all ObjectTypes.

        Returns:
            Dict mapping type name to description
        """
        objects = self._ontology.list_objects()
        return {
            name: obj.description or f"ObjectType: {name}"
            for name, obj in objects.items()
        }

    def get_action_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a summary of all Actions.

        Returns:
            Dict mapping action name to summary info
        """
        hazardous = set(self._actions.get_hazardous_actions())
        return {
            action: {
                "requires_proposal": action in hazardous,
                "description": (
                    self._actions.get_metadata(action).description
                    if self._actions.get_metadata(action)
                    else ""
                ),
            }
            for action in self._actions.list_actions()
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def build_agent_context(
    include_objects: bool = True,
    include_actions: bool = True,
    include_links: bool = True,
) -> str:
    """
    Build a complete agent context string.

    Args:
        include_objects: Include ObjectType definitions
        include_actions: Include Action definitions
        include_links: Include link graph

    Returns:
        Markdown formatted context
    """
    builder = OntologyContextBuilder()
    return builder.build_system_prompt(
        include_objects=include_objects,
        include_actions=include_actions,
        include_links=include_links,
    )


def get_context_json() -> Dict[str, Any]:
    """Get full context as JSON."""
    builder = OntologyContextBuilder()
    context = builder.build()
    return builder.export_json(context)
