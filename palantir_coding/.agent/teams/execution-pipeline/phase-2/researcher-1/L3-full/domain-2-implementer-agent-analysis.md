# Domain 2: Implementer Agent 도구/제약 분석

> **Date:** 2026-02-07
> **Researcher:** researcher-1
> **Sources:** implementer.md, task-api-guideline.md §11, CLAUDE.md §3/§5/[PERMANENT]

---

## 1. Agent Definition Summary

```yaml
name: implementer
model: opus
permissionMode: acceptEdits
memory: user  # persistent cross-session
max_instances: 4
spawned_in: Phase 6 (Implementation)
```

---

## 2. Tool Inventory

### Available Tools (11)
| Tool | Category | Purpose |
|------|----------|---------|
| Read | File I/O | Read files in codebase |
| Glob | File I/O | Find files by pattern |
| Grep | File I/O | Search file contents |
| Edit | File I/O | Modify existing files (exact string replacement) |
| Write | File I/O | Create new files |
| Bash | Execution | Run shell commands (build, test, lint) |
| TaskList | Task API | Read team task list (read-only) |
| TaskGet | Task API | Read specific task details (read-only) |
| mcp__sequential-thinking__sequentialthinking | Analysis | Structured reasoning |
| mcp__context7__resolve-library-id | External | Resolve library for docs query |
| mcp__context7__query-docs | External | Query library documentation |

### Disallowed Tools (3)
| Tool | Reason |
|------|--------|
| NotebookEdit | Not applicable to implementation tasks |
| TaskCreate | Lead-only sovereignty (DIA enforcement) |
| TaskUpdate | Lead-only sovereignty (DIA enforcement) |

### Tool Implications for execution-pipeline Design
- **Bash enables self-testing:** Implementer can run `npm test`, `pytest`, `cargo test`, etc. Self-test is MANDATORY per agent definition.
- **Context7 enables doc lookup:** Implementer can query external library docs during implementation.
- **Sequential-thinking enables reasoning:** Implementer should use for impact analysis, plan submission, and complex implementation decisions.
- **No TaskUpdate:** Implementer cannot mark own tasks complete — must report via SendMessage, Lead updates.

---

## 3. DIA TIER 1 Protocol (Full Detail)

### Impact Analysis Sections (6 required)

| # | Section | Content |
|---|---------|---------|
| 1 | Task Understanding | Restate in own words (no copy-paste), connection to project goals |
| 2 | Upstream Context | Inputs from Phase 4, specific DD-IDs and design section references |
| 3 | Files & Functions Impact Map | Files to create/modify (exact paths), functions to create/change (name + signature), downstream consumers |
| 4 | Interface Contracts | Interfaces to implement (signature quoted from Phase 4), breaking change risk |
| 5 | Cross-Teammate Impact | Other teammates affected, shared resources, divergence causal chain |
| 6 | Risk Assessment | Specific risks with specific mitigations |

### RC Checklist (10 items)

| ID | Criterion | Tests |
|----|-----------|-------|
| RC-01 | Task accurately restated in own words | Not copy-paste, semantic equivalence |
| RC-02 | Phase position correctly identified | Knows Phase 6, knows upstream/downstream |
| RC-03 | Upstream artifacts specifically referenced | Cites Phase 4 plan sections, DD-IDs |
| RC-04 | Affected file list is complete | No missing files vs plan §5 |
| RC-05 | Interface signatures are accurate | Matches Phase 4 spec exactly |
| RC-06 | Cross-teammate impact identified | Awareness of other implementers' files |
| RC-07 | Downstream causal chain explained | Knows what Phase 7/8 depends on |
| RC-08 | Breaking change risk assessed | Existing API/interface impact evaluated |
| RC-09 | No factual errors in claims | All references verifiable |
| RC-10 | No critical omissions vs Lead DIA | Lead's analysis not contradicted |

### LDAP HIGH (2 Questions)

Expected categories: RIPPLE_TRACE, FAILURE_MODE, DEPENDENCY_RISK, INTERCONNECTION_MAP

- 2 questions from 7 possible categories
- No ALTERNATIVE_DEMAND required (only for MAXIMUM intensity)
- Defense quality: specific module names, concrete propagation paths, quantified blast radius
- Weak/generic defense → [IMPACT_REJECTED]

### Max Attempts: 3

Failed 3x → [IMPACT_ABORT] → teammate terminated → Lead re-spawns with enhanced context

---

## 4. Two-Gate System

### Gate A: Impact Verification
```
Implementer submits [IMPACT-ANALYSIS]
    ↓
Lead reviews RC-01 ~ RC-10
    ↓
Lead issues [CHALLENGE] (LDAP HIGH: 2Q)
    ↓
Implementer defends
    ↓
[IMPACT_VERIFIED] or [IMPACT_REJECTED]
```

