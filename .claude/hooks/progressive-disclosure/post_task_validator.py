#!/usr/bin/env python3
"""
L1 Progressive Disclosure Validator
Version: 2.3.0

Validates that L1 output from subagents follows Progressive Disclosure schema.
Can be called from post-task-output.sh for strict validation.
"""

import sys
import re
import yaml
from typing import Optional


def extract_l1_yaml(output: str) -> Optional[dict]:
    """Extract L1 YAML block from output."""
    # Look for ```yaml ... ``` block
    yaml_match = re.search(r'```yaml\s*\n(.*?)\n```', output, re.DOTALL)
    if yaml_match:
        try:
            return yaml.safe_load(yaml_match.group(1))
        except yaml.YAMLError:
            return None
    return None


def validate_l1_progressive_disclosure(l1_yaml: dict) -> list[str]:
    """Validate Progressive Disclosure fields in L1."""
    errors = []

    # Required base fields
    required_fields = ['taskId', 'agentType', 'summary', 'status']
    for field in required_fields:
        if field not in l1_yaml:
            errors.append(f"Missing required field: {field}")

    # Validate status
    valid_statuses = ['success', 'partial', 'failed']
    if l1_yaml.get('status') not in valid_statuses:
        errors.append(f"Invalid status: {l1_yaml.get('status')}. Must be one of {valid_statuses}")

    # Progressive Disclosure fields
    if "priority" not in l1_yaml:
        errors.append("Missing required field: priority")
    elif l1_yaml["priority"] not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        errors.append(f"Invalid priority: {l1_yaml['priority']}")

    # Conditional validation: criticalCount > 0 requires CRITICAL priority
    critical_count = l1_yaml.get("criticalCount", 0)
    if isinstance(critical_count, int) and critical_count > 0:
        if l1_yaml.get("priority") != "CRITICAL":
            errors.append("priority should be CRITICAL when criticalCount > 0")

    # recommendedRead validation for CRITICAL/HIGH
    if l1_yaml.get("priority") in ["CRITICAL", "HIGH"]:
        if not l1_yaml.get("recommendedRead"):
            errors.append("recommendedRead required for CRITICAL/HIGH priority")
        else:
            # Validate recommendedRead structure
            for idx, item in enumerate(l1_yaml.get("recommendedRead", [])):
                if "anchor" not in item:
                    errors.append(f"recommendedRead[{idx}] missing anchor")
                if "reason" not in item:
                    errors.append(f"recommendedRead[{idx}] missing reason")

    # l2Index validation
    l2_index = l1_yaml.get("l2Index", [])
    if not l2_index:
        errors.append("l2Index is required")
    else:
        for idx, item in enumerate(l2_index):
            if "anchor" not in item:
                errors.append(f"l2Index[{idx}] missing anchor")
            if "tokens" not in item:
                errors.append(f"l2Index[{idx}] missing tokens estimate")
            if "priority" not in item:
                errors.append(f"l2Index[{idx}] missing priority")
            if "description" not in item:
                errors.append(f"l2Index[{idx}] missing description")

    # l2Path validation
    if not l1_yaml.get("l2Path"):
        errors.append("Missing required field: l2Path")

    # requiresL2Read validation
    if "requiresL2Read" not in l1_yaml:
        errors.append("Missing required field: requiresL2Read")

    return errors


def validate_token_count(l1_yaml: dict, max_tokens: int = 500) -> list[str]:
    """Estimate and validate L1 token count."""
    warnings = []

    # Rough estimation: ~4 chars per token
    l1_text = yaml.dump(l1_yaml, default_flow_style=False)
    estimated_tokens = len(l1_text) // 4

    if estimated_tokens > max_tokens:
        warnings.append(f"L1 exceeds token limit: ~{estimated_tokens} tokens (max: {max_tokens})")

    return warnings


def main():
    """Main entry point for CLI usage."""
    import json

    # Read from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            output = f.read()
    else:
        output = sys.stdin.read()

    # Extract and validate L1
    l1_yaml = extract_l1_yaml(output)

    if l1_yaml is None:
        result = {
            "valid": False,
            "errors": ["Could not extract L1 YAML block from output"],
            "warnings": []
        }
    else:
        errors = validate_l1_progressive_disclosure(l1_yaml)
        warnings = validate_token_count(l1_yaml)
        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "extracted_priority": l1_yaml.get("priority", "UNKNOWN"),
            "extracted_status": l1_yaml.get("status", "unknown")
        }

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
