# Codebase Impact Analysis — Gap Report

> Analyst output | 2026-02-14 | Scope: .claude/ INFRA v10.2
> Focus: What exists vs what is missing for real-time dynamic impact propagation

---

## Executive Summary

The current INFRA has **zero** runtime codebase impact analysis capability. There is no persistent dependency graph, no file-change-triggered impact propagation, no import map, and no mechanism for Lead to know what downstream files are affected by an upstream change. The closest existing capabilities are: (1) `manage-skills` using `git diff` for INFRA-scope change detection, (2) `verify-consistency` checking cross-file references within `.claude/`, and (3) `plan-decomposition` manually mapping task dependencies during planning. All of these are **manual, one-shot, and INFRA-scoped** -- none operate on application source code at runtime.

---

## 1. Component-by-Component Analysis

### 1.1 CLAUDE.md (Lead Protocol)

**Current state:**
- 43 lines, protocol-only. Zero mention of impact analysis, dependency tracking, or change propagation.
- Lead routes via Skill L1 WHEN conditions and Agent L1 PROFILE tags.
- Lead decides what files to check after a change by: reading implementer L1/L2 output, which lists `files_changed`. That is the full extent of "change awareness."

**Gaps:**
- No protocol step for "after code change, assess downstream impact."
- No mechanism for Lead to ask "what depends on file X?"
- Lead relies entirely on plan-phase dependency mapping (static, stale by execution time).
- No feedback loop: implementer changes file A -> Lead does NOT automatically check files that import/reference A.

**Verdict:** Fundamentally missing. Would need a new pipeline phase or cross-cutting skill.

---

### 1.2 Hooks (3 total)

**Current state:**

| Hook | Event | What It Does | Impact-Related? |
|------|-------|-------------|-----------------|
| on-subagent-start.sh | SubagentStart | Logs spawn, injects PT context | No |
| on-pre-compact.sh | PreCompact | Saves task snapshots, warns missing L1/L2 | No |
| on-session-compact.sh | SessionStart:compact | Injects recovery instructions | No |

**Gaps:**
- **No PostToolUse:Edit hook.** This is the most critical gap. CC fires `PostToolUse` after every successful tool call, with matcher on tool name. A `PostToolUse:Edit` hook could capture every file modification in real time (the hook input includes `tool_input` with the file path and edit details).
- **No PostToolUse:Write hook.** Same as above for file creation/overwrite.
- **No SubagentStop hook.** When an implementer finishes, there is no hook that collects what files changed and triggers impact analysis.
- **No Stop hook.** Could inject "impact assessment reminder" before Lead responds after an execution phase.

**What exists that could be extended:**
- The hook infrastructure is mature (3 working hooks, JSON stdin/stdout pattern established, `hookSpecificOutput.additionalContext` injection proven).
- `PostToolUse` with matcher `"Edit"` or `"Write"` could capture file paths and inject impact context.
- `SubagentStop` could collect the implementer's file change manifest and inject it into Lead's context.

**What is fundamentally missing:**
- Even if hooks capture file changes, there is no persistent knowledge store to query for "what depends on this file." The hook would need to either (a) call an external dependency analysis tool, or (b) read a pre-built dependency graph file.

---

### 1.3 settings.json

**Current state:**
- Permissions: `Bash(*)` allowed, meaning dependency analysis tools (grep, find, tree, etc.) are available.
- No hooks on Edit/Write/SubagentStop events configured.
- `defaultMode: delegate` means agents operate with delegated permissions.

**Gaps:**
- No `PostToolUse` hook entries for Edit or Write.
- No `SubagentStop` hook entry.
- No environment variable pointing to a dependency graph or import map.

---

### 1.4 implementer.md (Agent)

**Current state:**
- Tools: Read, Glob, Grep, Edit, Write, Bash, sequential-thinking.
- Constraint: "Only modify files assigned to you (non-overlapping ownership)."
- Constraint: "Run tests after changes to verify correctness."
- Constraint: "Write L1/L2/L3 output to assigned paths."
- Memory: Records impact analysis quality patterns (3-tier consumption chains, format mismatch propagation tracing).

**Gaps:**
- No instruction to report "what other files might be affected by my changes."
- No instruction to check imports/references of modified files.
- L1 output format (from execution-code) lists `files_changed` but NOT `files_potentially_affected`.
- Memory shows historical awareness of impact analysis (DIA protocol learnings) but this is NOT active -- it is vestigial from a previous system version.

