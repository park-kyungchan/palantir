# Domain 1: writing-plans Detailed Analysis

## Source File
`.claude/plugins/cache/claude-plugins-official/superpowers/4.2.0/skills/writing-plans/SKILL.md` (117 lines)

## Full Principle Extraction

### Overview Section (lines 8-17)
```
"Write comprehensive implementation plans assuming the engineer has zero context
for our codebase and questionable taste."
```
- **Principle:** Zero-context assumption
- **Agent Teams mapping:** Implementer teammates receive context via CIP injection, but the plan itself should still be self-contained enough that any implementer can execute it with only the injected context

```
"DRY. YAGNI. TDD. Frequent commits."
```
- **Principle:** Engineering philosophy constants
- **Agent Teams mapping:** Unchanged. These apply to plan content, not execution model

```
"Assume they are a skilled developer, but know almost nothing about our toolset or problem domain."
```
- **Principle:** Skilled but domain-ignorant executor
- **Agent Teams mapping:** Even with DIA verification, implementer understanding is limited to what CIP provides + their own exploration. Plan must be explicit.

### Bite-Sized Task Granularity (lines 20-28)
```
Each step is one action (2-5 minutes):
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code" - step
- "Run the tests" - step
- "Commit" - step
```
- **Principle:** Atomic, verifiable steps
- **Agent Teams mapping:** TaskCreate entries should have atomic acceptance criteria. The TDD cycle (write test → verify fail → implement → verify pass → commit) is preserved within each task's "Detailed Requirements" section, not as separate TaskCreate entries.

### Plan Document Header (lines 30-45)
```markdown
# [Feature Name] Implementation Plan
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]
```
- **Agent Teams replacement:**
```markdown
# [Feature Name] Implementation Plan
> **For Lead:** This plan is designed for Agent Teams native execution.
> Read this file, then orchestrate using CLAUDE.md Phase Pipeline protocol.
**Goal:** [One sentence]
**Architecture:** [2-3 sentences from GC-v3]
**Design Source:** [path to architecture-design.md from Phase 3]
**Pipeline:** [Phase structure for this feature]
```

### Task Structure (lines 47-88)
```markdown
### Task N: [Component Name]
**Files:** Create/Modify/Test paths
**Step 1:** Write failing test (with code)
**Step 2:** Run test (with command + expected output)
**Step 3:** Write implementation (with code)
**Step 4:** Run test (with command + expected output)
**Step 5:** Commit (with exact command)
```
- **Agent Teams mapping:** Each "Task N" becomes a TaskCreate entry. Steps become the "Detailed Requirements" content in the implementation plan §5 Change Specifications. The plan still contains exact code, but organized under TaskCreate's acceptance criteria structure.

### Remember Section (lines 90-95)
```
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD, frequent commits
```
- **Agent Teams mapping:** All preserved. "Reference relevant skills" becomes less relevant since Agent Teams doesn't use skill chaining within execution. Replace with "Reference design source and architecture decisions."

### Execution Handoff (lines 97-117)
```
Subagent-Driven (this session) vs Parallel Session (separate)
```
- **Agent Teams replacement:** Clean termination. "Next: Phase 5 — plan validation." No execution choice — pipeline progression is defined by CLAUDE.md §2.

## Structural Comparison

| writing-plans Element | Agent Teams Equivalent | Location in Template |
|----------------------|----------------------|---------------------|
| Plan header | Plan header (modified) | Template §header |
| Task N structure | TaskCreate definition | Template §4 |
| Step 1-5 per task | Change Specifications per task | Template §5 |
| Exact file paths | File Ownership Assignment | Template §3 |
| Test commands | Test Strategy | Template §6 |
| Commit commands | Commit Strategy | Template §8 |
| Execution handoff | Clean Termination | Skill termination section |
