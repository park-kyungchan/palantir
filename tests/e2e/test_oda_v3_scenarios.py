"""
ODA V3.0 End-to-End Test Scenarios
==================================

Tests the complete workflow of the Ontology-Driven Architecture:
1. Object Lifecycle (Create → Modify → Archive → Delete)
2. Action Execution (Validation → Commit → Side Effects)
3. Proposal Governance (Draft → Pending → Approve/Reject → Execute)
4. Router Intelligence (Local vs Relay routing decisions)
5. Concurrent Operations (Race condition handling)

Run with: pytest tests/e2e/test_oda_v3_scenarios.py -v --asyncio-mode=auto
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import ODA V3 modules
from scripts.ontology.ontology_types import (
    Cardinality,
    Link,
    ObjectStatus,
    OntologyObject,
    PropertyType,
    generate_object_id,
)
from scripts.ontology.objects.proposal import (
    InvalidTransitionError,
    Proposal,
    ProposalPriority,
    ProposalStatus,
    VALID_TRANSITIONS,
)
from scripts.ontology.actions import (
    ActionContext,
    ActionRegistry,
    ActionResult,
    ActionType,
    AllowedValues,
    CustomValidator,
    EditOperation,
    EditType,
    LogSideEffect,
    MaxLength,
    RequiredField,
    ValidationError,
    action_registry,
    register_action,
)
from scripts.llm.ollama_client import (
    HybridLLMService,
    HybridRouter,
    OllamaClient,
    OllamaResponse,
    RouterConfig,
    RoutingDecision,
    RouteTarget,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def system_context() -> ActionContext:
    """Create a system-level action context."""
    return ActionContext.system()


@pytest.fixture
def user_context() -> ActionContext:
    """Create a user action context."""
    return ActionContext(
        actor_id="user-001",
        correlation_id="test-correlation-123",
        metadata={"source": "pytest"}
    )


@pytest.fixture
def admin_context() -> ActionContext:
    """Create an admin action context."""
    return ActionContext(
        actor_id="admin-001",
        metadata={"role": "administrator"}
    )


@pytest.fixture
def router_config() -> RouterConfig:
    """Create a test router configuration."""
    return RouterConfig(
        word_threshold=30,
        sentence_threshold=3,
        critical_keywords=["delete", "deploy", "production", "database"],
        technical_terms=["api", "microservice"],
        ollama_base_url="http://localhost:11434",
        ollama_model="llama3.2",
        ollama_timeout=10.0,
        ollama_max_retries=1,
    )


@pytest.fixture
def temp_config_file(router_config: RouterConfig) -> Path:
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(router_config.model_dump_json())
        return Path(f.name)


# =============================================================================
# SCENARIO 1: ONTOLOGY OBJECT LIFECYCLE
# =============================================================================

class TestOntologyObjectLifecycle:
    """Test OntologyObject creation, modification, and deletion."""
    
    def test_object_creation_generates_uuid(self):
        """Verify that new objects get unique UUIDs."""
        obj1 = OntologyObject()
        obj2 = OntologyObject()
        
        assert obj1.id != obj2.id
        assert len(obj1.id) == 36  # UUID format
        assert obj1.version == 1
        assert obj1.status == ObjectStatus.ACTIVE
    
    def test_object_audit_fields_populated(self):
        """Verify audit fields are set on creation."""
        before = datetime.now(timezone.utc)
        obj = OntologyObject(created_by="agent-001")
        after = datetime.now(timezone.utc)
        
        assert obj.created_by == "agent-001"
        assert before <= obj.created_at <= after
        assert abs(obj.updated_at - obj.created_at) < timedelta(seconds=0.1)
    
    def test_touch_updates_version_and_timestamp(self):
        """Verify touch() increments version and updates timestamp."""
        obj = OntologyObject()
        original_version = obj.version
        original_updated_at = obj.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        obj.touch(updated_by="modifier-001")
        
        assert obj.version == original_version + 1
        assert obj.updated_at > original_updated_at
        assert obj.updated_by == "modifier-001"
    
    def test_soft_delete_sets_status(self):
        """Verify soft_delete() changes status to DELETED."""
        obj = OntologyObject()
        assert obj.is_active
        
        obj.soft_delete(deleted_by="admin-001")
        
        assert obj.status == ObjectStatus.DELETED
        assert not obj.is_active
        assert obj.updated_by == "admin-001"
    
    def test_archive_sets_status(self):
        """Verify archive() changes status to ARCHIVED."""
        obj = OntologyObject()
        
        obj.archive(archived_by="system")
        
        assert obj.status == ObjectStatus.ARCHIVED
        assert not obj.is_active


# =============================================================================
# SCENARIO 2: LINK TYPE VALIDATION
# =============================================================================

class TestLinkTypeDefinition:
    """Test Link type definitions and cardinality."""
    
    def test_link_creation_with_cardinality(self):
        """Verify Link accepts valid cardinality values."""
        link = Link(
            target=OntologyObject,
            link_type_id="parent_child",
            cardinality=Cardinality.ONE_TO_MANY,
        )
        
        assert link.cardinality == Cardinality.ONE_TO_MANY
        assert link.link_type_id == "parent_child"
    
    def test_link_type_id_validation(self):
        """Verify link_type_id must be snake_case."""
        # Valid
        Link(target=OntologyObject, link_type_id="valid_link_id")
        
        # Invalid (contains space)
        with pytest.raises(ValueError, match="snake_case"):
            Link(target=OntologyObject, link_type_id="invalid link")
    
    def test_all_cardinality_values(self):
        """Verify all Cardinality enum values."""
        assert Cardinality.ONE_TO_ONE.value == "1:1"
        assert Cardinality.ONE_TO_MANY.value == "1:N"
        assert Cardinality.MANY_TO_MANY.value == "N:N"


# =============================================================================
# SCENARIO 3: PROPOSAL STATE MACHINE
# =============================================================================

class TestProposalStateMachine:
    """Test Proposal lifecycle and state transitions."""
    
    def test_proposal_creation_defaults_to_draft(self):
        """Verify new proposals start in DRAFT status."""
        proposal = Proposal(
            action_type="create_task",
            created_by="agent-001"
        )
        
        assert proposal.status == ProposalStatus.DRAFT
        assert not proposal.is_terminal
    
    def test_valid_transition_draft_to_pending(self):
        """Verify DRAFT → PENDING transition works."""
        proposal = Proposal(action_type="test", created_by="x")
        
        proposal.submit()
        
        assert proposal.status == ProposalStatus.PENDING
        assert proposal.is_pending_review
    
    def test_valid_transition_pending_to_approved(self):
        """Verify PENDING → APPROVED transition works."""
        proposal = Proposal(action_type="test", created_by="x")
        proposal.submit()
        
        proposal.approve(reviewer_id="admin-001", comment="LGTM")
        
        assert proposal.status == ProposalStatus.APPROVED
        assert proposal.reviewed_by == "admin-001"
        assert proposal.review_comment == "LGTM"
        assert proposal.reviewed_at is not None
        assert proposal.can_execute
    
    def test_valid_transition_pending_to_rejected(self):
        """Verify PENDING → REJECTED transition works."""
        proposal = Proposal(action_type="test", created_by="x")
        proposal.submit()
        
        proposal.reject(reviewer_id="admin-001", reason="Not ready")
        
        assert proposal.status == ProposalStatus.REJECTED
        assert proposal.is_terminal
    
    def test_valid_transition_approved_to_executed(self):
        """Verify APPROVED → EXECUTED transition works."""
        proposal = Proposal(action_type="test", created_by="x")
        proposal.submit()
        proposal.approve(reviewer_id="admin-001")
        
        proposal.execute(result={"success": True})
        
        assert proposal.status == ProposalStatus.EXECUTED
        assert proposal.is_terminal
        assert proposal.executed_at is not None
        assert proposal.execution_result == {"success": True}
    
    def test_invalid_transition_draft_to_approved(self):
        """Verify DRAFT → APPROVED is blocked."""
        proposal = Proposal(action_type="test", created_by="x")
        
        with pytest.raises(InvalidTransitionError) as exc_info:
            proposal.approve(reviewer_id="admin-001")
        
        assert "draft" in str(exc_info.value).lower()
        assert "approved" in str(exc_info.value).lower()
    
    def test_invalid_transition_rejected_to_approved(self):
        """Verify REJECTED → APPROVED is blocked (terminal state)."""
        proposal = Proposal(action_type="test", created_by="x")
        proposal.submit()
        proposal.reject(reviewer_id="admin-001", reason="No")
        
        with pytest.raises(InvalidTransitionError):
            proposal.approve(reviewer_id="admin-002")
    
    def test_cancel_from_multiple_states(self):
        """Verify cancellation works from non-terminal states."""
        # From DRAFT
        p1 = Proposal(action_type="test", created_by="x")
        p1.cancel(canceller_id="user-001", reason="Changed mind")
        assert p1.status == ProposalStatus.CANCELLED
        
        # From PENDING
        p2 = Proposal(action_type="test", created_by="x")
        p2.submit()
        p2.cancel(canceller_id="user-001")
        assert p2.status == ProposalStatus.CANCELLED
        
        # From APPROVED (before execution)
        p3 = Proposal(action_type="test", created_by="x")
        p3.submit()
        p3.approve(reviewer_id="admin-001")
        p3.cancel(canceller_id="user-001")
        assert p3.status == ProposalStatus.CANCELLED
    
    def test_approve_requires_reviewer_id(self):
        """Verify approve() requires reviewer_id."""
        proposal = Proposal(action_type="test", created_by="x")
        proposal.submit()
        
        with pytest.raises(ValueError, match="reviewer_id"):
            proposal.approve(reviewer_id="")
    
    def test_reject_requires_reason(self):
        """Verify reject() requires reason."""
        proposal = Proposal(action_type="test", created_by="x")
        proposal.submit()
        
        with pytest.raises(ValueError, match="reason"):
            proposal.reject(reviewer_id="admin-001", reason="")
    
    def test_audit_log_generation(self):
        """Verify audit log contains all relevant fields."""
        proposal = Proposal(
            action_type="deploy_service",
            payload={"service": "checkout"},
            created_by="agent-001",
            priority=ProposalPriority.HIGH,
        )
        proposal.submit()
        proposal.approve(reviewer_id="admin-001", comment="Approved")
        
        audit = proposal.to_audit_log()
        
        assert audit["proposal_id"] == proposal.id
        assert audit["action_type"] == "deploy_service"
        assert audit["status"] == "approved"
        assert audit["priority"] == "high"
        assert audit["reviewed_by"] == "admin-001"


# =============================================================================
# SCENARIO 4: SUBMISSION CRITERIA VALIDATION
# =============================================================================

class TestSubmissionCriteria:
    """Test ActionType submission criteria validators."""
    
    def test_required_field_passes(self, system_context):
        """Verify RequiredField passes for non-empty value."""
        validator = RequiredField("title")
        
        result = validator.validate({"title": "My Task"}, system_context)
        
        assert result is True
    
    def test_required_field_fails_empty(self, system_context):
        """Verify RequiredField fails for empty string."""
        validator = RequiredField("title")
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({"title": ""}, system_context)
        
        assert "required" in str(exc_info.value).lower()
    
    def test_required_field_fails_missing(self, system_context):
        """Verify RequiredField fails for missing key."""
        validator = RequiredField("title")
        
        with pytest.raises(ValidationError):
            validator.validate({}, system_context)
    
    def test_allowed_values_passes(self, system_context):
        """Verify AllowedValues passes for valid value."""
        validator = AllowedValues("priority", ["low", "medium", "high"])
        
        result = validator.validate({"priority": "high"}, system_context)
        
        assert result is True
    
    def test_allowed_values_fails(self, system_context):
        """Verify AllowedValues fails for invalid value."""
        validator = AllowedValues("priority", ["low", "medium", "high"])
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({"priority": "urgent"}, system_context)
        
        assert "allowed values" in str(exc_info.value).lower()
    
    def test_max_length_passes(self, system_context):
        """Verify MaxLength passes for short string."""
        validator = MaxLength("title", 100)
        
        result = validator.validate({"title": "Short title"}, system_context)
        
        assert result is True
    
    def test_max_length_fails(self, system_context):
        """Verify MaxLength fails for long string."""
        validator = MaxLength("title", 10)
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({"title": "This is a very long title"}, system_context)
        
        assert "max length" in str(exc_info.value).lower()
    
    def test_custom_validator_passes(self, system_context):
        """Verify CustomValidator with passing function."""
        validator = CustomValidator(
            name="EvenNumber",
            validator_fn=lambda p, c: p.get("count", 0) % 2 == 0,
            error_message="Count must be even"
        )
        
        result = validator.validate({"count": 4}, system_context)
        
        assert result is True
    
    def test_custom_validator_fails(self, system_context):
        """Verify CustomValidator with failing function."""
        validator = CustomValidator(
            name="EvenNumber",
            validator_fn=lambda p, c: p.get("count", 0) % 2 == 0,
            error_message="Count must be even"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({"count": 3}, system_context)
        
        assert "even" in str(exc_info.value).lower()


# =============================================================================
# SCENARIO 5: ACTION EXECUTION FLOW
# =============================================================================

class TestActionExecution:
    """Test ActionType execution with validation and side effects."""
    
    @pytest.fixture
    def mock_action_class(self):
        """Create a mock ActionType for testing."""
        
        class MockAction(ActionType[OntologyObject]):
            api_name = "mock_action"
            object_type = OntologyObject
            submission_criteria = [
                RequiredField("name"),
                MaxLength("name", 50),
            ]
            side_effects = [LogSideEffect()]
            
            async def apply_edits(self, params, context):
                obj = OntologyObject(created_by=context.actor_id)
                edit = EditOperation(
                    edit_type=EditType.CREATE,
                    object_type="OntologyObject",
                    object_id=obj.id,
                    changes=params,
                )
                return obj, [edit]
        
        return MockAction
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, mock_action_class, user_context):
        """Verify successful action execution flow."""
        action = mock_action_class()
        
        result = await action.execute(
            params={"name": "Test Object"},
            context=user_context
        )
        
        assert result.success is True
        assert result.action_type == "mock_action"
        assert len(result.created_ids) == 1
        assert len(result.edits) == 1
        assert result.edits[0].edit_type == EditType.CREATE
    
    @pytest.mark.asyncio
    async def test_validation_failure(self, mock_action_class, user_context):
        """Verify action fails on validation error."""
        action = mock_action_class()
        
        result = await action.execute(
            params={"name": ""},  # Empty - will fail RequiredField
            context=user_context
        )
        
        assert result.success is False
        assert "criteria" in result.error.lower() or "validation" in result.error.lower()
        assert "validation_errors" in result.error_details
    
    @pytest.mark.asyncio
    async def test_side_effects_execute_after_commit(self, mock_action_class, user_context):
        """Verify side effects run after successful commit."""
        action = mock_action_class()
        
        with patch.object(LogSideEffect, 'execute', new_callable=AsyncMock) as mock_effect:
            result = await action.execute(
                params={"name": "Test"},
                context=user_context
            )
            
            assert result.success is True
            mock_effect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_side_effects_not_run_on_failure(self, mock_action_class, user_context):
        """Verify side effects don't run on validation failure."""
        action = mock_action_class()
        
        with patch.object(LogSideEffect, 'execute', new_callable=AsyncMock) as mock_effect:
            result = await action.execute(
                params={"name": ""},  # Will fail
                context=user_context
            )
            
            assert result.success is False
            mock_effect.assert_not_called()


