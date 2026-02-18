# Verify Consistency — Detailed Methodology
> On-demand reference. Contains reference extraction algorithm, DPS construction details,
> bidirectionality examples, coordinator pattern, phase sequence order, CLAUDE.md field
> table, severity classification, and pipeline impact assessment.

## Reference Extraction Algorithm

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

## DPS Construction Details (STANDARD/COMPLEX)

- **INCLUDE**: All skill descriptions with INPUT_FROM/OUTPUT_TO extracted. CLAUDE.md declared counts
  (agents: 6, skills count, domains breakdown). Phase sequence: pre-design, design, research, plan,
  plan-verify, orchestration, execution, verify. Coordinator pattern documentation
  (research-coordinator, plan-verify-coordinator, orchestrate-coordinator create valid indirect links).
  Cross-cutting exemption list. File paths within this analyst's ownership boundary.
- **EXCLUDE**: L2 body cross-references (only check description-level INPUT_FROM/OUTPUT_TO). Full
  pipeline state beyond current file set. Historical rationale for skill relationships. FAIL route
  exceptions already documented as exempt (inherently unidirectional).
- **Budget**: Context field ≤ 30% of analyst effective context.
- **Task**: Build directed reference graph. Check bidirectionality (A->B implies B->A). Check phase
  sequence (no backward refs except cross-cutting). Compare CLAUDE.md counts against filesystem.
- **Output**: L1 YAML with relationships_checked, inconsistencies, findings[]. L2 relationship graph +
  phase sequence validation.
- **Delivery**: `"{STATUS}|relationships:{n}|violations:{n}|ref:tasks/{team}/p7-consistency.md"`

## Bidirectionality Check — Example Table

| Source | Reference | Target | Expected Reverse | Status |
|--------|-----------|--------|------------------|--------|
| execution-code | OUTPUT_TO: execution-impact | execution-impact | INPUT_FROM: execution-code | consistent |
| design-risk | OUTPUT_TO: research-codebase | research-codebase | INPUT_FROM: design-risk | ? (verify) |
| verify-structural-content | OUTPUT_TO: verify-consistency | verify-consistency | INPUT_FROM: verify-structural-content | consistent |
| verify-consistency | OUTPUT_TO: verify-quality | verify-quality | INPUT_FROM: verify-consistency | consistent |

## Known Bidirectionality Exceptions

| Exception Type | Rule | Rationale |
|----------------|------|-----------|
| Homeostasis targets | May be OUTPUT_TO targets without reciprocal INPUT_FROM | Homeostasis skills accept input from any phase |
| FAIL routes | Unidirectional by nature | Error recovery does not create a forward dependency |
| "direct invocation" | Not a real skill reference | User-initiated, no reciprocal needed |
| "or" alternatives | Each alternative checked independently | e.g., "execution-infra (if FAIL) or execution-code (if FAIL)" |

## Coordinator Pattern Recognition

The pipeline includes coordinator skills (research-coordinator, plan-verify-coordinator,
orchestrate-coordinator) that consolidate parallel dimension outputs. These create indirect data flow:

- Pattern: `skill-A OUTPUT_TO -> coordinator -> skill-B INPUT_FROM`
- This is a VALID indirect bidirectional link — the coordinator acts as intermediary
- Do NOT flag as broken bidirectionality when skill-A and skill-B do not directly reference each other
- The expanded skill set (33 -> 40 skills) relies heavily on this coordinator pattern for P2, P4, P5

Example: `audit-static OUTPUT_TO -> research-coordinator -> plan-static INPUT_FROM` is valid even
though audit-static does not directly reference plan-static.

## Phase Sequence Order (P0 → P8)

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

Backward reference decision tree:
```
Is the source skill cross-cutting or homeostasis?
├─ YES → EXEMPT (no violation)
└─ NO → Is the reference a FAIL route?
    ├─ YES → EXEMPT (error recovery)
    └─ NO → VIOLATION (flag as MEDIUM severity)
```

## CLAUDE.md Consistency Check — Field Table

| CLAUDE.md Section | Field | Expected Value | Check Method |
|-------------------|-------|----------------|--------------|
| S1 Team Identity | Agent count | Count of `.claude/agents/*.md` | Glob + count |
| S1 Team Identity | Skills count | Count of `.claude/skills/*/SKILL.md` | Glob + count |
| S1 Team Identity | Domain count | Unique domains extracted from all descriptions | Grep "DOMAIN:" + unique |
| S1 Team Identity | Agent names | Names listed match agent filenames | Compare sets |
| S2 Pipeline Tiers | Phase labels | Match domain names in skill descriptions | Cross-reference |

Expected domain breakdown: Pipeline (8) + Homeostasis (4) + Cross-cutting (3) = 15 total.

## Severity Classification

| Inconsistency Type | Severity | Blocking? | Resolution Route |
|--------------------|----------|-----------|------------------|
| Unidirectional INPUT_FROM/OUTPUT_TO | HIGH | Yes | execution-infra: add missing reference |
| CLAUDE.md count mismatch | HIGH | Yes | execution-infra: update CLAUDE.md counts |
| Backward phase reference (non-FAIL, non-exempt) | MEDIUM | Yes | execution-infra or Lead assessment |
| Missing cross-cutting exemption documentation | LOW | No | Note in report for future cleanup |
| Circular dependency (non-FAIL) | LOW | No | Document cycle for Lead review |

## Pipeline Impact Assessment

| Failure Type | Blocking? | Rationale |
|--------------|-----------|-----------|
| Bidirectionality violation | Yes | Broken routing graph = missed skill invocations |
| Phase sequence violation | Yes | Could cause infinite loops or skipped phases |
| CLAUDE.md count drift | Yes | Lead uses counts for completeness validation |
| Circular dependency (FAIL-route) | No | Expected error recovery pattern |
| Missing exemption docs | No | Functional correctness unaffected |
