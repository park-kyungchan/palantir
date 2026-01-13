# Palantir FDE Learning: Orion System Architecture (ODA)
... [Content from Step 169 but OPTIMIZED with Step 174/178 changes] ...

## 4. Palantir Context (Code-Level)

### 4.1 OSDK Entry Point (TypeScript)
The Orion Kernel's initialization mirrors the **Foundry Ontology SDK (OSDK)** client creation.

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
```

### 4.2 AIP Logic & System Prompts
In **Palantir AIP Logic**, the "System Prompt" is configured in the **"Use LLM"** block.

```json
{
  "type": "llm_inference",
  "system_prompt": "You are a Flight Control Agent...",
  "tools": ["query_ontology", "call_function"],
  "temperature": 0.0
}
```

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
```
