#!/usr/bin/env python3
"""
ODA Progressive-Disclosure PostToolUse Hook
============================================

Transforms verbose subagent outputs into L1/L2/L3 layered format.
This hook intercepts Task tool results and:
1. Writes full output to L2 structured report
2. Returns only L1 headline to Main Agent context
3. Optionally suppresses verbose output from transcript
4. Validates JSON output against schemas (V2.1.10)

Exit Codes:
    0: Success - JSON output processed

JSON Output Fields:
    - hookSpecificOutput.additionalContext: L1 headline + L2 path
    - hookSpecificOutput.suppressOutput: true (hide verbose from transcript)
    - decision: "allow"

Configuration: ~/.claude/hooks/config/progressive_disclosure_config.yaml

V2.1.9 Feature: Auto L2 generation and context minimization
V2.1.10 Feature: JSON schema validation and dual-format L2 storage
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Try to import schema validation module
try:
    sys.path.insert(0, "/home/palantir/park-kyungchan/palantir")
    from lib.oda.planning.output_schemas import (
        validate_output,
        extract_structured_output,
        SCHEMA_REGISTRY,
    )
    HAS_SCHEMAS = True
except ImportError:
    HAS_SCHEMAS = False
    SCHEMA_REGISTRY = {}

# =============================================================================
# Configuration
# =============================================================================

CONFIG_PATH = Path("/home/palantir/.claude/hooks/config/progressive_disclosure_config.yaml")
L2_BASE = Path("/home/palantir/.agent/outputs")
LOG_PATH = Path("/home/palantir/park-kyungchan/palantir/.agent/logs/progressive_disclosure.log")
VALIDATION_LOG_PATH = Path("/home/palantir/.agent/logs/schema_validation.log")

# Agent type to directory mapping
AGENT_TYPE_DIRS = {
    "explore": "explore",
    "plan": "plan",
    "general-purpose": "general",
    "general_purpose": "general",
    "evidence-collector": "evidence",
    "evidence_collector": "evidence",
    "prompt-assistant": "prompt",
    "prompt_assistant": "prompt",
}

# Skills that should use Progressive-Disclosure
DISCLOSURE_SKILLS = {
    "plan", "audit", "deep-audit", "execute", "quality-check"
}

# Output budget per agent type (tokens, approximate)
AGENT_BUDGETS = {
    "explore": 5000,
    "plan": 10000,
    "general-purpose": 15000,
    "evidence-collector": 5000,
}


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML or use defaults."""
    defaults = {
        "enabled": True,
        "auto_generate_l2": True,
        "suppress_verbose_output": True,
        "max_headline_length": 100,
        "max_l2_tokens": 3000,
        "applicable_skills": list(DISCLOSURE_SKILLS),
        "log_transformations": True,
        "validate_json_schema": True,   # V2.1.10: Enable JSON validation
        "write_json_l2": True,          # V2.1.10: Write JSON alongside markdown
    }

    if not HAS_YAML or not CONFIG_PATH.exists():
        return defaults

    try:
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
        return {**defaults, **config}
    except Exception:
        return defaults


CONFIG = load_config()


# =============================================================================
# Output Analysis
# =============================================================================

def extract_agent_info(tool_input: Dict, tool_output: str) -> Tuple[str, str, str]:
    """
    Extract agent_id, agent_type, and description from Task result.

    Returns:
        (agent_id, agent_type, description)
    """
    # Get from tool input
    agent_type = tool_input.get("subagent_type", "general-purpose")
    description = tool_input.get("description", "Task execution")

    # Try to extract agent_id from output
    agent_id = None

    # Pattern 1: "agentId: abc123"
    match = re.search(r'agentId:\s*([a-f0-9-]{7,})', tool_output, re.IGNORECASE)
    if match:
        agent_id = match.group(1)

    # Pattern 2: L1 headline format "[abc123]"
    if not agent_id:
        match = re.search(r'\[([a-f0-9]{7,})\]', tool_output)
        if match:
            agent_id = match.group(1)

    # Pattern 3: Look for UUID-like patterns
    if not agent_id:
        match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', tool_output)
        if match:
            agent_id = match.group(1)[:7]  # Use first 7 chars

    # Generate if not found
    if not agent_id:
        agent_id = datetime.now().strftime("%H%M%S") + os.urandom(2).hex()

    return agent_id, agent_type, description


