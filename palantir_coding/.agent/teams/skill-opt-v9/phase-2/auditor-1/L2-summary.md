# L2 Summary — Coordinator Agent .md Systematic Audit

## Summary

Audited all 8 coordinator agent .md files across frontmatter (12 fields × 8 coordinators = 96 data points) and body content (611 total lines). Found 25 frontmatter field gaps, 2 distinct templates causing inconsistency, ~175 lines of protocol duplication in 5 coordinators, and 5 unused CC features (skills, hooks, mcpServers). The most impactful optimization is template unification: converge Template A (verbose, 5 coordinators) with Template B (lean, 3 coordinators) by having all 8 reference `coordinator-shared-protocol.md` and retaining only role-specific unique logic.

## Frontmatter Audit

### Field Presence Matrix

| Field | 8/8 | 5/8 | 0/8 | Notes |
|-------|:---:|:---:|:---:|-------|
| name | X | | | Consistent |
| description | X | | | Consistent pattern |
| model | X | | | All `opus` |
| permissionMode | X | | | All `default` (BUG-001 compliant) |
| maxTurns | X | | | 40/50/80 tiered |
| tools | X | | | All identical (7 tools) |
| disallowedTools | X | | | 5 full (4 items), 3 partial (2 items) |
| memory | | X | | Missing: arch, plan, valid |
| color | | X | | Missing: arch, plan, valid |
| skills | | | X | None have preloaded skills |
| mcpServers | | | X | None use MCP servers |
| hooks | | | X | None have agent-scoped hooks |

**Gap count:** 25 field-level gaps (3 memory + 3 color + 3 incomplete disallowedTools + 8 skills + 8 hooks)

### Two-Template Problem

The 3 missing-field coordinators (architecture, planning, validation) share a common "lean" template (Template B, ~61L each) that references both shared protocols but has minimal body content. The other 5 (research, verification, execution, testing, infra-quality) use a "verbose" template (Template A, 105-151L) that inlines shared protocol content but doesn't reference `coordinator-shared-protocol.md`.

| Template | Coordinators | Avg Body Lines | Refs coordinator-shared-protocol? | Has color/memory? | Full disallowedTools? |
|----------|-------------|---------------|:---------------------------------:|:-----------------:|:--------------------:|
| A (verbose) | 5 | 93L | NO | YES | YES |
| B (lean) | 3 | 39L | YES | NO | NO |

## Body Content Audit

### Section Inventory (across 8 coordinators)

| Section | A-type (5) | B-type (3) | In shared protocol? |
|---------|:----------:|:----------:|:-------------------:|
| Role | 5/5 | 3/3 | No (unique) |
| Workers list | 5/5 | 0/3 | No (unique) |
| Before Starting Work | 5/5 | 3/3 | No (unique) |
| Worker Management | 5/5 | 0/3 | §2 (shared) |
| Communication Protocol | 5/5 | 0/3 | §2.2-2.3 (partial) |
| Understanding Verification | 5/5 | 0/3 | §2.2-2.3 (shared) |
| Failure Handling | 5/5 | 0/3 | §6 (shared) |
| Coordinator Recovery | 5/5 | 0/3 | §7 (shared) |
| Output Format | 5/5 | 3/3 | §4 (shared) |
| Constraints | 5/5 | 3/3 | §1 + agent-common |
| How to Work | 0/5 | 3/3 | No (unique) |

### Duplication Quantification

In Template A coordinators, ~35 lines per coordinator (175L total) duplicate content from `coordinator-shared-protocol.md`:
- Coordinator Recovery: 6L × 5 = 30L
- Worker Management boilerplate: ~8L × 5 = 40L
- Communication Protocol boilerplate: ~10L × 5 = 50L
- Understanding Verification boilerplate: 3L × 5 = 15L
- Failure Handling boilerplate: 3L × 5 = 15L
- Constraints boilerplate: 5L × 5 = 25L

### Unique Logic per Coordinator

| Coordinator | Unique Logic | Lines |
|-------------|-------------|-------|
| research | Research distribution rules (codebase/external/audit routing) | ~7L |
| verification | Cross-dimension synthesis cascade rules | ~10L |
| architecture | (delegates to protocols) | ~0L |
| planning | Non-overlapping file assignment, P3→P4 handoff | ~5L |
| validation | No understanding verification for challengers, verdict types | ~5L |
| execution | Two-stage review dispatch (AD-9), fix loop rules, consolidated report format | ~45L |
| testing | Sequential P7→P8 lifecycle, conditional Phase 8, per-worker examples | ~20L |
| infra-quality | Score aggregation formula, cross-dimension synthesis | ~18L |

## Optimization Recommendations

### Priority 1: Template Unification (CRITICAL)
- Converge all 8 to a unified template that references both shared protocols
- Retain only unique logic in body (varies: 0-45L per coordinator)
- Expected reduction: ~175L total across 5 Template A coordinators
- Unification target: 39-90L per coordinator (down from 39-125L)

### Priority 2: Frontmatter Completion (HIGH)
- Add `memory: project` to all 8 (3 missing + potentially change 5 from `user` to `project`)
- Add `color:` to 3 missing (architecture, planning, validation)
- Complete `disallowedTools:` for 3 (add Edit + Bash to architecture, planning, validation)

### Priority 3: Skills Preload Evaluation (HIGH — Design Decision)
- 0/8 have skills preloaded
- Candidates: 5 coordinators could benefit from their phase's skill for contextual awareness
- **Trade-off:** Skills are 400-600L each — token cost vs. phase awareness benefit
- **Alternative:** Lead can inject phase-specific context at spawn time (Dynamic Context Injection)
- Recommendation: Defer to architecture phase for decision

### Priority 4: Protocol Reference Fix (HIGH)
- 5/8 missing `coordinator-shared-protocol.md` reference
- These 5 inline the content instead — inconsistent and harder to maintain
- Fix: add reference line, remove inlined duplicates

### Priority 5: Agent-Scoped Features (LOW-MEDIUM)
- Hooks: Could enforce progress-state.yaml writes and L1 incremental updates mechanically
- mcpServers: No clear need beyond sequential-thinking (already in tools)
- Evaluate after CC capabilities are better documented

## PT Goal Linkage

- **Design Decision D-6 (Precision Refocus):** Frontmatter can replace some body content. Template unification directly implements this.
- **Design Decision D-13 (Coordinator Shared Protocol):** 5/8 don't reference the protocol they should follow. Fix required.
- **CC Feature Adoption:** skills preload, agent-scoped hooks, and memory are underutilized CC features identified as optimization targets.

## Evidence Sources

- 8 coordinator .md files: `.claude/agents/{name}-coordinator.md`
- `coordinator-shared-protocol.md` (167L) — defines shared procedures
- `agent-common-protocol.md` (247L) — defines all-agent procedures
- CLAUDE.md §6 — coordinator management, spawning rules, BUG-001
- All line counts and field values extracted from direct file reads
