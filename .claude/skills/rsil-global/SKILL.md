---
name: rsil-global
description: "INFRA Meta-Cognition health assessment — auto-invoked by Lead after pipeline delivery or .claude/ infrastructure changes. Three-Tier observation window, 8 universal lenses, AD-15 filter. Lightweight (~2000 token budget). Findings-only output."
argument-hint: "[optional: specific area of concern]"
---

# RSIL Global

INFRA Meta-Cognition health assessment with ultrathink deep reasoning. Auto-invoked by Lead
after pipeline delivery or .claude/ infrastructure changes. Three-Tier Observation Window
reads only what's needed (~2000 token budget). Identifies INFRA consistency issues across
the just-completed work. Findings-only output — user approves before any changes.

**Announce at start:** "Running RSIL Global health assessment for the just-completed work."

**Core flow:** G-0 Observation Classification → G-1 Tiered Reading → G-2 Discovery (rare) → G-3 Classification → G-4 Record

## When to Use

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

**What this skill does:** Lightweight INFRA health scan using Three-Tier Observation
Window. Reads session artifacts and git diffs. Classifies findings using 8 Lenses
and AD-15 filter. Presents findings for user approval.

**What this skill does NOT do:** Deep component analysis (use /rsil-review), modify
files directly, spawn long-lived teammates, or auto-chain to other skills.

## Dynamic Context

!`ls -dt .agent/teams/*/ 2>/dev/null | head -3`

!`ls .agent/teams/*/phase-*/gate-record*.yaml 2>/dev/null | wc -l`

!`find .agent/teams/ -name "L1-index.yaml" 2>/dev/null | wc -l`

!`git diff --name-only HEAD~1 2>/dev/null | head -20`

!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50`

!`wc -l docs/plans/2026-02-08-narrow-rsil-tracker.md 2>/dev/null`

**Feature Input:** $ARGUMENTS (optional — specific area of concern)

---

## Phase 0: PERMANENT Task Check

Call `TaskList` and search for a task with `[PERMANENT]` in its subject.

```
TaskList result
     │
┌────┴────┐
found      not found
│           │
▼           ▼
TaskGet →   AskUser: "No PERMANENT Task found.
read PT     Create one for this feature?"
│           │
▼         ┌─┴─┐
Continue  Yes   No
to G-0    │     │
          ▼     ▼
        /permanent-tasks    Continue to G-0
        creates PT-v1       without PT
        → then G-0
