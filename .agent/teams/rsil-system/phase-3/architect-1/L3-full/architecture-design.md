# RSIL System — Phase 3 Architecture Design

**architect-1 | Phase 3 | rsil-system | 2026-02-09**

---

## 1. Architecture Overview

```
                         RSIL System Architecture
                         ========================

  ┌─────────────────────────────────────────────────────────┐
  │                   Shared Foundation                      │
  │  ┌──────────┐  ┌───────────┐  ┌────────────────────┐   │
  │  │ 8 Lenses │  │ AD-15     │  │ Layer 1/2 Boundary │   │
  │  │ (L1-L8)  │  │ Filter    │  │ Test               │   │
  │  └──────────┘  └───────────┘  └────────────────────┘   │
  │  (embedded identically in both skills)                  │
  └─────────────────────────────────────────────────────────┘
           │                              │
    ┌──────┴──────┐               ┌──────┴──────┐
    │ /rsil-global│               │/rsil-review │
    │ (NEW)       │               │ (REFINED)   │
    ├─────────────┤               ├─────────────┤
    │ Auto-invoke │               │ User-invoke │
    │ Observation │               │ Target-     │
    │   Window    │               │  specific   │
    │ Three-Tier  │               │ R-0→R-4     │
    │ G-0→G-4    │               │ Deep        │
    │ Lightweight │               │  analysis   │
    │ ~2000 tok   │               │ Full read   │
    └──────┬──────┘               └──────┬──────┘
           │                              │
           ▼                              ▼
    ┌──────────────────────────────────────────┐
    │          Unified Tracker                  │
    │  G-{N} findings  │  P-R{N} findings      │
    │  (source: global) │  (source: review)     │
    │  cross_refs ←────→ cross_refs             │
    └──────────────┬───────────────────────────┘
                   │
    ┌──────────────┴───────────────────────────┐
    │      Agent Memory (shared)                │
    │  ~/.claude/agent-memory/rsil/MEMORY.md    │
    │  §1 Config │ §2 Stats │ §3 Patterns │ §4 │
    └──────────────────────────────────────────┘
```

**System Identity:**
- Two independent skills sharing a stable foundation
- /rsil-global: breadth-first, lightweight, auto-invoked
- /rsil-review: depth-first, thorough, user-invoked
- Unified tracker preserves the cross-reference knowledge graph
- Shared agent memory enables cross-session learning

---

## 2. Architecture Decisions

Builds on Phase 1 decisions D-1 through D-5.

### AD-6: Findings-Only Output (No Auto-Apply)

**Decision:** /rsil-global NEVER auto-applies changes, even Category B findings. All findings are presented to the user for approval.

**Rationale:** GC-v2 constraint line 50: "Findings-only output (user approves before application)." D-3 "Immediate Cat B application" means Lead proposes for immediate action upon discovery, not auto-applies without consent. The auto-invoke mechanism means Lead initiates the review, not that it bypasses human judgment.

**Alternatives rejected:**
- Auto-apply Cat B: violates findings-only constraint, risks unintended changes
- Queue for next session: delays feedback loop unnecessarily (user IS present)

### AD-7: Adaptive Three-Tier Reading Per Work Type

**Decision:** Tier 0 classifies work type (A/B/C), then Tiers 1-3 adapt their data sources while preserving fixed context budgets (~100/~500/~1000 tokens).

**Rationale:** Type B/C work produces no gate records or L1 indexes. Git diff content serves as the equivalent high-signal source. The escalation logic (anomaly thresholds triggering next tier) remains consistent across all types.

**Alternatives rejected:**
- Uniform reading strategy: wastes tokens reading nonexistent artifacts for Type B/C
- Skip non-pipeline work: misses INFRA drift from direct edits (Type C is high-risk for silent inconsistency)

### AD-8: BREAK Escalation via AskUserQuestion

**Decision:** BREAK-severity findings trigger AskUserQuestion for immediate user attention. User can approve fix or defer (recorded with BREAK priority in tracker + agent memory).

**Rationale:** /rsil-global runs in the same session where the user just completed work — they are present. AskUserQuestion is the appropriate mechanism for urgent findings. If session terminates before presentation, findings persist in tracker and are re-detected next session.

**Alternatives rejected:**
- Auto-fix BREAKs: violates AD-6 (findings-only output)
- Silent logging: BREAK severity implies runtime failure risk — silent deferral is irresponsible

### AD-9: Tracker Section Isolation with ID Namespacing

**Decision:** Global findings use `G-{N}` prefix, narrow findings use `{Phase}-R{N}` prefix. Each skill writes to its own section within the unified tracker. Read-Merge-Write ensures sequential consistency.

**Rationale:** Zero ID collision. Section isolation prevents overwrite. Sequential execution (global before review in natural flow) ensures second writer sees first's additions. researcher-1 TA-2/TA-5 validated this schema.

**Alternatives rejected:**
- Separate tracker files: fragments the knowledge graph (researcher-1 TA-1: "Separate trackers fragment the knowledge graph")
- Single ID namespace: risks collision and complicates provenance tracking

### AD-10: Shared Foundation = Embedded Copy

**Decision:** Both skills contain identical copies of the 8 Lenses table, AD-15 Filter table, and Layer 1/2 Boundary Test. No external shared reference file.

**Rationale:** The shared foundation is stable (~85 lines total) and rarely changes. External reference files add a dependency that could break if moved/renamed. Each skill is self-contained and readable without external references. When the foundation evolves (e.g., new Lens L9), both skills are updated together in a single commit.

