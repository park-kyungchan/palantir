# Decision 011: Cross-Phase Handoff Protocol

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 42 agents (D-005) · D-007 BN-003  
**Depends on:** Decision 005, Decision 007, Decision 008

---

## 1. Problem Statement

Lead is the single point of context transfer between phases. Phase N's output is read
by Lead, interpreted, and constructed into Phase N+1's directive. Each handoff is a
potential information loss point.

With D-005:
- P3 architecture-coordinator produces consolidated L2 from 3 architect workers
- Lead must read, interpret, construct → P4 planning-coordinator directive  
- P4 planning-coordinator produces consolidated L2 from 3 planner workers
- Lead must read, interpret, construct → P5 validation-coordinator directive
- **7+ sequential handoffs in a COMPLEX pipeline: P2→P3→P4→P5→P6→P7→P8→P9**

**Core question:** What information MUST survive each handoff, and how do we prevent
progressive context degradation (the "telephone game" problem)?

---

## 2. Current State

### 2.1 Current Handoff Mechanism

```
Phase N completes:
  1. Coordinator writes consolidated L2-summary.md
  2. Coordinator reports to Lead via SendMessage
  3. Lead reads L2 + (optionally) L1
  4. Lead evaluates Gate N
  5. Lead constructs Phase N+1 directive

Phase N+1 starts:
  6. Lead spawns coordinator with directive containing:
     - PERMANENT Task reference
     - Phase N findings (paraphrased by Lead)
     - Phase N+1 specific instructions
     - File/scope assignments
```

### 2.2 Information Loss Points

| Step | Loss Risk | Cause |
|------|-----------|-------|
| Step 1 → Step 3 | MEDIUM | Lead may read L2 but skip L1 details (YAML structured data) |
| Step 3 → Step 5 | **HIGH** | Lead PARAPHRASES Phase N output into directive. Nuance lost. |
| Step 5 → Step 6 | LOW | Directive is written by Lead — what Lead writes, coordinator receives |
| Step 6 → workers | MEDIUM | Coordinator distributes directive to workers, may simplify |
| Cross-pipeline | **HIGH** | PERMANENT Task is only persistent artifact. If PT is not updated with Phase N key conclusions, they're lost. |

### 2.3 The "Telephone Game" Risk

Concrete example of progressive degradation across P3→P4→P5:

```
P3 architect discovers: "Module X has a hidden circular dependency with Module Y
  through a transitive path via Module Z's interface adapter."

→ P3 coordinator L2 summarizes: "Circular dependency found between Module X and Y."
  (lost: Module Z involvement, transitive nature, interface adapter detail)

→ Lead reads L2, constructs P4 directive: "Be aware of X↔Y dependency."
  (lost: circular nature, resolution required)

→ P4 planner receives: "X depends on Y"
  (transformed from circular dependency to simple dependency — plan may not address it)

→ P5 challenger receives plan: checks "are dependencies handled?"
  (sees X→Y and Y→(nothing) — never catches the circular issue)

Original finding completely lost by Phase 5.
```

---

## 3. Analysis

### 3.1 What MUST Survive Each Handoff

| Category | Examples | Why It's Critical |
|----------|---------|-------------------|
| **Architecture Decisions** | ADR-001: "Use event-driven pattern for X" | Downstream phases build on these; if lost, conflicting decisions emerge |
| **Risk Warnings** | "Circular dependency in X↔Y↔Z" | If lost, risk manifests as bug in P6 — 10x costlier to fix |
| **Interface Contracts** | "Module A exports fn(x: string): Promise\<Result\>" | If lost, implementers create incompatible APIs |
| **Constraints** | "No external HTTP calls in Module X (security)" | If lost, implementer violates constraint unknowingly |
| **Open Questions** | "User needs to clarify: single DB or multi-tenant?" | If lost, assumption made without user input |
| **File Scope** | "Module X: src/core/engine.ts, src/core/types.ts" | If lost, ownership conflicts in P6 |

### 3.2 What Can Be Safely Summarized

| Category | Examples | Why It's Safe to Summarize |
|----------|---------|--------------------------|
| Analysis methodology | "We used 3 searchers to find all usages" | Process details, not findings |
| Tool calls and discovery process | "Grep found 47 references" | Evidence trail, captured in L3 |
| Intermediate reasoning | "Considered 3 alternatives before choosing" | Already distilled into decision |
| Verification sources | "Checked against docs.palantir.com/..." | URLs captured in Evidence Sources |

