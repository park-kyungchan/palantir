---
name: web-deep-dive
description: "[Organism·WebDesign·Content] Generates a 4-level progressive accordion component with numbered badges, scroll-triggered entrance, and CSS expand/collapse transitions. Composes web-design-tokens. Click-to-deepen UX: L1 surface → L2 detail (cyan) → L3 evidence (cyan) → L4 action plan (magenta). IntersectionObserver drives lightOn reveal; ARIA and keyboard-accessible. Use for deep analysis panels, gap explanations, or layered content disclosure. References: portfolio.html."
user-invocable: true
argument-hint: "[items:json] [animate:true|false] [start-level:0|1]"
---

# web-deep-dive — Organism Usage Guide

Progressive accordion component: numbered cyan badges, 4-level expand/collapse, scroll-triggered entrance animation. Each item reveals deeper content layers (surface → detail → evidence → action plan) on successive clicks. Composes `web-design-tokens`.

---

## Prerequisites

Load in this order:

```html
<link rel="stylesheet" href="tokens.css">      <!-- web-design-tokens (required) -->
<link rel="stylesheet" href="deep-dive.css">   <!-- this skill -->
<script defer src="deep-dive.js"></script>
```

`web-design-tokens` must be loaded first — all CSS custom properties (`--neon-cyan`, `--neon-magenta`, `--bg-deep`, `--glass-border`, `--duration-slow`, `--ease-smooth`, `--text-secondary`) are resolved from the token sheet.

---

## Structure

```
.deep-dive-section                   ← optional wrapper
  .deep-dive-item[data-depth="0"]   ← one item per topic
    .deep-dive-item-header           ← clickable row (aria-expanded)
      .dive-badge                    ← numbered cyan circle
      .dive-title                    ← topic heading
    .dive-expand-level[data-level="1"]           ← L1: surface
      .dive-expand-content
    .dive-expand-level[data-level="2"]           ← L2: detail (cyan accent)
      .dive-expand-content
    .dive-expand-level[data-level="3"]           ← L3: evidence (cyan accent, darker)
      .dive-expand-content
    .dive-expand-level[data-level="4"]           ← L4: action plan (magenta accent)
      .dive-expand-content
```

---

## Data Attributes

| Attribute | Element | Values | Description |
|-----------|---------|--------|-------------|
| `data-depth` | `.deep-dive-item` | `0`–`4` | Current expand depth (managed by JS) |
| `data-level` | `.dive-expand-level` | `1`–`4` | Level identity for JS targeting |
| `data-label` | `.deep-dive-item` | string | Shared key for `GapMatrix.highlight()` cross-component linking |
| `data-animate` | `.deep-dive-section` | `true\|false` | Enable IntersectionObserver entrance (default: `true`) |

---

## HTML Template

```html
<section class="deep-dive-section" data-animate="true">

  <div class="deep-dive-item" data-depth="0" data-label="Topic A">
    <div class="deep-dive-item-header" role="button" tabindex="0"
         aria-expanded="false" aria-controls="dd-item-1-levels">
      <span class="dive-badge" aria-hidden="true">01</span>
      <span class="dive-title">Topic Title Here</span>
    </div>

    <div id="dd-item-1-levels">
      <div class="dive-expand-level" data-level="1">
        <div class="dive-expand-content">
          <p>L1 — Surface summary. One or two sentences capturing the key finding.</p>
        </div>
      </div>

      <div class="dive-expand-level" data-level="2">
        <div class="dive-expand-content l2">
          <p>L2 — Detailed analysis. Explain the mechanism or root cause.</p>
        </div>
      </div>

      <div class="dive-expand-level" data-level="3">
        <div class="dive-expand-content l3">
          <p>L3 — Evidence / data. Metrics, examples, citations.</p>
        </div>
      </div>

      <div class="dive-expand-level" data-level="4">
        <div class="dive-expand-content l4">
          <p>L4 — Action plan. <strong>Concrete next steps</strong> and owners.</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Repeat .deep-dive-item for each topic -->

</section>
```

---

## CSS Template

