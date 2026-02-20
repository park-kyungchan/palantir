# Coordinator Agent Memory

## Role
Multi-dimension synthesis agent. Reads N upstream analyst outputs, produces unified cross-cutting analysis.

## Key Patterns

### Synthesis Decision Tree
- <=3 files AND <=200 lines each: READ DIRECTLY
- <=5 files all <=50 lines: READ DIRECTLY (subagent overhead > benefit)
- >3 files with any >200 lines: Use sequential-thinking to process in batches (read 2-3 files per batch)

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

## Language Policy
- User-facing responses: Korean only
- Technical artifacts: English only
