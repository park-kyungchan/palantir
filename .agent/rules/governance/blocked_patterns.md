---
description: Dangerous command patterns that are blocked by PolicyResult
---

# Blocked Patterns

## Security Blocks
- `rm -rf` - Dangerous recursive deletion
- `sudo rm` - Sudo deletion not allowed
- `chmod 777` - Insecure permissions

## Code Reference
- `GovernanceEngine._check_dangerous_params()`
- `PolicyResult.decision == "BLOCK"`
