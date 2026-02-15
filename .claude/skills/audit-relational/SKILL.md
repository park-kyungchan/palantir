---
name: audit-relational
description: |
  [P2·Research·Relational] Inventories bidirectional cross-file relationship chains.

  WHEN: After research-codebase AND research-external complete. Wave 2 parallel audit.
  DOMAIN: research (skill 5 of 7). Parallel: static ∥ behavioral ∥ relational ∥ impact.
  INPUT_FROM: research-codebase (file inventory), research-external (pattern constraints), design-architecture (component boundaries).
  OUTPUT_TO: research-coordinator (relationship graph for cross-dimensional consolidation).

  METHODOLOGY: (1) Ingest Wave 1 findings, (2) Map all INPUT_FROM/OUTPUT_TO chains across files, (3) Verify bidirectional consistency (A→B implies B←A), (4) Identify broken/orphan/asymmetric links, (5) Report relationship graph + integrity issues with evidence.
  OUTPUT_FORMAT: L1 YAML relationship summary, L2 markdown integrity report.
user-invocable: false
disable-model-invocation: false
---

# Audit — Relational (Cross-File Relationship Integrity)

## Execution Model
- **STANDARD**: Spawn analyst (maxTurns:25). Systematic chain mapping across all files with declared relationships.
- **COMPLEX**: Spawn 2 analysts. Analyst-1 maps all declared relationships. Analyst-2 validates bidirectionality and identifies orphans.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `/tmp/pipeline/p2-audit-relational.md`, sends micro-signal: `PASS|relations:{N}|broken:{N}|ref:/tmp/pipeline/p2-audit-relational.md`.

## Methodology

### 1. Ingest Wave 1 Findings
Read research-codebase L1/L2 to extract:
- File inventory with all files containing relationship declarations
- Naming conventions and identifier patterns used for cross-references
- Module boundary information (which files belong to which logical groups)

Read research-external L2 for:
- Community constraints on relationship patterns (e.g., circular reference restrictions)
- Known relationship integrity rules for the technology stack

Read design-interface L1/L2 for:
- API contracts that define expected cross-file relationships
- Interface boundaries where relationship chains should start/end

### 2. Map Relationship Chains
For each file containing relationship declarations:
- **Extract outgoing references**: Parse INPUT_FROM, OUTPUT_TO, imports, references, links
- **Record each relationship**: `source_file -> target_file` with relationship type and declaration location (file:line)
- **Chain construction**: Follow multi-hop chains (A->B->C) to build complete relationship paths

Relationship types to detect:
- **Data flow**: INPUT_FROM/OUTPUT_TO declarations (skill files)
- **API contract**: Interface implementation references
- **Configuration**: Config files referencing other configs or code files
- **Documentation**: Cross-references in markdown/docs to other files
- **Transition tables**: Receives From/Sends To declarations in skill files

### 3. Verify Bidirectional Consistency
For each relationship A->B, verify the reverse exists:
- If A declares `OUTPUT_TO: B`, does B declare `INPUT_FROM: A`?
- If A's Sends To table lists B, does B's Receives From table list A?
- If A imports B, is A in B's expected consumers?

Classification of consistency:
| Status | Meaning | Example |
|--------|---------|---------|
| Consistent | Both directions declared | A.OUTPUT_TO:B AND B.INPUT_FROM:A |
| Asymmetric | One direction only | A.OUTPUT_TO:B BUT B missing INPUT_FROM:A |
| Orphan | Target does not exist | A.OUTPUT_TO:X BUT X file not found |
| Stale | Target exists but has no matching declaration | A.OUTPUT_TO:B BUT B has no INPUT_FROM field at all |

### 4. Identify Integrity Issues
Compile all issues found during verification:

**Broken Links**: References to files that do not exist
- File path, declaration location (file:line), expected target

**Orphan Declarations**: Files with INPUT_FROM/OUTPUT_TO pointing to non-existent skills
- File path, orphan reference, likely cause (renamed? deleted?)

