# Domain 3: brainstorming-pipeline → agent-teams-write-plan Interface Analysis

## Source Files
- `.claude/skills/brainstorming-pipeline/SKILL.md` (481 lines)
- `docs/plans/2026-02-07-brainstorming-pipeline-design.md` (755 lines)

## GC-v3 Complete Structure (brainstorming-pipeline output)

### From GC-v1 (Phase 1 — Discovery):
```yaml
---
version: GC-v1
created: {YYYY-MM-DD}
feature: {feature-name}
complexity: {SIMPLE|MEDIUM|COMPLEX}
---
```

Sections:
- **Scope**: Goal, In/Out Scope, Approach, Success Criteria, Estimated Complexity, Phase 2 Research Needs, Phase 3 Architecture Needs
- **Phase Pipeline Status**: Phase 1 COMPLETE
- **Constraints**: From Q&A
- **Decisions Log**: D-1+ with rationale and phase

### From GC-v2 (Phase 2 — Research):
Added sections:
- **Research Findings**: Synthesized from researcher L2 summaries
- **Codebase Constraints**: Discovered technical limitations
- **Phase 3 Architecture Input**: Key information architect needs
- **Phase Pipeline Status** updated: Phase 2 COMPLETE

### From GC-v3 (Phase 3 — Architecture):
Added sections:
- **Architecture Decisions**: Synthesized from architect L1/L2
- **Component Map**: Component list with responsibilities
- **Interface Contracts**: Key interfaces between components
- **Phase 4 Entry Requirements**: What Detailed Design needs
- **Phase Pipeline Status** updated: Phase 3 COMPLETE, Phase 4 PENDING

## What architect-1 needs from GC-v3 for Phase 4

| GC-v3 Section | Architect Usage in Phase 4 |
|---------------|---------------------------|
| Scope (Goal, Approach) | Bounds the implementation plan scope — what to build, what not to |
| Component Map | Decompose into implementer tasks — each component or component group → task |
| Interface Contracts | Define file ownership boundaries — interface provider and consumer → separate implementer scopes |
| Architecture Decisions | Translate design into concrete code — each decision becomes edit/create spec |
| Phase 4 Entry Requirements | Explicit checklist — what must be addressed in the plan |
| Research Findings | Technical constraints — existing APIs/patterns to reuse or avoid |
| Codebase Constraints | Hard limitations — things that cannot be changed |
| Constraints | Business/user constraints from Phase 1 |
| Decisions Log | Full decision trail — architect can reference D-N for rationale |

## GC-v4 Design (agent-teams-write-plan output)

### New Sections to ADD at GC-v3 → GC-v4:

```markdown
## Implementation Plan Reference
- Plan document: `docs/plans/YYYY-MM-DD-{feature-name}.md`
- Design source: `{session-dir}/phase-3/architect-1/L3-full/architecture-design.md`
- Plan author: architect-1 (Phase 4)

## Task Decomposition
| Task | Subject | Implementer | blockedBy | Files |
|------|---------|-------------|-----------|-------|
| A | {subject} | implementer-1 | [] | {file list} |
| B | {subject} | implementer-2 | [A] | {file list} |
{...}

## File Ownership Map
| Implementer | Files Owned | Operation |
|-------------|------------|-----------|
| implementer-1 | {file list} | CREATE/MODIFY |
| implementer-2 | {file list} | CREATE/MODIFY |

## Phase 6 Entry Conditions
- All implementation plan sections complete
- File ownership non-overlapping verified
- Task dependencies acyclic
- Acceptance criteria specific and verifiable
- {feature-specific conditions}

## Phase 5 Validation Targets
- {verifiable assertion 1}
- {verifiable assertion 2}
{These feed into devils-advocate Phase 5 skill}

## Commit Strategy
- Approach: {single | per-task | per-implementer}
- Justification: {why this approach}
```

### Sections to UPDATE:

```markdown
## Phase Pipeline Status
- Phase 1: COMPLETE
- Phase 2: COMPLETE
- Phase 3: COMPLETE (Gate 3 APPROVED)
- Phase 4: COMPLETE (Gate 4 APPROVED)
- Phase 5: PENDING (plan validation)
```