**Alternatives rejected:**
- Shared .md reference file: adds indirection, creates fragile dependency, saves ~85 lines but adds coordination cost
- Inline partial (only some elements shared): inconsistent approach, harder to maintain

### AD-11: Single Shared Agent Memory

**Decision:** Both skills share `~/.claude/agent-memory/rsil/MEMORY.md`. Statistics and patterns accumulate from both sources.

**Rationale:** Patterns are patterns regardless of discovery source. A finding from /rsil-global that becomes a pattern benefits /rsil-review's R-0 synthesis, and vice versa. Separation would fragment cumulative learning.

**Alternatives rejected:**
- Separate memory per skill: duplicates stats, fragments pattern library, complicates cross-skill learning

---

## 3. Component 1: /rsil-global Complete Flow Design

### 3.1 Frontmatter

```yaml
---
name: rsil-global
description: "INFRA Meta-Cognition health assessment — auto-invoked by Lead after pipeline delivery or .claude/ infrastructure changes. Three-Tier observation window, 8 universal lenses, AD-15 filter. Lightweight (~2000 token budget). Findings-only output."
argument-hint: "[optional: specific area of concern]"
---
```

### 3.2 When to Use (Auto-Invoke Decision Tree)

```
Work just completed in this session?
├── Pipeline delivery (Phase 9) finished? ── yes ──→ INVOKE /rsil-global
├── .claude/ files committed?
│   ├── yes
│   │   ├── ≥2 files changed? ── yes ──→ INVOKE /rsil-global
│   │   ├── 1 file changed
│   │   │   ├── Change touches cross-referenced file? ── yes ──→ INVOKE
│   │   │   └── Trivial edit (typo, formatting)? ── yes ──→ SKIP
│   │   └── no changes to .claude/ ──→ SKIP
│   └── no
├── Skill execution modified INFRA files? ── yes ──→ INVOKE
├── Read-only session (research, questions)? ──→ SKIP
└── Non-.claude/ changes only (application code)? ──→ SKIP
```

**Key principle:** Default to INVOKE for pipeline work and multi-file INFRA changes.
Default to SKIP for trivial edits, non-INFRA work, and read-only sessions.
When uncertain, invoke — the lightweight budget means low cost for a false positive.

### 3.3 Dynamic Context (Tier 0 Shell Injection)

```
!`ls -dt .agent/teams/*/ 2>/dev/null | head -3`

!`ls .agent/teams/*/phase-*/gate-record*.yaml 2>/dev/null | wc -l`

!`find .agent/teams/ -name "L1-index.yaml" 2>/dev/null | wc -l`

!`git diff --name-only HEAD~1 2>/dev/null | head -20`

!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -30`

!`wc -l docs/plans/2026-02-08-narrow-rsil-tracker.md 2>/dev/null`
```

**Feature Input:** $ARGUMENTS (optional — specific area of concern)

### 3.4 Phase G-0: Observation Window Classification

Lead-only. Use sequential-thinking.

**Announce at start:** "Running RSIL Global health assessment for the just-completed work."

```
Tier 0 Output (from Dynamic Context)
         │
    ┌────┴────────────────┐
    │ Classify Work Type  │
    └────┬────────────────┘
         │
    ┌────┴────┬────────┬──────────┐
    Type A    Type B   Type C    No work
    Pipeline  Skill    Direct    detected
    │         │        │         │
    ▼         ▼        ▼         ▼
  Standard  Git-diff  Git-diff  "No recent
  Tier 1    Tier 1    Tier 1    work detected.
  (gate+L1) (diff+    (diff+    Skipping."
            tracker)  MEMORY)   → EXIT
```

**Classification rules:**
- **Type A:** `.agent/teams/` has session directories with gate records → pipeline work
- **Type B:** No session dir, but git diff shows .claude/ skill or reference changes → skill execution
- **Type C:** No session dir, git diff shows .claude/ .md changes (not skills) → direct edit
- **No work:** No git diff, no new sessions → skip entirely

If $ARGUMENTS specifies a concern, note it for lens prioritization in G-1.

### 3.5 Phase G-1: Tiered Reading + Health Assessment

Lead-only. Use sequential-thinking for each tier transition.

#### Tier 1 Reading (per work type)

**Type A — Pipeline:**
1. Read the LATEST gate-record.yaml (most recent session, most recent phase)
2. Read the LATEST L1-index.yaml files (cap: 3 most recent per researcher-1 U-2)
3. Skim orchestration-plan.md (last 20 lines = current status)

**Type B — Skill-only:**
1. Read `git diff HEAD~1` for .claude/ file content changes
2. Read tracker diff (if narrow-rsil-tracker.md was modified)
3. Check if modified files reference other .claude/ files

**Type C — Direct edit:**
1. Read `git diff HEAD~1` content for specific changes
2. Read MEMORY.md diff (if changed)
3. List files that reference the modified files

#### Health Indicator Assessment

Apply the 5 INFRA health indicators to Tier 1 data:

| # | Indicator | Type A Signal | Type B/C Signal |
|---|-----------|---------------|-----------------|
| H-1 | Gate pass rate | PASS/FAIL counts in gate record | N/A (no gates) |
| H-2 | L1/L2 existence | Missing L1/L2 from any teammate | N/A |
| H-3 | Re-spawn count | Multiple `{role}-{N}` dirs same phase | N/A |
| H-4 | Warning density | TEAM-MEMORY.md warning count | N/A |
| H-5 | Cross-ref consistency | L1 references match across teammates | Diff references match target files |

**Note:** Type B/C only have H-5 (cross-reference consistency) as a directly measurable indicator. For Type B/C, Tier 1 primarily checks: "Do the changes maintain cross-file consistency?"

#### Lens Application (During Reading)

As Tier 1 data is read, apply relevant lenses to generate observations:

| Lens | Global Relevance | What to Look For |
|------|-----------------|-----------------|
| L1 Transition Integrity | HIGH | Gate criteria show implicit/skipped transitions? |
| L2 Evaluation Granularity | MEDIUM | Gate criteria bundled into single pass-through? |
| L3 Evidence Obligation | HIGH | L2 outputs missing evidence sources section? |
| L4 Escalation Paths | MEDIUM | BREAK findings without multi-step response? |
| L5 Scope Boundaries | HIGH | Cross-file references stale or inconsistent? |
| L6 Cleanup Ordering | LOW | Session cleanup incomplete? Orphan artifacts? |
| L7 Interruption Resilience | HIGH | Missing L1/L2 (work preservation failure)? |
| L8 Naming Clarity | LOW | ID conflicts across files? |

Generate observations (not full findings yet — those come in G-3).

#### Escalation Decision

```
Tier 1 Assessment
       │
  ┌────┴─────────────────────┐
  All indicators healthy     ≥1 anomaly detected
  No lens observations       │
  │                          ├── ≥1 FAIL in gate criteria
  ▼                          ├── ≥2 HIGH unresolved in L1
  "INFRA healthy.            ├── Re-spawn detected
  No findings."              ├── ≥2 cross-ref mismatches
  → G-4 (record "clean")    │
                             ▼
                        Tier 2 Reading
