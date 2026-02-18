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
| COMPLEX | 10+ files across 3+ domains, or structural changes (new domain/phase) | Complete INFRA-wide consistency audit |

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

| Category | Skills | Exemption Reason |
|----------|--------|------------------|
| Homeostasis | manage-infra, manage-codebase, self-diagnose, self-implement | Cross-cutting, any-phase operation |
| Cross-cutting | delivery-pipeline, pipeline-resume, task-management | Phase-independent utilities |
| FAIL routes | Any skill routing FAIL back to earlier phase | Error recovery is always backward |

### Count Source Priority

When CLAUDE.md count disagrees with filesystem:

```
AUTHORITATIVE SOURCE: Filesystem (always wins)
  .claude/agents/*.md  → agent count
  .claude/skills/*/SKILL.md → skill count
  unique domains in descriptions → domain count

CLAUDE.md must be updated to match filesystem, never the reverse.
```

## Methodology

### 1. Extract All References

For each skill description:
- Parse INPUT_FROM values (upstream skill/domain references)
- Parse OUTPUT_TO values (downstream skill/domain references)
- Build directed graph of skill dependencies

Reference extraction algorithm:

```
graph = DirectedGraph()
for each skill in .claude/skills/*/SKILL.md:
  desc = extract_frontmatter("description")
  input_from = parse_after("INPUT_FROM:", desc)
  output_to  = parse_after("OUTPUT_TO:", desc)
  domain     = parse_after("DOMAIN:", desc)
  for ref in input_from:  graph.add_edge(ref -> name, "INPUT_FROM")
  for ref in output_to:   graph.add_edge(name -> ref, "OUTPUT_TO")
  graph.set_node_attr(name, domain=domain)
```

For STANDARD/COMPLEX tiers, construct the DPS delegation prompt:
- **Context** (D11 priority: cognitive focus > token efficiency):
  - INCLUDE: All skill descriptions with INPUT_FROM/OUTPUT_TO extracted. CLAUDE.md declared counts (agents: 6, skills count, domains breakdown). Phase sequence: pre-design, design, research, plan, plan-verify, orchestration, execution, verify. Coordinator pattern documentation (research-coordinator, plan-verify-coordinator, orchestrate-coordinator create valid indirect links). Cross-cutting exemption list (manage-*, delivery, pipeline-resume, task-management, self-diagnose, self-implement). File paths within this analyst's ownership boundary.
  - EXCLUDE: L2 body cross-references (only check description-level INPUT_FROM/OUTPUT_TO). Full pipeline state beyond current file set. Historical rationale for skill relationships. FAIL route exceptions already documented as exempt (these are inherently unidirectional).
  - Budget: Context field ≤ 30% of analyst effective context.
- **Task**: Build directed reference graph. Check bidirectionality (A->B implies B->A). Check phase sequence (no backward refs except cross-cutting). Compare CLAUDE.md counts against filesystem.
- **Constraints**: Read-only. No modifications. Cross-cutting skills (manage-*, delivery, pipeline-resume, task-management, self-diagnose, self-implement) exempt from phase sequence.
- **Expected Output**: L1 YAML with relationships_checked, inconsistencies, findings[]. L2 relationship graph + phase sequence validation.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage format: `"{STATUS}|relationships:{relationships_checked}|violations:{inconsistencies}|ref:tasks/{team}/p7-consistency.md"`. L2 detail stays in agent context.

### 2. Verify Bidirectionality

