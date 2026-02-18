---
name: web-scroll-progress
description: "[Atom·WebDesign·Indicator] Provides fixed-top scroll progress bar with gradient fill tracking page scroll position. Two implementations: CSS-only scroll-driven animation (modern browsers) and JS scroll event fallback. Gradient: cyan to magenta to green. Use for long-form content pages. References web-design-tokens for colors."
user-invocable: true
argument-hint: "[gradient:neon|mono|custom] [height:2px|3px|4px]"
---

## Execution Model

Atom-level. Lead-direct. No subagents. User copy-pastes 3 reference files into their project.

## Usage

### 1. Prerequisites

Include `web-design-tokens` first:
```html
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="scroll-progress.css">
```

### 2. HTML

Copy `references/scroll-progress.html`. Place as first child of `<body>`.
The element id `scroll-progress` is required for the JS fallback.

### 3. CSS

Copy `references/scroll-progress.css`. The `@supports (animation-timeline: scroll())` block
enables CSS scroll-driven animation in Chrome/Edge/Safari. Firefox falls back to the JS implementation.

**CRITICAL**: `animation-timeline` is declared AFTER the `animation` shorthand — required by spec.

### 4. JavaScript (Firefox fallback only)

Copy `references/scroll-progress.js`. The script calls `CSS.supports('animation-timeline', 'scroll()')`
and silently exits in modern browsers — no wasted work.

## Configuration Options

| Option | Mechanism | Default |
|--------|-----------|---------|
| Height: 2px | `.scroll-progress--thin` class | 3px |
| Height: 4px | `.scroll-progress--thick` class | 3px |
| Gradient: neon | default | cyan → magenta → green |
| Gradient: mono | `.scroll-progress--mono` class | — |
| Gradient: custom | Override `background` in your CSS | — |

## Progressive Enhancement

- **Chrome 115+ / Edge 115+ / Safari 26+**: CSS-only, zero JavaScript execution.
- **Firefox**: JS fallback activates automatically. Uses `passive` scroll listener.
- **`prefers-reduced-motion`**: Bar hidden entirely via `display: none`.

## Browser Support Summary

| Browser | Method | Notes |
|---------|--------|-------|
| Chrome 115+ | CSS scroll-driven | `animation-timeline: scroll()` |
| Edge 115+ | CSS scroll-driven | Same as Chrome |
| Safari 26+ | CSS scroll-driven | Interop 2026 target |
| Firefox | JS fallback | `passive` scroll listener |

## Quality Gate
- [ ] `animation-timeline` declared AFTER `animation` shorthand in CSS
- [ ] `@supports (animation-timeline: scroll())` guard present
- [ ] JS fallback exits early via `CSS.supports()` check
- [ ] `prefers-reduced-motion` hides bar
- [ ] Element id `scroll-progress` present for JS targeting

## Output

4 files: `SKILL.md` + `references/scroll-progress.html` + `references/scroll-progress.css` + `references/scroll-progress.js`
