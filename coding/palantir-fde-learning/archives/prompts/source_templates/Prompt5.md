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
- Rate 1-5: Learning Curve, Interview Frequency, Palantir Criticality, Depth Required
- Include debugging strategies for Palantir re-engineering interviews
</instructions>
```
