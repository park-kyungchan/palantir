# Palantir AIP and Foundry Architecture: Implementation Deep Dive

Palantir's Foundry Ontology and AIP platform implement a **server-authoritative CQRS architecture** with explicit separation between read paths (Object Set Service), write paths (Funnel/Actions), and AI integration (AIP Logic blocks). This analysis validates and corrects baseline assumptions for mapping to the Orion ODA system, revealing key architectural divergences in caching strategy, versioning semantics, and function execution models.

## Technical errata: Corrections to baseline assumptions

Several baseline assumptions require correction based on implementation details discovered in official documentation and API specifications.

**Errata 1: OSDK does NOT implement write-back caching.** The Ontology SDK is a **thin, stateless client** that delegates all persistence to server-side Object Storage. Palantir recommends application-level caching using SWR (stale-while-revalidate) patterns rather than client-side write-back. This fundamentally differs from the Phonograph pattern with write-back caching in Orion ODA.

**Errata 2: AIP serialization uses TypeScript interfaces, not Pydantic-equivalent JSON schemas.** While schema-driven like Pydantic, AIP Logic marshals objects to string representations (`OBJECT_NAME property1 property2`) for LLM context windows, with explicit property selection required to manage token budgets. There is no native `model_dump(mode='json')` equivalent—objects must pass through the OSDK's TypeScript type system.

**Errata 3: Apollo uses YAML with custom substitution syntax, not Starlark.** The constraint language is standard YAML with `{{ }}` template substitution and Go template support for complex files. This is simpler than anticipated but includes powerful primitives for dependency management and rollout orchestration.

**Errata 4: Functions are triggered by platform applications, not HTTP/events.** Foundry Functions execute on-demand when Workshop variables update, Actions are applied, or Slate documents call backend services—not through traditional REST endpoints or event queues.

## AIP Logic internals: LLM-Ontology data marshaling

The AIP Runtime implements a **mediated tool execution model** where LLMs never directly access Ontology tools. Instead, LLMs generate structured tool call requests that the AIP Logic Runtime intercepts, validates against user permissions, executes, and returns serialized results to the context window.

```typescript
// AIP tool execution flow (conceptual)
[LLM Context] → Tool Request (structured/prompted) 
    → [AIP Runtime] validates permissions, executes tool
    → [Ontology/Function] returns data
    → [AIP Runtime] serializes response, counts tokens
    → [LLM Context] receives stringified result
```

**Two tool calling modes** coexist in the platform. **Prompted tool calling** inserts instructions into the prompt with a custom DIY function calling syntax (model-agnostic but sequential). **Native tool calling** uses built-in model capabilities for parallel execution and better token efficiency, but only works with select Palantir-provided models.

Token management is critical: each block maintains its own context window with token limits. Property selection directly impacts token usage since objects serialize to strings like `EMPLOYEE firstName lastName department`. The security model enforces **permission-scoped execution**—all tool calls run within the invoking user's permissions, with optional project-scoped elevation for imported resources.

## OSDK runtime behavior: Server-authoritative architecture

OSDK implements a fundamentally different philosophy than write-back caching. The SDK is stateless, making fresh requests for each operation and relying entirely on server-side Object Storage for consistency and versioning.

```typescript
// OSDK recommended caching pattern: SWR at application level
const fetcher = useCallback(async () => {
  return await client(MyObject)
    .withProperties({ /* runtime-derived aggregations */ })
    .fetchPage();
}, [client]);

const { data, error, isLoading } = useSWR('cache-key', fetcher);
```

**Link traversal optimization** uses the `pivotTo` method to push aggregations server-side:

```typescript
client(Project).withProperties({
  "taskCount": (baseSet) => baseSet.pivotTo("task").aggregate("$count"),
  "completedCount": (baseSet) => baseSet.pivotTo("task")
    .where({ "status": { $eq: "COMPLETED" } }).aggregate("$count"),
}).fetchPage();
```

**Cache invalidation** relies on real-time subscriptions with an `onOutOfDate` callback that signals when the client should reload the entire object set—there is no incremental invalidation protocol.

For **optimistic locking**, Object Storage V2 performs version checks only on objects directly used to generate edits, reducing `StaleObject` conflicts compared to V1's more aggressive checking. This provides weaker guarantees but better throughput. Conflict resolution follows a simple rule: **user edits always win** over datasource updates for edited properties.

## Apollo constraint language specifications

Apollo configurations use **YAML with a substitution templating language**. The `{{ }}` syntax supports variable interpolation, secret references, discovery lookups, and volume paths.

