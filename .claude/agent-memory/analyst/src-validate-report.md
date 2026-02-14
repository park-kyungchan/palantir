# SRC Requirements Validation Report

> Analyst output | 2026-02-14 | Pre-Design Validate (P1)
> Scope: SRC (Smart Reactive Codebase) architecture from brainstorm phase
> Reference: impact-analysis-gap-report.md (prior analyst output)
> Method: 5-dimension completeness check against INFRA v10.2 baseline

---

## Completeness Matrix

| # | Dimension | Status | Coverage | Gaps |
|---|-----------|--------|----------|------|
| 1 | Functional Scope | CONDITIONAL | 85% | 4 gaps (boundary ambiguity, user behaviors, codebase-map lifecycle) |
| 2 | Non-Functional Constraints | CONDITIONAL | 70% | 5 gaps (performance targets, context math, scalability limits) |
| 3 | Acceptance Criteria | FAIL | 40% | 7 gaps (no per-component success criteria, no integration tests) |
| 4 | Error Handling | CONDITIONAL | 65% | 6 gaps (partial coverage, missing degradation strategy) |
| 5 | Integration Points | CONDITIONAL | 75% | 5 gaps (hook coexistence, phase numbering, skill count impact) |

**Overall Verdict: CONDITIONAL_PASS**

The architecture is structurally sound and addresses the core gap identified in the prior analysis (zero runtime impact analysis). However, it lacks the operational specificity needed to proceed to design without addressing 27 gaps across 5 dimensions. The most critical shortfalls are in Acceptance Criteria (no measurable "done" definition) and Non-Functional Constraints (no context budget math proving feasibility within 200K limit).

---

## Dimension 1: Functional Scope

### 1.1 Feature Completeness Assessment

The 5-layer model maps well to the 4-priority gap list from the prior analysis:

| Prior Gap (Priority) | SRC Layer | Coverage |
|----------------------|-----------|----------|
| P1: PostToolUse Hook | L1: Change Detection | FULL -- on-file-change.sh with PostToolUse:Edit/Write |
| P2: Implementer Impact Reporting | L2: Impact Analysis | PARTIAL -- researcher-based, not implementer self-report |
| P3: Persistent Dependency Graph | L5: Knowledge Persistence | FULL -- codebase-map.md |
| P4: Cross-Implementer Propagation | L3: Cascade Update | FULL -- recursive multi-implementer spawning |
| P5: Post-Execution Impact Scan | L2: Impact Analysis | FULL -- P7.5 skill |

All 5 priority gaps are addressed. The architecture additionally introduces:
- Tiered Loading model (L0-L3) not in the gap list -- novel contribution
- Lead protocol change ("Impact-First Thinking") -- addresses the "Lead cannot ask what depends on X" gap
- manage-codebase homeostasis skill -- addresses persistent knowledge maintenance

### 1.2 Boundary Analysis

**What is explicitly IN scope:**
- `.claude/` INFRA files (primary)
- Application source code (extensible, secondary)
- Hook-based change detection
- Text-based grep analysis (no AST)
- Recursive convergence with bounded depth

**What is explicitly OUT of scope:**
- External file monitoring (CC is not a daemon)
- AST parsing
- Cross-session persistence beyond codebase-map.md

**GAP-F1: Ambiguous boundary between INFRA-primary and application-extensible.**
The brainstorm states "Scope: .claude/ INFRA primarily, extensible to application code" but does not define:
- What triggers the switch from INFRA-only to application-inclusive?
- Are both modes active simultaneously or is one disabled by default?
- Does `grep -rl` in the hook search `.claude/` only, or the entire repo?
- What file extensions/directories are included in application-code mode?

**GAP-F2: No user-facing behavior specification.**
The SRC system is entirely internal to the pipeline. There is no specification for:
- Does the user see hook output (additionalContext is system-level, invisible in transcript)?
- How does the user know cascade updates are happening?
- Can the user override or skip impact analysis?
- What happens if the user invokes `/delivery-pipeline` during an active cascade?

