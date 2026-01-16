"""
Tests for LLM-Native Intent Classifier (V4.0)

Tests the IntentClassifier and related components.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lib.oda.llm.intent_adapter import (
    BaseIntentAdapter,
    CommandDescription,
    IntentMatchType,
    IntentResult,
)
from lib.oda.pai.skills.intent_classifier import (
    IntentClassifier,
    IntentClassifierConfig,
    ClarificationFlow,
    ClarificationRequest,
    DEFAULT_COMMANDS,
    LegacyTriggerMatch,
    convert_to_trigger_match,
    create_intent_classifier,
    get_default_commands,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_adapter():
    """Create a mock adapter for testing."""
    adapter = MagicMock(spec=BaseIntentAdapter)
    adapter.classify = AsyncMock()
    return adapter


@pytest.fixture
def classifier(mock_adapter):
    """Create classifier with mock adapter."""
    return IntentClassifier(adapter=mock_adapter)


@pytest.fixture
def sample_commands():
    """Sample command list for testing."""
    return [
        CommandDescription(
            name="/test",
            description="Test command",
            examples=["test this", "테스트"]
        ),
        CommandDescription(
            name="/other",
            description="Other command",
            examples=["other", "다른"]
        ),
    ]


# =============================================================================
# INTENT CLASSIFIER TESTS
# =============================================================================

class TestIntentClassifier:
    """Tests for IntentClassifier class."""

    def test_init_default(self):
        """Test default initialization."""
        config = IntentClassifierConfig()
        classifier = IntentClassifier(config=config, commands=[])
        
        assert classifier.config.adapter_type == "claude"
        assert classifier.config.clarification_threshold == 0.7
        assert classifier.config.min_confidence == 0.3

    def test_init_with_commands(self, mock_adapter, sample_commands):
        """Test initialization with custom commands."""
        classifier = IntentClassifier(
            adapter=mock_adapter,
            commands=sample_commands
        )
        
        assert len(classifier.commands) == 2
        assert classifier.commands[0].name == "/test"

    def test_add_command(self, classifier):
        """Test adding a command."""
        initial_count = len(classifier.commands)
        
        classifier.add_command(CommandDescription(
            name="/new",
            description="New command"
        ))
        
        assert len(classifier.commands) == initial_count + 1

    def test_remove_command(self, classifier):
        """Test removing a command."""
        classifier.add_command(CommandDescription(
            name="/to-remove",
            description="To remove"
        ))
        initial_count = len(classifier.commands)
        
        classifier.remove_command("/to-remove")
        
        assert len(classifier.commands) == initial_count - 1

    @pytest.mark.asyncio
    async def test_classify_success(self, classifier, mock_adapter):
        """Test successful classification."""
        mock_adapter.classify.return_value = IntentResult(
            command="/audit",
            confidence=0.92,
            reasoning="User wants code review",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="코드 리뷰해줘"
        )
        
        result = await classifier.classify("코드 리뷰해줘")
        
        assert result.command == "/audit"
        assert result.confidence == 0.92
        mock_adapter.classify.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_low_confidence_fallback(self, classifier, mock_adapter):
        """Test fallback on low confidence."""
        mock_adapter.classify.return_value = IntentResult(
            command="/audit",
            confidence=0.2,  # Below min_confidence (0.3)
            reasoning="Uncertain",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="뭔가"
        )
        
        result = await classifier.classify("뭔가")
        
        # Should fallback to /ask
        assert result.command == "/ask"
        assert result.match_type == IntentMatchType.FALLBACK

    @pytest.mark.asyncio
    async def test_classify_error_handling(self, classifier, mock_adapter):
        """Test error handling."""
        mock_adapter.classify.side_effect = Exception("API Error")
        
        result = await classifier.classify("test input")
        
        # Should fallback to /ask on error
        assert result.command == "/ask"
        assert result.confidence == 0.0
        assert "Classification failed" in result.reasoning

    def test_classify_sync(self, classifier, mock_adapter):
        """Test synchronous classification."""
        mock_adapter.classify.return_value = IntentResult(
            command="/plan",
            confidence=0.85,
            reasoning="Planning request",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="계획 세워줘"
        )
        
        result = classifier.classify_sync("계획 세워줘")
        
        assert result.command == "/plan"

    def test_needs_clarification_true(self, classifier):
        """Test needs_clarification returns True for low confidence."""
        result = IntentResult(
            command="/audit",
            confidence=0.5,  # Below threshold (0.7)
            reasoning="Uncertain",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="test"
        )
        
        assert classifier.needs_clarification(result) is True

    def test_needs_clarification_false_high_confidence(self, classifier):
        """Test needs_clarification returns False for high confidence."""
        result = IntentResult(
            command="/audit",
            confidence=0.9,
            reasoning="Clear match",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="test"
        )
        
        assert classifier.needs_clarification(result) is False

    def test_needs_clarification_false_explicit(self, classifier):
        """Test needs_clarification returns False for explicit commands."""
        result = IntentResult(
            command="/audit",
            confidence=0.5,  # Low confidence but explicit
            reasoning="Explicit command",
            match_type=IntentMatchType.EXPLICIT,
            raw_input="/audit"
        )
        
        assert classifier.needs_clarification(result) is False


# =============================================================================
# CLARIFICATION FLOW TESTS
# =============================================================================

class TestClarificationFlow:
    """Tests for ClarificationFlow class."""

    @pytest.fixture
    def flow(self, classifier):
        """Create clarification flow."""
        return ClarificationFlow(classifier)

    @pytest.mark.asyncio
    async def test_create_clarification(self, flow):
        """Test creating clarification request."""
        top_result = IntentResult(
            command="/audit",
            confidence=0.5,
            reasoning="Might be code review",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="봐줘"
        )
        
        request = await flow.create_clarification(top_result, "봐줘")
        
        assert request.original_input == "봐줘"
        assert request.top_match.command == "/audit"
        assert len(request.suggested_options) > 0

    def test_clarification_request_prompt_generation(self):
        """Test auto-generated clarification prompt."""
        request = ClarificationRequest(
            original_input="도와줘",
            top_match=IntentResult(
                command="/ask",
                confidence=0.6,
                reasoning="Help request",
                match_type=IntentMatchType.SEMANTIC,
                raw_input="도와줘"
            )
        )
        
        assert "도와줘" in request.clarification_prompt
        assert "/ask" in request.clarification_prompt
        assert "60%" in request.clarification_prompt

    def test_to_ask_user_format(self):
        """Test conversion to AskUserQuestion format."""
        request = ClarificationRequest(
            original_input="test",
            top_match=IntentResult(
                command="/audit",
                confidence=0.5,
                reasoning="Maybe audit",
                match_type=IntentMatchType.SEMANTIC,
                raw_input="test"
            ),
            alternatives=[
                IntentResult(
                    command="/plan",
                    confidence=0.3,
                    reasoning="Maybe plan",
                    match_type=IntentMatchType.SEMANTIC,
                    raw_input="test"
                )
            ]
        )
        
        format_dict = request.to_ask_user_format()
        
        assert "questions" in format_dict
        assert len(format_dict["questions"]) == 1
        assert "options" in format_dict["questions"][0]


# =============================================================================
# BACKWARD COMPATIBILITY TESTS
# =============================================================================

class TestBackwardCompatibility:
    """Tests for backward compatibility with TriggerDetector."""

    def test_legacy_trigger_match(self):
        """Test LegacyTriggerMatch conversion."""
        intent_result = IntentResult(
            command="/audit",
            confidence=0.9,
            reasoning="Code review",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="코드 리뷰"
        )
        
        legacy = LegacyTriggerMatch(intent_result)
        
        assert legacy.skill_name == "audit"  # Without leading slash
        assert legacy.confidence == 0.9
        assert legacy.matched_keyword is None
        assert legacy.context_similarity == 0.9

    def test_convert_to_trigger_match(self):
        """Test convert_to_trigger_match function."""
        intent_result = IntentResult(
            command="/plan",
            confidence=0.85,
            reasoning="Planning",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="계획"
        )
        
        legacy = convert_to_trigger_match(intent_result)
        
        assert isinstance(legacy, LegacyTriggerMatch)
        assert legacy.skill_name == "plan"

    def test_legacy_to_dict(self):
        """Test LegacyTriggerMatch.to_dict()."""
        intent_result = IntentResult(
            command="/ask",
            confidence=0.7,
            reasoning="Help",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="도와줘"
        )
        
        legacy = LegacyTriggerMatch(intent_result)
        result_dict = legacy.to_dict()
        
        assert result_dict["skill_name"] == "ask"
        assert result_dict["confidence"] == 0.7
        assert result_dict["reasoning"] == "Help"


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_intent_classifier(self):
        """Test create_intent_classifier factory."""
        classifier = create_intent_classifier(adapter_type="local")
        
        assert classifier.config.adapter_type == "local"

    def test_get_default_commands(self):
        """Test get_default_commands."""
        commands = get_default_commands()
        
        assert len(commands) == len(DEFAULT_COMMANDS)
        # Verify it's a copy
        commands.append(CommandDescription(name="/new", description="New"))
        assert len(DEFAULT_COMMANDS) != len(commands)

    def test_default_commands_content(self):
        """Test default commands have expected entries."""
        commands = get_default_commands()
        names = [c.name for c in commands]
        
        assert "/ask" in names
        assert "/plan" in names
        assert "/audit" in names
        assert "/deep-audit" in names


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full flow."""

    @pytest.mark.asyncio
    async def test_full_classification_flow(self, mock_adapter):
        """Test full classification and clarification flow."""
        # Setup
        mock_adapter.classify.return_value = IntentResult(
            command="/audit",
            confidence=0.5,  # Low confidence
            reasoning="Uncertain",
            match_type=IntentMatchType.SEMANTIC,
            raw_input="봐줘"
        )
        
        classifier = IntentClassifier(adapter=mock_adapter)
        
        # Classify
        result = await classifier.classify("봐줘")
        
        # Check if clarification needed
        if classifier.needs_clarification(result):
            flow = ClarificationFlow(classifier)
            request = await flow.create_clarification(result, "봐줘")
            
            # Should have clarification prompt
            assert len(request.clarification_prompt) > 0
            
            # Should be convertible to AskUserQuestion format
            ask_format = request.to_ask_user_format()
            assert "questions" in ask_format
