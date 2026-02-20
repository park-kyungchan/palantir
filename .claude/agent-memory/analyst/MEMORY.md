# Analyst Agent Memory

## Key Patterns

### Skill L1 Budget Override
- settings.json `SLASH_COMMAND_TOOL_CHAR_BUDGET` overrides the default 16K formula
- Current value: 56K chars (3.5x default)
- MEMORY.md skill budget stats may quote 16K — always check settings.json for override
- Pattern: verify actual budget via settings.json before reporting coverage %

### CLAUDE.md vs MEMORY.md Line Limits
- 200L limit applies to MEMORY.md only (BUG-005 double-injection protection)
- CLAUDE.md has no documented truncation limit — its cost is every-call context load
- Do not conflate the two constraints when analyzing size issues

### Coordinator Pattern Coverage
- Phases with multiple skills follow coordinator pattern: P2 (research-coordinator), P4 (plan-verify-coordinator), P5 (orchestrate-coordinator)
- P7 (verify) is the known gap — 4 verify skills, no coordinator
- When checking phase coverage gaps, verify coordinator presence for each multi-skill phase

### context:fork Adoption Status
- Fixed in CC 2.1 (Feb 2026), but 0 skills use it as of 2026-02-20
- Candidate skills: read-only analysis workflows that write to file output, no P2P coordination needed
- Evidence source: ref_skills.md §6

### CE Hooks Are Advisory-Only
- All 3 CE hooks (ce-pre-read-section-anchor, ce-pre-grep-optimize, ce-post-grep-guard) exit 0
- They warn but never block — behavioral enforcement requires exit 2
- Registered in settings.json with 5s timeout each
