"""
COW CLI - Stage Agent Definitions

Defines specialized agents for each pipeline stage.
Each agent has specific tools, model, and system prompt.

Pipeline Stages:
- Stage A: Ingestion (PDF/image validation, preprocessing)
- Stage B: Text Parse (Mathpix OCR)
- Stage B1: Separation (Layout/Content separation)
- Stage C: Vision Parse (Gemini vision analysis)
- Stage D: Alignment (Cross-modal alignment)
- Stage E: Semantic Graph (Graph construction)
- Stage F: Regeneration (Output generation)
- Stage G: Human Review (HITL workflow)
- Stage H: Export (Final output)
"""
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("cow-cli.agents")


class ModelType(str, Enum):
    """Claude model types for different complexity levels."""

    HAIKU = "haiku"  # Fast, simple tasks
    SONNET = "sonnet"  # Balanced performance
    OPUS = "opus"  # Complex reasoning


class StageType(str, Enum):
    """Pipeline stage identifiers."""

    INGESTION = "A"  # Stage A
    TEXT_PARSE = "B"  # Stage B
    SEPARATION = "B1"  # Stage B1
    VISION_PARSE = "C"  # Stage C
    ALIGNMENT = "D"  # Stage D
    SEMANTIC_GRAPH = "E"  # Stage E
    REGENERATION = "F"  # Stage F
    HUMAN_REVIEW = "G"  # Stage G
    EXPORT = "H"  # Stage H


@dataclass
class AgentDefinition:
    """
    Definition of a pipeline stage agent.

    Attributes:
        name: Agent identifier
        stage: Pipeline stage
        model: Claude model type
        tools: List of MCP tools available to the agent
        system_prompt: System instructions for the agent
        description: Human-readable description
        max_tokens: Maximum output tokens
        temperature: Sampling temperature
    """

    name: str
    stage: StageType
    model: ModelType
    tools: list[str]
    system_prompt: str
    description: str
    max_tokens: int = 4096
    temperature: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for SDK integration."""
        return {
            "name": self.name,
            "stage": self.stage.value,
            "model": self.model.value,
            "tools": self.tools,
            "system_prompt": self.system_prompt,
            "description": self.description,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


# =============================================================================
# STAGE AGENT DEFINITIONS
# =============================================================================


INGESTION_AGENT = AgentDefinition(
    name="ingestion-agent",
    stage=StageType.INGESTION,
    model=ModelType.HAIKU,
    tools=[
        "mcp__cow-validation__validate_image",
        "mcp__cow-validation__check_duplicates",
    ],
    system_prompt="""You are the Ingestion Agent (Stage A) for the COW pipeline.

Your responsibilities:
1. Validate incoming images/PDFs for processing
2. Check for duplicates to avoid redundant API calls
3. Report any issues with input files

When processing:
- Always validate the image format, size, and resolution first
- Check for duplicates before allowing processing
- Return detailed validation results

If validation fails, provide clear error messages.""",
    description="Validates and preprocesses images before OCR",
)


TEXT_PARSE_AGENT = AgentDefinition(
    name="text-parse-agent",
    stage=StageType.TEXT_PARSE,
    model=ModelType.SONNET,
    tools=[
        "mcp__cow-mathpix__mathpix_request",
        "mcp__cow-mathpix__mathpix_poll",
    ],
    system_prompt="""You are the Text Parse Agent (Stage B) for the COW pipeline.

Your responsibilities:
1. Submit images to Mathpix API for OCR processing
2. Monitor processing status and retrieve results
3. Extract word_data with confidence scores

Processing guidelines:
- Request word_data with all data_options enabled
- Track confidence scores for quality assessment
- Handle API errors gracefully with retries

Output should include:
- request_id for tracking
- word_data with text, math, and diagram elements
- confidence metrics""",
    description="Processes images through Mathpix OCR API",
)


SEPARATOR_AGENT = AgentDefinition(
    name="separator-agent",
    stage=StageType.SEPARATION,
    model=ModelType.HAIKU,
    tools=[
        "mcp__cow-separator__separate_layout_content",
        "mcp__cow-separator__get_layout_elements",
    ],
    system_prompt="""You are the Separator Agent (Stage B1) for the COW pipeline.

