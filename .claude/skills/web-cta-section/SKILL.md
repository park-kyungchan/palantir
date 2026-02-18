---
name: web-cta-section
description: "[Organism·WebDesign·Action] Generates call-to-action section with gradient headline, description text, primary and secondary action buttons, and glass morphism background. Scroll-reveal entrance. Composes web-design-tokens. Button hover effects with WAAPI glow. Use for conversion sections, contact prompts, or newsletter signups. References: cta-section.html, cta-section.css, cta-section.js."
user-invocable: true
argument-hint: "[headline:text] [description:text] [primary-btn:text] [secondary-btn:text]"
---

# web-cta-section

Organism-level call-to-action section. Centered layout with gradient headline, body copy,
and a primary + secondary button group. Scroll-reveal entrance via IntersectionObserver
with WAAPI. Composes `web-design-tokens`.

## Prerequisites

Run `/web-design-tokens` first to load CSS tokens. No other skill dependency required.

## Parameters

Pass as `data-*` attributes on `.cta-section` or override inline:

- **headline** — Main heading text (gradient effect applied)
- **description** — Supporting paragraph (max ~120 chars recommended)
- **primary-btn** — Primary button label (default: `"Get Started"`)
- **secondary-btn** — Secondary button label (default: `"Learn More"`); omit to hide

## Usage

```
/web-cta-section headline:"Ready to build?" description:"Join 1000+ teams." primary-btn:"Start Free" secondary-btn:"View Docs"
```

## Files

1. **`cta-section.html`** — Section markup with heading, paragraph, button group
2. **`cta-section.css`** — Layout, gradient headline, button variants, glass option, responsive
3. **`cta-section.js`** — Scroll-reveal entrance, button hover glow, particle burst on primary click

## Button Variants

| Class | Style | Use |
|-------|-------|-----|
| `.cta-btn-primary` | Filled gradient (cyan→magenta) | Main conversion action |
| `.cta-btn-secondary` | Outlined with glass background | Secondary navigation |

Add `.cta-btn-magnetic` for mousemove magnetic attraction effect.

## Background Options

| Class on `.cta-section` | Effect |
|--------------------------|--------|
| *(default)* | Transparent — inherits page background |
| `.cta-section--glass` | Glass morphism backdrop panel |
| `.cta-section--aurora` | Inline aurora gradient orbs |

## Animation Architecture

- **Scroll-reveal** — `IntersectionObserver` adds `.is-visible` triggering WAAPI fade-up
  on `.cta-inner`
- **Button glow** — WAAPI `--glow-intensity` pulse on `mouseenter`; reversed on `mouseleave`
- **Particle burst** — On primary button click, 12 neon particles fan out then fade
  (optional, `data-particles` attribute)
- **`prefers-reduced-motion`** — All animations disabled; content immediately visible

## Responsive

Buttons stack vertically at ≤480px. Max-width container (`--container-max`) centered with
`padding: 0 var(--space-lg)`. Headline uses `clamp()` for fluid typography.

## Browser Support

| Feature | Support |
|---------|---------|
| CSS Gradient text (`-webkit-background-clip`) | All modern |
| Web Animations API | All modern |
| IntersectionObserver v1 | Baseline |
| `backdrop-filter` | Baseline Widely Available 2025 |

## Integration with Other Skills

- **Inputs**: `web-design-tokens` (required)
- **Outputs**: Standalone section block, typically placed at page bottom or between content
- **Peer**: Can host `web-chip` tags below the headline for social proof labels