**What could be extended:**
- Add to implementer constraints: "After editing file X, report files that import/reference X."
- Add to L1 output schema: `impact_candidates: []` field.
- Implementer already has Grep/Glob, so it CAN find references -- it just is not instructed to.

---

### 1.5 execution-code/SKILL.md

**Current state:**
- Spawns implementers per task-teammate matrix.
- Monitors via L1 output reading.
- Consolidates results into "unified file change manifest."
- L1 output: `files_changed: 0`, per-task `files: []` and `status`.

**Gaps:**
- "File change manifest" lists WHAT changed, not WHAT MIGHT BE AFFECTED.
- No step for "after all implementers complete, analyze cross-cutting impact."
- No step for "identify files not in the plan that reference changed files."
- COMPLEX tier has "dependency awareness" mentioned but this refers to TASK dependencies (build order), not CODE dependencies (import graph).

**What could be extended:**
- Add Step 3.5: "For each changed file, Grep for imports/references across codebase."
- Add to L1 output: `impact_analysis: { affected_files: [], confidence: high|medium|low }`.
- Add Quality Gate: "No high-impact files left unreviewed."

---

### 1.6 manage-skills/SKILL.md

**Current state:**
- Uses `git diff --name-only` to detect changed files.
- Maps changed files to INFRA domains via hardcoded rules (`.claude/agents/` -> design domain, etc.).
- Proposes CREATE/UPDATE/DELETE actions for skills based on domain coverage.
- Scope: `.claude/` directory ONLY. Does not analyze application source code.

**Gaps:**
- Detection rules are INFRA-specific (agent files, skill files, plan files).
- No detection rules for source code (Python imports, TypeScript imports, config references).
- No propagation: detects "file X changed" but does not ask "what else references file X?"
- No persistent knowledge: rules are hardcoded in the skill description, not derived from codebase analysis.

**What could be extended:**
- The `git diff` + domain mapping pattern could be generalized to source code.
- Detection rules could be made dynamic (read from a config file or generated by analysis).
- But this skill is specifically scoped to homeostasis of `.claude/` -- extending it to source code would violate its domain boundary.

---

### 1.7 research-codebase/SKILL.md

**Current state:**
- Discovers patterns, structures, conventions using Glob/Grep/Read.
- Read-only analysis, no modifications.
- Runs at P3 (research phase), before implementation.
- Output: L1 pattern inventory, L2 findings with file:line references.

**Gaps:**
- Runs ONCE during pre-execution research, not continuously during/after implementation.
- Does not build a persistent dependency graph or import map.
- Does not track "file X depends on file Y" relationships.
- Findings are point-in-time, not updated as code changes.
- No mechanism to re-trigger codebase research after an implementer changes files.

**What could be extended:**
- Could be invoked post-execution as an impact analysis pass.
- Could be enhanced to specifically build import/dependency maps.
- But its current design assumes pre-execution context -- would need significant L2 methodology changes.

---

## 2. Cross-Cutting Gap Analysis

### 2.1 Persistent Codebase Knowledge

| What | Exists? | Where? |
|------|---------|--------|
| Dependency graph (file-level) | NO | Nowhere |
| Import map (module-level) | NO | Nowhere |
| Symbol reference index | NO | Nowhere |
| File-to-domain mapping (source code) | NO | Only for `.claude/` in manage-skills |
| Change history per file | PARTIAL | `git log` available but never queried |
| Cross-reference cache | NO | Nowhere |

**Verdict:** There is ZERO persistent codebase knowledge. Every analysis starts from scratch using Glob/Grep.

---

### 2.2 Change Detection Flow

**Current flow (what happens when code changes):**

```
Implementer edits file A
  -> Implementer writes L1 (files_changed: [A])
  -> execution-code reads L1, builds file change manifest
  -> execution-review compares changes against design specs
  -> verify-* checks INFRA consistency
  -> delivery-pipeline commits
```

**Missing flow (what SHOULD happen for impact analysis):**

```
Implementer edits file A
  -> [MISSING] PostToolUse:Edit hook captures A's path
  -> [MISSING] Hook/skill queries "what imports/references A?"
  -> [MISSING] Returns affected files [B, C, D]
  -> [MISSING] Lead/skill checks if B, C, D need updates
  -> [MISSING] If yes: spawns additional implementer or flags for review
  -> execution-review reviews A AND affected files B, C, D
```

---

### 2.3 Lead Decision-Making After Changes

