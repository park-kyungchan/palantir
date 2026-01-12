"""
ODA V3.0 - Full Integration E2E Test
=====================================

"Trust, but Verify" - Validates the complete workflow:

    [LLM Output] 
         ↓
    [Plan Parser] → Pydantic Validation
         ↓
    [Kernel] → ActionRegistry Lookup
         ↓
    [GovernanceEngine] → Metadata Inspection
         ↓
    [ProposalRepository] → SQLite Persistence
         ↓
    [Admin Approval] → State Transition
         ↓
    [Kernel Executor] → Action Execution
         ↓
    [Verification] → DB State Check

Run with: pytest tests/e2e/test_full_integration.py -v --asyncio-mode=auto -s
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# ODA Core Imports
from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.objects.proposal import (
    Proposal,
    ProposalPriority,
    ProposalStatus,
    InvalidTransitionError,
)
from lib.oda.ontology.actions import (
    ActionContext,
    ActionRegistry,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    RequiredField,
    AllowedValues,
    LogSideEffect,
    register_action,
    action_registry,
)
from lib.oda.ontology.storage.database import Database, initialize_database
from lib.oda.ontology.storage.proposal_repository import (
    ProposalRepository,
    ProposalNotFoundError,
)


# =============================================================================
# MOCK LLM CLIENT
# =============================================================================

class MockLLMClient:
    """
    Simulates LLM responses for testing.
    Returns structured Plan data matching the expected schema.
    """
    
    def __init__(self, responses: List[Dict[str, Any]] = None):
        self.responses = responses or []
        self.call_count = 0
        self.last_prompt = None
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a mock LLM response."""
        self.last_prompt = prompt
        self.call_count += 1
        
        # Return pre-configured response or default
        if self.call_count <= len(self.responses):
            return self.responses[self.call_count - 1]
        
        # Default: Generate a deployment plan
        return {
            "objective": "Deploy checkout service to production",
            "jobs": [
                {
                    "job_id": "job-001",
                    "title": "Health Check",
                    "action_type": "check_health",
                    "params": {"service": "checkout"},
                    "priority": "high"
                },
                {
                    "job_id": "job-002", 
                    "title": "Deploy to Production",
                    "action_type": "deploy_service",
                    "params": {
                        "service_name": "checkout",
                        "version": "2.0.0",
                        "environment": "production"
                    },
                    "priority": "critical"
                }
            ]
        }


# =============================================================================
# MOCK ACTION DEFINITIONS (for isolated testing)
# =============================================================================

class MockActionRegistry:
    """Isolated action registry for testing."""
    
    def __init__(self):
        self._actions: Dict[str, type] = {}
    
    def register(self, action_cls: type) -> type:
        self._actions[action_cls.api_name] = action_cls
        return action_cls
    
    def get(self, api_name: str) -> Optional[type]:
        return self._actions.get(api_name)
    
    def list_actions(self) -> List[str]:
        return list(self._actions.keys())
    
    def get_hazardous_actions(self) -> List[str]:
        return [
            name for name, cls in self._actions.items()
            if getattr(cls, "requires_proposal", False)
        ]
    
    def get_metadata(self, api_name: str):
        # Mock metadata retrieval
        cls = self.get(api_name)
        if not cls: return None
        from lib.oda.ontology.actions import ActionMetadata
        return ActionMetadata(
            requires_proposal=getattr(cls, "requires_proposal", False),
            is_dangerous=getattr(cls, "is_dangerous", False),
            description=""
        )


# Test Actions
class CheckHealthAction(ActionType[OntologyObject]):
    """Safe action - executes immediately."""
    api_name = "check_health"
    object_type = OntologyObject
    requires_proposal = False
    
    submission_criteria = [RequiredField("service")]
    side_effects = [LogSideEffect()]
    
    async def apply_edits(self, params, context):
        return None, [EditOperation(
            edit_type=EditType.MODIFY,
            object_type="HealthCheck",
            object_id=f"health-{params['service']}",
            changes={"status": "healthy", "checked_at": utc_now().isoformat()}
        )]


class DeployServiceAction(ActionType[OntologyObject]):
    """Hazardous action - requires proposal approval."""
    api_name = "deploy_service"
    object_type = OntologyObject
    requires_proposal = True  # ⚠️ HAZARDOUS
    
    submission_criteria = [
        RequiredField("service_name"),
        RequiredField("version"),
        RequiredField("environment"),
        AllowedValues("environment", ["staging", "production"]),
    ]
    side_effects = [LogSideEffect()]
    
    async def apply_edits(self, params, context):
        return None, [EditOperation(
            edit_type=EditType.CREATE,
            object_type="Deployment",
            object_id=f"deploy-{params['service_name']}-{params['version']}",
            changes={
                "service": params["service_name"],
                "version": params["version"],
                "environment": params["environment"],
                "deployed_at": utc_now().isoformat(),
                "deployed_by": context.actor_id,
            }
        )]