```yaml
# configuration.yml example
replication:
  desired: 3
resources:
  requests: { cpu: 8, memory: 10Gi }
  limits: { cpu: 16, memory: 10Gi }

endpoints:
  definitions:
    my-endpoint:
      desired-port: 8080
      path: /api

conf:
  config:
    server:
      port: '{{endpoints.definitions.my-endpoint.desired-port}}'
      tls:
        key: '{{ssl.pem_path}}'
        cert: '{{ssl.cert_path}}'
    database:
      uri: '{{discovered.database-uris}}'
    auth:
      secret: '{{secret("oauth-secret")}}'
```

**Product dependencies** use version matchers with semantic version wildcards:

```yaml
# manifest.yml extensions
extensions:
  product-dependencies:
    - product-group: com.palantir.infra
      product-name: database
      minimum-version: 2.0.0
      maximum-version: 2.x.x  # Matches 2.0.0-2.999.999
```

Apollo differentiates from Helm through **constraint-based orchestration**: the Orchestration Engine evaluates maintenance windows, dependencies, health requirements, and suppression windows before issuing execution Plans. Apollo wraps Helm as a product type (`helm.v1`) rather than replacing it, adding immutable versioning, multi-environment management, and automatic recall across environments.

## Functions execution model and ActionType semantics

Foundry Functions operate as **platform-native serverless** with application-driven triggering rather than HTTP endpoints. Functions execute when Workshop variables update, Actions are applied, or Slate documents request backend computation.

**TypeScript decorators** define function capabilities and Ontology interactions:

```typescript
import { Function, OntologyEditFunction, Edits, Query } from "@foundry/functions-api";
import { Employee, Ticket } from "@foundry/ontology-api";

export class TicketFunctions {
  // Read-only function
  @Function()
  public calculatePriority(ticket: Ticket): Integer {
    return ticket.severity * ticket.customerTier;
  }

  // Ontology edit function - declares provenance
  @Edits(Employee, Ticket)
  @OntologyEditFunction()
  public assignTicket(ticket: Ticket, assignee: Employee): void {
    ticket.status = "Assigned";
    ticket.assignedTo = assignee;
    assignee.activeTickets.add(ticket);
  }

  // API-exposed query
  @Query({ apiName: "getOpenTickets" })
  public async getOpenTickets(): Promise<ObjectSet<Ticket>> {
    return Objects.search().ticket().filter(t => t.status.exactMatch("Open"));
  }
}
```

**Python equivalent** uses the `@function` decorator with edit declarations:

```python
from functions.api import function, OntologyEdit
from ontology_sdk import FoundryClient
from ontology_sdk.ontology.objects import Employee, Ticket

@function(edits=[Employee, Ticket])
def assign_ticket(ticket: Ticket, assignee: Employee) -> list[OntologyEdit]:
    ontology_edits = FoundryClient().ontology.edits()
    editable_ticket = ontology_edits.objects.Ticket.edit(ticket)
    editable_ticket.status = "Assigned"
    editable_employee = ontology_edits.objects.Employee.edit(assignee)
    editable_employee.active_tickets.add(editable_ticket)
    return ontology_edits.get_edits()
```

**Critical constraint**: Edit functions must be configured as ActionTypes to persist changes. Running directly only returns proposed edits without committing them.

## Ontology architecture: ObjectTypes, Links, and Actions

ObjectTypes define entity schemas with typed properties, primary keys, and metadata. Properties support base types (String, Integer, Date, Timestamp) plus specialized types (Vector for embeddings, Geopoint, Attachment, Cipher text for encrypted values).

```json
{
  "apiName": "ticket",
  "primaryKey": ["ticketId"],
  "properties": {
    "ticketId": { "baseType": "String" },
    "title": { "baseType": "String" },
    "priority": { "baseType": "String" },
    "status": { "baseType": "String" },
    "createdAt": { "baseType": "Timestamp" }
  },
  "rid": "ri.ontology.main.object-type.abc123"
}
```

**LinkTypes** define relationships with explicit cardinality. Foreign key links (1:1, 1:M, M:1) use property references; many-to-many requires join table datasets.

```typescript
// Link traversal in TypeScript
const manager: Employee | undefined = await employee.manager.get();      // SingleLink
const reports: Employee[] = await employee.directReports.all();           // MultiLink
const reportSet: ObjectSet<Employee> = employeeSet.searchAroundToEmployee(); // Pivot
```

**ActionTypes** implement the Command pattern with four lifecycle components: **Parameters** (inputs), **Submission Criteria** (validation guards), **Rules** (edit operations), and **Side Effects** (notifications, webhooks). This maps closely to the Orion ODA ActionType ABC but with declarative configuration rather than code inheritance.

## Isomorphism table: Orion ODA to Palantir mapping

