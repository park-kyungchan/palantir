# Palantir FDE Deep Research Prompts
*8 Optimized Research Groups for Gemini Deep Research*

---

## Research Context (Include in ALL prompts)

**Upload this context file with every Deep Research query:**

```markdown
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
```

---

## GROUP 1: Language Foundation
**File Output:** `01_language_foundation.md`

```
<goal>
Conduct comprehensive technical analysis of **JavaScript ES6+** and **TypeScript** for enterprise frontend development, specifically evaluating their application in large-scale data visualization platforms like Palantir Foundry.
</goal>

<context>
This is Research Group 1 of 8 for Palantir Frontend Engineer interview preparation. These languages form the absolute foundation - every other technology in this stack depends on them. The candidate has strong mathematical and AI/ML background but needs interview-ready depth on language internals, type systems, and Palantir-specific usage patterns.

Related technologies in this analysis: React (TypeScript-based), Blueprint UI (87.9% TypeScript), Redux Toolkit (TS integration), all build tools.
</context>

<content>
Cover these sections in order:

## JavaScript ES6+ Deep Dive
1. **Core Language Mechanics** (closures, prototypes, event loop, microtask queue)
2. **Async Patterns** (Promises, async/await, generators, async iteration)
3. **Modern Syntax** (destructuring, spread/rest, optional chaining, nullish coalescing)
4. **Memory & Performance** (garbage collection, WeakMap/WeakSet, performance optimization)
5. **Common Interview Patterns** (polyfills for map/reduce/filter/bind/Promise.all)

## TypeScript Architecture
1. **Type System Fundamentals** (structural typing vs nominal, type inference, generics)
2. **Advanced Types** (conditional types, mapped types, template literal types, utility types)
3. **Integration Patterns** (with React, Redux, GraphQL codegen)
4. **Palantir Usage** (Blueprint's type patterns, OSDK type safety requirements)
5. **TypeScript 5.x Features** (const type parameters, satisfies operator, decorators)

## Enterprise Patterns
1. **Large-Scale Architecture** (module systems, dependency injection, monorepo strategies)
2. **Error Handling** (custom error types, discriminated unions for error states)
3. **Performance at Scale** (tree shaking, code splitting, lazy loading)
4. **Migration Strategies** (JS to TS conversion patterns)

## Design Philosophy & Evolution
1. **JavaScript Evolution** (TC39 process, stage 3/4 proposals for 2024-2025)
2. **TypeScript Design Goals** (Anders Hejlsberg quotes on structural typing, gradual typing)
3. **Palantir's Approach** ("Millions of lines of TypeScript" - architectural decisions)

## Comparison Matrix
| Feature | JavaScript ES6+ | TypeScript | Palantir Usage |
|---------|-----------------|------------|----------------|
| Type Safety | Runtime only | Compile-time | Critical for Blueprint/OSDK |
| Tooling | Limited | Excellent | Required (Blueprint 87.9% TS) |
| ... | ... | ... | ... |

## Common Pitfalls Database
- **Pitfall:** `this` binding confusion
  - **Solution:** Arrow functions, explicit binding
  - **Interview Relevance:** High (debugging questions)
- (Include 10-15 common pitfalls with solutions)

## Interview-Ready Q&A Templates
Q: "Explain TypeScript's structural type system"
A: [Provide detailed, interview-ready answer with code examples]
(Include 15-20 common interview questions)
</content>

<style>
- Use markdown headers (##, ###)
- Keep paragraphs to 2-4 sentences
- Include code blocks for all syntax examples (use ```typescript and ```javascript)
- Use comparison tables for feature matrices
- Target 2,500-3,000 words
- Use bracketed citations [1], [2] with numbered reference list
</style>

<sources>
Prioritize 2024-2025 sources:
- Official TypeScript documentation (v5.x)
- TC39 proposals (stage 3-4)
- Palantir Blueprint GitHub repository (TypeScript patterns)
- StackOverflow discussions (2024-2025)
- Anders Hejlsberg interviews/talks
- Dan Abramov's blog (JavaScript fundamentals)
Avoid: Pre-2023 tutorials, generic bootcamp materials
Include version numbers for all claims
</sources>

<instructions>
- Rate 1-5: Learning Curve, Interview Frequency, Palantir Criticality, Depth Required
- Flag conflicting information between sources
- Include "Universal Concepts" section extracting language-agnostic principles
- Conclude with "Palantir Integration Notes" on how these languages enable Blueprint/Foundry
- Test all code examples for correctness
</instructions>
```

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

---

## GROUP 3: Styling Systems
**File Output:** `03_styling_systems.md`

