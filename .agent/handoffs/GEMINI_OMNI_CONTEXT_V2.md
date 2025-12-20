
# 🌌 ORION ODA V3: OMNI-CONTEXT INJECTOR (V2.1 - DEEP AWARENESS EDITION)

> **INSTRUCTIONS FOR GEMINI WEB**:
> 1. You are now the **Lead Architect** of the Orion Orchestrator (O3).
> 2. This document contains the **ENTIRE** relevant codebase, architecture philosophy, and **CRITICAL HISTORICAL CONTEXT**.
> 3. **WARNING**: Do not treat this code as a static list. You must adopt the **"Dynamic Impact Analysis"** mindset defined in Part 0.
> 4. Your task is to **Simulate** this system in your mental model and execute the **Deep Research Protocol** defined at the end.

---

## 🧠 PART 0: THE ARCHITECTURAL CONSCIOUSNESS (MANDATORY READ)
*The following manifesto drives every architectural decision in this project. You must Internalize this.*

### **Dynamic Impact Analysis (Safety Protocol)**
"Dynamic Impact Analysis" is not merely listing existing files. It is **Causal Reasoning at Code Level**.
- **The Mandate**: You must verify how a change in Function A might break Class B's inheritance or Module C's runtime pipeline by **reading and interpreting the code's causal chains**.
- **Why?**
    1.  **Hidden Coupling**: In ODA, the Ontology (Schema) and Engine (Logic) are tightly fused. Changing a schema field (`Plan`) can cascade into parsing failures in the `Kernel`, validation errors in the `Registry`, and hallucination in the `GovernanceEngine`.
    2.  **Semantic Drift**: We fight to preserve the "Governance First" philosophy. Without deep understanding, new features become "patchwork code" that bypasses our architectural constraints (Technical Debt).
    3.  **Predictability**: "I think this works" is unacceptable. "I know this works because I traced the data flow" is the only standard.

**Your Rule**: Never move to the next step without `read_file` and `analyze_code_structure` to master the Control Flow & Data Schema. **"Deep Context Awareness" is "Safety".**

---

## 🏛️ PART 1: SYSTEM IDENTITY & EVOLUTIONARY CONTEXT

### **Core Philosophy: Ontology-Driven Architecture (ODA)**
- **Schema is Law**: `Plan` (Pydantic) is the only valid LLM output.
- **Governance by Design**: `ActionRegistry` + `GovernanceEngine` enforce safety via Metadata.
- **Disconnected Kernel**: The Kernel is a generic execution loop; it knows *how* to loop, but *what* to run comes from Data.

### **The Journey to Now (Contextual Causality)**
*Understanding where we came from prevents regression.*

1.  **Phase 1: The Identity Crisis (Resolved)**
    - *Problem*: We had two base classes (`OrionObject` vs `OntologyObject`) causing type conflicts.
    - *Solution*: Unified under `OntologyObject` (File 2) with optimistic locking (`version`).
    - *Impact*: All entities now share a consistent audit trail and ID strategy.

2.  **Phase 2: Governance by If-Statement (Refactored)**
    - *Problem*: The Kernel had hardcoded `if action == 'deploy': check_policy()`. This was fragile.
    - *Solution*: Introduced `ActionMetadata` (File 4). Policies are now attached to the Action Definition, not the Kernel.
    - *Impact*: The Kernel is now "Generic". It queries the Registry for policy.

3.  **Phase 3: Dictionary-Driven Planning (Fixed)**
    - *Problem*: LLMs returned raw JSON dicts, leading to runtime `KeyError`s during execution.
    - *Solution*: Enforced Pydantic `Plan` models (File 5). The Kernel validates schema *before* logic execution.
    - *Impact*: "Fail-Fast" architecture established.

4.  **Verification State**
    - **Status**: ✅ 11/11 E2E Scenarios Passed.
    - **Significance**: We proved that *Safe* actions run immediately, *Hazardous* actions trigger Proposals, and *Unknown* actions are denied—all without hardcoded logic.

---

