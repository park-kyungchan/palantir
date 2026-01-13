---
description: Check ODA governance compliance for pending changes
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: [target_path]
---

# /governance Command

Validate changes against ODA governance rules before execution.

## Arguments
$ARGUMENTS - Optional target path (default: staged git changes)

## Governance Layers

### Layer 1: Security
- Blocked patterns (rm -rf, sudo, chmod 777)
- Code injection risks (eval, exec)
- Secret exposure

### Layer 2: Schema
- ObjectType compliance
- Property type validation
- Link cardinality rules

### Layer 3: Actions
- Docstring requirements
- Type hint validation
- Exception handling

### Layer 4: Protocol
- Evidence requirements
- Stage completion
- Anti-hallucination

## Execution Strategy

### Phase 1: Target Resolution

If no target specified:
```bash
git diff --name-only --cached  # Get staged files
```

If target specified, use `$ARGUMENTS` as target path.

### Phase 2: Parallel Governance Checks

**Deploy 4 parallel subagents using `run_in_background=true`:**

```python
# Layer 1: Security Check
Task(subagent_type="Explore", prompt="Scan for security violations: rm -rf, eval, exec, secrets...",
     description="L1: Security Check", run_in_background=True)

# Layer 2: Schema Check
Task(subagent_type="Explore", prompt="Validate ObjectType compliance, property types...",
     description="L2: Schema Check", run_in_background=True)

# Layer 3: Actions Check
Task(subagent_type="Explore", prompt="Validate docstrings, type hints, exception handling...",
     description="L3: Actions Check", run_in_background=True)

# Layer 4: Protocol Check
Task(subagent_type="Explore", prompt="Validate evidence requirements, stage completion...",
     description="L4: Protocol Check", run_in_background=True)
```

### Phase 3: Result Synthesis

Collect results from all 4 parallel checks, determine final APPROVED/CONDITIONAL/BLOCKED status.

**Performance:** Parallel execution reduces check time by 60-70%

## Output
Governance report with:
- Pass/Warn/Block status per layer
- Specific violations with locations
- Recommendations
- Final decision (APPROVED/CONDITIONAL/BLOCKED)

## Example
```
/governance                     # Check staged changes
/governance scripts/ontology/   # Check specific directory
```
