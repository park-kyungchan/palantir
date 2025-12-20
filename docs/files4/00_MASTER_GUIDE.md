# E2E Integration Test - Master Guide

> **Date**: 2025-12-20
> **Target Agent**: Antigravity IDE (Gemini 3.0 Pro)
> **Philosophy**: "Trust, but Verify"
> **Purpose**: Validate complete ODA pipeline before further refactoring

---

## 📋 Test Scenarios Overview

| # | Scenario | Input | Expected Behavior |
|:-:|:---------|:------|:------------------|
| 1 | Safe Action | "서비스 상태 확인해줘" | ⚡ Executes immediately |
| 2 | Hazardous Action | "운영 배포해줘" | 🛡️ Creates PENDING proposal |
| 3 | Unknown Action | "시스템 해킹해줘" | ⛔ DENIED |
| 4 | **Full Workflow** | Request → Approve → Execute | Complete governance cycle |
| 5 | Mixed Actions | Complex plan | Safe ✓, Hazardous 🛡️, Unknown ⛔ |
| 6 | Rejection | Proposal rejected | Terminal state, no execution |
| 7 | Audit Trail | Full workflow | History entries verified |
| 8 | Concurrency | 5 parallel proposals | All unique, all pending |

---

## 🎯 Scenario 4: Full Governance Workflow (핵심)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: User Request                                                │
│  ┌─────────────┐                                                    │
│  │ "운영 배포해줘" │ ─────▶ Mock LLM                                  │
│  └─────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: Kernel Processing                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │
│  │ Plan Parser │───▶│ ActionReg.  │───▶│ GovernanceEngine        │  │
│  │ (Pydantic)  │    │ .get()      │    │ .evaluate() →           │  │
│  │             │    │             │    │ "REQUIRE_PROPOSAL"      │  │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: Proposal Persistence                                        │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ ProposalRepository.save()                                        ││
│  │ ┌─────────────────────────────────────────────────────────────┐ ││
│  │ │ SQLite: INSERT INTO proposals (...) VALUES (...)            │ ││
│  │ │ SQLite: INSERT INTO proposal_history (...) action='created' │ ││
│  │ └─────────────────────────────────────────────────────────────┘ ││
│  │ Status: PENDING                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: Admin Approval                                              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ repo.approve(proposal_id, reviewer_id="admin-001")               ││
│  │ ┌─────────────────────────────────────────────────────────────┐ ││
│  │ │ SQLite: UPDATE proposals SET status='approved' ...          │ ││
│  │ │ SQLite: INSERT INTO proposal_history (...) action='approved'│ ││
│  │ └─────────────────────────────────────────────────────────────┘ ││
│  │ Status: PENDING → APPROVED                                       ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5: Kernel Execution Loop                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ kernel.execute_approved_proposals()                              ││
│  │ ┌─────────────────────────────────────────────────────────────┐ ││
│  │ │ 1. repo.find_by_status(APPROVED)                            │ ││
│  │ │ 2. action_cls = registry.get("deploy_service")              │ ││
│  │ │ 3. await action.execute(payload, context)                   │ ││
│  │ │ 4. repo.execute(proposal_id, result={...})                  │ ││
│  │ └─────────────────────────────────────────────────────────────┘ ││
│  │ Status: APPROVED → EXECUTED                                      ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 6: Verification                                                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ proposal = await repo.find_by_id(proposal_id)                    ││
│  │ assert proposal.status == ProposalStatus.EXECUTED                ││
│  │ assert proposal.executed_at is not None                          ││
│  │ assert proposal.execution_result["success"] == True              ││
│  │                                                                   ││
│  │ _, history = await repo.get_with_history(proposal_id)            ││
│  │ assert len(history) == 3  # created, approved, executed          ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

```bash
# 1. Create test file
# Copy code from 01_full_integration_test.md to:
# tests/e2e/test_full_integration.py

# 2. Run all tests
pytest tests/e2e/test_full_integration.py -v --asyncio-mode=auto -s

# 3. Run core scenario only
pytest tests/e2e/test_full_integration.py::TestFullIntegrationWorkflow::test_scenario_4_full_governance_workflow -v -s
```

---

## 📊 What This Test Validates

### ✅ Verified Components

| Layer | Component | Validation |
|:------|:----------|:-----------|
| **LLM** | MockLLMClient | Structured output generation |
| **Parsing** | Plan → Jobs | Correct field extraction |
| **Registry** | ActionRegistry.get() | Dynamic action lookup |
| **Governance** | GovernanceEngine | Metadata-driven decisions |
| **Persistence** | ProposalRepository | SQLite CRUD + WAL |
| **State Machine** | Proposal transitions | PENDING → APPROVED → EXECUTED |
| **History** | proposal_history | Full audit trail |
| **Concurrency** | Parallel proposals | No race conditions |

### ❌ Not Tested (Out of Scope)

| Component | Reason |
|:----------|:-------|
| Real LLM API | Use Instructor tests separately |
| Real Slack/Webhooks | Requires external services |
| Production Kernel loop | Tests isolated kernel methods |

---

## 🔍 Key Assertions

```python
# Scenario 4 핵심 검증 포인트

# 1. Proposal created with correct status
assert proposal.status == ProposalStatus.PENDING

# 2. DB persistence verified
saved_proposal = await repo.find_by_id(proposal_id)
assert saved_proposal is not None

# 3. Approval changes state
await repo.approve(proposal_id, "admin-001")
assert (await repo.find_by_id(proposal_id)).status == ProposalStatus.APPROVED

# 4. Execution recorded
executed = await kernel.execute_approved_proposals()
assert len(executed) == 1
assert executed[0]["result"]["success"] is True

# 5. Final state in DB
final = await repo.find_by_id(proposal_id)
assert final.status == ProposalStatus.EXECUTED
assert final.executed_at is not None
```

---

## 📋 Post-Test Next Steps

After all tests pass:

| Priority | Action | Reason |
|:---------|:-------|:-------|
| 🔴 P0 | **Dead Code Cleanup** | Remove OrionObject, core.py |
| 🟡 P1 | **SQLAlchemy Migration** | Type-safe persistence |
| 🟢 P2 | **Real Kernel Integration** | Apply pattern to kernel.py |

---

## 🚨 Troubleshooting

### "ModuleNotFoundError"

```bash
export PYTHONPATH=/home/palantir/orion-orchestrator-v2:$PYTHONPATH
```

### "Database is locked"

WAL mode should prevent this. If persistent:
```python
# Increase timeout in Database config
config = DatabaseConfig(path=path, timeout=60.0)
```

### "InvalidTransitionError in test"

Check proposal status before transition:
```python
print(f"Current status: {proposal.status}")
```

---

**End of Master Guide**
