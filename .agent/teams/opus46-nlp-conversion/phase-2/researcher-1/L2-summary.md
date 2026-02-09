# L2 Summary — Opus 4.6 NLP Conversion Audit

**Researcher:** researcher-1 | **Phase:** 2 (Deep Research) | **GC:** v1
**Date:** 2026-02-08

---

## Executive Summary

The current .claude/ infrastructure contains **847 lines** of instruction across 8 files.
Protocol markers (`[DIRECTIVE]`, `[STATUS]`, etc.) appear **37 times** across all files.
ALL CAPS enforcement language appears ~66 times in CLAUDE.md alone.
The DIA enforcement system ([PERMANENT] section) accounts for **40 lines** (19%) of CLAUDE.md
and is the single densest concentration of protocol markers (19 occurrences).

**Key finding:** Most protocol markers serve as _communication labels_, not enforcement mechanisms.
Opus 4.6 can infer message types from context without explicit bracket markers.
The real enforcement comes from `disallowedTools` in YAML frontmatter and hook scripts —
not from repeating "[IMPACT_VERIFIED]" in prose.

**Projected reduction:** 847 → ~560 lines (34% reduction) while preserving all semantic content.

---

## Domain 1: CLAUDE.md Content Audit (207 lines → ~135 lines)

### Section-by-Section Analysis

#### §0 Language Policy (lines 5-9) — 5 lines → 4 lines | KEEP
- Clean, essential. Minor: remove "Everything else:" bullet consolidation.
- No protocol markers. No ALL CAPS. Already good natural language.

#### §1 Team Identity (lines 11-17) — 7 lines → 5 lines | REWRITE-MINOR
- Essential config. Can consolidate env var reference into one line.
- "Delegate Mode — never modifies code directly" is good natural framing.

#### §2 Phase Pipeline (lines 18-34) — 17 lines → 14 lines | REWRITE-MINOR
- Table is efficient and essential. KEEP table.
- Lines 32-34 (Shift-Left, Gate Rule, DIA Enforcement) use enforcement language.
  - "Gate Rule: Lead approves every phase transition" → "Lead approves each phase transition"
  - "DIA Enforcement: Every task assignment requires..." → Remove entirely; this is restated in §6.
- Remove "Max 3 iterations per phase" — this is a rigid rule that Opus 4.6 can handle through judgment.

#### §3 Role Protocol (lines 36-49) — 14 lines → 10 lines | REWRITE
- Contains 3 protocol markers: [IMPACT-ANALYSIS], [PLAN], [PERMANENT]
- "Submit [IMPACT-ANALYSIS] before any work" → "Explain your understanding of the task before starting work"
- "Submit [PLAN] before any mutation" → "Share your implementation approach before making changes"
- "Detailed enforcement/compliance duties in [PERMANENT] section" → just reference the section naturally
- "Sub-Orchestrator capable via Task tool" — keep, useful.

#### §4 Communication Protocol (lines 51-69) — 19 lines → 12 lines | REWRITE
- The communication table has 13 rows with formal labels.
- Many rows describe the same concept: "Lead talks to teammate" in various contexts.
- **Proposed consolidation:** Group by flow direction (3 groups instead of 13 rows):
  1. Lead → Teammate: task context, updates, corrections, challenges, approvals
  2. Teammate → Lead: understanding check, status updates, plan proposals, challenge responses
  3. Lead → All: phase transition announcements
- Remove "Re-education" row — the concept of "re-education" is pedagogical framing that Opus 4.6 doesn't need. Just: "Lead clarifies if teammate misunderstands."
- Remove "Format definitions: see task-api-guideline.md §11" — cross-reference handled in §6.

#### §5 File Ownership Rules (lines 71-76) — 6 lines → 4 lines | KEEP
- Clean, essential rules. Minor compression possible.
- "Two teammates must never edit the same file concurrently" → "No concurrent edits to the same file"

#### §6 Orchestrator Decision Framework (lines 78-127) — 50 lines → 35 lines | REWRITE
- **Pre-Spawn Checklist (80-86):** 7 lines → 5 lines. Good content, slightly verbose gates.
  - "Gate S-1/S-2/S-3" labels → Natural: "Before spawning: clarify ambiguity, split large scopes, vary approach after failure"
