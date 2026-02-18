---
name: web-icon-badge
description: "[Atom·WebDesign·Icon] Provides circular icon container with gradient border, inner glow, and hover scale effect. Configurable size (sm/md/lg/xl), supports emoji, SVG inline, or image. Glass morphism background with backdrop-filter. Use for feature highlights, stat indicators, or avatar placeholders. References web-design-tokens for colors and glass tokens."
user-invocable: true
argument-hint: "[size:sm|md|lg|xl] [glow:true|false] [content:emoji|svg|img]"
---

# web-icon-badge

Atom-level circular icon container for web template compositions. Pairs with glass card
components and stat dashboards. Depends on `web-design-tokens` (tokens.css) for all
custom property values.

## Sizes

| Size  | Container | Inner icon | Use case                  |
|-------|-----------|------------|---------------------------|
| `sm`  | 40px      | 20px       | Inline labels, chip icons |
| `md`  | 56px      | 28px       | Feature cards (default)   |
| `lg`  | 72px      | 36px       | Section headings           |
| `xl`  | 96px      | 48px       | Hero highlights, avatars  |

Add the size modifier class to the `.icon-badge` element:
```html
<div class="icon-badge icon-badge--lg">🚀</div>
```

## Content Types

### Emoji
```html
<div class="icon-badge">🚀</div>
```

### SVG inline
```html
<div class="icon-badge">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
  </svg>
</div>
```

### Image
```html
<div class="icon-badge">
  <img src="avatar.png" alt="User avatar" loading="lazy">
</div>
```

## Glow Variants

Add `icon-badge--glow` to intensify the default glow ring:
```html
<div class="icon-badge icon-badge--xl icon-badge--glow">⚡</div>
```

To use a magenta glow instead of the default cyan:
```html
<div class="icon-badge icon-badge--glow-magenta">🔮</div>
```

## Color Accent Variants

Override the accent color using data attributes (maps to token palette):
```html
<div class="icon-badge" data-accent="green">✅</div>
<div class="icon-badge" data-accent="orange">⚠️</div>
<div class="icon-badge" data-accent="red">❌</div>
```

## With JS Entrance Animation

Add `data-animate` for IntersectionObserver-driven WAAPI fade-in-up:
```html
<div class="icon-badge" data-animate>🎯</div>
```
Include `icon-badge.js` on the page and call `IconBadge.init()`.

## Hover Cursor Follow (Optional)

Add `data-cursor-glow` to enable a lightweight cursor-follow glow effect:
```html
<div class="icon-badge" data-cursor-glow>💎</div>
```
Requires `icon-badge.js` (auto-init on `data-cursor-glow` presence).

## Integration with Stat Dashboard

Typical usage inside a stat or feature card:
```html
<div class="glass-card-static stat-card">
  <div class="icon-badge icon-badge--lg" data-animate>📊</div>
  <p class="stat-value">94%</p>
  <p class="stat-label">Health Score</p>
</div>
```

## Files

| File                      | Purpose                                  |
|---------------------------|------------------------------------------|
| `references/icon-badge.html` | Copy-paste HTML snippets, all variants |
| `references/icon-badge.css`  | Full CSS including size/glow variants  |
| `references/icon-badge.js`   | Optional entrance + cursor-glow JS     |

## Dependencies

- `web-design-tokens` → `tokens.css` must be loaded before `icon-badge.css`
- No external JS libraries required