| Orion ODA Pattern | Palantir Equivalent | Implementation Notes |
|-------------------|---------------------|---------------------|
| `OntologyObject` (Pydantic base) | `ObjectType` schema + `Osdk.Instance<T>` | Palantir uses JSON schema definitions; runtime instances via `Osdk.Instance<T>` wrapper. No Pydantic—TypeScript interfaces generated from metadata. |
| `UUIDv4` primary key | `primaryKey` property | Palantir supports composite keys and any property type. RID (`ri.ontology...`) is the true unique identifier, distinct from primary key. |
| `version` for optimistic locking | Offset tracking (OSv2) | No explicit version field. OSv2 tracks offsets per object type. Version checks only on edit-generating objects, not all loaded objects. |
| `ActionType` ABC | `ActionType` definition + `@OntologyEditFunction` | Declarative YAML/UI config for simple cases; `@OntologyEditFunction` decorator for code-based rules. |
| `submission_criteria` method | **Submission Criteria** conditions | Declarative conditions: user groups, parameter validation, property comparisons with AND/OR/NOT operators. |
| `side_effects` method | **Side Effects** rules | Declarative notifications and webhooks, executed post-commit. Cannot contain arbitrary code. |
| `apply_edits` method | **Rules** (edit operations) | Create/Modify/Delete Object rules or Function Rule pointing to `@OntologyEditFunction`. Returns `void`, edits captured by infrastructure. |
| `ObjectManager` (Phonograph) | **Object Set Service + Funnel** | Read through OSS, write through Actions→Funnel. No client-side caching—server-authoritative. |
| Write-Back Caching | **SWR at app level** | OSDK is stateless. Caching delegated to application layer via SWR/React Query. |
| Optimistic Locking | **StaleObject errors** | OSv2 checks versions on edit-generating objects only. Conflicts throw `StaleObject`; client retries. |
| Repository pattern | **OSS + Actions** | OSS serves read queries; Actions encapsulate writes. Explicit CQRS separation. |
| Redux actions | **ActionType parameters** | Parameters transport values; submission criteria act as middleware guards. |
| Redux reducers | **Rules (edit logic)** | Pure transformation via create/modify/delete rules or Function rules. |
| Redux selectors | **Object Set filters + aggregations** | Server-side filtering and aggregation via OSS queries and `withProperties`. |

## Code generation pipeline and type safety

OSDK generates type-safe bindings from Ontology metadata through the Developer Console. The 2.0 pipeline introduces **lazy loading** (only require what's used), **linear scaling** (with ontology shape, not size), and **client decoupling** (separate from generated code).

```typescript
// Generated SDK structure
@my-osdk-lib/sdk/
├── ontology/
│   ├── objects/
│   │   └── Ticket.ts          // Osdk.Instance<Ticket> type
│   ├── actions/
│   │   └── AssignTicket.ts    // Action parameter types
│   └── queries/
│       └── GetOpenTickets.ts  // Query return types
└── $ontologyRid.ts            // Ontology identifier

// Usage with full type safety
import { Ticket } from "@my-osdk-lib/sdk";
import { createClient, Osdk } from "@osdk/client";

const client = createClient(stackUrl, ontologyRid, auth);
const result: PageResult<Osdk.Instance<Ticket>> = 
  await client(Ticket).fetchPage({ $pageSize: 50 });

// Type-safe property access
result.data.forEach(ticket => {
  console.log(ticket.title);     // string
  console.log(ticket.priority);  // string  
  console.log(ticket.createdAt); // Timestamp
});
```

**Python SDK** follows similar patterns with generated stubs from Ontology metadata, using `FoundryClient` for object access and edit operations.

## Architectural implications for code mapping

The mapping from Orion ODA to Palantir patterns requires several adaptations:

**Caching architecture shift**: Replace write-back caching with server-authoritative patterns. Use OSDK subscriptions for real-time updates and implement SWR at the application boundary. The `onOutOfDate` callback signals full reload requirements.

**Version field removal**: Orion ODA's explicit `version` field doesn't map directly. Instead, rely on Palantir's offset tracking and handle `StaleObject` errors with retry logic. For optimistic UI updates, track local "pending" state separately.

**ActionType refactoring**: Convert `submission_criteria` methods to declarative condition configurations. Side effects become separate rule definitions. The `apply_edits` method maps to `@OntologyEditFunction` but must return `void` with edits captured implicitly.

**Primary key semantics**: Palantir distinguishes between primary key (business identifier) and RID (system identifier). Code expecting UUIDv4 equivalence should use `$primaryKey` for business logic but track `__rid` for system operations.

The fundamental pattern shift is from **client-centric state management** (Orion ODA with write-back caching) to **server-authoritative CQRS** (Palantir with OSS/Funnel separation). This affects error handling, conflict resolution, and real-time synchronization strategies throughout the codebase.