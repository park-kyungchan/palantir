---
name: oda-audit
description: |
  Internal 3-Stage Protocol Audit engine. Executes SCAN/TRACE/VERIFY on target codebase.
  DO NOT invoke directly - use /audit or /deep-audit commands which orchestrate with Explore subagent.
allowed-tools: Read, Grep, Glob, Bash
user-invocable: false
context: fork
agent: Explore
---

# ODA Audit Skill (3-Stage Protocol)

## Purpose
Perform comprehensive codebase audit following the 3-Stage Protocol methodology.
This skill enforces evidence-based analysis and prevents hallucination.

## Invocation
```
/oda-audit <target_path>
```

## Protocol Stages

### Stage A: SCAN (Surface Analysis)
**Goal:** Map the landscape before diving deep

**Actions:**
1. **File Discovery**
   ```bash
   find <target_path> -type f -name "*.py" | head -50
   ```

2. **Structure Analysis**
   - Identify entry points
   - Map directory structure
   - Count lines of code

3. **Complexity Assessment**
   - Small: 2-3 phases needed
   - Medium: 4-5 phases needed
   - Large: 6-7 phases needed

**Evidence Checklist:**
- [ ] `files_viewed`: List all files examined
- [ ] `requirements`: Document discovered requirements
- [ ] `complexity`: Assign complexity rating

### Stage B: TRACE (Logic Analysis)
**Goal:** Follow the data flow and dependencies

**Actions:**
1. **Import Verification**
   ```bash
   grep -r "^import\|^from" <target_path> --include="*.py"
   ```

2. **Signature Matching**
   - Document public APIs
   - Verify type hints
   - Check return types

3. **Call Graph Analysis**
   - Entry point → Dependencies
   - Identify circular imports
   - Map data flow

**Evidence Checklist:**
- [ ] `imports_verified`: All imports resolved
- [ ] `signatures_matched`: APIs documented
- [ ] `data_flow`: Call graph mapped

### Stage C: VERIFY (Quality Gate)
**Goal:** Ensure audit findings are actionable

**Quality Checks:**
1. **Code Quality**
   - [ ] Docstrings present
   - [ ] Type hints used
   - [ ] No bare exceptions

2. **Architecture**
   - [ ] Layer boundaries respected
   - [ ] No circular dependencies
   - [ ] SOLID principles followed

3. **Security**
   - [ ] No hardcoded secrets
   - [ ] Input validation present
   - [ ] SQL injection protected

**Finding Severities:**
| Severity | Action |
|----------|--------|
| CRITICAL | Must fix before merge |
| HIGH | Should fix in this PR |
| MEDIUM | Fix in follow-up |
| LOW | Nice to have |
| INFO | Documentation only |

## Output Format

```markdown
# ODA Audit Report: <target>

## Executive Summary
- Files Analyzed: N
- Complexity: small/medium/large
- Critical Findings: N
- Recommendations: N

## Stage A: SCAN Results
### Files Viewed
- path/to/file1.py (N lines)
- path/to/file2.py (N lines)

### Structure
[Directory tree]

### Complexity Assessment
[Rating and justification]

## Stage B: TRACE Results
### Import Analysis
[Import graph]

### API Signatures
[Public interface documentation]

### Data Flow
[Call graph or sequence diagram]

## Stage C: VERIFY Results
### Findings
| ID | Severity | Location | Description | Recommendation |
|----|----------|----------|-------------|----------------|
| F1 | HIGH | file.py:42 | Missing type hint | Add return type |

### Quality Score
- Code Quality: X/10
- Architecture: X/10
- Security: X/10
- Overall: X/10

## Evidence
- files_viewed: [list]
- lines_referenced: {file: [lines]}
- code_snippets: [relevant excerpts]
```

## Anti-Hallucination Rule
**CRITICAL:** This audit MUST produce evidence. An audit without `files_viewed` is INVALID.

```python
if not evidence.get("files_viewed"):
    raise AntiHallucinationError("Audit completed without examining any files")
```

## Integration with ODA
After audit completion:
1. Store findings in `.agent/memory/semantic/`
2. Create Proposals for critical findings
3. Update audit ledger

## Example Usage

```
User: /oda-audit scripts/ontology/

Claude: 3-Stage Audit Protocol을 시작합니다...
[Stage A: SCAN 실행]
[Stage B: TRACE 실행]
[Stage C: VERIFY 실행]
```

## Protocol Integration

This skill executes through the ODA Protocol Adapter:

### Python Invocation
```python
from scripts.claude.protocol_adapter import ODAProtocolAdapter, PROTOCOL_REGISTRY
from scripts.claude.handlers.audit_handlers import (
    audit_stage_a_handler,
    audit_stage_b_handler,
    audit_stage_c_handler,
)

# Get protocol
protocol_cls = PROTOCOL_REGISTRY.get("audit")
if protocol_cls:
    adapter = ODAProtocolAdapter(
        protocol=protocol_cls(),
        target_path="<TARGET>",
        session_id="<SESSION_ID>",
    )

    # Execute stages
    result_a = await adapter.execute_stage_a()
    if result_a.passed:
        result_b = await adapter.execute_stage_b()
        if result_b.passed:
            result_c = await adapter.execute_stage_c()
```

### CLI Invocation
```bash
python -m scripts.claude.protocol_runner audit <target_path>
```

### TodoWrite Integration
The adapter automatically manages todos:
- Stage A: SCAN → pending → in_progress → completed
- Stage B: TRACE → pending → in_progress → completed
- Stage C: VERIFY → pending → in_progress → completed