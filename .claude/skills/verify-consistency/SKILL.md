---
name: verify-consistency
description: >-
  Cross-references skill input/output bidirectionality and counts
  across all skill descriptions. Verifies phase sequence P0
  through P8. Second of four sequential verify stages. Use after
  verify-structural-content PASS or after multi-skill description
  edits. Reads from verify-structural-content structural and
  content integrity confirmation. Produces relationship matrix
  with consistency status for verify-quality on PASS, or routes
  back to execution-infra on FAIL. On FAIL, routes source skill,
  target skill, and missing direction to execution-infra. Builds
  directed reference graph from INPUT_FROM/OUTPUT_TO keys. Flags
  unidirectional references, unauthorized backward phase
  references, and CLAUDE.md count drift. TRIVIAL: Lead-direct
  on 2-3 files. STANDARD: 1 analyst. COMPLEX: 2 analysts —
  bidirectionality split from phase sequence. DPS context: all
  skill descriptions with INPUT_FROM/OUTPUT_TO extracted +
  CLAUDE.md counts. Exclude L2 body cross-references, FAIL
  route exceptions already documented as exempt.
user-invocable: true
disable-model-invocation: false
---

# Verify — Consistency

## Execution Model
- **TRIVIAL**: Lead-direct. Quick cross-reference check on 2-3 files.
- **STANDARD**: Spawn analyst (maxTurns: 25). Full relationship graph construction.
- **COMPLEX**: Spawn 2 analysts (maxTurns: 30 each). One for INPUT_FROM/OUTPUT_TO, one for phase sequence.

## Decision Points

### Tier Classification

| Tier | Criteria | Scope |
|------|----------|-------|
| TRIVIAL | 2-3 files changed in same domain | Quick cross-ref check on changed files only |
| STANDARD | 4-10 files across 2 domains | Full relationship graph for affected domains + adjacent |
| COMPLEX | 10+ files across 3+ domains, or structural changes | Complete INFRA-wide consistency audit |

### Scope Decision Tree

```
Only L2 body changed (no frontmatter)?  → SKIP (no routing impact)
Only non-.claude/ files changed?         → SKIP (no INFRA routing impact)
Otherwise → scope by change type:
  Single skill frontmatter   → That skill's INPUT_FROM/OUTPUT_TO only
  Domain-wide edit           → All skills in domain + adjacent domains
  CLAUDE.md edit             → Full count consistency check
  New skill creation         → Full bidirectionality + phase sequence + count
  New agent creation         → Agent count + skill descriptions referencing agent
```

### Phase Sequence Exemptions

Skills exempt from forward-only phase sequence enforcement:
- **Homeostasis**: manage-infra, manage-codebase, self-diagnose, self-implement — cross-cutting, any-phase
- **Cross-cutting**: delivery-pipeline, pipeline-resume, task-management — phase-independent utilities
- **FAIL routes**: any skill routing FAIL back to earlier phase — error recovery is always backward

### Count Source Priority

Filesystem always wins: `.claude/agents/*.md` → agent count, `.claude/skills/*/SKILL.md` → skill
count, unique domains in descriptions → domain count. CLAUDE.md must be updated to match, not the reverse.

## Methodology

Five steps — for algorithm pseudocode, DPS construction details, example tables, and severity
classification, read `resources/methodology.md`.

### 1. Extract All References
Parse INPUT_FROM and OUTPUT_TO values from each skill's description frontmatter. Build a directed
graph of skill dependencies. For STANDARD/COMPLEX tiers, construct analyst DPS with D11-filtered
context (see `resources/methodology.md` for INCLUDE/EXCLUDE/Budget block and delivery format).

### 2. Verify Bidirectionality
For each INPUT_FROM reference A→B: check that B's OUTPUT_TO includes A. Flag unidirectional pairs.
Exemptions: homeostasis targets, FAIL routes, "direct invocation", "or" alternatives.
See `resources/methodology.md` for example table and full exception list.

### 2.1 Coordinator Pattern Recognition
Coordinator skills (research-coordinator, plan-verify-coordinator, orchestrate-coordinator) create
valid indirect links: `skill-A OUTPUT_TO → coordinator → skill-B INPUT_FROM`. Do NOT flag these as
broken bidirectionality. See `resources/methodology.md` for full pattern detail.

### 3. Check Phase Sequence
Verify domain ordering follows P0→P8. Flag backward references from non-exempt pipeline skills.
Cross-cutting and homeostasis skills are always exempt. See `resources/methodology.md` for full
phase sequence and backward reference decision tree.

