---
description: Restore Main Agent context after Auto-Compact
allowed-tools: Read, Grep, Glob, TodoWrite, Task
---

# /recover Command

Restore Main Agent context after Auto-Compact or session interruption.

## Purpose

Auto-Compact compresses conversation context, potentially losing detailed subagent results.
This command recovers:
- Active plan files and their progress
- Interrupted/resumable agent IDs
- Incomplete todo items
- L2 structured reports

## When to Use

**Automatically invoke /recover when:**
1. Context seems incomplete ("잘 모르겠", "where we left off")
2. User mentions work you don't remember
3. TodoWrite shows tasks without context
4. Agent Registry has "running" or "interrupted" agents

## Pre-Execution: Initialize Recovery Tracking

```
TodoWrite([
  {"content": "Detect recovery need", "status": "pending", "activeForm": "Detecting recovery need"},
  {"content": "Collect plan file state", "status": "pending", "activeForm": "Collecting plan file state"},
  {"content": "Scan agent registry", "status": "pending", "activeForm": "Scanning agent registry"},
  {"content": "Find L2 reports", "status": "pending", "activeForm": "Finding L2 reports"},
  {"content": "Generate recovery prompt", "status": "pending", "activeForm": "Generating recovery prompt"},
  {"content": "Resume interrupted agents", "status": "pending", "activeForm": "Resuming interrupted agents"}
])
```

## Execution Steps

### Step 1: Detect Recovery Need

Check for indicators that recovery is needed:

```bash
# Check for active plan files
ls -la /home/palantir/park-kyungchan/palantir/.agent/plans/*.md 2>/dev/null || echo "No plan files"

# Check agent registry for interrupted/running agents
cat ~/.agent/config/agent_registry.yaml 2>/dev/null | grep -A5 "status:" || echo "No registry"

# Check for L2 outputs
ls -la ~/.agent/outputs/*/  2>/dev/null | head -20 || echo "No L2 outputs"
```

### Step 2: Read Active Plan File

If plan files exist, read the most recent one:

```
Read(".agent/plans/[most_recent].md")
```

Extract:
- Current phase (from ## Progress Tracking)
- Incomplete tasks (from ## Tasks where status ≠ completed)
- Agent Registry section (for resumable agent IDs)

### Step 3: Scan Agent Registry

Read agent registry and identify recovery candidates:

```
Read("~/.agent/config/agent_registry.yaml")
```

Filter for:
- `status: running` - Task was interrupted mid-execution
- `status: interrupted` - Explicitly marked for recovery
- `resume_eligible: true` - Can be resumed

### Step 4: Find L2 Reports

Scan for available L2 structured reports:

```
Glob(".agent/outputs/**/*.md")
```

For each interrupted agent, check if L2 exists:
- Path pattern: `.agent/outputs/{agent_type}/{agent_id}.md`

### Step 5: Generate Recovery Context

Synthesize collected information into Main Agent context:

```markdown
# Recovery Context Restored

## Active Plan
- File: {plan_path}
- Current Phase: {phase}
- Next Task: {task}

## Interrupted Agents
| Agent ID | Type | Task | Action |
|----------|------|------|--------|
| {id} | {type} | {desc} | `Task(resume="{id}")` |

## Available L2 Reports
- {report_path}: {summary}

## Recommended Actions
1. Resume interrupted agents for full results
2. Continue from current todo item
3. Read L2 reports for detailed context
```

### Step 6: Resume Interrupted Agents (Optional)

If interrupted agents exist and user approves, resume them:

```python
# For each interrupted agent
Task(
    subagent_type="{agent_type}",
    prompt="Continue your previous work. Previous context: {from_l2}",
    resume="{agent_id}",
    description="Resume {desc}"
)
```

## Output Format

```
🔄 Recovery Complete
====================

📋 Plan Restored: auto_compact_recovery_system.md
   Phase 3 of 7 in progress

⏸️  Interrupted Agents: 2
   - a1b2c3d (Explore): "Codebase analysis" → Ready to resume
   - e4f5g6h (Plan): "Feature design" → Ready to resume

📊 L2 Reports Available: 3
   - .agent/outputs/explore/a1b2c3d.md
   - .agent/outputs/plan/e4f5g6h.md

✅ Recommended Next Action:
   Resume interrupted agents with: Task(resume="a1b2c3d")
   Or continue plan Phase 3: recovery_manager.py implementation
```

## Integration with CLAUDE.md

This skill is referenced in CLAUDE.md Section 2.12 (Auto-Compact Recovery).

Recovery Detection Triggers (from CLAUDE.md):
1. Context appears incomplete
2. User mentions unfamiliar work
3. TodoWrite has context-less tasks
4. AgentRegistry shows unrecognized "running" agents

## Python API (Optional)

For programmatic use:

```python
from lib.oda.planning.recovery_manager import (
    get_recovery_manager,
    check_recovery_needed,
    get_recovery_prompt,
)

# Check if recovery needed
if check_recovery_needed(user_message):
    prompt = get_recovery_prompt()
    # Use prompt to restore context
```

## Post-Recovery

After successful recovery:
1. Clear recovery state: `recovery_manager.clear_recovery_state()`
2. Update plan file status to reflect resumed state
3. Continue with normal workflow

## Related Commands

- `/plan` - Create implementation plan (generates plan files)
- `/audit` - Code quality audit (generates L2 reports)
- `/init` - Initialize workspace
