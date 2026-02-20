# Coordinator Agent Memory

## Role
Multi-dimension synthesis agent. Reads N upstream analyst outputs, produces unified cross-cutting analysis.
Sub-Orchestrator: can spawn analyst/researcher subagents for file reading (>3 files OR any >200 lines).

## Key Patterns

### Synthesis Decision Tree
- <=3 files AND <=200 lines each: READ DIRECTLY
- <=5 files all <=50 lines: READ DIRECTLY (subagent overhead > benefit)
- >3 files with any >200 lines, OR >5 files total: SPAWN analyst subagent per file group (<=3 per agent)

### DLAT Coordinator Role (synthesis-only)
- Coordinator = N-to-1 synthesis ONLY. Cannot orchestrate parallel waves (CC limitation).
- Reads from DLAT_BASE analyst output files, not from subagent return values.
- Writes synthesis to: {DLAT_BASE}/coordinator/{phase}-synthesis.md
- Returns micro-signal: "{STATUS}|ref:{OUTPUT_PATH}"

### Output Format
Always use the standard coordination format:
- L1 Summary header with Status, Dimensions, Findings, Conflicts, Confidence
- L2 Cross-Dimension Synthesis: Consensus Findings + Conflicts + Gaps
- L2 Per-Dimension Summary table
- L3 Source Files list

## Active Projects (as of 2026-02-20)

### math-question-bank-redesign (W4)
- DLAT_BASE: ~/.claude/doing-like-agent-teams/projects/math-question-bank-redesign/
- Status: P6 PENDING (P0-P5 DONE)
- execution_plan_path: coordinator/p5-execution-plan.md
- Next: P6 Execution waves (Wave 1 DB + Wave 2 components + Wave 4 routing parallel, Wave 3 after Wave 2)

### math-problem-design-portfolio
- DLAT_BASE: ~/.claude/doing-like-agent-teams/projects/math-problem-design-portfolio/
- Status: COMPLETE (P0-P7 DONE, P8 SKIPPED by user decision)
- Output: /home/palantir/crowd_works/math-problem-design.html (1836L)

## Language Policy
- User-facing responses: Korean only
- Technical artifacts: English only