- **Spawn Matrix (88-90):** 3 lines → 2 lines. Already concise.
- **Gate Checklist (92-94):** 3 lines → 2 lines. Compress 5 items into natural sentence.
- **ASCII Status Visualization (96-98):** 3 lines → KEEP as-is. Essential for user visibility.
- **DIA Engine (100-109):** 10 lines → 6 lines. HEAVY REWRITE needed.
  - This is the core enforcement engine. Contains 7 protocol markers.
  - "Context Injection: Embed GC-v{N} + task-context.md in every [DIRECTIVE]"
    → "Include global context and task context when assigning work"
  - "Impact Verification: Review every [IMPACT-ANALYSIS] against RC checklist"
    → "Verify each teammate understands their task before approving"
  - "[VERIFICATION-QA] for gaps" → "Ask clarifying questions if gaps exist"
  - "Re-education: On [REJECTED], re-inject with corrections"
    → "If a teammate misunderstands, clarify and have them try again"
  - "Deviation levels: COSMETIC / INTERFACE_CHANGE / ARCHITECTURE_CHANGE"
    → Keep the concept but express naturally: "Deviations range from cosmetic (log only) to architectural (re-plan required)"
- **GC Version Tracking (111-112):** 2 lines → KEEP. Essential config detail.
- **L1/L2/L3 Handoff (114-115):** 2 lines → KEEP. Essential format definition.
- **Team Memory (117-120):** 4 lines → 3 lines. Minor compression.
- **Output Directory (122-127):** 6 lines → KEEP. Essential structure.

#### §7 MCP Tools (lines 129-144) — 16 lines → 10 lines | REWRITE
- Phase-by-phase table is useful but verbose.
- "All agents must use `mcp__sequential-thinking__sequentialthinking` for every analysis..."
  → "Use sequential-thinking for non-trivial analysis and decisions."
- The requirement matrix (Required/As needed/Recommended) can be simplified:
  → "Research phases (2-4): use tavily and context7 for external docs. All phases: use sequential-thinking."
- Remove the full 9-row table. Replace with 3 bullets.

#### §8 Safety Rules (lines 146-150) — 5 lines → 5 lines | KEEP
- Already concise. Essential safety content.

#### §9 Compact Recovery (lines 152-166) — 15 lines → 10 lines | REWRITE
- Contains 5 protocol markers: [DIRECTIVE], [INJECTION], [STATUS], [CONTEXT_LOST], CONTEXT_PRESSURE
- Lead Recovery: "Re-inject [DIRECTIVE]+[INJECTION] with latest GC-v{N}"
  → "Send latest context to each active teammate"
- Teammate Recovery: "report [CONTEXT_LOST] → await [INJECTION] → re-submit [IMPACT-ANALYSIS]"
  → "Report context loss, wait for fresh context from Lead, then reconfirm understanding"
- "Never proceed with summarized or remembered information alone" — KEEP. Critical behavioral rule.

#### [PERMANENT] Section (lines 168-207) — 40 lines → 25 lines | HEAVY REWRITE
This is the densest section. 19 protocol markers. 9 numbered Lead duties. 7 numbered Teammate duties.

**Lead Duties (170-189) — 20 lines → 12 lines:**
1. Task API Sovereignty → "Only Lead creates/updates tasks (enforced by tool restrictions)"
2. Context Injection (CIP) → Merge with §6 DIA Engine. Don't repeat.
3. Impact Verification (DIAVP) → "Verify teammate understanding. Use open-ended questions per role tier."
   - TIER 1/2/3 with RC item counts → Replace with natural descriptions (see Domain 3)
4. Enforcement Gate → "Understanding must be verified before approving implementation plans"
5. Propagation → Already in §6 DIA Engine. Remove duplicate.
6. Failure Escalation → "After 3 failed understanding checks, re-spawn the teammate"
7. Adversarial Challenge (LDAP) → Simplify to: "Challenge teammates with probing questions to verify systemic understanding. Intensity scales with phase criticality."
   - Remove the 7 category names (INTERCONNECTION_MAP, etc.) from CLAUDE.md. Move to task-api-guideline.md or remove entirely.
   - Remove "MAXIMUM (P3/P4: 3Q+alt), HIGH..." matrix from CLAUDE.md.
8. Team Memory → Already in §6. Remove duplicate.
9. Hook Enforcement → "Hooks verify L1/L2 file existence automatically"

