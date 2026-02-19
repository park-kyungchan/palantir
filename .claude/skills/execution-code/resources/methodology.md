# Execution Code — Detailed Methodology

> On-demand reference. Contains tier-specific DPS additions, DPS context field detail, and monitoring heuristics.
> Load this file when constructing implementer DPS prompts or diagnosing monitoring issues.

---

## DPS Context Field Construction (D11 Detail)

For every implementer DPS Context field:

**INCLUDE** (what the implementer needs for direction):
- Exact task row from orchestrate-coordinator matrix (`task_id`, description, `files[]`)
- Interface contracts verbatim from plan-relational: function signatures, data types, return values, error types
- PT subject and acceptance criteria

**EXCLUDE** (what causes drift):
- Other implementers' task details (unless there is a direct dependency)
- ADR rationale (pass WHAT decisions, not WHY they were made)
- Full pipeline state beyond this task group
- Rejected design alternatives

**Budget**: Context field ≤ 30% of implementer effective context budget.

---

## Tier-Specific DPS Variations

### TRIVIAL DPS Additions
- **Context**: Include full file content (small files fit in context). No line-range references needed.
- **Task**: Specify exact diff: "Change line X from `old` to `new`". Include expected test command: "Run `npm test -- --grep 'test name'` to verify."
- **Constraints**: Single file only. If change requires a second file, escalate to STANDARD.
- **maxTurns**: 15 (small scope, quick completion expected)

### STANDARD DPS Additions
- **Context**: Include file headers and relevant functions (not full files). Reference line ranges: "See `src/auth.ts:45-80` for the existing pattern."
- **Task**: Describe behavior change, not exact diff. Let implementer decide approach within interface contracts.
- **Constraints**: Assigned files only. Report (don't fix) issues in unassigned files.
- **maxTurns**: 25 (moderate scope)

### COMPLEX DPS Additions
- **Context**: Include architecture summary from design-architecture L2. Interface contracts from plan-relational for ALL cross-boundary interactions. Dependency order from plan-behavioral.
- **Task**: Describe component-level goals. Reference test suites: "All tests in `tests/auth/` must pass after changes."
- **Constraints**: Own files only. Use interface contracts as boundaries — do not reach into other implementers' file assignments.
- **maxTurns**: 30 (full scope, may need exploration)

---

## Monitoring Heuristics

| Signal | Pattern | Lead Action |
|--------|---------|-------------|
| **Healthy** | Implementer sends Ch3 micro-signal with incremental `files_changed`, no blockers | Continue monitoring |
| **Stalled** | No micro-signal after `maxTurns/2` | `TaskGet` to check status; send guidance via `SendMessage` |
| **Blocked on dep** | Implementer reports blocker on upstream output | Check if producer has completed via Ch3/Ch4. If COMM_PROTOCOL AWAIT is configured, consumer self-waits — Lead need not intervene. |
| **Scope creep** | Implementer modifying files outside assignment | `SendMessage` correction referencing constraint in original DPS |
| **Test failures** | Implementer reports test failures | Check if expectations match design-interface contracts. If contract mismatch → escalate to plan revision, not implementer workaround. |
