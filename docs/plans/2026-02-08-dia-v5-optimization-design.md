# DIA v5.0 — Opus 4.6 Optimization Design

> **Date:** 2026-02-08 | **Scope:** Full infrastructure rewrite
> **Goal:** Opus 4.6 measured language + Enhanced DIA + Dynamic Real-Time Integration
> **Input:** Codebase analysis + claude-code-guide research
> **Output:** All infrastructure files rewritten

---

## 1. Transformation Rules

### Opus 4.6 Measured Language
- `[MANDATORY]` → natural phrasing: "always", "must", or structural enforcement
- `[PERMANENT]` → keep ONLY as top-level section markers, remove inline usage
- `[FORBIDDEN]` → "never" or "do not"
- ALL CAPS inline → sentence case with emphasis via bold
- Redundant repetition → single authoritative statement
- Protocol-heavy formatting → conversational but precise
- "WHY:" blocks → keep but integrate naturally into context

### BUG-001 Resolution
- researcher.md: `permissionMode: plan` → `permissionMode: default`
- architect.md: `permissionMode: plan` → `permissionMode: default`
- All SKILL.md spawn examples: `mode: "plan"` → `mode: "default"` for researcher/architect
- Implementer/integrator keep `mode: "plan"` (Two-Gate System requires it)

### DIA v5.0 Enhancements
- **Always-Injected Context:** SubagentStart hook auto-injects GC version + team context
- **Dynamic Real-Time Integration:** Agents detect runtime GC changes via hook-injected additionalContext
- **Structured Impact Analysis:** YAML-friendly templates with machine-parseable sections
- **Semantic Integrity Tags:** Cross-file reference validation via consistent section IDs

### Hook Optimization
- Replace `find` with direct path construction (performance)
- JSON output for all hooks (machine-parseable)
- on-session-compact.sh → JSON additionalContext format
- on-subagent-start.sh → simplified path lookup
- Add SubagentStop validation (verify L1/L2 quality)

---

## 2. File Ownership

### Implementer-1: Core Infrastructure
- `.claude/CLAUDE.md`
- `.claude/references/task-api-guideline.md`

### Implementer-2: Agent Definitions
- `.claude/agents/researcher.md`
- `.claude/agents/architect.md`
- `.claude/agents/implementer.md`
- `.claude/agents/devils-advocate.md`
- `.claude/agents/tester.md`
- `.claude/agents/integrator.md`

### Implementer-3: Skills + Hooks
- `.claude/skills/brainstorming-pipeline/SKILL.md`
- `.claude/skills/agent-teams-write-plan/SKILL.md`
- `.claude/skills/agent-teams-execution-plan/SKILL.md`
- `.claude/hooks/on-subagent-start.sh`
- `.claude/hooks/on-subagent-stop.sh`
- `.claude/hooks/on-teammate-idle.sh`
- `.claude/hooks/on-task-completed.sh`
- `.claude/hooks/on-pre-compact.sh`
- `.claude/hooks/on-session-compact.sh`
- `.claude/hooks/on-task-update.sh`

---

## 3. Acceptance Criteria

- AC-1: No `[MANDATORY]` inline usage in any file
- AC-2: `[PERMANENT]` only at section-level headers
- AC-3: researcher/architect `permissionMode: default` in agent .md
- AC-4: All SKILL.md spawn examples use correct mode per BUG-001
- AC-5: integrator.md numbering fixed
- AC-6: All hooks use direct paths instead of `find`
- AC-7: on-session-compact.sh outputs JSON additionalContext
- AC-8: Cross-file protocol references consistent
- AC-9: DIA v5.0 version tag in CLAUDE.md
- AC-10: All existing functionality preserved (no behavioral changes)
