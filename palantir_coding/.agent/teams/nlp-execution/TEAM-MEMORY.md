# Team Memory — NLP Execution (Phase 6)

## Lead
- [Decision] 2 persistent implementers, 6 rounds, 11 tasks
- [Decision] C-4.2 fix applied: T11/T12 strictly after T4 (not parallel)
- [Decision] C-2.2: 4 lost behaviors restored in T2 (CLAUDE.md)
- [Warning] T3 excluded — task-api-guideline.md in separate terminal
- [Finding] Most tasks = replace content with L3-v2 rewritten text (mechanical)
- [Finding] PT-specific tasks (T1, T5-T8) reference permanent-tasks-design.md

## implementer-1
- [Decision] T1: Structured skill as procedural utility (Steps 1-3), not phased pipeline
- [Finding] T1: Skill registered by system immediately after creation (confirmed in skill list)
- [Pattern] T1 interface contract with T5-T7: skill name "permanent-tasks", search pattern "[PERMANENT]", 5 exact section headers
- [Warning] T5-T7 implementers MUST use identical search pattern and section headers — silent failure if mismatched
- [Decision] T4: Full file replacement (Write) — 100% new content from L3-v2 §4 verbatim
- [Finding] T4: 8 sections (not 7 as task description stated) — "Agent Memory" is the 8th
- [Pattern] T4 interface contract with T11/T12: title "Shared Protocol for All Teammates", 8 section headers
- [Warning] T11/T12 agent .md files MUST reference "agent-common-protocol.md" — the title changed from "Agent Common Protocol" to "Shared Protocol for All Teammates"
- [Decision] T11: Full file Write for all 3 (frontmatter + new body) — cleanest approach for body replacement
- [Finding] T11: researcher 80→63, architect 90→74, DA 74→73 (total -34 lines, 14% reduction)
- [Pattern] T11: researcher/architect share 6-section structure; DA has unique 7-section (no Before Starting/If Lead Asks)
- [Warning] All 6 agent files now use opening: `Read and follow .claude/references/agent-common-protocol.md for shared procedures.`
- [Decision] T5: Incremental Edit approach (11 targeted edits) — content transformation, not full rewrite
- [Finding] T5: GC references on lines 190, 332, 412 are session artifacts (correct to keep), not SSoT references
- [Pattern] T5: Phase 0 uses same interface contract as T1: TaskList search for `[PERMANENT]`, skill name `permanent-tasks`
- [Finding] T5: Directive format changed from `[INJECTION] GC-v1: {embedded}` to `PT-ID: {task ID} | PT-v{N}` + task-context.md
- [Warning] T5: Phase 2/3 verification wording must align with CLAUDE.md §6 "Verifying Understanding" (NLP v6.0 style)
- [Decision] T7: Incremental Edit approach (21 targeted edits) — same pattern as T5 but more complex (DIA TIER 1 + LDAP HIGH)
- [Finding] T7: 532→572 lines (+40, from Phase 0 + PT references + extra context layer)
- [Pattern] T7: Directive now 5 context layers (PT-ID first, then GC-v4, task-context, review instructions, plan path) — matches T6 pattern
- [Finding] T7: Understanding Verification section replaces DIA Flow (7 steps→6 steps, 2 probing questions kept)
- [Warning] T7: Clean Termination now includes PT update step (PT-v{N}→PT-v{N+1}) — downstream skills must account for version bump

## implementer-2
- [Decision] Full file replacement via Write tool (not incremental Edit) — 100% new content
- [Decision] C-2.2c integrated as parenthetical extension of >4 files rule for natural flow
- [Decision] C-2.2d placed at end of Before Spawning section as operational guidance
- [Finding] Final file: 172 lines total, ~140 content lines (v6.0 136 + C-2.2 4)
- [Finding] v5.1→v6.0 reduction: 207→172 lines (17% total line reduction, but massive semantic simplification)
- [Warning] Downstream T4 must match: "PERMANENT Task", "PT-v{N}", "TaskGet" terminology exactly
- [Warning] §9 references agent-common-protocol.md for recovery — T4 must include "If You Lose Context" section
- [Decision] T8: Restructured hook into 3-path logic (team+GC → team+PT → no-team fallback) instead of flat fallback
- [Finding] T8: Original flat fallback caused PT teams to receive legacy GC messages from other teams' global-context.md
- [Pattern] T8: Hook JSON output format: `{ "hookSpecificOutput": { "hookEventName": "SubagentStart", "additionalContext": "..." } }`
- [Decision] T12: Body replacement only — YAML frontmatter preserved exactly for all 3 files
- [Finding] T12: implementer 115→80, tester 91→77, integrator 117→81 (total -85 lines across 3 files)
- [Pattern] T12: All 3 files follow 6-section template (Role, Before Starting Work, If Lead Asks, How to Work, Output, Constraints) + role-specific extras
- [Warning] T12: Tester uses "Report to Lead for relay" (no Edit tool), implementer/integrator use "Write to TEAM-MEMORY section" (has Edit tool)
- [Decision] T6: Full file Write (15+ dispersed changes make incremental Edit risky) — 275→316 lines
- [Finding] T6: Phase 0 pattern identical to brainstorming-pipeline (T5) — same TaskList/[PERMANENT]/TaskGet flow
- [Pattern] T6: Directive Construction now 5 context layers (PT-ID first, then GC-v3, L2, arch path, CH-001)
- [Finding] T6: All TIER/LDAP/DIA markers removed — 0 legacy references (Grep verified)
- [Warning] T6: Gate 4 On APPROVE now has 4 steps (was 3) — step 2 is PT update, downstream skills must account for PT-v{N+1}
- [Decision] T9: Incremental Edit (3 targeted edits) — only 3 of 10 sections needed updating
- [Finding] T9: Verified line counts via wc -l: CLAUDE.md 171, agents 442 total, protocol 82, hook 67
- [Pattern] T9: [PERMANENT] sections are untouchable anchors — 3 exist in MEMORY.md (Language, Skill Opt, Visibility)
