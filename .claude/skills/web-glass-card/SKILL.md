---
name: web-glass-card
description: "[Atom·WebDesign·Card] Generates glass morphism card component with 3 variants: animated conic-gradient border, static frosted, cyan accent glow. Each includes self-contained JS for tilt hover effect via Web Animations API. Requires web-design-tokens foundation. References: glass-card.html (markup), glass-card.css (styles with @property animation), glass-card.js (3D tilt + glow)."
disable-model-invocation: true
user-invocable: true
argument-hint: "[variant:animated|static|cyan] [tilt:true|false]"
---

# web-glass-card

Atom-level glass morphism card component. Three variants with progressive enhancement
for tilt interaction via Web Animations API.

## Prerequisites

Run `/web-design-tokens` first to load CSS custom properties (`--glass-bg`, `--glass-border`,
`--bg-angle`, `--neon-cyan`, etc.) into your page. This skill's CSS consumes those tokens.

## Variants

| Variant | Class | Effect | Performance |
|---------|-------|--------|-------------|
| `animated` | `.glass-card` | Spinning conic-gradient border via `@property --bg-angle` | Medium (CSS-only) |
| `static` | `.glass-card-static` | Frosted glass with static border | Low (no animation) |
| `cyan` | `.glass-card-cyan` | Cyan glow border + box-shadow | Low (no animation) |

## Parameters

- **variant** — `animated` (default), `static`, or `cyan`
- **tilt** — `true` (default) or `false`; controls 3D mousemove effect on desktop

## Usage

```
/web-glass-card animated tilt:true
```

Copy the three reference files into your project:

1. **`glass-card.html`** — Semantic markup with data attributes
2. **`glass-card.css`** — `@property` animation + backdrop-filter + `@supports` guards
3. **`glass-card.js`** — Self-contained; call `initGlassCardTilt()` or auto-init on DOMContentLoaded

### Minimal Integration

```html
<!-- After web-design-tokens CSS -->
<link rel="stylesheet" href="glass-card.css">

<div class="glass-card" data-tilt>
  <div class="glass-card-body">
    <!-- your content -->
  </div>
</div>

<script src="glass-card.js"></script>
```

### Static Variant (No Animation)

```html
<div class="glass-card-static">
  <div class="glass-card-body">
    <!-- your content -->
  </div>
</div>
```

### Cyan Glow Variant

```html
<div class="glass-card-cyan">
  <div class="glass-card-body">
    <!-- your content -->
  </div>
</div>
```

## Animation Architecture

- **`@property --bg-angle`** — Registered angle type enables smooth conic-gradient rotation
- **CSS-only** — No JavaScript required for the border animation
- **Web Animations API** — Used only for glow transitions on mousemove (off main thread)
- **`requestAnimationFrame`** — Throttles mousemove calculations
- **`prefers-reduced-motion`** — Disables tilt + spin when user requests reduced motion
- **AbortController** — Cleans up all event listeners when card is removed from DOM

## Browser Support

| Feature | Support |
|---------|---------|
| `backdrop-filter` | Baseline Widely Available 2025 |
| `@property` | Baseline 2025 (all modern) |
| Web Animations API | All modern browsers |
| CSS Nesting | Baseline, 91% global |

`@supports (backdrop-filter: blur(1px))` guard included — fallback uses solid background.

## Integration with Other Skills

- **Inputs**: `web-design-tokens` (CSS tokens, required)
- **Outputs**: Card component used by `web-card-grid`, `web-hero-section`
- **Peer**: Can contain `web-chip`, `web-progress-bar`, `web-icon-badge` as children