### 3.3 The PT Connection

The PERMANENT Task already serves as persistent context, but its Codebase Impact Map
is a LIVING DOCUMENT that must be updated at each handoff:

```
PERMANENT Task Impact Map (evolves through phases):

P2: Impact Map = { files: [discovered files], patterns: [discovered patterns] }
P3: Impact Map += { decisions: [ADRs], risks: [identified risks], interfaces: [defined contracts] }
P4: Impact Map += { plan: [task breakdown], ownership: [file assignments], dependencies: [task chain] }
P5: Impact Map += { challenges: [resolved], conditions: [CONDITIONAL items], approved_risks: [accepted] }
P6: Impact Map += { implementations: [completed tasks], reviews: [verdicts], changes: [actual file changes] }
P7: Impact Map += { tests: [results], coverage: [assessment], failures: [unresolved] }
```

**Problem:** PT updates are Lead-authored. If Lead doesn't update PT with Phase N's
key findings, the next phase starts with stale context.

---

## 4. Proposed: Standardized Handoff Protocol

### 4.1 Coordinator L2 Mandatory Sections

Every coordinator's L2-summary.md must include a **"Downstream Handoff"** section
at the end, structured as follows:

```markdown
## Downstream Handoff

### Decisions Made (Forward-binding)
These decisions MUST be respected by downstream phases.
- [AD-1] Event-driven pattern for Module X (cannot be changed without re-architecture)
- [AD-2] PostgreSQL selected for persistence (migration cost if changed: HIGH)

### Risks Identified (Must-Track)
These risks require monitoring or mitigation in downstream phases.
- [R-1] Circular dependency X↔Y↔Z via interface adapter. Must be resolved in planning.
- [R-2] Module Z has no test coverage in existing codebase. Testing phase must address.

### Interface Contracts (Must-Satisfy)
These contracts were defined and downstream phases MUST satisfy them.
- [IC-1] Module A exports: `processEvent(e: Event): Promise<Result>`
- [IC-2] Module B expects: `ConfigSchema` interface from Module A

### Constraints (Must-Enforce)
These constraints were established and must be enforced downstream.
- [C-1] No external HTTP in Module X (security requirement)
- [C-2] Maximum 3 database queries per request (performance requirement)

### Open Questions (Requires Resolution)
These questions were NOT resolved and need user or downstream attention.
- [OQ-1] Single DB or multi-tenant? (blocks P6 database layer implementation)

### Artifacts Produced
- L1: `L1-index.yaml` (structured findings)
- L2: this file
- L3: `L3-full/` (per-worker detailed reports)
```

### 4.2 Lead Gate → PT Update Protocol

After Lead evaluates a gate and PASSES it:

```
Gate N PASS:
  1. Read coordinator's "Downstream Handoff" section
  2. Update PERMANENT Task:
     - Add Decisions to Architecture Decisions section
     - Add Risks to Constraints or create Risk Registry
     - Add Interface Contracts to a new "Active Contracts" section
     - Add Open Questions to Constraints (blocked items)
  3. Mark handoff items as "PT-synced: ✅" in Phase N directory
  4. Construct Phase N+1 directive referencing PT (NOT paraphrasing handoff)
```

### 4.3 Phase N+1 Directive Template

Instead of Lead paraphrasing Phase N output, the directive references PT directly:

```markdown
## Directive for {Phase N+1 Coordinator}

### Context Source
Read the PERMANENT Task via TaskGet for full project context.
Key sections updated from Phase {N}:
- Architecture Decisions: {count} decisions (AD-1 through AD-{N})
- Active Risks: {count} risks (R-1 through R-{N})
- Interface Contracts: {count} contracts (IC-1 through IC-{N})
- Open Questions: {count} unresolved items

### Phase-Specific Input
Read Phase {N} coordinator's L2 at: {path}
Focus on: "Downstream Handoff" section for items requiring your attention.

### Your Mission
{Phase N+1 specific instructions}

### Workers Assigned
{worker list with dimension assignments}
```

**Critical difference:** Lead does NOT paraphrase. Lead says "read PT" and "read L2 handoff."
This eliminates the telephone game — the coordinator reads the SOURCE, not Lead's summary.

### 4.4 Information Flow Diagram