**How Lead currently decides what files to check:**
1. Reads implementer L1 output (`files_changed` list).
2. Compares against plan-decomposition task list (static, pre-execution).
3. Routes to execution-review which checks changed files against design specs.
4. Routes to verify-* which checks `.claude/` INFRA consistency only.

**What Lead CANNOT do today:**
- Ask "what application files depend on the files that were just changed?"
- Know if a changed utility function is imported by 15 other files.
- Detect that changing an interface definition breaks downstream consumers.
- Propagate awareness: "implementer-1 changed the API, implementer-2 is building against the old API."

---

## 3. Capability Matrix

| Capability | Status | Component | Gap Level |
|-----------|--------|-----------|-----------|
| Detect file changes in real time | MISSING | No PostToolUse hook | Extendable (hook infra exists) |
| Query file dependencies | MISSING | No dep graph, no import map | Fundamentally missing |
| Propagate impact to Lead | MISSING | No hook/skill for this | Extendable (additionalContext proven) |
| Persistent dependency graph | MISSING | No storage mechanism | Fundamentally missing |
| Cross-implementer impact awareness | MISSING | No inter-agent communication | Fundamentally missing |
| Post-change codebase re-scan | MISSING | research-codebase is pre-exec only | Extendable (skill exists, needs re-scoping) |
| INFRA-scope change detection | EXISTS | manage-skills git diff | Works for .claude/ only |
| INFRA cross-reference checking | EXISTS | verify-consistency | Works for skill INPUT_FROM/OUTPUT_TO only |
| Static task dependency mapping | EXISTS | plan-decomposition, orchestration-decompose | Pre-execution only, stale by exec time |
| File change manifest | EXISTS | execution-code L1 output | Lists changes, not impact |
| Design spec compliance review | EXISTS | execution-review | Checks against plan, not runtime deps |

---

## 4. Prioritized Recommendations

### Priority 1: PostToolUse Hook for Edit/Write (Extendable, Low Effort)

Add a `PostToolUse` hook with matcher `"Edit"` and `"Write"` that:
- Captures the file path from `tool_input`
- Logs it to a session-scoped change manifest
- Optionally runs a quick `grep -rl` for reverse references
- Injects `additionalContext` with affected file list

This gives Lead real-time change awareness with minimal INFRA change. The hook infrastructure is proven and the pattern is established.

### Priority 2: Implementer Impact Reporting (Extendable, Low Effort)

Modify implementer.md and execution-code SKILL.md to:
- Instruct implementers to Grep for reverse references after each edit
- Add `impact_candidates` to L1 output schema
- Have execution-code consolidate impact candidates in its manifest

### Priority 3: Persistent Dependency Graph (Fundamentally Missing, High Effort)

Build a persistent file-level dependency graph:
- Generated by a new skill (or enhanced research-codebase)
- Stored as a JSON/YAML file in `.agent/` or project root
- Updated incrementally after each change
- Queried by hooks and skills for impact propagation

### Priority 4: Cross-Implementer Impact Propagation (Fundamentally Missing, High Effort)

When implementer-1 changes a file that implementer-2 depends on:
- Lead detects the cross-cutting impact via dependency graph
- Lead sends updated context to implementer-2 via TaskUpdate
- Requires: dependency graph + SubagentStop hook + Lead protocol change

### Priority 5: Post-Execution Impact Scan Skill (Extendable, Medium Effort)

New skill or extended research-codebase that runs AFTER execution:
- Reads file change manifest from execution-code
- For each changed file, traces all reverse dependencies
- Produces impact report with confidence levels
- Feeds into execution-review for expanded review scope

---

## 5. Vestigial Evidence

The implementer agent memory contains references to a historical "DIA protocol" (Dynamic Impact Analysis Verification Protocol) that was part of a previous INFRA version:

- `MEMORY.md` mentions "3-Protocol Architecture: CIP (Context Injection) + DIAVP (Impact Verification) + Lead-Only Task API"
- `MEMORY.md` mentions "Two-Gate Flow: Gate A (Impact) -> Gate B (Plan) for implementer/integrator"
- Implementer memory has detailed "Impact Analysis Quality" patterns including "3-tier consumption chains" and "format mismatch propagation tracing"
- A team directory `ch006-dia-v4` exists in `.agent/teams/` with architecture designs for context-delta and hook-enhancement

This suggests that a DIA system was designed and partially implemented in a previous version but was removed during the v10 rewrite. The architectural thinking exists in historical artifacts but is not active in the current system.