## 📂 PART 2: PROJECT SKELETON (FILE STRUCTURE)
```text
.
├── pyproject.toml              # Dependencies: pydantic, sqlalchemy, uuid6
├── scripts/
│   ├── ontology/
│   │   ├── actions.py          # [CORE] ActionRegistry, GovernanceEngine (Coupled to Kernel)
│   │   ├── objects/
│   │   │   └── proposal.py     # [CORE] Proposal State Machine (Coupled to Repo)
│   │   ├── storage/
│   │   │   └── proposal_repository.py # [CORE] Persistence Logic (Manual SQL)
│   │   ├── ontology_types.py   # [CORE] Base Classes (OntologyObject)
│   │   ├── plan.py             # [CORE] LLM Output Schema (Coupled to Kernel Parser)
│   │   └── job.py              # [CORE] Job Schema
│   ├── runtime/
│   │   └── kernel.py           # [CORE] The Execution Loop (Consumer of All Above)
│   └── llm/
│       └── ollama_client.py    # [Adapter] LLM Client
└── tests/
    └── e2e/
        └── test_full_integration.py # [VERIFICATION] The Proof of Architecture
```

---

## 💻 PART 3: THE VIRTUAL CODEBASE (FLATTENED)

### **FILE 1: `pyproject.toml` (Environment)**
```toml
[project]
name = "orion-orchestrator"
version = "2.0.0"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "uuid6"
]
```

### **FILE 2: `scripts/ontology/ontology_types.py` (The Foundation)**
```python
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ObjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def generate_object_id() -> str:
    return str(uuid.uuid4())

class OntologyObject(BaseModel):
    """Base Domain Entity with Optimistic Locking.
    CAUSALITY: Breaking this class breaks Persistence and Audit trails system-wide."""
    id: str = Field(default_factory=generate_object_id)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    status: ObjectStatus = ObjectStatus.ACTIVE
    version: int = Field(default=1, ge=1)

    def touch(self, updated_by: Optional[str] = None):
        self.updated_at = utc_now()
        self.version += 1
        if updated_by: self.updated_by = updated_by
```

### **FILE 3: `scripts/ontology/objects/proposal.py` (The State Machine)**
```python
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import Field
# from ontology_types import OntologyObject, utc_now

class ProposalStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"   # Awaiting Review
    APPROVED = "approved" # Ready for Execution
    REJECTED = "rejected" # Terminal
    EXECUTED = "executed" # Terminal

class Proposal(OntologyObject):
    """Represents a hazardous action requiring Human Review.
    CAUSALITY: The 'status' field drives the Kernel's execution loop."""
    action_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: ProposalStatus = ProposalStatus.DRAFT
    priority: str = "medium"
    
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comment: Optional[str] = None
    executed_at: Optional[datetime] = None

    def submit(self):
        self.status = ProposalStatus.PENDING
        self.touch()

    def approve(self, reviewer_id: str):
        if self.status != ProposalStatus.PENDING: raise ValueError("Invalid State")
        self.status = ProposalStatus.APPROVED
        self.reviewed_by = reviewer_id
        self.reviewed_at = utc_now()
        self.touch()

    def execute(self, executor_id: str):
        if self.status != ProposalStatus.APPROVED: raise ValueError("Not Approved")
        self.status = ProposalStatus.EXECUTED
        self.executed_at = utc_now()
        self.touch()
```

### **FILE 4: `scripts/ontology/actions.py` (Discovery & Governance)**
```python
from typing import Type, Dict, Optional
from dataclasses import dataclass
# from ontology_types import OntologyObject

@dataclass
class ActionMetadata:
    """Metadata is the mechanism of Governance."""
    requires_proposal: bool = False
    is_dangerous: bool = False

class ActionRegistry:
    """The Source of Truth for Capabilities.
    CAUSALITY: New actions MUST be registered here to be visible to the Kernel."""
    def __init__(self):
        self._actions: Dict[str, tuple[Type, ActionMetadata]] = {}
    
    def register(self, cls, **overrides):
        api_name = getattr(cls, "api_name", cls.__name__)
        requires_proposal = overrides.get("requires_proposal", getattr(cls, "requires_proposal", False))
        self._actions[api_name] = (cls, ActionMetadata(requires_proposal=requires_proposal))
        
    def get_metadata(self, name: str) -> Optional[ActionMetadata]:
        entry = self._actions.get(name)
        return entry[1] if entry else None

action_registry = ActionRegistry()

class GovernanceEngine:
    """The Policy Decision Point.
    CAUSALITY: Returns 'REQUIRE_PROPOSAL' which forces Kernel to abort execution and save state."""
    def __init__(self, registry: ActionRegistry):
        self.registry = registry

    def check_execution_policy(self, action_name: str) -> str:
        meta = self.registry.get_metadata(action_name)
        if not meta: return "DENY"
        return "REQUIRE_PROPOSAL" if meta.requires_proposal else "ALLOW_IMMEDIATE"
```

