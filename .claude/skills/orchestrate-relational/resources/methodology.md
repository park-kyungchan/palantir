# Orchestrate Relational — Detailed Methodology

> On-demand reference. Contains DPS construction details, dependency algorithms, template schemas, completeness checks, and failure sub-cases.
> Loaded when SKILL.md body directs. Zero cost until read.

---

## Step 1: DPS Construction — D11 Context Protocol

When constructing the analyst DPS, apply D11 priority order (cognitive focus > token efficiency):

**INCLUDE in Context field:**
- Verified plan L3 content: task list, producer-consumer edges, file assignments
- file-based signal protocol for status-signal handoffs
- DPS reference: each handoff needs producer task, consumer task, file path, format, fields, validation

**EXCLUDE from Context field:**
- Other orchestrate dimension outputs (static, behavioral, impact)
- Historical rationale from plan-verify phases
- Full pipeline state beyond this task's scope

**Budget:** Context field ≤ 30% of subagent effective context window.

### Tier-Specific DPS Variations

| Tier | Analyst Spawn | maxTurns | Scope |
|------|--------------|---------|-------|
| TRIVIAL | Skip — Lead defines handoffs inline (typically 0-1) | — | — |
| STANDARD | Single DPS to analyst | 15 | File-based dependencies only. Omit validation rules. |
| COMPLEX | Full DPS as specified | 25 | Deep analysis: validation rules, format verification, chain completeness proofs |

---

## Step 2: Dependency Types and Discovery

### Dependency Types

| Type | Description | DPS Requirement |
|------|-------------|-----------------|
| File output | Producer creates a file consumer reads | Path, format, schema |
| Artifact reference | Producer writes path, consumer reads from it | Path convention, existence check |
| Status signal | Producer reports PASS/FAIL, consumer gates on it | Signal format, expected values |
| Shared state | Producer modifies state consumer reads | Mutex strategy, read-after-write |

### Dependency Discovery Process

1. For each task, list outputs (files created/modified)
2. For each task, list inputs (files read, prerequisites)
3. Match outputs to inputs across tasks
4. Flag unmatched inputs (dangling — no producer) and unmatched outputs (orphaned — no consumer)

---

## Step 3: DPS Template Schema (file-based handoff spec)

```
DPS-{N}:
  producer: {task_id}
  consumer: {task_id}
  handoff:
    path: tasks/{work_dir}/{phase}-{skill}-{artifact}.md
    format: yaml|json|markdown
    fields:
      - name: {field}
        type: {string|number|boolean|list|object}
        required: true|false
    validation:
      - rule: {description}
        check: {how to verify}
  comm_protocol:
    notify: [{consumer_subagent_name}]       # Producer sends file-based signal to these subagents
    signal_format: "READY|path:tasks/{work_dir}/{file}|fields:{field_list}"
    await: [{producer_subagent_name}]        # Consumer waits for file-based signal from these subagents
```

**file-based handoff spec is MANDATORY for every DPS entry in COMPLEX tier.** This enables the Two-Channel Protocol: producer writes to disk (Ch2), signals Lead (Ch3 micro-signal), and signals consumer directly (file-based output). Lead does NOT relay data between subagents.

### Path Convention

All handoff files follow: `tasks/{work_dir}/{phase}-{skill}-{artifact}.{ext}`
- Phase: p5, p6, p7, p8
- Skill: abbreviated skill name
- Artifact: descriptive name (e.g., task-matrix, checkpoint-schedule)
- Extension: `.md` for markdown, `.yaml` for structured data

### Format Selection Table

| Data Type | Recommended Format | Reason |
|-----------|-------------------|--------|
| Structured results (L1) | YAML | Machine-parseable, standard L1 format |
| Narrative analysis (L2) | Markdown | Human-readable, supports tables |
| Task lists | YAML | Structured with arrays |
| Status signals | Micro-signal string | Minimal, follows file-based signal protocol |

---

## Step 4: Completeness Checks

| Check | Description | Failure Impact |
|-------|-------------|---------------|
| No dangling inputs | Every consumer input has a producer DPS | Consumer task will fail (missing data) |
| No orphaned outputs | Every producer output has a consumer DPS | Wasted computation (non-critical) |
| Format consistency | Producer output format matches consumer expected format | Parse failure at consumer |
| Field coverage | Consumer required fields are subset of producer output fields | Missing data at consumer |
| Path consistency | Producer writes to path consumer reads from | File-not-found at consumer |
| Ordering validity | Producer wave precedes consumer wave | Race condition |

### Chain Visualization

Build a data flow diagram showing:
```
[Task-A] --DPS-01--> [Task-B] --DPS-02--> [Task-D]
[Task-A] --DPS-03--> [Task-C] --DPS-04--> [Task-D]
```
Mark each edge with DPS ID, format, and field count. Highlight dangling inputs in red (FAIL).

---

## Step 5: Output DPS Specification

Produce complete handoff specification with:
- Ordered list of DPS entries by execution sequence
- Chain completeness verdict (PASS if no dangling inputs)
- Format consistency report
- Path registry (all `tasks/{work_dir}/` paths used)
- Summary: total handoffs, format distribution, dangling count

---

## Failure Sub-Cases

### Verified Plan Data Missing
- **Cause**: $ARGUMENTS path is empty or L3 file not found
- **Action**: Report FAIL. Signal: `FAIL|reason:plan-L3-missing|ref:tasks/{work_dir}/p5-orch-relational.md`
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
