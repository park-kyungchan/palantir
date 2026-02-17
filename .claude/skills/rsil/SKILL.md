---
name: rsil
description: >-
  Executes the Recursive Self-Improvement Loop as meta-level homeostasis
  coordinator. Detects INFRA bottlenecks via self-diagnose and manage-infra
  health scoring, researches community patterns via external search and
  codebase analysis, curates improvements with priority scoring, and routes
  to self-implement for application. Coordinates the full detect-research-
  curate-apply-verify-track cycle. User-invocable at any time or triggered
  when bottlenecks detected during pipeline execution. Reads from
  self-diagnose findings, manage-infra health report, and external research
  outputs. Produces improvement plan with prioritized pattern list and
  implementation sequence for self-implement execution.
user-invocable: true
argument-hint: "[focus-area]"
disable-model-invocation: false
allowed-tools: "Task"
metadata:
  category: homeostasis
  tags: [rsil, self-improvement, meta-level, homeostasis, continuous-improvement]
  version: 1.0.0
---

# RSIL — Recursive Self-Improvement Loop

## Core Philosophy

RSIL is NOT a one-time pipeline. It is an always-active meta-level self-improvement awareness:
- Every task execution = potential improvement trigger
- Actively leverages CC Agent Teams file I/O system (Task JSON + Inbox JSON)
- Detects bottlenecks and routes improvements immediately
- Skill lifecycle is unlimited -- add freely, remove/consolidate bottleneck skills
- Persists insights across sessions via PT metadata + MEMORY.md
- The skill itself is subject to RSIL -- it can improve itself

## Execution Model
- **TRIVIAL**: Lead-direct quick scan. Invoke self-diagnose findings only, route to self-implement if findings warrant. No external research. 1-2 steps of the loop.
- **STANDARD**: Lead with 1-2 agents. Detect + research phase (sequential), curate, apply via self-implement. 4-5 steps of the loop.
- **COMPLEX**: Full team (4+ agents). Detect + research (parallel agents), curate with cross-impact analysis, apply in waves via self-implement, full verify + track. All 6 steps.

## Phase-Aware Execution

This skill runs in homeostasis mode (outside normal pipeline tiers):
- Can be invoked at any time -- not tied to specific pipeline phase
- When invoked DURING a pipeline, runs as a side-loop without disrupting main flow
- Uses Team infrastructure (P2+ mode): SendMessage for coordination, TaskUpdate for tracking
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.
- **File I/O awareness**: CC Agent Teams = file-based system. This skill should detect and improve file I/O bottlenecks (slow reads, redundant scans, stale caches).

## Decision Points

### Full Loop vs Partial
- **Detection only** (Steps 1): User wants health snapshot. Stop after Step 1, report bottleneck list.
- **Known patterns** (Steps 1, 3-6): Skip Step 2 when patterns are already identified. Proceed directly from detection to curation.
- **Full loop** (Steps 1-6): Default for `/rsil` without focus-area. Complete detect-research-curate-apply-verify-track cycle.

### Scope Control
User can specify focus area via `$ARGUMENTS`:
- `/rsil` -- full loop, all categories
- `/rsil hooks` -- focus on hook-related bottlenecks only
- `/rsil skills` -- focus on skill routing and description quality
- `/rsil agents` -- focus on agent configuration and tool profiles
- `/rsil budget` -- focus on L1 budget and context engineering
- `/rsil file-io` -- focus on file I/O patterns and bottleneck detection

### Auto-Trigger Conditions
RSIL should be considered when any of these conditions are met:
- Health score < 85% (from manage-infra)
- 3+ HIGH severity findings in self-diagnose
- Pipeline failure in any phase
- User reports recurring bottleneck or routing failure
- Post-major-pipeline completion (proactive health maintenance)

### Tier Selection
- **TRIVIAL**: ≤3 findings from self-diagnose, all LOW/MEDIUM. No research needed.
- **STANDARD**: 4-8 findings, mix of severities. Some research beneficial.
- **COMPLEX**: 9+ findings OR any CRITICAL finding OR structural changes needed. Full research required.

## Methodology — 6-Step RSIL Loop

### Step 1: Detect (Bottleneck Discovery)

Merge signals from three homeostasis sources into a unified bottleneck list:

**1a. Self-Diagnose Findings**
- Invoke `/self-diagnose` with focus-area if provided
- Receive: categorized findings (10 categories), severity counts, file:line evidence
- Extract: bottleneck candidates from HIGH/CRITICAL findings

**1b. Manage-Infra Health**
- Invoke `/manage-infra` for current health score
- Receive: health score %, drift count, orphan count, per-component scores
- Extract: degraded components (score < 3), cross-component drift items

**1c. Manage-Codebase Dependencies**
- Invoke `/manage-codebase` for dependency map staleness
- Receive: entries count, staleness metrics, hotspot scores
- Extract: stale entries, high-hotspot files (potential fragility indicators)