# =============================================================================
# GOVERNANCE ENGINE
# =============================================================================

class GovernanceEngine:
    """
    Enforces governance policies based on action metadata.
    No hardcoded action names - purely metadata-driven.
    """
    
    def __init__(self, registry: MockActionRegistry):
        self.registry = registry
    
    def check_execution_policy(self, action_type: str) -> str:
        """
        Evaluate governance policy for an action.
        
        Returns:
            - "ALLOW_IMMEDIATE": Safe to execute immediately
            - "REQUIRE_PROPOSAL": Needs approval
            - "DENY": Unknown or forbidden action
        """
        meta = self.registry.get_metadata(action_type)
        if not meta:
            return "DENY"
        
        if meta.requires_proposal:
            return "REQUIRE_PROPOSAL"
        
        return "ALLOW_IMMEDIATE"


# =============================================================================
# INTEGRATION KERNEL
# =============================================================================

class IntegrationKernel:
    """
    The Generic Ontology-Driven Kernel.
    
    - Parses LLM output into structured jobs
    - Routes through GovernanceEngine
    - Creates Proposals for hazardous actions
    - Executes approved proposals
    """
    
    def __init__(
        self,
        llm: MockLLMClient,
        registry: MockActionRegistry,
        repo: ProposalRepository,
    ):
        self.llm = llm
        self.registry = registry
        self.governance = GovernanceEngine(registry)
        self.repo = repo
        self.execution_log: List[Dict[str, Any]] = []
    
    async def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Process a user prompt through the full pipeline.
        
        Returns:
            Summary of processing results
        """
        results = {
            "prompt": prompt,
            "jobs_processed": 0,
            "executed_immediately": [],
            "proposals_created": [],
            "denied": [],
        }
        
        # 1. Get plan from LLM
        plan = await self.llm.generate(prompt)
        
        # 2. Process each job
        for job in plan.get("jobs", []):
            action_type = job.get("action_type")
            parameters = job.get("params", {}) # fixed: was parameters in doc but params in mock
            
            # 3. Evaluate governance
            decision = self.governance.check_execution_policy(action_type)
            
            if decision == "ALLOW_IMMEDIATE":
                # Safe action - execute immediately
                result = await self._execute_action(action_type, parameters)
                results["executed_immediately"].append({
                    "action": action_type,
                    "result": result,
                })
                
            elif decision == "REQUIRE_PROPOSAL":
                # Hazardous action - create proposal
                proposal = await self._create_proposal(action_type, parameters)
                results["proposals_created"].append({
                    "action": action_type,
                    "proposal_id": proposal.id,
                    "status": proposal.status.value,
                })
                
            else:  # DENY
                results["denied"].append({
                    "action": action_type,
                    "reason": "Unknown action type",
                })
            
            results["jobs_processed"] += 1
        
        return results
    
    async def _execute_action(
        self,
        action_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an action and return result."""
        action_cls = self.registry.get(action_type)
        action = action_cls()
        context = ActionContext(actor_id="kernel")
        
        result = await action.execute(parameters, context)
        
        self.execution_log.append({
            "action": action_type,
            "timestamp": utc_now().isoformat(),
            "success": result.success,
        })
        
        return result.to_dict()
    
    async def _create_proposal(
        self,
        action_type: str,
        parameters: Dict[str, Any]
    ) -> Proposal:
        """Create and persist a proposal for hazardous action."""
        proposal = Proposal(
            action_type=action_type,
            payload=parameters,
            priority=ProposalPriority.HIGH,
            created_by="kernel",
        )
        proposal.submit()
        await self.repo.save(proposal, actor_id="kernel")
        
        return proposal
    
    async def execute_approved_proposals(self) -> List[Dict[str, Any]]:
        """
        Find and execute all approved proposals.
        Called by the kernel's main loop.
        """
        executed = []
        
        # Use find_by_status
        approved = await self.repo.find_by_status(ProposalStatus.APPROVED)
        
        for proposal in approved:
            action_cls = self.registry.get(proposal.action_type)
            
            if action_cls is None:
                continue
            
            # Execute the action
            result = await self._execute_action(
                proposal.action_type,
                proposal.payload
            )
            
            # Mark proposal as executed
            await self.repo.execute(
                proposal.id,
                executor_id="kernel",
                result=result # fixed: result is already a dict from _execute_action
            )
            
            executed.append({
                "proposal_id": proposal.id,
                "action": proposal.action_type,
                "result": result,
            })
        
        return executed