**Asymmetric Relationships**: One-directional declarations missing their counterpart
- Source file, target file, which direction is missing, severity

**Chain Breaks**: Multi-hop chains with gaps (A->B->?->D)
- Chain path, break point, files involved

For each issue, assess impact:
- HIGH: Breaks routing or data flow (e.g., skill OUTPUT_TO points to deleted skill)
- MEDIUM: Inconsistency that may cause confusion but does not break execution
- LOW: Cosmetic asymmetry with no functional impact

### 5. Report Relationship Graph and Integrity
Produce final output with:
- Complete relationship graph (all edges with types and directions)
- Bidirectional consistency matrix: per-relationship pair, mark as consistent/asymmetric/orphan/stale
- Integrity issues table sorted by severity (HIGH first)
- Chain analysis: longest chain, average chain length, chain break count
- Summary: total relations, consistent count, broken count, integrity percentage

## Failure Handling

### No Relationship Declarations Found
- **Cause**: Codebase has no cross-file relationship declarations (monolithic file or no metadata)
- **Action**: Report `relations: 0`. Note that relationship auditing is not applicable.
- **Route**: research-coordinator with empty graph

### Wave 1 Input Missing
- **Cause**: research-codebase did not produce file inventory
- **Action**: FAIL. Cannot map relationships without knowing which files exist.
- **Route**: Lead for re-routing to research-codebase

### Too Many Relationships for Turn Budget
- **Cause**: Large codebase with hundreds of cross-file references
- **Action**: Prioritize architecturally significant relationships (skill files, API contracts). Report partial with coverage percentage.
- **Route**: research-coordinator with partial flag

## Anti-Patterns

### DO NOT: Fix Broken Relationships
This is a read-only audit. Even if you discover a broken INPUT_FROM reference, document it as a finding. Do not edit the file to fix it. Fixes belong to execution phase.

### DO NOT: Infer Relationships Not Declared
Only map relationships that are explicitly declared in file content (import statements, frontmatter fields, transition tables). Do not infer that two files are related because they share a naming pattern or are in the same directory.

### DO NOT: Duplicate Dependency Analysis
Import chains and file-level dependencies are audit-static's scope. Relational audit focuses on declared semantic relationships (INPUT_FROM/OUTPUT_TO, API contracts, transition tables), not mechanical import statements.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-codebase | File inventory, naming conventions | L1 YAML: pattern inventory, L2: file list with roles |
| research-external | Relationship pattern constraints | L2: known rules for relationship integrity |
| design-interface | API contracts, interface definitions | L1 YAML: interfaces list, L2: contract specifications |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| research-coordinator | Relationship graph + integrity issues | Always (Wave 2 -> Wave 2.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing Wave 1 input | Lead | Which upstream missing |
| Analyst exhausted | research-coordinator | Partial graph + coverage percentage |
| No relationships found | research-coordinator | Empty graph with explanation |

## Quality Gate
- Every relationship edge has file:line evidence for both source and target declarations
- Bidirectional consistency verified for all relationship pairs
- Integrity issues classified by severity with impact assessment
- No inferred relationships (all edges backed by explicit declarations)
- Coverage metric: relationships verified / total relationships detected
- Chain analysis completed: longest chain, break count reported

## Output

### L1
```yaml
domain: research
skill: audit-relational
total_relations: 0
consistent: 0
asymmetric: 0
orphan: 0
broken: 0
integrity_percent: 100
issues:
  - source: ""
    target: ""
    type: asymmetric|orphan|broken|stale
    severity: HIGH|MEDIUM|LOW
```

### L2
- Complete relationship graph with edge types and directions
- Bidirectional consistency matrix per relationship pair
- Integrity issues table sorted by severity
- Chain analysis: longest chain, average length, break points
- Per-issue evidence with file:line references for both sides
- Summary statistics and integrity percentage
