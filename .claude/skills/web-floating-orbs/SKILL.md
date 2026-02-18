---
name: web-floating-orbs
description: "[Atom·WebDesign·Ambient] Provides floating background orbs with radial gradients, blur filter, and CSS keyframe animations for ambient visual effect. Optional JS for mouse parallax response. Multiple orb configurations: purple, cyan, magenta. Use as page background decoration. pointer-events:none, z-index:-1. References web-design-tokens for colors."
user-invocable: true
argument-hint: "[count:2|3|4] [parallax:true|false] [colors:neon|subtle|custom]"
---

## Execution Model

Atom-level. Lead-direct. No subagents. User copy-pastes 3–4 reference files into their project.

## Usage

### 1. Prerequisites

Include `web-design-tokens` first:
```html
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="floating-orbs.css">
```

### 2. HTML Structure

Copy `references/floating-orbs.html`. Place as first child of `<body>`, before all content.
The `aria-hidden="true"` attribute is required for accessibility.

**Parallax mode:** add `data-parallax="true"` to `.bg-orbs`:
```html
<div class="bg-orbs" data-parallax="true" aria-hidden="true">
```

### 3. CSS

Copy `references/floating-orbs.css`. Uses these design tokens:
- `--neon-purple` — orb 1 color
- `--neon-cyan` — orb 2 color
- `--neon-magenta` — orb 3 color

### 4. JavaScript (optional — parallax only)

Copy `references/floating-orbs.js` only when using `data-parallax="true"`.
Uses WAAPI for hardware-accelerated transforms. Respects `prefers-reduced-motion`.

## Orb Configuration

| Orb | Token | Size | Position | Duration |
|-----|-------|------|----------|----------|
| `bg-orb--1` | `--neon-purple` | 600×600px | Top-left (-5%) | 20s |
| `bg-orb--2` | `--neon-cyan` | 500×500px | Center-right (-8%) | 24s |
| `bg-orb--3` | `--neon-magenta` | 400×400px | Bottom-center (20%) | 22s |

**Count variants:**
- 2 orbs: add `bg-orbs--2` class to container (hides `orb--3`)
- 4 orbs: add `.bg-orb--4` manually with custom `background` and `animation`

## Parallax Mode

Mouse movement creates subtle depth via WAAPI transforms (hardware-accelerated, off-thread).
Depth multipliers: orb-1 = 0.015 (least), orb-2 = 0.025, orb-3 = 0.035 (most).
Automatically disabled when `prefers-reduced-motion: reduce` is set.

## Performance Notes

- `pointer-events: none` — zero interaction overhead
- `z-index: -1` — renders behind all content, no stacking impact
- `blur(100px)` is GPU-composited via filter — no CPU cost
- For low-end devices: reduce to `blur(60px)` or lower opacity to `0.15`
- WAAPI animations are composited off the main thread

## Quality Gate
- [ ] `aria-hidden="true"` on `.bg-orbs` container
- [ ] `pointer-events: none` and `z-index: -1` present
- [ ] Token `var()` references used (not hardcoded hex)
- [ ] `@media (prefers-reduced-motion: reduce)` pauses all animations
- [ ] JS parallax respects `prefers-reduced-motion` check

## Output

4 files: `SKILL.md` + `references/floating-orbs.html` + `references/floating-orbs.css` + `references/floating-orbs.js`
