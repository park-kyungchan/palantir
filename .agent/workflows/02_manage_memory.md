---
description: Manually inject Insights and Patterns into the Semantic Memory
---
# 02_manage_memory: Knowledge Injection

## 1. Interactive Memory Shell
- **Goal**: Manually add insights or patterns to LTM.
- **Action**: Initialize memory directories and generate JSON schemas for reference.
```bash
mkdir -p .agent/memory/semantic/insights .agent/memory/semantic/patterns .agent/schemas
source .venv/bin/activate && python - <<'PY'
import json
from pathlib import Path
from scripts.ontology.schemas.memory import OrionInsight, OrionPattern

out_dir = Path(".agent/schemas")
out_dir.mkdir(parents=True, exist_ok=True)

insight_schema = OrionInsight.model_json_schema()
pattern_schema = OrionPattern.model_json_schema()

(out_dir / "insight.schema.json").write_text(json.dumps(insight_schema, indent=2))
(out_dir / "pattern.schema.json").write_text(json.dumps(pattern_schema, indent=2))
print("Schemas written:", out_dir / "insight.schema.json", out_dir / "pattern.schema.json")
PY
```
    
- **Manual Action**:
    1. Create a JSON file in `.agent/memory/semantic/insights/`.
    2. Validate against `.agent/schemas/insight.schema.json`.
