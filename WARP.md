# Warp Agent — Claude Code INFRA Single-Instance Protocol

> Companion to `.claude/CLAUDE.md` (Team Constitution). This file bridges both environments.
> Warp Manage Rules (4 rules) provide additional Warp-specific context not visible to Claude Code CLI.

## 1. Dual Environment Architecture
- **Claude Code CLI (tmux)**: Agent Teams multi-instance. CLAUDE.md = governing document. Full pipeline with spawned teammates.
- **Warp Agent (Oz)**: Single-instance. CLAUDE.md + this file + 4 Manage Rules. Lead↔Teammate role switching.
- **Bridge files** (shared): CLAUDE.md, MEMORY.md, WARP.md, `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`

## 2. Single-Instance Execution
Warp Agent = single instance. Lead↔Teammate role switching:
1. **Lead phase**: Read task specs, construct directives, plan orchestration (CLAUDE.md §6)
2. **Teammate phase**: Bind persona → execute per agent .md + SKILL.md → produce L1/L2/L3
3. **Return to Lead**: Evaluate output, approve/reject, advance pipeline

In Teammate phase, respect persona's `disallowedTools` and scope constraints.

## 3. Persona Compliance
- **Agents** (`.claude/agents/*.md`, 46 files): frontmatter + body binding
  - 8 coordinators (Template B), 3 fork agents (Task API), 35 workers
- **Skills** (`.claude/skills/*/SKILL.md`, 10): §A/§B/§C/§D workflow
- **Protocols**: `agent-common-protocol.md`, `coordinator-shared-protocol.md`

## 4. Warp Tool → INFRA Pattern Mapping
- `create_plan` / `edit_plans` → L2 design doc, orchestration plan (STANDARD/COMPLEX)
- `create_todo_list` / `mark_todo_as_done` → PROGRESS.md equivalent (3+ steps)
- `grep` + `file_glob` → codebase-researcher (P2 research)
- `web_search` → external-researcher (P2 external docs)
- `read_files` (batch) → Deep context loading
- `edit_files` (multi-diff) → Big Bang multi-file edit
- `run_shell_command` (wait) → Build/lint/test validation
- `run_shell_command` (interact) → Dev server, REPL monitoring
- `address_review_comments` → Review dispatch (AD-9)
- `report_pr` → delivery-pipeline P9 Op-5

## 5. Output & Verification
- L1/L2/L3 per `agent-common-protocol.md` §Saving Your Work
- Path: `.agent/teams/{session-id}/phase-{N}/{role-id}/`
- Step-by-step: verify after every edit, checkpoint every 2-3 files
- Multi-file (5+): V1-V6 cross-reference checks
- Pipeline tiers: TRIVIAL(≤2) / STANDARD(3-8) / COMPLEX(>8)

## 6. Key References
- Agent catalog: `.claude/references/agent-catalog.md`
- Gate standard: `.claude/references/gate-evaluation-standard.md`
- Layer boundary: `.claude/references/layer-boundary-model.md`
- Task API guide: `.claude/references/task-api-guideline.md`
- MEMORY.md: `.claude/projects/-home-palantir/memory/MEMORY.md`

## 7. Language Policy
Per CLAUDE.md §0: User conversation in **Korean**. Technical artifacts in **English**.