# =============================================================================
# SCENARIO 6: ACTION REGISTRY
# =============================================================================

class TestActionRegistry:
    """Test ActionRegistry registration and lookup."""
    
    def test_register_and_get(self):
        """Verify action registration and retrieval."""
        registry = ActionRegistry()
        
        class TestAction(ActionType[OntologyObject]):
            api_name = "test_action"
            object_type = OntologyObject
            
            async def apply_edits(self, params, context):
                return None, []
        
        registry.register(TestAction)
        
        retrieved = registry.get("test_action")
        assert retrieved is TestAction
    
    def test_list_actions(self):
        """Verify listing registered actions."""
        registry = ActionRegistry()
        
        class Action1(ActionType[OntologyObject]):
            api_name = "action_1"
            object_type = OntologyObject
            async def apply_edits(self, params, context): return None, []
        
        class Action2(ActionType[OntologyObject]):
            api_name = "action_2"
            object_type = OntologyObject
            async def apply_edits(self, params, context): return None, []
        
        registry.register(Action1)
        registry.register(Action2)
        
        actions = registry.list_actions()
        assert "action_1" in actions
        assert "action_2" in actions
    
    def test_get_hazardous_actions(self):
        """Verify filtering hazardous actions."""
        registry = ActionRegistry()
        
        class SafeAction(ActionType[OntologyObject]):
            api_name = "safe_action"
            object_type = OntologyObject
            requires_proposal = False
            async def apply_edits(self, params, context): return None, []
        
        class HazardousAction(ActionType[OntologyObject]):
            api_name = "hazardous_action"
            object_type = OntologyObject
            requires_proposal = True
            async def apply_edits(self, params, context): return None, []
        
        registry.register(SafeAction)
        registry.register(HazardousAction)
        
        hazardous = registry.get_hazardous_actions()
        assert "hazardous_action" in hazardous
        assert "safe_action" not in hazardous


