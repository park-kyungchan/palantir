---
name: audit-relational
description: >-
  Inventories bidirectional cross-file relationship chains.
  Verifies A-to-B implies B-to-A consistency, identifies broken,
  orphan, and asymmetric links. Parallel with audit-static,
  audit-behavioral, and audit-impact. Use after research-codebase
  and research-external complete. Reads from research-codebase
  file inventory, research-external pattern constraints, and
  design-interface API contracts. Produces relationship summary
  and integrity report with link evidence for
  research-coordinator. On FAIL, Lead applies D12 escalation
  ladder. DPS needs research-codebase file inventory and naming
  conventions, research-external relationship constraints, and
  design-interface API contracts. Exclude static dependency
  graph, behavioral predictions, and pre-design conversation
  history.
user-invocable: false
disable-model-invocation: false
---

# Audit — Relational (Cross-File Relationship Integrity)

## Execution Model
- **TRIVIAL**: Lead-direct. Inline check of 1-2 file relationship declarations. No agent spawn. maxTurns: 0.
- **STANDARD**: Spawn analyst (maxTurns:25). Systematic chain mapping across all files with declared relationships.
- **COMPLEX**: Spawn 2 analysts (maxTurns:25 each). Analyst-1 maps all declared relationships. Analyst-2 validates bidirectionality and identifies orphans.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Decision Points

### Relationship Scan Scope
Based on file inventory from research-codebase L1.
- **≤20 files**: Single analyst, full scan. maxTurns: 20.
- **21-60 files**: Single analyst, prioritize skill files and API contracts. maxTurns: 25.
- **>60 files**: 2 analysts — Analyst-1 maps, Analyst-2 validates. maxTurns: 25 each.
- **Default**: Single analyst (STANDARD tier).

### Bidirectional Rule
A→B implies B→A. If A declares `OUTPUT_TO: B`, B must declare `INPUT_FROM: A`.
If A's Sends To table lists B, B's Receives From table must list A.

### Issue Severity
- **HIGH**: Breaks routing or data flow (e.g., `OUTPUT_TO` points to deleted skill).
- **MEDIUM**: Inconsistency causing documentation confusion; does not break execution.
- **LOW**: Cosmetic asymmetry with no functional impact.

> Classification rubric and asymmetry detection algorithm: read `resources/methodology.md`

## Methodology

1. **Ingest Wave 1 Findings**: Read research-codebase L1/L2 for file inventory and naming conventions. Read research-external L2 for relationship constraints. Read design-interface L1/L2 for API contracts.
2. **Map Relationship Chains**: Extract outgoing references (INPUT_FROM, OUTPUT_TO, imports, transition tables, documentation links) per file. Record each as `source:line → target` with type and declaration text.
3. **Verify Bidirectional Consistency**: For each A→B, verify reverse exists. Classify each pair as consistent / asymmetric / orphan / stale.
4. **Identify Integrity Issues**: Compile broken links, orphan declarations, asymmetric relationships, and chain breaks. Assign severity (HIGH/MEDIUM/LOW) per impact on active routing.
5. **Report Relationship Graph**: Produce complete graph, consistency matrix, issues table sorted by severity, chain analysis, and summary statistics.

> DPS construction guide: read `.claude/resources/dps-construction-guide.md`
> DAG construction steps, link evidence template, DPS template: read `resources/methodology.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error during relationship scan | L0 | Re-invoke same analyst, same scope |
| Incomplete chain mapping / missing files | L1 | SendMessage with refined file scope |
| Analyst exhausted turns before full validation | L2 | Kill → fresh analyst with refined DPS |
| Multi-analyst scope conflict | L3 | Modify analyst boundaries, reassign relationship sets |
| Strategic ambiguity / 3+ L2 failures | L4 | AskUserQuestion with options |

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`
> Edge cases (no declarations, missing Wave 1 input, turn budget exceeded): read `resources/methodology.md`

## Anti-Patterns

- **DO NOT fix broken relationships**: Read-only audit only. Document findings; fixes belong to the execution phase.
- **DO NOT infer undeclared relationships**: Only map explicitly declared references (frontmatter fields, import statements, transition tables). No naming-pattern or directory-proximity inference.
- **DO NOT duplicate dependency analysis**: Import chains and file-level coupling are audit-static scope. Focus on declared semantic relationships (INPUT_FROM/OUTPUT_TO, API contracts, transition tables).

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-codebase | File inventory, naming conventions | L1 YAML: pattern inventory; L2: file list with roles |
| research-external | Relationship pattern constraints | L2: known rules for relationship integrity |
| design-interface | API contracts, interface definitions | L1 YAML: interfaces list; L2: contract specifications |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| research-coordinator | Relationship graph + integrity issues | Always (Wave 2 → Wave 2.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing Wave 1 input | Lead | Which upstream skill is missing |
| Analyst exhausted | research-coordinator | Partial graph + coverage percentage |
| No relationships found | research-coordinator | Empty graph with explanation |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 `tasks/{team}/`, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- Every relationship edge has file:line evidence for both source and target declarations
- Bidirectional consistency verified for all relationship pairs
- Integrity issues classified by severity with impact assessment
- No inferred relationships (all edges backed by explicit declarations)
- Coverage metric reported: relationships verified / total relationships detected
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
pt_signal: "metadata.phase_signals.p2_research"
signal_format: "PASS|relations:{N}|broken:{N}|ref:tasks/{team}/p2-audit-relational.md"
```

### L2
- Complete relationship graph with edge types and directions
- Bidirectional consistency matrix per relationship pair
- Integrity issues table sorted by severity
- Chain analysis: longest chain, average length, break points
- Per-issue evidence with file:line references for both sides
- Summary statistics and integrity percentage