**1d. Ad-Hoc Signals**
- User-reported issues (from `$ARGUMENTS` or conversation context)
- Pipeline failures (from PT metadata if available)
- Tool availability gaps observed during recent executions
- File I/O bottlenecks (redundant reads, slow scans, cache misses)

**Output**: Unified bottleneck list with:
- Source (self-diagnose | manage-infra | manage-codebase | ad-hoc)
- Category (field-compliance | routing | budget | hooks | drift | dependency | file-io | etc.)
- Severity (CRITICAL | HIGH | MEDIUM | LOW)
- Evidence (file:line or metric value)

### Step 2: Research (Pattern Discovery)

For each bottleneck category, search for community solutions and best practices:

**2a. External Research**
- Spawn researcher agent for WebSearch/tavily queries
- Focus: CC community patterns, Claude Code best practices, agent coordination patterns
- Time filter: Latest CC version patterns (Feb 2025+)
- Query examples: "Claude Code skill description optimization", "agent teams file coordination patterns"

**2b. Codebase Analysis**
- Spawn analyst agent for local pattern inventory
- Scan .claude/ for existing patterns that work well (positive exemplars)
- Identify anti-patterns: skills with low utilization, agents with tool mismatches
- Cross-reference with codebase-map hotspots for fragility patterns

**2c. CC-Native Claim Handling**
- Any CC-native behavioral claims discovered during research: tag as `[CC-CLAIM]`
- Route tagged claims to `/research-cc-verify` before incorporating into improvement plan
- DO NOT apply unverified CC-native claims -- this is the Meta-Cognition Protocol gate

**Parallel execution** (COMPLEX tier): spawn researcher + analyst concurrently for 2a and 2b.

**Output**: Pattern candidates per bottleneck:
- Pattern name and description
- Source (community | local | documentation)
- Applicability score (1-5 based on relevance to our INFRA)
- CC-native claims flagged for verification

### Step 3: Curate (Prioritization)

Consolidate patterns from all research sources into a prioritized improvement plan:

**3a. Pattern Scoring**
For each candidate pattern, compute priority score:
```
priority = (impact × 3 + feasibility × 2) / (effort × 1)
```
- **Impact** (1-5): How much does this improve health score or resolve bottlenecks?
- **Feasibility** (1-5): Can this be implemented with current tools and constraints?
- **Effort** (1-5): How many files/agents/steps are required?

**3b. Cross-Impact Analysis**
- Identify synergies: patterns that amplify each other (group together)
- Identify conflicts: patterns that contradict each other (choose one)
- Identify dependencies: patterns that require others first (sequence accordingly)

**3c. Wave Grouping**
Group patterns into implementation waves:
- **Wave 1**: CRITICAL severity patterns + zero-dependency quick wins
- **Wave 2**: HIGH severity patterns + patterns dependent on Wave 1
- **Wave 3**: MEDIUM/LOW improvements + optional enhancements
- Each wave: max 2 parallel infra-implementers on non-overlapping files

**Output**: Prioritized improvement plan:
- Ordered pattern list with priority scores
- Wave assignments with dependency rationale
- Estimated file change manifest per wave
- Deferred items with rationale (if any patterns rejected)

### Step 4: Apply (Implementation)

Route prioritized patterns to self-implement for execution:

**4a. Delegation to Self-Implement**
- Invoke `/self-implement` with curated findings formatted as self-diagnose-compatible input
- self-implement spawns infra-implementers in waves (max 2 parallel, non-overlapping files)
- Max 3 iterations for convergence per wave

**4b. Implementation Monitoring**
- Track wave completion via SendMessage from self-implement
- If a wave fails: self-implement handles retry (max 1 retry per wave)
- If non-convergence after 3 iterations: accept partial, record deferred items

**Output**: Implementation manifest:
- Files changed per wave
- Findings fixed vs deferred
- Iteration count and convergence status

### Step 5: Verify (Health Re-check)

Validate that improvements actually improved system health:

**5a. Health Re-measurement**
- Re-invoke `/manage-infra` for post-implementation health score
- Compare: health_before vs health_after
- Calculate: health delta (positive = improvement, negative = regression)

**5b. Structural Verification**
- If structural changes were made (new skills, modified agents): invoke verify domain stages
- Check for regression: new orphans, broken relationships, drift introduced by changes
- Cross-reference codebase-map for new broken dependencies

**5c. Regression Detection**
- If health_after < health_before: HALT. Report regression details for manual review.
- If health_after == health_before: Improvements may be non-measurable. Report details.
- If health_after > health_before: SUCCESS. Record improvement delta.

**Output**: Verification verdict:
- Status: PASS (improved) | PARTIAL (some improved, some neutral) | FAIL (regression)
- Health delta: numeric difference
- New issues introduced (if any)
- Files requiring manual review (if regression detected)

### Step 6: Track (Cross-Session Persistence)

Record RSIL cycle results for cross-session continuity:

**6a. PT Metadata Update**
- If PT exists: update `metadata.rsil_cycles` with cycle results
- Record: cycle number, health delta, patterns applied, patterns deferred
- Record: timestamp, focus-area, trigger source

**6b. MEMORY.md Update**
- Update MEMORY.md INFRA State section with new health score
- Record significant insights (patterns that worked, anti-patterns confirmed)
- Keep concise -- MEMORY.md has 200-line budget (BUG-005: 2x token injection)

**6c. Backlog Documentation**
- Deferred patterns: record in MEMORY.md with severity and rationale
- Next cycle recommendations: prioritized list for future RSIL invocation
- Known gaps: areas where research found no suitable patterns

**Output**: RSIL cycle report:
- Cycle summary (1-paragraph narrative)
- Metrics: health_before, health_after, delta, patterns_applied, patterns_deferred
- Next cycle recommendations

## Anti-Patterns

### DO NOT: Run RSIL During Active Pipeline Execution
Unless explicitly requested by user. RSIL modifies .claude/ files that active pipelines may be reading. Wait for pipeline completion or run as explicitly requested side-loop.

### DO NOT: Apply Unverified CC-Native Claims
Route all CC-native behavioral claims through `/research-cc-verify` before incorporating into improvement plan. This is the Meta-Cognition Protocol gate. Reasoning-only judgment is insufficient.

### DO NOT: Remove Skills Without Checking Codebase-Map Dependencies
Before removing or consolidating any skill, check codebase-map for reference chains. A "low-utilization" skill may be a critical dependency for another skill.

### DO NOT: Skip Verification Step
Always compare health before/after. An improvement that introduces regression is worse than no improvement. Measure twice, cut once.

### DO NOT: Exceed MEMORY.md Budget
MEMORY.md has a 200-line limit (BUG-005: 2x token injection). Keep cycle records concise. Use topic files for detailed analysis.

### DO NOT: Run Multiple RSIL Cycles Without Verification
Each cycle must complete Step 5 (Verify) before starting the next cycle. Stacking unverified changes compounds regression risk.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (User invocation) | Focus area or general RSIL request | `$ARGUMENTS` text |
| self-diagnose | Findings suggesting systematic improvement needed | L1 YAML: findings[], findings_by_severity |
| manage-infra | Health score below threshold triggering improvement | L1 YAML: health_score, findings[] |
| (Pipeline failure) | Failure context from PT metadata | PT metadata: current_phase, error context |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| self-diagnose | Detection request with optional focus-area | Step 1 (always) |
| manage-infra | Health measurement request | Steps 1 and 5 (before/after) |
| manage-codebase | Dependency staleness check | Step 1 (detect phase) |
| research-cc-verify | CC-native claims from research | Step 2 (when [CC-CLAIM] tagged items found) |
| self-implement | Curated findings for implementation | Step 4 (after curation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Detection finds 0 bottlenecks | (Complete) | `status: complete`, message: "INFRA healthy, no improvements needed" |
| Research timeout / no patterns found | Step 3 (proceed with available data) | Partial pattern list, gaps noted |
| self-implement failure (non-convergence) | (Partial) | Deferred items with severity and rationale |
| Health regression detected in Step 5 | (Halt) | Regression details, manual review required |

## Failure Handling
| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| self-diagnose unavailable | CRITICAL | Abort | Yes | Cannot detect without diagnosis. Report `status: blocked`. |
| Research timeout | MEDIUM | Continue | No | Proceed with available data, note research gaps in report. |
| self-implement non-convergence | HIGH | Partial | No | Accept partial improvements, defer remaining to next cycle. |
| Health regression (Step 5) | CRITICAL | Halt | Yes | Stop cycle. Report regression for manual review. Do not proceed to Step 6. |
| manage-infra unavailable | MEDIUM | Continue | No | Skip health scoring, rely on self-diagnose findings only. |
| PT not found (tracking) | LOW | Continue | No | Write cycle results to MEMORY.md only, skip PT update. |

## Quality Gate
- All executed steps completed (or intentionally skipped with documented rationale)
- Health score maintained or improved (no regression)
- No HIGH severity regressions introduced
- MEMORY.md updated with cycle results (within 200-line budget)
- Deferred items documented with severity and rationale for next cycle
- CC-native claims verified before application (Meta-Cognition Protocol compliant)

## Output

### L1
```yaml
domain: homeostasis
skill: rsil
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
status: complete|partial|blocked|halted
```

### L2
- **Step 1 Results**: Bottleneck list with sources, categories, and severities
- **Step 2 Results**: Pattern candidates per bottleneck with applicability scores
- **Step 3 Results**: Prioritized improvement plan with wave assignments
- **Step 4 Results**: Implementation manifest from self-implement
- **Step 5 Results**: Health delta analysis and regression check
- **Step 6 Results**: Cross-session persistence updates and next cycle recommendations
- **Deferred Backlog**: Patterns not applied with rationale and recommended priority for next cycle