# =============================================================================
# SCENARIO 7: HYBRID ROUTER INTELLIGENCE
# =============================================================================

class TestHybridRouter:
    """Test HybridRouter routing decisions."""
    
    def test_simple_query_routes_local(self, router_config):
        """Verify simple queries route to LOCAL."""
        router = HybridRouter(router_config)
        
        decision = router.route("What is 2 + 2?")
        
        assert decision.target == RouteTarget.LOCAL
        assert decision.complexity_score < router_config.word_threshold
    
    def test_critical_keyword_routes_relay(self, router_config):
        """Verify critical keywords trigger RELAY routing."""
        router = HybridRouter(router_config)
        
        decision = router.route("Delete all user data")
        
        assert decision.target == RouteTarget.RELAY
        assert "delete" in decision.triggered_keywords
    
    def test_complex_query_routes_relay(self, router_config):
        """Verify complex queries route to RELAY."""
        router = HybridRouter(router_config)
        
        # Generate a long, complex query
        complex_query = " ".join(["word"] * 100)
        decision = router.route(complex_query)
        
        assert decision.target == RouteTarget.RELAY
        assert "complexity" in decision.reason.lower()
    
    def test_explicit_local_marker(self, router_config):
        """Verify [LOCAL] marker forces local routing."""
        router = HybridRouter(router_config)
        
        # Even with critical keyword, LOCAL marker overrides
        decision = router.route("[LOCAL] Deploy to production")
        
        assert decision.target == RouteTarget.LOCAL
        assert "explicit" in decision.reason.lower()
    
    def test_explicit_relay_marker(self, router_config):
        """Verify [RELAY] marker forces relay routing."""
        router = HybridRouter(router_config)
        
        decision = router.route("[RELAY] Simple question")
        
        assert decision.target == RouteTarget.RELAY
        assert "explicit" in decision.reason.lower()
    
    def test_technical_terms_increase_complexity(self, router_config):
        """Verify technical terms increase complexity score."""
        router = HybridRouter(router_config)
        
        # Without technical terms
        d1 = router.route("Set up the system")
        
        # With technical terms
        d2 = router.route("Set up the api microservice")
        
        assert d2.complexity_score > d1.complexity_score
    
    def test_routing_decision_contains_metrics(self, router_config):
        """Verify RoutingDecision includes metrics."""
        router = HybridRouter(router_config)
        
        decision = router.route("Create a task for the team")
        
        assert "word_count" in decision.metrics
        assert "sentence_count" in decision.metrics
        assert "threshold" in decision.metrics


