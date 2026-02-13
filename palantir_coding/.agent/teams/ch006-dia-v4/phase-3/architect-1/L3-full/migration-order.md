# Migration Order — DIA v3.1 → v4.0

**Author:** architect-1 | **Date:** 2026-02-07

---

## Migration Strategy: Bottom-Up (Infrastructure → Protocol → Agents)

### Rationale
- Hook scripts must exist before settings.json references them
- CLAUDE.md must define protocols before agent .md files reference them
- task-api-guideline.md must define Team Memory/Delta before CLAUDE.md cross-references it
- Agent .md files are leaf nodes — depend on everything else

---

## Phase Order

### Step 1: Hook Scripts (Infrastructure Layer)
**Files:** `on-teammate-idle.sh`, `on-task-completed.sh`, `on-subagent-start.sh`
**Dependencies:** None (standalone scripts)
**Action:**
1. CREATE `on-teammate-idle.sh` with L1/L2 validation logic
2. CREATE `on-task-completed.sh` with artifact validation logic
3. MODIFY `on-subagent-start.sh` with GC version additionalContext injection
4. Verify all scripts are executable (`chmod +x`)

**Why first:** Scripts must exist on disk before settings.json can point to them. Script errors at this stage are isolated — no protocol references yet.

### Step 2: settings.json (Hook Registration)
**Files:** `.claude/settings.json`
**Dependencies:** Step 1 (scripts must exist)
**Action:**
1. ADD `TeammateIdle` hook entry pointing to `on-teammate-idle.sh`
2. ADD `TaskCompleted` hook entry pointing to `on-task-completed.sh`
3. Existing `SubagentStart` entry remains unchanged (same script path)

**Why second:** Registering hooks before protocol documentation is safe — hooks validate independently. If registered before CLAUDE.md update, they still work (they check L1/L2 existence, which is already required by v3.1 protocol).

### Step 3: task-api-guideline.md (Protocol Foundation)
**Files:** `.claude/references/task-api-guideline.md`
**Dependencies:** None (standalone reference)
**Action:**
1. MODIFY §11 CIP: Add delta injection column to IP table, add Context Delta block
2. ADD §13: Team Memory Protocol (access rules, tags, lifecycle)
3. ADD §14: Context Delta Protocol (format, fallback tree, enhanced ACK)
4. Update version header: v3.0 → v4.0

**Why third:** task-api-guideline.md defines the detailed protocol that CLAUDE.md and agent .md will reference. Must be updated before those files add cross-references.

### Step 4: CLAUDE.md (Team Constitution)
**Files:** `.claude/CLAUDE.md`
**Dependencies:** Step 3 (task-api-guideline.md defines detailed protocol)
**Action:**
1. MODIFY §3: Add Team Memory and Context Delta Lead/Teammate duties
2. MODIFY §4: Add Team Memory Update row, replace CONTEXT-UPDATE/ACK-UPDATE formats
3. MODIFY §6: Add DIA Engine delta logic, Team Memory subsection, output directory
4. MODIFY [PERMANENT]: Add CIP delta mode, Team Memory duty (#8 Lead, #4a Teammate)
5. Update version header: v3.1 → v4.0

**Why fourth:** CLAUDE.md is the constitution — all agent .md files inherit from it. Must be updated before agents so agents reference correct section numbers and protocols.

### Step 5: Agent .md Files (Agent Instructions)
**Files:** 6 files in `.claude/agents/`
**Dependencies:** Step 4 (CLAUDE.md must define Team Memory protocol)
**Action:**
1. ALL 6 agents: Update [ACK-UPDATE] format in Mid-Execution Updates
2. implementer.md + integrator.md: Add TEAM-MEMORY.md Edit instructions + constraint
3. architect.md + researcher.md + tester.md: Add TEAM-MEMORY.md read + Lead relay
4. devils-advocate.md: Add TEAM-MEMORY.md read only

**Sub-order within Step 5:**
- implementer.md first (most complex change — Edit instructions + constraints)
- integrator.md second (same pattern as implementer)
- architect.md, researcher.md, tester.md (simpler — read + relay)
- devils-advocate.md last (simplest — read only)

**Why last:** Agent instructions are the most downstream — they reference CLAUDE.md protocols and task-api-guideline.md rules. Updating them last ensures all references are valid.

---

## Dependency Graph

```
Step 1: Hook Scripts ─────────┐
                               ▼
Step 2: settings.json ←── Step 1
                               │
Step 3: task-api-guideline.md  │ (independent of Steps 1-2)
             │                 │
             ▼                 │
Step 4: CLAUDE.md ←── Step 3   │
             │                 │
             ▼                 │
Step 5: Agent .md ←── Step 4   │
```

**Critical Path:** Step 3 → Step 4 → Step 5
**Parallel Path:** Steps 1-2 can execute parallel to Step 3

---

## Validation After Each Step

| Step | Validation |
|------|-----------|
| 1 | Scripts exist, executable, `bash -n` syntax check |
| 2 | `jq '.hooks.TeammateIdle' settings.json` returns valid entry |
| 3 | §13, §14 exist, version header = v4.0 |
| 4 | §3, §4, §6, [PERMANENT] contain new protocol text, version = v4.0 |
| 5 | All 6 agents have updated ACK format, Team Memory instructions |

---

## Rollback Strategy

- Each step is independently reversible via `git checkout -- {file}`
- Hook scripts can be deleted without affecting other files
- settings.json hook entries can be removed without breaking existing hooks
- Protocol files (CLAUDE.md, task-api-guideline.md) can be reverted to v3.1/v3.0
- Agent .md files can be reverted independently

**Atomic unit:** Each step should be committed separately for clean rollback.
