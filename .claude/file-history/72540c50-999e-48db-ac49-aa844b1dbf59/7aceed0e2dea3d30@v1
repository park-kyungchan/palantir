---
name: oda-governance
description: |
  Internal governance validation engine. Checks blocked patterns, schema rules, and quality gates.
  DO NOT invoke directly - use /governance command which orchestrates with schema-validator agent.
allowed-tools: Read, Grep, Glob, Bash
user-invocable: false
context: fork
agent: schema-validator
---

# ODA Governance Check Skill

## Purpose
Validate proposed changes against ODA governance rules before execution.
Prevents violations of schema, security, and quality standards.

## Invocation
```
/oda-governance [target_path]
```

## Governance Layers

### Layer 1: Blocked Patterns (Security)

**Always Blocked:**
| Pattern | Reason | Detection |
|---------|--------|-----------|
| `rm -rf` | Dangerous recursive deletion | Bash command scan |
| `sudo rm` | Privileged deletion | Bash command scan |
| `chmod 777` | Insecure permissions | Bash command scan |
| `DROP TABLE` | Database destruction | SQL scan |
| `eval(` | Code injection risk | Python scan |
| `exec(` | Code injection risk | Python scan |
| `__import__` | Dynamic import risk | Python scan |

**Detection Script:**
```bash
# Check for blocked patterns
grep -rn "rm -rf\|sudo rm\|chmod 777\|DROP TABLE\|eval(\|exec(" <target_path>
```

### Layer 2: Schema Compliance

**ObjectType Rules:**
1. All ObjectTypes must inherit from `OntologyObject`
2. Properties must have type hints
3. Links must specify cardinality
4. IDs must be UUIDv4 format

**Validation:**
```python
# Check ObjectType compliance
from scripts.ontology.registry import OntologyRegistry

registry = OntologyRegistry.instance()
for obj_type in registry.list_types():
    assert hasattr(obj_type, 'id'), f"{obj_type} missing id"
    assert hasattr(obj_type, 'created_at'), f"{obj_type} missing audit fields"
```

### Layer 3: Action Compliance

**Action Rules:**
1. Actions must have `apply_edits` method
2. Actions must return `EditOperation` list
3. Actions must have docstrings
4. Actions must have typed parameters

**Validation:**
```python
# Check Action compliance
from scripts.ontology.governance.quality_gate import CodeQualityGate

report = CodeQualityGate.validate_action_class(ActionClass)
if report.has_errors:
    raise GovernanceViolation(report.violations)
```

### Layer 4: Protocol Compliance

**Protocol Rules:**
1. Complex changes require 3-Stage Protocol
2. Each stage must produce evidence
3. Stage C must pass before execution
4. Anti-hallucination validation required

**Complexity Thresholds:**
| Complexity | Definition | Protocol Required |
|------------|------------|-------------------|
| Trivial | Single line fix | No |
| Small | < 50 lines, 1-2 files | Recommended |
| Medium | 50-200 lines, 3-5 files | Yes |
| Large | > 200 lines, 6+ files | Yes (with review) |

## Governance Report Format

```markdown
# ODA Governance Report

## Target: <path>
## Timestamp: <ISO datetime>
## Status: PASS / WARN / BLOCK

---

## Layer 1: Security Patterns
| Check | Status | Details |
|-------|--------|---------|
| No rm -rf | PASS | |
| No sudo rm | PASS | |
| No chmod 777 | PASS | |
| No eval/exec | WARN | Found in test_file.py:42 |

## Layer 2: Schema Compliance
| ObjectType | Status | Issues |
|------------|--------|--------|
| Task | PASS | |
| Agent | PASS | |
| CustomType | WARN | Missing docstring |

## Layer 3: Action Compliance
| Action | Status | Issues |
|--------|--------|--------|
| CreateTask | PASS | |
| UpdateTask | WARN | Missing type hint on param |

## Layer 4: Protocol Compliance
| Check | Status | Details |
|-------|--------|---------|
| Evidence present | PASS | 5 files viewed |
| Stage A complete | PASS | |
| Stage B complete | PASS | |
| Stage C complete | PENDING | Awaiting validation |

---

## Summary
- Total Checks: N
- Passed: N
- Warnings: N
- Blocked: N

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## Decision
- [ ] APPROVED: Proceed with changes
- [ ] CONDITIONAL: Fix warnings first
- [ ] BLOCKED: Critical violations found
```

## Violation Severities

```python
class ViolationSeverity(str, Enum):
    INFO = "info"        # Documentation, suggestions
    WARNING = "warning"  # Should fix, non-blocking
    ERROR = "error"      # Must fix in strict mode
    CRITICAL = "critical" # Always blocking
```

## Enforcement Modes

| Mode | Behavior |
|------|----------|
| `off` | No enforcement, report only |
| `warn` | Report violations, allow execution |
| `block` | Block execution on ERROR/CRITICAL |

**Configuration:**
```python
from scripts.ontology.governance.quality_gate import QualityGateEnforcement

QualityGateEnforcement.set_mode("block")  # Production
QualityGateEnforcement.set_mode("warn")   # Development
```

## Integration with Hooks

This skill integrates with Claude Code hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python -m scripts.ontology.governance.check --target $FILE_PATH"
          }
        ]
      }
    ]
  }
}
```

## Quick Checks

### Check Single File
```bash
python -m scripts.ontology.governance.check --file path/to/file.py
```

### Check Directory
```bash
python -m scripts.ontology.governance.check --dir scripts/ontology/
```

### Check Pending Changes
```bash
git diff --name-only | xargs python -m scripts.ontology.governance.check --files
```

## Example Usage

```
User: /oda-governance scripts/ontology/actions/

Claude: ODA Governance Check를 실행합니다.

## 대상: scripts/ontology/actions/

### Layer 1: Security Patterns
[Scanning for blocked patterns...]
- rm -rf: Not found
- sudo rm: Not found
- chmod 777: Not found
- eval/exec: Not found

Status: PASS

### Layer 2: Schema Compliance
[Checking ObjectType definitions...]
- All ObjectTypes inherit from OntologyObject
- All properties have type hints

Status: PASS

### Layer 3: Action Compliance
[Validating Action classes...]
- learning_actions.py: PASS
- memory_actions.py: WARN (missing docstring on line 45)

Status: WARN

### Layer 4: Protocol Compliance
- Evidence collection: Active
- Stage tracking: Enabled

Status: PASS

---

## Summary
- Security: PASS
- Schema: PASS
- Actions: WARN (1 issue)
- Protocol: PASS

## Decision: CONDITIONAL
Fix warning in memory_actions.py before merge.
```

## Protocol Integration

### Direct Governance Check
```python
from scripts.claude.handlers.governance_handlers import governance_check_handler
from scripts.claude.evidence_tracker import EvidenceTracker

tracker = EvidenceTracker(session_id="governance_check")
context = {
    "target_path": "<TARGET>",
    "evidence_tracker": tracker,
}

result = await governance_check_handler(context)

if result["results"]["overall"] == "BLOCK":
    print("BLOCKED: Security violations found")
    for v in result["findings"]:
        print(f"  - {v['file_path']}:{v['line']}: {v['description']}")
```

### CLI Invocation
```bash
python -c "
import asyncio
from scripts.claude.handlers.governance_handlers import governance_check_handler
from scripts.claude.evidence_tracker import EvidenceTracker

async def main():
    tracker = EvidenceTracker(session_id='cli')
    result = await governance_check_handler({
        'target_path': '$ARGUMENTS',
        'evidence_tracker': tracker,
    })
    print(result['message'])

asyncio.run(main())
"
```
