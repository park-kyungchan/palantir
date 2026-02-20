# Infra-Implementer Agent Memory

## Progressive Disclosure Pattern (confirmed 2026-02-19)

Standard 3-Stage Progressive Disclosure for SKILL.md optimization:
1. L2 (SKILL.md body): ≤200 lines. Execution Model, Decision Points, Methodology (condensed), Failure table, Anti-Patterns, Transitions, Quality Gate, Output.
2. resources/methodology.md: Moved content — DPS INCLUDE/EXCLUDE blocks, tool-profile matrix, assignment format tables, split rules, failure sub-cases.
3. .claude/resources/ links: phase-aware-execution.md, failure-escalation-ladder.md, dps-construction-guide.md, output-micro-signal-format.md, transitions-template.md, quality-gate-checklist.md.

### What to KEEP in SKILL.md L2
- model:sonnet rule + MCP→general-purpose rule (brief inline)
- Agent selection decision tree (numbered 1-5 priority list)
- Multi-capability task splitting rules (criteria, not tables)
- Failure handling table (L0-L4 rows)
- Anti-patterns (4 rules)
- Transitions tables (source/sends/failure routes)
- Quality gate bullets
- Output L1 YAML spec

### What to MOVE to resources/methodology.md
- DPS template INCLUDE/EXCLUDE/Budget blocks
- Tool-profile matrix table (B/C/D/E/F/G with tool lists)
- Assignment matrix format (T1/T2 example rows)
- Parallelism-optimized splitting table + DO/DO NOT rules
- Failure sub-cases (verbose prose per failure type)

## File Creation Pattern
- Always read existing SKILL.md before editing
- Create resources/ directory by creating resources/methodology.md (no shell commands available)
- Verify final line count matches target constraint

## Completed Skill Optimizations

| Skill | Before | After | methodology.md | Date |
|-------|--------|-------|----------------|------|
| plan-verify-static | 238L | 155L | 119L | 2026-02-19 |
| plan-relational | 238L | 188L | 107L | 2026-02-19 |
| execution-infra | 233L | 195L | 77L | 2026-02-19 |
| execution-code | 232L | 193L | 58L | 2026-02-19 |
| orchestrate-impact | 310L | 154L | 165L | 2026-02-19 |
| self-diagnose | 228L | 190L | 65L | 2026-02-19 |
| manage-infra | 300L | 200L | 116L | 2026-02-19 |
| rsil | 357L | 180L | 202L | 2026-02-19 |
| pipeline-resume | 300L | 181L | 153L | 2026-02-19 |
| verify-consistency | 330L | 200L | 131L | 2026-02-19 |
| execution-cascade | 323L | 199L | 157L | 2026-02-19 |
| manage-codebase | 276L→rewrite | 175L | 119L | 2026-02-20 (REQ-008: semantic fix — was .claude/ dep-mapper, now project source refactorer) |
| delivery-pipeline | 300L | 200L | 135L | 2026-02-19 |
| plan-verify-coordinator | 272L | 159L | 107L | 2026-02-19 |
| orchestrate-coordinator | 372L | 183L | 164L | 2026-02-19 |
| doing-like-agent-teams | 162L | 176L (rewrite) | 103L | 2026-02-19 |
| doing-like-agent-teams | 322L→rewrite | 359L | — | 2026-02-20 (single-session elevation: removed AT comparisons, added Prompt Caching + PT as Universal Context Source sections) |
| manage-skill | 400L | 184L | 151L | 2026-02-19 |

## Content Routing — plan-verify-static Pattern

KEEP in SKILL.md (routing/operational):
- PASS/FAIL thresholds (≥95%, <85%, HIGH orphan zero-tolerance)
- Orphan file definition (brief inline in Decision Points)
- Failure handling table (L0-L4 rows)
- Special case bullets (3 condensed)
- All Anti-Patterns, Transitions, Quality Gate, Output

MOVE to resources/methodology.md:
- Full DPS INCLUDE/EXCLUDE/Budget blocks
- Tier-specific DPS variations table
- Per-step verification procedure (Steps 1-5)
- Coverage matrix format table
- Evidence template code block
- Full PASS/CONDITIONAL_PASS/FAIL criteria with prose descriptions

## Content Routing — execution-infra Pattern

KEEP in SKILL.md (operational constraints):
- infra-implementer-only constraint (no Bash, no delete)
- Scope boundary list (.claude/ subtree only)
- Input validation checklist (5 gates before spawning)
- Parallel vs Sequential spawn decision rules
- Failure table (L0-L4 rows) + 3 pipeline-impact bullets
- All 6 Anti-Patterns (safety-critical, keep full text)
- Phase-Aware Execution (condensed + ref links)
- Transitions (all 3 tables), Quality Gate, Output L1

MOVE to resources/methodology.md:
- Tier-specific DPS variations (TRIVIAL/STANDARD/COMPLEX with maxTurns)
- Monitoring heuristics table (health/violation/overflow/corruption signals)
- Configuration format notes (frontmatter fields, agent profile format, settings.json key paths, hook script conventions)
