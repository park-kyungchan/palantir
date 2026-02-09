---
version: GC-v4
created: 2026-02-08
feature: opus46-nlp-conversion
complexity: MEDIUM
---

# Global Context — Opus 4.6 Native NLP Conversion

## Scope

**Goal:** Convert .claude/ infrastructure from protocol-marker enforcement to Opus 4.6 native
natural language instructions. Establish a clean LLM interaction layer that Palantir Ontology/Foundry
architecture will build upon.

**In Scope:**
- CLAUDE.md (207 → 132 lines): Natural language, §10 Integrity Principles replaces [PERMANENT]
- agent-common-protocol.md (79 → 48 lines): Natural instructions for shared procedures
- 6 agent .md files (561 → 345 lines): Role-based framing, open-ended verification
- DIA v6.0: RC items → open-ended questions; 5-level LDAP → 2-level (Standard/Deep)
- Communication format strings: [DIRECTIVE], [INJECTION] etc → natural conversation flow

**Out of Scope:**
- task-api-guideline.md (being optimized in separate terminal)
- Hook scripts (mechanical enforcement deferred to Ontology layer)
- Settings.json deny rules (already correct)
- Skills SKILL.md files (future RSI iterations)
- MCP server configuration

**Approach:** Full NLP Conversion — "enable success by clear criteria + trust + spot-check"

**Success Criteria:**
- Protocol markers replaced with natural alternatives
- Total: 847 → 525 lines (38% reduction)
- 28/28 CLAUDE.md behavioral requirements preserved
- 13/13 agent-common-protocol behaviors preserved
- DIA v6.0 operational with open-ended verification

## Key Research Findings (from claude-code-guide)

1. **Anthropic Official:** "Bloated CLAUDE.md causes Claude to ignore instructions."
   "Hardcoded complex, brittle logic" = anti-pattern.
2. **Opus 4.6 Sycophancy Reduction:** Heavy DIA over-compensates for drift no longer occurring.
3. **C Compiler Case Study:** Conversational guidance, not rigid gates.
4. **Measured Language > ALL CAPS:** Natural language compresses better.
5. **Role Prompting:** 3-5x better with well-defined roles vs. rule-based framing.
6. **Token Efficiency:** Directive overhead drops from ~2-3K to ~800-1200 tokens.

## Architectural Principle

- .claude/ INFRA = LLM interaction layer (natural language, model-native, trust-verify)
- Palantir Ontology/Foundry = Domain enforcement layer (structural, type-safe, mechanical)

## Phase 3 Architecture Design (architect-1)

**6 Architecture Decisions:**
- AD-1: Deduplicate — state once in authoritative location, reference elsewhere (~22 lines saved)
- AD-2: [PERMANENT] → §10 Integrity Principles (40→18 lines)
- AD-3: Communication table → 3 flow-direction groups
- AD-4: MCP matrix → 3 bullets
- AD-5: DIA v6.0 — checklists → role-appropriate open-ended questions
- AD-6: Agent template: Role → Before Starting → How to Work → Constraints

**DIA v6.0 Model:**
- Verification: Teammate explains → Lead asks 1-3 role-appropriate questions → Teammate defends with evidence
- Probing levels: Standard (P2/6/7/8: 1-2Q) | Deep (P3/4: 2-3Q + alternative) | None (P1/5/9)
- Pass: genuine understanding of interconnections, failure modes, interface impact
- Fail: surface rephrasing, can't name specifics, omits critical paths
- Max attempts: 3 critical / 2 researcher → re-spawn with clearer context

**Implementation Tasks (Phase 6):**
- T1: CLAUDE.md v6.0 (132 lines) — no dependencies
- T2: agent-common-protocol.md v2.0 (48 lines) — no dependencies
- T3: researcher.md + architect.md + devils-advocate.md (151 lines) — depends T1, T2
- T4: implementer.md + tester.md + integrator.md (194 lines) — depends T1, T2
- Parallelism: T1∥T2 → T3∥T4