```

If a PERMANENT Task exists, extract pipeline context (phase status, constraints,
recent architecture decisions) to inform observation window classification.

---

## Phase G-0: Observation Window Classification

Lead-only. Use sequential-thinking.

Classify the just-completed work using Dynamic Context output (Tier 0 data):

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

### Classification Rules

- **Type A (Pipeline):** `.agent/teams/` has session directories with gate records
- **Type B (Skill execution):** No session dir, but git diff shows .claude/ skill or reference changes
- **Type C (Direct edit):** No session dir, git diff shows .claude/ .md changes (not skills)
- **No work:** No git diff, no new sessions — skip entirely

**Mixed signals:** If both pipeline artifacts AND direct .claude/ edits are present
(e.g., a pipeline delivery that also modified CLAUDE.md directly), classify as Type A.
Type A's reading scope is the most comprehensive and subsumes Type B/C signals.
Note the .claude/ edits as additional context for G-1 lens application.

**Fallback rule:** When classification is uncertain, default to Type A.

**$ARGUMENTS handling:** If a specific concern was provided, note it for lens
prioritization in G-1. The concern does not change the work type — it focuses
which lenses receive deeper attention.

---

## Phase G-1: Tiered Reading + Health Assessment

Lead-only. Use sequential-thinking for each tier transition decision.

This is the core assessment phase. Read just enough to determine INFRA health,
then stop. Most runs complete at Tier 1.

### Tier 1 Reading

Read scope depends on work type from G-0. Stay within ~500 tokens per read.

**Type A — Pipeline work:**
1. Read the LATEST gate-record.yaml (most recent session, most recent phase)
2. Read the LATEST L1-index.yaml files (cap: 3 most recent)
3. Skim orchestration-plan.md (last 20 lines for current status)

**Type B — Skill execution:**
1. Read `git diff HEAD~1` for .claude/ file content changes
2. Read tracker diff (if narrow-rsil-tracker.md was modified)
3. Check if modified files reference other .claude/ files (cross-ref scan)

**Type C — Direct edit:**
1. Read `git diff HEAD~1` content for specific changes
2. Read MEMORY.md diff (if changed)
3. List files that reference the modified files

### Health Indicator Assessment

Apply these 5 indicators to Tier 1 data:

| # | Indicator | Type A Signal | Type B/C Signal |
|---|-----------|---------------|-----------------|
| H-1 | Gate pass rate | PASS/FAIL counts in gate record | N/A (no gates) |
| H-2 | L1/L2 existence | Missing L1/L2 from any teammate | N/A |
| H-3 | Re-spawn count | Multiple `{role}-{N}` dirs same phase | N/A |
| H-4 | Warning density | TEAM-MEMORY.md warning count | N/A |
| H-5 | Cross-ref consistency | L1 references match across teammates | Diff references match target files |

Type B/C only have H-5 (cross-reference consistency) as directly measurable.
For Type B/C, Tier 1 primarily answers: "Do the changes maintain cross-file consistency?"

### Lens Application During Reading

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

Generate observations at this stage — not full findings. Observations feed G-3
for classification.

If $ARGUMENTS specified a concern, give extra attention to the lenses most relevant
to that concern.

### Escalation Decision: Tier 1 → Tier 2

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

### Tier 2 Reading (Selective, ~1000 tokens)

Only for areas flagged by Tier 1. Read selectively:

- L2-summary.md for flagged teammates or phases
- TEAM-MEMORY.md for warning and pattern context
- For Type B/C: the actual modified files + their reference targets
- Cross-check: are issues systemic (cross-file) or localized?

### Escalation Decision: Tier 2 → Tier 3

```
≥3 cross-file anomalies detected    → Tier 3 (G-2)
OR ≥2 BREAK-severity issues         → Tier 3 (G-2)
OR systemic pattern across sessions → Tier 3 (G-2)
Otherwise                           → Skip G-2, proceed to G-3
```

---

## Phase G-2: Discovery (Tier 3 Only)

Most runs skip this phase entirely. Only triggered by Tier 2 escalation.

Spawn a codebase-researcher agent to investigate systemic anomalies:

```
subagent_type: "codebase-researcher"
prompt:
  "Investigate the following INFRA anomalies detected by /rsil-global:
   {list anomalies from Tier 2 with file paths and observations}

   For each anomaly:
   1. Read ALL referenced files bidirectionally
   2. Verify cross-file consistency
   3. Classify by severity: BREAK (runtime failure) / FIX (quality) / WARN (cosmetic)
   4. Return structured findings with file:line evidence"
```

**When to also spawn claude-code-guide:** Only if Tier 2 observations suggest a CC
capability gap (e.g., "this pattern might be better handled by a CC feature we're
not using"). This is rare — most global findings are consistency issues.

Collect structured findings and proceed to G-3.

---

## Phase G-3: Classification + Presentation

Lead-only. Use sequential-thinking.

### Classify All Observations and Findings

For each observation from G-1 (Tier 1/2) or finding from G-2 (Tier 3):

```
Apply AD-15 Filter:
├── Would require new hook? → Category A → REJECT
├── Achievable through .md NL change? → Category B → FIX
└── Requires Layer 2 structured system? → Category C → DEFER

