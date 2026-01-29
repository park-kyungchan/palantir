# Post-Compact Recovery Module

> **Version:** 1.0.0
> **Purpose:** Ensure full context restoration after Auto-Compact
> **Scope:** All pipeline skills

---

## 1. Overview

Auto-Compact reduces conversation context to a summary. This module ensures agents **NEVER** proceed with summarized information alone.

### Core Principle

```
COMPACT DETECTED → READ FILES → RESTORE CONTEXT → THEN PROCEED
                   ↑
            NEVER SKIP THIS STEP
```

---

## 2. Detection

### Compact Indicators

```python
def is_post_compact_session():
    """
    Detect if current session resumed after Auto-Compact.

    Indicators:
    - System message contains "continued from a previous conversation"
    - System message contains "summary below covers the earlier portion"
    - Conversation starts with summarized context block
    """
    indicators = [
        "This session is being continued from a previous conversation",
        "summary below covers the earlier portion",
        "context was summarized"
    ]
    return any(indicator in system_context for indicator in indicators)
```

---

## 3. Recovery Procedure

### 3.1 Step 1: Identify Active Workload

```python
def get_active_workload():
    """Read active workload from pointer file."""
    pointer_path = ".agent/prompts/_active_workload.yaml"

    if file_exists(pointer_path):
        content = Read(pointer_path)
        return extract_yaml_field(content, "slug")

    return None
```

### 3.2 Step 2: Read All Outputs

```python
def restore_skill_context(slug, skill_name):
    """
    Read all relevant outputs for a skill.

    IMPORTANT: Read L1, L2, AND L3 - not just L1 summary.
    """
    base_path = f".agent/prompts/{slug}"
    context = {}

    # Skill-specific reads
    skill_files = {
        "clarify": [
            f"{base_path}/clarify.yaml"
        ],
        "research": [
            f"{base_path}/research.md",           # L1
            f"{base_path}/research/l2_detailed.md",  # L2
            f"{base_path}/research/l3_synthesis.md", # L3
            f"{base_path}/research/tier2_review.md"  # Tier 2 review
        ],
        "planning": [
            f"{base_path}/plan.yaml"
        ],
        "orchestrate": [
            f"{base_path}/_context.yaml",
            f"{base_path}/_progress.yaml"
        ],
        "collect": [
            f"{base_path}/collection_report.md"
        ],
        "synthesis": [
            f"{base_path}/synthesis/synthesis_report.md"
        ]
    }

    files_to_read = skill_files.get(skill_name, [])

    for file_path in files_to_read:
        if file_exists(file_path):
            context[file_path] = Read(file_path)

    return context
```

### 3.3 Step 3: Validate Recovery

```python
def validate_recovery(context, skill_name):
    """
    Ensure sufficient context was recovered.

    Returns: (is_valid, missing_files)
    """
    required_files = {
        "clarify": ["clarify.yaml"],
        "research": ["research.md"],  # L1 minimum
        "planning": ["plan.yaml"],
        "orchestrate": ["_context.yaml"],
        "collect": ["collection_report.md"],
        "synthesis": ["synthesis_report.md"]
    }

    required = required_files.get(skill_name, [])
    missing = [f for f in required if not any(f in path for path in context.keys())]

    return (len(missing) == 0, missing)
```

---

## 4. Integration Pattern

### For Each Skill

```python
# At skill execution start
if is_post_compact_session():
    print("⚠️ Post-Compact Recovery: Restoring context from files...")

    slug = get_active_workload()
    if not slug:
        print("❌ No active workload found. Cannot proceed.")
        exit(1)

    context = restore_skill_context(slug, SKILL_NAME)
    is_valid, missing = validate_recovery(context, SKILL_NAME)

    if not is_valid:
        print(f"❌ Recovery failed. Missing files: {missing}")
        exit(1)

    print(f"✅ Context restored from {len(context)} files")
    # Now proceed with full context
```

---

## 5. Prohibited Actions After Compact

### NEVER Do These

| Action | Why Prohibited |
|--------|---------------|
| Modify code based on summary | Summary may miss critical details |
| Assume file paths from memory | Paths may have changed |
| Skip L2/L3 reads | L1 summary insufficient for detailed work |
| Proceed without workload slug | No way to locate correct files |
| Trust "remembered" variable values | Memory unreliable after compact |

### ALWAYS Do These

| Action | Why Required |
|--------|-------------|
| Read `_active_workload.yaml` | Authoritative source for current workload |
| Read ALL relevant L1/L2/L3 files | Full context restoration |
| Verify file existence before use | Files may have been modified |
| Re-read code before editing | Ensure working with current state |

---

## 6. Error Messages

```python
ERROR_MESSAGES = {
    "no_workload": "❌ Post-Compact Recovery Failed: No active workload found. "
                   "Run `/clarify` or `/research` to start a new workload.",

    "missing_files": "❌ Post-Compact Recovery Failed: Required files missing: {files}. "
                     "Workload may be incomplete or corrupted.",

    "read_error": "❌ Post-Compact Recovery Failed: Could not read {file}. "
                  "Check file permissions and path."
}
```

---

## 7. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-29 | Initial implementation for /research skill improvement |

---

*This module is referenced by CLAUDE.md Post-Compact Recovery Protocol*
