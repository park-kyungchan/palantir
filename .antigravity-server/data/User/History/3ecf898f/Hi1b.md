# ODA 3-Stage Protocol Framework - Implementation Plan

**Date:** 2026-01-05
**Protocol:** ANTIGRAVITY_ARCHITECT_V5.0
**Method:** RECURSIVE-SELF-IMPROVEMENT LOOP (4 iterations)

---

## Goal

Embed **3-Stage Deep-Dive Protocol** as an **enforced framework** at scripts-level, covering:
- Audit, Planning, Tasks, Execution, Orchestration

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 ODA 3-STAGE PROTOCOL FRAMEWORK              │
├─────────────────────────────────────────────────────────────┤
│  Stage A (SCAN) ──▶ Stage B (TRACE) ──▶ Stage C (VERIFY)    │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌─────────────────────────────────────────────────┐        │
│  │         StageResult (with Evidence)             │        │
│  └─────────────────────────────────────────────────┘        │
│                          │                                  │
│  ┌────────────────────────────────────────────────────┐     │
│  │         @require_protocol / GovernanceEngine       │     │
│  └────────────────────────────────────────────────────┘     │
│            ┌─────────────┼─────────────┐                    │
│            ▼             ▼             ▼                    │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│     │ActionType│  │ Proposal │  │MCP Server│                │
│     └──────────┘  └──────────┘  └──────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## Proposed Changes

### Phase 1: Core Framework

#### [NEW] `scripts/ontology/protocols/__init__.py`
Export all protocol components.

#### [NEW] `scripts/ontology/protocols/base.py`
Core abstractions:
- `Stage` enum (A_SCAN, B_TRACE, C_VERIFY)
- `StageResult` dataclass with `evidence` field
- `ProtocolResult` with pass/fail and all stage results
- `ThreeStageProtocol` abstract base class

#### [NEW] `scripts/ontology/protocols/decorators.py`
- `@require_protocol(ProtocolClass)` - Enforce before action
- `@stage_a`, `@stage_b`, `@stage_c` - Stage markers

---

### Phase 2: Protocol Implementations

#### [NEW] `scripts/ontology/protocols/audit_protocol.py`
| Stage | Purpose |
|-------|---------|
| A | Surface Scan - File structure, key patterns |
| B | Logic Trace - Data flow analysis |
| C | Quality Audit - Line-by-line review |

#### [NEW] `scripts/ontology/protocols/planning_protocol.py`
| Stage | Purpose |
|-------|---------|
| A | Blueprint - Requirements gathering |
| B | Integration - How it connects |
| C | Quality Gate - Design review |

#### [NEW] `scripts/ontology/protocols/execution_protocol.py`
| Stage | Purpose |
|-------|---------|
| A | Pre-Check - Dependencies, state |
| B | Execute - Actual work |
| C | Validate - Verify outcome |

---

### Phase 3: Integration

#### [MODIFY] `scripts/ontology/actions/__init__.py`
- Add `protocol_required` to `ActionMetadata`
- Add `check_protocol_compliance()` to `GovernanceEngine`
- New `PolicyResult.REQUIRE_PROTOCOL` decision

#### [MODIFY] `scripts/ontology/objects/proposal.py`
- `submit()` validates protocol completion

#### [MODIFY] `scripts/mcp/ontology_server.py`
- Wrap tool calls with protocol check

---

### Phase 4: Enforcement Modes

```python
class ProtocolPolicy(str, Enum):
    BLOCK = "block"    # Cannot proceed without passing
    WARN = "warn"      # Logs warning but proceeds
    SKIP = "skip"      # Protocol not required
```

---

## Anti-Hallucination Design

**StageResult.evidence** MUST include:
```python
evidence = {
    "files_viewed": ["path/to/file.py"],
    "lines_referenced": {"file.py": [42, 55, 100]},
    "code_snippets": {"file.py:42": "def my_function():"}
}
```

---

## Verification Plan

### Automated Tests
- `test_protocol_enforcement.py` - Block without protocol
- `test_stage_results.py` - Evidence validation

### Manual Verification
- Run deep-audit workflow with new framework
- Verify protocol logs in audit trail

---

## Impact

| Before | After |
|--------|-------|
| 3-Stage is a guideline | 3-Stage is enforced |
| No evidence tracking | Evidence in StageResult |
| Hallucination possible | Anti-hallucination via evidence |
