---
name: rsil
description: >-
  Executes the Recursive Self-Improvement Loop as meta-level homeostasis
  coordinator. Triggered when self-diagnose severity_counts HIGH>=3 OR
  manage-infra health_score<80%, or user-invocable at any time. Detects
  INFRA bottlenecks via self-diagnose and manage-infra health scoring,
  researches community patterns via external search and codebase analysis,
  curates improvements with priority scoring, and routes to self-implement
  for application. Coordinates the full detect-research-curate-apply-
  verify-track cycle. Reads from self-diagnose findings, manage-infra
  health report, and external research outputs. Produces improvement plan
  with prioritized pattern list and implementation sequence for
  self-implement. On FAIL (health regression detected in Step 5), halts
  cycle and Lead applies L4 escalation for manual review. DPS needs
  self-diagnose L1 severity_counts and manage-infra health_score. Exclude
  raw evidence detail and full pipeline state.
user-invocable: true
argument-hint: "[focus-area]"
disable-model-invocation: false
---

# RSIL — Recursive Self-Improvement Loop

## Core Philosophy

RSIL is NOT a one-time pipeline. It is an always-active meta-level self-improvement awareness:
- Every task execution = potential improvement trigger. The skill itself is subject to RSIL — it can improve itself.
- Detects bottlenecks and routes improvements immediately via homeostasis sources (self-diagnose, manage-infra, manage-codebase)
- Persists insights across sessions via PT metadata + MEMORY.md (compaction-safe)
- CC-native claims MUST be verified via `research-cc-verify` before application — inference-only judgment is prohibited

## Execution Model

- **TRIVIAL**: Lead-direct. Invoke self-diagnose only; route to self-implement if findings warrant. No external research. Steps 1 + 4.
- **STANDARD**: Lead + 1-2 agents. Detect + research sequential, curate, apply via self-implement. Steps 1-4-5-6.
- **COMPLEX**: Full team (4+ agents). Parallel detect + research, cross-impact curation, wave-based apply, full verify + track. All 6 steps.

## Phase-Aware Execution

Homeostasis mode — operates outside normal pipeline phases. Can be invoked at any time.
- When invoked DURING an active pipeline: runs as a side-loop without disrupting main flow
- Uses Team infrastructure (P2+ mode) with Two-Channel Protocol (D17)
- **File I/O awareness**: Detect and improve file I/O bottlenecks (slow reads, redundant scans, stale caches)
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.
- For phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Decision Points

### Full Loop vs Partial
- **Detection only** (Step 1): User wants health snapshot. Stop after Step 1, report bottleneck list.
- **Known patterns** (Steps 1, 3-6): Skip Step 2 when patterns are already identified.
- **Full loop** (Steps 1-6): Default for `/rsil` without focus-area.

### Scope Control
User specifies focus via `$ARGUMENTS`:
- `/rsil` — full loop, all categories
- `/rsil hooks` — hook-related bottlenecks only
- `/rsil skills` — skill routing and description quality
- `/rsil agents` — agent configuration and tool profiles
- `/rsil budget` — L1 budget and context engineering
- `/rsil file-io` — file I/O patterns and bottleneck detection

### Auto-Trigger Conditions
- Health score < 85% (from manage-infra)
- 3+ HIGH severity findings in self-diagnose
- Pipeline failure in any phase
- User reports recurring bottleneck or routing failure
- Post-major-pipeline completion (proactive health maintenance)
- ∴ Thinking reveals INFRA structural gap (ALWAYS ACTIVE — any mode, any pipeline, any phase)

### Tier Selection
- **TRIVIAL**: ≤3 findings, all LOW/MEDIUM. No research needed.
- **STANDARD**: 4-8 findings, mixed severities. Some research beneficial.
- **COMPLEX**: 9+ findings OR any CRITICAL finding OR structural changes needed. Full research required.

## Methodology — 6-Step RSIL Loop

> For detailed sub-step procedures, output formats, and scoring formulas: read `resources/methodology.md`

- **Step 1 — Detect**: Merge signals from self-diagnose (10 categories), manage-infra (health score), manage-codebase (dependency map), and ad-hoc user signals into a unified bottleneck list with source, category, severity, and evidence.

> **Lead RECEIVE (Step 1)**: After analyst completes — read task notification summary ONLY (micro-signal). Do NOT call `TaskOutput(block:true)` to pull full analyst output into Lead context. Pass the analyst output file path to downstream implementers via `INPUT_FILES` or `$ARGUMENTS`. The analyst writes findings to a file; Lead passes the file path. This is mandatory — `TaskOutput(block:true)` is the single-session equivalent of the Data Relay Tax anti-pattern.

- **Step 2 — Research**: Spawn researcher (external WebSearch) + analyst (codebase scan) in parallel. Tag all CC-native behavioral claims as `[CC-CLAIM]` → route to `research-cc-verify` before incorporating.

> **Lead RECEIVE (Step 2)**: Same pattern — receive micro-signal from researcher/analyst subagents. Pass file paths. Never embed full outputs in downstream DPS.