```

#### Tier 2 Reading (Selective, ~1000 tokens)

Only for flagged areas from Tier 1:
- Read L2-summary.md for flagged teammates/phases
- Read TEAM-MEMORY.md for warning/pattern context
- For Type B/C: Read the actual modified files + their reference targets
- Cross-check: Are issues systemic (cross-file) or localized?

**Tier 2 → Tier 3 Escalation:**
```
≥3 cross-file anomalies detected    → Tier 3
OR ≥2 BREAK-severity issues         → Tier 3
OR systemic pattern across sessions → Tier 3
Otherwise                           → G-2 (skip Tier 3, proceed to classification)
```

### 3.6 Phase G-2: Discovery (Tier 3 Only)

Spawn agents only when Tier 2 escalation triggers. Most runs skip this phase.

```
Tier 3 Triggered
       │
  ┌────┴────────────────────────────────┐
  │ Spawn Explore agent                  │
  │ Directive:                           │
  │ • Systemic investigation mandate     │
  │ • Specific anomalies from Tier 2     │
  │ • Cross-file consistency verification│
  │ • Return: structured findings        │
  └──────────────────────────────────────┘
```

**Agent directive construction:**
```
subagent_type: "Explore"
prompt:
  "Investigate the following INFRA anomalies detected by /rsil-global:
   {list anomalies from Tier 2 with file paths and observations}

   For each anomaly:
   1. Read ALL referenced files bidirectionally
   2. Verify cross-file consistency
   3. Classify by severity: BREAK (runtime failure) / FIX (quality) / WARN (cosmetic)
   4. Return structured findings with file:line evidence"
```

**When to also spawn claude-code-guide:**
Only if Tier 2 observations suggest a CC capability gap (e.g., "this pattern might be better handled by a CC feature we're not using"). This is rare in global reviews — most global findings are consistency issues, not capability gaps.

### 3.7 Phase G-3: Classification + Presentation

Lead-only. Use sequential-thinking.

#### Classify All Observations/Findings

```
For each observation from G-1 (Tier 1/2) or finding from G-2 (Tier 3):
    │
    ├── Apply AD-15 Filter:
    │   ├── Would require new hook? → Category A → REJECT
    │   ├── Achievable through .md NL change? → Category B → FIX
    │   └── Requires Layer 2 structured system? → Category C → DEFER
    │
    └── Apply Severity:
        ├── Runtime failure risk? → BREAK
        ├── Quality degradation? → FIX
        └── Cosmetic/minor? → WARN
```

#### Present to User

```markdown
## RSIL Global Assessment — {date}

**Work Type:** {A/B/C}
**Observation:** {what was reviewed}
**Tiers Used:** {0-1 / 0-2 / 0-3}
**Lenses Applied:** {N}/8

### Findings
| ID | Finding | Severity | Category | Lens |
|----|---------|----------|----------|------|

### BREAK Items (if any)
{detail per BREAK finding — file:line, evidence, proposed fix}

### FIX Items (Category B)
{detail per FIX — proposed NL text change}

### DEFER Items (Category C)
{detail — why L1 insufficient}

