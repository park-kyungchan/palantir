---
description: |
  Run ODA 3-Stage Audit on target path using Explore subagent.
  Quick audit for standard analysis; use /deep-audit for intensive review.
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: <target_path>
---

# /audit Command (Optimized with Explore Subagent)

Execute comprehensive 3-Stage Protocol audit on specified target.
**Optimization:** Delegates to Explore subagent for efficient codebase analysis.

## Arguments
$ARGUMENTS - Path to audit (default: current workspace)

---

## Execution Strategy

### Quick Audit (Default)
Uses `Task(subagent_type="Explore")` for fast, thorough scanning:

```python
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

    Return structured findings with file:line references.
    """,
    description="Explore audit on target"
)
```

### Deep Audit (For Complex Cases)
If quick audit reveals complexity=large, recommend:
```
→ Use /deep-audit $ARGUMENTS for intensive RSIL analysis
```

---

## Evidence Collection

This command automatically invokes evidence-collector agent:

```python
Task(
    subagent_type="evidence-collector",
    prompt="Track files_viewed and lines_referenced for audit evidence",
    run_in_background=True
)
```

Evidence requirements:
- **files_viewed:** Every examined file logged
- **lines_referenced:** Specific line numbers for findings
- **code_snippets:** Relevant excerpts preserved

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

## Integration with Native Capabilities

| Capability | Usage |
|------------|-------|
| `Task(Explore)` | Primary audit engine |
| `Task(evidence-collector)` | Background evidence tracking |
| `Skill(oda-audit)` | Internal protocol (context: fork) |
| `TodoWrite` | Stage progress tracking |

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
