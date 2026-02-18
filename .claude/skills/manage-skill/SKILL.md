---
name: manage-skill
description: >-
  Audits and improves skill L1/L2 quality to maximize Lead routing
  intelligence. L1 audit: routing signal density within 1024-char
  budget, context distribution hints, failure route summary, output
  location clarity, and cross-skill transition consistency. L2
  audit: DPS completeness per tier, 3-channel handoff compliance
  (PT signal + tasks/{team}/ output + SendMessage micro-signal),
  iteration tracking in PT metadata, and cognitive focus filtering
  in DPS Context fields. Cross-skill audit: transition graph
  orphans, domain compound failure gaps, and handoff protocol
  consistency. Homeostasis skill invoked explicitly. Reads all
  .claude/skills/*/SKILL.md. Produces scored audit with fix
  proposals (old/new diff, batch approval) plus cross-skill
  integrity report. Also handles skill creation, retirement,
  and L1 description optimization within 1024-char budget.
user-invocable: true
disable-model-invocation: true
argument-hint: "[audit|audit-single <n>|create <n>|retire <n>|optimize-l1 <n>]"
---

# Manage Skill — Skill Infrastructure Quality & Lifecycle

## Execution Model
- **audit / audit-single**: Lead-direct or analyst spawn depending on scope.
  - `audit-single <n>`: Lead-direct. Single skill, inline analysis.
  - `audit` (all skills): Spawn 2 analysts. Split: L1+cross-skill vs L2+DPS.
- **create**: Lead-direct. Interactive skill scaffolding with AskUserQuestion.
- **retire**: Lead-direct. Skill removal with transition rerouting.
- **optimize-l1**: Lead-direct. Rewrite L1 description within 1024-char budget.

## Governing Decisions (D1-D17)

This skill enforces the following confirmed design decisions across all skills:

| Decision | Enforcement Point |
|----------|------------------|
| D6: L1 1024-char hard limit | L1 audit char count |
| D8: coordinator L1/L2/L3 tiered output pattern | Cross-skill pattern consistency check |
| D10: P5(failure route) + P6(context hint) in all L1s | L1 signal extraction scoring |
| D11: Context Distribution priority (cognitive focus > token > progressive > asymmetric) | L2 DPS Context field audit |
| D12: Re-planning full autonomy ladder | L2 Failure Handling completeness |
| D15: Iteration tracking in PT metadata | L2 iteration ownership check |
| D16: Fix mode = propose+approve (old/new diff, batch) | Audit output format |
| D17: 3-channel Hybrid handoff (PT signal + tasks/{team}/ + SendMessage) | L2 output location + delivery audit |

## CC Native Constraint: L1 Description Budget

**Hard limit: 1024 English characters (including spaces) per skill description field.**

This is the ONLY information Lead auto-loads for routing decisions across all skills. Everything beyond this requires on-demand L2 loading.

### L1 Information Density Formula

Every L1 description must pack these routing signals (priority order):

| Priority | Signal | Purpose | Example |
|----------|--------|---------|---------|
| P0 | **Core verb** | What this skill does | "Verifies CC native implementability" |
| P1 | **Method** | How it does it | "via cc-reference cache or claude-code-guide" |
| P2 | **Pipeline position** | When + prerequisites | "Terminal pre-design skill. Use after validate PASS" |
| P3 | **Input source** | Reads FROM (with skill name) | "Reads from pre-design-validate validated requirements" |
| P4 | **Output target** | Produces FOR (with skill name + condition) | "Produces feasibility verdict for design-architecture on PASS" |
| P5 | **Failure route** | Where on FAIL (with skill name) | "routes back to brainstorm on FAIL" |
| P6 | **Context hint** | What Lead must prepare for DPS | "DPS needs architecture L1 components + L2 ADRs" |

**Budget allocation guideline:**
- P0-P2: ~400 chars (core identity + position)
- P3-P5: ~400 chars (data flow + failure route)
- P6: ~200 chars (context distribution hint)
- Total: ≤1024 chars

### L1 Quality Scoring Rubric

| Dimension | Weight | 0 (Missing) | 1 (Partial) | 2 (Complete) |
|-----------|--------|-------------|-------------|--------------|
| Core verb + method | 15% | No action verb | Verb but vague method | Clear verb + specific method |
| Pipeline position | 15% | No position info | Phase but no prerequisites | Phase + prerequisite skills + trigger |
| Input source | 15% | No input mentioned | "Reads from X" no skill name | "Reads from {skill} {data-type}" |
| Output target | 15% | No output mentioned | "Produces X" no target skill | "Produces {data} for {skill} on {condition}" |
| Failure route | 15% | No failure info | "FAIL" but no route | "Routes to {skill} on FAIL with {data}" |
| Context hint | 15% | No DPS guidance | Partial ("needs architecture") | "DPS needs {skill} L1 {fields} + L2 {sections}" |
| Char efficiency | 10% | >1024 or <500 | 500-700 (underutilized) | 700-1024 (well-utilized) |

**Score thresholds:**
- **A (≥1.7)**: L1 enables routing without L2 load
- **B (1.3-1.6)**: L1 enables routing with occasional L2 reference
- **C (0.9-1.2)**: L1 requires frequent L2 loads
- **F (<0.9)**: L1 insufficient for routing

## Decision Points

### Audit Scope Selection
- `audit`: Full audit of all skills. Cross-skill integrity + per-skill scores.
- `audit-single <n>`: Single skill + connected skills transition check.
- Default: If no argument, prompt via AskUserQuestion.

### Analyst Division (Full Audit)
- **Analyst A (L1 + Cross-Skill)**: All SKILL.md frontmatter. L1 scores. Transition graph. Orphans, duplicates.
- **Analyst B (L2 + DPS)**: All SKILL.md bodies. DPS completeness. 3-channel compliance. Iteration tracking.
- **Lead merges**: Cross-references A's transition gaps with B's DPS gaps.

### Fix Proposal Mode (D16)
All audit findings produce fix proposals in **propose+approve** mode:
1. Audit produces per-skill score card with specific issues
2. For each issue: old text, proposed new text, character count delta
3. Batch presentation: group by severity (F→C→B), max 5 skills per batch
4. AskUserQuestion per batch: "Apply these N fixes?" with per-skill toggle
5. Only approved fixes are applied

## Methodology

### 1. Discover Skills
```
Glob: .claude/skills/*/SKILL.md
```
Parse each: frontmatter (`name`, `description`, flags) + body section headers.

### 2. Audit L1 Descriptions (Per-Skill)

#### 2a. Character Count
- Total characters including spaces
- Flag >1024 as CRITICAL (over budget)
- Flag <500 as UNDERUTILIZED (can pack more signals)

#### 2b. Signal Extraction (P0-P6)
Parse description for each signal. Score per rubric.

#### 2c. D11 Cognitive Focus Check (P6 specific)
When P6 context hint exists, verify it follows D11 priority:
- Does it specify what to **exclude** (noise filter), not just what to include?
- Does it distinguish what Lead needs vs what teammate needs?
- Example GOOD: "DPS needs architecture L1 components only. Exclude L2 ADR rationale — teammate needs structure not reasoning."
- Example BAD: "Needs all architecture data."

### 3. Audit L2 Methodology (Per-Skill)

#### 3a. DPS Completeness Check

| Check | PASS Condition |
|-------|---------------|
| Tier-specific DPS | TRIVIAL, STANDARD, COMPLEX each addressed |
| DPS 5 fields | Context, Task, Constraints, Expected Output, Delivery |
| Context field cognitive focus | Specifies inclusions AND exclusions per D11 |
| Delivery field 3-channel | Matches D17 protocol (see 3b) |
| Output location physical | `~/.claude/tasks/{team}/{phase}-{skill}.md` |

#### 3b. D17 Three-Channel Handoff Compliance

Every skill's output section must specify all 3 channels:

| Channel | Location | Content | Check |
|---------|----------|---------|-------|
| PT metadata | `metadata.phase_signals.{phase}` | Compact signal: `"PASS\|key:value"` | Does L2 Output section mention PT update? |
| Full output file | `~/.claude/tasks/{team}/{phase}-{skill}.md` | L1 YAML + L2 detail | Does L2 specify file path pattern? |
| SendMessage | Lead inbox | Micro-signal: `"PASS\|ref:tasks/{team}/{phase}-{skill}.md"` | Does DPS Delivery field match? |

**Migration from /tmp/pipeline/**: Flag any skill still referencing `/tmp/pipeline/` as needing update to `tasks/{team}/`.

#### 3c. D15 Iteration Tracking Check
For skills involved in loops (brainstorm↔validate, feasibility retries):
- Does L2 mention iteration count?
- Is `PT metadata iterations.{skill}: N` the tracking mechanism?
- Does max iteration limit reference PT-based count (not Lead memory)?

#### 3d. D12 Re-planning Completeness
Verify failure handling covers the full escalation ladder:

| Level | Action | Check |
|-------|--------|-------|
| L0 | Retry same agent, same task | "Retry" or "re-invoke" in failure handling? |
| L1 | Nudge agent with refined context | "Refined DPS" or "additional context" mentioned? |
| L2 | Kill & respawn fresh agent | "Re-spawn" or "new agent" mentioned? |
| L3 | Restructure task graph | "Task re-decomposition" or "dependency change" mentioned? |
| L4 | Escalate to Human | "AskUserQuestion" or "Human decision" mentioned? |

Not all skills need all 5 levels. But skills with Failure Handling sections should cover at least L0, L2, L4.

#### 3e. Transition Consistency
For each `Sends To` / `Receives From`:
- Target/source skill exists?
- Bidirectional reference match?
- Data format consistent?

### 4. Cross-Skill Integrity Audit

#### 4a. Orphan Detection
- Dead-end targets (Sends To nonexistent skill)
- Orphan sources (Receives From nonexistent skill)
- Unreachable skills (not in any pipeline path)

#### 4b. Domain Compound Failure Gaps
Per pipeline domain: what if 2+ skills fail simultaneously?

#### 4c. Handoff Protocol Consistency
- All skills use same `tasks/{team}/` pattern (not mixed with `/tmp/pipeline/`)
- SendMessage micro-signal format consistent across skills
- PT signal key naming consistent (`phase_signals.{phase}`)

#### 4d. Context Distribution Pattern Adoption
- How many domains use coordinator's L1/L2/L3 tiered output?
- Which domains should adopt it?

### 5. Produce Audit Report

#### Per-Skill Score Card
```yaml
skill: {name}
l1_score: 0.0  # 0.0-2.0
l1_grade: A|B|C|F
l1_chars: 0
l1_budget_remaining: 0
signals:
  p0_verb: PASS|FAIL
  p1_method: PASS|FAIL
  p2_position: PASS|FAIL
  p3_input: PASS|FAIL
  p4_output: PASS|FAIL
  p5_failure: PASS|FAIL
  p6_context_hint: PASS|FAIL
