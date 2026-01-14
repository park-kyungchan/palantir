"""
Orion ODA PAI Skills - /ask Skill Unit Tests

Tests for the /ask skill (Prompt Assistant) including:
- Socratic questioning flow
- Prompt engineering keyword detection
- Auto-routing decision tree
- Command recommendation logic
- Korean and English keyword handling

Reference: .claude/skills/ask.md

Version: 1.0.0
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# ASK SKILL CORE LOGIC (Extracted from ask.md for testing)
# =============================================================================

# Technique-Keyword Mapping (from Section 5)
TECHNIQUE_KEYWORDS = {
    "chain_of_thought": {
        "ko": ["단계별", "논리적", "순서대로", "차근차근"],
        "en": ["step-by-step", "logical", "sequential", "methodically"]
    },
    "few_shot": {
        "ko": ["예시", "예를 들면", "샘플", "보여줘"],
        "en": ["example", "show me", "sample", "demonstrate"]
    },
    "react": {
        "ko": ["행동", "반복", "시도", "실행하면서"],
        "en": ["action", "iterate", "try", "execute"]
    },
    "tree_of_thought": {
        "ko": ["대안", "비교", "여러 방법", "옵션"],
        "en": ["alternative", "compare", "options", "multiple ways"]
    },
    "self_consistency": {
        "ko": ["확인", "검증", "일관성"],
        "en": ["verify", "validate", "consistent"]
    },
    "zero_shot_cot": {
        "ko": ["생각해보면", "따져보면"],
        "en": ["let's think", "reasoning"]
    }
}

# Intent Detection Patterns (from Section 2)
INTENT_PATTERNS = {
    "help_request": {
        "ko": ["도와", "모르", "헷갈", "이해가 안"],
        "en": ["help", "don't know", "confused", "don't understand"]
    },
    "method_question": {
        "ko": ["어떻게", "방법", "하려면"],
        "en": ["how", "method", "to do"]
    },
    "explanation_request": {
        "ko": ["뭐야", "무엇", "설명"],
        "en": ["what", "explain", "describe"]
    },
    "guide_request": {
        "ko": ["알려", "가르쳐"],
        "en": ["guide", "tutorial", "teach"]
    }
}

# Intent-to-Route Mapping (from Section 7)
INTENT_TO_ROUTE = {
    "exploration": {
        "keywords_ko": ["분석", "이해", "설명", "구조", "탐색"],
        "keywords_en": ["analyze", "understand", "explain", "structure", "explore"],
        "route": "Explore Agent"
    },
    "modification": {
        "keywords_ko": ["수정", "고쳐", "변경", "바꿔", "추가"],
        "keywords_en": ["fix", "modify", "change", "add", "update"],
        "route": "/plan"
    },
    "review": {
        "keywords_ko": ["검사", "리뷰", "확인", "체크", "감사"],
        "keywords_en": ["check", "review", "verify", "audit"],
        "route": "/audit"
    },
    "deep_analysis": {
        "keywords_ko": ["심층", "깊이", "상세", "철저히"],
        "keywords_en": ["deep", "thorough", "detailed", "intensive"],
        "route": "/deep-audit"
    },
    "planning": {
        "keywords_ko": ["계획", "설계", "아키텍처", "구현"],
        "keywords_en": ["plan", "design", "architecture", "implement"],
        "route": "/plan"
    }
}

# Recommendation Decision Matrix (from Section 8)
RECOMMENDATION_MATRIX = {
    ("explore", "low"): "Direct Read",
    ("explore", "medium"): "Explore Agent",
    ("explore", "high"): "Explore Agent + /plan",
    ("modify", "low"): "Direct Edit",
    ("modify", "medium"): "/plan",
    ("modify", "high"): "/plan + /audit",
    ("review", "low"): "/audit",
    ("review", "medium"): "/audit",
    ("review", "high"): "/deep-audit",
}


# =============================================================================
# IMPLEMENTATION FUNCTIONS (Extracted from ask.md)
# =============================================================================

def detect_technique(user_input: str) -> Optional[str]:
    """
    Detect prompt engineering technique from user input.

    From ask.md Section 5: Technique Detection Logic

    Args:
        user_input: User's input text

    Returns:
        Technique name if detected, None otherwise
    """
    user_input_lower = user_input.lower()
    for technique, keywords in TECHNIQUE_KEYWORDS.items():
        for lang_keywords in keywords.values():
            for keyword in lang_keywords:
                if keyword in user_input_lower:
                    return technique
    return None


def detect_intent_pattern(user_input: str) -> List[str]:
    """
    Detect intent patterns from user input.

    From ask.md Section 2: Intent Detection Patterns

    Args:
        user_input: User's input text

    Returns:
        List of detected intent patterns
    """
    user_input_lower = user_input.lower()
    detected = []

    for pattern_name, keywords in INTENT_PATTERNS.items():
        for lang_keywords in keywords.values():
            for keyword in lang_keywords:
                if keyword in user_input_lower:
                    if pattern_name not in detected:
                        detected.append(pattern_name)
                    break

    return detected


def determine_route(user_input: str) -> str:
    """
    Determine the routing target based on user input.

    From ask.md Section 7: Auto-Routing Decision Tree

    Args:
        user_input: User's input text

    Returns:
        Route target (skill name or agent)
    """
    user_input_lower = user_input.lower()

    for intent_name, intent_data in INTENT_TO_ROUTE.items():
        for keyword in intent_data["keywords_ko"]:
            if keyword in user_input_lower:
                return intent_data["route"]
        for keyword in intent_data["keywords_en"]:
            if keyword in user_input_lower:
                return intent_data["route"]

    # Default: stay in /ask for further clarification
    return "/ask"


def recommend_skill(intent: str, complexity: str) -> str:
    """
    Recommend appropriate skill based on intent and complexity.

    From ask.md Section 8: Recommendation Decision Matrix

    Args:
        intent: User intent category (explore, modify, review)
        complexity: Task complexity (low, medium, high)

    Returns:
        Recommended skill/action
    """
    return RECOMMENDATION_MATRIX.get((intent, complexity), "/ask")


def assess_clarity(user_input: str) -> float:
    """
    Assess clarity of user input.

    From ask.md Section 9: Execution Protocol
    Score ranges from 0 (very unclear) to 1 (very clear).

    Args:
        user_input: User's input text

    Returns:
        Clarity score (0.0 to 1.0)
    """
    score = 0.5  # Base score

    # Check for specific keywords indicating clear intent
    clear_indicators = [
        "분석", "수정", "검사", "계획", "구현",
        "analyze", "fix", "review", "plan", "implement"
    ]
    unclear_indicators = [
        "뭔가", "좀", "그거", "어떻게",
        "something", "somehow", "that thing"
    ]

    user_lower = user_input.lower()

    for indicator in clear_indicators:
        if indicator in user_lower:
            score += 0.15

    for indicator in unclear_indicators:
        if indicator in user_lower:
            score -= 0.1

    # Length bonus (longer inputs tend to be clearer)
    if len(user_input) > 50:
        score += 0.1
    elif len(user_input) < 10:
        score -= 0.1

    return max(0.0, min(1.0, score))


def needs_clarification(clarity_score: float, threshold: float = 0.7) -> bool:
    """
    Determine if user input needs clarification.

    From ask.md Section 9: Execution Protocol

    Args:
        clarity_score: Assessed clarity score
        threshold: Threshold for requiring clarification (default 0.7)

    Returns:
        True if clarification needed
    """
    return clarity_score < threshold


@dataclass
class SocraticQuestion:
    """Represents a Socratic clarification question."""
    category: str  # scope, goal, priority, task_type
    question: str
    options: List[Dict[str, str]]


def generate_socratic_questions(detected_gaps: List[str]) -> List[SocraticQuestion]:
    """
    Generate Socratic questions based on detected gaps.

    From ask.md Section 4: Clarification Question Templates

    Args:
        detected_gaps: List of information gaps (scope, goal, priority, task_type)

    Returns:
        List of SocraticQuestion objects
    """
    questions = []

    question_templates = {
        "scope": SocraticQuestion(
            category="scope",
            question="어떤 파일/모듈을 대상으로 할까요?",
            options=[
                {"label": "특정 파일", "description": "파일 경로 입력"},
                {"label": "특정 모듈", "description": "모듈명 입력"},
                {"label": "전체 프로젝트", "description": "프로젝트 전체"},
                {"label": "현재 작업 디렉토리", "description": "현재 위치"}
            ]
        ),
        "goal": SocraticQuestion(
            category="goal",
            question="최종 목표가 무엇인가요?",
            options=[
                {"label": "코드 분석/이해", "description": "코드 구조 파악"},
                {"label": "버그 수정", "description": "문제 해결"},
                {"label": "새 기능 구현", "description": "기능 추가"},
                {"label": "리팩토링/개선", "description": "코드 개선"},
                {"label": "문서화", "description": "문서 작성"},
                {"label": "테스트 작성", "description": "테스트 추가"}
            ]
        ),
        "priority": SocraticQuestion(
            category="priority",
            question="우선순위가 있나요?",
            options=[
                {"label": "긴급", "description": "즉시 처리 필요"},
                {"label": "높음", "description": "오늘 내 완료"},
                {"label": "보통", "description": "일주일 내"},
                {"label": "낮음", "description": "시간 여유 있음"}
            ]
        ),
        "task_type": SocraticQuestion(
            category="task_type",
            question="어떤 종류의 작업인가요?",
            options=[
                {"label": "탐색/분석", "description": "읽기 전용"},
                {"label": "수정/변경", "description": "파일 변경 필요"},
                {"label": "검사/리뷰", "description": "품질 확인"},
                {"label": "계획/설계", "description": "구현 전 계획"}
            ]
        )
    }

    for gap in detected_gaps:
        if gap in question_templates:
            questions.append(question_templates[gap])

    return questions


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_korean_inputs() -> List[Tuple[str, str]]:
    """Sample Korean inputs with expected techniques."""
    return [
        ("단계별로 설명해줘", "chain_of_thought"),
        ("예시를 보여줘", "few_shot"),
        ("여러 방법을 비교해줘", "tree_of_thought"),
        ("반복해서 시도해봐", "react"),
        ("검증해줘", "self_consistency"),
        ("그냥 해줘", None),  # No technique detected
    ]


@pytest.fixture
def sample_english_inputs() -> List[Tuple[str, str]]:
    """Sample English inputs with expected techniques."""
    return [
        ("explain step-by-step", "chain_of_thought"),
        ("show me an example", "few_shot"),
        ("compare multiple ways", "tree_of_thought"),
        ("iterate and try", "react"),
        ("validate this", "self_consistency"),
        ("just do it", None),  # No technique detected
    ]


@pytest.fixture
def sample_routing_inputs() -> List[Tuple[str, str]]:
    """Sample inputs with expected routing targets."""
    return [
        ("코드 구조를 분석해줘", "Explore Agent"),
        ("버그를 수정해줘", "/plan"),
        ("코드 리뷰해줘", "/audit"),
        ("심층적으로 검토해줘", "/deep-audit"),  # Fixed: use only deep_analysis keywords
        ("아키텍처를 설계해줘", "/plan"),
        ("뭔가 해줘", "/ask"),  # Ambiguous -> stay in /ask
    ]


# =============================================================================
# TEST CASES: Socratic Questioning Flow
# =============================================================================

class TestSocraticQuestioning:
    """Tests for Socratic questioning flow (ask.md Section 3)."""

    def test_generate_scope_question(self):
        """Test scope clarification question generation."""
        questions = generate_socratic_questions(["scope"])

        assert len(questions) == 1
        assert questions[0].category == "scope"
        assert "파일" in questions[0].question or "모듈" in questions[0].question
        assert len(questions[0].options) >= 3

    def test_generate_goal_question(self):
        """Test goal clarification question generation."""
        questions = generate_socratic_questions(["goal"])

        assert len(questions) == 1
        assert questions[0].category == "goal"
        assert "목표" in questions[0].question
        assert any("버그" in opt["label"] or "수정" in opt["label"]
                   for opt in questions[0].options)

    def test_generate_priority_question(self):
        """Test priority clarification question generation."""
        questions = generate_socratic_questions(["priority"])

        assert len(questions) == 1
        assert questions[0].category == "priority"
        assert "우선순위" in questions[0].question
        assert any("긴급" in opt["label"] for opt in questions[0].options)

    def test_generate_task_type_question(self):
        """Test task type clarification question generation."""
        questions = generate_socratic_questions(["task_type"])

        assert len(questions) == 1
        assert questions[0].category == "task_type"
        assert any("탐색" in opt["label"] or "분석" in opt["label"]
                   for opt in questions[0].options)

    def test_generate_multiple_questions(self):
        """Test multiple question generation."""
        gaps = ["scope", "goal", "priority"]
        questions = generate_socratic_questions(gaps)

        assert len(questions) == 3
        categories = [q.category for q in questions]
        assert "scope" in categories
        assert "goal" in categories
        assert "priority" in categories

    def test_generate_no_questions_for_unknown_gap(self):
        """Test that unknown gaps don't generate questions."""
        questions = generate_socratic_questions(["unknown_gap"])

        assert len(questions) == 0

    def test_question_options_have_labels(self):
        """Test that all options have labels and descriptions."""
        questions = generate_socratic_questions(["scope", "goal"])

        for question in questions:
            for option in question.options:
                assert "label" in option
                assert "description" in option
                assert len(option["label"]) > 0


