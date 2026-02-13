# Risk Architecture — Fork Agent Designs & Risk Register

## 1. Fork Agent .md Designs

### 1.1 pt-manager.md

```yaml
---
name: pt-manager
description: |
  Fork agent for permanent-tasks skill. Manages PERMANENT Task lifecycle
  (create, read-merge-write, notify teammates). Full Task API access.
  Spawned via context:fork from /permanent-tasks. Max 1 instance.
model: opus
permissionMode: default
memory: user
color: cyan
maxTurns: 30
tools:
  - Read
  - Glob
  - Grep
  - Write
  - TaskList
  - TaskGet
  - TaskCreate
  - TaskUpdate
  - AskUserQuestion
disallowedTools: []
---
# PT Manager

Fork-context agent for /permanent-tasks skill execution. You manage the
PERMANENT Task — the Single Source of Truth for pipeline execution.

## Role
You create or update the PERMANENT Task based on skill content and $ARGUMENTS.
You do NOT have conversation history — work only with the rendered skill content,
Dynamic Context, and $ARGUMENTS provided to you.

## Context Sources (Priority Order)
1. **$ARGUMENTS** — user's requirement description or context payload
2. **Dynamic Context** — git log, plans list, infrastructure version (pre-rendered)
3. **TaskList/TaskGet** — existing PT content for Read-Merge-Write
4. **AskUserQuestion** — probe user for missing context when $ARGUMENTS is insufficient

## How to Work
- Follow the skill body instructions exactly (Steps 1, 2A/2B, 3)
- Use AskUserQuestion when $ARGUMENTS is ambiguous or insufficient
- Write results through Task API only — no file output needed
- For teammate notifications (Step 2B.4): you cannot notify teammates directly.
  Include notification needs in your terminal summary output for Lead to relay.

## Error Handling
You operate in fork context — no coordinator, no team recovery.
- TaskList returns empty → treat as "not found", proceed to Step 2A (create)
- TaskGet fails for found ID → report error to user via AskUserQuestion, suggest manual check
- $ARGUMENTS empty → extract requirements from Dynamic Context only; if insufficient, AskUserQuestion
- Description too large → split Impact Map to file reference; PT holds path only
- Multiple [PERMANENT] tasks found → use first one, warn user about duplicates
- Any unrecoverable error → present clear error to user, do not retry silently

## Key Principles
- **Single Source of Truth** — one PERMANENT Task per project, not per pipeline
- **Refined state always** — consolidation produces a clean document, never an append log
- **Interface contract** — section headers and `[PERMANENT]` search pattern are shared contracts
- **Fork-isolated** — you have no conversation history, no coordinator, no teammates to escalate to
- **User is your recovery path** — when context is insufficient, ask the user directly

## Constraints
- No conversation history available — rely on $ARGUMENTS and Dynamic Context
- Full Task API is the EXCEPTION granted by D-10 — use responsibly
- Section headers in PT description are interface contracts — never rename them
- Always use Read-Merge-Write for updates (never overwrite)

## Never
- Create duplicate [PERMANENT] tasks (check TaskList first, always)
- Append without consolidating — always deduplicate, resolve contradictions, elevate abstraction
- Change the `[PERMANENT]` subject search pattern (interface contract with Phase 0)
- Change PT section header names (interface contract with all pipeline skills)
- Overwrite existing PT without reading current state first (Read-Merge-Write mandatory)
- Use TaskCreate for anything other than [PERMANENT] tasks
- Attempt direct teammate notification — you have no SendMessage access; report notification needs in terminal summary for Lead to relay
- Notify teammates for LOW-impact changes (only CRITICAL impact warrants Lead relay)
```

**Tool Justification:**

| Tool | Why Needed | Skill Reference |
|------|-----------|-----------------|
| TaskList | Step 1: discover [PERMANENT] task | Line 50-51 |
| TaskGet | Step 2B.1: read current PT | Line 108 |
| TaskCreate | Step 2A: create new PT | Line 86-93 |
| TaskUpdate | Step 2B.3: bump version and update | Line 141-145 |
| AskUserQuestion | Clarify ambiguous intent, duplicate warning | Lines 69, 72 |
| Read | Read MEMORY.md, plans for context enrichment | Implicit |
| Glob/Grep | Discover files referenced in impact map | Implicit |
| Write | Create output files if needed | Recovery |