# =============================================================================
# SCENARIO 8: ROUTER CONFIGURATION
# =============================================================================

class TestRouterConfiguration:
    """Test RouterConfig loading and validation."""
    
    def test_default_config(self):
        """Verify default configuration values."""
        config = RouterConfig()
        
        assert config.word_threshold == 50
        assert config.sentence_threshold == 5
        assert "delete" in config.critical_keywords
        assert config.ollama_model == "llama3.2"
    
    def test_config_from_json_file(self, temp_config_file):
        """Verify loading config from JSON file."""
        config = RouterConfig.from_file(temp_config_file)
        
        assert config.word_threshold == 30  # From fixture
    
    def test_config_validation(self):
        """Verify config validation constraints."""
        # Valid
        RouterConfig(word_threshold=100)
        
        # Invalid (below minimum)
        with pytest.raises(ValueError):
            RouterConfig(word_threshold=5)
    
    def test_config_to_file(self, router_config):
        """Verify saving config to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = Path(f.name)
        
        router_config.to_file(path)
        
        loaded = RouterConfig.from_file(path)
        assert loaded.word_threshold == router_config.word_threshold


# =============================================================================
# SCENARIO 9: OLLAMA CLIENT
# =============================================================================

class TestOllamaClient:
    """Test OllamaClient functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_mocked(self, router_config):
        """Verify health check with mocked response."""
        client = OllamaClient(router_config)
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            
            result = await client.health_check()
            
            assert result is True
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_generate_mocked(self, router_config):
        """Verify generate with mocked response."""
        client = OllamaClient(router_config)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "The answer is 4",
            "model": "llama3.2",
            "done": True,
            "total_duration": 1000000000,
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            response = await client.generate("What is 2 + 2?")
            
            assert response.content == "The answer is 4"
            assert response.model == "llama3.2"
            assert response.duration_seconds == 1.0
        
        await client.close()


