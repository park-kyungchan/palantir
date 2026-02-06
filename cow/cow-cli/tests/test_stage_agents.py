"""
Tests for Stage Agent Definitions.
"""
import pytest

from cow_cli.claude import (
    ModelType,
    StageType,
    AgentDefinition,
    INGESTION_AGENT,
    TEXT_PARSE_AGENT,
    SEPARATOR_AGENT,
    VISION_PARSE_AGENT,
    ALIGNMENT_AGENT,
    SEMANTIC_GRAPH_AGENT,
    REGENERATION_AGENT,
    HUMAN_REVIEW_AGENT,
    EXPORT_AGENT,
    STAGE_AGENTS,
    get_agent,
    get_agent_by_name,
    list_agents,
    get_agent_tools,
    get_pipeline_sequence,
)


class TestModelType:
    """Tests for ModelType enum."""

    def test_model_types(self):
        """Test all model types are defined."""
        assert ModelType.HAIKU.value == "haiku"
        assert ModelType.SONNET.value == "sonnet"
        assert ModelType.OPUS.value == "opus"


class TestStageType:
    """Tests for StageType enum."""

    def test_stage_types(self):
        """Test all stage types are defined."""
        assert StageType.INGESTION.value == "A"
        assert StageType.TEXT_PARSE.value == "B"
        assert StageType.SEPARATION.value == "B1"
        assert StageType.VISION_PARSE.value == "C"
        assert StageType.ALIGNMENT.value == "D"
        assert StageType.SEMANTIC_GRAPH.value == "E"
        assert StageType.REGENERATION.value == "F"
        assert StageType.HUMAN_REVIEW.value == "G"
        assert StageType.EXPORT.value == "H"


class TestAgentDefinition:
    """Tests for AgentDefinition dataclass."""

    def test_agent_to_dict(self):
        """Test agent serialization to dict."""
        agent = AgentDefinition(
            name="test-agent",
            stage=StageType.INGESTION,
            model=ModelType.HAIKU,
            tools=["tool1", "tool2"],
            system_prompt="Test prompt",
            description="Test description",
        )

        d = agent.to_dict()

        assert d["name"] == "test-agent"
        assert d["stage"] == "A"
        assert d["model"] == "haiku"
        assert d["tools"] == ["tool1", "tool2"]
        assert d["system_prompt"] == "Test prompt"
        assert d["description"] == "Test description"
        assert d["max_tokens"] == 4096
        assert d["temperature"] == 0.0


class TestIngestionAgent:
    """Tests for Ingestion Agent (Stage A)."""

    def test_agent_config(self):
        """Test agent configuration."""
        assert INGESTION_AGENT.name == "ingestion-agent"
        assert INGESTION_AGENT.stage == StageType.INGESTION
        assert INGESTION_AGENT.model == ModelType.HAIKU  # Fast, simple

    def test_agent_tools(self):
        """Test agent has required tools."""
        tools = INGESTION_AGENT.tools
        assert "mcp__cow-validation__validate_image" in tools
        assert "mcp__cow-validation__check_duplicates" in tools

    def test_agent_system_prompt(self):
        """Test agent has system prompt."""
        assert "Ingestion Agent" in INGESTION_AGENT.system_prompt
        assert "Stage A" in INGESTION_AGENT.system_prompt


class TestTextParseAgent:
    """Tests for Text Parse Agent (Stage B)."""

    def test_agent_config(self):
        """Test agent configuration."""
        assert TEXT_PARSE_AGENT.name == "text-parse-agent"
        assert TEXT_PARSE_AGENT.stage == StageType.TEXT_PARSE
        assert TEXT_PARSE_AGENT.model == ModelType.SONNET  # Balanced

    def test_agent_tools(self):
        """Test agent has required tools."""
        tools = TEXT_PARSE_AGENT.tools
        assert "mcp__cow-mathpix__mathpix_request" in tools
        assert "mcp__cow-mathpix__mathpix_poll" in tools


class TestSeparatorAgent:
    """Tests for Separator Agent (Stage B1)."""

    def test_agent_config(self):
        """Test agent configuration."""
        assert SEPARATOR_AGENT.name == "separator-agent"
        assert SEPARATOR_AGENT.stage == StageType.SEPARATION
        assert SEPARATOR_AGENT.model == ModelType.HAIKU

    def test_agent_tools(self):
        """Test agent has required tools."""
        tools = SEPARATOR_AGENT.tools
        assert "mcp__cow-separator__separate_layout_content" in tools
        assert "mcp__cow-separator__get_layout_elements" in tools