```
Before (telephone game):
  P3 Coordinator → L2 → Lead reads → Lead paraphrases → Directive → P4 Coordinator
                                   ↗ LOSS POINT ↘

After (direct reference):
  P3 Coordinator → L2 → Lead reads → Lead updates PT → Directive references PT + L2
                                    ↘              ↗
                                      NO PARAPHRASE
                                   
  P4 Coordinator → reads PT + reads P3 L2 directly → Full context preserved
```

---

## 5. Cross-Coordinator Direct Handoff (Advanced)

### 5.1 Current Model: All Through Lead
```
P3 Coordinator → Lead → P4 Coordinator → Lead → P5 Coordinator
```

### 5.2 Proposed Enhancement: Coordinator File Handoff
Coordinators write output to a KNOWN path. Next coordinator reads it directly.

```
Standard output path: .agent/teams/{team}/phase-{N}/coordinator/L2-summary.md
Next coordinator reads: .agent/teams/{team}/phase-{N-1}/coordinator/L2-summary.md
```

**This does NOT bypass Lead.** Lead still evaluates gates and spawns next coordinator.
But the next coordinator can ALSO read the previous coordinator's output directly,
reducing dependence on Lead's directive quality.

### 5.3 Risk Assessment
- **Pro:** Eliminates information loss. Next coordinator gets full source material.
- **Con:** Coordinator reads previous phase output without Lead's filtering.
  Could lead to information overload.
- **Mitigation:** The "Downstream Handoff" section IS the filter — coordinators
  focus on this section, not the entire L2.

---

## 6. Options

### Option A: Mandatory Handoff Section Only
- Add "Downstream Handoff" section to coordinator L2 format
- No changes to Lead's directive construction process
- Lead still paraphrases but has better source material

### Option B: Handoff Section + PT Update Protocol
- Add handoff section (§4.1) + Lead gate→PT update protocol (§4.2)
- Lead references PT instead of paraphrasing
- Eliminates telephone game for PT-synced items

### Option C: Full Protocol + Direct File Handoff (Recommended)
- §4.1 handoff section + §4.2 PT update + §4.3 directive template
- §5.2 coordinator cross-read capability
- Maximum information preservation

### Option D: Minimal — Let Opus-4.6 Handle It
- No changes. Trust Lead's 200K context window to preserve information.
- Rely on PT as-is for persistence.

---

## 7. Interaction with Other Decisions

| Decision | Interaction |
|----------|------------|
| D-005 | New coordinators must implement handoff section in their L2 format |
| D-007 BN-003 | This decision directly resolves BN-003 |
| D-008 | Gate evaluation includes "Evidence Collection" — handoff L2 is primary evidence |
| D-009 | Category memory accumulates cross-phase patterns from handoff items |
| D-012 | PT structure must accommodate handoff items (Decisions, Risks, Contracts) |
| D-013 | Handoff section format is part of coordinator shared protocol |
| D-016 | CLAUDE.md may need "Handoff Protocol" section |

---

## 8. User Decision Items

- [ ] Which option? (A / B / **C recommended** / D)
- [ ] Accept 6-category handoff section (Decisions/Risks/Contracts/Constraints/Questions/Artifacts)?
- [ ] Accept Lead gate→PT update protocol?
- [ ] Accept directive template (reference-based, not paraphrase-based)?
- [ ] Accept coordinator cross-read capability (§5.2)?
- [ ] Should handoff items have standardized IDs (AD-N, R-N, IC-N, C-N, OQ-N)?

---

## 9. Claude Code Directive (Fill after decision)

```
DECISION: Handoff protocol — Option [X]
SCOPE:
  - agent-common-protocol.md: Add "Downstream Handoff" section requirement for coordinators
  - All coordinator .md files: Reference handoff format
  - Skills: Update gate evaluation to include PT update step
  - PT structure: Add Architecture Decisions, Active Contracts, Risk Registry sections
  - Lead directive template: Reference-based (not paraphrase-based)
CONSTRAINTS:
  - Handoff section ≤ 30 lines per gate passage
  - ID format: AD-N, R-N, IC-N, C-N, OQ-N
  - PT update is Lead-only (agents cannot modify PT)
  - Coordinator cross-read is optional (not required)
PRIORITY: Handoff section > PT update > Directive template > Cross-read
DEPENDS_ON: D-005 (coordinator list), D-008 (gate evaluation), D-012 (PT structure)
```