### Summary
BREAK: {N} | FIX: {N} | DEFER: {N} | WARN: {N} | PASS: {N}
INFRA Health: {assessment}
```

**For BREAK findings:** Use AskUserQuestion:
"RSIL Global found {N} BREAK-severity issues requiring attention. Review and fix now, or defer to next session?"

**For all other findings:** Present summary, user decides what to apply.

**If zero findings:** "INFRA healthy. No findings from this assessment." → proceed to G-4.

### 3.8 Phase G-4: Record

#### Tracker Update

Update `docs/plans/2026-02-08-narrow-rsil-tracker.md`:

1. **§2 Summary Table:** Add row with source_skill=rsil-global
2. **§3 Detailed Findings:** Add "Global Findings" subsection with all G-{N} findings using extended schema:
   ```yaml
   - id: G-{N}
     source_skill: rsil-global
     finding_type: global
     finding: "{description}"
     category: "B"
     severity: "FIX"
     detection_tier: 1
     cross_refs: []
     decomposed_to: []
     status: "ACCEPTED"
   ```
3. **§4 Cross-Cutting Patterns:** Add if new systemic pattern discovered
4. **§5 Backlog:** Add accepted-but-not-applied items

#### Agent Memory Update

Read-Merge-Write to `~/.claude/agent-memory/rsil/MEMORY.md`:
- §1 Configuration: increment review count, update date
- §2 Lens Performance: increment findings/accepted per lens used
- §3 Patterns: add new cross-cutting pattern (if discovered)
- §4 Evolution: add lens candidate (if identified)

#### Terminal Summary

```markdown
## RSIL Global Complete

**Work Type:** {A/B/C}
**Tiers Used:** {0-1 / 0-2 / 0-3}
**Findings:** BREAK {N} | FIX {N} | DEFER {N} | WARN {N}
**Applied:** {N} (user-approved)
**INFRA Health:** {healthy / needs-attention / critical}

Tracker updated: {N} new findings (G-{start}~G-{end})
Agent memory updated: review #{N}, cumulative {total} findings

No auto-chaining. Session continues normally.
```

### 3.9 Error Handling

| Situation | Response |
|-----------|----------|
| No git diff and no sessions | "No recent work detected. Skipping." |
| Tier 0 misclassification suspected | Fall back to Type A reading (most comprehensive) |
| Tier 1 reads exceed budget | Cap at 3 L1 files + 1 gate record. Note truncation. |
| Tier 3 agent returns empty | Proceed with Tier 1/2 findings only |
| Tracker file not found | Create initial section structure, then append |
| Agent memory not found | Create with seed data from tracker |
| User cancels mid-review | Preserve partial tracker updates |

### 3.10 Principles

- Lightweight by design — most runs complete at Tier 1 with zero findings
- Observation window stays under ~2000 tokens (Tier 0+1+2 combined)
- Findings-only output — user approves before any changes
- AD-15 inviolable — Category A REJECT, B ACCEPT, C DEFER
- Lenses generate observations, not prescriptions
- Tier 3 (Explore agent) is the exception, not the norm
- Record everything — even "clean" runs update agent memory statistics
- Self-healing through persistence — unfixed BREAKs are re-detected next session
- Terminal — no auto-chaining to /rsil-review or other skills
- INFRA scope only — never assess application code

---

## 4. Component 2: /rsil-review Refinement Delta

Six targeted changes to the existing 561-line SKILL.md. Each specified with exact location, old/new text, and rationale.

### Delta 1: Ultrathink Integration (IMP-1)

**Location:** Line 9-11 (skill intro paragraph)
**Action:** MODIFY

**Old text (line 9-11):**
```
Meta-Cognition-Level quality review skill. Applies universal research lenses and
integration auditing to any target within .claude/ infrastructure. Identifies Layer 1
(NL-achievable) improvements and Layer 2 (Ontology Framework) deferrals.
```

**New text:**
```
Meta-Cognition-Level quality review skill with ultrathink deep reasoning. Applies
universal research lenses and integration auditing to any target within .claude/
infrastructure. Identifies Layer 1 (NL-achievable) improvements and Layer 2
(Ontology Framework) deferrals.
```

**Rationale:** Per researcher-2 IMP-1, official Claude Code skills docs state "include the word 'ultrathink' anywhere in your skill content" to enable extended thinking. Placement in intro ensures early processing. Net: +1 word, 0 line change.

### Delta 2: Target Size Pre-Check (IMP-2)

**Location:** After line 51 (after last Dynamic Context shell command)
**Action:** ADD

**New line:**
```
!`wc -l $ARGUMENTS 2>/dev/null`
```

**Rationale:** Pre-checks target file size at skill load time. Helps R-0 decide whether to read files in chunks or whole. ~1 line of output, minimal context cost. Net: +1 line.

### Delta 3: Agent Memory Integration (IMP-3 + IMP-5)

**Location A:** After line 51 (Dynamic Context, after new IMP-2 line)
**Action:** ADD

**New line:**
```
!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50`
```

**Rationale:** Pre-loads cumulative RSIL statistics and patterns into context before R-0 synthesis. The 50-line head captures §1 Config + §2 Lens Performance — the most useful data for informing lens selection and research question generation. Net: +1 line.

**Location B:** After line 483 (R-4 Phase, after "MEMORY.md Update" section)
**Action:** ADD section

**New text:**
```
### Agent Memory Update

Update `~/.claude/agent-memory/rsil/MEMORY.md` using Read-Merge-Write:
- §1 Configuration: increment review count, update last review date
- §2 Lens Performance: update per-lens statistics from this review
- §3 Cross-Cutting Patterns: add new universal pattern (if discovered in this review)
- §4 Lens Evolution: add candidate (if a new universal pattern suggests a new lens)

Only add patterns that apply across ANY target. One-off findings stay in tracker only.
```

**Rationale:** Closes the feedback loop — R-0 reads agent memory (via dynamic context), R-4 writes back accumulated learning. Net: +7 lines.

### Delta 4: Principles Section Merge (IMP-4/IMP-6)

**Location:** Lines 537-561 (Key Principles + Never sections)
**Action:** REPLACE both sections with single merged section

