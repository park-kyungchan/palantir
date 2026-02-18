---
name: web-hero-section
description: "[Organism·WebDesign·Hero] Generates full-viewport hero section with gradient animated title, subtitle, chip tags, scroll-down indicator, and floating orb background. Composes web-design-tokens + web-chip + web-floating-orbs atoms. Includes View Transitions API ready markup. Use as landing page entry point. References: hero-section.html, hero-section.css, hero-section.js."
user-invocable: true
argument-hint: "[title:text] [subtitle:text] [chips:comma,separated] [scroll-indicator:true|false]"
---

# web-hero-section

Organism-level full-viewport hero section. Composes three atoms: `web-design-tokens`
(colors/typography), `web-chip` (tag pills), `web-floating-orbs` (ambient background).
Provides staggered WAAPI entrance, View Transitions API naming, and a bouncing scroll
indicator.

## Prerequisites

Run `/web-design-tokens` first. Also run `/web-chip` and `/web-floating-orbs` for
the default composition.

## Structure

```
.hero-section
├── .bg-orbs (from web-floating-orbs — paste as first child)
│   ├── .bg-orb.bg-orb--1
│   ├── .bg-orb.bg-orb--2
│   └── .bg-orb.bg-orb--3
└── .hero-content
    ├── .hero-eyebrow           (optional label / company name)
    ├── h1.hero-title           (gradient animated headline)
    ├── p.hero-subtitle         (supporting text)
    ├── .hero-chips             (chip tag row — compose web-chip)
    │   └── .chip (×N)
    └── .hero-cta               (optional CTA buttons)
.hero-scroll-indicator          (bounce animation — absolute bottom)
```

## Entrance Animation Sequence (WAAPI)

1. **t=0ms**: `.hero-eyebrow` fades up (translateY 10→0, opacity 0→1)
2. **t=100ms**: `.hero-title` fades up with gradient visible
3. **t=250ms**: `.hero-subtitle` fades up
4. **t=420ms**: `.hero-chips` container fades in, children stagger (60ms each)
5. **t=ctaDelay**: `.hero-cta` fades up
6. **After CTA**: `.hero-scroll-indicator` fades in + bounce begins
7. **`prefers-reduced-motion`**: All entrances skipped — elements already visible

## View Transitions API

The hero title carries `view-transition-name: hero-title`. Named elements morph
automatically when navigating with `document.startViewTransition()`:

```javascript
link.addEventListener('click', e => {
  e.preventDefault();
  document.startViewTransition(() => {
    window.location.href = link.href;
  });
});
```

## Background Integration

Paste `.bg-orbs` from `/web-floating-orbs` as first child of `.hero-section`.
Add `data-parallax="true"` for mouse parallax (requires `floating-orbs.js`).

## Responsive Behavior

- Title: `clamp(2.2rem, 5vw, 3.5rem)` — fluid scaling mobile to desktop
- Subtitle: `max-width: 600px`, centered
- Chips: `flex-wrap` — reflows on narrow screens
- CTA: stacks vertically at `max-width: 480px`

## Variants

- `.hero-section--left` — left-aligns all content (default is centered)
- `.hero-section--dark` — explicit dark fallback for light-mode sites

## Customization

- Gradient colors via `--neon-cyan`, `--neon-magenta`, `--neon-green` tokens
- Remove `.hero-eyebrow` if no tagline needed
- Remove `.hero-scroll-indicator` if no scroll hint wanted
- Set `scroll-indicator: false` argument to skip indicator HTML
