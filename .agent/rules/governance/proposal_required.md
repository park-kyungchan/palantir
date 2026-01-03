---
description: Actions requiring Proposal approval before execution
---

# Proposal Required Actions

## Criteria
- Database schema changes
- Bulk data modifications
- External API deployments
- Permission modifications

## Flow
```
[Request] → [GovernanceEngine] → [Proposal] → [Approval] → [Execution]
```

## Code
- `PolicyResult.decision == "REQUIRE_PROPOSAL"`
