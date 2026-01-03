# Knowledge Base 00: Core Architecture & The OSDK Paradox
> **Module ID**: `00_palantir_core_architecture`
> **Prerequisites**: None
> **Estimated Time**: 15 Minutes

## 1. Universal Concept: Stateless REST vs. Managed State
In distributed systems, a fundamental tension exists between **Stateless Clients** (which scale easily but are "dumb") and **Managed State** (which is smart but hard to synchronize).

**The Architectural Fallacy**: Believing that a REST API wrapper (SDK) should behave like a Database (caching, dirty checking, write-back).
- **Reality**: Most modern SDKs are **Stateless Gateways**. They transport data but do not own its lifecycle.
- **Orion's Lesson**: We initially over-engineered an `ObjectManager` to act like a database client. We learned that the **Kernel (Polling)** capability is the true owner of state, not the SDK calls.

---

## 2. Technical Explanation
**The "Phonograph Pattern" is a Myth.** The Palantir Python SDK is a thin wrapper.

**Wrong Way (Stateful Assumption)**:
```python
# ❌ Anti-Pattern: Expecting the SDK to track changes
user = client.get_object("123")
user.name = "New Name"
# Expecting some background thread to save this? No.
```

**Right Way (Stateless RPC)**:
```python
import asyncio
from palantir.osdk import FoundryClient

async def update_stateless(client: FoundryClient, obj_id: str):
    # 1. Fetch Snapshot (Data is detached immediately)
    obj = await client.ontology.objects.get(obj_id)
    
    # 2. Mutate via Explicit Action (RPC)
    # The Action is a Transactional Event, not a local field update.
    await client.ontology.actions.apply(
        "updateUser",
        {
            "userId": obj_id,
            "newName": "New User Name"
        }
    )
    # 3. Re-fetch if you need latest state
    return await client.ontology.objects.get(obj_id)
```

---

## 3. Cross-Stack Comparison

| Feature | **Python OSDK** (Orion) | **React OSDK** (Frontend) | **Java/Hibernate** (Traditional) |
|:--- |:--- |:--- |:--- |
| **State** | **Stateless** (Snapshot) | **Stateless** (Snapshot) | **Stateful** (Attached) |
| **Caching** | Application Responsibility | SWR / React Query | L1/L2 Session Cache |
| **Updates** | Explicit Action Call | Explicit Action Call | `session.flush()` (Implicit) |
| **Sync** | Polling | Subscriptions (WebSocket) | Connection/Transaction |

---

## 4. Palantir Context (Foundry Architecture)
How Orion ODA maps to real Foundry architecture:

1.  **Foundry Client = Stateless REST**: The `foundry-platform-python` package has no internal cache.
2.  **Kernel = Compute Module**: Orion's `Kernel` loop mirrors a Palantir **Compute Module Container**.
    - **Pattern**: A container that runs forever, **polling** a queue or stream for jobs.
    - It is NOT a "Serverless Function" (which spins down). It is a "Stateful Worker" using stateless tools.
3.  **Ontology = Schema**: The "Source of Truth" is the server (Phonograph), not the client memory.

---

## 5. Design Philosophy
> "State is the root of all evil. Default to statelessness. Add state only when you absolutely cannot deliver the user experience without it."
> — *Anders Hejlsberg (TypeScript Creator)*

> "The OSDK is designed to get out of your way. It does not try to be a database. It tries to be a typed connection to the Ontology."
> — *Palantir OSDK Team Guidelines*

---

## 6. Practice Exercise: The "Optimistic UI"
**Challenge**: Implement a function that updates an object and returns the *predicted* state immediately, while verifying it asynchronously.

```python
# Todo: Implement this function
async def optimistic_update(client, user_id: str, new_name: str):
    # 1. Calculate Expected State (Local)
    # 2. Fire Action (Async)
    # 3. Return Expected State immediately
    pass
```

**(Self-Correction Hint)**: Did you wait for the Action to complete? True Optimistic UI doesn't wait! But in Python backend logic, we usually *do* wait for confirmation (Consistency > Latency).

---

## 7. Adaptive Next Steps
- **If you understand this**: Proceed to **[01_Language_Foundation](./01_language_foundation.md)** to see how Type Safety enforces this statelessness.
- **If confused**: Review **[09_Orion_ODA](./09_orion_system_architecture.md)** for a high-level diagram of the Kernel Loop.