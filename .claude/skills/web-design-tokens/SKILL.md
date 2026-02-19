---
name: web-design-tokens
description: >-
  [Foundation·WebDesign·Tokens] Emits CSS custom properties, font imports, base reset, accessibility defaults, and animation easing system for all web-* template skills. Use when starting any web design project or page. Provides: oklch color palette with hex fallbacks, @property registered animations (bg-angle, aurora-hue, shine-color), glass morphism tokens, prefers-reduced-motion block, color-mix() utilities, and 3 palette variants (neon/minimal/warm). All web-* skills reference these tokens as layer-0 foundation. Output: 3 copy-paste files (tokens.css, reset.css, fonts.html). Theme overrides via .theme-light class or data-palette attribute.
disable-model-invocation: true
user-invocable: true
argument-hint: "[theme:dark|light] [palette:neon|minimal|warm]"
---

## Usage

### Quick start (default dark/neon)

```
/web-design-tokens
```

Copy the three output files into your project's `css/` directory, then reference them in order:

```html
<!-- In <head> — copy from references/fonts.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&family=Noto+Sans+KR:wght@100..900&display=swap" rel="stylesheet">

<link rel="stylesheet" href="css/tokens.css">
<link rel="stylesheet" href="css/reset.css">
<!-- your template CSS comes after -->
```

### With options

```
/web-design-tokens theme:light palette:minimal
```

Apply the variant by adding the appropriate attribute:

```html
<!-- Light theme -->
<html class="theme-light">

<!-- Warm palette -->
<body data-palette="warm">
```

---

## Token Reference

### Colors

| Token | Value | oklch | Usage |
|-------|-------|-------|-------|
| `--bg-deep` | `#0a0a1e` | `oklch(9% 0.03 265)` | Page background |
| `--bg-surface` | `rgba(17,25,40,0.75)` | — | Elevated surface |
| `--neon-cyan` | `#00ffff` | `oklch(91% 0.19 194)` | Primary accent |
| `--neon-magenta` | `#ff00ff` | `oklch(70% 0.32 302)` | Secondary accent |
| `--neon-green` | `#2ecc71` | `oklch(75% 0.20 142)` | Success / positive |
| `--neon-purple` | `#bc13fe` | `oklch(58% 0.28 300)` | Decorative / orb |
| `--text-primary` | `#ecf0f1` | — | Body text |
| `--text-secondary` | `rgba(255,255,255,0.7)` | — | Secondary text |

### Glass morphism

| Token | Value | Usage |
|-------|-------|-------|
| `--glass-bg` | `rgba(17,25,40,0.75)` | Glass card fill |
| `--glass-bg-solid` | `rgba(10,10,30,0.92)` | Solid glass (animated border) |
| `--glass-border` | `rgba(255,255,255,0.125)` | Card border |
| `--glass-blur` | `blur(16px) saturate(180%)` | `backdrop-filter` value |
| `--neon-cyan-glass` | `color-mix(in oklch, cyan 15%, transparent)` | Tinted fill |
| `--neon-cyan-border` | `color-mix(in oklch, cyan 40%, transparent)` | Glowing border |

### Typography

| Token | Value |
|-------|-------|
| `--font-heading` | `'Inter', 'Noto Sans KR', sans-serif` |
| `--font-body` | `'Noto Sans KR', 'Inter', sans-serif` |
| `--font-mono` | `'Courier New', 'Consolas', monospace` |

### Spacing

| Token | px | Token | px |
|-------|----|-------|----|
| `--space-xs` | 4 | `--space-xl` | 32 |
| `--space-sm` | 8 | `--space-2xl` | 48 |
| `--space-md` | 16 | `--space-3xl` | 64 |
| `--space-lg` | 24 | `--space-section` | 96 |

### Animation

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-smooth` | `cubic-bezier(0.4, 0, 0.2, 1)` | Standard transitions |
| `--ease-bounce` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Spring-like reveal |
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | Fast deceleration |
| `--duration-fast` | `200ms` | Hover / micro |
| `--duration-normal` | `400ms` | Panel / card |
| `--duration-slow` | `800ms` | Page-level |
| `--duration-reveal` | `1200ms` | Hero entrance |

### @property registrations (Baseline 2025)

```css
@property --bg-angle    { syntax: "<angle>";  initial-value: 0deg;                   inherits: false; }
@property --aurora-hue  { syntax: "<angle>";  initial-value: 0deg;                   inherits: false; }
@property --glow-intensity { syntax: "<number>"; initial-value: 0.3;               inherits: false; }
@property --shine-color { syntax: "<color>";  initial-value: oklch(70% 0.3 240);   inherits: false; }
```

These enable gradient animation via CSS `transition` and `animation` — without @property, gradient transitions snap rather than interpolate.

---

## Theme Customization

### Switching to light theme

```css
/* Override at runtime by toggling class */
document.documentElement.classList.toggle('theme-light');
```

The `.theme-light` block in `tokens.css` inverts background and text tokens. Neon accent colors remain unchanged by default — override separately if needed.

### Switching palette

```js
document.body.dataset.palette = 'warm'; // 'minimal' | 'warm' | '' (default neon)
```

### Creating a custom palette

```css
/* In your own CSS, after importing tokens.css */
[data-palette="corporate"] {
  --neon-cyan:    #0078d4;   /* Microsoft blue */
  --neon-magenta: #8764b8;
  --neon-green:   #107c10;
  --neon-purple:  #5c2d91;
}
```

---

## Integration with other web-* skills

All web-* template skills assume `tokens.css` and `reset.css` are already loaded. They reference tokens directly:

```css
/* Example from web-glass-card */
.card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: var(--glass-blur);
  border-radius: var(--radius-md);
  transition: transform var(--duration-normal) var(--ease-smooth);
}
```

**Load order requirement:**
```
fonts.html → tokens.css → reset.css → [template skill CSS] → [page CSS]
```

---

## Accessibility

`reset.css` includes:

- `@media (prefers-reduced-motion: reduce)` — disables all animations globally
- `.sr-only` utility class for screen-reader-only text
- `:focus-visible` ring using `--neon-cyan` for keyboard navigation
- `color-scheme: dark light` meta tag in `fonts.html`

> **Note**: Always test color contrast against WCAG AA (4.5:1 for normal text). The neon palette at full opacity on `--bg-deep` exceeds AA, but glass overlay variants may reduce contrast — verify with a contrast checker.

---

## Pre-built components in tokens.css

`tokens.css` ships three ready-to-use component classes:

| Class | Description |
|-------|-------------|
| `.glass-card` | Animated conic-gradient rotating border (uses `--bg-angle`) |
| `.glass-card-static` | Static glass without animation (lower GPU cost) |
| `.glass-card-cyan` | Cyan-tinted glass with glow shadow |
| `.aurora-bg` | Fixed background aurora animation (oklch + `--aurora-hue`) |

Add `aria-hidden="true"` on `.aurora-bg` since it is decorative.
