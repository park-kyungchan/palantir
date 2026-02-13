# L2-summary.md — researcher-protocol (COA-1~5)

## Status: COMPLETE

## Executive Summary

Designed 5 interconnected COA protocols as a **layered system**, not 5 independent additions. The key architectural insight is that COA-2 (Self-Location) serves as the foundational signal layer that feeds all other protocols. Zero conflicts with existing DIA layers 1-4. All protocols extend current infrastructure rather than replacing it.

**New format strings:** 3 additions to CLAUDE.md §4 — [SELF-LOCATE], [REVERIFY], [REVERIFY-RESPONSE]
**Files affected:** CLAUDE.md (§3, §4, §6, §7, §9, [PERMANENT]), task-api-guideline.md (§11), all 6 agent .md, all 4 SKILL.md
**E2E scenarios:** 6 traced — happy path, multi-implementer, compact recovery, DIA rejection, scope change, skill chaining

## Layered Architecture

```
Layer 0: COA-2 (Self-Location Signal) — heartbeat pulse
   ├── feeds → Layer 1: COA-1 (Sub-Workflow Dashboard)
   ├── triggers → Layer 2: COA-3 (Documentation Checkpoint)
   └── triggers → Layer 3: COA-4 (Re-Verification Framework)
                       └── contains → COA-5 (MCP Check Type)
```

## COA-2: Self-Location Protocol (Foundational)
- **Format:** `[SELF-LOCATE] Phase {N} | Task {T}/{total} | Step: {desc} | Progress: {%} | MCP: {count} | Docs: {status}`
- **5 triggers:** Task boundary (MUST), milestone (MUST), >15min (SHOULD), on-demand (MUST), post-update (SHOULD)
- **Cost:** ~50-80 tokens per self-locate, ~500-800 total per teammate per session
- **Integration:** CLAUDE.md §3 (new obligation), §4 (new format), all 6 agent .md (execution phase)

## COA-1: Sub-Workflow Tracking (Lead-Side)
- **Format:** Sub-Workflow Status table in orchestration-plan.md (8 columns)
- **6 statuses:** ON_TRACK, ATTENTION, BLOCKED, REVERIFY, COMPLETING, COMPACT_RISK
- **Anomaly detection:** ATTENTION status triggers COA-4 re-verification
- **ASCII viz:** Provides structured data for User Visibility requirement
- **Integration:** CLAUDE.md §6 (new subsection + Gate Checklist item 6 + DIA Engine enhancement)

## COA-3: Continuous Documentation (Evidence Layer)
- **6 triggers:** Task boundary, milestone, ~75% pressure, >15min, IDLE, task completion
- **Enforcement:** Docs status in [SELF-LOCATE] → visible in sub-workflow table → ATTENTION on stale/missing
- **Key change:** Replaces vague "proactively throughout execution" with specific checkpoint triggers
- **Integration:** CLAUDE.md §3, §9 (enhanced Pre-Compact), all 6 agent .md (replace vague section)

## COA-4: Verification Continuity (Framework)
- **3 levels:** RV-1 (status ping, ~100 tok), RV-2 (comprehension check, ~300 tok), RV-3 (abbreviated IA, ~800 tok)
- **7 triggers:** silence, stale docs, scope change, milestone, low MCP, L1/L2 deviation, post-recovery
- **Escalation:** RV-1 → RV-2 → RV-3 → ABORT (3x failure). Frequency limits prevent over-verification.
- **Key design:** Extends DIA from entry-gate to mid-execution WITHOUT changing existing DIA
- **Integration:** CLAUDE.md §4, §6, [PERMANENT]; task-api-guideline.md §11; all 6 agent .md

## COA-5: MCP Usage Verification (Specialized Check)
- **Data source:** MCP field in [SELF-LOCATE] (already designed in COA-2)
- **Trigger:** MCP count = 0 at >50% progress in Required phase → COA-4 RV-2
- **4 statuses:** ACTIVE, LOW, MISSING, EXEMPT
- **Minimal standalone changes:** Mostly implemented through COA-2 + COA-4 infrastructure
- **Integration:** CLAUDE.md §7 (verification triggers subsection)

## Cross-Impact Matrix

| COA | CLAUDE.md §3 | §4 | §6 | §7 | §9 | [PERM] | task-api §11 | agent .md | SKILL.md |
|-----|-------------|----|----|----|----|--------|-------------|-----------|----------|
| COA-2 | obligation | format | — | — | — | — | — | execution | — |
| COA-1 | — | types | sub-workflow, gate, DIA | — | — | — | — | — | orch-plan |
| COA-3 | obligation | — | — | — | pre-compact | — | ISS-005 | pre-compact | — |
| COA-4 | — | format | DIA engine | — | — | extend desc | new section | new subsection | — |
| COA-5 | — | — | — | triggers | — | — | — | MCP note | — |

## Conflict Analysis Summary
- **Zero conflicts** with existing DIA layers 1-4 (CIP, DIAVP, LDAP, Hooks)
- All protocols EXTEND or ENHANCE existing infrastructure
- COA-3 REPLACES vague language with concrete triggers (same intent, better enforcement)
- COA-4 ADDS mid-execution verification (entry-gate DIA unchanged)
- New format strings are additive to §4 (existing 12 formats unchanged)

## Recommendations for Architect
1. Design COA-2 as the unified checkpoint mechanism first — everything depends on it
2. Keep COA-5 as a COA-4 specialization, not a separate protocol
3. Consider whether the sub-workflow table (COA-1) should be auto-updated by hooks (future enhancement)
4. The 3-level re-verification (COA-4) should be presented as a DIA extension, not a new layer
5. All L3-full/ specs include exact current text + proposed replacement text for every integration point

## MCP Tools Usage Report
| Tool | Calls | Purpose |
|------|-------|---------|
| sequential-thinking | 6 | Gap analysis, protocol design (COA-2→5), scenario planning, topology analysis |
| tavily | 1 | Multi-agent heartbeat/checkpoint protocol best practices verification |
| context7 | 0 | Not applicable — infrastructure is custom Agent Teams, no library docs needed |

## Sources
- CLAUDE.md v5.0 (381 lines) — primary authority
- task-api-guideline.md v5.0 (537 lines) — DIA enforcement protocol
- 6 agent .md files — role-specific protocol sections
- 4 SKILL.md files — orchestration templates
- Tavily: multi-agent orchestration heartbeat patterns (OpenClaw, industry surveys)