**Old text (25 lines, 2 sections):**
```
## Key Principles
- Framework is universal, scope is dynamic — SKILL.md never changes per target
- Lead's R-0 synthesis is the core value — Lenses × TARGET = specific questions
- Accumulated context is distilled into Lenses — individual findings are not in SKILL.md
- AD-15 inviolable — Category A REJECT, Category B ACCEPT, Category C DEFER
- Layer 1/2 boundary is the single test — "achievable through NL + existing infra?"
- Lenses evolve — new patterns discovered in future reviews can become L9, L10
- Evidence-based only — every finding cites CC docs or file:line references
- User confirms application — BREAK/FIX applied only after user approval
- Sequential thinking always — Lead uses structured reasoning at every decision point
- Terminal, no auto-chain — after RSIL, the user decides what happens next

## Never
- Use hardcoded Research Questions (generate from Lenses in R-0)
- Use hardcoded Integration Axes (derive from file references in R-0)
- Propose adding a new hook (AD-15 8→3 inviolable)
- Promote Category C to Category B (if L2 needed, it's DEFER)
- Accept findings without evidence (CC doc or file:line required)
- Modify files without user approval
- Auto-chain to another skill after completion
- Embed accumulated context in SKILL.md (only Lenses, never raw findings)
- Skip R-0 synthesis (the universal→specific bridge is mandatory)
- Treat Lenses as fixed (they evolve with new pattern discoveries)
```

**New text (15 lines, single section):**
```
## Principles

- Framework is universal, scope is dynamic — generate Research Questions and Integration Axes from Lenses in R-0, never hardcode them
- R-0 synthesis is the core value — the universal→specific bridge is mandatory for every review
- Accumulated context distills into Lenses — individual findings stay in tracker, not SKILL.md
- AD-15 inviolable — Category A REJECT, B ACCEPT, C DEFER. Never propose new hooks.
- Layer 1/2 boundary test is definitive — if Layer 2 is needed, it's DEFER. Never promote C to B.
- Lenses evolve — new universal patterns from future reviews become L9, L10
- Every finding cites CC documentation or file:line references — no unsupported claims
- User confirms all changes — present findings, wait for approval before modifying files
- Use sequential-thinking at every decision point throughout the review
- Terminal skill — user decides next step. No auto-chaining to other skills.
- Never embed raw findings in SKILL.md — only universal Lenses belong here
```

**Rationale:** 60% overlap between Key Principles and Never. Merged into positive-form statements that incorporate the prohibition. 21 items → 11 items, savings ~10 lines. Opus 4.6 follows natural positive instructions without needing separate prohibition lists.

### Delta 5: Output Format Simplification (IMP-7)

**Location:** Lines 201-231 (Static Layer: Output Format)
**Action:** MODIFY (simplify nested templates to guidance)

**Old text (~30 lines with nested code blocks)**

**New text (~25 lines):**
```
## Static Layer: Output Format

Both agents produce structured findings reports.

**[A] claude-code-guide output should include:**
- Findings Table: ID, Finding, Layer, Category, Lens, CC Evidence
- Category B Detail: What, Where (file:section), CC Capability, Why suboptimal, Proposed NL text
- Category C Detail: What, Why L1 cannot, What L2 provides, Current best NL workaround
- L1 Optimality Score (X/10)
- Top 3 Recommendations

**[B] Explore output should include:**
- Axis Results Table: Axis, File A, File B, Status, Findings
- Findings Detail: Axis, Severity, File A (path:line + content), File B (path:line + content), Inconsistency, Specific fix
- Integration Score (X/N axes passing)
```

**Rationale:** Templates were overly prescriptive with nested markdown code blocks. Opus 4.6 follows structured guidance reliably — exact format isn't necessary when required elements are clearly listed. Saves ~5 lines.

### Net Delta Summary

| Change | Lines Added | Lines Removed | Net |
|--------|------------|---------------|-----|
| Delta 1 (ultrathink) | 0 | 0 | 0 |
| Delta 2 (wc -l) | +1 | 0 | +1 |
| Delta 3a (memory read) | +1 | 0 | +1 |
| Delta 3b (memory write) | +7 | 0 | +7 |
| Delta 4 (principles merge) | +11 | -25 | -14 |
| Delta 5 (output simplify) | +13 | -18 | -5 |
| **Total** | **+33** | **-43** | **-10** |

**Final line count:** 561 - 10 = ~551 lines (aligns with researcher-2 estimate)

---

## 5. Component 3: Shared Foundation Specification

### What Is Shared

Three static elements are **identically embedded** in both /rsil-global and /rsil-review:

#### 5.1 Eight Meta-Research Lenses

**Identical text in both skills:**

```
## Static Layer: 8 Meta-Research Lenses

Universal quality principles. Apply to any target — the specific research questions
are generated by Lead based on which lenses are relevant to the observation/target.

| # | Lens | Core Question |
|---|------|---------------|
| L1 | TRANSITION INTEGRITY | Are state transitions explicit and verifiable? Could implicit transitions allow steps to be skipped? |
| L2 | EVALUATION GRANULARITY | Are multi-criteria evaluations individually evidenced? Or bundled into single pass-through judgments? |
| L3 | EVIDENCE OBLIGATION | Do output artifacts require proof of process (sources, tools used)? Or only final results? |
| L4 | ESCALATION PATHS | Do critical findings trigger appropriate multi-step responses? Or only single-shot accept/reject? |
| L5 | SCOPE BOUNDARIES | Are shared resources accessible across scope boundaries? Are cross-scope access patterns handled? |
| L6 | CLEANUP ORDERING | Are teardown/cleanup prerequisites explicitly sequenced? Or assumed to "just work"? |
| L7 | INTERRUPTION RESILIENCE | Is intermediate state preserved against unexpected termination? Or does the process assume completion? |
| L8 | NAMING CLARITY | Are identifiers unambiguous across all contexts where they appear? Or could the same name mean different things? |

Lenses evolve: if new universal patterns are discovered, add L9, L10, etc.
```

