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

## GROUP 2: React Ecosystem Core
**File Output:** `02_react_ecosystem.md`

```
<goal>
Analyze **React 18+**, **Blueprint UI Toolkit**, and **Redux/Redux Toolkit** (including Palantir's Redoodle) for enterprise data-dense applications, focusing on architectural patterns used in Palantir Foundry.
</goal>

<context>
Research Group 2 of 8. This is Palantir's core UI stack - Blueprint is explicitly mentioned in job postings, and Redoodle is Palantir's own Redux-TypeScript integration library. The candidate must demonstrate deep mastery here as interviews will directly test these frameworks.

Dependencies: Requires JavaScript/TypeScript (Group 1)
Related: Sass/SCSS (Group 3), GraphQL/REST (Group 4), Testing (Group 5)
</context>

<content>
## React 18+ Architecture
1. **Core Concepts** (components, hooks, reconciliation algorithm, fiber architecture)
2. **Modern Patterns** (Server Components, Suspense, Transitions, useId, useDeferredValue)
3. **State Management** (useState, useReducer, Context API, when to use what)
4. **Performance** (memoization, lazy loading, code splitting, React DevTools profiling)
5. **Concurrent Features** (startTransition, useDeferredValue for data-dense UIs)

## Blueprint UI Toolkit Deep Dive
1. **Architecture** (component design philosophy, accessibility-first approach)
2. **Core Components** (Table, Tree, Select, DatePicker, Forms for data-dense UIs)
3. **Data Handling** (large datasets in Table, virtualization patterns)
4. **Theming** (dark mode, custom themes, CSS variables)
5. **TypeScript Integration** (ITreeNode<T>, ITableProps<T> generic patterns)
6. **Palantir Patterns** (official examples from Blueprint docs, Foundry UI patterns)

## Redux Toolkit & Redoodle
1. **Redux Fundamentals** (unidirectional data flow, reducers, actions, store)
2. **Redux Toolkit** (createSlice, createAsyncThunk, RTK Query basics)
3. **Redoodle** (Palantir's typed actions, compound actions, immutable utilities)
4. **When to Use** (Redux vs Context vs React Query - decision matrix)
5. **Performance** (selector memoization, normalized state shape)

## Integration Patterns
1. **React + TypeScript** (FC<Props> patterns, generic components, type inference)
2. **React + Redux** (useSelector typing, action creator patterns)
3. **Blueprint + Redux** (form state management, table data binding)

## Enterprise Architecture
1. **Component Organization** (atomic design, feature-based folders)
2. **Code Splitting** (React.lazy, Suspense boundaries for large apps)
3. **Error Boundaries** (graceful degradation in data-intensive dashboards)

## Design Philosophy
1. **React's Declarative Paradigm** (Dan Abramov quotes on reconciliation)
2. **Blueprint's Data-Dense Focus** (quotes from Blueprint docs on desktop-first design)
3. **Redux Design Principles** (predictability, time-travel debugging)

## Comparison Matrix
| Aspect | React Context | Redux Toolkit | Redoodle | Palantir Choice |
|--------|---------------|---------------|----------|-----------------|
| Type Safety | Weak | Good | Excellent | Redoodle preferred |
| ... | ... | ... | ... | ... |

## Common Pitfalls
- **Pitfall:** Re-renders causing performance issues in large Blueprint Tables
  - **Solution:** React.memo, useMemo for expensive computations, virtualization
  - **Interview Relevance:** High (Palantir's data-dense focus)
(10-15 pitfalls)

## Interview Q&A
Q: "How would you optimize a Blueprint Table rendering 10,000 rows?"
A: [Detailed answer with virtualization, windowing, memoization strategies]
(15-20 questions)
</content>

<style>
Same as Group 1: Markdown headers, 2-4 sentence paragraphs, code blocks, tables, 2,500-3,000 words, bracketed citations
</style>

<sources>
- React 18 official docs (react.dev)
- Blueprint UI official docs and GitHub (github.com/palantir/blueprint)
- Redoodle GitHub (github.com/palantir/redoodle)
- Redux Toolkit official docs
- Palantir tech blog posts on frontend architecture
- StackOverflow (2024-2025)
</sources>

<instructions>
- Rate 1-5: Learning Curve, Interview Frequency, Palantir Criticality, Depth Required
- Include Blueprint-specific examples (Table, Tree components)
- Highlight Redoodle advantages over vanilla Redux
- Cross-reference with TypeScript patterns from Group 1
- Test all code examples
</instructions>
```
