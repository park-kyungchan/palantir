# Research Codebase — Detailed Methodology

> On-demand reference. Contains tier-specific DPS templates, common pattern types table, architecture decision priority guide, and severity classification.

## Tier-Specific DPS Templates

### TRIVIAL — Lead Executes Directly (no analyst spawn)
```
Glob for [pattern]. Grep in results for [convention]. Read top 3 matches.
Report: file:line + relevance to [architecture decision].
```
Lead performs these steps inline using its own tool access. Suitable when scope is 1-2 directories and 1-2 architecture decisions. Total effort: 3-5 tool calls.

### STANDARD — Single Analyst
```
Context: [Paste architecture decisions verbatim from design-architecture L1/L2]
Task: Explore [codebase area] to validate [all architecture decisions]. For each decision,
  find existing patterns, conventions, and reusable components. Report all findings with
  file:line references.
Constraints: Read-only. Glob -> Grep -> Read sequence. maxTurns: 25.
Expected Output: Pattern inventory (name, file:line, relevance, reusability) +
  anti-patterns with locations.
Delivery: Write output to tasks/{team}/p2-codebase.md. Send micro-signal to Lead via
  SendMessage: "PASS|patterns:{count}|ref:tasks/{team}/p2-codebase.md".
```
Single analyst receives all research questions. Lead consolidates output into research-audit input.

### COMPLEX — 2-4 Analysts with Partitioned Scope
```
Context (D11 priority: cognitive focus > token efficiency):
  INCLUDE: Architecture decisions for this analyst's scope (design-architecture component list,
    design-interface contracts, design-risk risk areas for this scope). File paths within
    assigned directory.
  EXCLUDE: Other analysts' scope areas. Pre-design history. Rejected alternatives. Full pipeline state.
  Budget: Context field ≤ 30% of effective context budget.
Task: Explore [specific directory subtree] to validate [subset of architecture decisions].
  Report findings with file:line references.
Constraints: Read-only. Stay within assigned directory scope. maxTurns: 25. If findings reference
  files outside your scope, note with file path and reason -- another analyst covers that area.
Expected Output: Pattern inventory for your scope + cross-reference notes for consolidation.
Delivery: Write output to tasks/{team}/p2-codebase.md. Send micro-signal to Lead:
  "PASS|patterns:{count}|ref:tasks/{team}/p2-codebase.md".
```
Lead merges outputs from all analysts: resolve cross-references, deduplicate patterns. Cross-reference resolution is Lead's responsibility, not analysts'.

## Common Codebase Pattern Types

| Pattern Type | Search Method | What It Reveals | Example |
|---|---|---|---|
| File structure | Glob `**/*.{ts,py,md}` | Directory layout, naming conventions, module boundaries | `src/auth/`, `lib/utils/` |
| Import/dependency | Grep `import.*from\|require\(` | Module dependency graph, coupling | Circular imports, shared utilities |
| Config conventions | Glob `*.{json,yaml,toml,env}` | Configuration patterns, environment handling | `.env` vs `config.yaml` vs hardcoded |
| Error handling | Grep `try.*catch\|except\|\.catch\|Error` | Error handling style consistency | Centralized vs per-function |
| Test structure | Glob `**/*.test.*\|**/*.spec.*\|**/test_*` | Test file conventions, coverage patterns | Co-located vs separate test dirs |
| Hook/plugin patterns | Glob `.claude/hooks/*\|plugins/*` | Extension points, lifecycle hooks | Hook naming, event handling |
| Type definitions | Grep `interface\|type\|class\|struct` | Type system usage, data modeling style | DTO patterns, domain models |
| Logging | Grep `console\.\|logger\.\|log\.` | Logging conventions, observability | Structured vs unstructured |
| API patterns | Grep `app\.(get\|post\|put)\|@(Get\|Post)` | API design style, routing conventions | REST vs RPC, middleware |
| State management | Grep `useState\|createStore\|redux\|zustand` | State management approach | Global vs local state |

**Usage guidance**: For STANDARD DPS, include 3-5 relevant pattern types. For COMPLEX with multiple analysts, assign pattern types per analyst to avoid overlapping searches. Always include "file structure" as the first search — it scopes all subsequent patterns.

## Architecture Decision Priority

When architecture has >5 ADRs, prioritize:
1. **Critical-path ADRs**: Block the most downstream tasks → deep research (Glob + Grep + Read)
2. **High-risk ADRs**: Flagged by design-risk as high uncertainty/impact → cross-reference risk output
3. **Technology-choice ADRs**: Library/framework selection → benefit most from existing usage patterns
4. **Nice-to-have ADRs**: Cosmetic or low-impact → shallow research (Glob count only) or defer to plan

For time-constrained scenarios (turns running low): stop after category 2, report remaining as "not researched — low priority."

## Pre-existing Knowledge Check

Before spawning analysts, check whether research-codebase was already executed:
- **Pipeline-resume**: Check PT metadata for `research.codebase.pattern_count > 0` or prior output file. Spawn targeted follow-up for gaps only.
- **Design feedback loop**: COMPLEX pipelines may loop back through research after architecture revision. Second pass focuses only on revised decisions, not full rescan.

## Failure Severity Classification

| Failure | Severity | Blocking? | Route |
|---------|----------|-----------|-------|
| No patterns for critical ADR | HIGH | No (increases risk) | audit-* (all 4) with `novel` flag per ADR |
| Critical ADR contradicted by codebase | HIGH | Conditional | design-architecture if fundamental; audit-* otherwise |
| Analyst maxTurns exhausted | MEDIUM | No | audit-* (all 4) with partial findings + uncovered area list |
| Contradictory patterns found | MEDIUM | No | audit-* (all 4) with contradiction report |
| File read permission error | LOW | No | Skip file, note in findings, continue |

All failure types route to the 4 audit skills (audit-static, audit-behavioral, audit-relational, audit-impact) regardless of severity. Exception: fundamental ADR contradiction escalates to design-architecture (see Decision Points: When to Escalate to Design).

**Pipeline Impact**: Research failures are non-blocking. Missing codebase evidence increases risk rating in plan-behavioral but does not halt pipeline. Absence of evidence ≠ evidence of absence.
