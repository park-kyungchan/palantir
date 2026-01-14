# Ontology Schemas

This directory holds exported ontology definitions derived from the runtime registry.

Generate the registry snapshot:
```bash
source .venv/bin/activate && python -m scripts.ontology.registry
```

This command also exports LLM-facing schemas:
- `proposal.schema.json` (Pydantic JSON Schema for `Proposal`)
- `stage_evidence.schema.json` (Pydantic JSON Schema for hazardous file operations)
- `action_schemas.json` (Action payload schemas derived from submission criteria)
- `link_registry.json` (LinkType registry snapshot)
