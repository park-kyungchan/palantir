# MCP Research Findings

**Date:** 2026-01-05
**Method:** Context7 + Tavily + Sequential-Thinking

---

## MCP Tools Used for Palantir Research

### 1. Context7 (Library Resolution)

```
Query: "Palantir Foundry OSDK Action Types"
Result: /websites/palantir_foundry (9896 snippets, High Reputation)
```

### 2. Context7 (Documentation Query)

| Query | Key Findings |
|-------|--------------|
| Action Types submission criteria | Regex validation, `^[A-Z]{3}$` pattern |
| Side Effects webhook | Writeback vs Side Effect timing |
| Proposal approval workflow | eligible_reviewers, required_approvals |

### 3. Tavily (Web Search)

```
Query: "Palantir AIP Foundry Action Types OSDK architecture 2024"
Sources:
- blog.palantir.com/building-with-palantir-aip
- palantir.com/docs/foundry/ontology-sdk
```

## Key Patterns Discovered

| Pattern | Description |
|---------|-------------|
| **Writeback** | Pre-mutation hook; failure aborts action |
| **Side Effect** | Post-mutation hook; failure logged only |
| **Approval Policy** | configurable reviewers, approval count |

## Integration with ODA

These patterns are mapped to ODA in:
- `actions/__init__.py` (SubmissionCriteria)
- `side_effects.py` (SideEffect protocol)
- `proposal.py` (Governance workflow)
