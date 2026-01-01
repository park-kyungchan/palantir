---
domain: osdk
difficulty: beginner
tags: osdk, typescript, sdk, client, foundry
---
# OSDK TypeScript Mastery

## OVERVIEW
The Ontology Software Development Kit (OSDK) is Palantir's primary client library for interacting with Foundry's Ontology from external applications. It provides type-safe TypeScript/JavaScript bindings for Objects, Actions, and Queries defined in your Ontology.

Key capabilities:
- **Type-Safe Client**: Auto-generated TypeScript types from your Ontology schema
- **Object Operations**: CRUD operations on Ontology Objects
- **Action Execution**: Invoke Ontology Actions with validated parameters
- **Query Support**: Execute Ontology Queries with proper typing
- **Real-time Subscriptions**: Subscribe to Object changes via WebSockets

The OSDK follows a thin-client architecture where the client is a lightweight wrapper around Foundry's REST APIs, with all business logic residing server-side in the Ontology definition.

## PREREQUISITES
Before working with OSDK:
1. **Foundry Access**: Active Foundry stack with Ontology defined
2. **TypeScript Knowledge**: Intermediate TypeScript/JavaScript skills
3. **OAuth Understanding**: Familiarity with OAuth 2.0 PKCE flow
4. **Node.js Environment**: Node.js 18+ with npm/yarn

Recommended prior learning:
- Foundry Platform Essentials (KB-01)
- Ontology Design Patterns (KB-03)

## CORE_CONTENT

### Client Initialization
```typescript
import { Client } from "@osdk/client";
import { createClient } from "@osdk/client";

// Create authenticated client
const client = createClient({
  baseUrl: "https://your-stack.palantirfoundry.com",
  ontologyRid: "ri.ontology.main.ontology.xxx",
  auth: async () => {
    // OAuth token provider
    return accessToken;
  }
});
```

### Object Operations
```typescript
import { Employee } from "@your-package/sdk";

// Fetch single object by primary key
const employee = await client(Employee).fetchOne("emp-123");
console.log(employee.fullName);

// Query objects with filters
const activeEmployees = await client(Employee)
  .where({ isActive: true })
  .orderBy(e => e.startDate.desc())
  .take(100);

// Update object properties
await client(Employee).update("emp-123", {
  department: "Engineering"
});
```

### Action Execution
```typescript
import { PromoteEmployee } from "@your-package/sdk";

// Execute action with parameters
const result = await client(PromoteEmployee).apply({
  employeeId: "emp-123",
  newTitle: "Senior Engineer",
  effectiveDate: new Date()
});
```

### Type Generation
OSDK types are auto-generated from your Ontology:
1. Define Object Types in Foundry
2. Run `npx @osdk/cli generate`
3. Import generated types in your application

## EXAMPLES

### React Application Integration
```typescript
// hooks/useEmployee.ts
import { useQuery } from "@tanstack/react-query";
import { Employee } from "@your-package/sdk";
import { client } from "./foundryClient";

export function useEmployee(id: string) {
  return useQuery({
    queryKey: ["employee", id],
    queryFn: () => client(Employee).fetchOne(id),
  });
}
```

### Server-Side Usage (Node.js)
```typescript
// services/employeeService.ts
import { client } from "./foundryClient";
import { Employee, CreateEmployee } from "@your-package/sdk";

export async function createEmployee(data: EmployeeInput) {
  const result = await client(CreateEmployee).apply({
    fullName: data.name,
    email: data.email,
    department: data.department,
  });
  return result.createdEmployee;
}
```

## COMMON_PITFALLS

1. **Token Expiration**: OSDK doesn't auto-refresh tokens; implement refresh logic
2. **Missing Object RID**: Always include `$objectRid` when needed for updates
3. **Sync vs Async**: All OSDK operations are async; always await them
4. **Rate Limiting**: Batch operations when possible to avoid 429 errors
5. **Type Mismatches**: Regenerate types after Ontology changes

## BEST_PRACTICES

1. **Centralize Client**: Create a single client instance per application
2. **Error Handling**: Wrap OSDK calls in try-catch with specific error types
3. **Pagination**: Always paginate large result sets
4. **Caching**: Use React Query or similar for client-side caching
5. **Type Safety**: Never use `any`; leverage generated types

## REFERENCES
- [Palantir OSDK Documentation](https://www.palantir.com/docs/foundry/ontology-sdk/)
- [palantir/osdk-ts GitHub](https://github.com/palantir/osdk-ts)
- [OSDK API Reference](https://www.palantir.com/docs/foundry/api/osdk/)
- Foundry Developer Console (in-stack documentation)