### **FILE 5: `scripts/runtime/kernel.py` (The Semantic Loop)**
```python
# Imports skipped for brevity (Plan, Proposal, etc.)

class OrionRuntime:
    """The ODA Kernel.
    CAUSALITY: 
    1. Consumes 'Plan' (Schema)
    2. Queries 'GovernanceEngine' (Logic)
    3. Mutates 'ProposalRepository' (Persistence)"""
    
    async def _process_task_cognitive(self, plan: Plan):
        for job in plan.jobs:
            policy = self.governance.check_execution_policy(job.action_name)
            
            if policy == "DENY":
                logger.error(f"Action {job.action_name} DENIED")
                
            elif policy == "REQUIRE_PROPOSAL":
                # HAZARDOUS: Create Proposal
                proposal = Proposal(
                    action_type=job.action_name,
                    payload=job.action_args,
                    status=ProposalStatus.PENDING
                )
                await self.repo.save(proposal)
                logger.info(f"Proposal Created: {proposal.id}")
                
            elif policy == "ALLOW_IMMEDIATE":
                # SAFE: Execute Now
                action_cls = action_registry.get(job.action_name)
                await action_cls().execute(job.action_args)
```

---

## ✅ PART 4: THE VERIFICATION (E2E TEST)
**File: `tests/e2e/test_full_integration.py`**
> **Summary**: This test ran successfully (11 passed scenarios).
> **Why it validates Architecture**: It proves that the *decoupling* works. The Kernel didn't need to know *what* "Check Health" does; it just asked the Registry allowed it. The Kernel didn't need to know *how* to govern "Deploy"; it just followed the `REQUIRE_PROPOSAL` signal from the Engine.

---

## 🔮 PART 5: DEEP RESEARCH PROTOCOL (NEXT STEPS)

**MISSION**: We need to evolve this from a "Working Prototype" to "Enterprise Grade".
**EXECUTE THE FOLLOWING RESEARCH WITH 'DYNAMIC IMPACT ANALYSIS' IN MIND**:

### 1. **Instructor (Python) Integration**
- **Goal**: Replace Mock LLM with real OpenAI/Ollama structured outputs.
- **Impact Risk**: How does `instructor` handle validation errors? Will it crash our `Kernel` loop or provide a retry mechanism?
- **Search**: "instructor python pydantic wrapper pattern for ollama and openai compatible"
- **Output**: A snippet patching `OllamaClient` to return our `Plan` Pydantic model.

### 2. **SQLAlchemy 2.0 Async Migration**
- **Goal**: Replace manual strings in `ProposalRepository` with strict ORM.
- **Impact Risk**: Our `OntologyObject` uses `version` for optimistic locking. The ORM must implement this *exactly* or we lose concurrency safety.
- **Search**: "sqlalchemy 2.0 async optimistic locking version column pattern"
- **Output**: A Declarative Base class mirroring our `OntologyObject`.

### 3. **FastAPI + React Dashboard**
- **Goal**: A UI for Approvals.
- **Impact Risk**: Exposing our internal `Proposal` objects to an API requires strict serialization (DTOs) to prevent leaking internal audit data.
- **Search**: "fastapi mount react static files production pattern"
- **Output**: Architecture for a monolithic "Agent Control Tower".

---

**FINAL DELIVERABLE**:
Produce `docs/ROADMAP_PHASE_4_5_6.md` containing the Tech Stack Table, Migration Snippets (ORM/Instructor), and a 2-week Sprint Plan.
