# Agent Teams — Team Constitution

> **Version:** 1.0 | **Architecture:** Agent Teams (Opus 4.6 Native)
> **Model:** claude-opus-4-6 (all instances) | **Runtime:** WSL2 + tmux + Claude Code CLI
> **Subscription:** Claude Max X20 (API-Free, CLI-Native only)

---

## 1. Team Identity

- **Workspace:** `/home/palantir`
- **Agent Teams Mode:** Enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
- **Display:** tmux split pane (`teammateMode: tmux`)
- **Lead:** Pipeline Controller (Delegate Mode default — never modifies code directly)
- **Teammates:** Dynamic spawning per phase (6 agent types available)

---

## 2. Phase Pipeline

| # | Phase | Zone | Teammate | Effort |
|---|-------|------|----------|--------|
| 1 | Discovery | PRE-EXEC | Lead only | max |
| 2 | Deep Research | PRE-EXEC | researcher (1-3) | max |
| 3 | Architecture | PRE-EXEC | architect (1) | max |
| 4 | Detailed Design | PRE-EXEC | architect (1) | high |
| 5 | Plan Validation | PRE-EXEC | devils-advocate (1) | max |
| 6 | Implementation | EXEC | implementer (1-4) | high |
| 7 | Testing | EXEC | tester (1-2) | high |
| 8 | Integration | EXEC | integrator (1) | high |
| 9 | Delivery | POST-EXEC | Lead only | medium |

**Shift-Left:** Pre-Execution (Phases 1-5) = 70-80% effort. Execution (6-8) = 20-30%.
**Gate Rule:** Lead approves EVERY phase transition. Results: APPROVE / ITERATE / ABORT.
**Iteration Budget:** Max 3 iterations per phase. On exceeded: ABORT or reduce scope.

---

## 3. Role Protocol

### Lead (Pipeline Controller)
- Operates in **Delegate Mode** — NEVER modifies code directly
- Responsibilities: spawn, assign, approve gates, message, terminate
- Maintains `orchestration-plan.md` and `global-context.md`
- Runs DIA (Dynamic-Impact-Awareness) engine continuously
- Reads teammate outputs at code-level for cross-impact analysis

### Teammates
- **Plan-Before-Execute:** Submit plan to Lead before ANY mutation (file edit, git op)
- Report completion via Shared Task List + Direct Message to Lead
- Reference `task-context.md` before EVERY Task API call ([PERMANENT])
- Sub-Orchestrator capable: decompose tasks, spawn subagents via Task tool
- Write L1/L2/L3 files at ~75% context pressure, then report CONTEXT_PRESSURE

---

## 4. Communication Protocol

| Type | Direction | When |
|------|-----------|------|
| Phase Directive | Lead → Teammate | Phase entry — task assignment |
| Status Report | Teammate → Lead | Task completion or blocking |
| Plan Submission | Teammate → Lead | Before any mutation |
| Approval/Rejection | Lead → Teammate | Response to plan |
| Phase Broadcast | Lead → All | Phase transitions ONLY (cost = 1:N) |
| Peer Query | Teammate → Teammate | Route through Lead preferred |

**Formats:**
- `[DIRECTIVE] Phase {N}: {task} | Files: {list}`
- `[STATUS] Phase {N} | {COMPLETE|BLOCKED|IN_PROGRESS} | {details}`
- `[PLAN] Phase {N} | Files: {list} | Changes: {desc} | Risk: {low|med|high}`
- `[APPROVED] Proceed.` / `[REJECTED] Reason: {details}. Revise: {guidance}.`

---

## 5. File Ownership Rules

- Each implementer assigned **non-overlapping file set** by Lead
- Concurrent editing of same file: **FORBIDDEN**
- Ownership documented in Shared Task List task description
- **Integrator** is the only role that can touch files across boundaries
- Read access: unrestricted for all roles

---

## 6. Orchestrator Decision Framework

### Spawn Matrix
- Phase 1, 9 = Lead only. All others require teammates.
- Count: determined by module_count or research_domain_count.
- Type: Phase 2→researcher, 3-4→architect, 5→devils-advocate, 6→implementer, 7→tester, 8→integrator.

### Gate Checklist
1. All phase output artifacts exist in teammate's output directory?
2. Output quality meets next-phase entry conditions?
3. No unresolved critical issues?
4. No inter-teammate conflicts?
5. L1/L2/L3 handoff files generated?

### DIA Engine (Lead)
- **Continuous:** Read teammate outputs → compare against Phase 4 design → detect deviations
- **Gate-time:** Full cross-impact analysis across all teammate outputs
- **Deviation response:** COSMETIC (log) / INTERFACE_CHANGE (update task-context) / ARCHITECTURE_CHANGE (re-plan)
- **User direct intervention:** Detect via Task List mutations → re-evaluate orchestration plan

### L1/L2/L3 Handoff
- L1: Index (YAML, ≤50 lines) — file list, status, decisions, unresolved items
- L2: Summary (MD, ≤200 lines) — narrative, findings, blockers, recommendations
- L3: Full Detail (directory) — complete reports, analysis, diffs, logs

### Output Directory
```
.agent/teams/{session-id}/
├── orchestration-plan.md
├── global-context.md
├── phase-{N}/
│   ├── gate-record.yaml
│   └── {role}-{id}/
│       ├── L1-index.yaml
│       ├── L2-summary.md
│       ├── L3-full/
│       ├── task-context.md
│       └── handoff.yaml
```

---

## 7. Safety Rules

**Blocked:** `rm -rf`, `sudo rm`, `chmod 777`, `DROP TABLE`, `DELETE FROM`
**Protected files:** `.env*`, `*credentials*`, `.ssh/id_*`, `**/secrets/**`
**Git safety:** Never force push main. Never skip hooks. No secrets in commits.

---

## 8. Compact Recovery

**Detection:** "This session is being continued from a previous conversation"

**Lead recovery:**
1. Read `orchestration-plan.md`
2. Read Shared Task List
3. Read current phase `gate-record.yaml`
4. Read active teammates' L1 indexes

**Teammate recovery:**
1. Read own `task-context.md`
2. Read own L1-index.yaml → L2-summary.md → L3-full/ as needed
3. Resume work from last recorded state

**NEVER** proceed with summarized/remembered information only.

---

## [PERMANENT] Semantic Integrity Guard

Every agent MUST read `.claude/references/task-api-guideline.md` before ANY Task API call.
Every teammate MUST read `task-context.md` before EVERY Task API call.
Every TaskCreate MUST include: objective, context in global pipeline, interface contracts,
file ownership, dependency chain, acceptance criteria, and semantic integrity check.
