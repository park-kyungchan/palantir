# Palantir FDE Interview Preparation Context

**Target Position:** Palantir Frontend Engineer (US)
**Candidate Background:** Mathematics Education B.A., AI/ML systems expert (LLMs, GraphRAG, Neo4j)
**Current Project:** "Universal Tutor" intelligent tutoring system
**Interview Focus:** React, TypeScript, Blueprint UI, data-dense visualization applications

**Complete Technology List (26 total):**
TIER 1: TypeScript, JavaScript ES6+, React, Blueprint UI Toolkit
TIER 2: Redux/Redux Toolkit, React Query, Sass/SCSS, CSS-in-JS, GraphQL, REST API
TIER 3: Webpack, Vite, Gradle, Jest, React Testing Library, Cypress/Playwright
TIER 4: Git Advanced, GitHub/PR, D3.js, Web Workers, WebSocket, Service Workers, Accessibility
TIER 5: Node.js, Java basics, Go basics

**Cross-Reference Instructions:**
When mentioning other technologies from this list, note compatibility and integration patterns.
Each research output will be consumed by an AI agent (Gemini 3.0 Pro) via markdown files.

**Upload this file with every Deep Research query in Gemini.**

---

## GROUP 4: Data Layer
**File Output:** `04_data_layer.md`

```
<goal>
Analyze **React Query**, **GraphQL**, and **REST API** integration patterns for frontend-backend data flow in enterprise data platforms.
</goal>

<context>
Research Group 4 of 8. Palantir explicitly uses GraphQL ("central to frontend development" per job postings) alongside REST (Foundry API). React Query handles server-state caching.

Dependencies: JavaScript/TypeScript (Group 1), React (Group 2)
Related: Redux (Group 2 - client state vs server state)
</context>

<content>
## REST API Fundamentals
1. **HTTP Methods** (GET/POST/PUT/DELETE, idempotency, status codes)
2. **Authentication** (OAuth 2.0, JWT - Foundry API uses OAuth 2.0)
3. **Error Handling** (retry strategies, exponential backoff)
4. **Performance** (pagination, caching headers, ETags)

## GraphQL Architecture
1. **Core Concepts** (schema, queries, mutations, subscriptions)
2. **Type System** (schema definition language, type generation)
3. **Client Libraries** (Apollo Client, urql, comparison)
4. **Performance** (query batching, caching, n+1 problem)
5. **Palantir Usage** (how GraphQL fits in Foundry architecture)

## React Query (TanStack Query)
1. **Server State Management** (vs client state in Redux)
2. **Core Hooks** (useQuery, useMutation, useInfiniteQuery)
3. **Caching Strategies** (stale-while-revalidate, invalidation)
4. **Optimistic Updates** (for responsive UIs)
5. **Integration** (with GraphQL, REST, WebSockets)

## Integration Patterns
1. **REST + React Query** (fetching, mutations, error boundaries)
2. **GraphQL + Apollo** (fragments, cache normalization)
3. **Hybrid Approach** (REST for legacy, GraphQL for new features)

## Enterprise Patterns
1. **Authentication Flow** (token refresh, interceptors)
2. **Real-time Data** (polling vs subscriptions vs WebSockets)
3. **Offline Support** (service workers, cache-first strategies)

## Comparison Matrix
| Feature | REST | GraphQL | Palantir Usage |
|---------|------|---------|----------------|
| Flexibility | Low | High | Both (Foundry REST + GraphQL) |
| ... | ... | ... | ... |

## Interview Q&A
Q: "How would you handle real-time data updates in a Palantir-style dashboard?"
A: [GraphQL subscriptions vs polling vs WebSockets analysis]
(15-20 questions)
</content>

<style>
2,500-3,000 words, code examples, architecture diagrams in text format
</style>

<sources>
- React Query official docs (tanstack.com)
- GraphQL official spec
- Apollo Client docs
- Palantir Foundry API documentation
- REST API best practices (2024-2025)
</sources>

<instructions>
- Rate 1-5: Learning Curve, Interview Frequency, Palantir Criticality, Depth Required
- Emphasize Palantir's dual REST/GraphQL approach, cross-reference Redux (client vs server state)
</instructions>
```