Your responsibilities:
1. Separate Mathpix output into Layout and Content data
2. Ensure ID consistency between layout and content elements
3. Track quality metrics for downstream processing

Separation rules:
- Layout: Spatial information (region, position, hierarchy)
- Content: Semantic information (text, latex, confidence)
- Maintain element ID references between both

Output:
- LayoutData with all spatial elements
- ContentData with all semantic elements
- Quality summary for review routing""",
    description="Separates OCR output into Layout and Content",
)


VISION_PARSE_AGENT = AgentDefinition(
    name="vision-parse-agent",
    stage=StageType.VISION_PARSE,
    model=ModelType.SONNET,
    tools=[
        # Vision tools would be added when implemented
        # "mcp__cow-vision__gemini_detect",
        # "mcp__cow-vision__gemini_interpret",
    ],
    system_prompt="""You are the Vision Parse Agent (Stage C) for the COW pipeline.

Your responsibilities:
1. Analyze images using Gemini vision API
2. Detect mathematical elements and diagrams
3. Interpret visual content semantically

Detection targets:
- Equations and mathematical expressions
- Geometric diagrams and graphs
- Charts and data visualizations
- Handwritten content regions

Output structured detection results for alignment.""",
    description="Vision-based analysis using Gemini API",
)


ALIGNMENT_AGENT = AgentDefinition(
    name="alignment-agent",
    stage=StageType.ALIGNMENT,
    model=ModelType.SONNET,
    tools=[
        # Alignment tools would be added when implemented
        # "mcp__cow-alignment__align_regions",
        # "mcp__cow-alignment__detect_inconsistencies",
    ],
    system_prompt="""You are the Alignment Agent (Stage D) for the COW pipeline.

Your responsibilities:
1. Align text-parsed and vision-parsed results
2. Detect inconsistencies between modalities
3. Flag items needing human review

Alignment process:
- Match layout elements by spatial overlap
- Compare content across parsing methods
- Calculate confidence deltas
- Flag significant discrepancies

Items with large confidence differences should be queued for review.""",
    description="Cross-modal alignment of parsing results",
)


SEMANTIC_GRAPH_AGENT = AgentDefinition(
    name="semantic-graph-agent",
    stage=StageType.SEMANTIC_GRAPH,
    model=ModelType.OPUS,  # Complex reasoning requires Opus
    tools=[
        # Graph tools would be added when implemented
        # "mcp__cow-graph__extract_nodes",
        # "mcp__cow-graph__infer_edges",
        # "mcp__cow-graph__validate_graph",
    ],
    system_prompt="""You are the Semantic Graph Agent (Stage E) for the COW pipeline.

Your responsibilities:
1. Build semantic graph from aligned content
2. Extract nodes (problems, solutions, concepts)
3. Infer edges (references, dependencies, equivalences)
4. Validate graph structure and consistency

Graph construction:
- Each content element becomes a node
- Infer relationships from mathematical structure
- Add metadata (confidence, source, type)
- Validate referential integrity

The semantic graph enables:
- Problem-solution matching
- Concept extraction
- Knowledge representation""",
    description="Constructs semantic knowledge graph",
)


REGENERATION_AGENT = AgentDefinition(
    name="regeneration-agent",
    stage=StageType.REGENERATION,
    model=ModelType.SONNET,
    tools=[
        # Regeneration tools would be added when implemented
        # "mcp__cow-regen__generate_latex",
        # "mcp__cow-regen__generate_svg",
    ],
    system_prompt="""You are the Regeneration Agent (Stage F) for the COW pipeline.

Your responsibilities:
1. Generate clean LaTeX from semantic graph
2. Create SVG diagrams from detected elements
3. Compare regenerated output with original

Regeneration process:
- Parse semantic graph nodes
- Generate LaTeX for mathematical content
- Create SVG for diagrams
- Calculate similarity with original

