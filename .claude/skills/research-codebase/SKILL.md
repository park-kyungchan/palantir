---
name: research-codebase
description: >-
  Discovers local codebase patterns via Glob/Grep/Read and documents
  patterns and anti-patterns with file:line references. Tags CC-native
  behavioral claims for shift-left verification via research-cc-verify.
  Parallel with research-external. Use after design domain complete when
  component structure, API contracts, and risk areas are defined.
  Reads from design-architecture component structure,
  design-interface API contracts, and design-risk risk areas.
  Produces pattern inventory with evidence for audit skills,
  plus CC-native claims for research-cc-verify gate.
  On FAIL (scan timeout or pattern conflict), Lead retries L0 with
  narrower scope. After 2 failures, L2 respawn with refined DPS.
  DPS needs design-architecture component list, design-interface API
  contracts, design-risk risk areas. Exclude pre-design conversation
  history and rejected alternatives.
user-invocable: true
disable-model-invocation: true
---

# Research — Codebase

## Execution Model
- **TRIVIAL**: Lead-direct. Quick Glob/Grep for specific patterns.
- **STANDARD**: Spawn analyst. Systematic codebase exploration per architecture area.
- **COMPLEX**: Spawn 2-4 analysts. Each explores non-overlapping codebase areas.

## Methodology

### 1. Identify Research Questions
From architecture decisions, extract questions needing codebase validation:
- "Does pattern X already exist?" → Grep
- "What files handle Y?" → Glob + Read
- "How is Z currently implemented?" → Read + analysis

### 2. Search Strategy
For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: Architecture decisions for this analyst's scope (D11: exclude other analysts' areas, pre-design history, rejected alternatives, full pipeline state; budget ≤30% of context).
- **Task**: "Explore [codebase area] to validate [architecture decisions]. Report all findings with file:line references."
- **Constraints**: Read-only. Glob → Grep → Read sequence. maxTurns: 25. For COMPLEX, stay within assigned directory scope; cross-scope references get file path + reason, not investigation.
- **Expected Output**: Pattern inventory (name, file:line, relevance, reusability) + anti-patterns. COMPLEX: include cross-reference notes for consolidation.
- **Delivery (2-channel)**: Ch2: `tasks/{work_dir}/p2-codebase.md`. Ch3 micro-signal to Lead: `"PASS|patterns:{count}|ref:tasks/{work_dir}/p2-codebase.md"`. Lead passes file path to research-coordinator.

Use tools systematically: 1. **Glob** (file discovery) → 2. **Grep** (pattern matching) → 3. **Read** (detailed analysis).

> Tier-specific DPS templates (TRIVIAL/STANDARD/COMPLEX): read `resources/methodology.md`
> Common codebase pattern types table: read `resources/methodology.md`

### 3. Document Findings
For each finding:
- **Pattern**: What was found (name, description)
- **Location**: file:line reference
- **Relevance**: high/medium/low to architecture decisions
- **Reusability**: Can this be reused or must it be modified?

### 4. Identify Anti-Patterns
Note problematic patterns with file:line locations: code duplication, tight coupling, missing error handling, inconsistent conventions.

### 5. Report Coverage
Map findings to architecture components:
- Components with strong codebase evidence → validated
- Components with no codebase evidence → novel, higher risk

### 6. Tag CC-Native Behavioral Claims
When codebase research discovers patterns related to CC runtime behavior (file structure, persistence, runtime effects, config), tag them explicitly:

**Tagging protocol:** For each discovered CC-native pattern, add a `[CC-CLAIM]` tag with:
- **Claim text**: The behavioral assertion in quotable form
- **Category**: FILESYSTEM | PERSISTENCE | STRUCTURE | CONFIG | BEHAVIORAL
- **Source evidence**: file:line where the pattern was observed
- **Verification need**: What empirical test would confirm/deny this claim

```
[CC-CLAIM] PERSISTENCE: "Task JSON files persist after subagent termination"
Source: ~/.claude/ (observed task files from terminated subagents)
Verification: Read task file for known-terminated subagent, check timestamps
```

These tagged claims become input for research-cc-verify, which runs empirical verification before claims enter ref cache.

## Decision Points

### Search Depth vs Breadth
- **Breadth-first** (default): Glob across all relevant directories first, then Grep. Use when decisions span multiple modules or codebase structure is unfamiliar.
- **Depth-first**: Targeted Grep+Read on specific directories. Use when decisions target a narrow, well-known area.

### Analyst Scope Division (COMPLEX)
- **By directory boundary**: Non-overlapping subtrees (e.g., `src/` vs `.claude/`). Preferred when architecture decisions map to filesystem boundaries.
- **By architecture question**: Each analyst investigates specific questions across the entire codebase. Use for cross-cutting concerns.

### Pattern Conflict Resolution
- **Report all variants**: When conflicting patterns exist, document all with file:line refs and flag as "inconsistent convention."
- **Recommend canonical**: When one pattern dominates (>70% usage), recommend it as canonical; flag minority as cleanup targets.

