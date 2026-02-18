---
name: web-status-badge
description: "[Atom·WebDesign·Status] Provides inline status indicator with pulse animation, color-coded variants (active/warning/error/info/neutral), and optional label. Dot + text pattern with configurable pulse speed. Use for system status, availability indicators, or progress states. Pure CSS animation with prefers-reduced-motion support. References web-design-tokens."
user-invocable: true
argument-hint: "[status:active|warning|error|info|neutral] [pulse:true|false] [label:text]"
---

# web-status-badge

Atom-level inline status indicator. Pure CSS — no JavaScript required. Uses oklch colors
from `web-design-tokens` for perceptually uniform color coding. Pairs with glass cards,
dashboard panels, and nav headers.

## Status Variants

| Variant    | Color   | Use case                          |
|------------|---------|-----------------------------------|
| `active`   | green   | Online, passing, available        |
| `warning`  | orange  | Degraded, pending, needs attention|
| `error`    | red     | Offline, failed, critical         |
| `info`     | cyan    | Informational, loading, neutral+  |
| `neutral`  | gray    | Unknown, disabled, inactive       |

## Basic Usage

```html
<!-- Dot only -->
<span class="status-badge status-badge--active"></span>

<!-- Dot + label (default) -->
<span class="status-badge status-badge--active">Online</span>

<!-- Pulse disabled -->
<span class="status-badge status-badge--active status-badge--no-pulse">Active</span>

<!-- Pulse speed override -->
<span class="status-badge status-badge--warning" style="--pulse-speed: 0.8s">Slow pulse</span>
```

## Accessibility

The animated dot is `aria-hidden`. Always include a text label or `aria-label` for
screen readers:

```html
<!-- Accessible: text is the label -->
<span class="status-badge status-badge--active">Active</span>

<!-- Accessible: dot-only with aria-label on wrapper -->
<span class="status-badge status-badge--active" aria-label="Status: active"></span>
```

## Pulse Animation

The pulse uses `@keyframes pulse-ring` — a scale + opacity fade. It respects
`prefers-reduced-motion: reduce` via the media query override in `status-badge.css`,
which disables the animation entirely.

Pulse speed can be overridden with the `--pulse-speed` CSS variable (default `1.5s`).

## Inline Integration Examples

```html
<!-- In a nav header -->
<nav>
  <span>API Status</span>
  <span class="status-badge status-badge--active">Operational</span>
</nav>

<!-- In a glass card -->
<div class="glass-card-static">
  <span class="status-badge status-badge--warning">Degraded</span>
  <p>Some services may be slow.</p>
</div>

<!-- Multiple statuses -->
<ul>
  <li><span class="status-badge status-badge--active">Auth API</span></li>
  <li><span class="status-badge status-badge--error">Payment API</span></li>
  <li><span class="status-badge status-badge--info">Analytics</span></li>
</ul>
```

## Files

| File                             | Purpose                                      |
|----------------------------------|----------------------------------------------|
| `references/status-badge.html`  | Copy-paste HTML snippets, all variants       |
| `references/status-badge.css`   | Full CSS with @keyframes, color variants, motion |

No JS file — pure CSS component.

## Dependencies

- `web-design-tokens` → `tokens.css` must be loaded before `status-badge.css`