**Teammate Duties (191-200) — 10 lines → 7 lines:**
1. Context Receipt → "Confirm you received and understood the context"
2. Impact Analysis → "Explain your understanding before starting work"
2a. Challenge Response → "Answer probing questions with specific evidence"
3. Task API → "Task API is read-only for you (creation/updates are Lead-only)"
4. Context Updates → "Acknowledge context updates and report any impact on your work"
4a. Team Memory → "Read team memory at start. Update your section with discoveries."
5. Pre-Compact → "Save your work (L1/L2/L3) proactively. Report if running low on context."
6. Recovery → Merge with §9. Remove duplicate.
7. Persistence → "Your work persists through files and messages, not memory"

**Cross-References (202-207) — 6 lines → 3 lines:**
- Consolidate into a single "See also" block.

### CLAUDE.md Protocol Marker Inventory

| Marker | Count | Natural Alternative |
|--------|-------|-------------------|
| [DIRECTIVE] | 3 | "task assignment" or "context injection" |
| [INJECTION] | 3 | "context" or "background" |
| [STATUS] | 2 | "status update" |
| [IMPACT-ANALYSIS] | 3 | "understanding check" or "task comprehension" |
| [IMPACT_VERIFIED] | 2 | "understanding confirmed" |
| [IMPACT_REJECTED] | 2 | "understanding insufficient" |
| [PLAN] | 2 | "implementation approach" |
| [APPROVED] | 0 | (implied in approval flow) |
| [CHALLENGE] | 2 | "probing question" |
| [CHALLENGE-RESPONSE] | 1 | "defense" or "evidence-based response" |
| [CONTEXT-UPDATE] | 1 | "context update" |
| [CONTEXT_LOST] | 1 | "context loss report" |
| [PERMANENT] | 2 | Section heading without brackets |
| CONTEXT_PRESSURE | 1 | "running low on context" |
| [REJECTED] | 1 | "insufficient understanding" |
| [VERIFICATION-QA] | 1 | "clarifying questions" |
| **Total** | **27** | — |

### CLAUDE.md Duplication Analysis

Several concepts are stated in multiple sections:

| Concept | Stated In | Recommendation |
|---------|-----------|---------------|
| Impact verification before work | §3, §6 DIA, [PERMANENT] Lead #3, [PERMANENT] Teammate #2 | State once in §3, reference in §6 |
| Context injection | §4, §6 DIA, [PERMANENT] Lead #2 | State once in §6 |
| Task API read-only | §3, [PERMANENT] Lead #1, [PERMANENT] Teammate #3 | State once in §3, note enforcement mechanism |
| Compact recovery | §9, [PERMANENT] Teammate #5-6 | State once in §9 |
| Team Memory | §6, [PERMANENT] Lead #8, [PERMANENT] Teammate #4a | State once in §6 |
| Challenge protocol | §4, [PERMANENT] Lead #7, [PERMANENT] Teammate #2a | State once in §6 |

**Estimated duplicate lines:** ~25 lines across CLAUDE.md (12% of file).

---

## Domain 2: Agent .md Natural Language Analysis

### Common Patterns Across All 6 Agents

**Structure (all files):**
1. YAML frontmatter (tools, permissions) — KEEP exactly as-is
2. One-line role description — KEEP
3. Protocol section with Impact Analysis template — REWRITE
4. Challenge Response section — REWRITE
5. Execution section with numbered steps — REWRITE
6. Output Format section — KEEP (essential)
7. Constraints section — KEEP (essential)

**Common anti-patterns:**
- Impact Analysis templates are copy-pasted with filled section headers
- "Use `mcp__sequential-thinking__sequentialthinking` for every..." appears in every file
- Phase numbering (Phase 1/1.5/2/3) creates false sense of rigid sequence

### Per-File Analysis

#### researcher.md (79 lines → ~50 lines)

**Current structure:**
- Frontmatter: 27 lines (KEEP)
- Role: 3 lines (KEEP)
- Impact Analysis template: 18 lines → 8 lines
- Challenge Response: 4 lines → 2 lines
- Execution steps: 7 lines → 4 lines
- Output Format: 4 lines (KEEP)
- Constraints: 1 line (KEEP)

