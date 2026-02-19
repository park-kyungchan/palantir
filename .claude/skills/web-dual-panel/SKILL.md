---
name: web-dual-panel
description: "[Organism·WebDesign·Layout] Generates two-column panel layout with glass cards containing icon-based content blocks. Equal-height columns with gap. Each panel supports icon badge, title, description, and list items. Composes web-design-tokens + web-glass-card + web-icon-badge. Use for feature comparisons, service tiers, or before/after layouts. References: dual-panel.html, dual-panel.css, dual-panel.js."
disable-model-invocation: true
user-invocable: true
argument-hint: "[layout:side-by-side|stacked] [panels:json]"
---

# web-dual-panel

Organism-level two-column glass card layout. Each panel carries an icon badge, title,
description, and a styled list. Equal-height columns via CSS Grid. Composes
`web-design-tokens`, `web-glass-card`, and `web-icon-badge`.

## Prerequisites

Run `/web-design-tokens`. Include `web-glass-card` and `web-icon-badge` CSS files.

## Parameters

- **layout** — `side-by-side` (default) or `stacked`
- **panels** — JSON array of 2 panel objects (see data format)

## Usage

```
/web-dual-panel layout:side-by-side
```

## Panel Data Format

Pass via `data-panels` JSON attribute on `.dual-panel`:

```json
[
  {
    "icon": "🔍",
    "accent": "cyan",
    "title": "Before",
    "description": "Manual process prone to errors.",
    "items": ["Slow iteration cycles", "No reproducibility", "High maintenance cost"]
  },
  {
    "icon": "⚡",
    "accent": "green",
    "title": "After",
    "description": "Automated pipeline with full audit trail.",
    "items": ["10× faster delivery", "Deterministic output", "Self-healing INFRA"]
  }
]
```

### Panel Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `icon` | string | Yes | Emoji or SVG for icon badge |
| `accent` | string | No | Badge accent color (`cyan`, `green`, `magenta`, `purple`, `orange`) |
| `title` | string | Yes | Panel heading |
| `description` | string | No | Short paragraph below heading |
| `items` | string[] | No | List entries with custom marker |

## Files

1. **`dual-panel.html`** — Two glass card panels with icon badge, title, description, list
2. **`dual-panel.css`** — CSS Grid two-column, equal height, list markers, responsive stack
3. **`dual-panel.js`** — Staggered panel entrance (WAAPI), optional comparison slider

## Layout Options

| `data-layout` | Behavior |
|---------------|----------|
| `side-by-side` | 2-column CSS Grid, equal width (default) |
| `stacked` | 1-column, panels flow vertically |

Responsive: collapses to `1fr` at ≤640px regardless of `layout` setting.

## Comparison Slider (Optional)

Add `data-comparison` on `.dual-panel` to enable a drag handle slider between the two
panels. The slider repositions a `clip-path` on the right panel to reveal/hide content.
Requires mouse + touch event listeners (included in `dual-panel.js`).

## Animation Architecture

- **WAAPI staggered entrance** — Left panel at `0ms`, right panel at `120ms` delay
- **IntersectionObserver** — Triggers entrance when panels enter viewport
- **List item stagger** — Each `<li>` animates in at `60ms` intervals after card entrance
- **`prefers-reduced-motion`** — Skips all animations; panels immediately visible

## Browser Support

| Feature | Support |
|---------|---------|
| CSS Grid | All modern |
| `backdrop-filter` | Baseline Widely Available 2025 |
| Web Animations API | All modern |
| `color-mix()` | Baseline 2025 |

## Integration with Other Skills

- **Inputs**: `web-design-tokens`, `web-glass-card`, `web-icon-badge`
- **Outputs**: Dual panel block used in comparison sections, service tiers, or feature contrast
- **Peer**: Can sit inside `web-section-wrapper`; panels can embed `web-chip` tags
