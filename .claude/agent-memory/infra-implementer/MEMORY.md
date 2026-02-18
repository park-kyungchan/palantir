# Infra-Implementer Agent Memory

## Key Patterns

### L1 Description Expansion (P4+P5+P6 signals)
- Always read spec file FIRST (`/tmp/skill-patch-spec.md` or similar) before touching skill files
- L1 YAML uses `description: >-` multiline format — content joins with single spaces after YAML parsing
- Target 700-1024 chars for L1 descriptions; hard limit is 1024
- P4 = failure route signal; P5 = DPS context hint; P6 = char utilization
- Preserve ALL existing P0-P3 signals exactly — only ADD new signals
- Use `>-` style (strip trailing newlines) — do NOT change to `|` block style

### D12 Escalation Table Placement
- Add the table AT THE TOP of existing `## Failure Handling` section
- Adapt "Failure Type" column to each skill's actual failure scenarios (not generic)
- Minimum required: L0, L2, L4. All 5 preferred for COMPLEX-tier skills

### D15 Iteration Tracking Placement
- Only applies to loop skills: brainstorm, validate, feasibility (and plan/execution skills per spec table)
- Add as `### Iteration Tracking (D15)` subsection WITHIN Methodology section (after last numbered step)
- Include: PT metadata key, iteration 1-2 strict mode, iteration 3 relaxed mode, max iterations

### D17 Note Placement
- Add blockquote `> **D17 Note**: P0-P1 local mode — Lead reads output directly via TaskOutput. 3-channel protocol applies P2+ only.`
- Place BEFORE `## Quality Gate` section (or directly before `## Output` if no Quality Gate)

### feasibility D12 exception
- pre-design-feasibility D12 is already PASS per audit — do NOT add table for it
- Only add D15 subsection and D17 note for feasibility