**Minor adaptation:** /rsil-review's intro line says "generated by Lead in Phase R-0 based on which lenses are relevant to $ARGUMENTS." /rsil-global's says "generated by Lead during G-1 based on which lenses are relevant to the observation window." The table itself is identical.

#### 5.2 AD-15 Filter

**Identical in both:**

```
## Static Layer: AD-15 Filter

| Category | Test | Action |
|----------|------|--------|
| A (Hook) | Would require adding a new hook | REJECT unconditionally |
| B (NL) | Achievable through .md file changes | ACCEPT — propose exact text |
| C (Layer 2) | Requires structured systems | DEFER — document why L1 insufficient |
```

#### 5.3 Layer 1/2 Boundary Test

**Identical in both:**

```
### Boundary Test

Apply to every finding:

"Can this be achieved through NL .md instructions + 3 existing hooks
 + Task API + MCP tools + Agent Teams messaging + Skill features?"

YES     → Layer 1, Category B — propose exact NL text change
NO      → Layer 2, Category C — document why L1 insufficient
PARTIAL → Split: L1 portion as B + L2 remainder as C
Hook    → REJECT unconditionally (AD-15: 8→3 inviolable)
```

### What Is NOT Shared

| Element | /rsil-global | /rsil-review |
|---------|-------------|-------------|
| Invocation | Auto (NL discipline) | User ($ARGUMENTS) |
| Observation/Target | INFRA health (breadth) | Specific component (depth) |
| Phase structure | G-0→G-4 (observation-first) | R-0→R-4 (synthesis-first) |
| Context budget | ~2000 tokens strict | No strict limit |
| Agent spawn | Tier 3 only (rare) | Always (R-1 parallel) |
| Dynamic context | Tier 0 shell (session/git) | Target-oriented shell (hooks/agents/skills) |
| Layer definitions | NOT embedded (lightweight) | Embedded (needed for agent directives) |
| Integration Audit | NOT included (lightweight) | Included (full methodology) |
| Output format | Compact summary | Full structured report |

### Cross-Reference Protocol

```
/rsil-global finding G-5: "Missing L2 in 60% of sessions"
    │
    ├── decomposed_to: ["P-R12", "P-R13"]
    │   (Lead decides to invoke /rsil-review on specific components)
    │
    └── /rsil-review finds P-R12, P-R13 with cross_refs: ["G-5"]

/rsil-review findings P4-R1, P6-R2, P9-R1: same theme
    │
    ├── promoted_to: "G-8"
    │   (/rsil-global detects pattern across 3 reviews)
    │
    └── G-8 cross_refs: ["P4-R1", "P6-R2", "P9-R1"]
```

**Promotion criteria:** A narrow finding becomes a global pattern when:
1. Same theme appears in ≥3 independent reviews
2. Theme applies across different target types (not target-specific)
3. AD-15 Category B (actionable via NL)

**Decomposition criteria:** A global finding triggers narrow review when:
1. Root cause is unclear from observation window
2. Fix requires detailed component analysis
3. Multiple components may be affected

---

## 6. Component 4: CLAUDE.md Integration

### Placement

After CLAUDE.md §2 Phase Pipeline table (line 33) and its trailing paragraph, before §3 Roles (line 35).

### Exact Text to Add

```markdown
After completing pipeline delivery (Phase 9) or committing .claude/ infrastructure
changes, Lead invokes /rsil-global for INFRA health assessment. Skip for trivial
single-file edits (typo fixes), non-.claude/ changes, or read-only sessions.
The review is lightweight (~2000 token observation budget) and presents findings
for user approval before any changes are applied.
```

**Line count:** 5 lines
**CLAUDE.md impact:** 172 → ~177 lines

### Why This Placement

- After Phase Pipeline table: positions RSIL as a post-pipeline activity (Phase 9.5 conceptually)
- Before Roles: doesn't disrupt the role definitions
- NL discipline approach: natural instruction that Lead reads at session start, not a mechanical trigger
- Measured tone: "invokes" not "MUST invoke", "Skip for" provides clear exceptions

### Non-Pipeline Trigger

The phrase "or committing .claude/ infrastructure changes" covers:
- Type B (skill execution that modifies .claude/ files)
- Type C (direct Lead edits to .claude/ files)
- Excludes: application code changes, read-only sessions

---

## 7. Component 5: Agent Memory Schema

### File: `~/.claude/agent-memory/rsil/MEMORY.md`

### Schema (4 Sections)