Output should be suitable for direct export.""",
    description="Regenerates clean output from semantic graph",
)


HUMAN_REVIEW_AGENT = AgentDefinition(
    name="human-review-agent",
    stage=StageType.HUMAN_REVIEW,
    model=ModelType.HAIKU,
    tools=[
        "mcp__cow-hitl__queue_for_review",
        "mcp__cow-hitl__get_review_status",
        "mcp__cow-hitl__submit_review",
        "mcp__cow-hitl__list_pending_reviews",
    ],
    system_prompt="""You are the Human Review Agent (Stage G) for the COW pipeline.

Your responsibilities:
1. Route low-confidence items to human review queue
2. Track review status and completion
3. Apply human corrections back to the pipeline

Routing criteria:
- Items with confidence < 0.75 need review
- Alignment inconsistencies need review
- Complex diagrams need review

After human review:
- Apply corrections to content
- Update confidence scores
- Log feedback for model improvement""",
    description="Manages human-in-the-loop review workflow",
)


EXPORT_AGENT = AgentDefinition(
    name="export-agent",
    stage=StageType.EXPORT,
    model=ModelType.HAIKU,
    tools=[
        # Export tools would be added when implemented
        # "mcp__cow-export__export_docx",
        # "mcp__cow-export__export_json",
        # "mcp__cow-export__export_latex",
    ],
    system_prompt="""You are the Export Agent (Stage H) for the COW pipeline.

Your responsibilities:
1. Export processed content to various formats
2. Generate DOCX, JSON, and LaTeX outputs
3. Validate export quality

Export formats:
- DOCX: For word processor editing
- JSON: For programmatic access
- LaTeX: For mathematical publishing

Ensure:
- All elements are included
- Formatting is preserved
- Math rendering is correct""",
    description="Exports content to various formats",
)


# =============================================================================
# AGENT REGISTRY
# =============================================================================


STAGE_AGENTS: dict[StageType, AgentDefinition] = {
    StageType.INGESTION: INGESTION_AGENT,
    StageType.TEXT_PARSE: TEXT_PARSE_AGENT,
    StageType.SEPARATION: SEPARATOR_AGENT,
    StageType.VISION_PARSE: VISION_PARSE_AGENT,
    StageType.ALIGNMENT: ALIGNMENT_AGENT,
    StageType.SEMANTIC_GRAPH: SEMANTIC_GRAPH_AGENT,
    StageType.REGENERATION: REGENERATION_AGENT,
    StageType.HUMAN_REVIEW: HUMAN_REVIEW_AGENT,
    StageType.EXPORT: EXPORT_AGENT,
}


def get_agent(stage: StageType) -> AgentDefinition:
    """Get agent definition for a stage."""
    return STAGE_AGENTS[stage]


def get_agent_by_name(name: str) -> Optional[AgentDefinition]:
    """Get agent definition by name."""
    for agent in STAGE_AGENTS.values():
        if agent.name == name:
            return agent
    return None


def list_agents() -> list[AgentDefinition]:
    """List all stage agents."""
    return list(STAGE_AGENTS.values())


def get_agent_tools(stage: StageType) -> list[str]:
    """Get tools available for a stage agent."""
    return STAGE_AGENTS[stage].tools


def get_pipeline_sequence() -> list[StageType]:
    """Get the standard pipeline execution sequence."""
    return [
        StageType.INGESTION,  # A
        StageType.TEXT_PARSE,  # B
        StageType.SEPARATION,  # B1
        StageType.VISION_PARSE,  # C
        StageType.ALIGNMENT,  # D
        StageType.SEMANTIC_GRAPH,  # E
        StageType.REGENERATION,  # F
        StageType.HUMAN_REVIEW,  # G
        StageType.EXPORT,  # H
    ]


__all__ = [
    # Types
    "ModelType",
    "StageType",
    "AgentDefinition",
    # Agents
    "INGESTION_AGENT",
    "TEXT_PARSE_AGENT",
    "SEPARATOR_AGENT",
    "VISION_PARSE_AGENT",
    "ALIGNMENT_AGENT",
    "SEMANTIC_GRAPH_AGENT",
    "REGENERATION_AGENT",
    "HUMAN_REVIEW_AGENT",
    "EXPORT_AGENT",
    # Registry
    "STAGE_AGENTS",
    "get_agent",
    "get_agent_by_name",
    "list_agents",
    "get_agent_tools",
    "get_pipeline_sequence",
]