# =============================================================================
# TEST CASES: Prompt Engineering Keyword Detection
# =============================================================================

class TestTechniqueDetection:
    """Tests for prompt engineering technique detection (ask.md Section 5)."""

    def test_detect_chain_of_thought_korean(self):
        """Test CoT detection with Korean keywords."""
        assert detect_technique("단계별로 설명해줘") == "chain_of_thought"
        assert detect_technique("논리적으로 분석해") == "chain_of_thought"
        assert detect_technique("순서대로 진행해") == "chain_of_thought"
        assert detect_technique("차근차근 알려줘") == "chain_of_thought"

    def test_detect_chain_of_thought_english(self):
        """Test CoT detection with English keywords."""
        assert detect_technique("explain step-by-step") == "chain_of_thought"
        assert detect_technique("do it logical way") == "chain_of_thought"
        assert detect_technique("process it sequentially") == "chain_of_thought"

    def test_detect_few_shot_korean(self):
        """Test few-shot detection with Korean keywords."""
        assert detect_technique("예시를 보여줘") == "few_shot"
        assert detect_technique("예를 들면 어떻게 해?") == "few_shot"
        assert detect_technique("샘플 코드 줘") == "few_shot"

    def test_detect_few_shot_english(self):
        """Test few-shot detection with English keywords."""
        assert detect_technique("show me an example") == "few_shot"
        assert detect_technique("demonstrate how to do this") == "few_shot"
        assert detect_technique("give me a sample") == "few_shot"

    def test_detect_tree_of_thought_korean(self):
        """Test ToT detection with Korean keywords."""
        assert detect_technique("대안을 제시해줘") == "tree_of_thought"
        assert detect_technique("여러 방법을 비교해") == "tree_of_thought"
        assert detect_technique("옵션이 뭐가 있어?") == "tree_of_thought"

    def test_detect_tree_of_thought_english(self):
        """Test ToT detection with English keywords."""
        assert detect_technique("show alternatives") == "tree_of_thought"
        assert detect_technique("compare different options") == "tree_of_thought"
        assert detect_technique("multiple ways to do this") == "tree_of_thought"

    def test_detect_react_korean(self):
        """Test ReAct detection with Korean keywords."""
        assert detect_technique("행동하면서 배워") == "react"
        assert detect_technique("반복해서 시도해") == "react"
        assert detect_technique("실행하면서 수정해") == "react"

    def test_detect_react_english(self):
        """Test ReAct detection with English keywords."""
        assert detect_technique("take action and learn") == "react"
        assert detect_technique("iterate until done") == "react"
        assert detect_technique("try different approaches") == "react"

    def test_detect_self_consistency_korean(self):
        """Test self-consistency detection with Korean keywords."""
        assert detect_technique("확인해줘") == "self_consistency"
        assert detect_technique("검증이 필요해") == "self_consistency"

    def test_detect_self_consistency_english(self):
        """Test self-consistency detection with English keywords."""
        assert detect_technique("verify this result") == "self_consistency"
        assert detect_technique("validate the output") == "self_consistency"

    def test_detect_zero_shot_cot_korean(self):
        """Test zero-shot CoT detection with Korean keywords."""
        assert detect_technique("생각해보면 이게 맞아") == "zero_shot_cot"
        assert detect_technique("따져보면 어떨까") == "zero_shot_cot"

    def test_detect_zero_shot_cot_english(self):
        """Test zero-shot CoT detection with English keywords."""
        assert detect_technique("let's think about this") == "zero_shot_cot"
        assert detect_technique("reasoning through the problem") == "zero_shot_cot"

    def test_no_technique_detected(self):
        """Test inputs with no technique keywords."""
        assert detect_technique("그냥 해줘") is None
        assert detect_technique("just do it") is None
        assert detect_technique("코드 수정해") is None

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        assert detect_technique("STEP-BY-STEP") == "chain_of_thought"
        assert detect_technique("Step-By-Step") == "chain_of_thought"
        assert detect_technique("EXAMPLE please") == "few_shot"

    def test_parametrized_korean_inputs(self, sample_korean_inputs):
        """Parametrized test for Korean inputs."""
        for user_input, expected_technique in sample_korean_inputs:
            assert detect_technique(user_input) == expected_technique

    def test_parametrized_english_inputs(self, sample_english_inputs):
        """Parametrized test for English inputs."""
        for user_input, expected_technique in sample_english_inputs:
            assert detect_technique(user_input) == expected_technique


