# Palantir AIP & OSDK architecture: Orion ODA validation

**Bottom line**: Orion ODA's architecture demonstrates **solid conceptual alignment** with Palantir's actual patterns but includes significant over-engineering in the ObjectManager caching layer and misconceptions about the Apollo governance model. The "Phonograph Pattern" caching is **architecturally unnecessary** since both Python and TypeScript OSDKs are stateless thin REST wrappers. However, the Kernel polling pattern closely mirrors Palantir's Compute Module architecture, validating that design choice.

---

## Part 1: The Phonograph myth—OSDK is stateless

The `foundry-platform-python` SDK is an **auto-generated, thin REST API wrapper** with zero client-side caching. Each API call maps directly to an HTTP endpoint with no object identity tracking, dirty detection, or write-back buffering. The `FoundryClient` class is purely organizational—a structured entry point that groups API namespaces.

**Evidence from the SDK**:
- No cache configuration options exist in the `Config` class
- Methods return Pydantic models directly (immutable data classes, not managed entities)
- Session management covers only HTTP/OAuth concerns, not data lifecycle
- The only "caching" is OAuth token caching in `palantir-oauth-client`, unrelated to object state

The TypeScript OSDK (`osdk-ts`) follows the same philosophy. `OsdkProvider` in React is **not a caching layer**—it provides authentication context distribution via React Context API, nothing more. Palantir's official recommendation is to use **SWR (stale-while-revalidate)** or React Query for caching:

```typescript
const { data, mutate } = useSWR<ITask[]>(
  ["tasks", project.$primaryKey],  // Cache key
  fetcher,
  { revalidateOnFocus: false }
);
```

**TypeScript's advantage**: OSDK 2.1+ supports real-time subscriptions (`object.subscribe()`) for reactive updates, which Python lacks entirely. But neither SDK maintains internal object caches.

| Feature | Python SDK | TypeScript SDK | Orion ObjectManager |
|---------|-----------|----------------|---------------------|
| Built-in caching | None | None | Custom TTL cache |
| Identity tracking | None | None | RID → object map |
| Write pattern | Immediate per-call | Immediate per-call | Write-back buffered |
| Optimistic locking | Server-side only | Server-side only | Client-side version |
| Real-time updates | Not available | Subscriptions (2.1+) | Manual polling |

**Verdict on ObjectManager**: The Phonograph write-back caching pattern is **over-engineering** that adds complexity without matching Palantir's actual architecture. The SDK intentionally delegates caching responsibility to the application layer.

---

## Part 2: AIP Runtime validates the Kernel pattern

The AIP Logic Runtime operates on a **hybrid execution model**—neither purely serverless nor purely persistent. This validates Orion ODA's Kernel polling approach more than expected.

### The actual AIP execution model

AIP Logic uses a **Blocks architecture** where each block is an atomic unit of LLM instruction. Blocks chain linearly to create chain-of-thought workflows with **5-minute execution limits** in production. The critical architectural detail: **LLMs cannot directly access tools**. Instead, LLMs *request* tool usage, and AIP Logic marshals these calls within the invoking user's permissions.

```
User Request → AIP Logic Runtime → Block Execution → LLM API Call
                                           ↓
                         LLM requests tool use (Query/Function/Action)
                                           ↓
                  AIP Logic intercepts & executes with user permissions
                                           ↓
                              Results return to LLM context
```

### Compute Modules: The polling pattern is correct

Palantir's Compute Modules are containerized workloads with a key architectural requirement: **the entry point container must implement a client that forever polls for events to process**. This is not pure serverless invocation—it's a persistent polling pattern with horizontal scaling.

```
Compute Module
├── Replica 1 (polls for events)
├── Replica 2 (polls for events)
└── ... (scales based on load)
```

Palantir offers two modes:
- **Serverless Functions**: Ephemeral, on-demand, no local caching possible
- **Deployed Functions**: Persistent environment, local caching allowed, continuous compute costs

**Verdict on Kernel**: The OrionRuntime active polling pattern **aligns well** with Palantir's Compute Module architecture. The key refinement needed: implement tool call marshaling (intercept LLM requests → execute with permissions → return results) rather than direct execution.

---

## Part 3: Apollo uses YAML, not code—governance model mismatch

Apollo's architecture fundamentally differs from Orion ODA's SQLite-based ProposalRepository. Apollo uses **pure YAML** with a template substitution language, not Starlark or programmatic validation.

### The manifest.yml structure

```yaml
manifest-version: "1.0"
product-group: com.palantir.example
product-name: my-service
product-version: 1.0.0
product-type: service.v1

extensions:
  product-dependencies:
    - product-group: org.postgresql
      product-name: postgresql
      minimum-version: 9.3.6
      maximum-version: 9.6.x
      optional: false
  
  volumes-v2:
    my-volume:
      volume-type:
        durable-volume: {}
```

### Template substitution (not Starlark)

Apollo uses `{{ }}` syntax for runtime substitution:

