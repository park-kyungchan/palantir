---
name: self-diagnose
description: >-
  Diagnoses INFRA health against CC native state across 10
  categories including unverified CC-native claims detection.
  Reads cc-reference cache and scans .claude/ files.
  Diagnosis only, does not fix. Paired with self-implement. Use
  when user invokes for INFRA health audit, after CC updates, or
  before releases. Reads from cc-reference cache ref_*.md files
  for ground truth and manage-infra health findings. Produces
  findings list with severity counts and diagnostic report with
  file:line evidence for self-implement. On FAIL (scan error or
  cc-reference unavailable), Lead applies L0 retry; 2+ failures
  escalate to L4. DPS needs cc-reference cache ref_*.md files
  and .claude/ file paths. Exclude agent-memory runtime data.
user-invocable: true
disable-model-invocation: false
argument-hint: "[focus-area]"
---

# Self-Diagnose — INFRA Health Research

## Current Metrics
- CLAUDE.md size: !`wc -c < .claude/CLAUDE.md 2>/dev/null || echo "0"` bytes

## Execution Model
- **TRIVIAL**: Lead-direct. Quick scan of 1-2 specific categories for a focused area. No agent spawn.
- **STANDARD**: Spawn 1 analyst (maxTurns:20). Full diagnostic checklist across all .claude/ files.
- **COMPLEX**: Spawn 2 analysts in parallel (maxTurns:15 each). Group A: field compliance + routing + utilization. Group B: budget + hooks + memory + permissions + colors.

## Phase-Aware Execution

Runs outside the linear P0–P8 pipeline (homeostasis domain). Team mode applies when a team is active.
- **Communication**: Four-Channel Protocol (Ch2 disk + Ch3 micro-signal to Lead + Ch4 P2P). Homeostasis reports are terminal — no downstream P2P consumers.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

> For phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Decision Points

### CC Reference Cache vs Live Research
- **Use cache only**: cc-reference files exist and were updated within the last RSI cycle. No focus-area requiring new CC features. Skip claude-code-guide spawn entirely (saves budget).
- **Delta research**: Cache exists but user-specified focus-area targets features not covered in cache. Spawn claude-code-guide with narrow query for delta only, merge into cache.
- **Full research**: No cc-reference cache exists, or cache is fundamentally stale. Spawn claude-code-guide for comprehensive feature inventory.

### Claude-code-guide Spawn Decision Tree
```
cc-reference cache exists? (memory/cc-reference/ has 5 files)
|-- NO --> Spawn claude-code-guide (full research). STOP if unavailable.
+-- YES --> Cache updated within 7 days?
    |-- YES --> Focus-area covered by cache?
    |   |-- YES --> Skip spawn (use cache only). Lowest cost path.
    |   +-- NO --> Spawn claude-code-guide (delta query for focus-area only)
    +-- NO --> CC version changed since cache?
        |-- YES --> Spawn claude-code-guide (full research, cache is stale)
        +-- NO --> Use cache (likely still valid, CC versions are stable)
```

### Diagnosis Scope
- **Focused**: User provides `[focus-area]` argument (e.g., "hooks", "agent-fields"). Scan only matching categories.
- **Full scan**: No focus-area specified. Diagnose all .claude/ files: agents, skills, hooks, settings, CLAUDE.md.

## Methodology

### 1. Research CC Native State
Read cached reference: `memory/cc-reference/` (5 files: native-fields, context-loading, hook-events, arguments-substitution, skill-disambiguation).
- Cache recent → use as ground truth; skip claude-code-guide spawn.
- Cache outdated or focus-area requires new info → spawn claude-code-guide for delta only.
- Include focus-area from `$ARGUMENTS` if provided. Update cache with new findings.
- Compare against `memory/context-engineering.md` for decision history.

### 2. Self-Diagnose INFRA
Scan all `.claude/` files using the diagnostic category checklist below. Spawn analyst agents for parallel scanning when the scope is full.

**Diagnostic Category Checklist:**