For each INPUT_FROM reference A->B:
- Check that B's OUTPUT_TO includes A
- Flag unidirectional references (A claims input from B, but B doesn't output to A)
Similarly for OUTPUT_TO references.

Bidirectionality check example:

| Source | Reference | Target | Expected Reverse | Status |
|--------|-----------|--------|------------------|--------|
| execution-code | OUTPUT_TO: execution-impact | execution-impact | INPUT_FROM: execution-code | consistent |
| design-risk | OUTPUT_TO: research-codebase | research-codebase | INPUT_FROM: design-risk | ? (verify) |
| verify-structural-content | OUTPUT_TO: verify-consistency | verify-consistency | INPUT_FROM: verify-structural-content | consistent |
| verify-consistency | OUTPUT_TO: verify-quality | verify-quality | INPUT_FROM: verify-consistency | consistent |

Known exceptions to strict bidirectionality:

| Exception Type | Rule | Rationale |
|----------------|------|-----------|
| Homeostasis targets | May be OUTPUT_TO targets without reciprocal INPUT_FROM | Homeostasis skills accept input from any phase |
| FAIL routes | Unidirectional by nature | Error recovery does not create a forward dependency |
| "direct invocation" | Not a real skill reference | User-initiated, no reciprocal needed |
| "or" alternatives | Each alternative checked independently | e.g., "execution-infra (if FAIL) or execution-code (if FAIL)" |

### 2.1 Coordinator Pattern Recognition

The pipeline includes coordinator skills (research-coordinator, plan-verify-coordinator, orchestrate-coordinator) that consolidate parallel dimension outputs. These create indirect data flow patterns:

- Pattern: `skill-A OUTPUT_TO -> coordinator -> skill-B INPUT_FROM`
- This is a VALID indirect bidirectional link -- the coordinator acts as intermediary
- Do NOT flag these as broken bidirectionality when skill-A and skill-B do not directly reference each other
- The expanded skill set (33 -> 40 skills, with 16 new and 9 deleted) relies heavily on this coordinator pattern for P2, P4, and P5 phases

Example: `audit-static OUTPUT_TO -> research-coordinator -> plan-static INPUT_FROM` is valid even though audit-static does not directly reference plan-static.

### 3. Check Phase Sequence

Verify domain ordering follows pipeline:

```
P0: pre-design   (brainstorm → validate → feasibility)
P1: design        (architecture → interface, risk)
P2: research      (codebase ∥ external → audit)
P3: plan          (decomposition → interface → strategy)
P4: plan-verify   (unified verification)
P5: orchestration (decompose → assign → verify)
P6: execution     (code ∥ infra → impact → cascade → review)
P7: verify        (structural-content → consistency → quality → cc-feasibility)
P8: delivery      (delivery-pipeline)
```

Backward reference = any OUTPUT_TO pointing to a domain with LOWER phase number.

```
Backward reference decision:
  Is the source skill cross-cutting or homeostasis?
  ├─ YES → EXEMPT (no violation)
  └─ NO → Is the reference a FAIL route?
      ├─ YES → EXEMPT (error recovery)
      └─ NO → VIOLATION (flag as MEDIUM severity)
```

- Cross-cutting skills (manage-*, delivery, pipeline-resume, task-management, self-diagnose, self-implement) exempt from sequence
- No backward phase references from pipeline skills (e.g., verify outputting to pre-design)

### 4. Verify CLAUDE.md Consistency

Check CLAUDE.md references match filesystem:

| CLAUDE.md Section | Field | Expected Value | Check Method |
|-------------------|-------|----------------|--------------|
| S1 Team Identity | Agent count | Count of `.claude/agents/*.md` | Glob + count |
| S1 Team Identity | Skills count | Count of `.claude/skills/*/SKILL.md` | Glob + count |
| S1 Team Identity | Domain count | Unique domains extracted from all descriptions | Grep "DOMAIN:" + unique |
| S1 Team Identity | Agent names | Names listed match agent filenames | Compare sets |
| S2 Pipeline Tiers | Phase labels | Match domain names in skill descriptions | Cross-reference |

Expected domain breakdown: Pipeline (8) + Homeostasis (4) + Cross-cutting (3) = 15 total.
Verify: skills count, agent count, and domain names all consistent between CLAUDE.md and filesystem.

### 5. Generate Consistency Report

Produce relationship matrix:
- All skill pairs with their reference direction
- Bidirectionality status per pair
- Phase sequence violations if any
- CLAUDE.md drift items if any

Severity classification for findings:

| Inconsistency Type | Severity | Blocking? | Resolution Route |
|--------------------|----------|-----------|------------------|
| Unidirectional INPUT_FROM/OUTPUT_TO | HIGH | Yes | execution-infra: add missing reference |
| CLAUDE.md count mismatch | HIGH | Yes | execution-infra: update CLAUDE.md counts |
| Backward phase reference (non-FAIL, non-exempt) | MEDIUM | Yes | execution-infra or Lead assessment |
| Missing cross-cutting exemption documentation | LOW | No | Note in report for future cleanup |
| Circular dependency (non-FAIL) | LOW | No | Document cycle for Lead review |

## Failure Handling

### D12 Escalation Ladder

| Failure Type | Level | Action |
|---|---|---|
| Analyst tool error reading skill descriptions | L0 Retry | Re-invoke analyst with same DPS |
| Reference graph incomplete or bidirectionality check missed files | L1 Nudge | SendMessage with corrected file list + exemption documentation |
| Analyst stuck on circular dependency resolution, turns exhausted | L2 Respawn | Kill analyst → spawn fresh with reduced scope per domain |
| Count mismatch reveals filesystem/CLAUDE.md structural divergence | L3 Restructure | Route count fixes to execution-infra before consistency check proceeds |
| 3+ L2 failures or graph construction strategy unclear | L4 Escalate | AskUserQuestion with situation summary + options |

| Failure Type | Action | Route | Data Passed |
|--------------|--------|-------|-------------|
| Bidirectionality violation | FAIL | execution-infra | `{ source, target, direction, missing_reverse }` |
| Phase sequence violation | FAIL | Lead (assess) then execution-infra | `{ source, source_phase, target, target_phase }` |
| CLAUDE.md count drift | FAIL | execution-infra | `{ component, declared, actual, diff }` |
| Circular dependency (non-FAIL) | WARN | Document for Lead review | `{ cycle[], involves_fail_route }` |

Pipeline impact assessment:

| Failure Type | Blocking? | Rationale |
|--------------|-----------|-----------|
| Bidirectionality violation | Yes | Broken routing graph = missed skill invocations |
| Phase sequence violation | Yes | Could cause infinite loops or skipped phases |
| CLAUDE.md count drift | Yes | Lead uses counts for completeness validation |
| Circular dependency (FAIL-route) | No | Expected error recovery pattern |
| Missing exemption docs | No | Functional correctness unaffected |

## Anti-Patterns

### DO NOT: Require Strict Bidirectionality for FAIL Routes
Error recovery routes are inherently unidirectional. FAIL routes from any skill back to execution-infra or Lead do not require reciprocal OUTPUT_TO declarations.

### DO NOT: Flag Homeostasis Skills for Phase Violations
Homeostasis and cross-cutting skills (manage-*, delivery-pipeline, pipeline-resume, task-management, self-diagnose, self-implement) operate across all phases by design. Phase sequence enforcement does not apply.

### DO NOT: Auto-Update CLAUDE.md Counts
Consistency check is strictly read-only. All fixes — including count corrections — route through execution-infra. Mixing verification with modification introduces bias.

### DO NOT: Check Semantic Correctness of References
Consistency verifies that if A references B, then B references A (structural bidirectionality). Whether A SHOULD reference B is verify-quality's domain.

### DO NOT: Deep-Scan L2 Bodies for References
Only check description-level INPUT_FROM/OUTPUT_TO, not L2 body cross-references. L2 bodies may contain illustrative examples that are not actual routing declarations.

### DO NOT: Combine Consistency with Quality Checks
Consistency = structural relationship integrity. Quality = routing effectiveness. These are separate verification dimensions with different scoring rubrics.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

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

| Failure Type | Route To | Data Passed |
|--------------|----------|-------------|
| Bidirectionality violation | execution-infra | Source skill, target skill, missing direction |
| Phase sequence violation | execution-infra (or Lead for FAIL route assessment) | Violating reference pair with phase numbers |
| CLAUDE.md count drift | execution-infra | Expected vs actual per component type |

> **D17 Note**: P0-P1 local mode — Lead reads output directly via TaskOutput. 3-channel protocol applies P2+ only.

## Quality Gate

- All INPUT_FROM/OUTPUT_TO references are bidirectional (or documented as exempt)
- Phase sequence follows P0->P8 ordering (no unauthorized backward references)
- CLAUDE.md component counts match filesystem exactly
- All cross-cutting exemptions are documented
- Zero unresolved inconsistencies after check

## Output

### L1
```yaml
domain: verify
skill: consistency
status: PASS|FAIL
pt_signal: "metadata.phase_signals.p7_consistency"
signal_format: "{STATUS}|relationships:{relationships_checked}|violations:{inconsistencies}|ref:tasks/{team}/p7-consistency.md"
relationships_checked: 0
inconsistencies: 0
bidirectionality_violations: 0
phase_sequence_violations: 0
claude_md_drift_items: 0
findings:
  - source: ""
    target: ""
    type: INPUT_FROM|OUTPUT_TO
    direction: forward|backward
    status: consistent|inconsistent|exempt
    severity: HIGH|MEDIUM|LOW
```

### L2
- Full relationship graph with consistency status per edge
- Bidirectionality check results (table of all reference pairs)
- Phase sequence logic validation (forward-only enforcement with exemptions noted)
- CLAUDE.md count comparison (declared vs actual per component type)
- Inconsistency detail: source file, target file, missing reference, recommended fix