```markdown
# RSIL Agent Memory

## 1. Configuration
- Last review: {date}
- Total reviews: {N} (global: {N}, narrow: {N})
- Cumulative findings: {N} (accepted: {N}, rejected: {N}, deferred: {N})
- Acceptance rate: {%}
- Active lenses: L1-L8

## 2. Lens Performance
| Lens | Applied | Findings | Accepted | Rate |
|------|---------|----------|----------|------|
| L1 TRANSITION INTEGRITY | {n} | {n} | {n} | {%} |
| L2 EVALUATION GRANULARITY | {n} | {n} | {n} | {%} |
| L3 EVIDENCE OBLIGATION | {n} | {n} | {n} | {%} |
| L4 ESCALATION PATHS | {n} | {n} | {n} | {%} |
| L5 SCOPE BOUNDARIES | {n} | {n} | {n} | {%} |
| L6 CLEANUP ORDERING | {n} | {n} | {n} | {%} |
| L7 INTERRUPTION RESILIENCE | {n} | {n} | {n} | {%} |
| L8 NAMING CLARITY | {n} | {n} | {n} | {%} |

Top performers: {lenses with >80% acceptance}
Low yield: {lenses with <50% acceptance}

## 3. Cross-Cutting Patterns
Patterns applicable across ANY target. One-off findings stay in tracker.

### P-{N}: {pattern name}
- Origin: {finding IDs}
- Scope: {where applicable}
- Principle: {one-line}
- Applied in: {list of targets}

## 4. Lens Evolution
Candidates for new lenses (L9, L10, ...).

### C-{N}: {candidate name}
- Evidence: {finding IDs from ≥3 reviews}
- Universality: applies to ≥3 target types? {yes/no}
- Proposed question: {draft core question}
- Status: CANDIDATE | PROMOTED | REJECTED
```

### Seed Data (From Current Tracker: 24 findings, 79% acceptance)

```markdown
# RSIL Agent Memory

## 1. Configuration
- Last review: 2026-02-08
- Total reviews: 4 (global: 0, narrow: 4)
- Cumulative findings: 24 (accepted: 19, rejected: 2, deferred: 3)
- Acceptance rate: 79%
- Active lenses: L1-L8

## 2. Lens Performance
| Lens | Applied | Findings | Accepted | Rate |
|------|---------|----------|----------|------|
| L1 TRANSITION INTEGRITY | 4 | 3 | 3 | 100% |
| L2 EVALUATION GRANULARITY | 3 | 2 | 2 | 100% |
| L3 EVIDENCE OBLIGATION | 4 | 3 | 3 | 100% |
| L4 ESCALATION PATHS | 3 | 2 | 2 | 100% |
| L5 SCOPE BOUNDARIES | 4 | 4 | 4 | 100% |
| L6 CLEANUP ORDERING | 2 | 1 | 1 | 100% |
| L7 INTERRUPTION RESILIENCE | 2 | 1 | 0 | 0% |
| L8 NAMING CLARITY | 3 | 2 | 2 | 100% |

Top performers: L1, L3, L5 (highest finding yield with 100% acceptance)
Low yield: L7 (1 finding, 0% acceptance — deferred to Layer 2)

## 3. Cross-Cutting Patterns

### P-1: Evidence Sources in All L2 Outputs
- Origin: P5-R1
- Scope: All teammate types producing L2 output
- Principle: Require "Evidence Sources" section in every L2-summary.md
- Applied in: plan-validation-pipeline, agent-common-protocol.md

### P-2: Explicit Checkpoint Steps in Directives
- Origin: P4-R1
- Scope: All skills that spawn teammates requiring understanding verification
- Principle: Structure as "Step 1: Read+Explain → Wait → Step 2: Execute"
- Applied in: agent-teams-write-plan, agent-teams-execution-plan

### P-3: Cross-File Integration Audit as Standard Step
- Origin: P6 (full RSIL review)
- Scope: All pipeline skill reviews
- Principle: Bidirectional consistency audit catches drift that single-file review misses
- Applied in: rsil-review methodology (standard)

### P-4: Rejection Cascade Specification
- Origin: P9-R1
- Scope: Skills with 2+ user confirmation gates
- Principle: Document which artifacts preserved, which ops skipped, what cleanup needed on rejection
- Applied in: delivery-pipeline

## 4. Lens Evolution
No candidates yet. Monitoring for patterns from future reviews.
```

### 200-Line Budget Allocation

| Section | Lines | Priority |
|---------|-------|----------|
| §1 Configuration | 8 | Critical |
| §2 Lens Performance | 18 | Critical |
| §3 Cross-Cutting Patterns | 50-80 | High (grows over time) |
| §4 Lens Evolution | 10-30 | Medium (grows over time) |
| **Total** | ~86-136 | 60-130 line buffer remaining |

### Read/Write Protocol

**READ (both skills):**
- Dynamic context injection at skill load: `!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50``
- The 50-line head captures §1 + §2 (the most operationally useful data)
- §3 and §4 are available via full read during R-0/G-1 if needed

**WRITE (both skills):**
- At record phase (G-4 for global, R-4 for review)
- Always Read-Merge-Write — never overwrite
- §1: Update counters and date
- §2: Increment per-lens statistics
- §3: Add pattern only if universal (applies across ≥3 targets)
- §4: Add candidate only if ≥3 independent evidence findings

---

## 8. Component 6: Cumulative Data Flow

### System Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Work Completed                        │
│  (Pipeline Phase 9 / Skill execution / Direct edit)     │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              /rsil-global (auto-invoke)                   │
│                                                          │
│  G-0: Observation → G-1: Tiered Read → G-2: Discovery   │
│  G-3: Classify → G-4: Record                            │
│                                                          │
│  Reads: session artifacts, git diff, agent memory        │
│  Writes: tracker (G-{N}), agent memory, summary          │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ (user may invoke, possibly targeting
                        │  areas flagged by /rsil-global)
                        ▼
┌─────────────────────────────────────────────────────────┐
│              /rsil-review (user-invoke)                   │
│                                                          │
│  R-0: Synthesis → R-1: Research → R-2: Classify          │
│  R-3: Apply → R-4: Record                                │
│                                                          │
│  Reads: target files, agent memory, CC docs              │
│  Writes: tracker (P-R{N}), agent memory, target files    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    Next Work Cycle                        │
│  /rsil-global reads agent memory → informed by all       │
│  previous findings → better lens application →           │
│  better findings → continuous improvement                │
└─────────────────────────────────────────────────────────┘
```