### 4. Verify CLAUDE.md Consistency
Compare CLAUDE.md declared counts (agents, skills, domains) against filesystem actuals.
Filesystem always wins. See `resources/methodology.md` for field-by-field check table.

### 5. Generate Consistency Report
Produce relationship matrix: all skill pairs with direction, bidirectionality status, phase sequence
violations, CLAUDE.md drift items. See `resources/methodology.md` for severity classification table
and pipeline impact assessment.

## Failure Handling

### D12 Escalation Ladder

| Failure Type | Level | Action |
|---|---|---|
| Analyst tool error reading skill descriptions | L0 Retry | Re-invoke analyst with same DPS |
| Reference graph incomplete or missed files | L1 Nudge | SendMessage with corrected file list + exemption docs |
| Analyst stuck on circular dependency, turns exhausted | L2 Respawn | Fresh instance, reduced scope per domain |
| Count mismatch reveals filesystem/CLAUDE.md divergence | L3 Restructure | Route count fixes to execution-infra first |
| 3+ L2 failures or graph construction strategy unclear | L4 Escalate | AskUserQuestion with summary + options |

> For escalation details: read `.claude/resources/failure-escalation-ladder.md`

### FAIL Routes

| Failure Type | Route | Data Passed |
|--------------|-------|-------------|
| Bidirectionality violation | execution-infra | `{ source, target, direction, missing_reverse }` |
| Phase sequence violation | Lead → execution-infra | `{ source, source_phase, target, target_phase }` |
| CLAUDE.md count drift | execution-infra | `{ component, declared, actual, diff }` |
| Circular dependency (non-FAIL) | Document for Lead review | `{ cycle[], involves_fail_route }` |

## Anti-Patterns

- **DO NOT** require bidirectionality for FAIL routes — error recovery is inherently unidirectional.
- **DO NOT** flag homeostasis/cross-cutting skills for phase violations — they are always exempt.
- **DO NOT** auto-update CLAUDE.md counts — this skill is strictly read-only; fixes go through execution-infra.
- **DO NOT** check semantic correctness of references — structural bidirectionality only; verify-quality owns semantics.
- **DO NOT** deep-scan L2 bodies — only check description-level INPUT_FROM/OUTPUT_TO, not illustrative examples.
- **DO NOT** combine consistency with quality checks — separate dimensions with different scoring rubrics.

## Phase-Aware Execution

Runs in P2+ Team mode only. Four-Channel Protocol applies:
- **Ch1**: PT metadata signal `metadata.phase_signals.p7_consistency`
- **Ch2**: Full output file at `tasks/{team}/p7-consistency.md`
- **Ch3**: Micro-signal to Lead (status only, not full data)
- **Ch4**: P2P signal to verify-quality on PASS

> For phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Transitions

### Receives From

| Source Skill | Data Expected | Format |
|--------------|---------------|--------|
| verify-structural-content | Structural+content checks confirmed | L1 YAML: PASS verdict with utilization metrics |
| Direct invocation | Specific files or full INFRA check | File paths or "full" flag via $ARGUMENTS |

### Sends To

| Target Skill | Data Produced | Trigger Condition |
|--------------|---------------|-------------------|
| verify-quality | Relationship integrity confirmed | PASS verdict (all checks green) |
| execution-infra | Consistency fix requests | FAIL verdict on .claude/ references |

### Failure Routes
FAIL → execution-infra (bidirectionality violations, count drift) or Lead → execution-infra
(phase sequence violations). See Failure Handling section for data passed per type.

> **D17 Note**: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate

- All INPUT_FROM/OUTPUT_TO references are bidirectional (or documented as exempt)
- Phase sequence follows P0→P8 ordering (no unauthorized backward references)
- CLAUDE.md component counts match filesystem exactly
- All cross-cutting exemptions are documented
- Zero unresolved inconsistencies after check

> For full quality gate checklist: read `.claude/resources/quality-gate-checklist.md`

## Output

### L1
```yaml
domain: verify
skill: consistency
status: PASS|FAIL
pt_signal: "metadata.phase_signals.p7_consistency"
signal_format: "{STATUS}|relationships:{n}|violations:{n}|ref:tasks/{team}/p7-consistency.md"
relationships_checked: 0
inconsistencies: 0
bidirectionality_violations: 0
phase_sequence_violations: 0
claude_md_drift_items: 0
findings:
  - source: ""
    target: ""
    type: INPUT_FROM|OUTPUT_TO
    status: consistent|inconsistent|exempt
    severity: HIGH|MEDIUM|LOW
```

### L2
Full relationship graph + bidirectionality pairs table + phase sequence validation + CLAUDE.md count comparison (declared vs actual) + inconsistency detail with recommended fix per item.
