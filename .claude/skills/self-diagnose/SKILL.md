---
name: self-diagnose
description: |
  [Homeostasis·SelfDiagnose·Research] INFRA health diagnosis via CC native state research. Reads cc-reference cache, scans .claude/ files for deficiencies (field compliance, routing, budget, hooks), produces categorized findings by severity.

  WHEN: User invokes for INFRA health audit. After CC updates or before releases. Diagnosis only — does NOT implement fixes.
  DOMAIN: Homeostasis (cross-cutting, self-improvement diagnosis). Paired with self-implement.
  INPUT_FROM: User invocation, manage-infra (health findings suggesting deeper analysis).
  OUTPUT_TO: self-implement (findings list for fix implementation).

  METHODOLOGY: (1) Read cc-reference cache (4 files), (2) Scan .claude/ files against 8-category diagnostic checklist, (3) Spawn analyst for parallel category scanning, (4) Categorize findings by severity (CRITICAL→LOW), (5) Produce sorted findings list with file:line evidence.
  OUTPUT_FORMAT: L1 YAML findings list with severity counts, L2 markdown diagnostic report with evidence.
user-invocable: true
disable-model-invocation: false
argument-hint: "[focus-area]"
---

# Self-Diagnose — INFRA Health Research

## Execution Model
- **TRIVIAL**: Lead-direct. Quick scan of 1-2 specific categories for a focused area.
- **STANDARD**: Spawn 1 analyst. Full diagnostic checklist across all .claude/ files. Standard invocation.
- **COMPLEX**: Spawn 2 analysts in parallel (field compliance + routing in one, budget + hooks in another). For comprehensive audits.

## Phase-Aware Execution
- **Standalone / P0-P1**: Spawn agent with `run_in_background`. Lead reads TaskOutput directly.
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers result via SendMessage micro-signal per conventions.md protocol.

## Decision Points

### CC Reference Cache vs Live Research
- **Use cache only**: cc-reference files exist and were updated within the last RSI cycle. No focus-area requiring new CC features. Skip claude-code-guide spawn entirely (saves budget).
- **Delta research**: Cache exists but user-specified focus-area targets features not covered in cache. Spawn claude-code-guide with narrow query for delta only, merge into cache.
- **Full research**: No cc-reference cache exists, or cache is fundamentally stale. Spawn claude-code-guide for comprehensive feature inventory.

### Claude-code-guide Spawn Decision Tree
```
cc-reference cache exists? (memory/cc-reference/ has 4 files)
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
Read cached reference: `memory/cc-reference/` (4 files: native-fields, context-loading, hook-events, arguments-substitution).
- If reference exists and is recent: use as ground truth (skip claude-code-guide spawn)
- If reference outdated or focus-area requires new info: spawn claude-code-guide for delta only
- Query focus: "What NEW native features exist since last verification date?"
- Include focus-area from user arguments if provided
- Update cc-reference files with any new findings
- Compare against `memory/context-engineering.md` for decision history

### 2. Self-Diagnose INFRA
Scan all `.claude/` files systematically using the diagnostic category checklist. Spawn analyst agents for parallel scanning when the scope is full (no focus-area).

**Diagnostic Category Checklist:**

| Category | Check | Tool | Severity if Failed |
|---|---|---|---|
| Field compliance | Non-native frontmatter fields present | Read + compare to native-fields.md | CRITICAL |
| Routing integrity | `disable-model-invocation: true` on pipeline skills | Grep across skills/ | CRITICAL |
| L1 budget | Total description chars exceed 32000 | Read all descriptions + sum chars | HIGH |
| Hook validity | Shell scripts have correct shebang, exit codes, JSON output | Read each hook script | HIGH |
| Agent memory config | `memory` field is valid enum for each agent | Read agents/*.md frontmatter | MEDIUM |
| Settings permissions | All `allow` entries reference existing tools/skills | Read settings.json, cross-reference | MEDIUM |
| Description utilization | Each description uses >80% of 1024 chars | Read + measure per-skill | LOW |
| Color assignments | All agents have unique `color` fields | Read agents, check duplicates | LOW |

**Procedure:**
- For focused scans: run only matching categories
- For full scans: run all 8 categories
- Each finding includes: ID, category, severity, file path, current value, expected value
- Produce categorized finding list sorted by severity (CRITICAL first)

For STANDARD/COMPLEX tiers, construct the delegation prompt:
- **Context**: All .claude/ file paths. CC native field reference from cache. Diagnostic checklist with 8 categories.
- **Task**: For each category, scan all relevant files. Record findings with file:line evidence. Classify severity per the checklist.
- **Constraints**: Read-only. No modifications. Grep scope limited to .claude/. Exclude agent-memory/ (historical, not active config).
- **Expected Output**: L1 YAML with findings_total, findings_by_severity, findings[]. L2 markdown with per-category analysis.
- **Delivery**: Write full result to `/tmp/pipeline/homeostasis-self-diagnose.md`. Send micro-signal to Lead via SendMessage: `{STATUS}|findings:{N}|ref:/tmp/pipeline/homeostasis-self-diagnose.md`.

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
| manage-skills | Skill inventory compliance issues | L1 YAML: actions[] |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| self-implement | Categorized findings list with severity | Always (Lead decides whether to proceed) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| cc-reference cache unavailable AND claude-code-guide fails | (Abort) | `status: blocked`, reason: no ground truth |
| Analyst maxTurns exhausted | (Partial) | `status: partial`, findings so far with coverage % |

## Failure Handling
| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| cc-reference missing + guide fails | CRITICAL | Abort | Yes | No ground truth. Report `status: blocked`. |
| Analyst maxTurns exhausted | MEDIUM | Partial | No | Report partial findings with coverage %. |
| 0 issues found | INFO | Complete | N/A | INFRA is healthy. `findings_total: 0`. |

## Quality Gate
- CC reference ground truth established (cache or live research)
- All 8 diagnostic categories scanned (or focused subset per arguments)
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
findings_total: 0
findings_by_severity:
  critical: 0
  high: 0
  medium: 0
  low: 0
categories_scanned: 0
categories_total: 8
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