**Before (Impact Analysis):**
```
### Phase 1: Impact Analysis (TIER 3, max 2 attempts)
Submit [IMPACT-ANALYSIS] to Lead via SendMessage:
\```
[IMPACT-ANALYSIS] Phase {N} | Attempt {X}/2

## 1. Task Understanding
- My assignment: {restate in own words}
- Why this matters: {connection to project goals}

## 2. Research Scope Boundaries
- In scope: {specific topics/areas}
- Out of scope: {what I will NOT research}
- Data sources: {specific tools/docs/APIs}

## 3. Downstream Usage
- Who consumes my output: {role + what they need}
- Output format contract: {L1/L2/L3 structure}
- If my findings change scope: {escalation path}
\```
```

**After:**
```
### Before Starting Work
Message Lead with your understanding of the task. Cover:
- What you're researching and why it matters
- What's in scope vs. out of scope
- Who will use your output and what format they need
```

**Reduction:** 18 lines → 4 lines. Same semantic content. Opus 4.6 will naturally produce
structured output when given clear expectations without rigid templates.

**Challenge Response — Before:**
```
### Phase 1.5: Challenge Response (MEDIUM: 1Q minimum)
On [CHALLENGE]: respond with [CHALLENGE-RESPONSE] providing specific evidence —
downstream consumer identification, concrete scope boundaries, assumption justification.
Expected categories: INTERCONNECTION_MAP, SCOPE_BOUNDARY, ASSUMPTION_PROBE.
```

**After:**
```
### If Lead Asks Probing Questions
Respond with specific evidence — name your downstream consumers, justify your scope boundaries,
and defend your assumptions with concrete references.
```

**Reduction:** 4 lines → 3 lines, but much more readable.

**Execution — Before:**
```
1. Decompose research into parallel sub-tasks when possible.
2. Use `mcp__sequential-thinking__sequentialthinking` for every analysis step and judgment.
3. Use `mcp__tavily__search` for latest documentation and best practices.
4. Use `mcp__context7__resolve-library-id` + `mcp__context7__query-docs` for library docs.
5. Cross-reference findings across multiple MCP tools before concluding.
6. Report key findings to Lead via SendMessage for TEAM-MEMORY.md relay.
7. Write L1/L2/L3 output files to assigned directory.
```

**After:**
```
### Research Execution
- Break research into parallel sub-tasks when possible
- Use sequential-thinking for analysis, tavily for current docs, context7 for library references
- Cross-reference findings before concluding; report key findings to Lead
- Write L1/L2/L3 files to your assigned directory
```

**Reduction:** 7 lines → 4 lines. MCP tool names are already in the YAML frontmatter tools list.

#### architect.md (89 lines → ~55 lines)

**Key changes:**
- Impact Analysis template (19 lines → 6 lines): Same pattern as researcher, but includes
  "Interface Contracts & Boundaries" and "Cross-Teammate Impact" — express as natural expectations
- Challenge Response (5 lines → 3 lines): "Architecture receives maximum scrutiny" is good tone.
  Remove "3Q + alternative required" — Opus 4.6 understands "thorough defense" without counting questions.
- "Produce Architecture Decision Records (ADR)" — KEEP. Good concrete deliverable.
- Phase 3 vs Phase 4 deliverables — KEEP. Essential differentiation.

**Before:**
```
### Phase 1.5: Challenge Response (MAXIMUM: 3Q + alternative required)
Architecture phases receive maximum scrutiny — design flaws caught here prevent exponential downstream cost.
On [CHALLENGE]: respond with [CHALLENGE-RESPONSE] providing specific component names,
interface contract references, concrete propagation chains, and quantified blast radius.
If ALTERNATIVE_DEMAND: propose at least one concrete alternative with its own interconnection map.
Expected categories: All 7.
```

**After:**
```
### If Lead Challenges Your Design
Architecture receives the deepest scrutiny — design flaws here multiply downstream.
Defend with specific component names, interface contracts, propagation chains, and blast radius.
If asked for alternatives, propose at least one concrete alternative with its own impact analysis.
```

#### devils-advocate.md (73 lines → ~50 lines)

**Key changes:**
- No Impact Analysis (TIER 0 exempt) — already clean. KEEP.
- Challenge Categories + Severity Ratings + Final Verdict — KEEP. These are the agent's core deliverables.
- "Use `mcp__sequential-thinking__sequentialthinking` for every challenge analysis" → "Use sequential-thinking for each challenge assessment"
- Remove "MCP-backed evidence preferred" — unnecessary qualification.

