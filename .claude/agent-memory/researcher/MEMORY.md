# Researcher Agent Memory

## Stable Patterns

### context7 Library ID Resolution (2026-02-19)
- Motion/Framer Motion: use `/websites/motion_dev` (1429 snippets, High rep) NOT `/grx7/framer-motion`
- GSAP: use `/llmstxt/gsap_llms_txt` (1656 snippets, High rep) — most comprehensive
- Lenis: use `/darkroomengineering/lenis` (45 snippets, High rep)
- Locomotive Scroll: use `/websites/scroll_locomotive_ca` (145 snippets) or `/locomotivemtl/locomotive-scroll` (277 snippets)
- BSMNT Scrollytelling: `/basementstudio/scrollytelling` (41 snippets)

### Scroll-Driven Animation Stack (2026-02-19, verified)
Canonical 2025 stack for scrollytelling in React/Next.js:
1. **Lenis** (`lenis/react`) — smooth scroll normalization. `syncTouch: false` default = native touch on mobile
2. **GSAP ScrollTrigger** — pin/scrub for fixed-background overlay pattern. `normalizeScroll(true)` for mobile
3. **GSAP SplitText** — word/char level text splitting for highlight effects. v3.13+ has `autoSplit`, `onSplit()`
4. **Motion `useScroll` + `useTransform`** — React-native scroll linking. v12 uses native ScrollTimeline
5. **CSS `animation-timeline: view()`** — zero-JS progressive enhancement (Chrome 115+, Safari 17.2+ partial)
6. **IntersectionObserver** — universal step-activation fallback

### CSS Scroll-Driven API Notes (2026-02-19)
- `@scroll-timeline` at-rule is DEPRECATED — use `animation-timeline` inline property
- `animation-range: entry 0% entry 60%` — controls when within element's viewport entry animation runs
- `view-timeline-name` + `animation-timeline: --name` = cross-element timeline coordination (Chrome only)
- Safari 17.2+: basic `view()` works, `animation-range` has gaps. Always test on iOS.

### GitHub MCP Auth (2026-02-19)
- GitHub MCP (`mcp__github-mcp-server__*`) returns "Authentication Failed: Bad credentials" — BLOCKED
- Do not retry GitHub search/code tools. Use context7 + resolve-library-id instead for code examples.