**Full design:** `.agent/teams/opus46-nlp-conversion/phase-3/architect-1/L3-full/architecture-design.md`

## CRITICAL UPSTREAM CHANGE: PERMANENT Task Design (GC-v4)

**Source:** `docs/plans/2026-02-08-permanent-tasks-design.md` (APPROVED by user)
**Impact:** ARCHITECTURE_CHANGE — global-context.md is REPLACED by PERMANENT Task (Task API entity)

**Key Changes That Must Be Reflected in L3:**
1. **GC-v{N} → PT-v{N}:** All version references change
2. **CIP:** Lead embeds full GC → Lead includes PT Task ID, teammate self-serves via TaskGet
3. **LDAP:** Guesswork → grounded in Codebase Impact Map (authoritative reference)
4. **Recovery:** Lead re-injects → teammates can TaskGet for self-recovery
5. **Communication formats:** [DIRECTIVE] includes PT-ID instead of full GC
6. **Persistence:** GC dies with TeamDelete → PT archived to ARCHIVE.md
7. **Phase 0:** All pipeline skills gain PT initialization step
8. **Operational Constraints:** Max 2 concurrent teammates, split tasks maximally, no token conservation

**What preserves from original L3:**
- NLP conversion approach (natural language > protocol markers)
- AD-1~AD-6 architectural decisions
- DIA v6.0 open questions model (enhanced with Impact Map)
- Agent template standardization
- Deduplication strategy

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED)
- Phase 2: COMPLETE (Gate 2 APPROVED)
- Phase 3: APPROVED → REVISION IN PROGRESS (PERMANENT Task integration)

## Constraints
- task-api-guideline.md is being modified concurrently in another terminal — do not touch
- Hook scripts are deferred to Ontology layer — do not modify
- Must preserve all semantic content while changing expression style
- Settings.json deny rules are already correct — do not modify
- PERMANENT Task design (2026-02-08-permanent-tasks-design.md) must be ABSOLUTELY reflected
- Max 2 concurrent teammates (local PC memory constraint)
- Split tasks maximally (1 file = 1 task when feasible)

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | Full NLP conversion over phased approach | User confirmed; Ontology layer handles mechanical enforcement | P1 |
| D-2 | task-api-guideline.md excluded | Being worked on in separate terminal | P1 |
| D-3 | Hooks excluded from this iteration | Mechanical enforcement deferred to Ontology/Foundry layer | P1 |
| D-4 | Focus on instruction quality, not just line reduction | Opus 4.6 responds to natural heuristics | P1 |
| D-5 | Deduplicate before rewriting | ~25 lines repeated across §3/§6/[PERMANENT] | P2 |
| D-6 | Impact Analysis templates highest-leverage | 110 → ~30 lines across 5 agents | P2 |
| D-7 | DIA simplified to 2-level + open questions | Counting doesn't guarantee depth | P2 |
| D-8 | agent-common-protocol.md highest-leverage file | Changes cascade to all 6 agents | P2 |
| D-9 | State once, reference elsewhere (AD-1) | Eliminates 22 duplicate lines | P3 |
| D-10 | [PERMANENT] → §10 Integrity Principles (AD-2) | Principles not procedures; natural > numbered duties | P3 |
| D-11 | Open questions > checklists (AD-5) | Harder to fake; tests reasoning not compliance | P3 |
| D-12 | "Optional" markers rejected (ALT defense) | LLMs treat examples as instructions; half-measures add confusion | P3 |
| D-13 | GC replaced by PERMANENT Task | Task API entity enables: self-serve via TaskGet, Codebase Impact Map, cross-session persistence | P3-rev |
| D-14 | CIP changes from embedding to TaskGet | Reduces directive size (BUG-002 mitigation), teammates always get latest version | P3-rev |
| D-15 | LDAP grounded in Impact Map | Challenges and defenses reference authoritative relationship data, not guesswork | P3-rev |