class TestSemanticGraphAgent:
    """Tests for Semantic Graph Agent (Stage E)."""

    def test_agent_uses_opus(self):
        """Test that semantic graph agent uses Opus for complex reasoning."""
        assert SEMANTIC_GRAPH_AGENT.model == ModelType.OPUS


class TestHumanReviewAgent:
    """Tests for Human Review Agent (Stage G)."""

    def test_agent_config(self):
        """Test agent configuration."""
        assert HUMAN_REVIEW_AGENT.name == "human-review-agent"
        assert HUMAN_REVIEW_AGENT.stage == StageType.HUMAN_REVIEW
        assert HUMAN_REVIEW_AGENT.model == ModelType.HAIKU

    def test_agent_tools(self):
        """Test agent has HITL tools."""
        tools = HUMAN_REVIEW_AGENT.tools
        assert "mcp__cow-hitl__queue_for_review" in tools
        assert "mcp__cow-hitl__get_review_status" in tools
        assert "mcp__cow-hitl__submit_review" in tools
        assert "mcp__cow-hitl__list_pending_reviews" in tools


class TestStageAgentsRegistry:
    """Tests for stage agent registry."""

    def test_all_stages_have_agents(self):
        """Test all stages have agent definitions."""
        for stage in StageType:
            assert stage in STAGE_AGENTS

    def test_total_agent_count(self):
        """Test correct number of agents."""
        assert len(STAGE_AGENTS) == 9  # A, B, B1, C, D, E, F, G, H

    def test_get_agent(self):
        """Test getting agent by stage."""
        agent = get_agent(StageType.INGESTION)
        assert agent == INGESTION_AGENT

    def test_get_agent_by_name(self):
        """Test getting agent by name."""
        agent = get_agent_by_name("separator-agent")
        assert agent == SEPARATOR_AGENT

    def test_get_agent_by_name_not_found(self):
        """Test getting non-existent agent."""
        agent = get_agent_by_name("nonexistent-agent")
        assert agent is None

    def test_list_agents(self):
        """Test listing all agents."""
        agents = list_agents()
        assert len(agents) == 9
        assert INGESTION_AGENT in agents
        assert EXPORT_AGENT in agents

    def test_get_agent_tools(self):
        """Test getting tools for a stage."""
        tools = get_agent_tools(StageType.HUMAN_REVIEW)
        assert "mcp__cow-hitl__queue_for_review" in tools


class TestPipelineSequence:
    """Tests for pipeline execution sequence."""

    def test_pipeline_sequence(self):
        """Test correct pipeline execution order."""
        sequence = get_pipeline_sequence()

        assert sequence[0] == StageType.INGESTION  # A
        assert sequence[1] == StageType.TEXT_PARSE  # B
        assert sequence[2] == StageType.SEPARATION  # B1
        assert sequence[3] == StageType.VISION_PARSE  # C
        assert sequence[4] == StageType.ALIGNMENT  # D
        assert sequence[5] == StageType.SEMANTIC_GRAPH  # E
        assert sequence[6] == StageType.REGENERATION  # F
        assert sequence[7] == StageType.HUMAN_REVIEW  # G
        assert sequence[8] == StageType.EXPORT  # H

    def test_sequence_length(self):
        """Test sequence contains all stages."""
        sequence = get_pipeline_sequence()
        assert len(sequence) == 9


class TestAgentModelAssignments:
    """Tests for appropriate model assignments."""

    def test_haiku_for_simple_tasks(self):
        """Test Haiku is used for simple/fast tasks."""
        haiku_agents = [
            INGESTION_AGENT,
            SEPARATOR_AGENT,
            HUMAN_REVIEW_AGENT,
            EXPORT_AGENT,
        ]
        for agent in haiku_agents:
            assert agent.model == ModelType.HAIKU, f"{agent.name} should use Haiku"

    def test_sonnet_for_balanced_tasks(self):
        """Test Sonnet is used for balanced tasks."""
        sonnet_agents = [
            TEXT_PARSE_AGENT,
            VISION_PARSE_AGENT,
            ALIGNMENT_AGENT,
            REGENERATION_AGENT,
        ]
        for agent in sonnet_agents:
            assert agent.model == ModelType.SONNET, f"{agent.name} should use Sonnet"

    def test_opus_for_complex_reasoning(self):
        """Test Opus is used for complex reasoning."""
        assert SEMANTIC_GRAPH_AGENT.model == ModelType.OPUS