```
<goal>
Evaluate **Sass/SCSS** and **CSS-in-JS** approaches for enterprise frontend styling, with focus on Blueprint's Sass-based architecture.
</goal>

<context>
Research Group 3 of 8. Blueprint uses Sass exclusively - understanding SCSS is critical for customizing Blueprint themes. CSS-in-JS represents the alternative paradigm for architectural discussions.

Dependencies: CSS fundamentals (assumed)
Related: React (Group 2), Blueprint (Group 2)
</context>

<content>
## Sass/SCSS Fundamentals
1. **Core Features** (variables, nesting, mixins, functions, @use/@forward)
2. **Blueprint's SCSS Architecture** (theming system, component styles, overrides)
3. **Build Integration** (webpack sass-loader, Vite SCSS support)
4. **Performance** (compilation optimization, source maps)

## CSS-in-JS Landscape
1. **Popular Libraries** (styled-components, Emotion, CSS Modules)
2. **Design Philosophy** (component-scoped styles, dynamic theming)
3. **Tradeoffs** (runtime cost vs DX, SSR considerations)

## Comparison & Palantir Context
| Aspect | Sass/SCSS | CSS-in-JS | Blueprint Choice |
|--------|-----------|-----------|------------------|
| Performance | Compile-time | Runtime | Sass (performance critical) |
| ... | ... | ... | ... |

## Enterprise Patterns
1. **Design Systems** (token-based theming, CSS variables)
2. **Responsive Design** (breakpoints, mobile-first vs desktop-first)
3. **Accessibility** (WCAG 2.1 AA, focus states, high contrast)

## Interview Q&A
(10-15 styling-focused questions)
</content>

<style>
Same format as previous groups, 1,500-2,000 words (lighter topic)
</style>

<sources>
- Sass official docs
- Blueprint theming documentation
- styled-components docs
- Palantir design system references
</sources>

<instructions>
Rate 1-5, emphasize Blueprint SCSS patterns, cross-reference React integration
</instructions>
```

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
Rate 1-5, emphasize Palantir's dual REST/GraphQL approach, cross-reference Redux (client vs server state)
</instructions>
```

---

## GROUP 5: Testing Pyramid
**File Output:** `05_testing_pyramid.md`

```
<goal>
Master **Jest**, **React Testing Library**, and **Cypress/Playwright** for comprehensive frontend testing strategies in enterprise applications.
</goal>

<context>
Research Group 5 of 8. Testing is critical for Palantir's re-engineering interviews (debugging buggy code) and demonstrates senior-level thinking. These tools form a natural hierarchy: unit → component → E2E.

Dependencies: JavaScript/TypeScript (Group 1), React (Group 2)
Related: All previous groups (need to test them)
</context>

<content>
## Jest Fundamentals
1. **Core Concepts** (test runners, matchers, mocks, spies, coverage)
2. **Configuration** (jest.config.js, setup files, transform)
3. **Advanced Patterns** (snapshot testing, timer mocks, module mocks)
4. **TypeScript Integration** (ts-jest, type-safe mocks)

## React Testing Library
1. **Testing Philosophy** (user-centric queries, accessibility testing)
2. **Core APIs** (render, screen, fireEvent, waitFor, user-event)
3. **Best Practices** (avoid implementation details, test user behavior)
4. **Blueprint Component Testing** (complex Table, Form testing strategies)

## Cypress vs Playwright
1. **Cypress** (architecture, commands, custom commands, fixtures)
2. **Playwright** (cross-browser, parallelization, network interception)
3. **Comparison** (Cypress vs Playwright for enterprise E2E)
4. **CI/CD Integration** (GitHub Actions, visual regression)

## Testing Strategies
1. **Testing Pyramid** (70% unit, 20% integration, 10% E2E)
2. **TDD Workflow** (red-green-refactor for interview live coding)
3. **Coverage Metrics** (meaningful coverage vs 100% coverage)

## Enterprise Patterns
1. **Test Data Management** (factories, fixtures, test databases)
2. **Flaky Test Prevention** (deterministic tests, proper waits)
3. **Performance Testing** (React DevTools Profiler in tests)

## Palantir Context
1. **Debugging Interview Prep** (systematic bug-finding approach)
2. **Large Codebase Testing** (test organization, shared utilities)

## Interview Q&A
Q: "How would you test a Blueprint Table with 10,000 rows?"
A: [Unit test data logic, RTL test rendering + virtualization, E2E test user interactions]
(15-20 testing questions)
</content>

<style>
2,500-3,000 words, test code examples, decision matrices
</style>

<sources>
- Jest official docs
- React Testing Library docs
- Cypress docs
- Playwright docs
- Kent C. Dodds blog (testing best practices)
- Palantir's testing philosophy (from blog/GitHub)
</sources>

<instructions>
Rate 1-5, include debugging strategies for Palantir re-engineering interviews
</instructions>
```

---

## GROUP 6: Build Tooling
**File Output:** `06_build_tooling.md`

```
<goal>
Understand **Webpack**, **Vite**, and **Gradle** for enterprise frontend build optimization and Java backend context.
</goal>