# =============================================================================
# TEST CASES: Intent Pattern Detection
# =============================================================================

class TestIntentPatternDetection:
    """Tests for intent pattern detection (ask.md Section 2)."""

    def test_detect_help_request_korean(self):
        """Test help request detection in Korean."""
        patterns = detect_intent_pattern("도와줘")
        assert "help_request" in patterns

        patterns = detect_intent_pattern("모르겠어")
        assert "help_request" in patterns

        patterns = detect_intent_pattern("헷갈려")
        assert "help_request" in patterns

    def test_detect_help_request_english(self):
        """Test help request detection in English."""
        patterns = detect_intent_pattern("help me")
        assert "help_request" in patterns

        patterns = detect_intent_pattern("I don't know how")
        assert "help_request" in patterns

    def test_detect_method_question_korean(self):
        """Test method question detection in Korean."""
        patterns = detect_intent_pattern("어떻게 해야 해?")
        assert "method_question" in patterns

        patterns = detect_intent_pattern("방법이 뭐야?")
        assert "method_question" in patterns

    def test_detect_method_question_english(self):
        """Test method question detection in English."""
        patterns = detect_intent_pattern("how do I do this?")
        assert "method_question" in patterns

    def test_detect_explanation_request_korean(self):
        """Test explanation request detection in Korean."""
        patterns = detect_intent_pattern("이게 뭐야?")
        assert "explanation_request" in patterns

        patterns = detect_intent_pattern("설명해줘")
        assert "explanation_request" in patterns

    def test_detect_explanation_request_english(self):
        """Test explanation request detection in English."""
        patterns = detect_intent_pattern("what is this?")
        assert "explanation_request" in patterns

        patterns = detect_intent_pattern("explain this")
        assert "explanation_request" in patterns

    def test_detect_guide_request_korean(self):
        """Test guide request detection in Korean."""
        patterns = detect_intent_pattern("알려줘")
        assert "guide_request" in patterns

        patterns = detect_intent_pattern("가르쳐줘")
        assert "guide_request" in patterns

    def test_detect_guide_request_english(self):
        """Test guide request detection in English."""
        patterns = detect_intent_pattern("guide me")
        assert "guide_request" in patterns

        patterns = detect_intent_pattern("show me a tutorial")
        assert "guide_request" in patterns

    def test_detect_multiple_patterns(self):
        """Test detection of multiple patterns in one input."""
        patterns = detect_intent_pattern("도와줘, 어떻게 해야해?")
        assert "help_request" in patterns
        assert "method_question" in patterns

    def test_no_pattern_detected(self):
        """Test input with no recognizable patterns."""
        patterns = detect_intent_pattern("코드 분석해")
        # Should return empty list (no help/method/explanation/guide patterns)
        assert len(patterns) == 0