| Category | Check | Tool | Severity if Failed |
|---|---|---|---|
| Field compliance | Non-native frontmatter fields present | Read + compare to native-fields.md | CRITICAL |
| Routing integrity | `disable-model-invocation: false` on pipeline skills | Grep across skills/ | CRITICAL |
| L1 budget | Total description chars exceed 32000 | Read all descriptions + sum chars | HIGH |
| Hook validity | Shell scripts have correct shebang, exit codes, JSON output | Read each hook script | HIGH |
| Agent memory config | `memory` field is valid enum for each agent | Read agents/*.md frontmatter | MEDIUM |
| Settings permissions | All `allow` entries reference existing tools/skills | Read settings.json, cross-reference | MEDIUM |
| Description utilization | Each description uses >80% of 1024 chars | Read + measure per-skill | LOW |
| Color assignments | All agents have unique `color` fields | Read agents, check duplicates | LOW |
| Constraint-implication | CC native constraint has unaddressed design implication in current INFRA | Read ref_*.md constraints → trace implication → verify INFRA compliance | HIGH |
| Unverified CC claims | ref_*.md behavioral claims lack empirical file:line evidence | Read ref_*.md + classify claims by evidence presence | HIGH |

> For Category 9 constraint-implication detail table and Category 10 unverified-claim detection tables: read `resources/methodology.md`

**Procedure:**
- For focused scans: run only matching categories.
- For full scans: run all 10 categories.
- Each finding includes: ID, category, severity, file path, current value, expected value.
- Produce categorized finding list sorted by severity (CRITICAL first).

> For DPS delegation template (Context INCLUDE/EXCLUDE/Budget, Task, Constraints, Output, Delivery): read `resources/methodology.md`

## Anti-Patterns

### DO NOT: Skip Diagnosis and Assume Issues
Never apply fixes based on assumptions or memory of past issues. INFRA state changes between cycles.

### DO NOT: Spawn claude-code-guide When Cache Is Sufficient
Each claude-code-guide spawn consumes significant context budget. Use cache when available.

### DO NOT: Scan Files Outside .claude/ Directory
Self-diagnose scope is strictly .claude/ infrastructure.

### DO NOT: Modify Any Files
This skill is read-only diagnosis. All modifications go through self-implement.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (User invocation) | Focus area or general diagnosis request | `$ARGUMENTS` text |
| manage-infra | Health check findings suggesting deeper analysis | L1 YAML: health_score, findings[] |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| self-implement | Categorized findings list with severity | Always (Lead decides whether to proceed) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| cc-reference cache unavailable AND claude-code-guide fails | (Abort) | `status: blocked`, reason: no ground truth |
| Analyst maxTurns exhausted | (Partial) | `status: partial`, findings so far with coverage % |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Failure Handling

### D12 Escalation Ladder

| Failure Type | Level | Action |
|---|---|---|
| File read error, tool timeout on specific files | L0 Retry | Re-invoke same analyst with same DPS |
| Analyst output missing specific diagnostic categories | L1 Nudge | SendMessage with category-specific scan instructions |
| Analyst maxTurns exhausted or context polluted | L2 Respawn | Kill → fresh analyst with focused scan scope |
| cc-reference cache corrupted and claude-code-guide fails | L3 Restructure | Rebuild cache from scratch, re-scope diagnosis |
| 3+ L2 failures or no ground truth source available | L4 Escalate | AskUserQuestion with situation summary and options |

## Quality Gate
- CC reference ground truth established (cache or live research)
- All 10 diagnostic categories scanned (or focused subset per arguments)
- Each finding has: ID, category, severity, file path, evidence
- Findings sorted by severity (CRITICAL → LOW)
- No false positives (each finding verified with file:line evidence)

## Output

### L1
```yaml
domain: homeostasis
skill: self-diagnose
status: complete|partial|blocked
cc_reference_source: cache|delta|full|none
pt_signal: "metadata.phase_signals.homeostasis"
signal_format: "{STATUS}|findings:{N}|severity_high:{N}|ref:tasks/{team}/homeostasis-self-diagnose.md"
findings_total: 0
findings_by_severity:
  critical: 0
  high: 0
  medium: 0
  low: 0
categories_scanned: 0
categories_total: 10
findings:
  - id: ""
    category: ""
    severity: CRITICAL|HIGH|MEDIUM|LOW
    file: ""
    current_value: ""
    expected_value: ""
```

### L2
- **CC Research Summary**: Reference source and any new findings
- **Diagnosis Report**: Per-category findings table with evidence
- **Coverage**: Categories scanned, files analyzed, scan completeness
- **Recommendations**: Priority-ordered list for self-implement
  - **Constraint-Implication Gaps**: Design implications of CC native constraints not addressed in current INFRA
