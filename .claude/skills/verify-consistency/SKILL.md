---
name: verify-consistency
description: |
  [P8·Verify·Consistency] Cross-file relationship integrity verifier. Checks coordinator-worker relationships match between CLAUDE.md and agent frontmatter, phase sequence logic, INPUT_FROM/OUTPUT_TO bidirectional consistency, skills table matches directory.

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