```yaml
conf:
  security:
    key-file: '{{ ssl.pem_path }}'
  server:
    port: '{{ endpoints.definitions.my-endpoint.desired-port }}'
  client:
    auth-secret: '{{ secret("client-shared-secret") }}'
```

### Governance: Plan-based paradigm

Apollo's governance differs architecturally from a status workflow:

1. **Orchestration Engine** continuously evaluates possible Plans
2. **Change Requests (CRs)** created for all Environment modifications
3. **Constraint evaluation** happens at runtime, not in code
4. **Agents in Spoke environments** poll for and execute approved Plans
5. **Automatic rollback** Plans execute after failures

| Aspect | Apollo | Orion ProposalRepository |
|--------|--------|--------------------------|
| Config format | YAML with `{{ }}` templating | JSON/SQL schemas |
| Constraint language | Declarative YAML + runtime eval | Python methods |
| State storage | Distributed Hub + Spoke agents | Local SQLite |
| Approval workflow | Built-in CR system (DEV/STANDARD/FedRAMP) | Custom status enum |
| Rollout strategy | Release Channels + Canary promotion | Manual workflow |

**Verdict on ProposalRepository**: The SQLite status workflow (DRAFT → PENDING → APPROVED → EXECUTED) is a **reasonable simulation** but architecturally distant from Apollo's distributed, Plan-based paradigm. Apollo separates *what* (manifest/config) from *when* (constraints/plans).

---

## Part 4: The isomorphism table

| Orion ODA Component | Implemented As | Palantir Real Equivalent | Verdict |
|---------------------|----------------|--------------------------|---------|
| `ObjectManager` | Write-back cache class with TTL | `foundry.Client` (stateless REST wrapper) | **OVER-ENGINEERED** — SDK has no caching |
| `ActionType` | Python ABC with `execute()` | Ontology ActionType / `@OntologyEditFunction` | **ALIGNED** — correct abstraction |
| `ProposalRepository` | SQLite DB with status workflow | Apollo Plans + Change Requests | **CONCEPTUALLY VALID** — but wrong paradigm |
| `Kernel` | Active loop polling for proposals | Compute Module entry container (forever-poll) | **WELL-ALIGNED** — matches Palantir pattern |
| `OntologyObject` (Pydantic) | BaseModel with UUIDv4, version | ObjectType schema + `Osdk.Instance<T>` | **ALIGNED** — correct modeling approach |
| `submission_criteria` | Method returning bool | Submission Criteria conditions | **ALIGNED** — correct concept |
| `side_effects` | Method for notifications | Side Effects rules | **ALIGNED** — correct concept |
| `apply_edits` | Method applying changes | Rules (edit operations) | **ALIGNED** — correct concept |
| "Phonograph Pattern" | Custom write-back caching | No equivalent (SDK is stateless) | **MARKETING FLUFF** — invented terminology |

---

## Architecture diagram: Actual vs. implemented data flow

### Palantir's actual data flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER/APPLICATION                          │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                     AIP LOGIC RUNTIME                            │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐         │
│  │ Block 1 │ → │ Block 2 │ → │ Block N │ → │ Output  │         │
│  └────┬────┘   └────┬────┘   └────┬────┘   └─────────┘         │
│       ↓             ↓             ↓                              │
│  ┌─────────────────────────────────────┐                        │
│  │      TOOL MARSHALING LAYER          │                        │
│  │  (LLM requests → Permission-scoped  │                        │
│  │   execution → Results returned)     │                        │
│  └─────────────────────────────────────┘                        │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ONTOLOGY LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Query Objects│  │ Call Function│  │ Apply Action │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                 OBJECT STORAGE (Phonograph)                      │
│         (Server-side persistence, no client cache)               │
└─────────────────────────────────────────────────────────────────┘
```

### Orion ODA's implemented flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER/APPLICATION                          │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ObjectManager (UNNECESSARY)                   │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Write-back cache, version tracking, dirty flags  │ ← DELETE  │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                     KERNEL (ALIGNED)                             │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Active polling loop for approved proposals       │ ← KEEP    │
│  │ (Matches Compute Module forever-poll pattern)    │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│               ProposalRepository (PARTIAL MATCH)                 │
│  ┌──────────────────────────────────────────────────┐           │
│  │ SQLite status workflow simulates Apollo Plans    │ ← REFACTOR│
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Code correction requests

### DELETE: ObjectManager caching layer

The `scripts/ontology/manager.py` ObjectManager is over-engineering based on a misconception. Palantir's SDK is intentionally stateless.

```python
# DELETE this entire pattern:
class ObjectManager:
    def __init__(self):
        self._cache = {}           # ← DELETE
        self._dirty_objects = set() # ← DELETE
        self._version_map = {}      # ← DELETE
    
    def get(self, rid):
        if rid in self._cache:     # ← DELETE
            return self._cache[rid]
        # ...