# =============================================================================
# TEST CASES: Auto-Routing Decision Tree
# =============================================================================

class TestAutoRouting:
    """Tests for auto-routing decision tree (ask.md Section 7)."""

    def test_route_to_explore_agent_korean(self):
        """Test routing to Explore Agent with Korean keywords."""
        assert determine_route("코드 구조를 분석해줘") == "Explore Agent"
        assert determine_route("이 함수를 이해하고 싶어") == "Explore Agent"
        assert determine_route("프로젝트 구조를 탐색해줘") == "Explore Agent"

    def test_route_to_explore_agent_english(self):
        """Test routing to Explore Agent with English keywords."""
        assert determine_route("analyze the code structure") == "Explore Agent"
        assert determine_route("help me understand this") == "Explore Agent"
        assert determine_route("explore the project") == "Explore Agent"

    def test_route_to_plan_for_modification_korean(self):
        """Test routing to /plan for modification requests in Korean."""
        assert determine_route("버그를 수정해줘") == "/plan"
        assert determine_route("이 코드를 변경해") == "/plan"
        assert determine_route("새 기능을 추가해줘") == "/plan"

    def test_route_to_plan_for_modification_english(self):
        """Test routing to /plan for modification requests in English."""
        assert determine_route("fix this bug") == "/plan"
        assert determine_route("modify the code") == "/plan"
        assert determine_route("add a new feature") == "/plan"

    def test_route_to_audit_korean(self):
        """Test routing to /audit with Korean keywords."""
        assert determine_route("코드 검사해줘") == "/audit"
        assert determine_route("리뷰해줘") == "/audit"
        assert determine_route("품질을 확인해줘") == "/audit"

    def test_route_to_audit_english(self):
        """Test routing to /audit with English keywords."""
        assert determine_route("check this code") == "/audit"
        # Note: "review" triggers /audit; first-match wins
        assert determine_route("audit the module") == "/audit"
        assert determine_route("verify the output") == "/audit"

    def test_route_to_deep_audit_korean(self):
        """Test routing to /deep-audit with Korean keywords."""
        # Note: "분석" is in exploration keywords which comes first in INTENT_TO_ROUTE
        # For unambiguous /deep-audit routing, use only deep_analysis keywords
        assert determine_route("심층적으로 봐줘") == "/deep-audit"
        assert determine_route("깊이 있게 검토해") == "/deep-audit"
        assert determine_route("철저히 점검해줘") == "/deep-audit"

    def test_route_to_deep_audit_english(self):
        """Test routing to /deep-audit with English keywords."""
        assert determine_route("deep investigation needed") == "/deep-audit"
        # Note: "thorough" and "detailed" are deep_analysis keywords
        assert determine_route("thorough inspection") == "/deep-audit"
        assert determine_route("detailed investigation") == "/deep-audit"

    def test_route_to_plan_for_planning_korean(self):
        """Test routing to /plan for planning requests in Korean."""
        assert determine_route("계획을 세워줘") == "/plan"
        assert determine_route("아키텍처를 설계해줘") == "/plan"
        assert determine_route("구현해줘") == "/plan"

    def test_route_to_plan_for_planning_english(self):
        """Test routing to /plan for planning requests in English."""
        assert determine_route("plan the implementation") == "/plan"
        assert determine_route("design the architecture") == "/plan"
        assert determine_route("implement this feature") == "/plan"

    def test_stay_in_ask_for_ambiguous_korean(self):
        """Test staying in /ask for ambiguous Korean input."""
        assert determine_route("뭔가 해줘") == "/ask"
        assert determine_route("그거 좀") == "/ask"

    def test_stay_in_ask_for_ambiguous_english(self):
        """Test staying in /ask for ambiguous English input."""
        assert determine_route("do something") == "/ask"
        assert determine_route("please help") == "/ask"

    def test_parametrized_routing(self, sample_routing_inputs):
        """Parametrized test for routing inputs."""
        for user_input, expected_route in sample_routing_inputs:
            assert determine_route(user_input) == expected_route


