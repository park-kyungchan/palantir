---
description: Inspect the Immutable Audit Log (Ontology DB)
---
# 04_governance_audit: Audit Log Inspection

## 1. Proposal History Check
- **Goal**: View history of a specific Proposal.
- **Action**:
```bash
source .venv/bin/activate && python -c "from scripts.ontology.objects.proposal import ProposalStatus; print('✅ ProposalStatus Ready')"
```

## 2. Action Trace Inspection
- **Goal**: View recent action executions (raw logs).
- **Action**:
    - List files in `.agent/traces/`.
```bash
mkdir -p .agent/traces
ls -lt .agent/traces/ | head -n 10
```
