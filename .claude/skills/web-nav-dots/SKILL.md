---
name: web-nav-dots
description: "[Atom·WebDesign·Navigation] Provides fixed-position section navigation dots with active state glow, hover label tooltips, and smooth scroll. JS IntersectionObserver tracks active section. Hidden on mobile via media query. Use for single-page scrolling sites with multiple sections. References web-design-tokens for colors."
user-invocable: true
argument-hint: "[position:right|left] [labels:true|false]"
---

## Execution Model

Atom-level. Lead-direct. No subagents. User copy-pastes 4 reference files into their project.

## Usage

### 1. Prerequisites

Include `web-design-tokens` first:
```html
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="nav-dots.css">
```

### 2. HTML Structure

Copy `references/nav-dots.html`. Customize `data-section` and `data-label` for each section.
Each `data-section` value must match the `id` of a page section:

```html
<section id="s1">...</section>
<section id="s2">...</section>
```

### 3. CSS

Copy `references/nav-dots.css`. Uses these design tokens:
- `--neon-cyan` — active dot color and glow
- `--duration-fast` — transition speed
- `--ease-smooth` — transition easing
- `--text-secondary` — label text color

### 4. JavaScript

Copy `references/nav-dots.js`. IIFE auto-initializes on load.
The IntersectionObserver (threshold: 0.4) sets `.active` on the dot matching the visible section.

## Configuration Options

| Option | Mechanism | Default |
|--------|-----------|---------|
| Position: right | default | Right side at 1.5rem |
| Position: left | `.nav-dots--left` class | — |
| Labels: hover tooltip | `data-label="Text"` attribute | Visible on hover/focus |
| Labels: hidden | Omit `data-label` attribute | No tooltip |
| Breakpoint | Edit `@media (max-width: 768px)` | 768px |

## Mobile Behavior

Hidden via `@media (max-width: 768px) { display: none }`.
To override: edit the breakpoint value in `nav-dots.css`.

## Keyboard Accessibility

Each dot has `role="button"` and `tabindex="0"`. Enter/Space keys trigger scroll.
`:focus-visible` outline uses `--neon-cyan` border for keyboard users.

## Quality Gate
- [ ] `data-section` values match actual section `id` attributes
- [ ] `nav-dots.js` included after HTML (or deferred)
- [ ] `tokens.css` loaded before `nav-dots.css`
- [ ] `prefers-reduced-motion`: uses `'instant'` scroll behavior

## Output

4 files: `SKILL.md` + `references/nav-dots.html` + `references/nav-dots.css` + `references/nav-dots.js`