# =============================================================================
# TEST CASES: Command Recommendation Logic
# =============================================================================

class TestCommandRecommendation:
    """Tests for command recommendation logic (ask.md Section 8)."""

    def test_explore_low_complexity(self):
        """Test recommendation for explore + low complexity."""
        assert recommend_skill("explore", "low") == "Direct Read"

    def test_explore_medium_complexity(self):
        """Test recommendation for explore + medium complexity."""
        assert recommend_skill("explore", "medium") == "Explore Agent"

    def test_explore_high_complexity(self):
        """Test recommendation for explore + high complexity."""
        assert recommend_skill("explore", "high") == "Explore Agent + /plan"

    def test_modify_low_complexity(self):
        """Test recommendation for modify + low complexity."""
        assert recommend_skill("modify", "low") == "Direct Edit"

    def test_modify_medium_complexity(self):
        """Test recommendation for modify + medium complexity."""
        assert recommend_skill("modify", "medium") == "/plan"

    def test_modify_high_complexity(self):
        """Test recommendation for modify + high complexity."""
        assert recommend_skill("modify", "high") == "/plan + /audit"

    def test_review_low_complexity(self):
        """Test recommendation for review + low complexity."""
        assert recommend_skill("review", "low") == "/audit"

    def test_review_medium_complexity(self):
        """Test recommendation for review + medium complexity."""
        assert recommend_skill("review", "medium") == "/audit"

    def test_review_high_complexity(self):
        """Test recommendation for review + high complexity."""
        assert recommend_skill("review", "high") == "/deep-audit"

    def test_unknown_combination_defaults_to_ask(self):
        """Test that unknown combinations default to /ask."""
        assert recommend_skill("unknown", "medium") == "/ask"
        assert recommend_skill("explore", "unknown") == "/ask"
        assert recommend_skill("random", "random") == "/ask"

    def test_all_matrix_combinations(self):
        """Test all combinations in the recommendation matrix."""
        for (intent, complexity), expected in RECOMMENDATION_MATRIX.items():
            assert recommend_skill(intent, complexity) == expected