<context>
Research Group 6 of 8. Webpack is explicitly mentioned in Palantir job postings. Vite represents modern alternative. Gradle handles JVM builds for Palantir's Java backends.

Dependencies: JavaScript/TypeScript (Group 1)
Related: All frontend code needs building
</context>

<content>
## Webpack Architecture
1. **Core Concepts** (entry, output, loaders, plugins, mode)
2. **Configuration** (webpack.config.js, multi-entry, code splitting)
3. **Optimization** (tree shaking, minification, bundle analysis)
4. **Blueprint Usage** (webpack-build-scripts from Blueprint repo)
5. **Performance** (build time optimization, caching)

## Vite Modern Approach
1. **Architecture** (ESM-based dev server, Rollup for production)
2. **Advantages** (instant HMR, fast cold start)
3. **Migration** (Webpack to Vite for existing projects)
4. **Use Cases** (when to use Vite vs Webpack)

## Gradle (Java Context)
1. **JVM Build System** (tasks, dependencies, plugins)
2. **Palantir Backend** (Java microservices, Gradle in job postings)
3. **Frontend Relevance** (full-stack understanding for system design)

## Comparison Matrix
| Aspect | Webpack | Vite | Palantir Usage |
|--------|---------|------|----------------|
| Dev Speed | Slow | Fast | Webpack (enterprise stability) |
| ... | ... | ... | ... |

## Enterprise Patterns
1. **Monorepo Builds** (Nx, Turborepo integration)
2. **CI/CD Optimization** (incremental builds, caching)
3. **Production Optimization** (chunk splitting strategies)

## Interview Q&A
Q: "How would you optimize Webpack build time for a large application?"
A: [Caching, parallelization, tree shaking, bundle analysis strategies]
(10-15 questions)
</content>

<style>
1,500-2,000 words (awareness-level topic)
</style>

<sources>
- Webpack official docs
- Vite official docs
- Gradle docs
- Palantir job postings (build tool mentions)
- Blueprint webpack-build-scripts GitHub
</sources>

<instructions>
Rate 1-5, emphasize Webpack for Palantir alignment, lighter coverage on Gradle
</instructions>
```

---

## GROUP 7: Version Control & Collaboration
**File Output:** `07_version_control.md`

```
<goal>
Master **Git Advanced** and **GitHub/PR workflows** for enterprise collaboration and code review practices.
</goal>

<context>
Research Group 7 of 8. Version control proficiency differentiates senior candidates. Palantir behavioral interviews probe collaboration and code review practices.

Dependencies: None (standalone skill)
Related: All code needs version control
</context>

<content>
## Git Advanced Techniques
1. **Core Operations** (rebase, cherry-pick, bisect, reflog)
2. **Branch Strategies** (Git Flow, trunk-based, feature flags)
3. **Conflict Resolution** (merge vs rebase, conflict strategies)
4. **History Manipulation** (interactive rebase, fixup, squash)
5. **Performance** (shallow clones, sparse checkout for monorepos)

## GitHub/PR Workflows
1. **PR Best Practices** (atomic commits, descriptive messages, linked issues)
2. **Code Review** (review etiquette, constructive feedback, approval processes)
3. **CI/CD Integration** (GitHub Actions, status checks, branch protection)
4. **Team Collaboration** (CODEOWNERS, PR templates, issue templates)

## Enterprise Patterns
1. **Monorepo Management** (submodules vs subtrees vs workspaces)
2. **Security** (signed commits, secret scanning, dependency scanning)
3. **Release Management** (semantic versioning, changelog generation)

