---
name: verify-consistency
description: |
  [P8·Verify·Consistency] Cross-file relationship integrity verifier. Checks skill-agent routing matches between CLAUDE.md and frontmatter, phase sequence logic, INPUT_FROM/OUTPUT_TO bidirectionality, and skills table vs directory.

  WHEN: After multi-file changes or relationship modifications. Third of 5 verify stages. Can run independently.
  DOMAIN: verify (skill 3 of 5). After verify-content PASS.
  INPUT_FROM: verify-content (content completeness confirmed) or direct invocation.
  OUTPUT_TO: verify-quality (if PASS) or execution-infra (if FAIL on .claude/ files) or execution-code (if FAIL on source files).

  METHODOLOGY: (1) Extract all INPUT_FROM/OUTPUT_TO refs from descriptions, (2) Build relationship graph, (3) Verify bidirectionality (A refs B <-> B refs A), (4) Check phase sequence (domain N -> domain N+1), (5) Verify CLAUDE.md skills table matches .claude/skills/ listing.
  OUTPUT_FORMAT: L1 YAML relationship matrix with consistency status, L2 markdown inconsistency report with source/target evidence.
user-invocable: true
disable-model-invocation: false
---

# Verify — Consistency

## Execution Model
- **TRIVIAL**: Lead-direct. Quick cross-reference check on 2-3 files.
- **STANDARD**: Spawn analyst. Full relationship graph construction.
- **COMPLEX**: Spawn 2 analysts. One for INPUT_FROM/OUTPUT_TO, one for phase sequence.

## Methodology

### 1. Extract All References
For each skill description:
- Parse INPUT_FROM values (upstream skill/domain references)
- Parse OUTPUT_TO values (downstream skill/domain references)
- Build directed graph of skill dependencies

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: All skill descriptions (paste the description field for each of the 35 skills with their INPUT_FROM/OUTPUT_TO values extracted). Include CLAUDE.md counts (agents: 6, skills: 35, domains: 8+4+3). Include expected phase sequence: pre-design→design→research→plan→plan-verify→orchestration→execution→verify.
- **Task**: "Build directed reference graph from INPUT_FROM/OUTPUT_TO values. For each reference pair: check bidirectionality (A→B implies B→A). Check phase sequence: no backward references except cross-cutting skills. Compare CLAUDE.md declared counts against actual filesystem counts."
- **Constraints**: Read-only. No modifications. Cross-cutting skills (manage-*, delivery, pipeline-resume, task-management, self-improve) are exempt from phase sequence rules.
- **Expected Output**: L1 YAML with relationships_checked, inconsistencies, findings[] (source, target, type, status). L2 relationship graph and phase sequence validation.

### 2. Verify Bidirectionality
For each INPUT_FROM reference A→B:
- Check that B's OUTPUT_TO includes A
- Flag unidirectional references (A claims input from B, but B doesn't output to A)
Similarly for OUTPUT_TO references.

### 3. Check Phase Sequence
Verify domain ordering follows pipeline:
- pre-design → design → research → plan → plan-verify → orchestration → execution → verify
- No backward phase references (e.g., verify outputting to pre-design)
- Cross-cutting skills (manage-*, delivery, pipeline-resume) exempt from sequence

### 4. Verify CLAUDE.md Consistency
Check CLAUDE.md references match filesystem:
- Skills count in S1 matches actual `.claude/skills/` directory count
- Agent count matches `.claude/agents/` file count
- Domain names consistent between CLAUDE.md and skill descriptions

### 5. Generate Consistency Report
Produce relationship matrix:
- All skill pairs with their reference direction
- Bidirectionality status per pair
- Phase sequence violations if any
- CLAUDE.md drift items if any

## Quality Gate
- All INPUT_FROM/OUTPUT_TO references are bidirectional
- Phase sequence has no backward references
- CLAUDE.md counts match filesystem reality
- Zero unresolved inconsistencies

## Output

### L1
```yaml
domain: verify
skill: consistency
status: PASS|FAIL
relationships_checked: 0
inconsistencies: 0
findings:
  - source: ""
    target: ""
    type: INPUT_FROM|OUTPUT_TO
    status: consistent|inconsistent
```

### L2
- Relationship graph with consistency status
- Bidirectionality check results
- Phase sequence logic validation
