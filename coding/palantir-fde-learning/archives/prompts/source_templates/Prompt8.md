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
- Rate 1-5: Learning Curve, Interview Frequency, Palantir Criticality, Depth Required
- Emphasize D3.js and a11y for Palantir alignment, cross-reference Blueprint
</instructions>
```
