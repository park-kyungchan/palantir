---
name: web-chip
description: "[Atom·WebDesign·Tag] Generates pill-shaped tag/chip components in flex-wrap container. Variants: default (outlined), filled, colored (neon accents). Minimal JS for optional click-to-filter interaction. Requires web-design-tokens. References: chip.html (markup), chip.css (styles), chip.js (optional filter)."
disable-model-invocation: true
user-invocable: true
argument-hint: "[variant:default|filled|colored] [interactive:true|false]"
---

# web-chip

Atom-level pill/tag chip component. Flex-wrap container with three visual variants.
Optional JS click-to-filter interaction via Web Animations API.

## Prerequisites

Run `/web-design-tokens` first. This skill requires `--neon-cyan`, `--neon-magenta`,
`--glass-border`, `--text-secondary`, `--font-heading` tokens.

## Variants

| Variant | Class | Appearance |
|---------|-------|------------|
| `default` | `.chip` | Outlined pill — white border 15%, muted background |
| `filled` | `.chip.chip--filled` | Solid glass background with stronger border |
| `colored` | `.chip.chip--cyan` / `.chip--magenta` / `.chip--green` | Neon accent color border + subtle tinted background |

## Parameters

- **variant** — `default` (default), `filled`, or `colored`
- **interactive** — `true` or `false` (default); adds click-to-toggle active state + WAAPI transition

## Usage

```
/web-chip colored interactive:true
```

### Minimal Integration

```html
<link rel="stylesheet" href="chip.css">

<div class="hero-chips">
  <span class="chip">Tag Label</span>
  <span class="chip chip--cyan">Active Tag</span>
  <span class="chip chip--filled">Filled Tag</span>
</div>

<!-- Optional: include only when interactive:true -->
<script src="chip.js"></script>
```

### Interactive Filter Group

Add `data-filter-group` to the container and `data-filter-value` to each chip:

```html
<div class="hero-chips" data-filter-group="skills">
  <span class="chip chip--cyan chip--active" data-filter-value="all">All</span>
  <span class="chip" data-filter-value="math">Math</span>
  <span class="chip" data-filter-value="physics">Physics</span>
</div>
```

JavaScript emits a `chipfilter` custom event on the container:

```javascript
document.querySelector('[data-filter-group]').addEventListener('chipfilter', (e) => {
  console.log(e.detail.value); // selected filter value
});
```

## Container Layout

`.hero-chips` uses `display: flex; flex-wrap: wrap; gap: 0.6rem; justify-content: center`.
Override alignment via `data-align="left"` attribute on the container.

## Color Modifier Classes

| Class | Token Used |
|-------|-----------|
| `.chip--cyan` | `--neon-cyan` |
| `.chip--magenta` | `--neon-magenta` |
| `.chip--green` | `--neon-green` |
| `.chip--purple` | `--neon-purple` |

## Animation Architecture

- **WAAPI** — `element.animate()` for smooth active-state transitions (opacity + scale)
- **Event delegation** — Single listener on container, not per-chip
- **No external imports** — Pure vanilla JS, ~40 lines

## Integration with Other Skills

- **Inputs**: `web-design-tokens` (required)
- **Outputs**: Used inside `web-glass-card`, `web-hero-section` components
- **Peer**: Often accompanies `web-icon-badge` for labeling patterns
