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
