---
name: web-pipeline-steps
description: "[Organism·WebDesign·Workflow] Renders a vertical numbered step card sequence with scroll-entrance animation, domain color-coding, and optional spotlight mode. Composes web-design-tokens + web-glass-card. Step headers show numbered badge (cyan/magenta/green by domain) + skill name + optional parallel badge. IntersectionObserver drives staggered translateY reveal; spotlight tracks active card during scroll. Use for pipeline diagrams, process walkthroughs, or methodology displays. References: portfolio.html"
disable-model-invocation: true
user-invocable: true
argument-hint: "[steps:json] [domain:d0|d1|d2] [spotlight:true|false] [animate:true|false]"
---

# web-pipeline-steps — Organism Usage Guide

Vertical numbered step card sequence with scroll-driven entrance animation, domain color badges, optional parallel markers, and an optional spotlight mode that highlights the active card during scroll. Composes `web-design-tokens` (foundation) and `web-glass-card` (atom).

---

## Prerequisites

Load in this order before `pipeline-steps.css`:

```html
<link rel="stylesheet" href="tokens.css">           <!-- web-design-tokens -->
<link rel="stylesheet" href="glass-card.css">        <!-- web-glass-card -->
<link rel="stylesheet" href="pipeline-steps.css">    <!-- this skill -->
<script defer src="pipeline-steps.js"></script>
```

---

## Structure

```
ol.pipeline-steps                        ← semantic ordered list, flex column
  li.step-card                           ← glass-card-static, scroll-reveal host
    .step-header                         ← flex row: badge + name + optional parallel badge
      .step-number.d0|.d1|.d2           ← 32 px circle, domain-colored
      .step-skill-name                   ← bold heading, neon-cyan
      .step-parallel-badge  (optional)   ← magenta pill "PARALLEL"
    .step-body                           ← description text
      p                                  ← prose content
      table  (optional)                  ← input/output data table
        thead > tr > th
        tbody > tr > td
      ol.step-sub-steps  (optional)      ← nested sub-steps
        li
```

---

## HTML Template

```html
<ol class="pipeline-steps" id="pipeline-steps"
    data-animate="true"
    data-spotlight="false"
    aria-label="Process steps">

  <!-- Step 1: d0 domain (cyan) -->
  <li class="step-card" data-step="1">
    <div class="step-header">
      <span class="step-number d0" aria-hidden="true">1</span>
      <span class="step-skill-name">Pre-Design: Brainstorm</span>
    </div>
    <div class="step-body">
      <p>Expand requirements through structured divergent thinking. Surface all constraints, risks, and open questions before committing to any architecture.</p>
      <table>
        <thead>
          <tr><th>Input</th><th>Output</th></tr>
        </thead>
        <tbody>
          <tr><td>User request, project context</td><td>Requirement list, open questions</td></tr>
        </tbody>
      </table>
    </div>
  </li>

  <!-- Step 2: d1 domain (magenta), with PARALLEL badge -->
  <li class="step-card" data-step="2">
    <div class="step-header">
      <span class="step-number d1" aria-hidden="true">2</span>
      <span class="step-skill-name">Research: Codebase + External</span>
      <span class="step-parallel-badge" aria-label="Runs in parallel">PARALLEL</span>
    </div>
    <div class="step-body">
      <p>Run codebase audit and external research concurrently. Fan-out to two subagents; Lead synthesizes results.</p>
      <ol class="step-sub-steps">
        <li>Codebase: file map, dependency graph, entry points</li>
        <li>External: library versions, API contracts, community guidance</li>
      </ol>
    </div>
  </li>

  <!-- Step 3: d2 domain (green) -->
  <li class="step-card" data-step="3">
    <div class="step-header">
      <span class="step-number d2" aria-hidden="true">3</span>
      <span class="step-skill-name">Execution: Code</span>
    </div>
    <div class="step-body">
      <p>Implement changes atomically. Each commit closes exactly one task. Pre-commit hooks enforce quality backpressure.</p>
    </div>
  </li>

</ol>
```

---

## CSS Template

