---
name: orchestrate-relational
description: |
  [P5·Orchestration·HOW] Specifies DPS contracts per producer-consumer handoff with path, format, and validation rules.

  WHEN: After plan-verify-coordinator complete (all PASS). Wave 5 parallel with orchestrate-static/behavioral/impact.
  DOMAIN: orchestration (skill 3 of 5). Parallel: static ∥ behavioral ∥ relational ∥ impact -> coordinator.
  INPUT_FROM: plan-verify-coordinator (verified plan L3 via $ARGUMENTS).
  OUTPUT_TO: orchestrate-coordinator (DPS handoff specs with chain completeness verdict).

  METHODOLOGY: (1) Read pv-coordinator L3 task list and dependency graph, (2) Identify all producer-consumer data dependencies, (3) Define DPS per handoff: file path, format (YAML/JSON/md), required fields, validation rules, (4) Validate chain completeness: no dangling inputs, no circular chains, (5) Output DPS specification with path registry and chain_complete flag.
  OUTPUT_FORMAT: L1 YAML DPS specs with chain_complete flag, L2 data flow chain with gap report.
user-invocable: false
disable-model-invocation: false
---

# Orchestrate — Relational (HOW)

## Execution Model
- **TRIVIAL**: Skip (orchestration simplified for trivial tiers).
- **STANDARD**: Spawn 1 analyst. Systematic handoff identification and DPS definition.
- **COMPLEX**: Spawn 1 analyst with maxTurns:25. Deep handoff analysis with validation rules and chain completeness proofs.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn analyst with `team_name` parameter. Agent delivers result via SendMessage micro-signal per conventions.md protocol.
- **Delivery**: Write full result to `/tmp/pipeline/p5-orch-relational.md`. Send micro-signal to Lead via SendMessage: `PASS|handoffs:{N}|ref:/tmp/pipeline/p5-orch-relational.md`.

## Decision Points

### DPS Granularity
When deciding handoff specification depth:
- **Independent tasks** (no shared data): No DPS needed between them. Skip.
- **File-based handoff** (producer writes file, consumer reads): Define path + format + required fields.
- **Status-signal handoff** (producer reports PASS/FAIL): Define signal format per conventions.md. No file DPS needed.
- **Shared-state handoff** (both read/write same file): REJECT. Redesign as file-based with single producer.

### Format Selection
When producer output format is ambiguous from plan description:
- **Structured data** (task lists, assignments, metrics): Default to YAML. Machine-parseable for L1.
- **Narrative analysis** (rationale, evidence, summaries): Default to markdown. Human-readable for L2.
- **Mixed** (structured + narrative): Use markdown with YAML frontmatter. Standard L1+L2 pattern.

### Chain Completeness Verdict
When evaluating handoff chain integrity:
- **0 dangling inputs AND 0 orphaned outputs**: chain_complete: true. PASS.
- **0 dangling inputs BUT >= 1 orphaned output**: chain_complete: true. WARN (wasted computation, non-blocking).
- **>= 1 dangling input**: chain_complete: false. FAIL. Consumer tasks will break at execution.

## Methodology

### 1. Read Verified Plan
Load plan-verify-coordinator L3 output via `$ARGUMENTS` path. Extract:
- Task list with IDs, descriptions, file assignments
- Dependency graph (producer-consumer edges)
- Interface contracts from plan-interface (if available in L3)
- File change manifest per task

For STANDARD/COMPLEX tiers, construct the delegation prompt for the analyst with:
- **Context**: Paste verified plan L3 content. Include conventions.md SendMessage protocol. Include DPS reference: each handoff needs producer task, consumer task, file path, format, fields, validation.
- **Task**: "Identify ALL inter-task data dependencies. For each, define a DPS (Data-Passing Specification) with: producer task, consumer task, handoff file path, data format, required fields, validation rules. Validate chain completeness: every consumer input has a producer, no dangling inputs."
- **Constraints**: Read-only analysis. No modifications. Use `/tmp/pipeline/` as base path for handoff files. Every DPS must be fully specified.
- **Expected Output**: L1 YAML DPS specs. L2 handoff chain visualization with data flow.
- **Delivery**: Write full result to `/tmp/pipeline/p5-orch-relational.md`. Send micro-signal to Lead via SendMessage: `PASS|handoffs:{N}|ref:/tmp/pipeline/p5-orch-relational.md`.

#### Step 1 Tier-Specific DPS Variations
**TRIVIAL**: Skip — Lead defines handoffs inline (typically 0-1 handoffs for single-module tasks).
**STANDARD**: Single DPS to analyst. maxTurns:15. Define handoffs for file-based dependencies only. Omit validation rules.
**COMPLEX**: Full DPS as above. maxTurns:25. Deep handoff analysis with validation rules, format verification, and chain completeness proofs.

### 2. Identify Inter-Task Data Dependencies
Scan dependency graph for all producer-consumer relationships:

#### Dependency Types
| Type | Description | DPS Requirement |
|------|-------------|-----------------|
| File output | Producer creates a file consumer reads | Path, format, schema |
| Artifact reference | Producer writes path, consumer reads from it | Path convention, existence check |
| Status signal | Producer reports PASS/FAIL, consumer gates on it | Signal format, expected values |
| Shared state | Producer modifies state consumer reads | Mutex strategy, read-after-write |

#### Dependency Discovery Process
1. For each task, list outputs (files created/modified)
2. For each task, list inputs (files read, prerequisites)
3. Match outputs to inputs across tasks
4. Flag unmatched inputs (dangling -- no producer) and unmatched outputs (orphaned -- no consumer)

### 3. Define DPS Per Handoff
For each identified dependency, create a Data-Passing Specification:

```
DPS-{N}:
  producer: {task_id}
  consumer: {task_id}
  handoff:
    path: /tmp/pipeline/{phase}-{skill}-{artifact}.md
    format: yaml|json|markdown
    fields:
      - name: {field}
        type: {string|number|boolean|list|object}
        required: true|false
    validation:
      - rule: {description}
        check: {how to verify}
```

#### Path Convention
All handoff files follow the pattern: `/tmp/pipeline/{phase}-{skill}-{artifact}.{ext}`
- Phase: p5, p6, p7, p8
- Skill: abbreviated skill name
- Artifact: descriptive name (e.g., task-matrix, checkpoint-schedule)
- Extension: `.md` for markdown, `.yaml` for structured data

#### Format Selection
| Data Type | Recommended Format | Reason |
|-----------|-------------------|--------|
| Structured results (L1) | YAML | Machine-parseable, standard L1 format |
| Narrative analysis (L2) | Markdown | Human-readable, supports tables |
| Task lists | YAML | Structured with arrays |
| Status signals | Micro-signal string | Minimal, follows conventions.md protocol |

### 4. Validate Handoff Chain Completeness
Verify the handoff chain has no gaps:

#### Completeness Checks
| Check | Description | Failure Impact |
|-------|-------------|---------------|
| No dangling inputs | Every consumer input has a producer DPS | Consumer task will fail (missing data) |
| No orphaned outputs | Every producer output has a consumer DPS | Wasted computation (non-critical) |
| Format consistency | Producer output format matches consumer expected format | Parse failure at consumer |
| Field coverage | Consumer required fields are subset of producer output fields | Missing data at consumer |
| Path consistency | Producer writes to path consumer reads from | File-not-found at consumer |
| Ordering validity | Producer wave precedes consumer wave | Race condition |

#### Chain Visualization
Build a data flow diagram showing:
```
[Task-A] --DPS-01--> [Task-B] --DPS-02--> [Task-D]
[Task-A] --DPS-03--> [Task-C] --DPS-04--> [Task-D]
```

Mark each edge with DPS ID, format, and field count. Highlight dangling inputs in red (FAIL).

### 5. Output DPS Specification
Produce complete handoff specification with:
- Ordered list of DPS entries by execution sequence
- Chain completeness verdict (PASS if no dangling inputs)
- Format consistency report
- Path registry (all `/tmp/pipeline/` paths used)
- Summary: total handoffs, format distribution, dangling count

## Failure Handling

### Verified Plan Data Missing
- **Cause**: $ARGUMENTS path is empty or L3 file not found
- **Action**: Report FAIL. Signal: `FAIL|reason:plan-L3-missing|ref:/tmp/pipeline/p5-orch-relational.md`
- **Route**: Back to plan-verify-coordinator for re-export

### Dangling Input Detected
- **Cause**: Consumer task expects data that no producer task generates
- **Action**: Flag in L1 with severity HIGH. Include: consumer task ID, missing input, suggested producer.
- **Route**: Orchestrate-coordinator decides: add producer task or modify consumer to remove dependency.

### Circular Handoff Chain
- **Cause**: Task A produces for Task B which produces for Task A
- **Action**: Flag as chain cycle. Recommend breaking by converting one handoff to a pre-computed input.
- **Route**: Report to orchestrate-coordinator for resolution.

### Ambiguous Data Format
- **Cause**: Producer output format unclear from plan description
- **Action**: Default to markdown with YAML frontmatter (most flexible). Flag as assumption.

## Anti-Patterns

### DO NOT: Define Handoffs Without Specific Paths
"Task A passes data to Task B" is not a DPS. Every handoff must have a concrete file path, format, and field list.

### DO NOT: Use Shared Mutable State
Two tasks writing to the same file is not a handoff -- it is a race condition. Each handoff must have exactly 1 producer and 1+ consumers (read-only).

### DO NOT: Assume Implicit Handoffs
If the plan says "Task B uses Task A's output" but does not specify how, define the DPS explicitly. Implicit handoffs break at execution.

### DO NOT: Define Handoffs for Independent Tasks
Tasks with no data dependency do not need DPS entries. Only create handoffs where actual data flows between tasks.

### DO NOT: Ignore Format Compatibility
A producer outputting JSON and consumer expecting YAML will fail silently. Always verify format alignment.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-verify-coordinator | Verified plan L3 | File path via $ARGUMENTS: tasks, dependencies, file assignments |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestrate-coordinator | DPS handoff specs | Always (HOW dimension output) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Plan L3 missing | plan-verify-coordinator | Missing file path |
| Dangling inputs | orchestrate-coordinator | Consumer details + missing producer |
| Chain cycle | orchestrate-coordinator | Cycle path + break recommendation |
| All handoffs defined | orchestrate-coordinator | Complete DPS specs (normal flow) |

## Quality Gate
- Every inter-task data dependency has a DPS entry
- Every DPS has concrete path, format, and fields
- No dangling inputs (every consumer input has a producer)
- No circular handoff chains
- Path convention followed (/tmp/pipeline/ prefix)
- Format consistency between producer output and consumer input
- Producer wave precedes consumer wave in all DPS entries

## Output

### L1
```yaml
domain: orchestration
skill: relational
dimension: HOW
handoff_count: 0
dangling_inputs: 0
chain_complete: true|false
handoffs:
  - id: ""
    producer: ""
    consumer: ""
    path: ""
    format: yaml|json|markdown
    fields: []
```

### L2
- DPS specification per handoff
- Data flow chain visualization (ASCII)
- Completeness analysis with gap report
- Path registry for all handoff files