# =============================================================================
# SCENARIO 10: CONCURRENT OPERATIONS
# =============================================================================

class TestConcurrentOperations:
    """Test thread safety and concurrent access."""
    
    @pytest.mark.asyncio
    async def test_concurrent_proposal_submissions(self):
        """Verify multiple proposals can be submitted concurrently."""
        proposals = [
            Proposal(action_type=f"action_{i}", created_by=f"agent-{i}")
            for i in range(10)
        ]
        
        async def submit_proposal(p: Proposal):
            await asyncio.sleep(0.01)  # Simulate async work
            p.submit()
            return p
        
        results = await asyncio.gather(*[submit_proposal(p) for p in proposals])
        
        assert all(p.status == ProposalStatus.PENDING for p in results)
        assert len(set(p.id for p in results)) == 10  # All unique IDs
    
    @pytest.mark.asyncio
    async def test_concurrent_object_creation(self):
        """Verify concurrent object creation generates unique IDs."""
        async def create_object():
            await asyncio.sleep(0.001)
            return OntologyObject()
        
        objects = await asyncio.gather(*[create_object() for _ in range(100)])
        
        ids = [obj.id for obj in objects]
        assert len(set(ids)) == 100  # All unique


# =============================================================================
# SCENARIO 11: INTEGRATION TEST
# =============================================================================

