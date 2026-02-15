# Analyst Agent Memory

## Analysis Patterns

### General Methodology
- Always read all reference files before analyzing (cc-reference/*, existing skills, agents)
- For audits: read ALL files in scope before analyzing -- parallel reads of agents+hooks+settings, then skills in batches, then cross-references
- ADR format: Context -> Decision -> Consequences (with +/- trade-offs)
- Gap resolution tracking: map every gap to specific section/ADR in architecture doc

### Quality Scoring
- Use severity tiers: CRITICAL / HIGH / MEDIUM / LOW / ADVISORY
- Track convergence trajectory across iterations (e.g., 47 -> 20 -> 6 = converging)
- Diminishing returns threshold: when CRITICAL=0, HIGH=0, MEDIUM<=3, recommend STOP
- Overall health score: 1-10 scale, weighted by severity distribution
- Component health vs integration health are separate scores (integration is usually lower)

### Common Finding Categories
- L1/L2 consistency: frontmatter vs body contradictions (INPUT_FROM vs "Receives From")
- Bidirectionality gaps: skill A references B but B does not reference A
- Phase tag alignment: ensure skill tags match CLAUDE.md pipeline tier definitions
- Tool-agent mismatch: skill methodology assumes tools the assigned agent does not have
- Failure path coverage: well-defined vs vague vs undefined
- Cross-component integration: hook-agent matchers, settings permissions, dashboard accuracy
- L1 budget compliance: all descriptions must be <=1024 chars

### Context Budget Analysis
- Agent spawns create SEPARATE 200K context windows
- Only L1 summaries (~300-500 tokens) return to Lead
- Separate Lead context (persistent + conversation) from agent spawn contexts
- L1 budget: total auto-loaded descriptions capped at 32,000 chars

### Output Standards
- Architecture docs: comprehensive with ADRs and trade-off analysis
- Interface docs: boundary definitions with cross-boundary invariants
- Risk docs: FMEA format (component, failure mode, RPN scoring)
- Audit reports: findings table + severity distribution + health score + recommendations

### File Path Patterns
- Audit outputs: `/home/palantir/.claude/agent-memory/analyst/{audit-name}.md`
- Architecture docs: same directory
- CC reference cache: `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/`

### Established Conventions
- L1 INPUT_FROM = routing triggers only; L2 "Receives From" = all data sources
- Homeostasis and cross-cutting skills are exempt from strict pipeline ordering
- Failure routes are the only valid backward phase references
- Generic domain refs in L1 should use specific skill names (e.g., "design-architecture" not "design domain")

### Tool Usage
- Grep with regex for counting protocol markers: `\[([A-Z_]+)\]`
- Read files in parallel batches to minimize turn count
- Write findings immediately after analysis -- do not wait for gate approval
