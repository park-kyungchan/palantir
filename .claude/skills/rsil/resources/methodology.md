# RSIL — Detailed Methodology

> On-demand reference. Contains cycle execution templates, improvement tracking format, claim flow details (Producer→Tagger→Verifier→Codifier), and retroactive audit procedures. Load when executing Steps 1-6 of the RSIL loop.

---

## Step 1: Detect — Detail

Merge signals from three homeostasis sources into a unified bottleneck list.

### 1a. Self-Diagnose Findings
- Invoke `/self-diagnose` with focus-area if provided
- Receive: categorized findings (10 categories), severity counts, file:line evidence
- Extract: bottleneck candidates from HIGH/CRITICAL findings

### 1b. Manage-Infra Health
- Invoke `/manage-infra` for current health score
- Receive: health score %, drift count, orphan count, per-component scores
- Extract: degraded components (score < 3), cross-component drift items

### 1c. Manage-Codebase Dependencies
- Invoke `/manage-codebase` for dependency map staleness
- Receive: entries count, staleness metrics, hotspot scores
- Extract: stale entries, high-hotspot files (potential fragility indicators)

### 1d. Ad-Hoc Signals
- User-reported issues (from `$ARGUMENTS` or conversation context)
- Pipeline failures (from PT metadata if available)
- Tool availability gaps observed during recent executions
- File I/O bottlenecks (redundant reads, slow scans, cache misses)

**Output format** — Unified bottleneck list with:
- Source: `self-diagnose | manage-infra | manage-codebase | ad-hoc`
- Category: `field-compliance | routing | budget | hooks | drift | dependency | file-io | etc.`
- Severity: `CRITICAL | HIGH | MEDIUM | LOW`
- Evidence: `file:line` or metric value

---

## Step 2: Research — Detail

For each bottleneck category, search for community solutions and best practices.

### 2a. External Research
- Spawn researcher agent for WebSearch/tavily queries
- Focus: CC community patterns, Claude Code best practices, agent coordination patterns
- Time filter: Latest CC version patterns (Feb 2025+)
- Query examples: "Claude Code skill description optimization", "agent teams file coordination patterns"

### 2b. Codebase Analysis
- Spawn analyst agent for local pattern inventory
- Scan `.claude/` for existing patterns that work well (positive exemplars)
- Identify anti-patterns: skills with low utilization, agents with tool mismatches
- Cross-reference with codebase-map hotspots for fragility patterns

### 2c. CC-Native Claim Handling (Meta-Cognition Gate)
- Any CC-native behavioral claims discovered during research: tag as `[CC-CLAIM]`
- Route tagged claims to `/research-cc-verify` before incorporating into improvement plan
- DO NOT apply unverified CC-native claims — this is the Meta-Cognition Protocol gate

**Claim Flow**: Producer (`research-codebase`/`research-external`, `claude-code-guide`) → Tagger (`[CC-CLAIM]`) → Verifier (`research-cc-verify`) → Codifier (`execution-infra`).

**Retroactive Audit**: `self-diagnose` Category 10 detects unverified claims in the ref cache.

**Parallel execution** (COMPLEX tier): spawn researcher + analyst concurrently for 2a and 2b.

**Output format** — Pattern candidates per bottleneck:
- Pattern name and description
- Source: `community | local | documentation`
- Applicability score (1-5 based on relevance to our INFRA)
- CC-native claims flagged for verification

---

## Step 3: Curate — Detail

Consolidate patterns from all research sources into a prioritized improvement plan.

### 3a. Pattern Scoring
For each candidate pattern, compute priority score:
```
priority = (impact × 3 + feasibility × 2) / (effort × 1)
```
- **Impact** (1-5): How much does this improve health score or resolve bottlenecks?
- **Feasibility** (1-5): Can this be implemented with current tools and constraints?
- **Effort** (1-5): How many files/agents/steps are required?

### 3b. Cross-Impact Analysis
- Identify synergies: patterns that amplify each other (group together)
- Identify conflicts: patterns that contradict each other (choose one)
- Identify dependencies: patterns that require others first (sequence accordingly)

### 3c. Wave Grouping
Group patterns into implementation waves:
- **Wave 1**: CRITICAL severity patterns + zero-dependency quick wins
- **Wave 2**: HIGH severity patterns + patterns dependent on Wave 1
- **Wave 3**: MEDIUM/LOW improvements + optional enhancements
- Each wave: max 2 parallel infra-implementers on non-overlapping files