**Minimal changes needed.** This file is the closest to natural language already.

#### implementer.md (114 lines → ~70 lines)

**Key changes:**
- Impact Analysis template (28 lines → 10 lines): Largest template. 6 sections including
  Files & Functions Impact Map, Interface Contracts, Risk Assessment.
  → Compress to: "Before starting, tell Lead: what files you'll change, what interfaces are affected,
  which teammates' work overlaps with yours, and what risks you see."
- Two-Gate System (4 lines → 2 lines): "Gate A → Gate B" → "First confirm understanding, then share your plan"
- Plan Submission template (7 lines → 3 lines)
- Sub-Orchestrator Mode (2 lines → KEEP)
- Constraints — mostly KEEP. "File ownership is strict" is good natural language.

**Before (Plan Submission):**
```
### Phase 2: Plan Submission (Gate B)
\```
[PLAN] Phase 6
Files: [list of files to create/modify]
Changes: [description of each change]
Risk: [low|medium|high]
Interface Impact: [which interfaces are affected]
\```
```

**After:**
```
### Before Making Changes
Share your plan with Lead: which files you'll modify, what changes you'll make,
risk level, and any interface impacts. Wait for approval before proceeding.
```

#### tester.md (90 lines → ~60 lines)

**Key changes:**
- Impact Analysis template (20 lines → 6 lines): Similar pattern to researcher.
- "Test Design Principles" section — KEEP. Good, clean, natural language already.
- "[STATUS] Phase 7 | ITERATE_NEEDED | {failure details}" → "Message Lead with failure details if fixes are needed"

#### integrator.md (116 lines → ~70 lines)

**Key changes:**
- Impact Analysis template (28 lines → 10 lines): Same as implementer pattern.
- Plan Submission template (8 lines → 3 lines): Same as implementer.
- Conflict Resolution Principles — KEEP. Good natural language already.
- "[STATUS] Phase 8 | BLOCKED | Irreconcilable conflict: {details}" → "Message Lead if a conflict can't be resolved"

### agent-common-protocol.md (79 lines → ~45 lines)

**Current structure:**
- Phase 0: Context Receipt (4 lines) — REWRITE
- Mid-Execution Updates (4 lines) — REWRITE
- Completion (3 lines) — KEEP
- Task API Access (2 lines) — KEEP
- Team Memory (5 lines) — KEEP
- Context Pressure & Auto-Compact (14 lines) — REWRITE
- Memory (2 lines) — KEEP

**Before (Context Receipt):**
```
## Phase 0: Context Receipt

1. Receive [DIRECTIVE] + [INJECTION] from Lead.
2. Parse embedded global-context.md (note GC-v{N}).
3. Parse embedded task-context.md.
4. Send to Lead: `[STATUS] Phase {N} | CONTEXT_RECEIVED | GC-v{ver}, TC-v{ver}`
```

**After:**
```
## When You Receive a Task Assignment

Read the global context and task context provided by Lead.
Confirm receipt by messaging Lead with the context version you received.
```

**Before (Context Pressure):**
```
### Context Pressure (~75% capacity)
1. Immediately write L1/L2/L3 files with all work completed so far.
2. Send `[STATUS] CONTEXT_PRESSURE | L1/L2/L3 written` to Lead.
3. Await Lead termination and replacement with L1/L2 injection.

### Auto-Compact Detection
If you see "This session is being continued from a previous conversation":
1. Send `[STATUS] CONTEXT_LOST` to Lead immediately.
2. Do not proceed with any work using only summarized context.
3. Await [INJECTION] from Lead with full GC + task-context.
4. Read your own L1/L2/L3 files to restore progress.
5. Re-submit [IMPACT-ANALYSIS] to Lead (TIER 0 exempt — await Lead instructions instead).
6. Wait for [IMPACT_VERIFIED] before resuming work.
```

**After:**
```
### Running Low on Context
Save all work to L1/L2/L3 files immediately, then tell Lead you're running low.
Lead will shut you down and re-spawn you with your saved progress.

### If You Lose Context (Session Continued)
Tell Lead immediately. Do not continue working from memory alone.
Wait for Lead to send fresh context, read your L1/L2/L3 files, then reconfirm
your understanding of the task before resuming.
```

### Agent .md Line Count Summary

