# Decision 015: L1/L2/L3 Output Format Standardization

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 42 agents (D-005) · agent-common-protocol §Output  
**Depends on:** Decision 005, Decision 011, Decision 013

---

## 1. Problem Statement

Every agent produces L1/L2/L3 output, but format consistency varies:
- L1: YAML structure varies (different key names, nesting levels)
- L2: Markdown structure varies (different section ordering, content depth)
- L3: Directory structure varies (per-worker vs per-topic organization)

Consumers of these outputs (coordinators, Lead, downstream phases) must adapt to
each agent's format. With 42 agents, format inconsistency becomes a readability
and automation barrier.

**Core question:** Should L1/L2/L3 formats be standardized, and if so, to what degree?

---

## 2. Current State (Code-Level Audit)

### 2.1 L1 (YAML Index) Format Variations

| Agent Category | L1 Format | Key Fields |
|----------------|-----------|------------|
| Researchers | findings list + counts | `findings: [{id, summary, source, pt_goal_link}]` |
| Verifiers | findings + verdicts | `findings: [{id, claim, verdict, evidence}]` |
| Architects | decisions + risks | Unspecified — varies |
| Implementers | task status + files | `tasks: [{id, status, files_changed}]` |
| Reviewers | verdict + issues | Unspecified — output via SendMessage, not L1 |
| Coordinators | per-worker status | `workers: [{name, status, findings_count}]` |
| Auditor | inventory + gaps | `audit: [{category, count, coverage_pct}]` |

**Issue:** No mandatory schema. `pt_goal_link` is "optional" per protocol.
Some agents have detailed L1 specs in their `.md`, others say only "L1-index.yaml: {brief}".

### 2.2 L2 (Markdown Summary) Format Variations

All agents produce L2 as markdown, but section ordering differs:

| Agent | L2 Sections (observed) |
|-------|----------------------|
| Researchers | Summary → Findings → Evidence Sources → PT Goal Linkage |
| Verifiers | Summary → Per-Claim Results → Cross-Dimension → Evidence Sources |
| Architects | Summary → ADRs → Risk Matrix → Component Design (D-005 TBD) |
| Implementers | Summary → Changes → Self-Review → Files |
| Coordinators | Summary → Per-Worker Results → Cross-Dimension Synthesis → Evidence Sources |

**Issue:** "Evidence Sources" section is required by agent-common-protocol but its
placement (beginning vs end) and format varies. D-011 adds a mandatory "Downstream
Handoff" section for coordinators — where does it go relative to Evidence Sources?

### 2.3 L3 (Detailed Output) Format Variations

L3 is inherently varied because it captures raw work product. No standardization
needed or desired for L3 contents.

### 2.4 Where Outputs Are Stored

```
.agent/teams/{team}/phase-{N}/{agent-role}/
├── L1-index.yaml
├── L2-summary.md
└── L3-full/
    └── (agent-specific detailed files)
```

Path structure is consistent. File names are consistent. It's the CONTENT that varies.

---

## 3. Analysis

### 3.1 Who Reads Agent Output?

| Consumer | What They Read | What They Need |
|----------|---------------|----------------|
| **Coordinator** | Worker L1 + L2 | Quick status (L1) + detailed findings for synthesis (L2) |
| **Lead** | Coordinator L2 (not worker) | Gate evidence + downstream handoff (L2) |
| **Next-phase agents** | Previous coordinator L2 | Handoff items: decisions, risks, contracts (L2) |
| **Execution monitor** | Implementer L1 | Task status, files changed (L1) |
| **Delivery pipeline** | All L1 + coordinator L2 | Consolidation for commit (L1 + L2) |

### 3.2 Pain Points

| Pain Point | Impact | Frequency |
|-----------|--------|-----------|
| Coordinator reads 3 worker L1s with different schemas | Must parse each differently | Every coordinated phase |
| Lead searches for "Evidence Sources" in L2 | Varies: sometimes at top, sometimes at bottom | Every gate |
| Delivery pipeline consolidates L1 across agents | Must handle N different YAML schemas | Every P9 |
| D-011 Downstream Handoff section placement | Undefined — each coordinator might put it differently | Every handoff |

### 3.3 Standardization vs Flexibility Trade-off

**Over-standardization risk:** Forcing all agents into identical formats may lose
domain-specific value. An architect's L1 (ADRs, risk matrix) is fundamentally different
from a tester's L1 (test results, coverage).

**Under-standardization risk:** Consumers spend tokens parsing different formats.
Automation (delivery consolidation) becomes brittle.

**Balance:** Standardize the STRUCTURE (required sections, ordering) but not the
CONTENT (domain-specific fields within sections).

---

## 4. Proposed: L1/L2 Canonical Formats

### 4.1 L1 Canonical Schema

