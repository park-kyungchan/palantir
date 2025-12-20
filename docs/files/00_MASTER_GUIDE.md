# Orion ODA v3.0 Refactoring Master Guide

> **Date**: 2025-12-20
> **Reviewer**: Senior Developer (External)
> **Total Estimated Time**: 5.5 hours

---

## 📦 Delivery Contents

| File | Module | Priority | Time |
|:---|:---|:---:|:---:|
| `01_ontology_types.md` | `scripts/ontology/ontology_types.py` | 🟢 P3 | 30m |
| `02_proposal.md` | `scripts/ontology/objects/proposal.py` | 🔴 P0 | 1h |
| `03_actions.md` | `scripts/ontology/actions.py` | 🔴 P0 | 3h |
| `04_ollama_client.md` | `scripts/llm/ollama_client.py` | 🟡 P1 | 1h |

---

## ⚠️ Critical: Apply in Order

Dependencies require **strict sequential application**:

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 01_ontology_types.md                               │
│  └── Foundation layer (Cardinality, Link, OntologyObject)   │
├─────────────────────────────────────────────────────────────┤
│  Step 2: 02_proposal.md                                     │
│  └── Depends on: OntologyObject from Step 1                 │
├─────────────────────────────────────────────────────────────┤
│  Step 3: 03_actions.md                                      │
│  └── Depends on: OntologyObject from Step 1                 │
│  └── Integrates with: Proposal from Step 2                  │
├─────────────────────────────────────────────────────────────┤
│  Step 4: 04_ollama_client.md                                │
│  └── Independent (can be applied anytime)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Commands

### Step 1: Apply ontology_types.py

```bash
# Backup existing file
cp scripts/ontology/ontology_types.py scripts/ontology/ontology_types.py.bak

# Apply new implementation (copy code block from 01_ontology_types.md)
# Then verify:
python -c "
from scripts.ontology.ontology_types import *
assert Cardinality.ONE_TO_MANY.value == '1:N'
obj = OntologyObject()
assert len(obj.id) == 36
print('✅ Step 1 passed')
"
```

### Step 2: Apply proposal.py

```bash
# Backup existing file
cp scripts/ontology/objects/proposal.py scripts/ontology/objects/proposal.py.bak

# Apply new implementation (copy code block from 02_proposal.md)
# Then verify:
python -c "
from scripts.ontology.objects.proposal import *
p = Proposal(action_type='test', created_by='agent-001')
p.submit()
assert p.status == ProposalStatus.PENDING
print('✅ Step 2 passed')
"
```

### Step 3: Apply actions.py

```bash
# Backup existing file
cp scripts/ontology/actions.py scripts/ontology/actions.py.bak

# Apply new implementation (copy code block from 03_actions.md)
# Then verify:
python -c "
from scripts.ontology.actions import *
rf = RequiredField('title')
try:
    rf.validate({'title': ''}, ActionContext.system())
except ValidationError:
    print('✅ Step 3 passed')
"
```

### Step 4: Apply ollama_client.py

```bash
# Backup existing file
cp scripts/llm/ollama_client.py scripts/llm/ollama_client.py.bak

# Apply new implementation (copy code block from 04_ollama_client.md)
# Then verify:
python -c "
from scripts.llm.ollama_client import *
router = HybridRouter()
d = router.route('Delete database')
assert d.target == RouteTarget.RELAY
print('✅ Step 4 passed')
"
```

### Full Verification

```bash
# Run all tests
python tests/e2e/test_v3_production.py
```

---

## 📝 Post-Refactoring Tasks

After applying all refactoring snippets:

### 1. Update `core_definitions.py`

Add concrete ActionTypes for Task and Agent:

```python
# scripts/ontology/objects/core_definitions.py

from scripts.ontology.actions import (
    ActionType, register_action, RequiredField, 
    AllowedValues, MaxLength, EditType, EditOperation,
    ActionContext, LogSideEffect
)
from scripts.ontology.ontology_types import OntologyObject, Link, Cardinality

class Task(OntologyObject):
    title: str
    description: str = ""
    priority: str = "medium"
    assigned_to_id: Optional[str] = None  # FK to Agent
    
    # Link definition
    assigned_to: ClassVar[Link["Agent"]] = Link(
        target=Agent,
        link_type_id="task_assigned_to_agent",
        cardinality=Cardinality.MANY_TO_ONE,
    )

@register_action
class CreateTaskAction(ActionType[Task]):
    api_name = "create_task"
    object_type = Task
    
    submission_criteria = [
        RequiredField("title"),
        AllowedValues("priority", ["low", "medium", "high"]),
        MaxLength("title", 255),
    ]
    
    side_effects = [LogSideEffect()]
    
    async def apply_edits(self, params, context):
        task = Task(**params, created_by=context.actor_id)
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Task",
            object_id=task.id,
            changes=params,
        )
        return task, [edit]
```

### 2. Create Router Config File

```bash
mkdir -p config
cat > config/router.yaml << 'EOF'
word_threshold: 50
sentence_threshold: 5
critical_keywords:
  - delete
  - deploy
  - production
  - database
ollama_base_url: "http://localhost:11434"
ollama_model: "llama3.2"
EOF
```

### 3. Update GEMINI.md Protocol

Add to governance rules:

```markdown
## Action Rules
- All Ontology mutations MUST use ActionType classes
- Hazardous actions MUST set `requires_proposal = True`
- Side effects execute ONLY after successful commit
```

---

## 🔍 Architecture Diagram (Post-Refactoring)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User / External System                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      HybridRouter (A4)                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │
│  │  Keywords   │───▶│ Complexity  │───▶│ RoutingDecision         │  │
│  │  Detection  │    │ Scoring     │    │ (LOCAL/RELAY + reason)  │  │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                          │                           │
              ┌───────────┘                           └───────────┐
              ▼                                                   ▼
┌─────────────────────────┐                     ┌─────────────────────────┐
│   OllamaClient (A4)     │                     │   RelayQueue            │
│   - Async generation    │                     │   - SQLite WAL          │
│   - Retry logic         │                     │   - Atomic dequeue      │
└─────────────────────────┘                     └─────────────────────────┘
              │                                                   │
              └───────────────────────┬───────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ActionType (A2)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ SubmissionCrit. │─▶│   apply_edits() │─▶│   SideEffects       │  │
│  │ (Validation)    │  │ (Transactional) │  │ (Post-commit)       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   OntologyObject    │  │     Proposal        │  │    EditOperation    │
│   (A5)              │  │     (A3)            │  │    (Audit Trail)    │
│   - UUID PK         │  │   - State Machine   │  │                     │
│   - Audit fields    │  │   - approve/reject  │  │                     │
│   - Versioning      │  │   - execute         │  │                     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

---

## ✅ Definition of Done

All refactoring is complete when:

- [ ] All 4 modules replaced with new implementations
- [ ] All verification tests pass
- [ ] `test_v3_production.py` passes
- [ ] `GEMINI.md` updated with new governance rules
- [ ] `config/router.yaml` created
- [ ] No import errors in kernel.py

---

**End of Master Guide**