- **Step 3 — Curate**: Score patterns by `(impact×3 + feasibility×2) / effort`. Run cross-impact analysis (synergies, conflicts, dependencies). Group into Wave 1 (CRITICAL), Wave 2 (HIGH), Wave 3 (MEDIUM/LOW).
- **Step 4 — Apply**: Delegate curated findings to `/self-implement`. self-implement spawns infra-implementers in waves (max 2 parallel, non-overlapping files). Max 3 convergence iterations per wave.
- **Step 5 — Verify**: Re-invoke manage-infra for health_after. Compare health_before vs health_after. If regression detected → HALT cycle and escalate to L4.
- **Step 6 — Track**: Update PT `metadata.iterations.rsil: N` and `metadata.phase_signals.homeostasis`. Update MEMORY.md with health score and significant insights (within 200-line budget).

## Anti-Patterns

- **DO NOT run RSIL during active pipeline execution** unless explicitly requested. RSIL modifies `.claude/` files that active pipelines may be reading.
- **DO NOT apply unverified CC-native claims.** Route all `[CC-CLAIM]` items through `/research-cc-verify`. Reasoning-only judgment is insufficient — this is the Meta-Cognition Protocol gate.
- **DO NOT remove skills without checking codebase-map dependencies.** A "low-utilization" skill may be a critical dependency for another skill.
- **DO NOT skip Step 5 (Verify).** An improvement that introduces regression is worse than no improvement.
- **DO NOT exceed MEMORY.md budget.** 200-line limit enforced (BUG-005: 2x token injection). Use topic files for detailed analysis.
- **DO NOT stack unverified cycles.** Each cycle must complete Step 5 before starting the next. Stacking compounds regression risk.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (User invocation) | Focus area or general RSIL request | `$ARGUMENTS` text |
| self-diagnose | Findings suggesting systematic improvement needed | L1 YAML: findings[], findings_by_severity |
| manage-infra | Health score below threshold | L1 YAML: health_score, findings[] |
| (Pipeline failure) | Failure context from PT metadata | PT metadata: current_phase, error context |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| self-diagnose | Detection request with optional focus-area | Step 1 (always) |
| manage-infra | Health measurement request | Steps 1 and 5 (before/after) |
| manage-codebase | Dependency staleness check | Step 1 (detect phase) |
| research-cc-verify | CC-native claims from research | Step 2 (when [CC-CLAIM] items found) |
| self-implement | Curated findings for implementation | Step 4 (after curation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Detection finds 0 bottlenecks | (Complete) | `status: complete`, "INFRA healthy, no improvements needed" |
| Research timeout / no patterns | Step 3 (proceed with available data) | Partial pattern list, gaps noted |
| self-implement non-convergence | (Partial) | Deferred items with severity and rationale |
| Health regression in Step 5 | (Halt) | Regression details, manual review required |

## Failure Handling

> For escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

| Failure Type | Level | Action |
|---|---|---|
| Transient tool error during research or health check | L0 Retry | Re-invoke same agent with same DPS |
| Research output incomplete or self-diagnose missing categories | L1 Nudge | Respawn with refined DPS targeting focused query or category list |
| Agent exhausted turns or context polluted mid-cycle | L2 Respawn | Kill → fresh agent with reduced scope DPS |
| self-implement non-convergence or parallel conflict | L3 Restructure | Regroup patterns into smaller non-conflicting waves |
| Health regression after Step 5 or 3+ L2 failures | L4 Escalate | AskUserQuestion with regression details and options |

> For per-failure-type severity, blocking status, and resolution details: read `resources/methodology.md`

## Quality Gate
- All executed steps completed (or intentionally skipped with documented rationale)
- Health score maintained or improved (no regression)
- No HIGH severity regressions introduced
- MEMORY.md updated with cycle results (within 200-line budget)
- Deferred items documented with severity and rationale for next cycle
- CC-native claims verified before application (Meta-Cognition Protocol compliant)

## Output

> D17 Note: Two-Channel protocol — Ch2 (`tasks/{work_dir}/`) + Ch3 (micro-signal to Lead).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

### L1
```yaml
domain: homeostasis
skill: rsil
status: complete|partial|blocked|halted
pt_signal: "metadata.phase_signals.homeostasis"
signal_format: "{STATUS}|health_delta:{N}|patterns:{N}|ref:tasks/{work_dir}/homeostasis-rsil.md"
cycle: 1
trigger: user|auto|pipeline-failure
focus_area: all|hooks|skills|agents|budget|file-io
health_before: 0
health_after: 0
health_delta: 0
bottlenecks_detected: 0
patterns_researched: 0
patterns_applied: 0
patterns_deferred: 0
cc_claims_verified: 0
```

**Channel 2 output file**: Write full L1+L2 result to `tasks/{work_dir}/homeostasis-rsil.md`.

### L2
- Step 1: Bottleneck list with sources, categories, and severities
- Step 2: Pattern candidates per bottleneck with applicability scores
- Step 3: Prioritized improvement plan with wave assignments
- Step 4: Implementation manifest from self-implement
- Step 5: Health delta analysis and regression check
- Step 6: Cross-session persistence updates and next cycle recommendations
- Deferred Backlog: Patterns not applied with rationale and priority for next cycle