```yaml
# L1-index.yaml — Universal Schema
# All agents MUST include these top-level keys.
# Domain-specific keys are added underneath.

agent: {role-id}
phase: {P-number}
status: {complete|in_progress|blocked}
timestamp: {ISO 8601}

# --- Domain-specific section (varies by role) ---
# Researchers: findings: [{id, summary, source, verdict, pt_goal_link}]
# Implementers: tasks: [{id, status, files_changed, pt_goal_link}]
# Reviewers: reviews: [{task_id, verdict, issues_count}]
# Coordinators: workers: [{name, status, findings_count}]
# etc.

# --- Universal footer ---
evidence_count: {N}        # Number of evidence items in L2
pt_goal_links:             # All pt_goal_link values aggregated
  - "R-1 (Requirement Name)"
  - "AD-3 (Decision Name)"
```

**Mandatory keys (4):** `agent`, `phase`, `status`, `timestamp`
**Recommended keys (2):** `evidence_count`, `pt_goal_links`
**Domain-specific keys:** Free-form, per agent `.md` specification

### 4.2 L2 Canonical Section Order

```markdown
# L2-summary.md — Universal Section Order

## Summary
{1-3 sentence executive summary of this agent's work}

## {Domain-Specific Sections}
{Varies by role — findings, decisions, reviews, test results, etc.}
{Multiple sections allowed — ordered by agent's .md specification}

## Evidence Sources
{Required by agent-common-protocol}
- Key references, MCP tool findings, verification data
- URLs, file paths, cross-agent references

## PT Goal Linkage
{Optional but recommended — connecting work to requirements}
- R-1: {how this work addresses requirement 1}
- AD-3: {how this work implements decision 3}

## Downstream Handoff
{ONLY for coordinators — required by D-011}
### Decisions Made (forward-binding)
### Risks Identified (must-track)
### Interface Contracts (must-satisfy)
### Constraints (must-enforce)
### Open Questions (requires resolution)
### Artifacts Produced
```

**Rules:**
1. `## Summary` is ALWAYS first
2. Domain-specific sections follow Summary
3. `## Evidence Sources` is ALWAYS second-to-last (or last for non-coordinators)
4. `## PT Goal Linkage` is ALWAYS before Evidence Sources (if present)
5. `## Downstream Handoff` is ALWAYS last (coordinators only, per D-011)

### 4.3 L3 Format

**No standardization.** L3 is raw work product. Directory structure at agent discretion.
Only requirement: L3 lives in `L3-full/` subdirectory.

---

## 5. Implementation Path

### 5.1 Where to Document

The canonical formats belong in `agent-common-protocol.md` under existing
"Saving Your Work" section, expanded with L1/L2 canonical format specifications.

### 5.2 Agent `.md` Updates

Each agent's "Output Format" section should reference the canonical format:

```markdown
## Output Format
Follow L1/L2 canonical format from agent-common-protocol.md.
Domain-specific additions:
- **L1-index.yaml:** Add `findings: [{id, summary, verdict, evidence}]`
- **L2-summary.md:** Domain sections: Findings → Cross-Dimension Synthesis
- **L3-full/:** Per-topic analysis files
```

### 5.3 Backward Compatibility

Existing agents already produce L1/L2 — this standardization ADDS mandatory keys
and section ordering. It does NOT remove existing fields. Migration is additive.

---

## 6. Options

### Option A: Full Standardization (L1 schema + L2 order)
- Define canonical L1 YAML schema with mandatory + domain keys
- Define canonical L2 section order
- Update agent-common-protocol.md
- Update all 42 agent `.md` files to reference canonical format

### Option B: L2 Order Only
- Standardize L2 section ordering (Summary first, Evidence last)
- Leave L1 format per agent
- Lower implementation effort

### Option C: No Standardization
- Let each agent self-determine format
- Coordinators and Lead adapt per agent

### Option D: Canonical Format + Progressive Adoption (Recommended)
- Define canonical L1 + L2 formats in agent-common-protocol.md
- Mandatory for D-005 new agents (created from scratch)
- Progressive adoption for existing agents (updated when next modified)
- D-011's Downstream Handoff placement formalized (last section)

---

## 7. User Decision Items

- [ ] Which option? (A / B / C / **D recommended**)
- [ ] Accept L1 mandatory keys: agent, phase, status, timestamp?
- [ ] Accept L2 section order: Summary → Domain → PT Linkage → Evidence → Handoff?
- [ ] Accept L3 as unstandardized?
- [ ] Accept progressive adoption for existing agents?
- [ ] Should L1 pt_goal_links be mandatory or recommended?

---

## 8. Claude Code Directive (Fill after decision)

```
DECISION: Output format standardization — Option [X]
SCOPE:
  - agent-common-protocol.md §Saving Your Work: add L1/L2 canonical format
  - New D-005 agents: created with canonical format references
  - Existing agents: progressive adoption on next modification
CONSTRAINTS:
  - L3 remains unstandardized (domain-specific)
  - Backward compatible — adds keys, doesn't remove
  - pt_goal_links: recommended, not mandatory
  - Downstream Handoff (D-011): always last section in L2
PRIORITY: L2 ordering > L1 schema > Agent .md updates
DEPENDS_ON: D-005 (new agents), D-011 (handoff placement), D-013 (coordinator protocol)
```