### Gate B: Plan Approval
```
Implementer submits [PLAN]
    ↓
Lead reviews: Files, Changes, Risk, Interface Impact
    ↓
[APPROVED] or [REJECTED]
```

**Gate A is PREREQUISITE for Gate B.** No [PLAN] submission without passing Gate A.

---

## 5. File Ownership Rules (CLAUDE.md §5)

| Rule | Detail |
|------|--------|
| Non-overlapping | Each implementer assigned distinct file set by Lead |
| Concurrent editing | FORBIDDEN — no two implementers touch same file |
| Documentation | Ownership documented in task description |
| Cross-boundary access | Read: unrestricted. Write: FORBIDDEN (only integrator can cross boundaries) |
| Violation handling | [STATUS] BLOCKED + "Need file outside ownership: {path}" → Lead resolves |

### Implications for Adaptive Spawn
- File ownership must be determined BEFORE spawning implementers
- Lead reads plan §3 (File Ownership Assignment) and §4 (TaskCreate Definitions)
- If task A and task B share files → cannot be parallelized → sequential or single implementer
- If task A and task B have disjoint files → can be parallel → separate implementers

---

## 6. Sub-Orchestrator Capability

Implementer can decompose own task into sub-tasks:

| Capability | Detail |
|------------|--------|
| Spawn method | Task tool (NOT TaskCreate) |
| Nesting limit | 1 level (subagents cannot spawn further subagents) |
| Boundary constraint | All sub-work within implementer's file ownership |
| Reporting | Significant sub-orchestration decisions reported to Lead |
| Use cases | Internal decomposition, parallel independent sub-work, code-reviewer subagent dispatch |

**Critical for execution-pipeline:** This is how the implementer dispatches spec-reviewer and code-quality-reviewer subagents within its own task scope.

---

## 7. Plan-Before-Execute Protocol

### [PLAN] Format
```
[PLAN] Phase 6
Files: [list of files to create/modify]
Changes: [description of each change]
Risk: [low|medium|high]
Interface Impact: [which interfaces are affected]
```

### Execution Sequence
1. Pass Gate A (Impact Analysis + LDAP)
2. Submit [PLAN] to Lead
3. Wait for [APPROVED]
4. Execute: modify files within ownership
5. Run self-tests
6. Write L1/L2/L3
7. Report [STATUS] COMPLETE to Lead

---

## 8. Adaptive Spawn Strategy

### Decision Factors

| Factor | 1 Implementer | 2 Implementers | 3-4 Implementers |
|--------|---------------|----------------|-------------------|
| Task count | 1-2 tasks | 3-5 tasks | 6+ tasks |
| File overlap | Any overlap | Some disjoint sets | Mostly/fully disjoint |
| Dependencies | Tightly coupled | Some independent | Mostly independent |
| Complexity | HIGH per task | MEDIUM per task | LOW-MEDIUM per task |
| Time pressure | Low | Medium | High |

### Algorithm (Lead Decision)

```
1. Read plan §4 (TaskCreate Definitions) — count tasks
2. Read plan §3 (File Ownership Assignment) — identify file sets
3. Build dependency graph from blockedBy/blocks
4. Identify independent task clusters (no shared files, no dependencies)
5. implementer_count = min(independent_clusters, 4)
6. If implementer_count == 0 (all tasks dependent): use 1 implementer, sequential
7. Assign each implementer a non-overlapping cluster
```

### Partition Rules
- Tasks sharing files → same implementer
- Tasks with blockedBy → dependent group → same implementer OR sequential
- Independent tasks with disjoint files → separate implementers (parallel)
- Max 4 implementers (agent definition limit)

### DIA Overhead Consideration
- Each implementer requires full DIA: ~5-22K tokens for Impact Analysis + LDAP
- For 4 implementers: ~20-88K tokens of DIA overhead
- Trade-off: DIA overhead vs parallel execution time savings
- Recommendation: Use fewer implementers for small plans (≤5 tasks), more for large plans (6+ independent tasks)

---

## 9. Context Pressure Handling

| Trigger | Action |
|---------|--------|
| ~75% context capacity | Write L1/L2/L3 immediately |
| After writing | Send [STATUS] CONTEXT_PRESSURE to Lead |
| Lead response | Terminate → re-spawn with L1/L2 injection |
| Recovery | New implementer reads L1/L2/L3 → resumes from last checkpoint |

### L1/L2/L3 Output Format
- **L1-index.yaml:** Modified files with change descriptions
- **L2-summary.md:** Implementation narrative, decisions made
- **L3-full/:** Code diffs, self-test results, implementation notes

---

## 10. Memory System

```
~/.claude/agent-memory/implementer/MEMORY.md
```

- Persistent across sessions (user scope)
- Consulted at start of every session
- Updated with: implementation patterns, code conventions, lessons learned
- General learnings (not project-specific, since user-scope)