## Palantir Context
1. **Interview Questions** (behavioral: "Describe a difficult code review")
2. **Collaboration Philosophy** (Palantir's emphasis on teamwork)

## Interview Q&A
Q: "How do you handle a large feature that conflicts with main branch?"
A: [Rebase strategy, feature flags, incremental merges]
(10-15 questions)
</content>

<style>
1,500-2,000 words, command examples, workflow diagrams in text
</style>

<sources>
- Git official docs
- GitHub docs
- Git best practices (2024-2025)
- Atlassian Git tutorials
</sources>

<instructions>
Rate 1-5, emphasize behavioral interview relevance
</instructions>
```

---

## GROUP 8: Advanced Capabilities & Visualization
**File Output:** `08_advanced_capabilities.md`

```
<goal>
Explore **D3.js**, **Web Workers**, **WebSocket**, **Service Workers**, and **Accessibility** for advanced enterprise frontend capabilities.
</goal>

<context>
Research Group 8 of 8. D3.js is critical for Palantir (they maintain Plottable, a D3-based charting library). Web Workers and WebSocket enable real-time data processing. Accessibility is enterprise compliance requirement.

Dependencies: JavaScript (Group 1), React (Group 2)
Related: Data-dense UIs (Blueprint Group 2)
</context>

<content>
## D3.js for Data Visualization
1. **Core Concepts** (selections, data joins, scales, axes)
2. **React Integration** (D3 + React patterns, who owns the DOM)
3. **Plottable** (Palantir's D3-based charting library architecture)
4. **Performance** (SVG vs Canvas, virtualization for large datasets)
5. **Palantir Usage** (visualization patterns in Foundry)

## Web Workers
1. **Concurrency Model** (main thread vs worker threads)
2. **Use Cases** (heavy computations, data processing for dashboards)
3. **Communication** (postMessage, Transferable objects)
4. **Debugging** (Chrome DevTools for workers)

## WebSocket
1. **Real-time Communication** (vs polling, vs Server-Sent Events)
2. **Protocol** (handshake, frames, close codes)
3. **React Integration** (custom hooks, connection management)
4. **Palantir Context** (real-time data updates in Foundry dashboards)

## Service Workers
1. **PWA Fundamentals** (offline support, caching strategies)
2. **Use Cases** (offline-first apps, background sync)
3. **Enterprise Considerations** (deployment, update strategies)

## Accessibility (a11y)
1. **WCAG 2.1 AA** (perceivable, operable, understandable, robust)
2. **React Patterns** (semantic HTML, ARIA attributes, keyboard navigation)
3. **Blueprint a11y** (Blueprint's accessibility-first approach)
4. **Testing** (axe-core, screen readers, keyboard-only navigation)

## Comparison Matrix
| Technology | Use Case | Palantir Relevance | Priority |
|------------|----------|-------------------|----------|
| D3.js | Data visualization | High (Plottable) | Must-learn |
| ... | ... | ... | ... |

## Interview Q&A
Q: "How would you visualize 100,000 data points in a responsive chart?"
A: [D3 + Canvas for performance, aggregation, LOD techniques, Web Workers for processing]
(15-20 questions covering all technologies)
</content>

<style>
2,500-3,000 words, code examples for each technology
</style>

<sources>
- D3.js official docs and Observable notebooks
- Plottable GitHub (github.com/palantir/plottable)
- MDN Web Workers, WebSocket, Service Workers docs
- WCAG 2.1 spec
- Blueprint accessibility documentation
- Palantir visualization examples
</sources>

<instructions>
Rate 1-5, emphasize D3.js and a11y for Palantir alignment, cross-reference Blueprint
</instructions>
```

---

## Execution Instructions

### 1. **Preparation**
- Create context file: `palantir-fde-context.md` with the template above
- Open Gemini Deep Research (gemini.google.com/app - AI Ultra plan)

### 2. **Execution Order**
Run in dependency order:
1. GROUP 1 (Language Foundation) - foundational
2. GROUP 2 (React Ecosystem) - depends on Group 1
3. GROUP 3-8 (parallel or sequential) - all depend on Groups 1-2

### 3. **Quality Control**
After each research completes:
- Export to Google Docs (native export)
- Use "Gem Chat Exporter" Chrome extension to export as markdown
- Save to `/home/palantir/coding/palantir-fde-prep/XX_groupname.md`
- Verify bracketed citations [1], [2] are present
- Check that cross-references to other groups are included

### 4. **Batch Optimization**
- Run 3-5 queries in parallel (separate tabs)
- AI Ultra allows 200/day - more than sufficient
- Each research takes 5-10 minutes
- Total time: ~1-2 hours for all 8

### 5. **Post-Research Aggregation**
After all 8 complete:
- Upload all 8 markdown files to NotebookLM
- Generate "Briefing Docs" for executive summary
- Create comparison matrices spanning all groups
- Extract "Universal Concepts" across all technologies

---

## Success Criteria

Each research output must include:
- [ ] 2,000-3,000 words (Groups 1,2,4,5,8) or 1,500-2,000 words (Groups 3,6,7)
- [ ] Bracketed numeric citations [1], [2], [3] with reference list
- [ ] Code examples tested for correctness
- [ ] Comparison tables where applicable
- [ ] 1-5 ratings on: Learning Curve, Interview Frequency, Palantir Criticality, Depth Required
- [ ] "Universal Concepts" section extracting language-agnostic principles
- [ ] "Palantir Integration Notes" linking to Blueprint/Foundry usage
- [ ] Cross-references to other technology groups
- [ ] 15-20 interview Q&A for major groups, 10-15 for smaller groups

---

**Total Research Coverage:** 8 groups spanning 26 technologies
**Estimated Total Output:** ~18,000-22,000 words of interview-ready technical knowledge
**Time to Complete:** 1-2 hours (parallel execution)
**AI Ultra Cost:** Included in subscription (200 reports/day limit)
