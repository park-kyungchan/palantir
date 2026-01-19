from __future__ import annotations

import pytest

from lib.oda.ontology.actions import ActionContext, GovernanceEngine, action_registry


def test_action_registry_contains_core_domain_actions() -> None:
    assert action_registry.get("workspace.create") is not None
    assert action_registry.get("session.create") is not None
    assert action_registry.get("assessment.create") is not None


@pytest.mark.asyncio
async def test_action_execute_via_registry_dispatch() -> None:
    action_cls = action_registry.get("workspace.create")
    assert action_cls is not None

    action = action_cls()
    result = await action.execute(
        params={"name": "E2E WS", "owner_id": "user-1", "workspace_type": "personal"},
        context=ActionContext(actor_id="user-1", metadata={"e2e": True}),
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.name == "E2E WS"


@pytest.mark.asyncio
async def test_stage_c_verify_validate_only_mode() -> None:
    from lib.oda.ontology.actions.quality_actions import StageCVerifyAction

    result = await StageCVerifyAction().execute(
        params={"checks_to_run": ["build"]},
        context=ActionContext.system(),
        validate_only=True,
    )
    assert result.success is True
    assert "dry-run" in (result.message or "").lower()


def test_governance_engine_requires_proposal_for_hazardous_actions() -> None:
    engine = GovernanceEngine(action_registry)

    decision = engine.check_execution_policy("workspace.delete")
    assert decision.decision == "REQUIRE_PROPOSAL"

    blocked = engine.check_execution_policy("file.modify", params={"command": "rm -rf /"})
    assert blocked.decision == "BLOCK"