### Codebase Size Estimation
- **Small (<100 files)**: TRIVIAL. Lead executes directly, no analyst spawn.
- **Medium (100-1000 files)**: STANDARD. Single analyst with full DPS.
- **Large (>1000 files)**: COMPLEX with directory partitioning. Confirm size via Glob `**/*` count before spawning. When in doubt, bias toward STANDARD — over-partitioning wastes coordination overhead.

> ADR priority guidance, pre-existing knowledge check, escalation-to-design conditions: read `resources/methodology.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Scan timeout, tool error, permission denied | L0 Retry | Re-invoke same analyst, same DPS |
| Incomplete findings or off-scope patterns returned | L1 Nudge | Respawn with refined DPS targeting narrower scope or refined search questions |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh analyst with refined DPS and narrower directory scope |
| Pattern conflict breaks ADR assumptions, scope shift discovered | L3 Restructure | Split scope, modify task graph, reassign directory boundaries |
| 3+ L2 failures or fundamental ADR contradiction requiring design revision | L4 Escalate | AskUserQuestion with contradiction evidence and options |

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`
> Failure severity classification and routing rules: read `resources/methodology.md`

## Anti-Patterns

- **Grep without Glob first**: Leads to irrelevant matches and missed files. Always Glob first to establish search scope.
- **No file:line references**: Abstract findings like "uses factory pattern" are not actionable. Every pattern needs a concrete file:line.
- **Modify files during research**: Read-only. Document bugs as findings; let execution-code handle fixes.
- **Duplicate pre-design research**: Read P0 output before spawning analysts. Focus on architecture-specific questions not answered in P0.
- **No scope limits**: Scope searches to relevant directories. Exclude `node_modules/`, `.git/`, build artifacts.
- **File count as pattern count**: Count unique conventions, not raw file matches. 15 files with the same error shape = 1 error-handling pattern.
- **Evidence as recommendation**: Findings are descriptive. "Pattern X exists in 8/12 modules" is research. "Adopt pattern X" is design.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`
> D17 Note: use 2-channel protocol (Ch2 output file `tasks/{work_dir}/`, Ch3 micro-signal to Lead).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|---|---|---|
| design-architecture | Architecture decisions needing codebase validation | L1 YAML: `components[]` with names and dependencies, L2: ADRs with technology choices |
| design-interface | Interface definitions referencing existing contracts | L1 YAML: `interfaces[]`, L2: method signatures to validate against codebase |
| design-risk | Risk areas needing focused codebase research | L1 YAML: `risk_areas[]` with severity, L2: investigation priorities |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| audit-static | Codebase dependency patterns and file inventory | Always (Wave 1 → Wave 2 parallel audits) |
| audit-behavioral | Existing behavior patterns and implementations | Always |
| audit-relational | Cross-file relationship patterns and references | Always |
| audit-impact | Change propagation evidence from codebase | Always |

### Failure Routes
| Failure Type | Route To | Data Passed |
|---|---|---|
| No patterns found | audit-* (all 4 audits) | Empty inventory with "novel" flags per architecture decision |
| Analyst exhausted | audit-* (all 4 audits) | Partial findings + uncovered area list |
| Critical gap in architecture | design-architecture | Gap description requiring architecture revision (COMPLEX feedback loop) |

## Quality Gate
- Every architecture decision has ≥1 codebase finding or explicit "novel" flag
- All findings have file:line references
- Anti-patterns documented with specific locations
- Pattern count reflects unique conventions, not raw file matches
- No prescriptive recommendations in findings (evidence only)
- COMPLEX: All analyst scopes covered, cross-references resolved
- If `escalate_to_design: true`, escalation_reason is detailed and threshold criteria documented
- CC-native behavioral claims tagged with [CC-CLAIM] and categorized (if any discovered)

## Output

### L1
```yaml
domain: research
skill: codebase
pattern_count: 0
file_count: 0
escalate_to_design: false
escalation_reason: ""
cc_native_claims: 0
patterns:
  - name: ""
    files: []
    relevance: high|medium|low
    reusability: reuse|modify|replace
novel_decisions:
  - adr: ""
    reason: "no existing pattern found"
uncovered_areas:
  - area: ""
    reason: "analyst maxTurns exhausted"
pt_signal: "metadata.phase_signals.p2_research"
signal_format: "PASS|patterns:{count}|cc_claims:{n}|ref:tasks/{work_dir}/p2-codebase.md"
```

### L2
- Pattern inventory with file:line references per architecture decision
- Convention analysis: dominant patterns, minority variants, inconsistencies
- Anti-patterns and technical debt noted with severity and location
- Reusable components identified with modification requirements
- Cross-reference notes (COMPLEX only): inter-analyst findings resolved
- Novel decision rationale: why no codebase evidence was found
- Escalation details (if applicable): contradiction evidence with file:line proof
- CC-native claims tagged for verification (for research-cc-verify routing)
