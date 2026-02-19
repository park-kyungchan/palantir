---
name: web-progress-bar
description: "[Atom·WebDesign·DataViz] Generates animated horizontal progress/gap bars with labels, percentage display, and status tags. 3 color variants (green/cyan/magenta). JS uses IntersectionObserver to trigger fill animation + animated counter on scroll-into-view. Optional CSS Scroll-Driven Animation mode. Requires web-design-tokens. References: progress-bar.html, progress-bar.css, progress-bar.js."
disable-model-invocation: true
user-invocable: true
argument-hint: "[color:green|cyan|magenta] [value:0-100] [target:0-100] [label:text]"
---

# web-progress-bar

Atom-level animated progress bar with label, percentage counter, optional target marker,
and status tag. Used in gap-matrix data visualization patterns.

## Prerequisites

Run `/web-design-tokens` first. Requires `--neon-cyan`, `--neon-green`, `--neon-magenta`,
`--ease-out-expo`, `--duration-reveal`, `--font-heading` tokens.

## Parameters

- **color** — `green` (default), `cyan`, or `magenta`
- **value** — Current fill percentage, `0–100` (default: `70`)
- **target** — Optional target marker position, `0–100` (omit to hide)
- **label** — Text label shown left of bar (default: `"Progress"`)

## Usage

```
/web-progress-bar cyan value:65 target:90 label:"수리논술 이해도"
```

### Minimal HTML (data-attribute driven)

```html
<link rel="stylesheet" href="progress-bar.css">

<div class="gap-matrix">
  <div class="gap-row"
       data-value="65"
       data-target="90"
       data-color="cyan"
       data-tag="medium">
    <span class="gap-label">수리논술 이해도</span>
    <div class="gap-bar-track">
      <div class="gap-bar-fill cyan" style="width:0%"></div>
      <div class="gap-bar-target" style="left:90%"></div>
      <span class="gap-bar-pct">0%</span>
    </div>
    <span class="gap-tag medium">보통</span>
  </div>
</div>

<script src="progress-bar.js"></script>
```

## Data Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `data-value` | `0–100` | Fill percentage |
| `data-target` | `0–100` | Dashed target line position (omit to hide) |
| `data-color` | `green\|cyan\|magenta` | Bar color variant |
| `data-tag` | `none\|medium\|high` | Status tag severity class |

## Animation Modes

### Mode 1: IntersectionObserver (Default, all browsers)

JS watches for `.gap-row` elements entering the viewport at `threshold: 0.15`.
On entry: animates `width` from `0%` to `data-value%` using CSS transition,
then runs `requestAnimationFrame` counter from `0` to `data-value`.

### Mode 2: CSS Scroll-Driven Animation (Chrome/Edge/Safari, progressive)

When `data-scroll-driven="true"` is set on `.gap-matrix`, the JS skips IO
and adds `scroll-driven` class which activates `animation-timeline: view()`.

```html
<div class="gap-matrix" data-scroll-driven="true">
  ...
</div>
```

Requires `@supports (animation-timeline: view())` — automatically detected.
Firefox falls back to Mode 1 (IO).

## Color Variants

| Class | Color | Token |
|-------|-------|-------|
| `.gap-bar-fill.green` | `--neon-green` | Green fill gradient |
| `.gap-bar-fill.cyan` | `--neon-cyan` | Cyan fill gradient |
| `.gap-bar-fill.magenta` | `--neon-magenta` | Magenta fill gradient |

## Status Tags

| Class | Meaning | Style |
|-------|---------|-------|
| `.gap-tag.none` | No gap | Green tinted |
| `.gap-tag.medium` | Moderate gap | Cyan tinted |
| `.gap-tag.high` | Significant gap | Magenta tinted |

## Accessibility

- `role="progressbar"` + `aria-valuenow` + `aria-valuemin="0"` + `aria-valuemax="100"` set by JS
- `prefers-reduced-motion` disables counter animation; bar immediately shows final value
- Label text always visible (no animation on label)

## Integration with Other Skills

- **Inputs**: `web-design-tokens` (required)
- **Outputs**: Used in `web-gap-matrix`, `web-stat-dashboard` organisms
- **Peer**: Often displayed inside `web-glass-card-static` containers