l2_compliance:
  dps_completeness: PASS|FAIL
  d17_handoff: PASS|FAIL
  d15_iteration: PASS|FAIL|N/A
  d12_replanning: PASS|FAIL
fixes:
  - issue: "P5 failure route missing"
    old: ""
    new: "routes to brainstorm on FAIL with gap report"
    char_delta: +45
```

#### Cross-Skill Integrity Report
```yaml
transition_graph:
  total_edges: 0
  orphans: []
  dead_ends: []
handoff_compliance:
  d17_compliant: 0
  tmp_pipeline_legacy: 0
  missing_sendmessage: 0
domain_compound_gaps: []
context_distribution:
  l1l2l3_adoption: "1/N domains"
```

### 6. Fix Proposal (D16 Mode)

After audit, for each skill with grade < A:

1. Generate proposed L1 rewrite (optimize-l1 logic)
2. Generate proposed L2 patches (D17 handoff, D15 iteration, D12 re-planning)
3. Present as batch:
```
=== Batch 1: F-grade skills (3 skills) ===

[1] pre-design-brainstorm
    L1: 348 → 891 chars | C → A
    OLD: "Gathers requirements through structured..."
    NEW: "Gathers requirements via structured AskUserQuestion..."
    Issues fixed: +P5 failure route, +P6 context hint