# =============================================================================
# TEST CASES: Clarity Assessment
# =============================================================================

class TestClarityAssessment:
    """Tests for clarity assessment (ask.md Section 9)."""

    def test_clear_intent_high_score(self):
        """Test that clear intent gets high clarity score."""
        # Adding multiple clear keywords to ensure score > 0.6
        score = assess_clarity("코드를 분석하고 검사해줘")
        assert score >= 0.6

        score = assess_clarity("analyze and review the code structure in detail")
        assert score >= 0.6

    def test_unclear_intent_low_score(self):
        """Test that unclear intent gets low clarity score."""
        score = assess_clarity("뭔가 해줘")
        assert score < 0.6

        score = assess_clarity("그거 좀")
        assert score < 0.5

    def test_longer_input_bonus(self):
        """Test that longer inputs get slight bonus."""
        short_score = assess_clarity("분석해")
        long_score = assess_clarity("이 프로젝트의 전체 코드 구조를 분석해서 아키텍처를 파악해줘")

        # Long input should have higher or equal score
        assert long_score >= short_score

    def test_score_bounded_zero_to_one(self):
        """Test that score is always between 0 and 1."""
        test_inputs = [
            "",
            "a",
            "분석 검사 계획 구현 수정",  # Many clear keywords
            "뭔가 좀 그거 어떻게",  # Many unclear keywords
        ]

        for inp in test_inputs:
            score = assess_clarity(inp)
            assert 0.0 <= score <= 1.0

    def test_needs_clarification_below_threshold(self):
        """Test that low clarity triggers clarification need."""
        low_score = 0.5
        assert needs_clarification(low_score, threshold=0.7) is True

    def test_no_clarification_above_threshold(self):
        """Test that high clarity doesn't need clarification."""
        high_score = 0.8
        assert needs_clarification(high_score, threshold=0.7) is False

    def test_clarification_at_threshold(self):
        """Test behavior at exactly threshold."""
        threshold = 0.7
        assert needs_clarification(0.7, threshold=threshold) is False
        assert needs_clarification(0.69, threshold=threshold) is True