def is_verbose_output(output: str) -> bool:
    """
    Determine if output is verbose and should be transformed.

    Returns True if output exceeds thresholds suggesting L2 generation is beneficial.
    """
    if not output:
        return False

    char_count = len(output)
    line_count = output.count('\n') + 1

    # Verbose if exceeds either threshold
    return char_count > 1000 or line_count > 30


def generate_headline(agent_type: str, agent_id: str, output: str, description: str) -> str:
    """
    Generate L1 headline from verbose output.

    Format: "✅ {Type}[{id}]: {summary}"
    """
    max_len = CONFIG.get("max_headline_length", 100)

    # Extract key metrics from output
    metrics = extract_metrics(output)

    # Build summary
    if metrics:
        summary_parts = []
        if "files" in metrics:
            summary_parts.append(f"{metrics['files']} files")
        if "issues" in metrics:
            summary_parts.append(f"{metrics['issues']} issues")
        if "phases" in metrics:
            summary_parts.append(f"{metrics['phases']} phases")
        if "findings" in metrics:
            summary_parts.append(f"{metrics['findings']} findings")

        if summary_parts:
            summary = ", ".join(summary_parts)
        else:
            summary = description[:50]
    else:
        # Use first meaningful line
        summary = extract_first_summary(output) or description[:50]

    # Determine status icon
    if any(word in output.lower() for word in ["error", "failed", "critical"]):
        icon = "❌"
    elif any(word in output.lower() for word in ["warning", "warn", "caution"]):
        icon = "⚠️"
    else:
        icon = "✅"

    # Format type name
    type_name = agent_type.replace("-", " ").title().replace(" ", "")

    headline = f"{icon} {type_name}[{agent_id[:7]}]: {summary}"

    if len(headline) > max_len:
        headline = headline[:max_len-3] + "..."

    return headline


def extract_metrics(output: str) -> Dict[str, int]:
    """Extract numeric metrics from output."""
    metrics = {}

    # Files count
    match = re.search(r'(\d+)\s*files?', output, re.IGNORECASE)
    if match:
        metrics["files"] = int(match.group(1))

    # Issues/findings count
    match = re.search(r'(\d+)\s*(issues?|findings?|problems?)', output, re.IGNORECASE)
    if match:
        metrics["issues"] = int(match.group(1))

    # Phases count
    match = re.search(r'(\d+)\s*phases?', output, re.IGNORECASE)
    if match:
        metrics["phases"] = int(match.group(1))

    # Findings specifically
    match = re.search(r'findings?:\s*(\d+)', output, re.IGNORECASE)
    if match:
        metrics["findings"] = int(match.group(1))

    return metrics


def extract_first_summary(output: str) -> Optional[str]:
    """Extract first meaningful summary line from output."""
    lines = output.strip().split('\n')

    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        # Skip markdown headers, empty lines, separators
        if not line or line.startswith('#') or line.startswith('-' * 3) or line.startswith('='):
            continue
        # Skip very short lines
        if len(line) < 10:
            continue
        # Found a content line
        return line[:80]

    return None


# =============================================================================
# JSON Schema Validation (V2.1.10)
# =============================================================================