[2] research-codebase
    L1: 562 → 934 chars | C → A
    ...

Apply batch? [All / Select individually / Skip]
```
4. AskUserQuestion with batch approval options

### 7. Optimize L1 (optimize-l1 action)

Single skill rewrite:
1. Read current description, score against rubric
2. Identify missing signals (P0-P6)
3. Rewrite maximizing signal density within 1024 chars
4. **Rewrite rules:**
   - Remove redundant words ("This skill" → implied)
   - Ensure P5 failure route present
   - Add P6 context hint with D11 cognitive focus framing
   - Sentence structure: `Verb + object + method. Position. Input. Output. Failure. Context hint.`
5. Present old vs new with scores
6. AskUserQuestion: apply or reject

### 8. Create Skill (create action)

1. AskUserQuestion: domain, pipeline position, connected skills
2. Generate frontmatter (L1 ≥ A grade, 1024 chars)
3. Generate L2 skeleton with:
   - Execution Model (3 tiers)
   - Decision Points
   - Methodology with DPS templates
   - D17 Output section (3-channel handoff)
   - D15 Iteration tracking (if loop skill)
   - D12 Failure Handling (escalation ladder)
   - Transitions (Receives From / Sends To / Failure Routes)
4. Validate L1 score ≥ 1.7 before output

### 9. Retire Skill (retire action)

1. Transition graph impact: which skills reference this one?
2. Report all broken edges
3. Suggest rerouting
4. AskUserQuestion: confirm with rerouting plan
5. Output: deletion target + other skills needing Transition updates

## Failure Handling

### Skill File Parse Error
- **Action**: Report with file path. Score as F. Propose fix.
- **Escalation**: L0 (retry parse), L4 (Human if structural)

### Cross-Skill Reference to Non-Existent Skill
- **Action**: Flag as orphan edge. May be: not yet created, renamed, or typo.
- **Escalation**: L1 (suggest correct name), L4 (Human if ambiguous)

### L1 Over Budget (>1024 chars)
- **Action**: CRITICAL flag. Propose trimmed version preserving P0-P5, compressing P6.
- **Escalation**: L0 (auto-trim), L4 (Human if signal must be sacrificed)

## Anti-Patterns

### DO NOT: Audit Without Reading All Skills
Full audit requires all SKILL.md files. Partial audits miss cross-skill integrity issues.

### DO NOT: Optimize L1 by Removing Routing Signals
When trimming, never remove P0-P5. Compress wording. P6 can be abbreviated but not removed.

### DO NOT: Create Skills Without Transition Validation
New skills must have valid Receives From / Sends To. No orphan creation.

### DO NOT: Auto-Apply Fixes Without Approval
D16 mandates propose+approve mode. Never write to SKILL.md without Human batch approval via AskUserQuestion.

### DO NOT: Ignore /tmp/pipeline/ Legacy References
D17 standardized on `tasks/{team}/`. Any remaining `/tmp/pipeline/` references must be flagged for migration.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|---|---|---|
| (User invocation) | Action request | $ARGUMENTS: "audit", "audit-single X", "create X", "retire X", "optimize-l1 X" |
| self-diagnose | Skill health issues | Category 10 findings |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| (Lead context) | Audit report + fix proposals | After audit/audit-single |
| (Lead context) | New SKILL.md content | After create |
| (Lead context) | Retirement impact report | After retire |
| (Lead context) | Optimized L1 with old/new diff | After optimize-l1 |

### Failure Routes
| Failure Type | Route To | Data Passed |
|---|---|---|
| Skill parse error | (Lead context) | Error + file path |
| Over-budget L1 | (Self — optimize-l1) | Current + trimmed proposal |

## Quality Gate
- All discovered skills scored (full audit: none skipped)
- L1 scores use consistent rubric
- Cross-skill transition graph complete
- D17 handoff compliance checked for all skills
- Fix proposals include old/new diff with char counts
- No fixes applied without Human approval (D16)

## Output

### L1
```yaml
domain: homeostasis
skill: manage-skill
action: audit|audit-single|create|retire|optimize-l1
skills_audited: 0
avg_l1_score: 0.0
grade_distribution:
  A: 0
  B: 0
  C: 0
  F: 0
cross_skill_issues: 0
d17_compliance_pct: 0
```

### L2
- Per-skill score cards with fix proposals (audit)
- Cross-skill integrity report (audit)
- New skill content (create)
- Retirement impact (retire)
- Old/new L1 diff (optimize-l1)

### Output Location (D17)
- Full report: `~/.claude/tasks/{team}/homeostasis-manage-skill.md`
- PT signal: `metadata.phase_signals.homeostasis: "PASS|audited:{N}|avg:{score}"`
- SendMessage: `"PASS|action:{type}|audited:{N}|ref:tasks/{team}/homeostasis-manage-skill.md"`