Apply Severity:
├── Runtime failure risk? → BREAK
├── Quality degradation? → FIX
└── Cosmetic/minor? → WARN
```

### Present to User

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

**BREAK handling:** Use AskUserQuestion — "RSIL Global found {N} BREAK-severity
issues requiring attention. Review and fix now, or defer to next session?"

**Zero findings:** "INFRA healthy. No findings from this assessment." → proceed to G-4.

---

## Phase G-4: Record

### Tracker Update

Read-Merge-Write to `docs/plans/2026-02-08-narrow-rsil-tracker.md`:

1. **§2 Summary Table:** Add row with source_skill=rsil-global
2. **§3 Global Findings:** Append G-{N} entries using this schema:
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

### Agent Memory Update

Read-Merge-Write to `~/.claude/agent-memory/rsil/MEMORY.md`:

- §1 Configuration: increment review count, update date
- §2 Lens Performance: increment findings/accepted per lens used
- §3 Cross-Cutting Patterns: add new universal pattern (if discovered)
- §4 Lens Evolution: add lens candidate (if identified)

### Terminal Summary

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

---

## Error Handling

| Situation | Response |
|-----------|----------|
| No git diff and no sessions | "No recent work detected. Skipping." |
| Tier 0 misclassification suspected | Fall back to Type A reading (most comprehensive) |
| Tier 1 reads exceed budget | Cap at 3 L1 files + 1 gate record. Note truncation. |
| Tier 3 agent returns empty | Proceed with Tier 1/2 findings only |
| Tracker file not found | Create initial section structure, then append |
| Agent memory not found | Create with seed data from tracker |
| User cancels mid-review | Preserve partial tracker updates |

---

## Static Layer: 8 Meta-Research Lenses

Universal quality principles. Apply to any target — the specific research questions
are generated by Lead during G-1 based on which lenses are relevant to the observation window.

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

Lenses evolve: if new universal patterns are discovered, add L9, L10, etc. Update this
table and MEMORY.md accordingly.

---

## Static Layer: AD-15 Filter

| Category | Test | Action |
|----------|------|--------|
| A (Hook) | Would require adding a new hook | REJECT unconditionally |
| B (NL) | Achievable through .md file changes | ACCEPT — propose exact text |
| C (Layer 2) | Requires structured systems | DEFER — document why L1 insufficient |

### Boundary Test

Apply to every finding:

```
"Can this be achieved through NL .md instructions + 3 existing hooks
 + Task API + MCP tools + Agent Teams messaging + Skill features?"

YES     → Layer 1, Category B — propose exact NL text change
NO      → Layer 2, Category C — document why L1 insufficient
PARTIAL → Split: L1 portion as B + L2 remainder as C
Hook    → REJECT unconditionally (AD-15: 8→3 inviolable)
```

---

## Key Principles

- Lightweight by design — most runs complete at Tier 1 with zero findings
- Observation window stays under ~2000 tokens (Tier 0+1+2 combined)
- Findings-only output — user approves before any changes
- AD-15 inviolable — Category A REJECT, B ACCEPT, C DEFER
- Lenses generate observations, not prescriptions
- Tier 3 (codebase-researcher agent) is the exception, not the norm
- Record everything — even "clean" runs update agent memory statistics
- Self-healing through persistence — unfixed BREAKs are re-detected next session
- Terminal — no auto-chaining to /rsil-review or other skills
- INFRA scope only — never assess application code
- Use sequential-thinking at every tier transition and classification decision

## Never

- Modify files without user approval (findings-only output)
- Auto-chain to /rsil-review or other skills after completion
- Propose adding a new hook (AD-15 8→3 inviolable)
- Promote Category C to Category B (if L2 needed, it's DEFER)
- Skip G-0 classification (observation window type determines reading scope)
- Exceed ~2000 token observation budget without noting truncation
- Spawn agents for Tier 1 or Tier 2 work (agents only at Tier 3)
- Treat Lenses as fixed (they evolve with new pattern discoveries)
- Assess application code (INFRA scope only — .claude/ and pipeline artifacts)
