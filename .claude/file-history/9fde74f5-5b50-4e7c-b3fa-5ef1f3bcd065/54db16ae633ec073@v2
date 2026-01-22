---
description: |
  Run ODA 3-Stage Audit on target path using Explore subagent.
  Quick audit for standard analysis; use /deep-audit for intensive review.
  **[V2.1.7] ContextBudgetManager, Parallel Execution, Resume 지원.**
  **[V2.1.9] Progressive-Disclosure Native - Auto L2 generation via PostToolUse Hook**
allowed-tools: Read, Grep, Glob, Bash, Task, TodoWrite
argument-hint: <target_path>

# V2.1.9 Features (includes V2.1.7)
v21x_features:
  context_budget_manager: true    # Check context before delegation
  parallel_execution: true        # Background subagents for large scopes
  resume_support: true            # Resume interrupted audits
  ultrathink_mode: false          # Quick audit uses standard mode
  task_decomposer: true           # Split large audits
  progressive_disclosure: true    # V2.1.9: Hook auto-generates L2
  suppress_verbose_output: true   # V2.1.9: Verbose output hidden
  auto_l2_generation: true        # V2.1.9: L2 reports created automatically
---

# /audit Command (Optimized with Explore Subagent)

Execute comprehensive 3-Stage Protocol audit on specified target.
**Optimization:** Delegates to Explore subagent for efficient codebase analysis.

## Arguments
$ARGUMENTS - Path to audit (default: current workspace)

---

## Execution Strategy

### Step 0: Context Budget Check (V2.1.7 MANDATORY)

Before any delegation, verify context budget:

```python
# ContextBudgetManager ensures safe delegation
from lib.oda.planning.context_budget_manager import (
    ContextBudgetManager,
    ThinkingMode,
    DelegationDecision,
)

manager = ContextBudgetManager(thinking_mode=ThinkingMode.STANDARD)
decision = manager.check_before_delegation("Explore", estimated_tokens=5000)

if decision == DelegationDecision.PROCEED:
    # Safe to delegate
    pass
elif decision == DelegationDecision.REDUCE_SCOPE:
    # Apply TaskDecomposer to split audit
    from lib.oda.planning.task_decomposer import should_decompose_task, decompose_task
    if should_decompose_task("Audit target", "$ARGUMENTS"):
        subtasks = decompose_task(...)
        # Deploy parallel subagents (see below)
elif decision in [DelegationDecision.DEFER, DelegationDecision.ABORT]:
    # Suggest /compact before proceeding
    print("⚠️ Context usage high. Consider running /compact first.")
```

### Step 1: Task Decomposition Check (Large Scope)

For large targets, decompose into parallel subagents:

```python
from lib.oda.planning.task_decomposer import (
    TaskDecomposer,
    SubagentType,
    should_decompose_task,
)

# Check scope keywords: "전체", "모든", "all", "entire"
if should_decompose_task("Audit $ARGUMENTS", scope="$ARGUMENTS"):
    decomposer = TaskDecomposer()
    subtasks = decomposer.decompose("Audit", "$ARGUMENTS", SubagentType.EXPLORE)

    # Deploy parallel background audits (Boris Cherny pattern)
    for subtask in subtasks:
        Task(
            subagent_type="Explore",
            prompt=subtask.prompt,  # Includes output budget constraint
            description=f"Parallel audit: {subtask.description[:30]}",
            run_in_background=True,  # V2.1.7 Parallel Execution
        )
    # Wait for all subtasks before synthesis
```

### Step 2: Quick Audit (Default - Single Scope)

Uses `Task(subagent_type="Explore")` for fast, thorough scanning:

**V2.1.9 Progressive-Disclosure:**
- Hook automatically intercepts verbose audit results
- Writes to L2: `.agent/outputs/explore/{agent_id}_structured.md`
- Returns L1 headline: `✅ Explore[id]: N files, M issues`
- Main Agent context cost: ~100 tokens (instead of 5000+)

```python
# V2.1.9: Hook handles output transformation
Task(
    subagent_type="Explore",
    prompt="""
    Perform 3-Stage Audit on: $ARGUMENTS

    Stage A (SCAN):
    - Discover all files (Python, config, tests)
    - Map directory structure
    - Assess complexity (small/medium/large)

    Stage B (TRACE):
    - Verify import paths
    - Document public APIs
    - Map data flow between modules

    Stage C (VERIFY):
    - Check for blocked patterns (rm -rf, eval, etc.)
    - Validate type hints and docstrings
    - Score quality (1-10)

    Return comprehensive findings with file:line references.
    """,
    description="Explore audit on target"
)

# Hook automatically:
# 1. Captures verbose response (may be 5000+ tokens)
# 2. Writes L2 structured report
# 3. Returns L1 headline only to Main Agent
# 4. Suppresses verbose from transcript

# To access details:
# Read(".agent/outputs/explore/{agent_id}_structured.md")
```

### Deep Audit (For Complex Cases)
If quick audit reveals complexity=large, recommend:
```
→ Use /deep-audit $ARGUMENTS for intensive RSIL analysis
```

---

## Evidence Collection (V2.1.7 Enhanced)

This command automatically invokes evidence-collector agent with parallel execution:

```python
# Background evidence collection (V2.1.7 Parallel Pattern)
Task(
    subagent_type="evidence-collector",
    prompt="""
    Track audit evidence for: $ARGUMENTS

    Required Evidence:
    - files_viewed: Every examined file
    - lines_referenced: Specific line numbers for findings
    - code_snippets: Relevant excerpts

    ## Constraint: Output Budget
    YOUR OUTPUT MUST NOT EXCEED 5000 TOKENS.
    """,
    run_in_background=True,  # V2.1.7: Non-blocking execution
    description="Background evidence collection"
)
```

