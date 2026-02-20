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
- Phases with multiple skills follow coordinator pattern: P2 (research-coordinator), P4+P7 (validate-coordinator), P5 (orchestrate-coordinator)
- validate-coordinator is phase-parameterized: P4 routes to orchestration, P7 routes to delivery-pipeline
- Old stale skills: plan-verify-coordinator, verify-coordinator — both superseded by validate-coordinator
- When checking phase coverage gaps, verify coordinator presence for each multi-skill phase

### Semantic Collision Audit Patterns (2026-02-20)
- "CANNOT: Task" in agent descriptions = CONFIRMED ambiguity (Task spawn tool vs Task API)
- All 4 worker agents (analyst, researcher, implementer, infra-implementer) have this collision
- P4+P7 share domain `validate` — domain field alone cannot distinguish phase
- 10 stale skills (plan-verify-*, verify-*) still exist on disk but removed from CLAUDE.md routing table
- orchestrate-static references "general-purpose subagent_type" which is an undefined agent profile
- Full findings: `.claude/doing-like-agent-teams/projects/validate-skills/analyst/rsil-semantic-audit.md`

### context:fork Adoption Status
- Fixed in CC 2.1 (Feb 2026), but 0 skills use it as of 2026-02-20
- Candidate skills: read-only analysis workflows that write to file output, no P2P coordination needed
- Evidence source: ref_skills.md §6

### CE Hooks Are Advisory-Only
- All 3 CE hooks (ce-pre-read-section-anchor, ce-pre-grep-optimize, ce-post-grep-guard) exit 0
- They warn but never block — behavioral enforcement requires exit 2
- Registered in settings.json with 5s timeout each