# =============================================================================
# TEST CASES: Edge Cases and Integration
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_input(self):
        """Test handling of empty input."""
        assert detect_technique("") is None
        assert detect_intent_pattern("") == []
        assert determine_route("") == "/ask"
        assert assess_clarity("") <= 0.5

    def test_whitespace_only_input(self):
        """Test handling of whitespace-only input."""
        assert detect_technique("   ") is None
        assert detect_intent_pattern("   ") == []
        assert determine_route("   ") == "/ask"

    def test_mixed_language_input(self):
        """Test handling of mixed Korean/English input."""
        # Korean keyword should be detected
        assert detect_technique("please 단계별로 explain") == "chain_of_thought"

        # First matching keyword determines route
        route = determine_route("코드를 analyze 해줘")
        assert route in ["Explore Agent", "/audit"]  # Either is valid

    def test_special_characters_in_input(self):
        """Test handling of special characters."""
        assert detect_technique("step-by-step!!!") == "chain_of_thought"
        assert detect_technique("예시@#$%를 보여줘") == "few_shot"

    def test_very_long_input(self):
        """Test handling of very long input."""
        long_input = "단계별로 " * 100 + "설명해줘"
        assert detect_technique(long_input) == "chain_of_thought"

        score = assess_clarity(long_input)
        assert 0.0 <= score <= 1.0

    def test_unicode_input(self):
        """Test handling of various Unicode characters."""
        assert detect_technique("예시를 보여줘 ") == "few_shot"
        assert detect_technique("step-by-step") == "chain_of_thought"

    def test_keyword_at_beginning_middle_end(self):
        """Test keyword detection at different positions."""
        # Beginning
        assert detect_technique("단계별로 하자") == "chain_of_thought"
        # Middle
        assert detect_technique("일단 단계별로 해보자") == "chain_of_thought"
        # End
        assert detect_technique("이건 단계별") == "chain_of_thought"


