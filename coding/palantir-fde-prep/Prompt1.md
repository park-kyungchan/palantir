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
