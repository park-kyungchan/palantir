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
disable-model-invocation: false
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
- **Context**: Paste the relevant architecture decisions (design-architecture L1 `components[]` list + specific L2 sections for this analyst's scope). Include the research questions from Step 1 that this analyst must answer verbatim.
- **Task**: "Explore [specific codebase area, e.g., `src/auth/**`, `.claude/skills/`] to validate [specific architecture decisions]. For each decision, find existing patterns, conventions, and reusable components. Report all findings with file:line references."
- **Scope**: Explicit directory/file glob patterns to search. For COMPLEX, assign non-overlapping areas per analyst (e.g., analyst-1: `src/`, analyst-2: `.claude/`).
- **Constraints**: Read-only analysis. No file modifications. Use Glob → Grep → Read sequence systematically.
- **Expected Output**: Pattern inventory as structured list: pattern name, file:line location, relevance (high/medium/low), reusability assessment. Anti-patterns with specific file:line locations.
- **Delivery**: Write full output to tasks/{team}/p2-codebase.md. Send micro-signal to Lead via SendMessage: "PASS|patterns:{count}|ref:tasks/{team}/p2-codebase.md".

Use tools systematically:
1. **Glob** for file discovery: `**/*.md`, `**/*.ts`, specific paths
2. **Grep** for pattern matching: function names, imports, config keys
3. **Read** for detailed analysis: understand implementation, not just find it

#### Tier-Specific DPS Templates

**TRIVIAL DPS** -- Lead executes directly, no analyst spawn:
> Glob for `[pattern]`. Grep in results for `[convention]`. Read top 3 matches.
> Report: file:line + relevance to `[architecture decision]`.

Lead performs these steps inline using its own tool access. Suitable when the search scope is 1-2 directories and 1-2 architecture decisions. Total effort: 3-5 tool calls.

**STANDARD DPS** -- Single analyst with full delegation:
> Context: [Paste architecture decisions verbatim from design-architecture L1/L2]
> Task: Explore [codebase area] to validate [all architecture decisions]. For each decision, find existing patterns, conventions, and reusable components. Report all findings with file:line references.
> Constraints: Read-only. Glob -> Grep -> Read sequence. maxTurns: 25.
> Expected Output: Pattern inventory (name, file:line, relevance, reusability) + anti-patterns with locations.
> Delivery: Write output to tasks/{team}/p2-codebase.md. Send micro-signal to Lead via SendMessage: "PASS|patterns:{count}|ref:tasks/{team}/p2-codebase.md".

Single analyst receives all research questions. Lead consolidates output directly into research-audit input format.

**COMPLEX DPS** -- 2-4 analysts with partitioned scope:
> Context (D11 priority: cognitive focus > token efficiency):
>   INCLUDE: Architecture decisions for this analyst's scope (design-architecture component list, design-interface contracts, design-risk risk areas for this scope). File paths within assigned directory.
>   EXCLUDE: Other analysts' scope areas. Pre-design conversation history. Rejected design alternatives. Full pipeline state.
>   Budget: Context field ≤ 30% of effective context budget.
> Task: Explore [specific directory subtree, e.g., `src/auth/`] to validate [subset of architecture decisions]. Report findings with file:line references.
> Constraints: Read-only. Stay within assigned directory scope. maxTurns: 25. If your findings reference files outside your scope, note the cross-reference with file path and reason -- another analyst will cover that area.
> Expected Output: Pattern inventory for your scope + cross-reference notes for consolidation.
> Delivery: Write output to tasks/{team}/p2-codebase.md. Send micro-signal to Lead via SendMessage: "PASS|patterns:{count}|ref:tasks/{team}/p2-codebase.md".

Lead must merge outputs from all analysts, resolving cross-references and deduplicating patterns found independently by multiple analysts. Cross-reference resolution is Lead's responsibility, not the analysts'.

### 3. Document Findings
For each finding:
- **Pattern**: What was found (name, description)
- **Location**: file:line reference
- **Relevance**: high/medium/low to architecture decisions
- **Reusability**: Can this be reused or must it be modified?

### 4. Identify Anti-Patterns
Note problematic patterns that architecture should avoid:
- Code duplication
- Tight coupling
- Missing error handling
- Inconsistent conventions

### 5. Report Coverage
Map findings to architecture components:
- Components with strong codebase evidence → validated
- Components with no codebase evidence → novel, higher risk

### 6. Tag CC-Native Behavioral Claims

When codebase research discovers patterns related to CC runtime behavior, tag them explicitly for verification:

**What constitutes a CC-native behavioral claim:**
- File structure assertions: "X file exists at Y path", "directory Z has layout W"
- Persistence assertions: "X survives compaction/termination/restart"
- Runtime behavior: "feature X triggers Y", "setting Z produces effect W"
- Configuration effects: "field X accepts values Y", "setting Z enables feature W"

**Tagging protocol:**
For each discovered CC-native pattern, add a `[CC-CLAIM]` tag in the findings with:
- **Claim text**: The behavioral assertion in quotable form
- **Category**: FILESYSTEM | PERSISTENCE | STRUCTURE | CONFIG | BEHAVIORAL
- **Source evidence**: file:line where the pattern was observed
- **Verification need**: What empirical test would confirm/deny this claim

**Example:**
```
[CC-CLAIM] PERSISTENCE: "Inbox JSON files persist after agent termination"
Source: ~/.claude/teams/*/inboxes/*.json (observed files from terminated agents)
Verification: Read inbox file for known-terminated agent, check message timestamps
```

These tagged claims become input for research-cc-verify, which runs the empirical verification before claims enter ref cache.

## Common Codebase Patterns Reference

When constructing analyst DPS prompts, include relevant search patterns from this table. Lead selects patterns based on architecture decision types -- not all patterns apply to every research task.

| Pattern Type | Search Method | What It Reveals | Example |
|---|---|---|---|
| File structure | Glob `**/*.{ts,py,md}` | Directory layout, naming conventions, module boundaries | `src/auth/`, `lib/utils/` |
| Import/dependency | Grep `import.*from\|require\(` | Module dependency graph, coupling between components | Circular imports, shared utilities |
| Config conventions | Glob `*.{json,yaml,toml,env}` | Configuration patterns, environment handling | `.env` vs `config.yaml` vs hardcoded |
| Error handling | Grep `try.*catch\|except\|\.catch\|Error` | Error handling style consistency | Centralized vs per-function error handling |
| Test structure | Glob `**/*.test.*\|**/*.spec.*\|**/test_*` | Test file conventions, coverage patterns | Co-located vs separate test directories |
| Hook/plugin patterns | Glob `.claude/hooks/*\|plugins/*` | Extension points, lifecycle hooks | Hook naming, event handling conventions |
| Type definitions | Grep `interface\|type\|class\|struct` | Type system usage, data modeling style | DTO patterns, domain models |
| Logging | Grep `console\.\|logger\.\|log\.` | Logging conventions, observability | Structured vs unstructured logging |
| API patterns | Grep `app\.(get\|post\|put)\|@(Get\|Post)` | API design style, routing conventions | REST vs RPC, middleware patterns |
| State management | Grep `useState\|createStore\|redux\|zustand` | State management approach | Global vs local state patterns |

**Usage guidance**: For a typical STANDARD DPS, include 3-5 relevant pattern types. For COMPLEX with multiple analysts, assign pattern types per analyst to avoid overlapping searches. Always include "file structure" as the first search -- it scopes all subsequent patterns.

## Decision Points

### Search Depth vs Breadth
- **Breadth-first** (default): Glob across all relevant directories first, then Grep for key patterns. Use when architecture decisions span multiple modules or when codebase structure is unfamiliar.
- **Depth-first**: Focus on specific directories with targeted Grep+Read. Use when architecture decisions target a narrow, well-known area (e.g., "how does the existing hook system work?").

### Analyst Scope Division (COMPLEX)
- **By directory boundary**: Each analyst owns a non-overlapping directory subtree (e.g., `src/` vs `.claude/`). Preferred when architecture decisions naturally map to filesystem boundaries.
- **By architecture question**: Each analyst investigates a specific set of architecture questions across the entire codebase. Use when questions are cross-cutting (e.g., "find all error handling patterns" spans multiple directories).

### Pattern Conflict Resolution
- **Report all variants**: When conflicting patterns exist (e.g., two different error handling styles), document all with file:line refs and flag as "inconsistent convention."
- **Recommend canonical**: When one pattern dominates (>70% usage), recommend it as canonical and flag the minority as potential cleanup targets.

### Codebase Size Estimation
Lead estimates search scope before choosing tier and analyst configuration:
- **Small (<100 files)**: TRIVIAL treatment. Lead can handle directly with Glob+Grep. No analyst spawn needed. Typical for micro-services, single-module projects, or scoped searches within a known subdirectory.
- **Medium (100-1000 files)**: STANDARD treatment. Single analyst with full DPS. Broad enough to benefit from systematic exploration but manageable within one analyst's turn budget.
- **Large (>1000 files)**: COMPLEX treatment with directory partitioning. Assign each analyst a non-overlapping directory subtree. Use `find -type f | wc -l` equivalent (Glob `**/*` count) to confirm size before spawning.

When in doubt, bias toward STANDARD. Over-partitioning a medium codebase wastes coordination overhead. Under-partitioning a large codebase wastes analyst turns on irrelevant files.

### Pre-existing Knowledge Check
Before spawning analysts, Lead checks whether research-codebase was already executed in this pipeline run. This applies in two scenarios:
- **Pipeline-resume**: If the pipeline was interrupted and resumed, previous research findings may exist in the PERMANENT task metadata. Read PT before spawning to avoid duplicate work. Spawn targeted follow-up for gaps only.
- **Design feedback loop**: In COMPLEX pipelines, design-architecture may loop back through research after revision. The second research pass should focus only on the revised architecture decisions, not repeat the full scan.

Detection method: Check PT metadata for `research.codebase.pattern_count > 0` or existence of prior research-codebase output. If found, extract the list of already-answered questions and exclude them from the new analyst DPS.

### Architecture Decision Priority
When architecture has many decisions (>5 ADRs), not all can receive equal research depth within analyst turn budgets. Prioritize:
1. **Critical-path ADRs**: Decisions that block the most downstream tasks. These get deep research (Glob + Grep + Read).
2. **High-risk ADRs**: Decisions flagged by design-risk as having high uncertainty or high impact. Cross-reference with risk assessment output.
3. **Technology-choice ADRs**: Decisions involving library/framework selection benefit most from codebase evidence (existing usage patterns, version compatibility).
4. **Nice-to-have ADRs**: Cosmetic or low-impact decisions. These get shallow research (Glob count only) or are deferred to plan phase.

For time-constrained scenarios (analyst turns running low), stop after category 2 and report remaining ADRs as "not researched -- low priority" in the output.

### When to Escalate to Design
Normal flow: research findings go to research-audit, then to plan. But one scenario requires escalation back to design-architecture:
- **Condition**: Codebase evidence strongly contradicts an architecture decision. Not merely "the pattern is novel" (which is expected) but "the existing codebase does the exact opposite of what the ADR prescribes, and the existing approach is deeply embedded."
- **Example**: ADR says "use event-driven architecture" but codebase has synchronous request-response patterns in 90%+ of modules with no event infrastructure.
- **Threshold**: Contradiction must be (a) fundamental (not surface-level naming differences), (b) widespread (>70% of relevant codebase), and (c) costly to overcome (not a simple refactor).
- **Action**: Add `escalate_to_design: true` in L1 output with `escalation_reason` in L2. Route to design-architecture for ADR revision before continuing to plan.
- **Non-escalation**: If the contradiction is localized (<30% of codebase) or easily overridden, report it as a finding but do not escalate. Let plan-behavioral handle the migration approach.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Scan timeout, tool error, permission denied | L0 Retry | Re-invoke same analyst, same DPS |
| Incomplete findings or off-scope patterns returned | L1 Nudge | SendMessage with narrower scope or refined search questions |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh analyst with refined DPS and narrower directory scope |
| Pattern conflict breaks ADR assumptions, scope shift discovered | L3 Restructure | Split scope, modify task graph, reassign directory boundaries |
| 3+ L2 failures or fundamental ADR contradiction requiring design revision | L4 Escalate | AskUserQuestion with contradiction evidence and options |

### Severity Classification

| Failure | Severity | Blocking? | Route |
|---------|----------|-----------|-------|
| No patterns found for critical ADR | HIGH | No (increases risk) | audit-* (all 4 audits) with `novel` flag per ADR |
| Critical ADR contradicted by codebase | HIGH | Conditional | design-architecture if fundamental; audit-* otherwise |
| Analyst maxTurns exhausted | MEDIUM | No | audit-* (all 4 audits) with partial findings + uncovered area list |
| Contradictory patterns found | MEDIUM | No | audit-* (all 4 audits) with contradiction report (all variants, file:line refs) |
| File read permission error | LOW | No | Skip file, note in findings, continue search |

### Routing After Failure
All failure types route to the 4 audit skills (audit-static, audit-behavioral, audit-relational, audit-impact) regardless of severity. Each audit receives the full findings and extracts its dimensional subset. The only exception is the conditional escalation for fundamental ADR contradictions -- see Decision Points: When to Escalate to Design.

### Pipeline Impact
Research failures are non-blocking. Missing codebase evidence increases the risk rating in plan-behavioral but does not halt the pipeline. The rationale: absence of evidence is not evidence of absence. A pattern may exist but be difficult to find, or the codebase area may genuinely be novel territory.

## Anti-Patterns

### DO NOT: Grep Without Glob First
Jumping straight to Grep without understanding directory structure leads to irrelevant matches and missed files. Always Glob first to establish the search scope, then Grep within that scope.

### DO NOT: Report Patterns Without File:Line References
Abstract findings like "the codebase uses factory pattern" are not actionable. Every pattern must have at least one concrete file:line reference that downstream skills can validate.

### DO NOT: Modify Files During Research
This is a read-only skill. Even if you discover a bug or typo, do NOT fix it. Document it as a finding and let execution-code handle the fix through the proper pipeline.

### DO NOT: Duplicate Research Already Done in Pre-Design
Pre-design-feasibility may have done basic codebase checks. Read its output before spawning analysts to avoid re-discovering the same patterns. Focus on architecture-specific questions not answered in P0.

### DO NOT: Search Entire Repository Without Scope Limits
For large codebases, searching everything wastes analyst turns. Use architecture decisions to scope searches to relevant directories. Exclude `node_modules/`, `.git/`, build artifacts.

### DO NOT: Treat File Count as Pattern Count
Finding 20 files matching a glob is not the same as finding 20 patterns. A pattern is a reusable convention confirmed by consistent usage across multiple locations. Multiple files may exhibit the same single pattern. When reporting `pattern_count`, count unique conventions -- not raw file matches. Example: 15 files all using `try/catch` with the same error shape is 1 error-handling pattern, not 15.

### DO NOT: Confuse Codebase Evidence with Recommendation
Research documents what exists in the codebase. It does not recommend what should be built. Statements like "the codebase should adopt pattern X" belong to the design domain. Research provides evidence for or against design decisions -- e.g., "pattern X exists in 8/12 modules (67% adoption)" is research; "adopt pattern X for the new module" is design. Keep findings descriptive, not prescriptive.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| design-architecture | Architecture decisions needing codebase validation | L1 YAML: `components[]` with names and dependencies, L2: ADRs with technology choices |
| design-interface | Interface definitions referencing existing contracts | L1 YAML: `interfaces[]`, L2: method signatures to validate against codebase |
| design-risk | Risk areas needing focused codebase research | L1 YAML: `risk_areas[]` with severity, L2: investigation priorities |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| audit-static | Codebase dependency patterns and file inventory | Always (Wave 1 → Wave 2 parallel audits) |
| audit-behavioral | Existing behavior patterns and implementations | Always (Wave 1 → Wave 2 parallel audits) |
| audit-relational | Cross-file relationship patterns and references | Always (Wave 1 → Wave 2 parallel audits) |
| audit-impact | Change propagation evidence from codebase | Always (Wave 1 → Wave 2 parallel audits) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| No patterns found | audit-* (all 4 audits) | Empty inventory with "novel" flags per architecture decision |
| Analyst exhausted | audit-* (all 4 audits) | Partial findings + uncovered area list |
| Critical gap in architecture | design-architecture | Gap description requiring architecture revision (COMPLEX feedback loop) |

## Quality Gate
- Every architecture decision has >=1 codebase finding or explicit "novel" flag
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
signal_format: "PASS|patterns:{count}|cc_claims:{n}|ref:tasks/{team}/p2-codebase.md"
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
