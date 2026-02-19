---
name: web-stat-dashboard
description: "[Organism·WebDesign·Metrics] Generates animated counter grid with icon badges, glass cards, labels, and optional trend indicators. Staggered entrance animation. Composes web-design-tokens + web-glass-card + web-icon-badge. IntersectionObserver triggers countUp animation. Use for KPI displays, achievement counters, or statistics overview. References: stat-dashboard.html, stat-dashboard.css, stat-dashboard.js."
disable-model-invocation: true
user-invocable: true
argument-hint: "[stats:json] [columns:2|3|4] [animate:true|false]"
---

# web-stat-dashboard

Organism-level metric grid. Each stat card composes a glass card, icon badge, animated
counter, label, and optional trend indicator. Entrance animation is staggered via WAAPI.

## Prerequisites

Run `/web-design-tokens` first. Also load `web-glass-card` and `web-icon-badge` CSS
for the composed sub-components.

## Parameters

- **stats** — JSON array of stat objects (see data format below)
- **columns** — Grid columns: `2`, `3` (default), or `4`
- **animate** — `true` (default) enables countUp on intersection; `false` shows final value immediately

## Usage

```
/web-stat-dashboard columns:3 animate:true
```

## Stat Data Format

Pass stats via `data-stats` JSON attribute on `.stat-dashboard`:

```json
[
  { "icon": "🏆", "value": 94, "label": "Health Score", "suffix": "%", "trend": "up" },
  { "icon": "⚙️", "value": 48, "label": "Skills Built", "suffix": "", "trend": "up" },
  { "icon": "📦", "value": 6,  "label": "Agent Profiles", "suffix": "", "trend": null }
]
```

### Stat Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `icon` | string | Yes | Emoji or SVG string for icon badge |
| `value` | number | Yes | Target counter value |
| `label` | string | Yes | Description text below counter |
| `suffix` | string | No | Appended to value (e.g., `%`, `K`, `+`) |
| `trend` | `"up"` \| `"down"` \| `null` | No | Trend arrow indicator |

## Files

1. **`stat-dashboard.html`** — Grid container + stat card template, built from JSON
2. **`stat-dashboard.css`** — Grid layout, card styles, counter typography, trend arrow, stagger
3. **`stat-dashboard.js`** — IntersectionObserver, countUp via `requestAnimationFrame`, stagger WAAPI

## Counter Animation

`easeOutExpo` tween: `1 - Math.pow(2, -10 * progress)`. Runs in `requestAnimationFrame`
loop once the card enters the viewport. Large numbers automatically format with comma
separators. Suffixes like `K`/`M` are configurable per stat.

## Staggered Entrance

Cards animate with `80ms` delay per card using WAAPI:
```js
card.animate([
  { opacity: 0, transform: 'translateY(20px)' },
  { opacity: 1, transform: 'translateY(0)' }
], { duration: 600, delay: index * 80, fill: 'forwards', easing: 'cubic-bezier(0.16,1,0.3,1)' });
```

## Trend Indicators

`trend: "up"` renders a `▲` arrow in `--neon-green`; `trend: "down"` renders `▼` in
`--neon-red`. Omit the field or set to `null` to hide indicator.

## Browser Support

| Feature | Support |
|---------|---------|
| CSS Grid with `auto-fit` | All modern |
| Web Animations API | All modern |
| IntersectionObserver v1 | Baseline |
| `color-mix()` | Baseline 2025 |

## Integration with Other Skills

- **Inputs**: `web-design-tokens`, `web-glass-card`, `web-icon-badge`
- **Outputs**: Metric grid used in hero sections, dashboards, or proof-of-work sections
- **Peer**: Can be embedded inside `web-section-wrapper` or `web-deep-dive`
