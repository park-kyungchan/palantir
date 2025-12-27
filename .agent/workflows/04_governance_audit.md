---
description: Inspect the Immutable Audit Log (Ontology DB)
---
# 04_governance_audit: Audit Log Inspection

## 1. Proposal History Check
- **Goal**: View history of a specific Proposal.
- **Action**:
```bash
# Usage: python -m scripts.ontology.tools.audit --proposal_id [ID]
echo "Please provide Proposal ID to inspect."
```

## 2. Action Trace Inspection
- **Goal**: View recent action executions (raw logs).
- **Action**:
    - List files in `.agent/traces/`.
```bash
ls -lt .agent/traces/ | head -n 10
```
