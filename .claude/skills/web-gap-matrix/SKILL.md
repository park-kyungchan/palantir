---
name: web-gap-matrix
description: "[Organism·WebDesign·Analytics] Generates interactive horizontal bar chart matrix with category grouping, progress-bar atoms, gap tags, and target lines. Composes web-design-tokens + web-progress-bar + web-status-badge. IntersectionObserver triggers staggered fill animations. Use for gap analysis, skill assessment, or comparative metrics. References: gap-matrix.html, gap-matrix.css, gap-matrix.js."
user-invocable: true
argument-hint: "[categories:json] [show-targets:true|false] [animate:true|false]"
---

# web-gap-matrix — Organism Usage Guide

Interactive gap analysis matrix: category-grouped rows, animated fill bars, colored status tags, and dashed target lines. Composes `web-design-tokens` + `web-progress-bar` atoms.

---

## Prerequisites

Load these in order before `gap-matrix.css`:
```html
<link rel="stylesheet" href="tokens.css">        <!-- web-design-tokens -->
<link rel="stylesheet" href="progress-bar.css">  <!-- web-progress-bar -->
<link rel="stylesheet" href="gap-matrix.css">    <!-- this skill -->
<script defer src="gap-matrix.js"></script>
```

---

## HTML Data Attributes

Each `.gap-row` is configured entirely via `data-*` attributes — no inline styles needed:

| Attribute     | Type            | Description                                     |
|---------------|-----------------|-------------------------------------------------|
| `data-value`  | `0–100`         | Current level percentage (fill width)           |
| `data-target` | `0–100`         | Target/goal percentage (dashed line position)   |
| `data-color`  | `green\|cyan\|magenta` | Fill and tag accent color                |
| `data-tag`    | `none\|medium\|high`   | Gap severity label pill                  |
| `data-label`  | string          | Row name (matches `GapMatrix.highlight(label)`) |
| `data-tooltip`| string          | Hover tooltip description text                  |

---

## Category Groups

Wrap rows in `.gap-category` for collapsible section headers:

```html
<div class="gap-matrix" id="gap-matrix" data-animate="true" data-show-targets="true">

  <div class="gap-category">
    <button class="gap-category-header" aria-expanded="true">
      <span class="gap-category-title">Technical Skills</span>
      <span class="gap-category-count">3 items</span>
      <span class="gap-category-chevron" aria-hidden="true">▾</span>
    </button>
    <div class="gap-category-body">

      <div class="gap-row"
           data-value="72" data-target="90"
           data-color="cyan" data-tag="medium"
           data-label="LaTeX Typesetting"
           data-tooltip="Needs practice with complex expressions">
        <span class="gap-label">LaTeX Typesetting</span>
        <div class="gap-bar-track">
          <div class="gap-bar-fill cyan"></div>
          <div class="gap-bar-target"></div>
          <span class="gap-bar-pct">0%</span>
        </div>
        <span class="gap-tag medium">Medium</span>
        <div class="gap-row-tooltip" role="tooltip">
          <span class="tooltip-name">LaTeX Typesetting</span>
          Needs practice with complex expressions
        </div>
      </div>

    </div>
  </div>

</div>
```

---

## Matrix-Level Attributes

| Attribute              | Default | Description                              |
|------------------------|---------|------------------------------------------|
| `data-animate="true"`  | `true`  | Enable IntersectionObserver stagger      |
| `data-show-targets`    | `true`  | Show dashed target lines                 |

---

## Color / Tag Reference

| `data-color` | Fill gradient                           | `data-tag` | Pill color  |
|--------------|-----------------------------------------|------------|-------------|
| `green`      | rgba(46,204,113,0.6) → 0.3              | `none`     | neon-green  |
| `cyan`       | rgba(0,255,255,0.5) → 0.2               | `medium`   | neon-cyan   |
| `magenta`    | rgba(255,0,255,0.5) → 0.2               | `high`     | neon-magenta|

---

## JavaScript API

```js
// Highlight a row (e.g., linked to a deep-dive panel in view)
GapMatrix.highlight('LaTeX Typesetting');

// Clear all highlights
GapMatrix.clearHighlights();
```

Link `web-gap-matrix` to `web-deep-dive` via IntersectionObserver on the deep-dive items:
```js
const observer = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) GapMatrix.highlight(e.target.dataset.label);
  });
}, { threshold: 0.5 });
document.querySelectorAll('.deep-dive-item').forEach(el => observer.observe(el));
```

---

## CSS Scroll-Driven Mode (Chrome/Edge/Safari)

JS auto-detects `@supports (animation-timeline: scroll())` and adds `.scroll-driven` to the matrix. The CSS then handles fill animation without JS counters. Firefox falls back to IntersectionObserver automatically.

---

## Responsive Behavior

- **Default**: label (140px) + track (flex: 1) + tag — horizontal row
- **≤500px**: label shrinks to 90px, smaller font
- **≤420px**: label stacks above track (flex-wrap)

---

## Composition Notes

- **web-design-tokens**: all `var(--neon-*)`, `var(--glass-*)`, `var(--ease-*)` tokens
- **web-progress-bar**: shares `.gap-row`, `.gap-bar-track`, `.gap-bar-fill` base atoms
- **web-status-badge**: tag pills (`.gap-tag`) follow same color token pattern
- **web-deep-dive**: `GapMatrix.highlight(label)` API for linked panel coordination
