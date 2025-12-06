---
description: Create and Dispatch a Governed Plan (Tier 1 Action)
---

# 📋 Workflow: Ontology Planning

## 1. Concept
In Orion V3 (Palantir ODA), you do not "just run code". You create a **Plan Object** (Digital Twin of Intent) and dispatch it to the Governance Funnel.

## 2. Schema Definition
Your Plan must conform to `.agent/schemas/plan.schema.json`.

```json
{
  "id": "UUID",
  "plan_id": "human-readable-id",
  "objective": "Task Goal",
  "jobs": [
    {
      "id": "job_1",
      "action_name": "run_command",
      "action_args": { "CommandLine": "ls -la", "SafeToAutoRun": true }
    }
  ]
}
```

## 3. Dispatch
Use the CLI to validate and persist the plan.

```bash
./scripts/orion dispatch --file path/to/plan.json
```

## 4. Governance Check
The engine will:
1. Validate against Pydantic Schema.
2. Log the intent to `.agent/logs/ontology_ledger.jsonl`.
3. Persist the file to `.agent/plans/`.
