# Palantir FDE Learning: Orion System Architecture (ODA)

## 1. Universal Concept: Ontology-Driven Architecture (ODA)
**Definition:** A system design where the **Data Model (Ontology)** is the single source of truth for both structure and logic. Instead of code manipulating loose data, all state changes are defined as **Actions** within the Ontology itself.

**Core Principles:**
1.  **Schema is Law:** If it's not in the Ontology, it doesn't exist.
2.  **Governance by Design:** State mutations are gated by strict **Action Definitions** (Validators).
3.  **decoupled Execution:** The "Brain" (LLM) defines a **Plan** (Data), the "Kernel" (Runtime) executes it.

---

## 2. Technical Explanation (The Orion Implementation)

The Orion System is a concrete implementation of ODA in Python.

### A. The Schema (Ontology Types)
The "nouns" of the system. Every entity inherits from `OntologyObject`.
*Source: `scripts/ontology/ontology_types.py`*

```python
class OntologyObject(BaseModel):
    id: str = Field(default_factory=generate_object_id)
    version: int = Field(default=1)  # Optimistic Locking
    status: ObjectStatus = ObjectStatus.ACTIVE

# Example Domain Object
class Task(OntologyObject):
    title: str
    assigned_to: Link[Agent] = Link(target=Agent, cardinality="1:1")
```

### B. The Logic (Action Registry)
The "verbs" of the system. Direct database implementation is forbidden. You must define an `ActionType`.
*Source: `scripts/ontology/actions.py`*

```python
class ActionType(ABC):
    submission_criteria: List[SubmissionCriterion] = []
    
    async def execute(self, params, context):
        # 1. Validate
        self.validate(params)
        # 2. Mutate (Atomic)
        obj, edits = await self.apply_edits(params)
        # 3. Side Effects (Async)
        await self.run_side_effects()
```

### C. The Runtime (Kernel Loop)
The "engine" that drives the system. It uses an **Active Polling** mechanism.
*Source: `scripts/runtime/kernel.py`*

1.  **Cognitive Phase**: LLM (Instructor) converts User Intent -> `Plan` (JSON).
2.  **Governance Phase**: Check `ActionMetadata`.
    *   Safe? -> Execute Immediately.
    *   Hazardous? -> Create `Proposal` (Wait for Human/Admin).
3.  **Execution Phase**: `ToolMarshaler` routes the Action to the Registry.

---

## 3. Cross-Stack Comparison

| Feature | Orion ODA | Redux (React) | Terraform | Kubernetes |
| :--- | :--- | :--- | :--- | :--- |
| **State** | Ontology DB | Store | tfstate | etcd |
| **Mutation** | ActionType | Action/Reducer | Resource | Controller |
| **Logic** | GovernanceEngine | Middleware | Provider | Reconciliation Loop |
| **Validation** | SubmissionCriteria | PropTypes/TS | Schema | Admission Controller |

---

## 4. Palantir Context
This architecture mirrors **Palantir AIP (Artificial Intelligence Platform)** and **Foundry**:

*   **Ontology**: The central nervous system of the enterprise.
*   **Actions**: The only way to write back to the Ontology (replacing CRUD).
*   **Functions**: Logic that runs on top of objects (Orion's "Thinking").
*   **Logic**: AIP Logic determines *which* tool/action to use (Orion's `Plan`).

> "In Foundry, you don't write SQL `INSERT` statements. You trigger an **Action** which has been pre-configured with permissions, validation logic, and side effects (like email notifications)."

---

## 5. Design Philosophy
> **"Code as Data"**
> By representing the "Plan" as a Pydantic Model (`scripts/ontology/plan.py`) rather than executing arbitrary Python code, we allow the system to **introspect, validate, and audit** its own thoughts before acting.

> **"Optimistic Concurrency"**
> The `version` field in `OntologyObject` prevents race conditions in a multi-agent environment (Gemini vs Claude vs User) without heavy database locking.

---

## 6. Practice Exercise
**Task:** Create a new Action in the Orion System.

**Requirements:**
1.  Define a `ArchiveOldTasks` action in `scripts/ontology/actions.py` (or a content file).
2.  **Criteria**: Task must be > 30 days old (CustomValidator).
3.  **Side Effect**: Log the count of archived tasks.
4.  **Governance**: Mark it as `requires_proposal=True` (Destructive action).

**Deliverable:**
```python
@register_action(requires_proposal=True)
class ArchiveOldTasks(ActionType[Task]):
    api_name = "archive_old_tasks"
    # Implement apply_edits...
```

---

## 7. Adaptive Next Steps
Now that you understand the "Brain" (Ontology) and "Body" (Runtime), explore how **Memory** works in `scripts/consolidation.py` to see how the system learns from its own executions.