**Output format** — Prioritized improvement plan:
- Ordered pattern list with priority scores
- Wave assignments with dependency rationale
- Estimated file change manifest per wave
- Deferred items with rationale (if any patterns rejected)

---

## Step 4: Apply — Detail

Route prioritized patterns to self-implement for execution.

### 4a. Delegation to Self-Implement
- Invoke `/self-implement` with curated findings formatted as self-diagnose-compatible input
- self-implement spawns infra-implementers in waves (max 2 parallel, non-overlapping files)
- Max 3 iterations for convergence per wave

### 4b. Implementation Monitoring
- Track wave completion via SendMessage from self-implement
- If a wave fails: self-implement handles retry (max 1 retry per wave)
- If non-convergence after 3 iterations: accept partial, record deferred items

**Output format** — Implementation manifest:
- Files changed per wave
- Findings fixed vs deferred
- Iteration count and convergence status

---

## Step 5: Verify — Detail

Validate that improvements actually improved system health.

### 5a. Health Re-measurement
- Re-invoke `/manage-infra` for post-implementation health score
- Compare: health_before vs health_after
- Calculate: health delta (positive = improvement, negative = regression)

### 5b. Structural Verification
- If structural changes were made (new skills, modified agents): invoke verify domain stages
- Check for regression: new orphans, broken relationships, drift introduced by changes
- Cross-reference codebase-map for new broken dependencies

### 5c. Regression Detection
- If `health_after < health_before`: HALT. Report regression details for manual review.
- If `health_after == health_before`: Improvements may be non-measurable. Report details.
- If `health_after > health_before`: SUCCESS. Record improvement delta.

**Output format** — Verification verdict:
- Status: `PASS (improved) | PARTIAL (some improved, some neutral) | FAIL (regression)`
- Health delta: numeric difference
- New issues introduced (if any)
- Files requiring manual review (if regression detected)

---

## Step 6: Track — Detail

Record RSIL cycle results for cross-session continuity.

### 6a. PT Metadata Update
- If PT exists: update `metadata.iterations.rsil: N` with current cycle count (D15 canonical field)
- Record cycle results in `metadata.phase_signals.homeostasis`:
  `"{STATUS}|health_delta:{N}|patterns:{N}|ref:tasks/{team}/homeostasis-rsil.md"`
- Record: health delta, patterns applied, patterns deferred, focus-area, trigger source

### 6b. MEMORY.md Update
- Update MEMORY.md INFRA State section with new health score
- Record significant insights (patterns that worked, anti-patterns confirmed)
- Keep concise — MEMORY.md has 200-line budget (BUG-005: 2x token injection)

### 6c. Backlog Documentation
- Deferred patterns: record in MEMORY.md with severity and rationale
- Next cycle recommendations: prioritized list for future RSIL invocation
- Known gaps: areas where research found no suitable patterns

**Output format** — RSIL cycle report:
- Cycle summary (1-paragraph narrative)
- Metrics: health_before, health_after, delta, patterns_applied, patterns_deferred
- Next cycle recommendations

---

## Iteration Tracking (D15)

- Lead manages `metadata.iterations.rsil: N` in PT before each RSIL invocation
- Iteration 1-2: strict mode (FAIL in Step 5 → halt cycle, manual review required)
- Iteration 3: relaxed mode (proceed with documented gaps, flag in phase_signals)
- Max iterations: 3 per pipeline session. On exceed: auto-PASS with deferred backlog documented.

---

## Failure Detail Table

| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| self-diagnose unavailable | CRITICAL | Abort | Yes | Cannot detect without diagnosis. Report `status: blocked`. |
| Research timeout | MEDIUM | Continue | No | Proceed with available data, note research gaps in report. |
| self-implement non-convergence | HIGH | Partial | No | Accept partial improvements, defer remaining to next cycle. |
| Health regression (Step 5) | CRITICAL | Halt | Yes | Stop cycle. Report regression for manual review. Do not proceed to Step 6. |
| manage-infra unavailable | MEDIUM | Continue | No | Skip health scoring, rely on self-diagnose findings only. |
| PT not found (tracking) | LOW | Continue | No | Write cycle results to MEMORY.md only, skip PT update. |
