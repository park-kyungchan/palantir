# COA-6: CLAUDE.md Placement Specification

## Placement Architecture

**Decision:** Add "Spawn Constraints (Permanent)" subsection WITHIN §6, after Pre-Spawn Checklist gates, before Spawn Matrix.

**Taxonomy:**
- Gates (S-*): Conditional checks evaluated per-spawn (S-1, S-2, S-3)
- Constraints (SC-*): Fixed rules that always apply (SC-1, SC-2)

**No duplication:** BUG-002 stays only in Pre-Spawn Checklist (S-2/S-3). BUG-001/RTDI-009 go into Spawn Constraints only.

## Insertion Point

After CLAUDE.md line 158:
```
Violation of any gate is a Lead orchestration failure. All three gates are mandatory for every spawn.
```

Before CLAUDE.md line 160:
```
### Spawn Matrix
```

## Exact Text to Insert

```markdown

### Spawn Constraints (Permanent)

These constraints always apply to every teammate spawn. Unlike gates (conditional checks),
constraints are fixed rules with no evaluation needed.

**SC-1: Mode Override**
- Always spawn ALL teammates with `mode: "default"` in the Task tool call.
- Rationale: `permissionMode: plan` in agent .md frontmatter blocks MCP tool calls (BUG-001).
  The Task tool `mode` parameter overrides the agent's frontmatter `permissionMode`.
  Safety is maintained by `disallowedTools` in each agent .md, which blocks mutations
  (Edit, Write, Bash) independently of permission mode.
- Reference: MEMORY.md BUG-001

**SC-2: Plan Mode Disabled**
- No agent operates in `permissionMode: plan` at runtime. This is a consequence of SC-1.
- Agent .md files may still declare `permissionMode: plan` in frontmatter, but the Task tool
  `mode: "default"` parameter overrides it at spawn time.
- Reference: RTDI-009

```

## Verification Checklist

1. [x] No duplication with §6 Pre-Spawn Checklist (BUG-002 stays in S-2/S-3 only)
2. [x] No conflict with existing §6 content
3. [x] SC-1 and SC-2 cover BUG-001 and RTDI-009 respectively
4. [x] Cross-references to MEMORY.md for diagnostic history
5. [x] Placement is within §6 (single authority for all spawn-time rules)
6. [x] Gate vs Constraint taxonomy is clear and non-overlapping

## What Does NOT Change in CLAUDE.md

- §6 Pre-Spawn Checklist: No changes (BUG-002 coverage is complete as-is)
- §7 MCP Tools: No changes
- §8 Safety Rules: No changes
- §9 Compact Recovery: No changes
- [PERMANENT] DIA Enforcement: No changes (mentions mode: "default" only implicitly via protocol)

## Relationship to Existing Content

| Constraint | MEMORY.md | agent-teams-bugs.md | CLAUDE.md (current) | CLAUDE.md (proposed) |
|------------|-----------|---------------------|---------------------|----------------------|
| BUG-001 | Full description | Full description (Korean) | NOT PRESENT | SC-1: Mode Override |
| BUG-002 | Full description | Not present | §6 S-2/S-3 (complete) | No change needed |
| RTDI-009 | Not present (session GC only) | Not present | NOT PRESENT | SC-2: Plan Mode Disabled |