### Trigger Matrix

| Event | Tracker | Agent Memory | Main MEMORY |
|-------|---------|-------------|-------------|
| /rsil-global G-4 (any findings) | Append G-{N} to §3 Global, update §2 Summary | Update §1 stats, §2 lens perf, §3 if pattern | Only if new cross-cutting pattern |
| /rsil-global G-4 (clean) | No change to findings | Update §1 (date, count+1) | No change |
| /rsil-review R-4 (findings) | Append P-R{N} to §3 sprint section, update §2 | Update §1 stats, §2 lens perf, §3 if pattern | Only if new cross-cutting pattern |
| Narrow→Global promotion | Add cross_ref links, create G-{N} | Add to §3 Patterns | Update RSIL summary |
| Global→Narrow decomposition | Add cross_ref links, note decomposed_to | No change | No change |
| Lens evolution (promoted) | Note in finding that triggered it | Move from §4 to Lenses table | Update lens count |
| Tracker split (>150 findings) | Archive old → fresh active | No change | Note archive date |

### Version Tracking

No formal version numbers needed. Tracking is implicit through:
- **Tracker:** Finding IDs are monotonically increasing (G-1, G-2... and P-R1, P-R2...)
- **Agent Memory §1:** "Last review" date + "Total reviews" count
- **Consistency check:** Agent memory §1 counts should match tracker §2 Summary Table totals

If inconsistency detected between agent memory and tracker counts:
1. Tracker is source of truth (detailed audit trail)
2. Recalculate agent memory §1 from tracker §2 Summary Table
3. Note the correction in agent memory

---

## 9. Risk Matrix

| # | Risk | L | I | Score | Mitigation |
|---|------|---|---|-------|------------|
| R-1 | Tier 0 work type misclassification | LOW | MED | 3 | Multiple independent signals (session dir + git diff + skill trace). Fallback: treat as Type A (most comprehensive). |
| R-2 | Context budget overrun in large sessions | MED | LOW | 4 | Cap at 3 most recent L1 files (researcher-1 U-2). Note truncation in assessment. |
| R-3 | NL discipline non-compliance (Lead forgets) | MED | LOW | 4 | CLAUDE.md §2 instruction + agent memory §1 "last review" date creates staleness awareness. No mechanical enforcement needed — NL discipline is a conscious choice. |
| R-4 | Tracker growth beyond manageable size | LOW | LOW | 2 | Split at 150 findings into quarterly archives (researcher-1 TA-4). Active tracker keeps last 50 + open backlog + patterns. |
| R-5 | Agent memory 200-line limit pressure | MED | LOW | 4 | Budget allocation pre-defined. §3 Patterns capped by universality filter (≥3 targets). §4 Evolution capped by evidence threshold (≥3 reviews). Buffer: 60-130 lines. |
| R-6 | Shared agent memory write conflict | LOW | MED | 3 | Sequential execution only (U-3). Natural ordering: global first, review later. Read-Merge-Write pattern. |
| R-7 | /rsil-global generates noise (many low-value findings) | MED | LOW | 4 | Tier escalation gates filter signal. Most clean runs → zero findings. AD-15 filter catches non-actionable items. Agent memory tracks acceptance rate — low rates trigger self-correction. |

---

## 10. Phase 4 Readiness Notes

### What Phase 4 (Detailed Design) Needs to Produce

1. **Exact SKILL.md text for /rsil-global** — complete file content (~400-500 lines)
2. **Exact change specifications for /rsil-review** — all 5 deltas with precise old/new text
3. **Exact CLAUDE.md addition** — 5 lines, precise insertion point
4. **Agent memory seed file** — ready-to-create content
5. **Tracker schema migration plan** — how to add Global Findings section + extended schema to existing tracker
6. **Implementation task breakdown** — file ownership, ordering, dependencies

### Architecture Constraints for Phase 4

- /rsil-global SKILL.md should follow the same structural pattern as /rsil-review (frontmatter → When to Use → Dynamic Context → Phase 0 → Static Layers → Phases → Error Handling → Principles)
- The 5 /rsil-review deltas should be applicable independently (no ordering dependency between deltas)
- CLAUDE.md change is a single atomic insertion (no multi-location edit)
- Agent memory seed data should be derivable from current tracker (no manual data entry needed)
- Tracker migration should be backward-compatible (existing P-R{N} findings unchanged, new Global section added)

### Recommended Implementation Split

| Task | Files | Implementer |
|------|-------|-------------|
| A: /rsil-global SKILL.md | `.claude/skills/rsil-global/SKILL.md` (NEW) | implementer-1 |
| B: /rsil-review deltas + CLAUDE.md | `.claude/skills/rsil-review/SKILL.md` (MODIFY), `.claude/CLAUDE.md` (MODIFY) | implementer-2 |
| C: Agent memory + tracker | `~/.claude/agent-memory/rsil/MEMORY.md` (NEW), `docs/plans/2026-02-08-narrow-rsil-tracker.md` (MODIFY) | implementer-2 |

Zero file overlap between Task A and Tasks B+C. Tasks B+C share an implementer because the /rsil-review deltas reference the agent memory schema (Delta 3).

---

*Architecture design complete. All 6 components specified with decisions, evidence, and Phase 4 guidance.*
