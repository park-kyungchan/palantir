# Hierarchical Orchestration Guide

> **Version:** 1.2.0
> **Date:** 2026-02-02
> **Architecture:** Task-Centric Hybrid with Sub-Orchestrator Support
> **Related:** [Task API Guideline](task-api-guideline.md) for detailed Task patterns

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Workflow](#workflow)
4. [Usage Examples](#usage-examples)
5. [L1/L2/L3 Progressive Disclosure](#l1l2l3-progressive-disclosure)
6. [Context Pollution Prevention](#context-pollution-prevention)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Overview

Hierarchical Orchestration enables **multi-level task decomposition** where workers can become sub-orchestrators, breaking down complex tasks into manageable subtasks.

### Key Benefits

- **Scalability**: Decompose arbitrarily complex tasks into hierarchies
- **Context Isolation**: L1/L2/L3 prevents context overflow in Main Agent
- **Flexibility**: Workers choose optimal decomposition strategies
- **Transparency**: Full audit trail across all hierarchy levels

### System Components

| Component | Role | Version |
|-----------|------|---------|
| `/orchestrate` | Pure task decomposition (no assignment) | 4.0.0 |
| `/assign` | Task assignment with Sub-Orchestrator mode | 3.0.0 |
| `/worker` | Worker self-service + Sub-Orchestrator commands | 4.0.0 |
| `pd-task-interceptor.sh` | L1/L2/L3 enforcement hook | 4.0.0 |

---

## Architecture

### Hierarchy Levels

```
Level 0 (Main Orchestrator)
    │
    ├─ Task #1 ──────────────> terminal-b (Sub-Orchestrator)
    │   │
    │   └─ Level 1
    │       ├─ Subtask #1.1 ──> terminal-b
    │       ├─ Subtask #1.2 ──> terminal-c
    │       └─ Subtask #1.3 ──> terminal-d
    │
    ├─ Task #2 ──────────────> terminal-c (Regular Worker)
    │
    └─ Task #3 ──────────────> terminal-d (Sub-Orchestrator)
        │
        └─ Level 1
            └─ Subtask #3.1 ──> terminal-d (Sub-Sub-Orchestrator)
                │
                └─ Level 2
                    ├─ Subtask #3.1.1
                    └─ Subtask #3.1.2
```

### Metadata Fields

Each task carries hierarchy metadata:

```yaml
metadata:
  hierarchyLevel: 0           # 0=main, 1=sub, 2=sub-sub
  subOrchestratorMode: true   # Can decompose?
  canDecompose: true          # Permission flag
  parentTaskId: "1"           # Parent task reference
```

---

## Workflow

### Phase 1: Main Orchestration

```bash
# Main Agent decomposes project
/orchestrate "Implement authentication system"

# Output:
# ✅ Created Tasks:
#   Task #1: Implement user login
#   Task #2: Implement JWT tokens
#   Task #3: Implement password reset
```

**Key Change (v4.0):** `/orchestrate` no longer assigns owners. Tasks created with `owner: "unassigned"`.

### Phase 2: Assignment with Sub-Orchestrator Mode

```bash
# Assign Task #1 with Sub-Orchestrator capability
/assign 1 terminal-b --sub-orchestrator

# Output:
# ✅ Task #1 assigned to terminal-b (Sub-Orchestrator)
#    - hierarchyLevel: 0
#    - canDecompose: true
```

**Without `--sub-orchestrator`:**
- Worker can only execute, not decompose
- Regular worker workflow

**With `--sub-orchestrator`:**
- Worker can run `/worker orchestrate` to decompose
- Creates subtasks with hierarchyLevel + 1

### Phase 3: Sub-Orchestrator Decomposition

```bash
# In terminal-b
/worker start b

# Worker decides task is complex, decomposes it
/worker orchestrate b

# Output:
# 📋 Task to Decompose:
#    ID: #1
#    Subject: Implement user login
#
# ✅ Ready to decompose
#    Next: Run /orchestrate with breakdown
```

```bash
# Worker decomposes into subtasks
/orchestrate "Break user login into components"

# Output:
# ✅ Created Subtasks (hierarchyLevel: 1):
#   Subtask #4: Create login form UI
#   Subtask #5: Implement auth API endpoint
#   Subtask #6: Add session management
```

### Phase 4: Delegation

```bash
# Delegate subtasks to workers
/worker delegate b

# Output:
# Found 3 subtasks to delegate:
#   - Task #4: Create login form UI
#   - Task #5: Implement auth API endpoint
#   - Task #6: Add session management
#
# Next Step: /assign auto
```

```bash
/assign auto

# Output:
# 🟢 Task #4 → terminal-b
# 🟢 Task #5 → terminal-c
# 🟢 Task #6 → terminal-d
```

### Phase 5: Sub-Workers Execute

```bash
# Each worker executes their subtask
# In terminal-c:
/worker start c   # Works on Task #5

# In terminal-d:
/worker start d   # Works on Task #6
```

### Phase 6: Collection (L1/L2/L3)

```bash
# After all subtasks complete, Sub-Orchestrator collects results
/worker collect-sub b

# Output:
# 📊 Subtask Status:
#    Total: 3
#    Completed: 3 ✅
#    Pending: 0
#
# ✍️  Generating L1 summary...
#
# ✅ Collection Complete!
# Files Generated:
#   📄 L1 (Summary for Main): .agent/prompts/{slug}/outputs/terminal-b/task-1-l1-summary.md (450 tokens)
#   📄 L2 (Subtask Summaries): .agent/prompts/{slug}/outputs/terminal-b/task-1-l2-summaries.md
#   📄 L3 (Full Details): .agent/prompts/{slug}/outputs/terminal-b/task-1-l3-details.md
#
# Context Pollution Check: ✅ PASSED
```

### Phase 7: Complete Parent Task

```bash
/worker done b

# Output:
# ✅ Task #1 marked as completed
# L1 Summary delivered to Main Agent (450 tokens)
# L2/L3 stored in .agent/outputs/
```

---

## Usage Examples

### Example 1: Simple Sub-Orchestration

```bash
# 1. Main creates tasks
/orchestrate "Build user dashboard"
# → Task #1: Build user dashboard

# 2. Assign with Sub-Orchestrator mode
/assign 1 terminal-b --sub-orchestrator

# 3. Worker decomposes (in terminal-b)
/worker start b
/worker orchestrate b
/orchestrate "Break dashboard into widgets"
# → Subtask #2: User profile widget
# → Subtask #3: Activity feed widget
# → Subtask #4: Settings widget

# 4. Delegate
/assign 2 terminal-b
/assign 3 terminal-c
/assign 4 terminal-d

# 5. Workers execute
# (terminal-b, c, d each work on their subtask)

# 6. Collect results
/worker collect-sub b
# → L1 summary (480 tokens)
# → L2/L3 files saved

# 7. Complete
/worker done b
```

### Example 2: Multi-Level Hierarchy (Level 2)

```bash
# Main creates task
/orchestrate "Implement E2E testing suite"
# → Task #1: Implement E2E testing suite

# Assign to Sub-Orchestrator
/assign 1 terminal-b --sub-orchestrator

# Level 1: Worker decomposes
/worker orchestrate b
/orchestrate "Break E2E testing into categories"
# → Subtask #2: Auth flow tests
# → Subtask #3: Dashboard tests
# → Subtask #4: Payment tests

# Subtask #2 is complex, assign with Sub-Orchestrator mode
/assign 2 terminal-c --sub-orchestrator
/assign 3 terminal-d
/assign 4 terminal-e

# Level 2: terminal-c further decomposes Subtask #2
# (in terminal-c)
/worker start c
/worker orchestrate c
/orchestrate "Break auth tests into scenarios"
# → Subtask #5: Login test (hierarchyLevel: 2)
# → Subtask #6: Logout test (hierarchyLevel: 2)
# → Subtask #7: Password reset test (hierarchyLevel: 2)

# Assign Level 2 subtasks
/assign 5 terminal-c
/assign 6 terminal-c
/assign 7 terminal-c

# Execute, collect, complete
# (terminal-c collects L2 results into L1 for terminal-b)
# (terminal-b collects all L1 results into final L1 for Main)
```

---

## L1/L2/L3 Progressive Disclosure

### Purpose

Prevent **context overflow** by structuring outputs hierarchically:

- **L1**: Concise summary (max 500 tokens) → Main Agent
- **L2**: Section summaries with anchors → File
- **L3**: Full detailed results → File

### L1 Format (YAML)

```yaml
taskId: abc12345
agentType: general-purpose
summary: |
  Completed user login implementation with 3 subtasks.
  All auth flows validated and tested.
status: success

# Hierarchy Metadata
hierarchyLevel: 0
parentTaskId: ""
isSubOrchestrator: true

# Progressive Disclosure
priority: HIGH
findingsCount: 3
criticalCount: 0

l2Index:
  - anchor: "#subtask-summaries"
    tokens: 200
    priority: HIGH
    description: "Summary of each subtask result"

l2Path: .agent/prompts/{slug}/outputs/terminal-b/task-1-l2-summaries.md
requiresL2Read: false
nextActionHint: "Review L2 for implementation details"
```

### L2 Format (Markdown)

```markdown
# Task #1: User Login Implementation - Subtask Summaries

## Subtask #4: Create login form UI {#subtask-4}
<!-- Estimated tokens: 150 -->

Created React login form with:
- Email/password inputs
- Form validation
- Error handling
- Accessibility features

## Subtask #5: Implement auth API endpoint {#subtask-5}
<!-- Estimated tokens: 180 -->

Built `/api/auth/login` endpoint:
- JWT token generation
- Password bcrypt verification
- Rate limiting
- Session management

## Subtask #6: Add session management {#subtask-6}
<!-- Estimated tokens: 120 -->

Implemented session store:
- Redis-based session storage
- 24-hour expiration
- Refresh token logic
```

### L3 Format (Full Details)

```markdown
# Task #1: User Login Implementation - Full Details

## Task #4: Create login form UI

File: .agent/outputs/terminal-b/task-4-full-output.md

### Implementation

[Full code implementation]
[Test results]
[Screenshots]
[Performance metrics]

---

## Task #5: Implement auth API endpoint

File: .agent/outputs/terminal-c/task-5-full-output.md

[Complete API documentation]
[Request/response examples]
[Error handling details]
[Security considerations]

---

## Task #6: Add session management

File: .agent/outputs/terminal-d/task-6-full-output.md

[Session architecture]
[Redis configuration]
[Token refresh flow]
[Load testing results]
```

---

## Context Pollution Prevention

### Validation Rules

The system automatically validates L1 summaries:

```javascript
// Constraints
L1_MAX_TOKENS = 500
L1_MAX_CHARS = 2000

// Forbidden patterns (indicate L2/L3 leakage)
- Full task details (## Task #X with large content)
- Large code blocks (>500 chars)
- File content dumps
```

### Sanitization Process

If L1 validation fails:

1. **Detect**: Check length and forbidden patterns
2. **Warn**: Display warnings to worker
3. **Sanitize**:
   - Truncate large code blocks
   - Remove file content dumps
   - Cut to max length with "[Truncated]" marker
4. **Save**: Update L1 file with sanitized version

### Example Output

```
⚠️  Context Pollution Prevention Triggered:
  ⚠️  L1 exceeds 2000 chars (2847 chars)
  ⚠️  L1 contains L2/L3 pattern: ## Task #\d+\n.*\n.*\n
  ⚠️  Estimated tokens (711) exceeds limit (500)
  ✅ L1 sanitized and saved

✅ Collection Complete!

Files Generated:
  📄 L1 (Summary for Main): ...task-1-l1-summary.md (498 tokens)
  📄 L2 (Subtask Summaries): ...task-1-l2-summaries.md
  📄 L3 (Full Details): ...task-1-l3-details.md

Context Pollution Check: ⚠️ SANITIZED
```

---

## Troubleshooting

### Issue: "Sub-Orchestrator mode not enabled"

**Symptom:**
```bash
/worker orchestrate b
# ❌ Sub-Orchestrator mode not enabled for this task
```

**Solution:**
```bash
# Task must be assigned with --sub-orchestrator flag
/assign <taskId> terminal-b --sub-orchestrator
```

### Issue: "No subtasks found"

**Symptom:**
```bash
/worker delegate b
# ❌ No subtasks found for Task #1
```

**Solution:**
```bash
# Must run /worker orchestrate first to create subtasks
/worker orchestrate b
/orchestrate "Decompose task into subtasks"
```

### Issue: "Cannot collect - pending subtasks"

**Symptom:**
```bash
/worker collect-sub b
# ⏸️  Cannot collect - pending subtasks:
#   - Task #5: Implement API (in_progress)
```

**Solution:**
```bash
# Wait for all subtasks to complete
# Check status: /worker status b --all
# Once all completed: /worker collect-sub b
```

### Issue: L1 summary too large

**Symptom:**
```
Context Pollution Check: ⚠️ SANITIZED
```

**Solution:**
- This is automatic! System sanitizes L1.
- If critical info lost, review L2/L3 files directly
- Improve future summaries: be more concise in L1

### Issue: Lost L2/L3 files

**Symptom:**
```bash
# Can't find .agent/prompts/{slug}/outputs/terminal-b/task-1-l2-summaries.md
```

**Solution:**
```bash
# Check terminal ID and task ID
ls .agent/prompts/{slug}/outputs/terminal-b/

# Recreate from subtask outputs
/worker collect-sub b  # Regenerates L1/L2/L3
```

---

## Best Practices

### 1. When to Use Sub-Orchestrator Mode

✅ **Use when:**
- Task is complex with 3+ logical subtasks
- Worker has domain expertise to decompose optimally
- Dynamic decomposition needed based on runtime findings

❌ **Don't use when:**
- Task is straightforward (1-2 steps)
- Decomposition is already clear (just create subtasks directly)
- No benefit from worker-driven breakdown

### 2. Hierarchy Depth

- **Recommended**: Max 2 levels (Main → Sub → Sub-Sub)
- **Avoid**: 3+ levels (diminishing returns, overhead)

### 3. L1 Summary Writing

```yaml
# ✅ Good L1
summary: |
  Completed auth implementation. 3/3 subtasks done.
  Login, JWT, and sessions all working. Tests passing.

# ❌ Bad L1 (too detailed)
summary: |
  Completed authentication implementation including:
  1. Login form with React hooks, validation, error handling
  2. JWT endpoint with bcrypt, rate limiting, refresh tokens
  3. Redis session store with 24h expiration and cleanup
  [... 500 more words ...]
```

### 4. Task Granularity

- **Main Level**: Project features (4-8 hours work)
- **Sub Level 1**: Components/modules (1-2 hours work)
- **Sub Level 2**: Small units (15-30 min work)

### 5. File Organization

```
.agent/prompts/{slug}/outputs/    # V7.1 workload-scoped paths
├── terminal-b/                   # Sub-Orchestrator outputs
│   ├── task-1-l1-summary.md
│   ├── task-1-l2-summaries.md
│   └── task-1-l3-details.md
├── terminal-c/                   # Sub-worker outputs
│   └── task-5-output.md
└── terminal-d/                   # Sub-worker outputs
    └── task-6-output.md
```

---

## Summary

Hierarchical Orchestration provides:

1. **Scalability**: Decompose complex projects into manageable hierarchies
2. **Context Safety**: L1/L2/L3 prevents Main Agent context overflow
3. **Flexibility**: Workers choose optimal decomposition strategies
4. **Transparency**: Full audit trail with metadata tracking

**Key Commands:**
- `/orchestrate` - Decompose tasks (no assignment)
- `/assign <taskId> <terminal> --sub-orchestrator` - Enable Sub-Orchestrator mode
- `/worker orchestrate` - Worker decomposes current task
- `/worker delegate` - Assign subtasks
- `/worker collect-sub` - Collect results with L1/L2/L3

**Version History:**
- v1.0.0 (2026-01-25): Initial release with Sub-Orchestrator support