```css
/* ── Container ─────────────────────────────────────────────── */
.deep-dive-item {
  margin-bottom: 1.5rem;
  border-radius: 8px;
  overflow: hidden;
}

/* ── Header row ─────────────────────────────────────────────── */
.deep-dive-item-header {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  cursor: pointer;
  transition: background var(--duration-fast, 150ms) var(--ease-smooth);
}

.deep-dive-item-header:hover,
.deep-dive-item-header:focus-visible {
  background: rgba(255, 255, 255, 0.06);
  outline: 2px solid var(--neon-cyan);
  outline-offset: -2px;
}

/* ── Badge ───────────────────────────────────────────────────── */
.dive-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--neon-cyan);
  color: var(--bg-deep);
  font-family: var(--font-heading);
  font-size: 0.7rem;
  font-weight: 800;
  box-shadow: 0 0 12px rgba(0, 255, 255, 0.4);
}

/* ── Title ───────────────────────────────────────────────────── */
.dive-title {
  font-family: var(--font-heading);
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--neon-cyan);
}

/* ── Expand levels (collapsed default) ──────────────────────── */
.dive-expand-level {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  padding: 0 1rem;
  transition:
    max-height var(--duration-slow, 400ms) var(--ease-smooth),
    opacity    var(--duration-slow, 400ms) var(--ease-smooth);
}

.dive-expand-level.expanded {
  max-height: 500px;
  opacity: 1;
}

/* ── Shared content base ─────────────────────────────────────── */
.dive-expand-content {
  padding: 0.8rem 0;
  font-size: 0.82rem;
  line-height: 1.7;
  color: var(--text-secondary);
}

/* ── Level-specific accents ──────────────────────────────────── */
.dive-expand-content.l2 {
  border-left: 3px solid rgba(0, 255, 255, 0.15);
  padding-left: 1rem;
  background: rgba(0, 255, 255, 0.02);
  border-radius: 0 6px 6px 0;
}

.dive-expand-content.l3 {
  border-left: 3px solid rgba(0, 255, 255, 0.4);
  padding-left: 1rem;
  background: rgba(0, 255, 255, 0.03);
}

.dive-expand-content.l4 {
  border-left: 3px solid rgba(255, 0, 255, 0.4);
  padding-left: 1rem;
  background: rgba(255, 0, 255, 0.03);
}

/* L4 emphasis uses magenta instead of cyan */
.dive-expand-content.l4 strong {
  color: var(--neon-magenta);
}

/* ── Scroll-entrance animation ───────────────────────────────── */
.deep-dive-item {
  opacity: 0;
  transform: translateY(20px);
  transition:
    opacity  var(--duration-slow, 400ms) var(--ease-smooth),
    transform var(--duration-slow, 400ms) var(--ease-smooth);
}

.deep-dive-item.visible {
  opacity: 1;
  transform: translateY(0);
}

/* ── Reduced motion ──────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .dive-expand-level,
  .deep-dive-item {
    transition: none;
  }
}
```

---

## JS Template

```js
(function DeepDive() {
  'use strict';

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Entrance animation via IntersectionObserver ──────────── */
  function initEntranceObserver(section) {
    if (reducedMotion) {
      section.querySelectorAll('.deep-dive-item').forEach(el => el.classList.add('visible'));
      return;
    }
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    section.querySelectorAll('.deep-dive-item').forEach(el => obs.observe(el));
  }

  /* ── Expand levels 1..depth, collapse depth+1..4 ─────────── */
  function setDepth(item, targetDepth) {
    const levels = item.querySelectorAll('.dive-expand-level');
    levels.forEach(level => {
      const lvl = parseInt(level.dataset.level, 10);
      if (lvl <= targetDepth) {
        level.classList.add('expanded');
      } else {
        level.classList.remove('expanded');
      }
    });
    item.dataset.depth = targetDepth;

    const header = item.querySelector('.deep-dive-item-header');
    if (header) {
      header.setAttribute('aria-expanded', targetDepth > 0 ? 'true' : 'false');
    }
  }

  /* ── Click / keyboard handler ────────────────────────────── */
  function onActivate(item) {
    const current = parseInt(item.dataset.depth || '0', 10);
    const maxLevel = item.querySelectorAll('.dive-expand-level').length;
    // Cycle: 0 → 1 → 2 → ... → maxLevel → 0
    const next = current >= maxLevel ? 0 : current + 1;
    setDepth(item, next);
  }

  /* ── Init ─────────────────────────────────────────────────── */
  function init() {
    document.querySelectorAll('.deep-dive-section').forEach(section => {
      const animate = section.dataset.animate !== 'false';
      if (animate) initEntranceObserver(section);

      section.querySelectorAll('.deep-dive-item-header').forEach(header => {
        const item = header.closest('.deep-dive-item');

        header.addEventListener('click', () => onActivate(item));

        header.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onActivate(item);
          }
        });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
```

---

## Customization

| Goal | Change |
|------|--------|
| Start with L1 visible | Call `setDepth(item, 1)` after `init()` for desired items |
| Limit to 3 levels | Remove `.dive-expand-level[data-level="4"]` from HTML |
| Change badge color | Override `--neon-cyan` on `.dive-badge` or swap to `var(--neon-magenta)` |
| Animate entrance delay | Add `transition-delay` on each `.deep-dive-item` (e.g., `nth-child` stagger) |
| Link to gap matrix | Use `data-label` + `GapMatrix.highlight(item.dataset.label)` inside IntersectionObserver |
| Custom max-height | Override `max-height` on `.dive-expand-level.expanded` if content exceeds 500px |

---

## Accessibility

- `.deep-dive-item-header` has `role="button"`, `tabindex="0"`, and `aria-expanded` (updated by JS on each toggle)
- `aria-controls` links the header to the levels container (`id` on wrapper `<div>`)
- `aria-hidden="true"` on `.dive-badge` (decorative number, not semantic)
- Keyboard: `Enter` and `Space` activate the same cycle as click
- `prefers-reduced-motion`: transitions disabled; entrance animation skipped (items immediately `.visible`)

---

## Composition Notes

- **web-design-tokens**: all `var(--neon-*)`, `var(--glass-border)`, `var(--bg-deep)`, `var(--duration-slow)`, `var(--ease-smooth)`, `var(--text-secondary)` tokens
- **web-gap-matrix**: cross-link via `GapMatrix.highlight(label)` — observe `.deep-dive-item` with IntersectionObserver at `threshold: 0.5`, call highlight on entry
- No other atom dependencies; this organism is self-contained beyond the token foundation
