---
name: orchestrate-relational
description: >-
  Specifies DPS contracts per producer-consumer handoff with
  path, format, and validation rules. Validates chain
  completeness. Parallel with orchestrate-static,
  orchestrate-behavioral, and orchestrate-impact. Use after
  plan-verify-coordinator complete with all PASS. Reads from
  plan-verify-coordinator verified plan L3 via $ARGUMENTS.
  Produces DPS specs with chain completeness flag and data flow
  chain with gap report for orchestrate-coordinator. DPS contracts include MCP_DIRECTIVES (WHEN/WHY/WHAT) and file-based handoff spec per DPS v5. On FAIL, Lead
  applies D12 escalation. DPS needs plan-verify-coordinator
  verified plan L3. Exclude other orchestrate dimension outputs.
user-invocable: true
disable-model-invocation: true
---

# Orchestrate — Relational (HOW)

## Execution Model
- **TRIVIAL**: Skip (orchestration simplified for trivial tiers).
- **STANDARD**: Spawn 1 analyst. maxTurns:15. Systematic handoff identification and DPS definition.
- **COMPLEX**: Spawn 1 analyst. maxTurns:25. Deep handoff analysis with validation rules and chain completeness proofs.

## Phase-Aware Execution

Two-Channel protocol only. Single-session subagent execution:
- **Subagent writes** output file to `tasks/{work_dir}/p5-orch-relational.md`
- **Ch3 micro-signal** to Lead with PASS/FAIL status
- **Task tracking**: Subagent calls TaskUpdate on completion. File ownership: only modify assigned files.

> For micro-signal format details: read `.claude/resources/output-micro-signal-format.md`

## Decision Points

### DPS Granularity
- **Independent tasks** (no shared data): No DPS needed. Skip.
- **File-based handoff** (producer writes file, consumer reads): Define path + format + required fields.
- **Status-signal handoff** (producer reports PASS/FAIL): Define signal format per file-based signal protocol. No file DPS needed.
- **Shared-state handoff** (both read/write same file): REJECT. Redesign as file-based with single producer.

### Format Selection
- **Structured data** (task lists, assignments, metrics): Default to YAML. Machine-parseable for L1.
- **Narrative analysis** (rationale, evidence, summaries): Default to markdown. Human-readable for L2.
- **Mixed** (structured + narrative): Use markdown with YAML frontmatter. Standard L1+L2 pattern.

### Chain Completeness Verdict
- **0 dangling inputs AND 0 orphaned outputs**: `chain_complete: true`. PASS.
- **0 dangling inputs BUT >= 1 orphaned output**: `chain_complete: true`. WARN (wasted computation, non-blocking).
- **>= 1 dangling input**: `chain_complete: false`. FAIL. Consumer tasks will break at execution.

## Methodology

### 1. Read Verified Plan
Load plan-verify-coordinator L3 output via `$ARGUMENTS` path. Extract task list, dependency graph (producer-consumer edges), interface contracts, and file change manifest per task.

Construct analyst DPS with D11 context filtering (cognitive focus first — exclude other dimension outputs, historical rationale, full pipeline state). Budget: Context ≤ 30% of subagent context.

> For DPS construction details (D11 INCLUDE/EXCLUDE blocks, tier DPS variations): read `resources/methodology.md`

**Analyst delivery:** Write to `tasks/{work_dir}/p5-orch-relational.md`. Ch3: `PASS|handoffs:{N}|ref:tasks/{work_dir}/p5-orch-relational.md`.

### 2. Identify Inter-Task Data Dependencies
Scan dependency graph for all producer-consumer relationships: file outputs, artifact references, status signals, and shared-state cases (reject last type).

> For dependency type definitions and discovery algorithm: read `resources/methodology.md`

### 3. Define DPS Per Handoff (with file-based handoff spec)
For each identified dependency, create a Data-Passing Specification with P2P handoff protocol. file-based handoff spec (notify/signal_format/await) is MANDATORY for every DPS entry in COMPLEX tier.

> For full DPS YAML schema, file-based handoff spec details, path convention, and format selection table: read `resources/methodology.md`

### 4. Validate Handoff Chain Completeness
Verify no dangling inputs, no format mismatches, no path inconsistencies, and no circular chains. Build chain visualization (ASCII data flow diagram).

> For completeness checks table and chain visualization format: read `resources/methodology.md`

### 5. Output DPS Specification
Produce ordered DPS entries by execution sequence, chain completeness verdict, format consistency report, path registry, and summary metrics.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Plan L3 path empty or file missing (transient) | L0 Retry | Re-invoke after plan-verify-coordinator re-exports |
| DPS incomplete or handoff path ambiguous | L1 Nudge | Respawn with refined DPS targeting refined path convention constraints |
| Agent stuck, context polluted, turns exhausted | L2 Respawn | Kill → fresh analyst with refined DPS |
| Dangling inputs unresolvable without plan restructure | L3 Restructure | Route to orchestrate-coordinator as chain design blocker |
| 3+ L2 failures or circular chains unresolvable | L4 Escalate | AskUserQuestion with situation + options |

> For failure sub-case details (plan missing, dangling input, circular chain, ambiguous format): read `resources/methodology.md`

## Anti-Patterns

- **DO NOT: Define handoffs without specific paths.** "Task A passes data to Task B" is not a DPS. Every handoff must have a concrete file path, format, and field list.
- **DO NOT: Use shared mutable state.** Two tasks writing to the same file is a race condition, not a handoff. Each handoff must have exactly 1 producer and 1+ consumers (read-only).
- **DO NOT: Assume implicit handoffs.** If the plan says "Task B uses Task A's output" without specifying how, define the DPS explicitly. Implicit handoffs break at execution.
- **DO NOT: Define handoffs for independent tasks.** Only create handoffs where actual data flows between tasks.
- **DO NOT: Ignore format compatibility.** A producer outputting JSON and consumer expecting YAML will fail silently. Always verify format alignment.

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

> D17 Note: Two-Channel protocol — Ch2 (file output to tasks/{work_dir}/) + Ch3 (micro-signal to Lead).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- Every inter-task data dependency has a DPS entry
- Every DPS has concrete path, format, and fields
- No dangling inputs (every consumer input has a producer)
- No circular handoff chains
- Path convention followed (`tasks/{work_dir}/` prefix)
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
pt_signal: "metadata.phase_signals.p5_orchestrate_relational"
signal_format: "PASS|handoffs:{N}|chain_complete:{bool}|ref:tasks/{work_dir}/p5-orch-relational.md"
```

### L2
- DPS specification per handoff
- Data flow chain visualization (ASCII)
- Completeness analysis with gap report
- Path registry for all handoff files