### Sections PRESERVED from GC-v3 (no modification):
- Scope, Constraints, Decisions Log (add Phase 4 decisions)
- Research Findings, Codebase Constraints
- Architecture Decisions, Component Map, Interface Contracts
- Phase 4 Entry Requirements (mark as satisfied)

## Pipeline Connection Diagram

```
brainstorming-pipeline          agent-teams-write-plan           [Phase 5 skill]
──────────────────────          ──────────────────────           ────────────────
P1: Discovery (Lead)
  → GC-v1
P2: Research (researcher)
  → GC-v2
P3: Architecture (architect)
  → GC-v3
  → architecture-design.md
  → L1/L2/L3
Gate 3 APPROVE
  → Shutdown architect
  → TeamDelete
  → Preserve artifacts
  → User message:
    "Next: Phase 4"
                                 User invokes skill
                                 Lead reads artifacts:
                                   → GC-v3
                                   → architecture-design.md
                                   → researcher L2
                                 TeamCreate (new team)
                                 Spawn architect-1 (new)
                                 DIA: TIER 2 + LDAP MAXIMUM
                                 Architect produces plan:
                                   → docs/plans/{feature}.md
                                   → L1/L2/L3
                                 Gate 4 APPROVE
                                   → GC-v3 → GC-v4
                                 Shutdown architect
                                 TeamDelete
                                 User message:
                                   "Next: Phase 5"
                                                                  User invokes skill
                                                                  Reads GC-v4
                                                                  Reads plan doc
                                                                  devils-advocate
                                                                  validates plan

```

## Session Continuity Mechanism

### Problem
brainstorming-pipeline does `TeamDelete` at termination. This cleans up team coordination files but preserves `.agent/teams/{session-id}/` artifacts. agent-teams-write-plan needs to find these artifacts.

### Solution: Hybrid Auto-Discovery

**Dynamic Context Injection block for the skill:**
```markdown
**Previous Pipeline Output:**
!`ls -d /home/palantir/.agent/teams/*/global-context.md 2>/dev/null | while read f; do dir=$(dirname "$f"); echo "---"; echo "Dir: $dir"; head -6 "$f"; done`
```

This auto-discovers all session directories with global-context.md files. The skill Lead can then:
1. Parse the output to find GC-v3 with "Phase 3: COMPLETE"
2. If multiple candidates, present to user via AskUserQuestion
3. If single candidate, confirm with user
4. Read the selected session's artifacts

**$ARGUMENTS usage:**
User can also provide explicit path: `/agent-teams-write-plan .agent/teams/{specific-session}/`

### Data Flow

```
brainstorming-pipeline artifacts       agent-teams-write-plan reads
─────────────────────────────────      ──────────────────────────────
{session-id}/global-context.md    →    GC-v3 (full context)
{session-id}/phase-3/architect-1/
  L1-index.yaml                   →    Architecture summary
  L2-summary.md                   →    Architecture narrative
  L3-full/architecture-design.md  →    Full architecture design
{session-id}/phase-2/researcher-*/
  L2-summary.md                   →    Research findings (reference)
{session-id}/orchestration-plan.md →   Pipeline history
{session-id}/phase-*/gate-record.yaml → Gate results
```

## Key Design Considerations

1. **New team, new session-id**: agent-teams-write-plan creates its own `.agent/teams/{new-session-id}/` for Phase 4 artifacts. It reads from the brainstorming-pipeline's session directory but writes to its own.

2. **Architect is new instance**: The Phase 3 architect is shut down. Phase 4 spawns a new architect-1 who receives all context via CIP injection (GC-v3 embedded + architecture-design.md as reference).

3. **Plan dual-save**: Implementation plan saved to both `docs/plans/` (permanent, for future sessions) and `.agent/teams/{new-session-id}/phase-4/architect-1/L3-full/` (session artifacts).

4. **GC version continuity**: GC-v3 from brainstorming-pipeline is copied to the new session directory and updated to GC-v4 at Gate 4. The version numbering continues across skills.