# =============================================================================
# FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def test_db() -> Database:
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_integration.db"
        db = Database(db_path)
        await db.initialize()
        yield db


@pytest_asyncio.fixture
async def repo(test_db: Database) -> ProposalRepository:
    """Create repository with test database."""
    return ProposalRepository(test_db)


@pytest.fixture
def test_registry() -> MockActionRegistry:
    """Create isolated test registry with actions."""
    registry = MockActionRegistry()
    registry.register(CheckHealthAction)
    registry.register(DeployServiceAction)
    return registry


@pytest.fixture
def mock_llm() -> MockLLMClient:
    """Create mock LLM client."""
    return MockLLMClient()


@pytest_asyncio.fixture
async def kernel(
    mock_llm: MockLLMClient,
    test_registry: MockActionRegistry,
    repo: ProposalRepository,
) -> IntegrationKernel:
    """Create integration kernel with all dependencies."""
    return IntegrationKernel(mock_llm, test_registry, repo)


# =============================================================================
# E2E TEST SCENARIOS
# =============================================================================

class TestFullIntegrationWorkflow:
    """
    Full E2E integration tests validating the complete pipeline.
    """
    
    @pytest.mark.asyncio
    async def test_scenario_1_safe_action_executes_immediately(
        self,
        kernel: IntegrationKernel,
        mock_llm: MockLLMClient,
    ):
        """
        Scenario: Safe action should execute without proposal.
        """
        # Configure LLM to return safe action
        mock_llm.responses = [{
            "objective": "Check service health",
            "jobs": [
                {
                    "job_id": "job-001",
                    "action_type": "check_health",
                    "params": {"service": "api-gateway"},
                }
            ]
        }]
        
        # Process
        result = await kernel.process_prompt("서비스 상태 확인해줘")
        
        # Verify
        assert result["jobs_processed"] == 1
        assert len(result["executed_immediately"]) == 1
        assert len(result["proposals_created"]) == 0
        assert result["executed_immediately"][0]["action"] == "check_health"
        assert result["executed_immediately"][0]["result"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_scenario_2_hazardous_action_creates_proposal(
        self,
        kernel: IntegrationKernel,
        repo: ProposalRepository,
        mock_llm: MockLLMClient,
    ):
        """
        Scenario: Hazardous action should create proposal.
        """
        # Configure LLM
        mock_llm.responses = [{
            "objective": "Deploy to production",
            "jobs": [
                {
                    "job_id": "job-001",
                    "action_type": "deploy_service",
                    "params": {
                        "service_name": "checkout",
                        "version": "2.0.0",
                        "environment": "production"
                    },
                }
            ]
        }]
        
        # Process
        result = await kernel.process_prompt("운영 배포해줘")
        
        # Verify kernel result
        assert result["jobs_processed"] == 1
        assert len(result["executed_immediately"]) == 0
        assert len(result["proposals_created"]) == 1
        
        proposal_info = result["proposals_created"][0]
        assert proposal_info["action"] == "deploy_service"
        assert proposal_info["status"] == "pending"
        
        # Verify DB persistence
        proposal_id = proposal_info["proposal_id"]
        saved_proposal = await repo.find_by_id(proposal_id)
        
        assert saved_proposal is not None
        assert saved_proposal.status == ProposalStatus.PENDING
        assert saved_proposal.action_type == "deploy_service"
        assert saved_proposal.payload["service_name"] == "checkout"
    
    @pytest.mark.asyncio
    async def test_scenario_3_unknown_action_denied(
        self,
        kernel: IntegrationKernel,
        mock_llm: MockLLMClient,
    ):
        """
        Scenario: Unknown action should be denied.
        """
        mock_llm.responses = [{
            "objective": "Hack the system",
            "jobs": [
                {
                    "job_id": "job-001",
                    "action_type": "hack_system",
                    "params": {},
                }
            ]
        }]
        
        result = await kernel.process_prompt("시스템 해킹해줘")
        
        assert result["jobs_processed"] == 1
        assert len(result["executed_immediately"]) == 0
        assert len(result["proposals_created"]) == 0
        assert len(result["denied"]) == 1
        assert result["denied"][0]["action"] == "hack_system"
    
    @pytest.mark.asyncio
    async def test_scenario_4_full_governance_workflow(
        self,
        kernel: IntegrationKernel,
        repo: ProposalRepository,
        mock_llm: MockLLMClient,
    ):
        """
        Scenario: Complete governance workflow.
        """
        # Step 1: Create proposal via kernel
        mock_llm.responses = [{
            "objective": "Deploy to production",
            "jobs": [
                {
                    "job_id": "job-001",
                    "action_type": "deploy_service",
                    "params": {
                        "service_name": "payment-service",
                        "version": "3.0.0",
                        "environment": "production"
                    },
                }
            ]
        }]
        
        result = await kernel.process_prompt("운영 배포해줘")
        proposal_id = result["proposals_created"][0]["proposal_id"]
        
        # Verify PENDING
        proposal = await repo.find_by_id(proposal_id)
        assert proposal.status == ProposalStatus.PENDING
        
        # Step 2: Admin approval
        await repo.approve(
            proposal_id,
            reviewer_id="admin-001",
            comment="Deployment approved after review"
        )
        
        # Verify APPROVED
        proposal = await repo.find_by_id(proposal_id)
        assert proposal.status == ProposalStatus.APPROVED
        assert proposal.reviewed_by == "admin-001"
        
        # Step 3: Kernel executes approved proposals
        executed = await kernel.execute_approved_proposals()
        
        # Verify execution
        assert len(executed) == 1
        assert executed[0]["proposal_id"] == proposal_id
        assert executed[0]["result"]["success"] is True
        
        # Step 4: Verify EXECUTED in DB
        proposal = await repo.find_by_id(proposal_id)
        assert proposal.status == ProposalStatus.EXECUTED
        assert proposal.executed_at is not None
        assert proposal.execution_result is not None
    
    @pytest.mark.asyncio
    async def test_scenario_5_mixed_actions_workflow(
        self,
        kernel: IntegrationKernel,
        repo: ProposalRepository,
        mock_llm: MockLLMClient,
    ):
        """
        Scenario: Mix of safe, hazardous, and unknown actions.
        """
        mock_llm.responses = [{
            "objective": "Complex deployment",
            "jobs": [
                {
                    "job_id": "job-001",
                    "action_type": "check_health",
                    "params": {"service": "api"},
                },
                {
                    "job_id": "job-002",
                    "action_type": "deploy_service",
                    "params": {
                        "service_name": "api",
                        "version": "1.0.0",
                        "environment": "staging"
                    },
                },
                {
                    "job_id": "job-003",
                    "action_type": "unknown_action",
                    "params": {},
                },
                {
                    "job_id": "job-004",
                    "action_type": "check_health",
                    "params": {"service": "db"},
                },
            ]
        }]
        
        result = await kernel.process_prompt("복합 배포 작업")
        
        # Verify counts
        assert result["jobs_processed"] == 4
        assert len(result["executed_immediately"]) == 2  # Two check_health
        assert len(result["proposals_created"]) == 1     # One deploy_service
        assert len(result["denied"]) == 1                # One unknown
        
        # Verify specific results
        executed_actions = [e["action"] for e in result["executed_immediately"]]
        assert executed_actions.count("check_health") == 2
        
        assert result["proposals_created"][0]["action"] == "deploy_service"
        assert result["denied"][0]["action"] == "unknown_action"
    
    @pytest.mark.asyncio
    async def test_scenario_6_proposal_rejection_workflow(
        self,
        kernel: IntegrationKernel,
        repo: ProposalRepository,
        mock_llm: MockLLMClient,
    ):
        """
        Scenario: Proposal gets rejected.
        """
        # Create proposal
        mock_llm.responses = [{
            "objective": "Risky deployment",
            "jobs": [
                {
                    "job_id": "job-001",
                    "action_type": "deploy_service",
                    "params": {
                        "service_name": "critical-service",
                        "version": "0.0.1-alpha",
                        "environment": "production"
                    },
                }
            ]
        }]
        
        result = await kernel.process_prompt("위험한 배포")
        proposal_id = result["proposals_created"][0]["proposal_id"]
        
        # Reject
        await repo.reject(
            proposal_id,
            reviewer_id="admin-001",
            reason="Version too unstable for production"
        )
        
        # Verify REJECTED
        proposal = await repo.find_by_id(proposal_id)
        assert proposal.status == ProposalStatus.REJECTED
        assert "unstable" in proposal.review_comment
        
        # Verify kernel doesn't execute rejected proposals
        executed = await kernel.execute_approved_proposals()
        assert len(executed) == 0
        
        # Verify terminal state - can't approve after rejection
        with pytest.raises(InvalidTransitionError):
            await repo.approve(proposal_id, "admin-002")
    
    @pytest.mark.asyncio
    async def test_scenario_7_audit_trail_verification(
        self,
        kernel: IntegrationKernel,
        repo: ProposalRepository,
        mock_llm: MockLLMClient,
    ):
        """
        Scenario: Verify complete audit trail in database.
        """
        # Full workflow
        mock_llm.responses = [{
            "objective": "Audited deployment",
            "jobs": [
                {
                    "job_id": "job-001",
                    "action_type": "deploy_service",
                    "params": {
                        "service_name": "audit-service",
                        "version": "1.0.0",
                        "environment": "production"
                    },
                }
            ]
        }]
        
        # Create
        result = await kernel.process_prompt("배포 with audit")
        proposal_id = result["proposals_created"][0]["proposal_id"]
        
        # Approve
        await repo.approve(proposal_id, "admin-001", "Approved")
        
        # Execute
        await kernel.execute_approved_proposals()
        
        # Get history
        _, history = await repo.get_with_history(proposal_id)
        
        # Verify audit trail
        assert len(history) >= 3
        
        actions = [h.action for h in history]
        assert "created" in actions or "bulk_saved" in actions
        assert "approved" in actions
        assert "executed" in actions
        
        # Verify chronological order
        timestamps = [h.created_at for h in history]
        assert timestamps == sorted(timestamps)
    
    @pytest.mark.asyncio
    async def test_scenario_8_concurrent_proposals(
        self,
        kernel: IntegrationKernel,
        repo: ProposalRepository,
        mock_llm: MockLLMClient,
    ):
        """
        Scenario: Multiple concurrent proposals.
        """
        # Create multiple proposals concurrently
        async def create_proposal(service_name: str):
            mock_client = MockLLMClient([{
                "objective": f"Deploy {service_name}",
                "jobs": [
                    {
                        "job_id": "job-001",
                        "action_type": "deploy_service",
                        "params": {
                            "service_name": service_name,
                            "version": "1.0.0",
                            "environment": "production"
                        },
                    }
                ]
            }])
            
            local_kernel = IntegrationKernel(mock_client, kernel.registry, repo)
            return await local_kernel.process_prompt(f"Deploy {service_name}")
        
        # Create 5 proposals concurrently
        results = await asyncio.gather(*[
            create_proposal(f"service-{i}") for i in range(5)
        ])
        
        # Verify all created
        assert all(len(r["proposals_created"]) == 1 for r in results)
        
        # Verify unique IDs
        proposal_ids = [r["proposals_created"][0]["proposal_id"] for r in results]
        assert len(set(proposal_ids)) == 5
        
        # Verify all pending
        pending = await repo.find_pending()
        assert len(pending) == 5


# =============================================================================
# EXECUTION LOG TESTS
# =============================================================================

class TestExecutionLogging:
    """Tests for kernel execution logging."""
    
    @pytest.mark.asyncio
    async def test_execution_log_populated(
        self,
        kernel: IntegrationKernel,
        mock_llm: MockLLMClient,
    ):
        """Verify execution log captures all executed actions."""
        mock_llm.responses = [{
            "jobs": [
                {"action_type": "check_health", "params": {"service": "a"}}, # params
                {"action_type": "check_health", "params": {"service": "b"}},
            ]
        }]
        
        await kernel.process_prompt("Check services")
        
        assert len(kernel.execution_log) == 2
        assert all(log["action"] == "check_health" for log in kernel.execution_log)
        assert all(log["success"] is True for log in kernel.execution_log)


# =============================================================================
# DATABASE INTEGRITY TESTS
# =============================================================================

class TestDatabaseIntegrity:
    """Tests for database consistency and integrity."""
    
    @pytest.mark.asyncio
    async def test_wal_mode_enabled(self, test_db: Database):
        """Verify WAL mode is active for concurrency."""
        from sqlalchemy import text
        async with test_db.transaction() as session:
            result = await session.execute(text("PRAGMA journal_mode;"))
            row = result.fetchone()
        assert row[0] == "wal"
    
    @pytest.mark.asyncio
    async def test_proposal_version_increments(
        self,
        repo: ProposalRepository,
    ):
        """Verify optimistic locking works."""
        proposal = Proposal(
            action_type="test_action",
            created_by="test"
        )
        proposal.submit()
        
        await repo.save(proposal)
        v1 = (await repo.find_by_id(proposal.id)).version
        
        await repo.approve(proposal.id, "admin")
        v2 = (await repo.find_by_id(proposal.id)).version
        
        assert v2 > v1


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--asyncio-mode=auto",
        "-s",
        "--tb=short",
    ])