```

**Replace with**: Direct SDK calls or SWR-style fetching wrapper if needed.

### ADD: Tool call marshaling layer

The Kernel should intercept and marshal tool calls rather than executing directly:

```python
# ADD this pattern:
class ToolMarshaler:
    def __init__(self, user_context):
        self.permissions = user_context.permissions
    
    async def execute_tool_request(self, tool_call):
        """LLM requests tool use → validate permissions → execute → return"""
        if not self._has_permission(tool_call.tool_name, self.permissions):
            raise PermissionDenied(f"User lacks permission for {tool_call.tool_name}")
        
        result = await self._execute_within_scope(tool_call)
        return result
```

### ADD: Stale-while-revalidate pattern (if caching needed)

If caching is truly necessary, implement SWR pattern instead of write-back:

```python
# ADD this pattern if caching is required:
class SWRCache:
    def __init__(self, ttl_seconds=60):
        self._cache = {}
        self._timestamps = {}
        self._ttl = ttl_seconds
    
    async def get(self, key, fetcher):
        """Return stale data immediately, revalidate in background"""
        if key in self._cache:
            data = self._cache[key]
            if self._is_stale(key):
                asyncio.create_task(self._revalidate(key, fetcher))
            return data
        return await self._fetch_and_cache(key, fetcher)
```

### RENAME: For accuracy

| Current Name | Rename To | Reason |
|--------------|-----------|--------|
| `Phonograph Pattern` | DELETE entirely | Marketing fluff—no Palantir equivalent |
| `ObjectManager` | `OntologyClient` or delete | Aligns with SDK naming |
| `Kernel` | `ComputeModule` | Matches Palantir terminology |
| `ProposalRepository` | `PlanStore` or `ChangeRequestStore` | Aligns with Apollo concepts |

### REFACTOR: ProposalRepository to Plan-based model

```python
# CURRENT (status workflow):
class ProposalRepository:
    def transition(self, proposal_id, new_status):
        # DRAFT → PENDING → APPROVED → EXECUTED

# REFACTORED (Plan-based):
class PlanStore:
    def create_plan(self, entity_changes, constraints):
        """Create a Plan with declarative constraints"""
        plan = Plan(
            changes=entity_changes,
            constraints=constraints,  # YAML-style constraints
            status="PENDING_CONSTRAINTS"
        )
        return plan
    
    def evaluate_constraints(self, plan):
        """Runtime constraint evaluation (Apollo pattern)"""
        for constraint in plan.constraints:
            if not constraint.is_satisfied():
                return False
        return True
```

---

## Final verdict

### Architectural accuracy score: **6/10**

The implementation demonstrates strong conceptual understanding but includes significant over-engineering and one major misconception about SDK architecture.

### Valid patterns implemented correctly

1. **Kernel polling pattern** — Matches Compute Module forever-poll architecture
2. **ActionType abstraction** — Correctly models Ontology ActionType concept
3. **OntologyObject Pydantic models** — Appropriate approach for ObjectType schemas
4. **Submission criteria / Side effects / Apply edits** — Correct conceptual mapping to Palantir's Action components
5. **Status workflow concept** — Valid simulation of governance, even if paradigm differs

### Anti-patterns and misconceptions

1. **"Phonograph Pattern" write-back caching** — Invented terminology for non-existent SDK feature. Both Python and TypeScript SDKs are stateless by design.
2. **ObjectManager complexity** — Adds identity tracking, dirty flags, and version management that the SDK intentionally omits.
3. **SQLite as state store** — Apollo uses distributed Hub + Spoke agents, not local persistence.
4. **Python validation rules** — Apollo uses declarative YAML constraints evaluated at runtime, not programmatic validation.
5. **Missing tool marshaling** — AIP Logic intercepts LLM tool requests and executes with permissions; current Kernel lacks this layer.

### Priority refactoring recommendations

1. **HIGH**: Delete ObjectManager caching layer entirely. Use direct SDK calls.
2. **HIGH**: Add tool call marshaling layer to Kernel for permission-scoped execution.
3. **MEDIUM**: Rename components to match Palantir terminology (Kernel → ComputeModule).
4. **MEDIUM**: Refactor ProposalRepository to Plan-based model with declarative constraints.
5. **LOW**: Consider adding real-time subscriptions if using TypeScript frontend.

### The marketing vs. engineering reality

| Claim | Reality |
|-------|---------|
| "Phonograph Pattern" | **Marketing fluff** — SDK has no caching; Phonograph is server-side storage |
| "Write-back optimization" | **Over-engineering** — SDK intentionally stateless |
| "Kernel execution model" | **Engineering reality** — Matches Compute Module polling pattern |
| "ActionType abstraction" | **Engineering reality** — Correct ontology modeling |
| "Governance workflow" | **Partial reality** — Status workflow is valid but Apollo uses Plans |

The core Kernel and ActionType patterns demonstrate genuine alignment with Palantir architecture. The ObjectManager caching layer should be deleted as it contradicts Palantir's intentional design choice to make SDKs stateless and delegate caching to the application layer.