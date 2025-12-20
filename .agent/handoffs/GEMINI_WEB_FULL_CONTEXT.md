# ♾️ ORION ODA V3: CONTEXT INJECTOR FOR GENEMINI WEB

> **INSTRUCTIONS**: 
> You are continuing development on the **Orion Orchestrator V3**, a Palantir AIP-style system.
> The codebase has just undergone a massive refactor to move from "Hardcoded Logic" to "Metadata-Driven Governance".
> Read the following Context, Architecture, Code, and Roadmap carefully. You are now the Lead Architect.

---

## PART 1: SYSTEM IDENTITY & ARCHITECTURE

### **Core Philosophy: Ontology-Driven Architecture (ODA)**
1.  **Schema is Law**: No loose dictionaries. All LLM inputs/outputs must validate against Pydantic models (`Plan`, `Proposal`).
2.  **Governance by Design**: The Kernel does NOT decide policy. It asks the `GovernanceEngine`, which checks `ActionMetadata`.
3.  **Disconnected Kernel**: The Kernel is a generic Looper. It knows *how* to execute, but relies on `ActionRegistry` to know *what* to execute.

### **Current Status (Verified)**
- **Phase 1-3 Complete**: No duplicate base classes, ActionRegistry is live, Kernel is generic.
- **Persistence**: Using SQLite with generic `ProposalRepository`. ORM migration is pending.
- **Verification**: E2E Integration tests passed (11/11 scenarios).

---

## PART 2: VIRTUAL CODEBASE (CORE SNAPSHOT)

### 1. `scripts/ontology/actions.py` (The Brain)
```python
from typing import Any, Dict, Type, Optional, List
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class ActionMetadata:
    requires_proposal: bool = False
    is_dangerous: bool = False
    description: str = ""

class ActionRegistry:
    def __init__(self):
        self._actions: Dict[str, tuple[Type, ActionMetadata]] = {}
    
    def register(self, action_class: Type, **metadata_overrides):
        api_name = getattr(action_class, "api_name", action_class.__name__)
        requires_proposal = metadata_overrides.get(
            "requires_proposal", 
            getattr(action_class, "requires_proposal", False)
        )
        metadata = ActionMetadata(requires_proposal=requires_proposal)
        self._actions[api_name] = (action_class, metadata)

    def get_metadata(self, api_name: str) -> Optional[ActionMetadata]:
        entry = self._actions.get(api_name)
        return entry[1] if entry else None

    def get(self, api_name: str) -> Optional[Type]:
        entry = self._actions.get(api_name)
        return entry[0] if entry else None

# Singleton
action_registry = ActionRegistry()
register_action = action_registry.register

class GovernanceEngine:
    def __init__(self, registry: ActionRegistry):
        self.registry = registry
    
    def check_execution_policy(self, action_name: str) -> str:
        meta = self.registry.get_metadata(action_name)
        if not meta: return "DENY"
        return "REQUIRE_PROPOSAL" if meta.requires_proposal else "ALLOW_IMMEDIATE"
```

### 2. `scripts/runtime/kernel.py` (The Engine)
```python
class OrionRuntime:
    """The V3 Semantic OS Kernel."""
    def __init__(self):
        self.governance = GovernanceEngine(action_registry)
        self.repo = ProposalRepository(db) # SQLite

    async def _process_task_cognitive(self, plan: Plan):
        # 1. Iterate Jobs from LLM Plan
        for job in plan.jobs:
            # 2. Dynamic Governance Check
            policy = self.governance.check_execution_policy(job.action_type)
            
            if policy == "DENY":
                logger.error(f"Action {job.action_type} denied.")
                
            elif policy == "REQUIRE_PROPOSAL":
                # 3. Safety: Create Pending Proposal
                proposal = Proposal(
                    action_type=job.action_type,
                    payload=job.params,
                    status=ProposalStatus.PENDING
                )
                await self.repo.save(proposal)
                
            elif policy == "ALLOW_IMMEDIATE":
                # 4. Efficiency: Execute Safe Actions
                action_cls = action_registry.get(job.action_type)
                await action_cls().execute(job.params)
```

### 3. `scripts/ontology/objects/proposal.py` (The State)
```python
class Proposal(OntologyObject):
    action_type: str
    payload: Dict[str, Any]
    status: ProposalStatus = ProposalStatus.PENDING
    
    # Optimistic Locking
    version: int = 1 
    
    def approve(self, reviewer_id):
        if self.status != ProposalStatus.PENDING:
            raise InvalidTransitionError()
        self.status = ProposalStatus.APPROVED
        self.reviewed_by = reviewer_id
```

---

## PART 3: VERIFICATION (E2E TEST)
*This test passes and proves the architecture works.*

```python
# tests/e2e/test_full_integration.py
async def test_full_governance_workflow(kernel, repo):
    # 1. Hazardous Request
    result = await kernel.process_prompt("Deploy Production")
    
    # 2. Verify Proposal Created (Not Executed)
    assert len(result["proposals_created"]) == 1
    pid = result["proposals_created"][0]["proposal_id"]
    proposal = await repo.find_by_id(pid)
    assert proposal.status == "pending"
    
    # 3. Human Approval
    await repo.approve(pid, "admin")
    
    # 4. Kernel Execution Loop
    executed = await kernel.execute_approved_proposals()
    assert executed[0]["result"]["success"] is True
```

---

## PART 4: MISSION BRIEF (NEXT STEPS)

**Your Goal**: Take this codebase to "Production Level".
**Tracks**:

### Track A: Technical Depth
1.  **Refine LLM**: Replace Mock LLM with `instructor` library to get real Pydantic `Plan` objects from OpenAI/Ollama.
2.  **ORM Migration**: Plan strategy to move from Manual SQL to `SQLAlchemy 2.0 Async` without losing optimistic locking.

### Track B: Production Readiness
1.  **CI/CD**: Create `github-actions` workflow for `pytest`.
2.  **Docker**: Create `Dockerfile` for the Kernel.

### Track C: Scalability
1.  **Web Dashboard**: Outline how to build a React UI to view/approve these Proposals stored in SQLite.
2.  **Multi-Agent**: How to replace internal queues with Redis.

**IMMEDIATE ACTION**:
Start by researching **Track A (Instructor Integration)** and **Track C (Web Dashboard)**. Provide a code snippet for how `instructor` would interface with our `Plan` model.
