# Proposal Validation Workflow

> **Purpose:** Prevent workflow violations by validating Subagent output against ODA ActionType schemas before Proposal creation.
> **Triggered By:** Main Agent after receiving proposals from any subagent.

---

## Problem Statement

Subagents may return proposals with incorrect field names or missing required fields:

```json
// Subagent output (WRONG)
{"path": "/home/palantir/README.md", "content": "..."}

// ODA ActionType expects (CORRECT)
{"file_path": "/home/palantir/README.md", "content": "...", "reason": "..."}
```

Without validation, these errors are only caught at `execute_proposal()`, wasting an approval cycle.

---

## Solution: Schema Validator Gate

### Integration Point

After subagent returns proposals, BEFORE `create_proposal()`:

```python
# Main Agent workflow
subagent_output = Task(subagent_type="general-purpose", ...)

# NEW: Validate each proposal against ODA schema
for proposal in subagent_output.proposals:
    validated_payload = validate_and_transform(
        action_type=proposal["action"],
        payload=proposal
    )

    # Only create proposal with validated payload
    mcp__oda_ontology__create_proposal(
        action_type=proposal["action"],
        payload=validated_payload
    )
```

### Validation Steps

#### Step 1: Identify ActionType Schema

```python
# Query ODA Kernel for ActionType definition
action_def = mcp__oda_ontology__inspect_action(api_name=action_type)
# Returns: submission_criteria, required fields, validation rules
```

#### Step 2: Schema Mapping

Common field mappings for `file.*` actions:

| Subagent Output | ODA Schema | Transform |
|-----------------|------------|-----------|
| `path` | `file_path` | Rename field |
| `content` | `content` | Keep as-is |
| (missing) | `reason` | Add from subagent context |
| (missing) | `stage_evidence` | Add from Stage A/B evidence |

#### Step 3: Validate Required Fields

```python
required_fields = extract_required_fields(action_def.submission_criteria)
# For file.write: ["file_path", "content", "reason"]

for field in required_fields:
    if field not in payload:
        raise ValidationError(f"Missing required field: {field}")
```

#### Step 4: Apply Transformations

```python
FIELD_MAPPINGS = {
    "file.write": {
        "path": "file_path",  # Rename
    },
    "file.modify": {
        "path": "file_path",
        "changes": "modifications",
    }
}

def transform_payload(action_type: str, payload: dict) -> dict:
    mappings = FIELD_MAPPINGS.get(action_type, {})
    transformed = {}

    for key, value in payload.items():
        new_key = mappings.get(key, key)  # Rename if mapping exists
        transformed[new_key] = value

    return transformed
```

---

## Implementation Options

### Option A: Inline Validation (Main Agent)

Main Agent performs validation directly:

```python
# In orchestrator code
def create_validated_proposal(action_type: str, subagent_payload: dict) -> str:
    # 1. Get schema
    schema = mcp__oda_ontology__inspect_action(api_name=action_type)

    # 2. Transform fields
    payload = transform_payload(action_type, subagent_payload)

    # 3. Add missing required fields
    if "reason" not in payload and "reason" in subagent_payload:
        payload["reason"] = subagent_payload.get("reason", "Automated action")

    # 4. Create proposal
    return mcp__oda_ontology__create_proposal(
        action_type=action_type,
        payload=payload
    )
```

### Option B: Schema Validator Subagent (Recommended)

Delegate validation to dedicated subagent:

```python
# Main Agent delegates validation
validation_result = Task(
    subagent_type="schema-validator",
    prompt=f"""
        Validate this proposal against ODA ActionType schema:

        Action Type: {action_type}
        Payload: {json.dumps(subagent_payload)}

        Return:
        {{
            "valid": true/false,
            "transformed_payload": {{...}},  # Corrected payload if needed
            "violations": [...],  # List of schema violations found
            "transformations": [...],  # List of field transformations applied
        }}
    """,
    description="Validate proposal schema"
)

if validation_result.valid:
    mcp__oda_ontology__create_proposal(
        action_type=action_type,
        payload=validation_result.transformed_payload
    )
else:
    # Log violations and request correction
    log_validation_failure(validation_result.violations)
```

### Option C: PreToolUse Hook Enforcement

Add hook that intercepts `create_proposal` calls:

```bash
# .claude/hooks/pre-proposal-validation.sh
#!/bin/bash
# Triggered when mcp__oda_ontology__create_proposal is called

TOOL_INPUT="${CLAUDE_TOOL_INPUT}"
ACTION_TYPE=$(echo "$TOOL_INPUT" | jq -r '.action_type')
PAYLOAD=$(echo "$TOOL_INPUT" | jq '.payload')

# Validate against known schemas
case "$ACTION_TYPE" in
    "file.write"|"file.modify")
        # Check for required field
        if ! echo "$PAYLOAD" | jq -e '.file_path' > /dev/null 2>&1; then
            echo '{"status":"blocked","reason":"Missing file_path field"}'
            exit 2  # Block the tool call
        fi
        ;;
esac

echo '{"status":"allowed"}'
exit 0
```

---

## Recommended Approach: Defense in Depth

Combine all three options for maximum protection:

```
Layer 1: Subagent Prompt Enhancement
├── Include ODA schema in subagent instructions
├── Provide correct field name examples
└── Request structured JSON output

Layer 2: Schema Validator Gate (Primary)
├── Task(subagent_type="schema-validator")
├── Validates and transforms payloads
└── Returns corrected payload or violations

Layer 3: PreToolUse Hook (Fallback)
├── Intercepts create_proposal calls
├── Performs final validation check
└── Blocks invalid proposals with exit 2
```

---

## Integration with Existing Workflow

### Updated E2E Flow

```
1. User Request
2. Stage A: SCAN
3. Stage B: TRACE
4. Task(general-purpose) → Returns proposals[]
5. NEW → Task(schema-validator) → Validates each proposal
6. mcp__oda_ontology__create_proposal() ← With validated payload
7. mcp__oda_ontology__approve_proposal()
8. mcp__oda_ontology__execute_proposal()
9. Stage C: VERIFY
```

### Code Template

```python
# Complete workflow with validation
async def execute_with_validation(requirements: str):
    # Stage A/B
    plan = await create_plan(requirements)

    # Get proposals from subagent
    subagent_result = Task(
        subagent_type="general-purpose",
        prompt=f"Implement: {requirements}. Return proposals only.",
    )

    # Validate each proposal
    for proposal in subagent_result.proposals:
        validation = Task(
            subagent_type="schema-validator",
            prompt=f"Validate: {json.dumps(proposal)}",
        )

        if not validation.valid:
            raise WorkflowViolation(validation.violations)

        # Create proposal with validated payload
        mcp__oda_ontology__create_proposal(
            action_type=proposal["action"],
            payload=validation.transformed_payload
        )

    # Approval and execution
    pending = mcp__oda_ontology__list_pending_proposals()
    for p in pending:
        mcp__oda_ontology__approve_proposal(proposal_id=p.id)
        mcp__oda_ontology__execute_proposal(proposal_id=p.id)
```

---

## Metrics and Monitoring

Track validation effectiveness:

```yaml
# .agent/metrics/validation_stats.yaml
total_validations: 0
passed: 0
failed: 0
auto_transformed: 0  # Successfully auto-corrected
blocked: 0  # Could not be corrected

common_violations:
  - field: "path_vs_file_path"
    count: 0
  - field: "missing_reason"
    count: 0
```