**GAP-F3: codebase-map.md initial generation vs incremental update ambiguity.**
The brainstorm describes:
- manage-codebase skill generates/updates codebase-map.md
- codebase-map.md contains per-file dependency graph
But does not specify:
- How is the initial codebase-map.md generated (full scan at session start)?
- What triggers manage-codebase: after every cascade cycle, once at P8.5, or both?
- How large can codebase-map.md grow? Current `.claude/` has ~80 files. A real codebase could have thousands.
- What if codebase-map.md does not exist when the hook fires?

**GAP-F4: Semantic classification undefined.**
Impact analysis classifies dependents as DIRECT/TRANSITIVE/SEMANTIC. The first two are grep-derivable:
- DIRECT: file A imports/references file B (grep finds B's name in A)
- TRANSITIVE: file A references B, B references C (2-hop)
But SEMANTIC ("same interface") is undefined:
- How does text-based grep detect "same interface" without AST?
- What constitutes an interface in `.claude/` INFRA files? (e.g., INPUT_FROM/OUTPUT_TO references? YAML field names?)
- What constitutes an interface in application code without AST?

### 1.3 Verdict: CONDITIONAL (85%)

Core features are well-defined. Boundaries, user-facing behaviors, and the semantic classification method need specification before design phase.

---

## Dimension 2: Non-Functional Constraints

### 2.1 Explicitly Stated Constraints

| Constraint | Value | Source | Verifiable? |
|-----------|-------|--------|-------------|
| Recursion depth | Max 3 iterations | Brainstorm | YES |
| Hook output size | Max 500 chars | Brainstorm | YES |
| Context limit | 200K tokens | CC platform | YES |
| MEMORY.md summary | <=200 lines | CC platform | YES |
| Max parallel agents | 4 | Brainstorm | YES (practical guideline) |
| No AST parsing | Text-based grep only | Brainstorm | YES |
| CC non-daemon | No external monitoring | CC platform | YES |
| Hook one-shot | Not persistent | CC platform | YES |

### 2.2 Missing Performance Targets

**GAP-NF1: No hook execution time budget.**
The existing hooks have explicit timeouts (10s, 30s, 15s). The on-file-change.sh hook runs `grep -rl` on every Edit/Write call. For a codebase with 1000+ files:
- What is the acceptable latency for `grep -rl`?
- What timeout should the hook have?
- The brainstorm does not specify a timeout value.
- Current hooks use 10-30s. `grep -rl` on a large repo could take seconds.
- Recommended: Define max execution time (e.g., 5s) and fallback behavior if exceeded.

**GAP-NF2: No context budget math proving feasibility.**
The SRC system adds significant context consumption:

| Component | Estimated Context Cost |
|-----------|----------------------|
| Hook additionalContext (500 chars) | ~125 tokens per Edit/Write call |
| impact-analysis skill L2 | ~800 tokens when loaded |
| cascade-update skill L2 | ~800 tokens when loaded |
| manage-codebase skill L2 | ~800 tokens when loaded |
| codebase-map.md (if loaded) | 200-2000+ tokens depending on size |
| New skill L1 descriptions (3 skills) | ~3 x 250 = 750 tokens added to persistent budget |

Current L1 budget: 26,315 of 32,000 chars used (v10.3). Adding 3 new skill descriptions (~750 chars each = 2,250 chars) would bring usage to 28,565/32,000 = 89%. This is feasible but tight.

The per-turn cost is more concerning: a complex cascade with 3 iterations, each spawning researcher + implementers, could consume 50K+ tokens per cycle. With 200K total and existing pipeline already consuming ~80K through P7, this leaves only ~120K for P7.5 + P7.6 + P8 + P8.5 + P9. No budget analysis proves this fits.

**GAP-NF3: No scalability ceiling defined.**
The architecture is designed for `.claude/` (~80 files). What happens at:
- 500 files? (small app)
- 5,000 files? (medium app)
- 50,000 files? (large monorepo)
- `grep -rl` performance degrades linearly with file count.
- codebase-map.md size grows linearly (or worse) with file count.
- The brainstorm says "extensible to application code" but provides no scalability analysis.

**GAP-NF4: No specification for hook firing frequency.**
PostToolUse:Edit fires after EVERY Edit call. A typical implementer task might make 10-30 Edit calls. This means:
- 10-30 hook firings per implementer per task
- Each firing runs `grep -rl` and injects additionalContext
- But additionalContext "survives the current turn only" (from cc-reference/context-loading.md)
- And the hook fires on the AGENT's context (implementer), not Lead's context
- Does the brainstorm intend the hook to fire on implementer agents, Lead, or both?

**GAP-NF5: Token cost multiplier not estimated.**
Each cascade iteration potentially spawns: 1 researcher (30 maxTurns) + N implementers (50 maxTurns each). At ~7x token multiplier per agent, a 3-iteration cascade with 2 implementers per iteration adds: 3 * (1 researcher + 2 implementers) = 9 additional agent spawns. At 200K context each, that is 1.8M additional tokens per cascade event. The brainstorm does not acknowledge this cost.

### 2.3 Verdict: CONDITIONAL (70%)

Constraints are enumerated but not validated against real-world scenarios. The missing context budget math (GAP-NF2) and scalability ceiling (GAP-NF3) are the most critical gaps -- they could invalidate the entire architecture if the numbers do not work.

---

## Dimension 3: Acceptance Criteria

### 3.1 Per-Component Success Criteria

**GAP-AC1: on-file-change.sh has no acceptance criteria.**
What does "working" mean?
- Successfully captures file path from PostToolUse:Edit input? (testable)
- Successfully runs `grep -rl` and returns results? (testable)
- Injects additionalContext within 500 char limit? (testable)
- Fires on BOTH Edit and Write tool calls? (requires separate matchers or combined hook)
- Does NOT fire on Read, Glob, Grep calls? (matcher specificity)
- Exits within timeout? (testable)

**GAP-AC2: impact-analysis skill has no acceptance criteria.**
What does "working" mean?
- Researcher correctly classifies DIRECT dependencies? (how to verify?)
- Researcher correctly classifies TRANSITIVE dependencies? (how to verify 2-hop?)
- SEMANTIC classification is accurate? (undefined, per GAP-F4)
- Output format matches L1/L2 schema? (structural check only)
- Researcher completes within maxTurns (30)?

**GAP-AC3: cascade-update skill has no acceptance criteria.**
What does "convergence" mean?
- All identified affected files have been updated?
- No new impact detected after final iteration?
- How do we distinguish "converged" from "gave up at iteration 3"?
- What is the acceptable false-negative rate (files that should have been updated but were not)?

**GAP-AC4: manage-codebase skill has no acceptance criteria.**
What does "correct codebase-map" mean?
- All import/reference relationships captured?
- No stale entries for deleted files?
- Hotspot detection accuracy?
- Map parseable by hook and skills?

**GAP-AC5: codebase-map.md has no format specification.**
The brainstorm says "per-file dependency graph: imports, importedBy, hotspots, recent changes" but does not specify:
- YAML, JSON, or markdown table format?
- One entry per file or grouped by directory?
- Maximum size constraint?
- Schema for hotspot scoring?
- How "recent changes" is timestamped/scoped?

**GAP-AC6: Pipeline integration has no end-to-end acceptance test.**
No specification for how to verify the full flow:
- Modify file A -> hook fires -> impact analysis -> cascade update -> verification
- What is the test scenario? (e.g., "change a skill description, verify INPUT_FROM refs update")
- What is the expected outcome for a known dependency chain?

**GAP-AC7: No definition of "done" for the entire SRC system.**
What conditions must all be true for SRC to be considered "complete and working"?
- All 5 components deployed?
- End-to-end flow verified?
- Performance within budget?
- No regression in existing pipeline behavior?

### 3.2 Verdict: FAIL (40%)

This is the weakest dimension. The brainstorm describes WHAT to build but not HOW TO VERIFY it works. Every component needs explicit pass/fail criteria before entering design.

---

## Dimension 4: Error Handling

### 4.1 Explicitly Addressed Error Scenarios

| Scenario | Stated Handling | Adequate? |
|----------|----------------|-----------|
| Recursion depth exceeded | Max 3 iterations, then stop | PARTIAL -- what happens to unresolved impacts? |
| Context budget exceeded | Hook injection max 500 chars | YES for hook, but what about skill context? |
| CC not a daemon | Text-based grep only, no monitoring | YES -- architectural constraint |

### 4.2 Unaddressed Error Scenarios

**GAP-EH1: grep -rl fails or returns empty.**
Scenarios:
- `grep -rl` returns exit code 1 (no matches) -- is this "no dependents" or "grep failed"?
- `grep -rl` times out (large repo, slow disk)
- `grep -rl` returns too many results (popular utility file referenced by 100+ files)
- The hook currently has no error handling pattern for grep failure. Existing hooks (`on-subagent-start.sh`) check for `jq` availability but not for tool failures.

**GAP-EH2: Recursive convergence does not happen in 3 iterations.**
The brainstorm says "max 3 iterations" but does not specify:
- What state is the codebase left in? (partially updated, inconsistent?)
- Does Lead report the failure to the user?
- Does the pipeline continue to P8 (verify) or abort?
- Is there a "best effort" vs "all or nothing" semantic?
- Recommendation: Define explicit behavior -- either (a) proceed to P8 with warning, letting verify catch remaining issues, or (b) abort cascade, report unresolved impacts, let user decide.

**GAP-EH3: codebase-map.md is stale or corrupted.**
Scenarios:
- Map was generated 5 sessions ago, files have changed significantly
- Map YAML/JSON is malformed (partial write, truncation)
- Map references files that no longer exist
- Map is missing files that were recently added
- No staleness detection mechanism is specified. Recommendation: include a `generated_at` timestamp and a `file_count` field, verify against current filesystem before trusting.

**GAP-EH4: Hook output exceeds 500 char limit.**
The brainstorm sets a 500 char max for additionalContext, but:
- What if `grep -rl` returns 50 files? (50 x ~30 chars/path = 1500 chars)
- Does the hook truncate, prioritize, or error?
- What truncation strategy preserves the most critical information?
- Recommendation: Sort by relevance (closest dependency), truncate with "... and N more files" suffix.

**GAP-EH5: Impact analysis researcher produces incorrect classification.**
- What if the researcher classifies a DIRECT dependency as TRANSITIVE or vice versa?
- What if the researcher misses a dependency entirely?
- There is no verification step between impact analysis (P7.5) and cascade update (P7.6).
- Recommendation: Consider a lightweight self-check step or have the cascade-update skill verify impact classifications before applying changes.

**GAP-EH6: Cascade update introduces NEW impacts not in original analysis.**
The brainstorm mentions "recursive convergence" but does not address:
- Cascade update modifies file B, which introduces a new dependency on file C (not in original impact list)
- Does the system re-run impact analysis on cascade-modified files?
- If yes, this could create an unbounded expansion (A affects B, B-update affects C, C-update affects D...)
- The 3-iteration limit bounds this, but the behavior within those iterations needs specification.

### 4.3 Degradation Strategy

**Not specified.** The brainstorm does not define a graceful degradation path:
- If the hook fails: does the pipeline revert to pre-SRC behavior (no impact awareness)?
- If impact analysis times out: does P7.6 cascade skip?
- If codebase-map is unavailable: does the hook fall back to grep-only?

Recommendation: Define a degradation hierarchy:
1. Full SRC: hook + codebase-map + impact-analysis + cascade-update
2. Degraded SRC: hook + grep-only (no codebase-map) + impact-analysis + manual review
3. No SRC: pre-SRC behavior (Lead reads implementer L1 file_changed list, no impact propagation)

### 4.4 Verdict: CONDITIONAL (65%)

Some scenarios are addressed (recursion depth, context budget), but critical failure modes (grep failures, non-convergence behavior, stale map, cascading expansion) are unspecified.

---

## Dimension 5: Integration Points

### 5.1 Hook Integration

**Current state:** 3 hooks in settings.json (SubagentStart, PreCompact, SessionStart:compact).

**New hook:** PostToolUse with matcher "Edit" (and separately "Write", or combined).

**Integration analysis:**

The new hook coexists cleanly with existing hooks -- they fire on different events. No conflict. However:

**GAP-IP1: Hook scope ambiguity -- global vs agent-scoped.**
From cc-reference/hook-events.md: PostToolUse hooks can be scoped to global, agent, or skill level. The brainstorm does not specify:
- Global scope: fires on ALL Edit/Write calls across Lead AND all agents
- Agent scope: fires only for specific agent types
- Skill scope: fires only during specific skill execution

If global: the hook fires when implementers edit files (desired), but ALSO when Lead reads/routes (if Lead ever uses Edit -- which it should not per CLAUDE.md but technically could).

If agent-scoped (in implementer.md hooks): fires only for implementer agents. But then the hook injects into the IMPLEMENTER's context, not Lead's. This contradicts the brainstorm's stated flow: "injects additionalContext to Lead."

**Critical finding:** PostToolUse hooks inject additionalContext into the context of the AGENT that used the tool, NOT the parent Lead. This means:
- If implementer calls Edit -> hook fires -> additionalContext goes to IMPLEMENTER
- Lead never sees the hook output
- The brainstorm's stated flow ("captures file path -> injects additionalContext to Lead") is architecturally impossible with a PostToolUse hook on an agent's Edit call

This is a fundamental design issue. Possible workarounds:
1. Hook writes to a file; Lead polls the file after implementer completes (via SubagentStop hook or L1 output)
2. Implementer is instructed to include impact candidates in its L1 output (this is Priority 2 from the gap report)
3. Use a SubagentStop hook that reads implementer's change manifest and injects into Lead
4. Hook writes to shared state file; Lead reads it as part of execution-code consolidation (Step 5)

**GAP-IP2: Two separate matchers needed for Edit and Write.**
From settings.json structure: each PostToolUse entry has a single `matcher` field. To fire on both Edit AND Write, the brainstorm needs either:
- Two separate PostToolUse entries (one with matcher "Edit", one with matcher "Write")
- One PostToolUse entry with matcher "" (empty = matches ALL tools, including Read, Grep, Glob, Bash -- far too noisy)
- Investigation needed: does CC support matcher arrays or regex? (Not documented in hook-events.md)

### 5.2 Skill Integration

**Current state:** 32 skills across 10 domains.

**New skills:** 3 (impact-analysis at P7.5, cascade-update at P7.6, manage-codebase at homeostasis).

**Integration analysis:**

**GAP-IP3: Phase numbering creates pipeline ambiguity.**
Current phases: P0-P9, with P7=execution, P8=verify, P9=delivery. The brainstorm introduces P7.5 and P7.6 as sub-phases within execution. This creates:
- Pipeline tier definitions reference P7, P8, P9. Do P7.5 and P7.6 count as part of P7?
- CLAUDE.md says "Max 3 iterations per phase." Does P7.5 have its own 3-iteration limit separate from P7?
- Existing skill INPUT_FROM/OUTPUT_TO references use domain names (execution, verify), not phase numbers. How do P7.5/P7.6 integrate with this naming?

Recommendation: Treat P7.5 and P7.6 as sub-skills within the execution domain rather than separate phases. Name them `execution-impact` and `execution-cascade` to follow the existing `execution-code`, `execution-infra`, `execution-review` pattern.

**New execution domain flow:**
```
execution-code ─┐
execution-infra ┘─→ execution-impact → execution-cascade → execution-review
```

This integrates naturally with the existing INPUT_FROM/OUTPUT_TO system.

**GAP-IP4: Skill count increases from 32 to 35.**
Adding 3 skills (impact-analysis, cascade-update, manage-codebase) increases:
- CLAUDE.md §1 Team Identity: "32 skills" must update to "35 skills"
- L1 budget: 26,315 + ~2,250 = ~28,565 chars (89% of 32,000) -- feasible but monitor
- manage-skills domain mapping: needs new detection rules for impact/cascade domain
- verify-consistency: more INPUT_FROM/OUTPUT_TO pairs to validate

If P8.5 (codebase-map update) is a separate skill rather than part of manage-codebase, count goes to 36.

### 5.3 Knowledge File Integration

**Current knowledge files:**
- MEMORY.md (200 lines, auto-loaded)
- Agent-specific MEMORY.md (3 agents with `memory: project`)

**New knowledge file:** codebase-map.md

**Integration analysis:**
- The brainstorm says "codebase-map summary in MEMORY.md <=200 lines" -- this consumes MEMORY.md space that is currently used for project memory, session history, and topic files. Current MEMORY.md is already ~155 lines. Adding a codebase-map summary could push it over 200.
- codebase-map.md itself is a new file. Where does it live?
  - In `.claude/` (project-scoped, version-controlled)
  - In `.agent/` (session-scoped, not version-controlled)
  - In `.claude/agent-memory/` (agent-scoped, persists across sessions)
- The file needs to be readable by: (a) the hook script (bash), (b) the impact-analysis skill (researcher), (c) the manage-codebase skill (analyst/infra-implementer), and (d) optionally Lead for L0 auto-load.

**GAP-IP5: codebase-map.md location and lifecycle not specified.**
No decision on:
- File path
- Version control inclusion/exclusion
- Who creates it initially
- Who is allowed to update it
- How often it is regenerated vs incrementally updated
- What happens when it conflicts with git changes from other contributors

### 5.4 Agent Integration

**Current agents:** 6 (analyst, researcher, implementer, infra-implementer, delivery-agent, pt-manager).

**New agent requirements:**
- impact-analysis uses researcher agent (existing)
- cascade-update uses implementer agents (existing)
- manage-codebase uses analyst or infra-implementer (existing)

No new agents needed. This is a strength of the architecture -- it reuses existing agent profiles.

However, the researcher agent (maxTurns: 30) may need more turns for complex impact analysis. And implementer agents spawned for cascade updates need clear instructions to include impact awareness in their L1 output.

### 5.5 Existing Pipeline Impact

**P7 execution-code:** Must be modified to trigger P7.5 after consolidation. Currently, execution-code consolidates results and reports to execution-review. The new flow inserts impact-analysis between consolidation and review.

**P7 execution-review:** Review scope expands to include cascade-updated files, not just originally-planned files. The reviewer must distinguish between "planned changes" and "cascade changes" for appropriate review depth.

**P8 verify:** No direct modification needed. Verify operates on all changed files regardless of origin.

**P9 delivery:** File change manifest must include cascade-updated files. Commit message should note cascade updates.

### 5.6 Verdict: CONDITIONAL (75%)

Integration is mostly feasible, but GAP-IP1 (hook context injection targeting) is a potential architecture-breaking issue that must be resolved in design. The phase numbering (GAP-IP3) and skill naming are solvable with the `execution-impact`/`execution-cascade` pattern.

---

## Overall Verdict: CONDITIONAL_PASS

The SRC architecture is structurally sound and addresses all 5 priority gaps from the prior impact-analysis gap report. The 5-layer model is well-conceived, the tiered loading design is elegant, and the reuse of existing agents is efficient. However, the brainstorm is a **conceptual architecture** that lacks the **operational specificity** required for a clean transition to design.

### Risk Assessment

| Risk | Severity | Gap(s) | Mitigation |
|------|----------|--------|------------|
| Hook injects into agent context, not Lead | CRITICAL | IP1 | Must redesign hook-to-Lead communication |
| Context budget overflow in complex cascade | HIGH | NF2, NF5 | Run budget math with worst-case scenario |
| No acceptance criteria for any component | HIGH | AC1-AC7 | Define per-component pass/fail before design |
| Semantic classification undefined for grep-only | MEDIUM | F4 | Either remove SEMANTIC tier or define grep-based heuristic |
| codebase-map.md unbounded growth | MEDIUM | F3, NF3 | Define size cap and pruning strategy |
| grep -rl performance on large repos | MEDIUM | NF1, NF3 | Define timeout and fallback |
| Non-convergence after 3 iterations | MEDIUM | EH2 | Define explicit behavior (continue vs abort) |

---

## Gap Summary

### Critical (must resolve before design)

1. **GAP-IP1**: PostToolUse hook additionalContext injects into the CALLING agent's context, not Lead. The brainstorm's stated flow (hook -> Lead) is architecturally impossible. Must redesign hook-to-Lead communication channel.
2. **GAP-NF2**: No context budget math proving the full SRC flow (P7 + P7.5 + P7.6 + P8 + P8.5 + P9) fits within 200K tokens including cascade iterations.
3. **GAP-AC7**: No definition of "done" for the SRC system. Cannot enter design without knowing what success looks like.

### High (should resolve before design, can defer to early design)

4. **GAP-F1**: Ambiguous scope boundary between INFRA-only and application-code modes.
5. **GAP-F4**: SEMANTIC dependency classification undefined for text-based grep analysis.
6. **GAP-AC5**: codebase-map.md has no format specification (YAML, JSON, markdown, schema).
7. **GAP-AC6**: No end-to-end acceptance test scenario defined.
8. **GAP-EH2**: Non-convergence behavior unspecified (continue vs abort, state left behind).
9. **GAP-NF5**: Token cost multiplier for cascade iterations not estimated (potential 1.8M+ tokens).
10. **GAP-IP3**: Phase numbering P7.5/P7.6 creates pipeline ambiguity. Recommend `execution-impact`/`execution-cascade` naming.

### Medium (can resolve during design)

11. **GAP-F2**: No user-facing behavior specification for SRC events.
12. **GAP-F3**: codebase-map.md initial generation vs incremental update lifecycle undefined.
13. **GAP-NF1**: No hook execution time budget or timeout specification.
14. **GAP-NF3**: No scalability ceiling defined (what file count is supported).
15. **GAP-NF4**: Hook firing frequency not scoped (fires on every Edit call in every agent).
16. **GAP-EH1**: grep -rl failure modes not handled (timeout, empty, too many results).
17. **GAP-EH3**: codebase-map.md staleness/corruption detection not specified.
18. **GAP-EH4**: Hook output truncation strategy when exceeding 500 char limit not defined.
19. **GAP-EH5**: No verification step between impact analysis and cascade update.
20. **GAP-EH6**: Cascade update introducing new impacts (unbounded expansion within iteration limit).
21. **GAP-IP2**: Two separate PostToolUse matchers needed for Edit and Write hooks.
22. **GAP-IP4**: Skill count increase (32 -> 35) requires CLAUDE.md, manage-skills, budget updates.
23. **GAP-IP5**: codebase-map.md file location, lifecycle, and ownership not specified.

### Low (can resolve during implementation)

24. **GAP-AC1**: on-file-change.sh acceptance criteria not specified.
25. **GAP-AC2**: impact-analysis skill acceptance criteria not specified.
26. **GAP-AC3**: cascade-update skill convergence definition not specified.
27. **GAP-AC4**: manage-codebase skill acceptance criteria not specified.

---

## Appendix: Key File References

| File | Path | Relevance |
|------|------|-----------|
| CLAUDE.md | `/home/palantir/.claude/CLAUDE.md` | Protocol definition, skill/agent counts, pipeline tiers |
| MEMORY.md | `/home/palantir/.claude/projects/-home-palantir/memory/MEMORY.md` | Current INFRA state, 200-line limit |
| settings.json | `/home/palantir/.claude/settings.json` | Hook configuration, permissions, env vars |
| hook-events.md | `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/hook-events.md` | PostToolUse event specification, matcher patterns |
| context-loading.md | `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/context-loading.md` | additionalContext behavior, context budget |
| native-fields.md | `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/native-fields.md` | Skill/agent frontmatter field reference |
| execution-code SKILL.md | `/home/palantir/.claude/skills/execution-code/SKILL.md` | Current P7 execution flow, L1 output schema |
| execution-review SKILL.md | `/home/palantir/.claude/skills/execution-review/SKILL.md` | Current review flow, scope expansion needed |
| verify-consistency SKILL.md | `/home/palantir/.claude/skills/verify-consistency/SKILL.md` | Cross-file reference checking baseline |
| manage-skills SKILL.md | `/home/palantir/.claude/skills/manage-skills/SKILL.md` | Skill lifecycle management, domain mapping |
| on-subagent-start.sh | `/home/palantir/.claude/hooks/on-subagent-start.sh` | Hook pattern reference (additionalContext injection) |
| impact-analysis-gap-report.md | `/home/palantir/.claude/agent-memory/analyst/impact-analysis-gap-report.md` | Prior analysis, 5-priority gap list |
| brainstorming_topic_infra.md | `/home/palantir/brainstorming_topic_infra.md` | CC technical reference used in brainstorm |