| File | Current | Projected | Reduction |
|------|---------|-----------|-----------|
| researcher.md | 79 | 50 | -37% |
| architect.md | 89 | 55 | -38% |
| devils-advocate.md | 73 | 50 | -32% |
| implementer.md | 114 | 70 | -39% |
| tester.md | 90 | 60 | -33% |
| integrator.md | 116 | 70 | -40% |
| agent-common-protocol.md | 79 | 45 | -43% |
| **Total** | **640** | **400** | **-37.5%** |

---

## Domain 3: DIA Recalibration Specification

### Current DIA System Map

**DIAVP Tiers:**

| Tier | Role | Sections | RC Items | Max Attempts |
|------|------|----------|----------|-------------|
| 0 | devils-advocate | Exempt | 0 | 0 |
| 1 | implementer, integrator | 6 | 10 | 3 |
| 2 | architect, tester | 4 | 7 | 3 |
| 3 | researcher | 3 | 5 | 2 |

**LDAP Intensity Matrix:**

| Intensity | Phases | Questions |
|-----------|--------|-----------|
| MAXIMUM | P3, P4 | 3Q + alternative |
| HIGH | P6, P8 | 2Q |
| MEDIUM | P2, P7 | 1Q |
| EXEMPT | P5 | 0 |
| NONE | P1, P9 | 0 |

**RC Checklist Items (from CLAUDE.md references, RC-01~RC-10):**
Referenced but not defined in CLAUDE.md itself — defined in task-api-guideline.md §11 (out of scope).

### Problem Analysis

The current DIA system over-specifies verification mechanics:
1. **Template rigidity**: 6-section templates with exact headers force compliance-theater rather than genuine understanding
2. **Counting questions**: "3Q + alternative" doesn't guarantee depth; one insightful question beats three surface-level ones
3. **Tier complexity**: 4 tiers × variable sections × variable RC items = high cognitive overhead for Lead to manage
4. **RC items not in CLAUDE.md**: The actual checklist lives in task-api-guideline.md, so CLAUDE.md references something teammates can't see
5. **LDAP categories**: 7 named categories (INTERCONNECTION_MAP, etc.) are hard to remember and add no value — Lead generates challenges based on context, not by checking category boxes

### Proposed DIA Recalibration

#### Simplified Verification Model

Replace tiers/RC items/categories with **role-appropriate open-ended questions**:

**For Researchers (currently TIER 3):**
Lead asks 1 question after receiving understanding check:
> "What would change in your research approach if [X constraint] were removed?"

This single question tests: scope awareness, constraint understanding, and adaptability.
No template needed — researcher explains their understanding naturally.

**For Architects (currently TIER 2):**
Lead asks 2 questions:
> 1. "Walk me through how a change in [component X] would propagate to [component Y]."
> 2. "What's the most likely failure mode of this design, and how does your architecture handle it?"

These replace 7 RC items. They test interconnection awareness and failure reasoning.

**For Implementers/Integrators (currently TIER 1):**
Lead asks 2-3 questions:
> 1. "Which other teammates' work could break if your changes don't match the interface spec?"
> 2. "What's your rollback plan if [specific risk] materializes?"
> 3. (If cross-boundary) "How will you verify that the integrated output matches the design?"

These replace 10 RC items. They test interface awareness, risk thinking, and verification planning.

**For Devils-Advocate:** Remains exempt (unchanged).

**For Testers (currently TIER 2):**
Lead asks 1-2 questions:
> 1. "What's the one test case that, if it fails, means the entire feature is broken?"
> 2. "What would you NOT test, and why?"

These test prioritization and scope judgment.

#### Simplified LDAP

Replace the 5-level intensity matrix with a 2-level model:

| Level | When | What |
|-------|------|------|
| Standard | All phases except P1/P5/P9 | 1-2 probing questions based on task context |
| Deep | P3/P4 (architecture/design) | 2-3 probing questions + request for alternative approach |

Remove named categories entirely. Lead generates questions organically based on the specific
task context, not by checking off a list of 7 categories.

#### CLAUDE.md Impact

Current [PERMANENT] Lead duties #3 and #7 (DIAVP + LDAP) = 12 lines.
After recalibration: ~5 lines describing the simplified verification approach.