**Design Rationale for Full Task API:**
- permanent-tasks is the ONLY skill that creates tasks (TaskCreate)
- All other fork agents only need TaskUpdate (for PT version bumps)
- D-10 exception is specifically designed for this case
- Risk of misuse: LOW — skill body constrains usage to [PERMANENT] pattern only
- NL instruction "Never create duplicate [PERMANENT] tasks" provides guardrail

---

### 1.2 delivery-agent.md

```yaml
---
name: delivery-agent
description: |
  Fork agent for delivery-pipeline skill. Handles Phase 9 delivery:
  consolidation, git commit, PR creation, cleanup. TaskUpdate only.
  Spawned via context:fork from /delivery-pipeline. Max 1 instance.
model: opus
permissionMode: default
memory: user
color: yellow
maxTurns: 50
tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - TaskList
  - TaskGet
  - TaskUpdate
  - AskUserQuestion
disallowedTools:
  - TaskCreate
---
# Delivery Agent

Fork-context agent for /delivery-pipeline skill execution. You handle Phase 9
(Delivery) — the terminal phase of the pipeline.

## Role
You consolidate pipeline output, create git commits, optionally create PRs,
archive session artifacts, and update MEMORY.md. You execute the full Phase 9
flow as defined in the skill body.

## Context Sources (Priority Order)
1. **Dynamic Context** — gate records, archives, git status, session dirs (pre-rendered)
2. **$ARGUMENTS** — feature name or session-id
3. **TaskList/TaskGet** — PERMANENT Task for pipeline context
4. **File reads** — gate records, L1/L2, orchestration plans across sessions

## How to Work
- Follow the skill body instructions exactly (Phase 0 → 9.1 → 9.2 → 9.3 → 9.4)
- Every external action requires USER CONFIRMATION via AskUserQuestion
- Use Bash for git operations only (commit, status, diff, gh pr create)
- Use Edit for MEMORY.md merge (Read-Merge-Write pattern)
- Use Write for ARCHIVE.md creation

## User Confirmation Gates
You MUST get explicit user approval before:
1. Session set confirmation (9.1)
2. MEMORY.md write (Op-2)
3. Git commit (Op-4)
4. PR creation (Op-5)
5. Artifact cleanup (Op-6)
Never bypass these gates. Use AskUserQuestion for each.

## No Nested Skill Invocation
If no PERMANENT Task is found in Phase 0, do NOT attempt to invoke /permanent-tasks.
Instead, inform the user: "No PERMANENT Task found. Please run /permanent-tasks first,
then re-run /delivery-pipeline." This avoids the double-fork problem.

## Error Handling
You operate in fork context — no coordinator, no team recovery.
- No Phase 7/8 output found → inform user, suggest /verification-pipeline
- PT and GC both missing → warn user, attempt discovery from gate records alone
- Git working tree clean → warn, offer to skip to Phase 9.4 (ARCHIVE + cleanup only)
- Commit rejected by user → offer modification or skip; handle MEMORY.md state
- PR creation fails → report error, provide manual `gh pr create` command for user
- MEMORY.md merge conflict → present both versions, let user choose
- Session directory not found → fall back to PT for cross-session references
- User cancellation at any gate → preserve all artifacts created so far, report partial completion
- Fork termination mid-sequence → operations designed to be idempotent; user can re-run safely

## Key Principles
- **User confirms everything external** — git, PR, MEMORY.md, cleanup all need explicit approval
- **Consolidation before delivery** — knowledge persistence (9.2) precedes git operations (9.3)
- **Multi-session by default** — scan across ALL related session directories, not just one
- **Present, don't assume** — show discovered sessions and let user confirm the set
- **Idempotent operations** — ARCHIVE.md write is overwrite-safe, MEMORY.md is Read-Merge-Write
- **Fork-isolated** — no teammates, no coordinator, user is your only interaction partner
- **Terminal** — no auto-chaining, no "Next:" section, pipeline ends here

## Constraints
- No TaskCreate — you can only update existing tasks (mark DELIVERED)
- No conversation history — rely on Dynamic Context and file reads
- Stage specific files only — never use `git add -A` or `git add .`
- Terminal phase — no auto-chaining to other skills after completion

## Never
- Auto-commit without user confirmation (every external action needs approval)
- Force push or skip git hooks
- Include `.env*`, `*credentials*`, `.ssh/id_*`, `**/secrets/**` in commits
- Use `git add -A` or `git add .` (stage specific files only)
- Invoke /permanent-tasks or any other skill (no nested fork invocation)
- Add a "Next:" section to the terminal summary
- Delete L1/L2/L3 directories or ARCHIVE.md during cleanup
- Write MEMORY.md without user preview and approval
- Silently auto-discover sessions without user confirmation
- Retry failed git operations without user guidance
```

**Tool Justification:**

| Tool | Why Needed | Skill Reference |
|------|-----------|-----------------|
| TaskList | Phase 0: discover PT | Line 63 |
| TaskGet | Phase 0 + Op-1: read PT content | Line 72, 149 |
| TaskUpdate | Op-1: mark DELIVERED, Op-7: close tasks | Line 156, 292-294 |
| AskUserQuestion | 5+ user confirmation gates | Lines 179, 229, 253, 286 |
| Bash | Op-4: git commit; Op-5: gh pr create | Lines 215-231 |
| Read | Gate records, L1/L2, MEMORY.md, ARCHIVE.md | Throughout |
| Glob | Session directory discovery, artifact inventory | Lines 269-270 |
| Grep | Session scanning, file reference checking | Implicit |
| Edit | Op-2: MEMORY.md merge | Line 174 |
| Write | Op-3: ARCHIVE.md creation | Line 196 |

**Why no TaskCreate:**
- delivery-pipeline Phase 0 can invoke /permanent-tasks for PT creation
- In fork context, nested skill invocation is a Critical Unknown (#4)
- Instead: abort with user message if no PT found
- This eliminates the double-fork problem at cost of one extra user step
- delivery-pipeline NEVER creates tasks in normal flow — only reads/updates

**maxTurns: 50 Rationale:**
- 7 operations (Phase 0 + 9.1-9.4 with sub-ops)
- 5+ user gates × ~3 turns each = ~15 turns for gates alone
- File reading/writing across multiple sessions = ~10-15 turns
- Git operations + PR = ~5 turns
- Buffer for error handling and re-presentation = ~10 turns
- Total estimate: 35-45 turns → 50 provides safe margin

---

### 1.3 rsil-agent.md

```yaml
---
name: rsil-agent
description: |
  Shared fork agent for rsil-global and rsil-review skills. INFRA quality
  assessment and review. Can spawn research agents for deep analysis.
  TaskUpdate only. Spawned via context:fork. Max 1 instance.
model: opus
permissionMode: default
memory: user
color: purple
maxTurns: 50
tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Task
  - TaskList
  - TaskGet
  - TaskUpdate
  - AskUserQuestion
disallowedTools:
  - TaskCreate
---
# RSIL Agent

Shared fork-context agent for /rsil-global and /rsil-review skill execution.
You perform INFRA quality assessment using the 8 Meta-Research Lenses and
AD-15 filter.

## Role
You execute whichever RSIL skill invoked you — the skill body defines your
specific workflow. rsil-global is lightweight (Tier 1-3 observation),
rsil-review is deep (parallel research + integration audit).

## Context Sources (Priority Order)
1. **Dynamic Context** — session dirs, git diff, agent memory (pre-rendered)
2. **$ARGUMENTS** — optional concern (rsil-global) or target+scope (rsil-review)
3. **TaskList/TaskGet** — PERMANENT Task for pipeline context
4. **Agent memory** — ~/.claude/agent-memory/rsil/MEMORY.md (cross-session patterns)

## How to Work

### When executing rsil-global:
- Follow G-0 → G-1 → G-2 (rare) → G-3 → G-4 flow
- Stay within ~2000 token observation budget
- Spawn codebase-researcher via Task tool ONLY at Tier 3 (rare escalation)
- Most runs complete at Tier 1 with zero findings

### When executing rsil-review:
- Follow R-0 → R-1 → R-2 → R-3 → R-4 flow
- R-0: synthesize research questions and integration axes (your core work)
- R-1: spawn claude-code-guide + codebase-researcher in parallel via Task tool
- R-2: merge and classify findings
- R-3: apply user-approved changes via Edit
- R-4: update tracker and agent memory

## Agent Spawning (R-1 / G-2)
Use the Task tool to spawn research agents:
- subagent_type: "claude-code-guide" or "codebase-researcher"
- Include your synthesized directive in the prompt
- These are one-shot invocations, not persistent teammates
- Wait for both to complete before proceeding
- If Task tool spawning fails: fall back to sequential in-agent execution
  (read CC docs + axis files directly yourself — slower but viable)

## Error Handling
You operate in fork context — no coordinator, no team recovery.
- $ARGUMENTS empty or unclear (rsil-review) → AskUserQuestion to clarify target and scope
- TARGET file not found → AskUserQuestion to verify file path
- No Lenses applicable to target → warn user: "Low Lens coverage. Integration audit only?"
- Spawned agent returns empty/error (R-1) → proceed with your own analysis + other agent's results
- Both spawned agents fail → fall back to sequential in-agent execution (read files directly)
- All findings PASS → report "Clean review. No changes needed."
- User cancellation → preserve partial tracker updates, no file changes applied
- Tracker file not found → create initial section structure, then append
- Agent memory not found → create with seed data from tracker
- Tier 1 reads exceed observation budget → cap at 3 L1 files + 1 gate record, note truncation

## Key Principles
- **AD-15 inviolable** — Category A (Hook) REJECT, Category B (NL) ACCEPT, Category C (L2) DEFER
- **Findings-only output** — user approves before any file modifications (R-3)
- **Lenses are universal, scope is dynamic** — same 8 lenses generate different questions per target
- **R-0 synthesis is the core value** — the universal→specific bridge is mandatory for every review
- **Accumulated context distills into Lenses** — individual findings stay in tracker, not SKILL.md
- **Fork-isolated** — no Lead to escalate to, no coordinator, user is your interaction partner
- **Terminal** — user decides next step after completion, no auto-chaining

## Constraints
- No TaskCreate — only read tasks and update PT version
- INFRA scope only — never assess application code
- Findings-only until user approves — no preemptive file modifications

## Never
- Modify files without user approval (findings-only until R-3 approval)
- Auto-chain to any other skill after completion
- Propose adding a new hook (AD-15: hook count is inviolable)
- Promote Category C findings to Category B (if Layer 2 is needed, it's DEFER)
- Skip G-0 classification in rsil-global (observation window type determines reading scope)
- Exceed ~2000 token observation budget in rsil-global without noting truncation
- Spawn agents for Tier 1 or Tier 2 work in rsil-global (agents only at Tier 3)
- Assess application code (INFRA scope only — .claude/ and pipeline artifacts)
- Embed raw findings in agent memory — only universal Lens-level patterns belong there
```

**Tool Justification:**

| Tool | Why Needed | Skill Reference |
|------|-----------|-----------------|
| Task | R-1: spawn claude-code-guide + codebase-researcher; G-2: spawn codebase-researcher | rsil-review:336-343, rsil-global:243-253 |
| TaskList | Phase 0: discover PT | Both skills |
| TaskGet | Phase 0: read PT content | Both skills |
| TaskUpdate | R-4/G-4: update PT with RSIL results | rsil-review:487, rsil-global:implied |
| AskUserQuestion | Clarify target, present findings, BREAK handling | rsil-review:239, rsil-global:311 |
| Read | Target files, tracker, agent memory, session artifacts | Throughout |
| Glob/Grep | File discovery, cross-reference scanning | Throughout |
| Edit | R-3: apply FIX items to INFRA files | rsil-review:436-448 |
| Write | G-4/R-4: tracker updates, agent memory updates | rsil-global:322-348, rsil-review:459-483 |

**Why SHARED agent (not separate):**
1. Both skills share 80%+ tool requirements (Read, Glob, Grep, Edit, Write, TaskList, TaskGet, TaskUpdate, AskUserQuestion)
2. rsil-review adds only Task tool — rsil-global rarely needs it (Tier 3 only)
3. Agent .md defines the CEILING of permissions; skill body constrains actual usage
4. rsil-global explicitly says "No agent spawning for Tier 1/2" — NL sufficient guardrail
5. Single file = simpler maintenance, consistent frontmatter evolution
6. maxTurns: 50 covers both (rsil-global finishes in ~15 turns naturally)

**Trade-off acknowledged:**
- rsil-global gets Task tool access it rarely needs (~5% of runs hit Tier 3)
- Principle of least privilege slightly violated
- Mitigation: NL instruction "Spawn codebase-researcher via Task tool ONLY at Tier 3"
- This is the same pattern used by implementer (has Bash but NL constrains usage scope)

---

## 2. Comprehensive Risk Register

### RISK-1: Custom Agent Resolution Failure
**Severity:** HIGH | **Likelihood:** LOW (D-15 confirmed feasibility) | **Impact:** CATASTROPHIC
**Description:** If `agent:` field cannot reference `.claude/agents/{name}.md` at runtime, all 3 fork agent designs become invalid. The entire fork architecture collapses.
**Evidence:** D-15 confirms feasibility. palantir-dev.md shows `agent: Explore | Plan | custom` syntax. CC research indicates custom agent support. However, zero production usage of custom agents in fork context exists in this codebase.
**Mitigation:**
- Primary: Pre-deployment validation test — create minimal fork skill with `agent: "pt-manager"` and verify agent .md loads
- Fallback: Use `agent: general-purpose` with skill body containing all agent instructions. Loses .md separation but functionally works (70% confidence primary works; fallback always available)
- Impact of fallback: 3 agent .md files become unused, skill bodies grow by ~30-50L each
**Cascade:** Blocks D-11 entirely. D-9 (fork) still works with fallback. D-10 (Task API exception) still needed.

### RISK-2: Permanent-Tasks Fork Loses Conversation History
**Severity:** MEDIUM-HIGH | **Likelihood:** CERTAIN (by design) | **Impact:** LOCALIZED
**Description:** Fork agents start clean. permanent-tasks Step 2A says "extract from full conversation + $ARGUMENTS" — conversation is empty in fork context. Degraded experience for manual (non-pipeline) invocation.
**Evidence:** Fork mechanism confirmed: "Fork agent does NOT inherit invoking agent's conversation history" (codebase-researcher-2 L2).
**Mitigation Strategy (3-layer):**
1. **Pipeline auto-invocation (primary use case):** $ARGUMENTS carries structured context from Phase 0 code. FULLY MITIGATED — no degradation.
2. **Manual invocation with rich $ARGUMENTS:** User provides `/permanent-tasks "Full description of what changed: X, Y, Z and why"`. Dynamic Context (git log, plans) supplements. PARTIALLY MITIGATED — depends on user providing good input.
3. **Manual invocation with sparse $ARGUMENTS:** AskUserQuestion probes for missing context. Agent can also Read recent git log, plans, existing PT. DEGRADED BUT FUNCTIONAL — more interactive, slower.
**Residual risk:** Users accustomed to Lead-in-context mode (rich conversation) will experience step-down in context richness. Documentation should set expectations.
**Cascade:** Affects permanent-tasks only. No cascade to other skills.

### RISK-3: Delivery-Pipeline Fork Complexity
**Severity:** MEDIUM | **Likelihood:** HIGH | **Impact:** MODERATE
**Description:** delivery-pipeline has 5+ user confirmation gates, git operations, nested /permanent-tasks invocation, multi-session discovery, and MEMORY.md merge. Fork isolation adds complexity without simplification.
**Evidence:** 471L skill, 7 distinct operations, highest fork-risk rating (HIGH) per codebase-researcher-2.
**Mitigation Strategy:**
1. **Nested skill elimination:** Replace "invoke /permanent-tasks" with "abort if no PT" message. Eliminates double-fork problem entirely. Cost: one extra user step.
2. **Idempotent operations:** ARCHIVE.md write is idempotent (overwrite). MEMORY.md uses Read-Merge-Write (rerunnable). Git commit is naturally atomic.
3. **Recovery path:** If fork terminates mid-sequence, user re-runs /delivery-pipeline. Discovery algorithm (9.1) picks up partial state from disk.
4. **Phased adoption:** Fork delivery-pipeline LAST, after pt-manager and rsil-agent are validated. Validate simpler fork agents first to build confidence.
**Residual risk:** Fork termination between MEMORY.md write (Op-2) and git commit (Op-4) leaves dirty state. Recovery exists but requires user re-run.
**Cascade:** If delivery fork fails, fallback to Lead-in-context for /delivery-pipeline while other 3 skills use fork.

### RISK-4: Skills Preload Token Cost
**Severity:** LOW | **Likelihood:** CERTAIN | **Impact:** MINIMAL
**Description:** `skills:` preload in coordinator frontmatter injects full skill content at startup (~400-600L per skill). Unfavorable ratio: persistent context cost vs. intermittent awareness benefit.
**Evidence:** CC research §9.1 confirms skills preload mechanism. Each skill description already loads at session start (~100 tokens). Full content adds 400-600L.
**Assessment:**
- Coordinator awareness of skill content: NICE TO HAVE, not essential
- Lead already embeds relevant skill excerpts in coordinator directives
- Dynamic Context Injection provides session state more efficiently
- 400-600L per preloaded skill × 5 pipeline skills = 2000-3000L permanent context cost
**Verdict: DEFER.** Cost exceeds benefit. Keep current model where Lead selectively references skill content in directives.
**Cascade:** None. This is an independent optimization decision.

### RISK-5: Big Bang Deployment (20+ files simultaneously)
**Severity:** HIGH | **Likelihood:** MEDIUM | **Impact:** BROAD
**Description:** D-8 mandates all 9 skills + 8 coordinator .md + 3 new agent .md changed simultaneously for interface consistency. A syntax error in any single file can break the entire INFRA.
**Evidence:** 20+ files = 9 SKILL.md + 8 coordinator .md + 3 new agent .md + CLAUDE.md §10 + agent-common-protocol.md = 22 files minimum.
**Mitigation Strategy:**
1. **Pre-commit validation:** Validate all YAML frontmatter parses correctly (simple Bash check)
2. **Atomic commit:** Single git commit for all changes — easy revert via `git revert`
3. **Smoke test sequence:** After commit, invoke each fork skill with trivial $ARGUMENTS to verify:
   a. pt-manager: `/permanent-tasks "test"` — verify fork loads agent .md
   b. rsil-agent: `/rsil-global` — verify fork loads + Dynamic Context renders
   c. delivery-agent: skip (requires pipeline artifacts; validate manually)
4. **Rollback plan:** `git revert HEAD` restores previous state. No database or external state to unwind.
5. **Staging approach:** Implementers work on non-overlapping file sets. Integrator merges with cross-boundary verification.
**Residual risk:** Subtle NL instruction conflicts may not surface in smoke testing. Detected by next pipeline run or /rsil-global.
**Cascade:** Failure affects entire INFRA. Rollback available but disruptive.

### RISK-6: Fork Agent Crash Recovery
**Severity:** MEDIUM | **Likelihood:** LOW | **Impact:** LOCALIZED
**Description:** Fork agent may crash due to: context limit exhaustion, tool timeout, MCP server failure, or CC platform error. Orphaned process and partial state.
**Evidence:** Fork lifecycle unclear (Critical Unknown #6). If fork persists after crash, it could consume resources.
**Mitigation:**
- Fork agents write intermediate state to disk (L1/L2 for rsil-agent, ARCHIVE.md for delivery-agent, Task API for pt-manager)
- pt-manager: Task API operations are atomic — crash between operations loses at most one update
- delivery-agent: each Op is designed to be re-runnable (idempotent discovery, Read-Merge-Write for MEMORY)
- rsil-agent: tracker updates are append-only, agent memory is Read-Merge-Write
- CC platform handles fork cleanup (terminate on completion or error)
**Residual risk:** If fork crashes after writing ARCHIVE.md but before git commit, user must manually re-run.
**Cascade:** No cascade — each fork is isolated by design.

### RISK-7: Fork Agent State Corruption
**Severity:** MEDIUM | **Likelihood:** LOW | **Impact:** MODERATE
**Description:** Fork agent writes to shared files (MEMORY.md, tracker, PT). If fork crashes mid-write, shared files may be corrupted.
**Mitigation:**
- Task API operations are atomic (single API call per update)
- File writes (ARCHIVE.md, tracker) are complete-or-nothing (Write tool)
- Edit operations (MEMORY.md) have rollback via `git checkout -- path`
- Read-Merge-Write pattern is designed for idempotent recovery
**Residual risk:** Extremely low — Claude Code's Write tool is atomic at the OS level.

### RISK-8: Task List Scope Confusion
**Severity:** MEDIUM | **Likelihood:** MEDIUM | **Impact:** MODERATE
**Description:** Which task list does fork agent see? If fork gets isolated task list, PT discovery fails. If fork shares main session task list, concurrent modifications possible.
**Evidence:** Critical Unknown #3 from Phase 2 research. Team-based task scoping exists in Agent Teams.
**Assessment:** Fork agents invoked by Lead should share Lead's task list context (same session). This is the expected behavior for `context: fork` — the fork is an extension of Lead, not an independent team member.
**Mitigation:**
- Pre-deployment validation: verify fork agent can call TaskList and see the same [PERMANENT] task as Lead
- If isolated: pt-manager becomes non-functional (cannot discover PT). Fallback: pass PT task ID via $ARGUMENTS
**Cascade:** Blocks pt-manager and delivery-agent Phase 0 if isolated. rsil-agent less affected (PT is optional context).

### ~~RISK-9: SendMessage Scope in Fork~~ — ELIMINATED
Removed by cross-lens resolution: SendMessage removed from pt-manager tools.
Fork agents do not join teams (interface-architect §1.7, structure-architect fork template).
Teammate notifications delegated to Lead relay via pt-manager's terminal summary output.

---

## 3. Open Questions Resolution

### OQ-1: Can fork agent spawn subagents via Task tool?

**Analysis:**
- Fork agent is a CC subagent. The Task tool is a standard CC tool.
- If Task tool is listed in agent .md `tools:`, the fork agent should have access.
- CC's tool gating is per-agent-instance based on frontmatter — no special fork restriction documented.
- Risk: fork may not have team context for `team_name` parameter.
- Counter-evidence: rsil-review R-1 spawns are one-shot (no team_name needed).

**Verdict: YES, with high confidence (85%).**
- Task tool works like any other tool — frontmatter controls access.
- rsil-agent gets Task tool in its frontmatter → can spawn.
- Spawned agents are one-shot (no team context needed for R-1).
- Pre-deployment validation: test rsil-agent spawning a codebase-researcher.

**If NO (fallback):**
- rsil-review stays Lead-in-context (Lead orchestrates R-1 directly)
- rsil-global stays fork (doesn't need Task for Tier 1/2)
- rsil-agent.md removes Task tool, split into rsil-fork-agent (global only) + Lead-in-context (review)

### OQ-2: Template variant count — 2 or 3?

**Analysis:**
- 2 variants: coordinator-based + fork-based
- 3 variants: coordinator-based + fork-simple (rsil, permanent-tasks) + fork-complex (delivery)

**Assessment of delivery-agent complexity:**
- 50 maxTurns vs 30 for pt-manager
- Bash access (unique among fork agents)
- 5+ user gates (more than any other fork agent)
- Multi-session discovery (unique complexity)
- But: still follows same fork pattern (context:fork + agent: + Dynamic Context + $ARGUMENTS)

**Verdict: 2 variants.** Delivery-agent's complexity is in the SKILL body, not the template structure. The fork template is the same: frontmatter (context:fork, agent:) + Spawn Section (N/A for fork) + Directive Section ($ARGUMENTS + Dynamic Context) + Interface Section (PT read/write) + Cross-Cutting (references). Delivery's unique complexity is captured in per-skill delta, not a separate template.

### OQ-3: GC elimination timeline

**Analysis:**
- GC has 14 section types → proposed reduction to 3 (D-14)
- 9 "Phase N Entry Requirements" sections replaced by L2 Downstream Handoff
- 2 sections migrate to PT
- 3 remain (execution metrics, gate records, version marker)

**Elimination approach:**
- Phase N Entry Requirements: skills currently write them at gate transitions
- L2 Downstream Handoff already exists in agent-common-protocol.md
- Next-phase skills currently read GC for entry requirements
- After redesign: next-phase skills read predecessor's L2 directly

**Verdict: Remove in v9.0 (this release).** The L2 Downstream Handoff mechanism is already operational. GC Phase N Entry Requirements are redundant. Big Bang approach (D-8) is the right time to remove them — all skills change simultaneously, so the interface contract changes atomically.

**Implementation notes:**
- Remove GC write instructions from 5 pipeline skills
- Remove GC read instructions from 5 pipeline skills
- Keep 3 GC sections (execution metrics, gate records, version marker) as session scratch
- GC becomes optional session scratch, not authoritative state

---

## 4. Failure Mode Catalog

### FM-1: Fork Loads Wrong Agent .md
**Trigger:** Typo in skill frontmatter `agent:` field
**Impact:** Fork runs with wrong tools/permissions
**Detection:** Immediate — wrong agent behavior visible to user
**Recovery:** Fix typo, re-invoke skill

### FM-2: Dynamic Context Command Failure
**Trigger:** Shell command in `!command` syntax fails
**Impact:** Skill load failure (entire skill doesn't render)
**Detection:** Immediate — skill invocation error
**Recovery:** Fix command syntax (use `2>/dev/null || echo "{}"` pattern)
**Prevention:** All Dynamic Context commands already use `2>/dev/null` safety pattern

### FM-3: $ARGUMENTS Too Large for Task API
**Trigger:** User provides very long $ARGUMENTS that, combined with PT description, exceeds Task API limits
**Impact:** TaskCreate or TaskUpdate fails
**Detection:** API error returned to fork agent
**Recovery:** pt-manager truncates or summarizes $ARGUMENTS; splits Impact Map to file reference

### FM-4: Concurrent PT Modification
**Trigger:** Fork agent (pt-manager) updates PT while a teammate also reads PT mid-update
**Impact:** Teammate reads partial/stale PT state
**Detection:** Not easily detected (no locking mechanism)
**Recovery:** Teammate re-reads PT on next TaskGet call
**Prevention:** pt-manager's Step 2B.4 notification mechanism alerts teammates of changes

### FM-5: Git Conflict in Delivery
**Trigger:** Another process modifies same files between delivery-agent's read and commit
**Impact:** Git commit fails or includes unintended changes
**Detection:** `git status` shows unexpected changes
**Recovery:** delivery-agent presents conflicts to user via AskUserQuestion
**Prevention:** Delivery is terminal phase — other agents should be shut down

### FM-6: Agent Spawning Deadlock in Fork
**Trigger:** rsil-agent spawns 2 agents (R-1) and one hangs indefinitely
**Impact:** rsil-agent blocked waiting for agent completion
**Detection:** maxTurns timeout (50 turns)
**Recovery:** CC platform terminates fork on maxTurns. User re-runs with narrower scope.
**Prevention:** Use `max_turns` parameter on spawned agents; timeout parameter on Bash calls

### FM-7: MEMORY.md Merge Conflict
**Trigger:** delivery-agent's Read-Merge-Write reads old MEMORY.md, user modifies it externally, agent writes merged result
**Impact:** User's external changes lost
**Detection:** Post-write `git diff` shows unexpected delta
**Recovery:** `git checkout -- MEMORY.md` to restore, then re-run delivery
**Prevention:** User confirmation gate (Op-2) includes diff preview

---

## 5. Phased Adoption Strategy

Given the risks identified, recommend this deployment sequence:

### Phase A: Validation (before any production deployment)
1. Create 3 agent .md files
2. Create minimal test skill with `context: fork` + `agent: "pt-manager"`
3. Verify: custom agent resolution works (RISK-1 primary)
4. Verify: fork agent sees main session task list (RISK-8)
5. Verify: fork agent can spawn subagents via Task tool (OQ-1)
6. If any fail → activate fallback architecture before proceeding

### Phase B: Low-Risk Fork (rsil-global)
- Deploy rsil-agent + fork rsil-global skill
- Lowest risk (rarely spawns agents, read-heavy, optional PT)
- Validates fork mechanism in production with minimal blast radius

### Phase C: Medium-Risk Fork (rsil-review, permanent-tasks)
- Deploy fork rsil-review (validates agent spawning from fork)
- Deploy fork permanent-tasks with pt-manager (validates Task API from fork)
- Monitor for RISK-2 degradation in manual invocation

### Phase D: High-Risk Fork (delivery-pipeline)
- Deploy fork delivery-pipeline with delivery-agent LAST
- Only after Phases B+C prove stable
- Most complex fork — benefits from lessons learned

**Note:** D-8 (Big Bang) mandates simultaneous deployment. The phased adoption above is a TESTING sequence, not a deployment sequence. All files are committed together, but validation happens in the order above.

---

## 6. RISK-4 Detailed Assessment: Skills Preload

### Token Cost Analysis

| Coordinator | Preloaded Skills | Estimated Cost |
|-------------|-----------------|----------------|
| research-coordinator | brainstorming-pipeline | ~600L |
| architecture-coordinator | brainstorming-pipeline | ~600L |
| planning-coordinator | agent-teams-write-plan | ~360L |
| validation-coordinator | plan-validation-pipeline | ~430L |
| execution-coordinator | agent-teams-execution-plan | ~690L |
| testing-coordinator | verification-pipeline | ~570L |
| ALL coordinators | — | ~3,250L total |

### Cost-Benefit Analysis

**Benefits:**
- Coordinators aware of their skill's orchestration logic
- Faster context when Lead references skill instructions
- Self-service: coordinator can re-read skill without Lead

**Costs:**
- ~3,250L permanent context in each coordinator session
- Coordinators already receive directive with relevant excerpts from Lead
- Most coordinator decisions don't require full skill knowledge
- Dynamic Context Injection (in skill) already provides session state

**Verdict: DEFER.**
- Net negative ratio: ~3,250L cost vs. marginal awareness benefit
- Lead's directive embedding is sufficient and more targeted
- If needed in future: adopt selectively (execution-coordinator only, highest skill complexity)
