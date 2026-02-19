# audit-relational — Methodology Reference

Loaded on-demand by SKILL.md. Contains detailed algorithms, templates, and edge case protocols.

---

## 1. Relationship Graph (DAG) Construction

### Relationship Types to Detect

| Type | Where to Look | Example Declaration |
|------|--------------|---------------------|
| **Data flow** | Skill frontmatter, L2 body | `INPUT_FROM: research-codebase`, `OUTPUT_TO: research-coordinator` |
| **API contract** | Interface definitions, design-interface L2 | `implements: ISkillRunner` |
| **Configuration** | Config files referencing other configs/code | `extends: base-config.json` |
| **Documentation** | Markdown cross-links | `[see audit-static](../audit-static/SKILL.md)` |
| **Transition tables** | Receives From / Sends To sections in skill L2 | Table row listing source or target skill |

### Step-by-Step DAG Construction

For each file in the research-codebase file inventory:

1. Parse YAML frontmatter for `INPUT_FROM`, `OUTPUT_TO`, `domain`, `skill` fields — record all references.
2. Scan the L2 body for `## Transitions` section. Extract all rows from "Receives From" and "Sends To" tables.
3. Extract import statements and API contract references (language-specific syntax).
4. Extract markdown hyperlinks pointing to other `.claude/` files.
5. Record each discovered edge as: `source_file:line → target_file` with type and raw declaration text.

Chain construction (post-collection):
- Build an adjacency list keyed by source file.
- Traverse multi-hop chains (A→B→C) using BFS/DFS to identify complete paths.
- Flag chain breaks: a hop where the intermediate node file does not exist in the inventory.
- Record longest chain length, average chain length, and break count.

---

## 2. Link Evidence Template

Record each relationship with this structure:

```
source:      {relative_file_path}:{line_number}
target:      {relative_file_path}:{line_number}  # "NOT_FOUND" if orphan
direction:   A→B | B→A | bidirectional
type:        data_flow | api_contract | configuration | documentation | transition
declaration: "{exact_text_of_declaration}"
status:      consistent | asymmetric | orphan | stale
severity:    HIGH | MEDIUM | LOW
```

Example — asymmetric transition:
```
source:      .claude/skills/research-codebase/SKILL.md:52
target:      .claude/skills/audit-relational/SKILL.md:179
direction:   A→B
type:        transition
declaration: "| audit-relational | Pattern inventory | Always |"
status:      asymmetric
severity:    MEDIUM
```

Example — orphan reference:
```
source:      .claude/skills/plan-static/SKILL.md:31
target:      .claude/skills/audit-decomp/SKILL.md:NOT_FOUND
direction:   A→B
type:        data_flow
declaration: "INPUT_FROM: audit-decomp"
status:      orphan
severity:    HIGH
```

---

## 3. Asymmetry Detection Algorithm

```
FUNCTION classify_edge(A, B, all_edges):
  reverse = find_edge(B → A, all_edges)
  IF reverse EXISTS:
    RETURN consistent
  ELIF file_exists(B):
    IF B has no relationship declarations at all:
      RETURN stale          # target exists but has no metadata
    ELSE:
      RETURN asymmetric     # target exists, has metadata, but no back-reference
  ELSE:
    RETURN orphan           # target file does not exist

FUNCTION assign_severity(status, edge):
  IF status == orphan AND edge.type IN [data_flow, transition]:
    RETURN HIGH             # breaks active routing
  IF status == asymmetric AND edge.type == data_flow:
    RETURN HIGH             # pipeline coordination failure
  IF status == asymmetric AND edge.type == transition:
    RETURN MEDIUM           # documentation confusion
  IF status == stale:
    RETURN MEDIUM
  IF status == orphan AND edge.type IN [documentation, configuration]:
    RETURN LOW
  RETURN LOW                # default
```

Remediation guidance (document only — do not fix during audit):
- **consistent**: Record as verified. No action needed.
- **asymmetric**: Note which direction is missing. Provide file:line for the existing direction.
- **orphan**: Note expected target path. Likely cause: file renamed or deleted.
- **stale**: Note that target exists but lacks relationship metadata. Likely never updated.

---

## 4. Orphan Classification Rubric

| Status | Definition | Example | Typical Cause |
|--------|-----------|---------|---------------|
| **broken** | Declaration references a path not found in the filesystem | `OUTPUT_TO: audit-decomp` but no such SKILL.md | File deleted or renamed without updating references |
| **missing** | Expected counterpart declaration absent from existing target file | A.OUTPUT_TO:B → B file exists but has no `INPUT_FROM` field at all | Target file never received metadata |
| **asymmetric** | Counterpart field exists but references a different skill, not A | A.OUTPUT_TO:B → B.INPUT_FROM lists C, not A | Incomplete update after refactor |
| **orphan** | File has declarations that reference no other existing file in the inventory | All references in file point to deleted paths | Legacy artifact with no live connections |

Severity override: if a HIGH broken/orphan affects any skill currently listed in CLAUDE.md Phase Definitions, escalate to CRITICAL and flag for immediate repair routing.

---

## 5. DPS Template for Relational Analysts

### COMPLEX Tier — Analyst-1 (Mapper)