Evidence requirements:
- **files_viewed:** Every examined file logged
- **lines_referenced:** Specific line numbers for findings
- **code_snippets:** Relevant excerpts preserved

### Agent Registry for Resume (V2.1.7)

Track agent IDs for Auto-Compact recovery:

```python
from lib.oda.planning.agent_registry import AgentRegistry, register_agent
from lib.oda.planning.output_layer_manager import OutputLayerManager, OutputLayer

# Initialize managers
registry = AgentRegistry()
output_manager = OutputLayerManager()

# After launching subagent
result = Task(subagent_type="Explore", ..., run_in_background=True)

# Register agent for Resume eligibility
registry.register(
    agent_id=result.agent_id,
    agent_type="Explore",
    description="Audit of $ARGUMENTS",
    context_budget=5000,
    parent_task="audit_$ARGUMENTS"
)

# After completion, process output layers
headline = output_manager.format_headline(
    agent_id=result.agent_id,
    agent_type="Explore",
    summary="Audit complete: 8 files, 3 issues",
    status="completed",
    metrics={"files_scanned": 8, "issues_found": 3}
)
# L1 Headline: "✅ Explore[agent_id]: Audit complete: 8 files, 3 issues"

# Write L2 Structured Report for on-demand access
report_path = output_manager.write_structured_report(
    agent_id=result.agent_id,
    agent_type="Explore",
    task_description="Audit $ARGUMENTS",
    result=result.output,
    status="completed"
)
# Creates: .agent/outputs/explore/{agent_id}_structured.md

# Mark completion
registry.mark_completed(result.agent_id, output_path=report_path)

# After Auto-Compact, resume with:
for agent in registry.get_resumable():
    if "audit" in agent.description.lower():
        Task(
            subagent_type=agent.type,
            prompt="Continue audit from previous state",
            resume=agent.id,  # V2.1.7 Resume Parameter
            description="Resume interrupted audit"
        )
```

### 3-Layer Progressive-Disclosure (V2.1.7)

Output layers for context efficiency:

| Layer | Content | Location | Token Cost |
|-------|---------|----------|------------|
| **L1 Headline** | `✅ Explore[id]: summary` | Main Context | ~50 |
| **L2 Structured** | Findings, evidence, recs | `.agent/outputs/explore/{id}_structured.md` | ~2000 |
| **L3 Raw** | Full transcript | `/tmp/claude/.../tasks/{id}.output` | Full |

Access based on need:
```python
# L1 is always in main context (auto-included)

# Access L2 when need details without full context cost
if need_details:
    l2_content = output_manager.read_layer(agent_id, OutputLayer.L2_STRUCTURED)

# Access L3 via Resume when full recovery needed
if need_full_context:
    Task(resume=agent_id, prompt="Report complete findings")
```

---

## Output Format

```markdown
# Audit Report: $ARGUMENTS

## Summary
| Metric | Value |
|--------|-------|
| Files scanned | N |
| Complexity | small/medium/large |
| Critical findings | N |
| Quality score | X/10 |

## Stage A: SCAN
### Structure
[Directory tree visualization]

### Complexity Assessment
[Rating with justification]

## Stage B: TRACE
### Import Analysis
| Module | Status | Issues |
|--------|--------|--------|
| module.py | VALID | None |

### API Documentation
[Public interface summary]

## Stage C: VERIFY
### Findings
| Severity | Location | Description |
|----------|----------|-------------|
| HIGH | file.py:42 | Missing type hint |

### Quality Scores
- Code Quality: X/10
- Architecture: X/10
- Security: X/10

## Recommendations
1. [Priority recommendations]

## Next Steps
- [ ] Address HIGH findings
- [ ] Run /deep-audit if needed
- [ ] Update documentation
```

---

## Integration with Native Capabilities (V2.1.7)

| Capability | Usage | V2.1.7 Enhancement |
|------------|-------|-------------------|
| `Task(Explore)` | Primary audit engine | `run_in_background=True` for parallel |
| `Task(evidence-collector)` | Background evidence tracking | Non-blocking parallel execution |
| `Skill(oda-audit)` | Internal protocol (context: fork) | Isolated context for deep analysis |
| `TodoWrite` | Stage progress tracking | Auto-Compact recovery support |
| `ContextBudgetManager` | Context usage check | Pre-delegation verification |
| `TaskDecomposer` | Large scope splitting | 32K output budget compliance |
| `Resume Parameter` | Auto-Compact recovery | Continue interrupted audits |

### V2.1.7 Subagent Budget Allocation

| Mode | Explore Budget | Evidence Budget | Total |
|------|---------------|-----------------|-------|
| STANDARD | 5,000 tokens | 3,000 tokens | 8,000 |
| ULTRATHINK | 15,000 tokens | 8,000 tokens | 23,000 |

### Parallel Execution Pattern (Boris Cherny)

```python
# CORRECT: Deploy independent agents in parallel
Task(subagent_type="Explore", ..., run_in_background=True)  # Audit
Task(subagent_type="evidence-collector", ..., run_in_background=True)  # Evidence

# WRONG: Sequential blocking
result1 = Task(...)  # Blocks
result2 = Task(...)  # Waits - inefficient
```

---

## Comparison: /audit vs /deep-audit

| Aspect | /audit | /deep-audit |
|--------|--------|-------------|
| Speed | Fast (Explore agent) | Thorough (RSIL method) |
| Depth | Standard analysis | Microscopic review |
| Use case | Regular checks | Pre-merge validation |
| Evidence | Automatic | Mandatory with BLOCK |

---

## Example Usage

```
/audit scripts/ontology/        # Audit specific directory
/audit .                        # Audit current workspace
/audit hwpx/                    # Audit sibling project
```
