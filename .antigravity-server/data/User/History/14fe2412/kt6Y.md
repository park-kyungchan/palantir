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
*Source: `scripts/ontology/actions/__init__.py`*

```python
class ActionType(ABC, Generic[T]):
    """Base class for all ActionTypes in ODA v3.0"""
    
    # Class attributes
    api_name: ClassVar[str]
    object_type: ClassVar[Type[T]]
    submission_criteria: ClassVar[List[SubmissionCriterion]] = []
    side_effects: ClassVar[List[SideEffect]] = []
    requires_proposal: ClassVar[bool] = False  # Hazardous flag

    async def execute(self, params, context) -> ActionResult:
        # 1. Validate (SubmissionCriteria)
        # 2. Apply Edits with ConcurrencyError retry (3x)
        # 3. Side Effects (async, fire-and-forget)
```

### B.1 Built-in Submission Criteria
- `RequiredField(field_name)`: Essential data validation.
- `MaxLength(field_name, max)`: String constraints.
- `AllowedValues(field_name, [values])`: Enum-like validation.
- `CustomValidator(name, fn, error_msg)`: Arbitrary logic.

### B.2 Built-in Side Effects
- `LogSideEffect()`: Compliance logging.
- `WebhookSideEffect(url)`: External system integration.
- `SlackNotification(channel)`: Operational alerts.

### C. The Runtime (Kernel Loop)
The "engine" that drives the system. It uses an **Active Polling** mechanism.
*Source: `scripts/runtime/kernel.py`*

#### ToolMarshaler
*Source: `scripts/runtime/marshaler.py`*

The `ToolMarshaler` provides a secure marshaling layer for executing Actions, ensuring that raw permissions are never exposed directly to the LLM.

```python
class ToolMarshaler:
    async def execute_action(self, action_name, params, context) -> ActionResult:
        # 1. Validate Action existence
        # 2. Instantiate Action (Stateless)
        # 3. Execute (Delegates to ActionType.execute)
        return await action_instance.execute(params, context)
```

1.  **Cognitive Phase**: LLM (Instructor) converts User Intent -> `Plan` (JSON).
2.  **Governance Phase**: Check `ActionMetadata`.
    *   Safe? -> Execute Immediately via `ToolMarshaler`.
    *   Hazardous? -> Create `Proposal` (Wait for Human/Admin).
3.  **Execution Phase**: `ToolMarshaler` handles the safe invocation.

### D. Persistence Layer (NEW)
*Source: `scripts/ontology/storage/`*

#### D.1 Repository Pattern
The deprecated `ObjectManager` cached layer has been replaced by explicit, domain-specific repositories.
- `ProposalRepository`: Async ORM, audit history, status workflow.
- `ActionLogRepository`: Immutable execution logs.

#### D.2 ProposalRepository
```python
class ProposalRepository:
    async def save(self, proposal, actor_id) -> None
    async def find_by_id(self, id) -> Optional[Proposal]
    async def approve(self, id, reviewer_id, comment) -> Proposal
    async def execute(self, id, executor_id, result) -> Proposal
    async def get_history(self, id) -> List[AuditEntry]
```

#### D.3 Optimistic Locking
All repositories enforcement version-based concurrency control:
- `ConcurrencyError` raised on version mismatch.
- `ActionType.execute()` includes automatic retry (3x with exponential backoff).

---

## 3. Cross-Stack Comparison

| Feature | Orion ODA | Redux (React) | Terraform | Kubernetes |
| :--- | :--- | :--- | :--- | :--- |
| **State** | Ontology DB | Store | tfstate | etcd |
| **Mutation** | ActionType | Action/Reducer | Resource | Controller |
| **Logic** | GovernanceEngine | Middleware | Provider | Reconciliation Loop |
| **Validation** | SubmissionCriteria | PropTypes/TS | Schema | Admission Controller |

---

## 4. Palantir Context (Code-Level)

### 4.1 OSDK Entry Point (TypeScript)
The Orion Kernel's initialization mirrors the **Foundry Ontology SDK (OSDK)** client creation. Just as Orion injects `GEMINI.md`, the OSDK injects the `OntologyMetadata` into the client.

```typescript
// Real OSDK Initialization Pattern (Frontend/Public)
import { createClient } from "@osdk/client";
import { createPublicOauthClient } from "@osdk/oauth";

const client = createClient(
  "https://stack.palantirfoundry.com",
  "my-ontology-rid",
  createPublicOauthClient(
    "my-client-id",
    "https://stack.palantirfoundry.com", // Platform URL
    "https://myapp.com/callback"       // Redirect URL (Required)
  )
);

// Orion's Equivalent (kernel.py)
// runtime = OrionRuntime(ontology_path="scripts/ontology")
```

### 4.2 AIP Logic & System Prompts
In **Palantir AIP Logic**, the "System Prompt" is configured in the **"Use LLM"** block. It defines the "Constitution" for that specific logic chain.

```json
// AIP Logic Block Configuration
{
  "type": "llm_inference",
  "system_prompt": "You are a Flight Control Agent. You have access to the [Airports, Flights] ontology objects...",
  "tools": ["query_ontology", "call_function"],
  "temperature": 0.0
}
```
Orion's `GEMINI.md` serves the exact same purpose but at the *Agent Root* level.

### 4.3 Functions on Objects
Orion's `Actions` are isomorphic to **Foundry Functions**:

```typescript
// Foundry Function (TypeScript v2)
import { Function, Integer } from "@foundry/functions-api";
import { Ticket } from "@foundry/ontology-api";

export default async function upgradeTicket(ticket: Ticket): Promise<void> {
    if (ticket.status === 'economy') {
        ticket.status = 'business'; // Mutation
    }
}

// Orion Action
async def execute(self, ticket: Ticket, context):
    if ticket.status == 'economy':
        ticket.status = 'business' # Mutation
```
Both systems enforce that **logic must be wrapped in defined functions/actions**, never raw DB writes.

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
