---
name: manage-skill
description: >-
  Audits and improves skill L1/L2 quality to maximize Lead routing
  intelligence. L1 audit: routing signal density within 1024-char
  budget, context distribution hints, failure route summary, output
  location clarity, and cross-skill transition consistency. L2
  audit: DPS completeness per tier, Two-Channel handoff compliance
  (Ch2 file output + Ch3 micro-signal),
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

This skill enforces confirmed design decisions across all skills:

| Decision | Enforcement Point |
|----------|------------------|
| D6: L1 1024-char hard limit | L1 audit char count |
| D8: coordinator L1/L2/L3 tiered output pattern | Cross-skill pattern consistency check |
| D10: P5(failure route) + P6(context hint) in all L1s | L1 signal extraction scoring |
| D11: Context Distribution priority (cognitive focus > token > progressive > asymmetric) | L2 DPS Context field audit |
| D12: Re-planning full autonomy ladder | L2 Failure Handling completeness |
| D15: Iteration tracking in PT metadata | L2 iteration ownership check |
| D16: Fix mode = propose+approve (old/new diff, batch) | Audit output format |
| D17: Two-Channel handoff (Ch2 tasks/{work_dir}/ file output + Ch3 micro-signal to Lead) | L2 output location + delivery audit |

## CC Native Constraint: L1 Description Budget

**Hard limit: 1024 English characters (including spaces) per skill description field.**

This is the ONLY information Lead auto-loads for routing decisions. Everything beyond this requires on-demand L2 loading.

Every L1 must pack 7 routing signals (P0 core verb → P6 context hint). Budget: P0-P2 ~400 chars, P3-P5 ~400 chars, P6 ~200 chars.

**Score thresholds:**
- **A (≥1.7)**: L1 enables routing without L2 load
- **B (1.3-1.6)**: L1 enables routing with occasional L2 reference
- **C (0.9-1.2)**: L1 requires frequent L2 loads
- **F (<0.9)**: L1 insufficient for routing

> Full signal priority table, budget allocation, and 7-dimension scoring rubric: read `resources/methodology.md`

## Decision Points

### Audit Scope Selection
- `audit`: Full audit of all skills. Cross-skill integrity + per-skill scores.
- `audit-single <n>`: Single skill + connected skills transition check.
- Default: If no argument, prompt via AskUserQuestion.

### Analyst Division (Full Audit)
- **Analyst A (L1 + Cross-Skill)**: All SKILL.md frontmatter. L1 scores. Transition graph. Orphans, duplicates.
- **Analyst B (L2 + DPS)**: All SKILL.md bodies. DPS completeness. 2-channel compliance. Iteration tracking.
- **Lead merges**: Cross-references A's transition gaps with B's DPS gaps.

### Fix Proposal Mode (D16)
All audit findings produce fix proposals in **propose+approve** mode:
1. Per-skill score card with specific issues
2. For each issue: old text, proposed new text, character count delta
3. Batch by severity (F→C→B), max 5 skills per batch
4. AskUserQuestion per batch: "Apply these N fixes?" with per-skill toggle
5. Only approved fixes are applied

> Detailed audit steps (1-9), score card YAML template, D17 compliance tables, fix proposal batch format: read `resources/methodology.md`

## Phase-Aware Execution
- **Homeostasis (all tiers)**: Lead-direct or analyst spawn. No team infrastructure for audit-single. Full audit may use team mode for parallel analysts.
- **P2+ (background subagents)**: Analysts spawn with `run_in_background:true`, `context:fork`. Deliver via Two-Channel Protocol.
- **Ch2**: Write report to `tasks/{work_dir}/homeostasis-manage-skill.md`.
- **Ch3** micro-signal to Lead: `PASS|action:{type}|audited:{N}|ref:tasks/{work_dir}/homeostasis-manage-skill.md`.

> Phase-aware routing: read `.claude/resources/phase-aware-execution.md`
> DPS construction: read `.claude/resources/dps-construction-guide.md`

## Failure Handling

| Failure Type | Action | Escalation |
|-------------|--------|------------|
| Skill file parse error | Report with path. Score as F. Propose fix. | L0 retry parse, L4 if structural |
| Cross-skill ref to non-existent skill | Flag as orphan edge. Suggest correct name or creation. | L1 nudge, L4 if ambiguous |
| L1 over budget (>1024 chars) | CRITICAL flag. Propose trimmed version preserving P0-P5. | L0 auto-trim, L4 if signals sacrificed |

> D12 escalation ladder: read `.claude/resources/failure-escalation-ladder.md`

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
D17 standardized on `tasks/{work_dir}/`. Any remaining `/tmp/pipeline/` references must be flagged for migration.

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

> D17 Note: Two-Channel protocol — Ch2 (file output to tasks/{work_dir}/) + Ch3 (micro-signal to Lead).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

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
- Full report: `~/.claude/tasks/{work_dir}/homeostasis-manage-skill.md`
- PT signal: `metadata.phase_signals.homeostasis: "PASS|audited:{N}|avg:{score}"`
- file-based signal: `"PASS|action:{type}|audited:{N}|ref:tasks/{work_dir}/homeostasis-manage-skill.md"`
