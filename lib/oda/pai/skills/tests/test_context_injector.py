"""
Orion ODA PAI Skills - Context Injector Unit Tests

Tests for the Auto Full-Context-Injection System including:
- Reference loading for each skill type
- Plan file loading for resume scenarios
- Auto-detection of references from user input
- Integration with SkillRouter
- Edge cases and error handling

Reference: lib/oda/pai/skills/context_injector.py

Version: 1.0.0
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from lib.oda.pai.skills.context_injector import (
    ContextInjector,
    InjectedContext,
    InjectContextAction,
    REFERENCE_MAP,
    AUTO_DETECT_KEYWORDS,
    inject_context,
    get_default_injector,
    get_reference_map,
    WORKSPACE_ROOT,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace with reference files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create reference directory
        ref_dir = workspace / ".claude" / "references"
        ref_dir.mkdir(parents=True)

        # Create sample reference files
        (ref_dir / "3-stage-protocol.md").write_text(
            "# 3-Stage Protocol\n\n## Stage A: SCAN\nScan the codebase..."
        )
        (ref_dir / "governance-rules.md").write_text(
            "# Governance Rules\n\n## Blocked Patterns\n- rm -rf..."
        )
        (ref_dir / "delegation-patterns.md").write_text(
            "# Delegation Patterns\n\n## Task Delegation\nUse subagents..."
        )
        (ref_dir / "native-capabilities.md").write_text(
            "# Native Capabilities\n\n## Context Modes\n..."
        )
        (ref_dir / "pai-integration.md").write_text(
            "# PAI Integration\n\n## Overview\nPAI modules..."
        )
        (ref_dir / "intent-classification.md").write_text(
            "# Intent Classification\n\n## LLM-Native\n..."
        )
        (ref_dir / "orchestration-flow.md").write_text(
            "# Orchestration Flow\n\n## Main Agent\n..."
        )
        (ref_dir / "llm-agnostic-architecture.md").write_text(
            "# LLM-Agnostic Architecture\n\n## Proposal System\n..."
        )

        # Create plans directory
        plans_dir = workspace / ".agent" / "plans"
        plans_dir.mkdir(parents=True)

        # Create sample plan file
        (plans_dir / "test-plan.md").write_text(
            "# Plan: Test Plan\n\n## Metadata\nStatus: in_progress\n\n## Tasks\n- Task 1"
        )
        (plans_dir / "completed-plan.md").write_text(
            "# Plan: Completed Plan\n\n## Metadata\nStatus: completed\n\n## Tasks\n- Done"
        )

        yield workspace


@pytest.fixture
def injector(temp_workspace):
    """Create a ContextInjector with temporary workspace."""
    return ContextInjector(workspace_root=str(temp_workspace))


@pytest.fixture
def empty_injector():
    """Create a ContextInjector with non-existent workspace."""
    return ContextInjector(workspace_root="/nonexistent/path")


# =============================================================================
# TEST CASES: Reference Map Configuration
# =============================================================================

class TestReferenceMap:
    """Tests for REFERENCE_MAP configuration."""

    def test_reference_map_has_ask_skill(self):
        """Test that /ask skill has references."""
        assert "ask" in REFERENCE_MAP
        assert len(REFERENCE_MAP["ask"]) >= 1
        assert any("native-capabilities" in ref for ref in REFERENCE_MAP["ask"])

    def test_reference_map_has_plan_skill(self):
        """Test that /plan skill has references."""
        assert "plan" in REFERENCE_MAP
        assert len(REFERENCE_MAP["plan"]) >= 2
        assert any("3-stage-protocol" in ref for ref in REFERENCE_MAP["plan"])
        assert any("delegation-patterns" in ref for ref in REFERENCE_MAP["plan"])

    def test_reference_map_has_audit_skill(self):
        """Test that /audit skill has references."""
        assert "audit" in REFERENCE_MAP
        assert len(REFERENCE_MAP["audit"]) >= 2
        assert any("3-stage-protocol" in ref for ref in REFERENCE_MAP["audit"])
        assert any("governance-rules" in ref for ref in REFERENCE_MAP["audit"])

    def test_reference_map_has_deep_audit_skill(self):
        """Test that /deep-audit skill has references."""
        assert "deep-audit" in REFERENCE_MAP
        assert len(REFERENCE_MAP["deep-audit"]) >= 2

    def test_all_references_are_valid_paths(self):
        """Test that all references follow expected path pattern."""
        for skill, refs in REFERENCE_MAP.items():
            for ref in refs:
                assert ref.startswith(".claude/references/")
                assert ref.endswith(".md")

    def test_get_reference_map_returns_copy(self):
        """Test that get_reference_map returns a copy."""
        map1 = get_reference_map()
        map2 = get_reference_map()

        # Modify one
        map1["test"] = ["test.md"]

        # Other should be unchanged
        assert "test" not in map2


class TestAutoDetectKeywords:
    """Tests for AUTO_DETECT_KEYWORDS configuration."""

    def test_protocol_keywords_exist(self):
        """Test that protocol-related keywords are configured."""
        assert "protocol" in AUTO_DETECT_KEYWORDS
        assert "stage" in AUTO_DETECT_KEYWORDS
        assert "scan" in AUTO_DETECT_KEYWORDS

    def test_governance_keywords_exist(self):
        """Test that governance-related keywords are configured."""
        assert "governance" in AUTO_DETECT_KEYWORDS
        assert "proposal" in AUTO_DETECT_KEYWORDS
        assert "hazardous" in AUTO_DETECT_KEYWORDS

    def test_delegation_keywords_exist(self):
        """Test that delegation-related keywords are configured."""
        assert "delegate" in AUTO_DETECT_KEYWORDS
        assert "subagent" in AUTO_DETECT_KEYWORDS

    def test_pai_keywords_exist(self):
        """Test that PAI-related keywords are configured."""
        assert "pai" in AUTO_DETECT_KEYWORDS
        assert "trait" in AUTO_DETECT_KEYWORDS


# =============================================================================
# TEST CASES: ContextInjector Initialization
# =============================================================================

class TestContextInjectorInit:
    """Tests for ContextInjector initialization."""

    def test_default_initialization(self):
        """Test default initialization."""
        injector = ContextInjector()
        assert injector.workspace_root == Path(WORKSPACE_ROOT)
        assert injector.reference_map == REFERENCE_MAP
        assert injector.enable_cache is True

    def test_custom_workspace_root(self, temp_workspace):
        """Test initialization with custom workspace root."""
        injector = ContextInjector(workspace_root=str(temp_workspace))
        assert injector.workspace_root == temp_workspace

    def test_custom_reference_map(self):
        """Test initialization with custom reference map."""
        custom_map = {"custom": ["custom.md"]}
        injector = ContextInjector(reference_map=custom_map)
        assert injector.reference_map == custom_map

    def test_disable_cache(self):
        """Test initialization with cache disabled."""
        injector = ContextInjector(enable_cache=False)
        assert injector.enable_cache is False

    def test_get_default_injector(self):
        """Test get_default_injector convenience function."""
        injector = get_default_injector()
        assert isinstance(injector, ContextInjector)


# =============================================================================
# TEST CASES: Reference Loading
# =============================================================================

class TestReferenceLoading:
    """Tests for reference file loading."""

    def test_load_existing_reference(self, injector, temp_workspace):
        """Test loading an existing reference file."""
        content = injector._load_reference(".claude/references/3-stage-protocol.md")
        assert content is not None
        assert "3-Stage Protocol" in content
        assert "Stage A" in content

    def test_load_nonexistent_reference(self, injector):
        """Test loading a non-existent reference file."""
        content = injector._load_reference(".claude/references/nonexistent.md")
        assert content is None

    def test_reference_caching(self, injector, temp_workspace):
        """Test that references are cached."""
        ref_path = ".claude/references/3-stage-protocol.md"

        # First load
        content1 = injector._load_reference(ref_path)
        assert content1 is not None
        assert ref_path in injector._cache

        # Second load should use cache
        content2 = injector._load_reference(ref_path)
        assert content1 == content2

    def test_cache_disabled(self, temp_workspace):
        """Test loading without cache."""
        injector = ContextInjector(
            workspace_root=str(temp_workspace),
            enable_cache=False
        )

        ref_path = ".claude/references/3-stage-protocol.md"
        content = injector._load_reference(ref_path)
        assert content is not None
        assert ref_path not in injector._cache

    def test_clear_cache(self, injector, temp_workspace):
        """Test cache clearing."""
        ref_path = ".claude/references/3-stage-protocol.md"
        injector._load_reference(ref_path)
        assert len(injector._cache) > 0

        injector.clear_cache()
        assert len(injector._cache) == 0

    def test_preload_references(self, injector, temp_workspace):
        """Test preloading references."""
        loaded = injector.preload_references(["plan"])
        assert loaded >= 1
        assert len(injector._cache) >= 1


# =============================================================================
# TEST CASES: Plan File Loading
# =============================================================================

class TestPlanFileLoading:
    """Tests for plan file loading."""

    def test_load_existing_plan_file(self, injector, temp_workspace):
        """Test loading an existing plan file."""
        content = injector._load_plan_file("test-plan")
        assert content is not None
        assert "Test Plan" in content
        assert "in_progress" in content

    def test_load_nonexistent_plan_file(self, injector):
        """Test loading a non-existent plan file."""
        content = injector._load_plan_file("nonexistent-plan")
        assert content is None

    def test_detect_active_plan(self, injector, temp_workspace):
        """Test active plan detection."""
        active = injector._detect_active_plan()
        assert active == "test-plan"

    def test_detect_no_active_plan(self, empty_injector):
        """Test when no active plan exists."""
        active = empty_injector._detect_active_plan()
        assert active is None

    def test_auto_load_active_plan(self, injector, temp_workspace):
        """Test auto-loading active plan when no slug provided."""
        content = injector._load_plan_file(None)
        assert content is not None
        assert "Test Plan" in content


# =============================================================================
# TEST CASES: Context Injection
# =============================================================================

class TestContextInjection:
    """Tests for context injection."""

    def test_inject_for_audit_skill(self, injector, temp_workspace):
        """Test injection for /audit skill."""
        context = injector.inject("audit")

        assert context.skill_name == "audit"
        assert context.success
        assert len(context.references_loaded) >= 2
        assert any("3-stage-protocol" in ref for ref in context.references_loaded)
        assert any("governance-rules" in ref for ref in context.references_loaded)

    def test_inject_for_plan_skill(self, injector, temp_workspace):
        """Test injection for /plan skill."""
        context = injector.inject("plan")

        assert context.skill_name == "plan"
        assert context.success
        assert any("delegation-patterns" in ref for ref in context.references_loaded)

    def test_inject_for_ask_skill(self, injector, temp_workspace):
        """Test injection for /ask skill."""
        context = injector.inject("ask")

        assert context.skill_name == "ask"
        assert context.success
        assert any("native-capabilities" in ref for ref in context.references_loaded)

    def test_inject_for_unknown_skill(self, injector):
        """Test injection for unknown skill."""
        context = injector.inject("unknown-skill")

        assert context.skill_name == "unknown-skill"
        assert len(context.references_loaded) == 0

    def test_inject_with_user_input_auto_detection(self, injector, temp_workspace):
        """Test injection with auto-detection from user input."""
        context = injector.inject(
            "ask",
            user_input="protocol stage A를 실행해줘"
        )

        # Should detect protocol/stage keywords
        assert len(context.auto_detected) >= 1
        assert any("3-stage-protocol" in ref for ref in context.auto_detected)

    def test_inject_with_plan_file(self, injector, temp_workspace):
        """Test injection including plan file."""
        context = injector.inject("audit", include_plan=True)

        assert context.plan_file is not None
        assert "Plan" in context.content

    def test_inject_without_plan_file(self, injector, temp_workspace):
        """Test injection excluding plan file."""
        context = injector.inject("audit", include_plan=False)

        assert context.plan_file is None

    def test_inject_with_specific_plan_slug(self, injector, temp_workspace):
        """Test injection with specific plan slug."""
        context = injector.inject(
            "audit",
            include_plan=True,
            plan_slug="test-plan"
        )

        assert context.plan_file == "test-plan"


class TestInjectedContext:
    """Tests for InjectedContext dataclass."""

    def test_success_property_with_content(self):
        """Test success property when content exists."""
        context = InjectedContext(
            skill_name="test",
            content="Some content"
        )
        assert context.success is True

    def test_success_property_without_content(self):
        """Test success property when content is empty."""
        context = InjectedContext(
            skill_name="test",
            content=""
        )
        assert context.success is False

    def test_reference_count_property(self):
        """Test reference_count property."""
        context = InjectedContext(
            skill_name="test",
            references_loaded=["ref1.md", "ref2.md", "ref3.md"]
        )
        assert context.reference_count == 3

    def test_to_prompt_prefix_with_content(self):
        """Test prompt prefix generation with content."""
        context = InjectedContext(
            skill_name="audit",
            references_loaded=["ref1.md"],
            content="Reference content here"
        )

        prefix = context.to_prompt_prefix()
        assert "## Injected Context for /audit" in prefix
        assert "ref1.md" in prefix
        assert "Reference content here" in prefix

    def test_to_prompt_prefix_without_content(self):
        """Test prompt prefix generation without content."""
        context = InjectedContext(
            skill_name="test",
            content=""
        )

        prefix = context.to_prompt_prefix()
        assert prefix == ""

    def test_to_prompt_prefix_with_plan_file(self):
        """Test prompt prefix includes plan file."""
        context = InjectedContext(
            skill_name="test",
            plan_file="my-plan",
            content="Content"
        )

        prefix = context.to_prompt_prefix()
        assert "Active Plan File" in prefix
        assert "my-plan" in prefix

    def test_to_prompt_prefix_with_auto_detected(self):
        """Test prompt prefix includes auto-detected references."""
        context = InjectedContext(
            skill_name="test",
            auto_detected=["auto1.md", "auto2.md"],
            content="Content"
        )

        prefix = context.to_prompt_prefix()
        assert "Auto-Detected References" in prefix
        assert "auto1.md" in prefix


# =============================================================================
# TEST CASES: Auto-Detection
# =============================================================================

class TestAutoDetection:
    """Tests for auto-detection of references from user input."""

    def test_detect_protocol_keywords(self, injector):
        """Test detection of protocol keywords."""
        refs = injector.auto_detect_references("protocol stage A 실행")
        assert any("3-stage-protocol" in ref for ref in refs)

    def test_detect_governance_keywords(self, injector):
        """Test detection of governance keywords."""
        refs = injector.auto_detect_references("governance proposal 검토")
        assert any("governance-rules" in ref for ref in refs)

    def test_detect_delegation_keywords(self, injector):
        """Test detection of delegation keywords."""
        refs = injector.auto_detect_references("delegate to subagent")
        assert any("delegation-patterns" in ref for ref in refs)

    def test_detect_pai_keywords(self, injector):
        """Test detection of PAI keywords."""
        refs = injector.auto_detect_references("pai trait 설정")
        assert any("pai-integration" in ref for ref in refs)

    def test_detect_intent_keywords(self, injector):
        """Test detection of intent keywords."""
        refs = injector.auto_detect_references("classify user intent")
        assert any("intent-classification" in ref for ref in refs)

    def test_detect_multiple_keywords(self, injector):
        """Test detection of multiple keywords."""
        refs = injector.auto_detect_references(
            "protocol governance delegate"
        )
        assert len(refs) >= 2

    def test_no_detection_for_generic_input(self, injector):
        """Test no detection for generic input."""
        refs = injector.auto_detect_references("코드를 수정해줘")
        assert len(refs) == 0

    def test_empty_input_returns_empty(self, injector):
        """Test empty input returns empty list."""
        refs = injector.auto_detect_references("")
        assert refs == []

    def test_case_insensitive_detection(self, injector):
        """Test case-insensitive detection."""
        refs_lower = injector.auto_detect_references("protocol")
        refs_upper = injector.auto_detect_references("PROTOCOL")
        refs_mixed = injector.auto_detect_references("Protocol")

        assert refs_lower == refs_upper == refs_mixed


# =============================================================================
# TEST CASES: Skill Reference Management
# =============================================================================

class TestSkillReferenceManagement:
    """Tests for skill reference management."""

    def test_get_skill_references(self, injector):
        """Test getting references for a skill."""
        refs = injector.get_skill_references("audit")
        assert len(refs) >= 2
        assert any("3-stage-protocol" in ref for ref in refs)

    def test_get_skill_references_unknown(self, injector):
        """Test getting references for unknown skill."""
        refs = injector.get_skill_references("unknown")
        assert refs == []

    def test_add_skill_reference(self, injector):
        """Test adding a reference to a skill."""
        injector.add_skill_reference("custom", "custom.md")
        refs = injector.get_skill_references("custom")
        assert "custom.md" in refs

    def test_add_skill_reference_no_duplicate(self, injector):
        """Test that duplicate references are not added."""
        injector.add_skill_reference("custom", "custom.md")
        injector.add_skill_reference("custom", "custom.md")
        refs = injector.get_skill_references("custom")
        assert refs.count("custom.md") == 1


# =============================================================================
# TEST CASES: InjectContextAction
# =============================================================================

class TestInjectContextAction:
    """Tests for InjectContextAction."""

    def test_action_metadata(self):
        """Test action metadata."""
        assert InjectContextAction.api_name == "inject_context"
        assert InjectContextAction.is_hazardous is False

    def test_action_execute(self, temp_workspace):
        """Test action execution."""
        injector = ContextInjector(workspace_root=str(temp_workspace))
        action = InjectContextAction(
            skill_name="audit",
            user_input="protocol 실행",
            injector=injector
        )

        result = action.execute()
        assert isinstance(result, InjectedContext)
        assert result.skill_name == "audit"
        assert result.success

    def test_action_default_injector(self):
        """Test action with default injector."""
        action = InjectContextAction(
            skill_name="ask",
            user_input=""
        )
        assert action.injector is not None


# =============================================================================
# TEST CASES: Convenience Functions
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_inject_context_function(self):
        """Test inject_context convenience function."""
        with patch.object(ContextInjector, 'inject') as mock_inject:
            mock_inject.return_value = InjectedContext(
                skill_name="test",
                content="content"
            )
            result = inject_context("test", "input", True)
            assert isinstance(result, InjectedContext)

    def test_get_reference_map_function(self):
        """Test get_reference_map convenience function."""
        ref_map = get_reference_map()
        assert isinstance(ref_map, dict)
        assert "audit" in ref_map


# =============================================================================
# TEST CASES: Router Integration
# =============================================================================

class TestRouterIntegration:
    """Tests for integration with SkillRouter."""

    def test_router_has_context_injector(self):
        """Test that SkillRouter has a ContextInjector."""
        from lib.oda.pai.skills.router import SkillRouter

        router = SkillRouter()
        assert hasattr(router, '_context_injector')
        assert isinstance(router._context_injector, ContextInjector)

    def test_route_result_has_injected_context(self):
        """Test that RouteResult includes injected_context field."""
        from lib.oda.pai.skills.router import RouteResult

        result = RouteResult(matched=True)
        assert hasattr(result, 'injected_context')


# =============================================================================
# TEST CASES: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_unicode_in_user_input(self, injector):
        """Test handling of unicode in user input."""
        refs = injector.auto_detect_references("protocol 프로토콜 ")
        assert isinstance(refs, list)

    def test_very_long_user_input(self, injector):
        """Test handling of very long user input."""
        long_input = "protocol " * 1000
        refs = injector.auto_detect_references(long_input)
        assert isinstance(refs, list)

    def test_special_characters_in_input(self, injector):
        """Test handling of special characters."""
        refs = injector.auto_detect_references("protocol!@#$%^&*()")
        assert isinstance(refs, list)

    def test_whitespace_only_input(self, injector):
        """Test handling of whitespace-only input."""
        refs = injector.auto_detect_references("   \n\t  ")
        assert refs == []

    def test_none_workspace_root(self):
        """Test initialization with None workspace root uses default."""
        injector = ContextInjector(workspace_root=None)
        assert injector.workspace_root == Path(WORKSPACE_ROOT)

    def test_file_read_error_handling(self, temp_workspace):
        """Test handling of file read errors."""
        injector = ContextInjector(workspace_root=str(temp_workspace))

        # Create a file that can't be read (simulate error)
        with patch('pathlib.Path.read_text', side_effect=PermissionError("Access denied")):
            content = injector._load_reference(".claude/references/3-stage-protocol.md")
            assert content is None

    def test_error_tracking_in_context(self, injector):
        """Test that errors are tracked in context."""
        context = injector.inject("audit")
        # With temp workspace, some references might not exist
        assert isinstance(context.errors, list)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