```
OBJECTIVE: Map all declared cross-file relationships in the codebase.

CONTEXT (D11 — cognitive focus):
  INCLUDE:
    - research-codebase L1 file inventory (path provided via $ARGUMENTS[0])
    - Naming conventions from research-codebase L2
    - research-external L2 relationship constraints (path via $ARGUMENTS[1])
  EXCLUDE:
    - Other audit dimensions (static/behavioral/impact) — not relevant to this task
    - Pre-design conversation history
    - Full pipeline state beyond P2 research phase

TASK:
  Extract all INPUT_FROM/OUTPUT_TO, Receives From/Sends To,
  import statements, and API contract relationships across all files
  in the provided file inventory.
  Record each relationship using the Link Evidence Template
  (source:line, target:line, direction, type, declaration, status placeholder).

CONSTRAINTS:
  - Read-only analysis. Do not edit any file.
  - No inferred relationships. Only explicitly declared references.
  - maxTurns: 25

OUTPUT: Write to tasks/{team}/p2-audit-relational-map.md
  L1 YAML:
    total_edges: N
    types_found: [data_flow, transition, ...]
  L2:
    Adjacency list with full Link Evidence Template entries per edge.

DELIVERY:
  Ch3: SendMessage(Lead): "PASS|edges:{N}|ref:tasks/{team}/p2-audit-relational-map.md"
  Ch4: SendMessage(Analyst-2): "READY|path:tasks/{team}/p2-audit-relational-map.md|fields:edges,evidence"
```

### COMPLEX Tier — Analyst-2 (Validator)

```
OBJECTIVE: Validate bidirectional consistency of the relationship map produced by Analyst-1.

CONTEXT (D11 — cognitive focus):
  INCLUDE:
    - Analyst-1 relationship map (await Ch4 READY signal, then read path from signal)
    - design-interface L1 API contracts (path via $ARGUMENTS[0])
  EXCLUDE:
    - research-codebase raw file inventory (already processed by Analyst-1)
    - Other audit dimensions

AWAIT: Ch4 signal from Analyst-1 before starting validation.

TASK:
  1. Read Analyst-1 map from tasks/{team}/p2-audit-relational-map.md.
  2. Apply Asymmetry Detection Algorithm to classify each edge:
     consistent | asymmetric | orphan | stale.
  3. Assign severity: HIGH | MEDIUM | LOW per classification rubric.
  4. Compute: integrity_percent = (consistent_count / total_edges) * 100.
  5. Run chain analysis: longest chain, average length, break count.

CONSTRAINTS:
  - Read-only analysis. Do not edit any file.
  - maxTurns: 25

OUTPUT: Write to tasks/{team}/p2-audit-relational.md
  L1 YAML: total_relations, consistent, asymmetric, orphan, broken, integrity_percent
  L2:
    - Complete relationship graph with edge types and directions
    - Bidirectional consistency matrix per relationship pair
    - Integrity issues table sorted by severity (HIGH first)
    - Chain analysis: longest chain, average length, break points
    - Per-issue evidence with file:line references for both sides
    - Summary statistics and integrity percentage

DELIVERY (4-channel D17):
  Ch1: TaskUpdate PT metadata.phase_signals.p2_research:
       "PASS|relations:{N}|broken:{N}"
  Ch2: tasks/{team}/p2-audit-relational.md (already written above)
  Ch3: SendMessage(Lead):
       "PASS|relations:{N}|broken:{N}|ref:tasks/{team}/p2-audit-relational.md"
  Ch4: SendMessage(research-coordinator):
       "READY|path:tasks/{team}/p2-audit-relational.md|fields:graph,issues,integrity_percent"
```

### STANDARD Tier — Single Analyst

Single analyst performs both mapping and validation in one pass.
- maxTurns: 25
- Output path: `tasks/{team}/p2-audit-relational.md`
- DELIVERY: same 4-channel D17 protocol as Analyst-2 above

### TRIVIAL Tier

Lead-direct inline. Check 1-2 files for declared relationships.
No formal DPS. Record findings inline in Lead context.
If any HIGH issues found, immediately route to research-coordinator with findings summary.

---

## 6. Failure Edge Cases

### No Relationship Declarations Found

- **Cause**: Codebase has no cross-file relationship declarations (monolithic file, early-stage project, or no metadata).
- **Action**: Report `relations: 0`. Note that relationship auditing is not applicable to this codebase in its current state. Do not treat as FAIL.
- **Route**: research-coordinator with empty graph and explanation note.
- **Signal**: `"PASS|relations:0|broken:0|ref:tasks/{team}/p2-audit-relational.md"`

### Wave 1 Input Missing

- **Cause**: research-codebase did not produce file inventory, or inventory path is incorrect in $ARGUMENTS.
- **Action**: FAIL immediately. Cannot map relationships without knowing which files exist.
- **Route**: Lead for re-routing to research-codebase.
- **Signal**: `"FAIL|reason:missing_wave1_input|ref:tasks/{team}/p2-audit-relational.md"`

### Too Many Relationships for Turn Budget

- **Cause**: Large codebase with hundreds of cross-file references exceeds analyst turn budget.
- **Action**: Prioritize architecturally significant relationships in this order:
  1. Active pipeline skills (listed in CLAUDE.md Phase Definitions)
  2. API contracts and interface boundaries
  3. Configuration cross-references
  4. Documentation links (lowest priority, skip if budget exhausted)
- **Report**: Mark output as `partial: true` with `coverage_percent` field.
- **Route**: research-coordinator with partial flag.

### Analyst Context Pollution

- **Cause**: Analyst-1 has too many edges in context and begins hallucinating target paths not in the original inventory.
- **Detection trigger**: Any invented file path not present in the research-codebase file inventory.
- **Action**: L2 Respawn with scoped file subset. Split by directory/module boundary.
- **Prevention**: Analyst-1 should validate each target against the file inventory before recording the edge.