def validate_json_output(tool_input: Dict, tool_output: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Validate subagent output against schema.

    Args:
        tool_input: Original Task tool input containing subagent_type
        tool_output: Raw output string from subagent

    Returns:
        Tuple of (is_valid, parsed_json, validation_message)
        - is_valid: True if valid JSON matching schema
        - parsed_json: Parsed dictionary if valid, None otherwise
        - validation_message: Human-readable status message
    """
    if not HAS_SCHEMAS:
        return False, None, "Schema module not available"

    if not CONFIG.get("validate_json_schema", True):
        return False, None, "JSON validation disabled in config"

    agent_type = tool_input.get("subagent_type", "general-purpose")
    normalized = agent_type.lower().replace("-", "_").replace(" ", "_")

    # Check if we have a schema for this agent type
    schema_key = None
    if normalized in SCHEMA_REGISTRY:
        schema_key = normalized
    elif normalized.replace("_", "-") in SCHEMA_REGISTRY:
        schema_key = normalized.replace("_", "-")

    if not schema_key:
        # Try direct JSON parse without schema validation
        try:
            json_match = re.search(r'\{[\s\S]*\}', tool_output)
            if json_match:
                parsed = json.loads(json_match.group())
                return True, parsed, f"Valid JSON (no schema for {agent_type})"
        except json.JSONDecodeError:
            pass
        return False, None, f"No schema for {agent_type}"

    # Try to extract and validate JSON using schema module
    try:
        result, error = extract_structured_output(tool_output, schema_key)
        if result is not None:
            # Convert Pydantic model to dict
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else dict(result)
            return True, result_dict, "Valid JSON matching schema"
        elif error:
            # Schema validation failed, try direct parse
            pass
    except Exception as e:
        pass

    # Fallback: Try direct JSON parse without schema validation
    try:
        # Find JSON in output (code block or raw)
        json_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
        matches = re.findall(json_block_pattern, tool_output)
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                return True, parsed, "Valid JSON (schema validation skipped)"
            except json.JSONDecodeError:
                continue

        # Try finding raw JSON object
        json_match = re.search(r'\{[\s\S]*\}', tool_output)
        if json_match:
            parsed = json.loads(json_match.group())
            return True, parsed, "Valid JSON (schema validation skipped)"
    except json.JSONDecodeError:
        pass
    except Exception:
        pass

    return False, None, "No valid JSON found in output"


def log_validation(agent_id: str, agent_type: str, is_valid: bool, message: str) -> None:
    """
    Log schema validation results for debugging.

    Args:
        agent_id: Unique identifier for the agent
        agent_type: Type of subagent (Explore, Plan, etc.)
        is_valid: Whether validation succeeded
        message: Validation status message
    """
    if not CONFIG.get("log_transformations", True):
        return

    try:
        VALIDATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now().isoformat(),
            "agent_id": agent_id,
            "agent_type": agent_type,
            "schema_valid": is_valid,
            "schemas_available": HAS_SCHEMAS,
            "message": message
        }
        with open(VALIDATION_LOG_PATH, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass  # Fail silently - logging should not break the hook


# =============================================================================
# L2 Report Generation
# =============================================================================

def generate_l2_report(
    agent_id: str,
    agent_type: str,
    description: str,
    output: str,
    headline: str,
    validated_json: Optional[Dict] = None
) -> str:
    """
    Generate L2 structured report from verbose output.

    Structure:
    - Metadata table
    - Summary (L1 headline)
    - Structured Output (if valid JSON) - V2.1.10
    - Critical Findings (if any)
    - Details (main content, truncated if needed)
    - Recommendations (if any)
    - L3 Reference

    Args:
        agent_id: Unique identifier for the agent
        agent_type: Type of subagent
        description: Task description
        output: Raw output string
        headline: L1 headline
        validated_json: Optional validated JSON dict (V2.1.10)

    Returns:
        Formatted markdown report string
    """
    timestamp = datetime.now().isoformat()
    budget = AGENT_BUDGETS.get(agent_type.lower(), 10000)
    has_json = validated_json is not None

    report = f"""# Agent Output: {agent_id}

## Metadata
| Field | Value |
|-------|-------|
| Agent Type | {agent_type} |
| Execution Time | {timestamp} |
| Status | completed |
| Context Budget | {budget} tokens |
| Description | {description[:100]} |
| JSON Validated | {has_json} |

## Summary
{headline}

"""

    # V2.1.10: If we have validated JSON, include it prominently
    if validated_json:
        json_str = json.dumps(validated_json, indent=2, ensure_ascii=False)
        report += f"""## Structured Output (JSON)
```json
{json_str}
```

"""

    # Extract and add critical findings
    findings = extract_findings(output)
    if findings:
        report += "## Critical Findings\n"
        for i, finding in enumerate(findings[:10], 1):
            report += f"{i}. {finding}\n"
        report += "\n"

    # Add details section (truncated if too long)
    max_detail_chars = CONFIG.get("max_l2_tokens", 3000) * 4  # ~4 chars per token
    details = output

    if len(details) > max_detail_chars:
        details = details[:max_detail_chars]
        details += "\n\n... [truncated - see L3 for full output]"

    report += f"""## Details
```
{details}
```

"""

    # Extract and add recommendations
    recommendations = extract_recommendations(output)
    if recommendations:
        report += "## Recommendations\n"
        for rec in recommendations[:5]:
            report += f"- {rec}\n"
        report += "\n"

    # Add L3 reference
    report += f"""## File References
- L3 Raw Output: /tmp/claude/.../tasks/{agent_id}.output
- Created: {timestamp}
"""

    return report


def extract_findings(output: str) -> list:
    """Extract findings/issues from output."""
    findings = []

    # Pattern 1: "[CRITICAL]", "[HIGH]", "[WARNING]" markers
    for match in re.finditer(r'\[(CRITICAL|HIGH|WARNING|ERROR)\]\s*([^\n]+)', output, re.IGNORECASE):
        findings.append(f"[{match.group(1).upper()}] {match.group(2).strip()}")

    # Pattern 2: Lines starting with severity markers
    for match in re.finditer(r'^(?:CRITICAL|HIGH|WARNING|ERROR):\s*(.+)$', output, re.MULTILINE | re.IGNORECASE):
        findings.append(match.group(1).strip())

    return findings


def extract_recommendations(output: str) -> list:
    """Extract recommendations from output."""
    recommendations = []

    # Look for recommendation section
    match = re.search(r'(?:Recommendations?|Suggestions?|Next Steps?):\s*\n((?:[-*]\s*.+\n?)+)', output, re.IGNORECASE)
    if match:
        for line in match.group(1).split('\n'):
            line = line.strip()
            if line.startswith(('-', '*')):
                recommendations.append(line[1:].strip())

    return recommendations


def write_l2_report(
    agent_id: str,
    agent_type: str,
    report: str,
    validated_json: Optional[Dict] = None
) -> Path:
    """
    Write L2 report to file and return path.

    V2.1.10: Also writes .json file alongside .md when JSON is available.

    Args:
        agent_id: Unique identifier for the agent
        agent_type: Type of subagent
        report: Markdown report content
        validated_json: Optional validated JSON dict

    Returns:
        Path to the markdown report file
    """
    type_dir = AGENT_TYPE_DIRS.get(agent_type.lower(), "general")
    output_dir = L2_BASE / type_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write markdown report (existing behavior)
    report_path = output_dir / f"{agent_id}_structured.md"
    report_path.write_text(report)

    # V2.1.10: Also write JSON file if validated and enabled
    if validated_json and CONFIG.get("write_json_l2", True):
        json_path = output_dir / f"{agent_id}_structured.json"
        try:
            json_content = json.dumps(validated_json, indent=2, ensure_ascii=False)
            json_path.write_text(json_content)
        except Exception:
            pass  # JSON write failure should not break the hook

    return report_path


# =============================================================================
# Main Hook Logic
# =============================================================================

def transform_task_output(tool_input: Dict, tool_output: str) -> Dict[str, Any]:
    """
    Transform verbose Task output into Progressive-Disclosure format.

    V2.1.10: Includes JSON validation and dual-format L2 storage.

    Returns JSON output for Claude Code hook system.
    """
    # Extract agent info
    agent_id, agent_type, description = extract_agent_info(tool_input, tool_output)

    # Check if output is verbose enough to transform
    if not is_verbose_output(tool_output):
        # Output is already concise, pass through
        return {
            "decision": "allow",
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
            }
        }

    # V2.1.10: Validate JSON output against schema
    is_valid_json, validated_json, validation_msg = validate_json_output(tool_input, tool_output)

    # Log validation result
    log_validation(agent_id, agent_type, is_valid_json, validation_msg)

    # Generate L1 headline
    headline = generate_headline(agent_type, agent_id, tool_output, description)

    # Generate L2 report with JSON if available
    l2_report = generate_l2_report(
        agent_id, agent_type, description, tool_output, headline,
        validated_json=validated_json  # V2.1.10
    )

    # Write L2 report (and JSON if available)
    l2_path = write_l2_report(agent_id, agent_type, l2_report, validated_json=validated_json)

    # Determine JSON path for additional context
    json_path_info = ""
    if validated_json and CONFIG.get("write_json_l2", True):
        type_dir = AGENT_TYPE_DIRS.get(agent_type.lower(), "general")
        json_path = L2_BASE / type_dir / f"{agent_id}_structured.json"
        json_path_info = f"\n**L2 JSON Available:**\nPath: `{json_path}`"

    # Build additional context for Main Agent
    additional_context = f"""## Subagent Result (Progressive-Disclosure)

**L1 Headline:**
{headline}

**L2 Report Available:**
Path: `{l2_path}`
To read full details: `Read("{l2_path}")`{json_path_info}

**Agent ID (for resume):** `{agent_id}`
**JSON Validated:** {is_valid_json} ({validation_msg})

---
*Full output transformed to L2 for context efficiency. Read L2 if details needed.*
"""

    # Determine if we should suppress verbose output
    suppress = CONFIG.get("suppress_verbose_output", True)

    return {
        "decision": "allow",
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": additional_context,
            "suppressOutput": suppress,
        }
    }


def log_transformation(
    agent_id: str,
    agent_type: str,
    original_size: int,
    headline_size: int,
    l2_path: str
) -> None:
    """Log transformation for debugging."""
    if not CONFIG.get("log_transformations", True):
        return

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now().isoformat(),
            "agent_id": agent_id,
            "agent_type": agent_type,
            "original_chars": original_size,
            "headline_chars": headline_size,
            "l2_path": str(l2_path),
            "reduction_ratio": round(headline_size / max(original_size, 1), 4),
        }
        with open(LOG_PATH, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point for PostToolUse hook."""
    try:
        if not CONFIG.get("enabled", True):
            print(json.dumps({"decision": "allow"}))
            return

        # Read hook input
        data = json.load(sys.stdin)
        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})
        tool_output = data.get('tool_output', '')

        # Only transform Task tool results
        if tool_name != 'Task':
            print(json.dumps({"decision": "allow"}))
            return

        # Convert tool_output to string if needed
        if isinstance(tool_output, dict):
            tool_output = json.dumps(tool_output, indent=2)
        elif not isinstance(tool_output, str):
            tool_output = str(tool_output)

        # Transform output
        result = transform_task_output(tool_input, tool_output)

        # Log if transformation occurred
        if result.get("hookSpecificOutput", {}).get("suppressOutput"):
            agent_id, agent_type, _ = extract_agent_info(tool_input, tool_output)
            headline = result.get("hookSpecificOutput", {}).get("additionalContext", "")
            l2_path = L2_BASE / AGENT_TYPE_DIRS.get(agent_type.lower(), "general") / f"{agent_id}_structured.md"
            log_transformation(
                agent_id=agent_id,
                agent_type=agent_type,
                original_size=len(tool_output),
                headline_size=len(headline),
                l2_path=str(l2_path)
            )

        # Output result
        print(json.dumps(result))

    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow"}))
    except Exception as e:
        # Fallback to allow on error
        print(json.dumps({
            "decision": "allow",
            "systemMessage": f"[FALLBACK] Progressive disclosure error: {e}"
        }))
    finally:
        sys.exit(0)


if __name__ == '__main__':
    main()
