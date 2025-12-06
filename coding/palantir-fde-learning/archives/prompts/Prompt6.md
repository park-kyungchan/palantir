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
- Rate 1-5: Learning Curve, Interview Frequency, Palantir Criticality, Depth Required
- Emphasize Webpack for Palantir alignment, lighter coverage on Gradle
</instructions>
```
