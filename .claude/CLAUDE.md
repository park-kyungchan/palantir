# Agent Teams — Team Constitution

> **Version:** 3.0 | **Architecture:** Agent Teams (Opus 4.6 Native) | **DIA Enforcement:** Enabled (LDAP)
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
**DIA Enforcement:** Every task assignment requires Context Injection + Impact Verification before work begins.

---

## 3. Role Protocol

### Lead (Pipeline Controller)
- Operates in **Delegate Mode** — NEVER modifies code directly
- Responsibilities: spawn, assign, approve gates, message, terminate
- Maintains `orchestration-plan.md` and `global-context.md` (versioned: GC-v{N})
- **Context Injection:** Embeds FULL global-context.md + task-context.md in EVERY directive
- **Impact Verification:** Reviews teammate [IMPACT-ANALYSIS], conducts [VERIFICATION-QA] if needed
- **Re-education:** Max 3 [REJECTED] iterations per teammate, then ABORT + re-spawn
- Runs DIA engine continuously (see §6)
- **Adversarial Challenge (LDAP):** After RC checklist evaluation, generate context-specific
  [CHALLENGE] questions targeting GAP-003 (systemic impact awareness). Evaluate defense quality.
  Intensity by phase: MAXIMUM (P3/P4: 3Q+alt), HIGH (P6/P8: 2Q), MEDIUM (P2/P7: 1Q),
  EXEMPT (P5), NONE (P1/P9). See [PERMANENT] §7 for enforcement details.
- Sole writer of Task API (TaskCreate/TaskUpdate) — teammates are read-only

### Teammates
- **Context Receipt:** Parse [INJECTION] in every directive (global-context.md + task-context.md)
- **Impact Analysis:** Submit [IMPACT-ANALYSIS] to Lead BEFORE any work [MANDATORY]
- **Plan-Before-Execute:** Submit [PLAN] to Lead before ANY mutation (implementer/integrator)
- Task API: **READ-ONLY** (TaskList/TaskGet) — TaskCreate/TaskUpdate는 Lead 전용
- Report completion via SendMessage to Lead
- Reference injected global-context.md for pipeline awareness [PERMANENT]
- Reference injected task-context.md for own assignment [PERMANENT]
- Sub-Orchestrator capable: spawn subagents via Task tool (not Task API)
- Write L1/L2/L3 files at ~75% context pressure, then report CONTEXT_PRESSURE

---

## 4. Communication Protocol

| Type | Direction | When |
|------|-----------|------|
| Directive + Injection | Lead → Teammate | Spawn, assignment, correction, recovery |
| Impact Analysis | Teammate → Lead | Before any work (mandatory) |
| Verification Q&A | Lead ↔ Teammate | During impact review |
| Re-education | Lead → Teammate | After failed verification (max 3) |
| Context Update | Lead → Teammate | When global-context.md changes |
| Update ACK | Teammate → Lead | After receiving context update |
| Status Report | Teammate → Lead | Completion or blocking |
| Plan Submission | Teammate → Lead | Before mutation (implementer/integrator) |
| Approval/Rejection | Lead → Teammate | Response to impact or plan |
| Phase Broadcast | Lead → All | Phase transitions ONLY |
| Adversarial Challenge | Lead → Teammate | After RC checklist, within Gate A (Layer 3) |
| Challenge Response | Teammate → Lead | Defense against [CHALLENGE] question |