class TestIntegrationScenarios:
    """Integration tests for realistic user scenarios."""

    def test_scenario_code_review_request(self):
        """Test complete flow for code review request."""
        user_input = "이 PR의 코드를 리뷰해줘"

        # Should detect review intent
        route = determine_route(user_input)
        assert route == "/audit"

        # Should have reasonable clarity
        clarity = assess_clarity(user_input)
        assert clarity >= 0.5

        # Recommend based on medium complexity
        recommendation = recommend_skill("review", "medium")
        assert recommendation == "/audit"

    def test_scenario_feature_implementation(self):
        """Test complete flow for feature implementation request."""
        user_input = "새로운 로그인 기능을 구현해줘"

        # Should route to /plan
        route = determine_route(user_input)
        assert route == "/plan"

        # High clarity
        clarity = assess_clarity(user_input)
        assert clarity >= 0.5

        # Recommend for modify + high
        recommendation = recommend_skill("modify", "high")
        assert recommendation == "/plan + /audit"

    def test_scenario_help_request(self):
        """Test complete flow for help request."""
        user_input = "도와줘, 어떻게 해야 할지 모르겠어"

        # Should stay in /ask
        route = determine_route(user_input)
        assert route == "/ask"

        # Detect help pattern
        patterns = detect_intent_pattern(user_input)
        assert "help_request" in patterns

        # Low clarity should trigger clarification
        clarity = assess_clarity(user_input)
        assert needs_clarification(clarity)

    def test_scenario_step_by_step_analysis(self):
        """Test flow when user requests step-by-step analysis."""
        user_input = "코드 구조를 단계별로 분석해줘"

        # Should detect CoT technique
        technique = detect_technique(user_input)
        assert technique == "chain_of_thought"

        # Should route to Explore Agent
        route = determine_route(user_input)
        assert route == "Explore Agent"

    def test_scenario_ambiguous_then_clarified(self):
        """Test scenario where initial request is ambiguous."""
        # Initial ambiguous request
        initial_input = "그거 좀 해줘"

        # Should stay in /ask
        route = determine_route(initial_input)
        assert route == "/ask"

        # Should need clarification
        clarity = assess_clarity(initial_input)
        assert needs_clarification(clarity)

        # Generate clarification questions
        questions = generate_socratic_questions(["scope", "goal", "task_type"])
        assert len(questions) == 3

        # After clarification - include more clear keywords for higher clarity score
        clarified_input = "auth 모듈의 버그를 수정하고 검사해줘"

        # Should now route to /plan (modification keywords)
        route = determine_route(clarified_input)
        assert route == "/plan"

        # Higher clarity (with multiple clear keywords)
        clarity = assess_clarity(clarified_input)
        assert clarity >= 0.7  # More specific assertion


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