**Before ([PERMANENT] Lead #3):**
```
3. **Impact Verification (DIAVP):** Review every [IMPACT-ANALYSIS] against RC checklist.
   TIER 1 (implementer/integrator): 6 sections, 10 RC items, max 3 attempts.
   TIER 2 (architect/tester): 4 sections, 7 RC items, max 3 attempts.
   TIER 3 (researcher): 3 sections, 5 RC items, max 2 attempts.
   TIER 0 (devils-advocate): Exempt.
```

**After:**
```
3. **Understanding Verification:** After a teammate explains their understanding,
   ask 1-3 open-ended questions appropriate to their role. Focus on interconnection
   awareness, failure reasoning, and interface impact. Max 3 attempts; if a teammate
   can't demonstrate understanding after 3 tries, re-spawn with clearer context.
```

**Before ([PERMANENT] Lead #7):**
```
7. **Adversarial Challenge (LDAP):** After RC checklist, generate [CHALLENGE] targeting GAP-003.
   Categories (7): INTERCONNECTION_MAP, SCOPE_BOUNDARY, RIPPLE_TRACE, FAILURE_MODE,
   DEPENDENCY_RISK, ASSUMPTION_PROBE, ALTERNATIVE_DEMAND.
   Intensity: MAXIMUM (P3/P4: 3Q+alt), HIGH (P6/P8: 2Q), MEDIUM (P2/P7: 1Q), EXEMPT (P5), NONE (P1/P9).
   Gate A withheld until challenge defense passes. Failed defense = [IMPACT_REJECTED].
```

**After:**
```
7. **Probing Questions:** After verifying understanding, ask deeper questions to test
   systemic awareness. For architecture phases (3/4): ask for alternative approaches.
   Understanding must be verified before approving any implementation plan.
```

---

## Cross-Impact Matrix

| Finding | Files Affected | Priority |
|---------|---------------|----------|
| Protocol marker removal | CLAUDE.md, all 6 agents, common-protocol | HIGH |
| Impact Analysis template compression | All 6 agents | HIGH |
| CLAUDE.md duplication removal | CLAUDE.md [PERMANENT] vs §3/§6 | HIGH |
| DIA tier simplification | CLAUDE.md [PERMANENT], all 5 agent tiers | HIGH |
| LDAP intensity reduction | CLAUDE.md [PERMANENT] Lead #7 | MEDIUM |
| Communication table consolidation | CLAUDE.md §4 | MEDIUM |
| MCP table simplification | CLAUDE.md §7 | LOW |
| Phase numbering removal in agents | All 6 agents | LOW |

---

## Key Recommendations for Architect (Phase 3)

1. **Start with CLAUDE.md** — it's the root document. Changes here cascade to all agents.
2. **Deduplicate before rewriting** — remove the ~25 duplicate lines first, then convert remaining content.
3. **Preserve behavioral semantics** — every removal should be tested: "does the agent still know to do X?"
4. **Template elimination is the biggest win** — Impact Analysis templates are 18-28 lines each across 5 agents. Converting to natural expectations saves ~80 lines total.
5. **DIA recalibration is coupled with agent files** — the new verification questions should be defined once in CLAUDE.md and referenced from agents, not duplicated.
6. **Keep YAML frontmatter untouched** — tool lists, permissions, and model settings are mechanical and correct.
7. **Common protocol is the highest-leverage file** — changes here affect all 6 agents simultaneously.

---

## MCP Tools Usage Report

| Tool | Used? | Purpose |
|------|-------|---------|
| sequential-thinking | No — unavailable in session | Would have used for analysis classification decisions |
| tavily | No — unavailable in session | Not needed for this internal audit (no external docs) |
| context7 | No — unavailable in session | Not needed for this internal audit |
| WebSearch | Not needed | Internal codebase audit, no external research required |

**Fallback:** All analysis performed through systematic file reading and pattern matching.
This audit is internal-facing (analyzing our own infrastructure), so MCP tools for external
documentation were not required.

---

## Unresolved Items

| Item | Severity | Recommendation |
|------|----------|---------------|
| RC-01~RC-10 checklist content | LOW | These live in task-api-guideline.md (out of scope). The simplified verification model replaces them. |
| LDAP design doc synchronization | LOW | `docs/plans/2026-02-07-ch001-ldap-design.yaml` references the old intensity matrix. Should be updated when CLAUDE.md changes. |
| Hook scripts alignment | LOW | Hooks reference protocol markers in exit codes. Deferred to Ontology layer. |
| Agent memory templates | LOW | Deferred work item. Not affected by NLP conversion. |
