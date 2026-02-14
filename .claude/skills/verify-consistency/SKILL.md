---
name: verify-consistency
description: |
  [P8·Verify·Consistency] Cross-file relationship integrity verifier. Checks skill-agent routing relationships match between CLAUDE.md and agent frontmatter, phase sequence logic, INPUT_FROM/OUTPUT_TO bidirectional consistency, skills table matches directory.

  WHEN: After multi-file changes or relationship modifications. Third of 5 verification stages. Can run independently.
  DOMAIN: verify (skill 3 of 5). After verify-content PASS.
  INPUT_FROM: verify-content (content completeness confirmed) or direct invocation.
  OUTPUT_TO: verify-quality (if PASS) or execution domain (if FAIL, fix required).
  ONTOLOGY_LENS: RELATE (how objects connect to each other).

  METHODOLOGY: (1) Extract all INPUT_FROM/OUTPUT_TO references from descriptions, (2) Build relationship graph, (3) Verify bidirectionality (A references B ↔ B references A), (4) Check phase sequence (domain N outputs → domain N+1 inputs), (5) Verify CLAUDE.md skills table matches .claude/skills/ listing.
  OUTPUT_FORMAT: L1 YAML relationship matrix with consistency status, L2 markdown inconsistency report with source/target evidence.
user-invocable: true
disable-model-invocation: false
input_schema:
  type: object
  properties:
    target:
      type: string
      description: "File or directory to verify (default: .claude/)"
  required: []
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
lens: RELATE
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
