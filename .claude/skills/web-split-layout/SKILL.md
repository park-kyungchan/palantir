---
name: web-split-layout
description: "[Organism·WebDesign·Layout] Generates sticky-left scrolling-right split layout for side-by-side content presentation. Left panel stays fixed while right panel scrolls. Responsive: stacks vertically on mobile. Composes web-design-tokens + web-glass-card. Use for portfolio items, feature showcases, or comparison views. References: split-layout.html, split-layout.css, split-layout.js."
user-invocable: true
argument-hint: "[ratio:40-60|50-50|30-70] [sticky:left|right] [mobile:stack|tabs]"
---

# web-split-layout

Organism-level sticky split layout. Left panel is `position: sticky` while right panel
scrolls. Built with CSS Grid, composes `web-design-tokens` and `web-glass-card`.

## Prerequisites

Run `/web-design-tokens` to load CSS tokens. Optionally include `web-glass-card` for
glass-panel styling.

## Parameters

- **ratio** — Column ratio: `40-60` (default), `50-50`, `30-70`
- **sticky** — Which side is sticky: `left` (default) or `right`
- **mobile** — Mobile behavior: `stack` (default, stacks vertically) or `tabs`

## Usage

```
/web-split-layout ratio:40-60 sticky:left mobile:stack
```

## Ratio Options

| Ratio | Left column | Right column | Use case |
|-------|-------------|--------------|----------|
| `40-60` | 2fr | 3fr | Default: nav/thumbnail + content |
| `50-50` | 1fr | 1fr | Side-by-side comparison |
| `30-70` | 3fr | 7fr | Minimal sidebar + wide content |

Apply via `data-ratio="40-60"` on `.split-layout`.

## Files

1. **`split-layout.html`** — Two-column markup, sticky panel, scrollable content
2. **`split-layout.css`** — CSS Grid layout, sticky positioning, responsive breakpoint
3. **`split-layout.js`** — Scroll progress indicator, IntersectionObserver section tracking

## Sticky Behavior

The left panel uses `position: sticky; top: 0; height: 100vh` so it remains fixed in
the viewport while `.split-right` overflows and scrolls. For `sticky:right`, CSS
classes are swapped via `data-sticky="right"`.

## Mobile Adaptation

At ≤768px the grid collapses to `grid-template-columns: 1fr`. The previously sticky
panel becomes normal flow. When `mobile:tabs`, a JS-driven tab switch replaces the
column layout on mobile.

## Animation Architecture

- **IntersectionObserver** — Tracks active section in right panel (adds `.is-active` to
  matching left-panel highlight)
- **Scroll progress** — `requestAnimationFrame`-driven progress bar for right panel
- **`prefers-reduced-motion`** — Disables all scroll-linked transitions
- **WAAPI** — Fade-in on initial mount via `.animate()` on both panels

## Browser Support

| Feature | Support |
|---------|---------|
| CSS Grid | All modern browsers |
| `position: sticky` | Baseline Widely Available |
| Container Queries | Baseline Widely Available |
| `backdrop-filter` | Baseline Widely Available 2025 |

## Integration with Other Skills

- **Inputs**: `web-design-tokens` (required), `web-glass-card` (optional panels)
- **Outputs**: Layout wrapper that contains any web-* atoms as panel content
- **Peer**: `web-nav-dots` can track sections in the right panel