```css
/* ── pipeline-steps.css ── */

/* Container */
.pipeline-steps {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Step card — extends glass-card-static */
.step-card {
  /* glass-card-static supplies: background, border, border-radius, backdrop-filter */
  padding: 1.5rem 2rem;
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s var(--ease-out, ease-out),
              transform 0.6s var(--ease-out, ease-out);
}

/* Stagger children (JS sets --stagger-index via data-step attribute) */
.step-card.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Spotlight: dim non-active cards when spotlight mode is on */
.pipeline-steps.spotlight-active .step-card:not(.spotlight-on) {
  opacity: 0.4;
  transition: opacity 0.4s ease;
}

.pipeline-steps.spotlight-active .step-card.spotlight-on {
  opacity: 1;
  box-shadow: 0 0 0 2px var(--neon-cyan, oklch(90% 0.18 195));
}

/* Header row */
.step-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

/* Numbered badge */
.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-family: var(--font-heading, sans-serif);
  font-size: 0.85rem;
  font-weight: 700;
  flex-shrink: 0;
}

/* Domain color variants */
.step-number.d0 {
  background-color: oklch(from var(--neon-cyan, oklch(90% 0.18 195)) l c h / 0.15);
  color: var(--neon-cyan, oklch(90% 0.18 195));
  border: 1px solid var(--neon-cyan, oklch(90% 0.18 195));
}

.step-number.d1 {
  background-color: oklch(from var(--neon-magenta, oklch(75% 0.25 330)) l c h / 0.15);
  color: var(--neon-magenta, oklch(75% 0.25 330));
  border: 1px solid var(--neon-magenta, oklch(75% 0.25 330));
}

.step-number.d2 {
  background-color: oklch(from var(--neon-green, oklch(80% 0.20 145)) l c h / 0.15);
  color: var(--neon-green, oklch(80% 0.20 145));
  border: 1px solid var(--neon-green, oklch(80% 0.20 145));
}

/* Skill name label */
.step-skill-name {
  font-family: var(--font-heading, sans-serif);
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--neon-cyan, oklch(90% 0.18 195));
  line-height: 1.2;
}

/* Parallel badge */
.step-parallel-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2em 0.6em;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  background-color: oklch(from var(--neon-magenta, oklch(75% 0.25 330)) l c h / 0.2);
  color: var(--neon-magenta, oklch(75% 0.25 330));
  border: 1px solid oklch(from var(--neon-magenta, oklch(75% 0.25 330)) l c h / 0.4);
}

/* Step body text */
.step-body {
  font-size: 0.85rem;
  color: var(--text-secondary, oklch(70% 0 0));
  line-height: 1.7;
}

.step-body p {
  margin: 0 0 0.75rem;
}

.step-body p:last-child {
  margin-bottom: 0;
}

/* Input/output table */
.step-body table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
  margin-top: 0.5rem;
}

.step-body table th,
.step-body table td {
  padding: 0.35rem 0.6rem;
  border: 1px solid var(--glass-border, oklch(100% 0 0 / 0.1));
  text-align: left;
}

.step-body table th {
  background-color: oklch(from var(--neon-cyan, oklch(90% 0.18 195)) l c h / 0.08);
  color: var(--neon-cyan, oklch(90% 0.18 195));
  font-weight: 600;
}

/* Nested sub-steps */
.step-sub-steps {
  margin: 0.5rem 0 0 1rem;
  padding: 0;
  list-style: decimal;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.step-sub-steps li {
  padding-left: 0.25rem;
}

/* ── Responsive ── */
@media (max-width: 480px) {
  .step-card {
    padding: 1rem 1.25rem;
  }

  .step-body {
    font-size: 0.8rem;
  }
}
```

---

## JS Template

