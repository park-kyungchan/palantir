---
name: web-section-wrapper
description: "[Organism·WebDesign·Section] Scaffolds reusable page section with scroll-reveal entrance, gradient-underline section title, and optional glass background variant. Provides data-section-id hook for web-nav-dots active tracking. Composes web-design-tokens. Use as content section container wrapping any organism or custom content. References: section-wrapper.html, section-wrapper.css, section-wrapper.js."
user-invocable: true
argument-hint: "[id:section-id] [label:eyebrow-text] [title:heading] [glass:true|false] [reveal:true|false]"
---

# web-section-wrapper

Organism-level page section container. Provides the structural scaffold — `data-section-id` for
nav-dot integration, scroll-reveal entrance for the title block, and an optional glass
background variant — that all content sections share.

## Prerequisites

Run `/web-design-tokens` first. Optionally run `/web-nav-dots` for active-section tracking.

## Structure

```
section.section-wrapper[data-section-id]
└── .section-inner
    ├── .section-header         (optional title block)
    │   ├── p.section-eyebrow
    │   ├── h2.section-title    (gradient underline via ::after)
    │   └── p.section-subtitle (optional)
    └── .section-body           (slot for organism content)
        └── ... (compose any organism here)
```

## Nav-Dot Integration

Set `data-section-id` on `.section-wrapper` matching the `data-target` in `.nav-dots` markup:

```html
<section class="section-wrapper" data-section-id="projects">...</section>
```

`section-wrapper.js` registers each section with `floating-nav-dots.js` via a
`CustomEvent('section:register')` on `document`. If `web-nav-dots` is not loaded, the event
dispatch is safely ignored.

## Scroll-Reveal Entrance

### CSS Scroll-Driven (Chrome/Edge/Safari)

```css
@supports (animation-timeline: view()) {
  .section-header {
    animation: section-reveal linear both;
    animation-timeline: view();
    animation-range: entry 10% entry 40%;
  }
}
```

### Fallback: IntersectionObserver (Firefox)

`section-wrapper.js` detects missing `animation-timeline` support and falls back to an
IntersectionObserver that adds `.section-wrapper--visible` on intersection. CSS transitions
handle the reveal on `.section-wrapper--visible .section-header`.

## Glass Background Variant

Add `.section-wrapper--glass` to apply glass morphism to the entire section background:

```html
<section class="section-wrapper section-wrapper--glass" ...>
```

Requires `backdrop-filter` support (no fallback for very old browsers — gracefully degrades
to solid background).

## Responsive Behavior

- `.section-inner`: `max-width: 1100px`, horizontally centered
- `padding`: `5rem 2rem` desktop, `3rem 1.5rem` mobile
- Section title: `clamp(1.6rem, 3.5vw, 2.4rem)` fluid scaling
- Eyebrow: hides on very narrow screens (≤ 360px) if needed

## Gradient Underline Title

`.section-title::after` renders a gradient line below the heading:

```css
.section-title::after {
  content: '';
  display: block;
  height: 3px;
  background: linear-gradient(
    90deg,
    var(--neon-cyan),
    var(--neon-magenta)
  );
  /* Reveals from left on scroll-reveal */
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.6s ease;
}
.section-wrapper--visible .section-title::after {
  transform: scaleX(1);
}
```

CSS scroll-driven variant uses `animation-range` to achieve the same effect.

## Variants

- `.section-wrapper--glass` — glass morphism section background
- `.section-wrapper--dark` — explicit dark override for light-mode parent pages
- `.section-wrapper--narrow` — `max-width: 800px` for text-heavy sections
