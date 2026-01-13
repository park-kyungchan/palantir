# Palantir OSDK 2.0 & Functions v2 Standards

## Overview
Based on deep research (2026-01-04), the Palantir FDE Learning system and ODA follow the modern OSDK 2.0 standards for client initialization and object functions.

## 1. OSDK 2.0 Client Initialization
Legacy OSDK 1.x required full ontology generation (tight coupling). OSDK 2.0 uses "Lazy Loading" and scales linearly with ontology metadata.

**Modern Initialization Pattern (TypeScript):**
```typescript
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
```

## 2. Functions v2 (TypeScript)
Functions v2 (Node.js runtime) provides first-class OSDK support and moves away from legacy decorators like `@FoundryFunction`.

**Modern Function Pattern:**
```typescript
import { Function, Integer } from "@foundry/functions-api";
import { Ticket } from "@foundry/ontology-api";

/**
 * Modern Functions v2 prefer the export default syntax.
 */
export default async function upgradeTicket(ticket: Ticket): Promise<void> {
    if (ticket.status === 'economy') {
        ticket.status = 'business'; // Mutation via Ontology Edit
    }
}
```

## 3. Key Advantages
- **Lazy Loading**: Only necessary components are loaded when used.
- **Separation of Concerns**: Client is separated from generated code, allowing hotfixes without full SDK regeneration.
- **Type-Safety**: Strong ergonomics derived from the ontology subset relevant to the application.