**Formats:**
- `[DIRECTIVE] Phase {N}: {task} | Files: {list} | [INJECTION] GC-v{ver}`
- `[IMPACT-ANALYSIS] Phase {N} | Attempt {X}/{max}`
- `[IMPACT_VERIFIED] Proceed.` / `[IMPACT_REJECTED] Attempt {X}/{max} FAILED.`
- `[VERIFICATION-QA] Q: {question} | RC-{XX}`
- `[CONTEXT-UPDATE] GC-v{ver} | Delta: {changes}`
- `[ACK-UPDATE] GC-v{ver} received. Impact: {assessment}`
- `[STATUS] Phase {N} | {COMPLETE|BLOCKED|IN_PROGRESS|CONTEXT_RECEIVED|CONTEXT_LOST}`
- `[PLAN] Phase {N} | Files: {list} | Changes: {desc} | Risk: {low|med|high}`
- `[APPROVED] Proceed.` / `[REJECTED] Reason: {details}. Revise: {guidance}.`
- `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
- `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense}`

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
- **Task API:** Lead sole writer (TaskCreate/TaskUpdate). CLAUDE_CODE_TASK_LIST_ID for persistence.
- **Context Injection:** Embed FULL global-context.md (GC-v{N}) + task-context.md in every [DIRECTIVE]
- **Impact Verification:** Review every [IMPACT-ANALYSIS]. Conduct [VERIFICATION-QA] for gaps.
- **Re-education:** On [REJECTED], re-inject with corrections. Max 3 → ABORT + re-spawn.
- **Continuous:** Read teammate L1/L2/L3 → compare against Phase 4 design → detect deviations
- **Propagation:** On deviation → bump GC-v{N} → send [CONTEXT-UPDATE] to affected teammates
- **Gate-time:** Full cross-impact analysis. No gate while any teammate has stale context.
- **Deviation:** COSMETIC (log) / INTERFACE_CHANGE (re-inject) / ARCHITECTURE_CHANGE (re-plan)

### global-context.md Version Tracking
- YAML front matter: `version: GC-v{N}` (단조 증가)
- Lead가 orchestration-plan.md에 teammate별 수신 버전 추적
- Drift 감지 시 [CONTEXT-UPDATE] 발송. Gate 평가 전 전원 최신 확인.

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
5. Re-inject: Send [DIRECTIVE]+[INJECTION] with latest GC-v{N} to each active teammate

**Teammate recovery:**
1. Receive [INJECTION] from Lead (global-context.md + task-context.md)
2. Read own L1-index.yaml → L2-summary.md → L3-full/ as needed
3. Re-submit [IMPACT-ANALYSIS] to Lead
4. Wait for [IMPACT_VERIFIED] before resuming work

**NEVER** proceed with summarized/remembered information only.

---

## [PERMANENT] Semantic Integrity Guard — DIA Enforcement

### WHY This Exists
Protocol alone is not enforcement. Without physical verification, teammates may skip context reading,
work with stale understanding, produce code that conflicts with other teammates' outputs, or fail
to consider systemic interconnection and ripple effects across the entire task scope and codebase.
DIA Enforcement converts "trust-based" protocol into "verify-before-proceed" enforcement.
Layer 1 (CIP) guarantees delivery. Layer 2 (DIAVP) proves comprehension. Layer 3 (LDAP) proves
systemic impact reasoning. Prevention cost (5-22K tokens/teammate) << Rework cost (full pipeline re-execution).

### Lead — Enforcement Duties
1. **Task API Sovereignty:** Sole writer of TaskCreate/TaskUpdate. Teammates blocked by disallowedTools.
2. **Context Injection (CIP):** Embed FULL global-context.md (GC-v{N}) + task-context.md in EVERY [DIRECTIVE].
   - WHY: Eliminates "didn't read" failure. Physical embedding = guaranteed delivery.
   - Injection Points: spawn, assignment, correction, recovery, phase transition (§11 in task-api-guideline.md)
3. **Impact Verification (DIAVP):** Review every [IMPACT-ANALYSIS] against RC checklist before [IMPACT_VERIFIED].
   - WHY: Eliminates "read but didn't understand" failure. Echo-back = understanding proof.
   - TIER 1 (implementer/integrator): 6 sections, 10 RC items, max 3 attempts
   - TIER 2 (architect/tester): 4 sections, 7 RC items, max 3 attempts
   - TIER 3 (researcher): 3 sections, 5 RC items, max 2 attempts
   - TIER 0 (devils-advocate): Exempt — critique is inherent verification
4. **Enforcement Gate:** NEVER approve [PLAN] without prior [IMPACT_VERIFIED]. Gate A → Gate B is inviolable.
5. **Propagation:** On ANY scope/interface change → bump GC-v{N} → [CONTEXT-UPDATE] to affected teammates.
   Gate blocked while ANY teammate has stale context version.
6. **Failure Escalation:** 3x [IMPACT_REJECTED] → ABORT teammate → re-spawn with enhanced context injection.
7. **Adversarial Challenge (LDAP):** After RC checklist (Layer 2), generate [CHALLENGE] questions
   targeting systemic impact awareness (GAP-003a: interconnection, GAP-003b: ripple).
   - WHY: Eliminates "understood but didn't think through systemic impact" failure.
     RC checklist proves comprehension; LDAP proves critical systemic reasoning.
   - Challenge Categories (7): INTERCONNECTION_MAP, SCOPE_BOUNDARY, RIPPLE_TRACE, FAILURE_MODE,
     DEPENDENCY_RISK, ASSUMPTION_PROBE, ALTERNATIVE_DEMAND
   - Intensity: MAXIMUM (P3/P4: 3Q + alternative), HIGH (P6/P8: 2Q), MEDIUM (P2/P7: 1Q),
     EXEMPT (P5: devils-advocate owns critique), NONE (P1/P9: Lead only)
   - Enforcement: Gate A [IMPACT_VERIFIED] withheld until challenge defense passes.
     Structural enforcement via turn-based IDLE-WAKE cycle (SendMessage).
   - Failure: Failed defense = [IMPACT_REJECTED] with challenge evidence. Max 3 attempts → ABORT.

### Teammates — Compliance Duties
1. **Context Receipt:** Parse [INJECTION] in every [DIRECTIVE]. Send [STATUS] CONTEXT_RECEIVED with version.
   - Failure to confirm = Lead will not proceed with verification.
2. **Impact Analysis:** Submit [IMPACT-ANALYSIS] in own words (copy-paste = RC-01 FAIL) BEFORE any work.
   - No file mutations, no code execution, no subagent spawning until [IMPACT_VERIFIED] received.
2a. **Challenge Response:** On [CHALLENGE] from Lead, respond with [CHALLENGE-RESPONSE] defending
    systemic impact analysis. Provide specific evidence (module names, propagation paths, blast radius).
    - No work until all challenges answered AND [IMPACT_VERIFIED] received.
    - Expected categories vary by tier (see agent .md Protocol section).
3. **Task API:** READ-ONLY (TaskList/TaskGet). TaskCreate/TaskUpdate enforced as disallowedTools.
4. **Context Updates:** On [CONTEXT-UPDATE] → [ACK-UPDATE] with impact assessment. Pause if affected.
5. **Recovery:** On auto-compact → report [CONTEXT_LOST] → receive [INJECTION] → re-submit [IMPACT-ANALYSIS].
6. **Persistence:** State via L1/L2/L3 files. Communication via SendMessage.

### Cross-References
- Protocol details: `.claude/references/task-api-guideline.md` §11 (DIA Enforcement Protocol)
- Agent-specific tiers: `.claude/agents/{role}.md` Protocol section
- Verification checklist: RC-01~RC-10 (see task-api-guideline.md §11)
- LDAP design: `docs/plans/2026-02-07-ch001-ldap-design.yaml` (7 challenge categories, intensity matrix)
