---
name: web-card-grid
description: "[Organism·WebDesign·Grid] Renders responsive card grid composing web-glass-card atoms with CSS Grid auto-fill/minmax, Container Queries, and stagger-reveal entrance. CSS scroll-driven animation primary; IntersectionObserver JS fallback for Firefox. Use for portfolio, project showcase, or feature grid sections. References: card-grid.html, card-grid.css, card-grid.js."
user-invocable: true
argument-hint: "[columns:2|3|4] [min-card-width:280px] [gap:sm|md|lg] [stagger:true|false]"
---

# web-card-grid

Organism-level responsive card grid. Composes `web-glass-card` atoms inside a CSS Grid container
with `auto-fill/minmax` for intrinsic responsiveness. Reveals cards via CSS scroll-driven
animations with an `IntersectionObserver` fallback for Firefox.

## Prerequisites

Run `/web-design-tokens` and `/web-glass-card` first. Optionally run `/web-section-wrapper` to
wrap the grid inside a full section container.

## Structure

```
.card-grid-section
└── .card-grid-inner
    ├── .card-grid-header        (optional title block)
    │   ├── p.section-eyebrow
    │   └── h2.section-title[id]
    └── .card-grid[role="list"]
        └── .glass-card[role="listitem"][data-grid-item] (×N)
            └── ... (from web-glass-card)
```

## Reveal Animation

### Primary: CSS Scroll-Driven (Chrome/Edge/Safari)

```css
@supports (animation-timeline: view()) {
  [data-grid-item] {
    animation: grid-item-reveal linear both;
    animation-timeline: view();
    animation-range: entry 0% entry 30%;
  }
}
```

Each item has `animation-delay` based on its column position (via nth-child), creating a
horizontal stagger effect within each row.

### Fallback: IntersectionObserver (Firefox)

- `card-grid.js` detects `CSS.supports('animation-timeline', 'view()')` — exits immediately in
  supporting browsers
- In Firefox: observes each `[data-grid-item]` and adds `.is-visible` class on intersection
- `.is-visible` triggers a CSS transition with `--item-delay` custom property for per-item stagger

## CSS Grid Layout

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--card-min-width, 280px), 1fr));
  gap: var(--grid-gap, 1.5rem);
}
```

Override `--card-min-width` and `--grid-gap` custom properties to control layout.

## Container Queries

Each `[data-grid-item]` carries `container-type: inline-size`. Card content can adapt based on
its own width rather than the viewport.

```css
@container (max-width: 300px) {
  .glass-card-body { padding: 1rem; }
}
```

## Responsive Behavior

- `auto-fill/minmax`: reflows automatically — 4 columns on wide screens, 1 on mobile
- No breakpoints needed in most cases
- Container query on card item for inner content adaptation
- `gap` scales from `0.75rem` (mobile) to `1.5rem` (≥ 768px)

## Customization

- Override `--card-min-width` (default `280px`) to control column count behavior
- Override `--grid-gap` (default `1.5rem`) for spacing
- Remove `.card-grid-header` if the section has an external heading
- Set `stagger: false` argument to skip delay calculations

## Variants

- `.card-grid--compact` — reduces gap and card padding
- `.card-grid--centered` — `justify-content: center` for odd-count last rows