class TestFullIntegration:
    """Full integration test of the ODA workflow."""
    
    @pytest.mark.asyncio
    async def test_full_governance_workflow(self, user_context, admin_context):
        """Test complete proposal governance workflow."""
        # 1. Create a hazardous action proposal
        proposal = Proposal(
            action_type="deploy_to_production",
            payload={"service": "checkout", "version": "2.0.0"},
            created_by=user_context.actor_id,
            priority=ProposalPriority.HIGH,
        )
        
        # 2. Submit for review
        proposal.submit(submitter_id=user_context.actor_id)
        assert proposal.is_pending_review
        
        # 3. Admin reviews and approves
        proposal.approve(
            reviewer_id=admin_context.actor_id,
            comment="Verified deployment plan"
        )
        assert proposal.can_execute
        
        # 4. Execute the action
        proposal.execute(
            executor_id="system",
            result={"deployment_id": "deploy-123", "status": "success"}
        )
        
        # 5. Verify final state
        assert proposal.is_terminal
        assert proposal.status == ProposalStatus.EXECUTED
        assert proposal.execution_result["status"] == "success"
        
        # 6. Verify audit trail
        audit = proposal.to_audit_log()
        assert audit["reviewed_by"] == admin_context.actor_id
        assert audit["status"] == "executed"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
