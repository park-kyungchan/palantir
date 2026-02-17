---
name: self-diagnose
description: >-
  Diagnoses INFRA health against CC native state across 10
  categories including unverified CC-native claims detection. Reads cc-reference cache and scans .claude/ files.
  Diagnosis only, does not fix. Paired with self-implement. Use
  when user invokes for INFRA health audit, after CC updates, or
  before releases. Reads from cc-reference cache ref_*.md files
  for ground truth and manage-infra health findings. Produces
  findings list with severity counts and diagnostic report with
  file:line evidence for self-implement.
user-invocable: true
disable-model-invocation: false
argument-hint: "[focus-area]"
allowed-tools: "Read Glob Grep Write"
metadata:
  category: homeostasis
  tags: [cc-native-diagnosis, infra-health-audit, 10-category-scan]
  version: 2.0.0
---

# Self-Diagnose — INFRA Health Research

## Execution Model
- **TRIVIAL**: Lead-direct. Quick scan of 1-2 specific categories for a focused area. No agent spawn.
- **STANDARD**: Spawn 1 analyst (maxTurns:20). Full diagnostic checklist across all .claude/ files.
- **COMPLEX**: Spawn 2 analysts in parallel (maxTurns:15 each). Group A: field compliance + routing + utilization. Group B: budget + hooks + memory + permissions + colors.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

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
| Constraint-implication | CC native constraint has unaddressed design implication in current INFRA | Read ref_*.md constraints → trace implication → verify INFRA compliance | HIGH |
| Unverified CC claims | ref_*.md behavioral claims lack empirical file:line evidence | Read ref_*.md + classify claims by evidence presence | HIGH |

**Category 9: Constraint-Implication Alignment**

Traces each CC native constraint to its design implications and verifies current INFRA respects them:

| CC Native Constraint | Design Implication | Verification Check |
|---------------------|-------------------|-------------------|
| No shared memory between agents | Information must be explicitly communicated; external file refs are phantom dependencies | Verify no skill/agent assumes implicit context sharing. Check all cross-agent data has explicit delivery mechanism (DPS inline, SendMessage, or disk+path). |
| Agent ≠ skill context | Agent does not see skill L2 body; DPS must fully convey execution instructions | Verify DPS templates include all execution-critical info from skill L2 (Phase-Aware, error handling, output format). |
| Lead compaction risk | Inter-phase routing state may be lost during auto-compaction | Verify PT metadata captures enough state for phase resumption. Check pipeline-resume can reconstruct from PT alone. |
| SendMessage = text only | Cannot inject structured data into agent context; summary must be self-contained | Verify micro-signal formats contain enough context for Lead routing decisions without loading full disk output. |
| Inbox = poll per API turn | No real-time coordination; teammate sees messages only on next turn | Verify no skill assumes synchronous teammate response. Check all coordination is async-compatible. |
| Subagent 30K char limit | Background agent output truncated beyond 30K chars | Verify agents prioritize critical info first in output. Check large outputs use disk+path pattern. |

For each row: Read the relevant ref_*.md for the constraint, then Grep/Read INFRA files to verify the check. Flag violations as HIGH severity.

**Category 10: Unverified CC-Native Claims in Ref Cache**

Detects behavioral claims in ref_*.md files that were codified without empirical verification:

| Check | Method | What It Detects |
|-------|--------|-----------------|
| Behavioral verb scan | Grep ref_*.md for "persist", "survive", "trigger", "inject", "deliver", "auto-", "ephemeral", "transient" | Claims about CC runtime behavior |
| Evidence presence | For each claim: check for file:line evidence or "Verified:" annotation | Unverified assertions presented as facts |
| Cross-reference | Compare claim against actual filesystem state | Claims contradicted by current system state |

For each unverified claim found: flag as HIGH severity with the claim text, source file:line, and suggested verification method (Glob/Read test to run via research-cc-verify).

**Origin**: SendMessage "ephemeral" error (2026-02-17). Lead's reasoning-only judgment produced incorrect CC-native claim → propagated to 4 ref files before user caught it. Cost: full correction cycle. Prevention: this category + research-cc-verify Shift-Left gate.

**Procedure:**
- For focused scans: run only matching categories
- For full scans: run all 10 categories
- Each finding includes: ID, category, severity, file path, current value, expected value
- Produce categorized finding list sorted by severity (CRITICAL first)

For STANDARD/COMPLEX tiers, construct the delegation prompt:
- **Context**: All .claude/ file paths. CC native field reference from cache. Diagnostic checklist with 10 categories.
- **Task**: For each category, scan all relevant files. Record findings with file:line evidence. Classify severity per the checklist.
- **Constraints**: Read-only analyst agent. No modifications. Grep scope limited to .claude/. Exclude agent-memory/ (historical, not active config). maxTurns:20.
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
