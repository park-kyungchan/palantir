# ORION ORCHESTRATOR V2 - DOCUMENTATION INDEX

> **Last Updated**: 2025-12-27
> **Maintainer**: Claude 4.5 Opus + Gemini 3.0 Pro

---

## QUICK NAVIGATION

| Document | Purpose | Priority |
|----------|---------|----------|
| [AGENT_WORK_PROTOCOL.md](./AGENT_WORK_PROTOCOL.md) | LLM-Agnostic execution guide | **READ FIRST** |
| [AGENT_HANDOFF_PROTOCOL.md](./AGENT_HANDOFF_PROTOCOL.md) | Claude ↔ Gemini collaboration | **REQUIRED** |
| [TASK_TEMPLATES.md](./TASK_TEMPLATES.md) | Copy-paste code templates | **REFERENCE** |
| [GAP_ANALYSIS_PALANTIR_AIP.md](./GAP_ANALYSIS_PALANTIR_AIP.md) | Palantir architecture comparison | CONTEXT |
| [MAINTAINABILITY_SCALABILITY_GUIDE.md](./MAINTAINABILITY_SCALABILITY_GUIDE.md) | Long-term maintenance | PLANNING |

---

## DOCUMENT PURPOSES

### 1. AGENT_WORK_PROTOCOL.md
**WHO**: Any LLM Agent
**WHAT**: Step-by-step execution instructions with zero ambiguity
**WHEN**: Before any task execution

Contains:
- Absolute rules
- File structure reference
- Action execution protocol
- All available actions with exact parameters
- Error handling matrix
- Validation rules

### 2. AGENT_HANDOFF_PROTOCOL.md
**WHO**: Claude 4.5 Opus + Gemini 3.0 Pro
**WHAT**: Inter-agent communication protocol
**WHEN**: Switching between agents

Contains:
- Role definitions (Orchestrator vs Logic Core)
- Handoff file format
- Agent-specific execution protocols
- Workflow diagrams
- Sample handoffs

### 3. TASK_TEMPLATES.md
**WHO**: Any LLM Agent writing code
**WHAT**: Copy-paste ready code templates
**WHEN**: Implementing features

Contains:
- 10 task templates (T1-T10)
- Object type creation
- Action implementation
- Repository methods
- API endpoints
- Validation cheatsheets

### 4. GAP_ANALYSIS_PALANTIR_AIP.md
**WHO**: Project Owner / Planning
**WHAT**: Comparison with Palantir AIP/Foundry architecture
**WHEN**: Strategic planning

Contains:
- Feature comparison matrix
- Gap severity ratings
- Implementation roadmap
- Priority recommendations

### 5. MAINTAINABILITY_SCALABILITY_GUIDE.md
**WHO**: Long-term maintainer
**WHAT**: Production-ready patterns
**WHEN**: Before deployment

Contains:
- Code organization recommendations
- Testing strategy
- Error handling patterns
- Logging configuration
- Deployment configurations
- Scaling patterns

---

## AGENT INFRASTRUCTURE FILES

```
/home/palantir/orion-orchestrator-v2/scripts/agent/
├── __init__.py         # Module exports
├── executor.py         # AgentExecutor class (ENTRY POINT)
└── protocols.py        # ExecutionProtocol, TaskResult
```

---

## READING ORDER

### For New Agents
1. AGENT_WORK_PROTOCOL.md (entire document)
2. TASK_TEMPLATES.md (T4: Execute Action)
3. AGENT_HANDOFF_PROTOCOL.md (if collaborating)

### For Feature Implementation
1. AGENT_HANDOFF_PROTOCOL.md (get handoff)
2. TASK_TEMPLATES.md (find relevant template)
3. AGENT_WORK_PROTOCOL.md Section 4 (action reference)

### For Architecture Understanding
1. GAP_ANALYSIS_PALANTIR_AIP.md
2. MAINTAINABILITY_SCALABILITY_GUIDE.md
3. CLAUDE.md + GEMINI.md (protocol definitions)

---

## KEY FILE PATHS

### Entry Points
```
AGENT EXECUTOR:    scripts/agent/executor.py
API SERVER:        scripts/api/main.py
KERNEL:            scripts/runtime/kernel.py
```

### Ontology Core
```
BASE TYPES:        scripts/ontology/ontology_types.py
ACTIONS:           scripts/ontology/actions.py
TASK ACTIONS:      scripts/ontology/objects/task_actions.py
PROPOSAL:          scripts/ontology/objects/proposal.py
```

### Storage
```
DATABASE:          scripts/ontology/storage/database.py
REPOSITORY:        scripts/ontology/storage/proposal_repository.py
MODELS:            scripts/ontology/storage/models.py
```

### Data
```
SQLITE DB:         data/ontology.db
RELAY QUEUE:       relay.db
```

### Handoffs
```
PENDING:           .agent/handoffs/pending/
COMPLETED:         .agent/handoffs/completed/
```

---

## COMMAND REFERENCE

### Start API Server
```bash
cd /home/palantir/orion-orchestrator-v2
python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8000
```

### Start Kernel
```bash
cd /home/palantir/orion-orchestrator-v2
python -m scripts.runtime.kernel
```

### Run Tests
```bash
cd /home/palantir/orion-orchestrator-v2
python -m pytest tests/ -v
```

### Execute Action (Python)
```python
from scripts.agent.executor import AgentExecutor
executor = AgentExecutor()
await executor.initialize()
result = await executor.execute_action("create_task", {"title": "X"}, "agent")
```

---

## VERSIONING

| Document | Version | Last Updated |
|----------|---------|--------------|
| AGENT_WORK_PROTOCOL | v1.0 | 2025-12-27 |
| AGENT_HANDOFF_PROTOCOL | v1.0 | 2025-12-27 |
| TASK_TEMPLATES | v1.0 | 2025-12-27 |
| GAP_ANALYSIS | v1.0 | 2025-12-27 |
| MAINTAINABILITY_GUIDE | v1.0 | 2025-12-27 |

---

**END OF INDEX**