```js
/* ── pipeline-steps.js ── */

(function PipelineSteps() {
  'use strict';

  const container = document.getElementById('pipeline-steps');
  if (!container) return;

  const animate   = container.dataset.animate   !== 'false';
  const spotlight = container.dataset.spotlight === 'true';

  const cards = Array.from(container.querySelectorAll('.step-card'));

  // ── Stagger delays (set CSS variable for transition-delay) ──
  cards.forEach((card, i) => {
    card.style.transitionDelay = `${i * 0.1}s`;
  });

  // ── Scroll-entrance: IntersectionObserver ──
  if (animate) {
    const entranceObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            entranceObserver.unobserve(entry.target); // fire once
          }
        });
      },
      { threshold: 0.15 }
    );
    cards.forEach((card) => entranceObserver.observe(card));
  } else {
    // animate=false: make all cards visible immediately
    cards.forEach((card) => card.classList.add('visible'));
  }

  // ── Spotlight mode: highlight the card most in view ──
  if (spotlight) {
    container.classList.add('spotlight-active');

    const spotlightObserver = new IntersectionObserver(
      (entries) => {
        let maxRatio = 0;
        let topCard  = null;

        // Find the card with the highest intersection ratio
        cards.forEach((card) => {
          const ratio = card._intersectionRatio ?? 0;
          if (ratio > maxRatio) {
            maxRatio = ratio;
            topCard  = card;
          }
        });

        if (topCard) {
          cards.forEach((c) => c.classList.remove('spotlight-on'));
          topCard.classList.add('spotlight-on');

          // Dispatch custom event for cross-component coordination
          container.dispatchEvent(
            new CustomEvent('pipelinestep:spotlight', {
              bubbles: true,
              detail: {
                step:    topCard.dataset.step,
                element: topCard,
              },
            })
          );
        }
      },
      {
        threshold: [0, 0.25, 0.5, 0.75, 1.0],
      }
    );

    // Track ratio per card via individual observers
    cards.forEach((card) => {
      const tracker = new IntersectionObserver(
        ([entry]) => { card._intersectionRatio = entry.intersectionRatio; },
        { threshold: [0, 0.1, 0.25, 0.5, 0.75, 1.0] }
      );
      tracker.observe(card);
      spotlightObserver.observe(card);
    });
  }

  // ── Public API ──
  window.PipelineSteps = {
    /**
     * Programmatically activate spotlight on a step by index (1-based) or element.
     * @param {number|HTMLElement} target
     */
    spotlight(target) {
      cards.forEach((c) => c.classList.remove('spotlight-on'));
      const card =
        typeof target === 'number'
          ? cards.find((c) => c.dataset.step === String(target))
          : target;
      if (card) card.classList.add('spotlight-on');
    },

    /** Clear all spotlight and entrance state. */
    reset() {
      cards.forEach((c) => {
        c.classList.remove('visible', 'spotlight-on');
      });
    },
  };
})();
```

---

## Data Attributes

| Attribute | Element | Values | Description |
|-----------|---------|--------|-------------|
| `data-animate` | `ol.pipeline-steps` | `true` (default) / `false` | Enable IntersectionObserver scroll entrance |
| `data-spotlight` | `ol.pipeline-steps` | `true` / `false` (default) | Enable spotlight tracking mode |
| `data-step` | `li.step-card` | integer string (`"1"`, `"2"`, …) | Step index; used by public API and custom event |

---

## Domain Color Reference

| Class | Color Token | Visual |
|-------|-------------|--------|
| `.d0` | `--neon-cyan` | Cyan badge — D0 foundation / pre-design domain |
| `.d1` | `--neon-magenta` | Magenta badge — D1 drill / execution domain |
| `.d2` | `--neon-green` | Green badge — D2 evaluation / delivery domain |

Add more variants by extending `.step-number.dN` with additional color tokens from `web-design-tokens`.

---

## Customization Guide

### Change gap between cards

```css
.pipeline-steps { gap: 3rem; }
```

### Disable stagger delay

Remove the `transitionDelay` assignment in the JS, or set it to `0s`:

```css
.step-card { transition-delay: 0s !important; }
```

### Adjust entrance threshold

Pass a higher `threshold` (e.g., `0.3`) to `entranceObserver` to trigger the reveal later in the scroll.

### Link spotlight to a side panel

```js
document.getElementById('pipeline-steps').addEventListener('pipelinestep:spotlight', (e) => {
  const { step } = e.detail;
  document.querySelectorAll('.detail-panel').forEach((p) => {
    p.hidden = p.dataset.step !== step;
  });
});
```

### Add a new domain color

```css
.step-number.d3 {
  background-color: oklch(from var(--neon-yellow, oklch(88% 0.18 95)) l c h / 0.15);
  color: var(--neon-yellow, oklch(88% 0.18 95));
  border: 1px solid var(--neon-yellow, oklch(88% 0.18 95));
}
```

---

## Composition Notes

- **web-design-tokens**: all `var(--neon-*)`, `var(--glass-border)`, `var(--font-heading)`, `var(--text-secondary)`, `var(--ease-out)` tokens
- **web-glass-card**: `.step-card` inherits `glass-card-static` background, backdrop-filter, and border-radius — this skill only adds padding and entrance animation
- **Cross-component**: `pipelinestep:spotlight` custom event allows coordination with `web-deep-dive` or any side panel without direct coupling
- **Accessibility**: uses `<ol>` (semantic ordered list) for step sequence; `aria-label` on the container; `aria-hidden` on decorative badge numbers; `aria-label` on the parallel badge; table markup with `<thead>` for screen readers
