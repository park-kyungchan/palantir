/**
 * progress-bar.js — Scroll-Triggered Progress Bar Animation
 * Self-contained. No external imports required.
 *
 * Features:
 * - IntersectionObserver triggers fill animation on scroll entry
 * - requestAnimationFrame animated percentage counter
 * - data-value, data-target, data-color, data-tag attribute config
 * - CSS Scroll-Driven Animation detection + graceful fallback
 * - Sets role="progressbar" + aria-valuenow for accessibility
 * - prefers-reduced-motion: shows final value immediately (no animation)
 * - Auto-init on DOMContentLoaded for .gap-row elements
 *
 * Usage:
 *   <div class="gap-row" data-value="75" data-color="cyan" data-tag="medium">
 *     <span class="gap-label">Label</span>
 *     <div class="gap-bar-track">
 *       <div class="gap-bar-fill cyan" style="width:0%"></div>
 *       <span class="gap-bar-pct">0%</span>
 *     </div>
 *     <span class="gap-tag medium">보통</span>
 *   </div>
 *
 *   <script src="progress-bar.js"></script>
 */

(function () {
  'use strict';

  const prefersReducedMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  // ── CSS Scroll-Driven Animation support detection ──────────
  const supportsScrollDriven = CSS.supports('animation-timeline', 'scroll()');

  // ── Duration for counter animation (ms) ───────────────────
  const COUNTER_DURATION = prefersReducedMotion ? 0 : 1200;

  /**
   * Animate a number from start to end over duration ms.
   * Updates the display element and aria-valuenow.
   *
   * @param {HTMLElement} row — .gap-row (for aria)
   * @param {HTMLElement} pctEl — .gap-bar-pct span
   * @param {number} start
   * @param {number} end
   * @param {number} duration
   */
  function animateCounter(row, pctEl, start, end, duration) {
    if (duration === 0) {
      pctEl.textContent = `${end}%`;
      row.setAttribute('aria-valuenow', end);
      return;
    }

    const startTime = performance.now();

    function step(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out-expo approximation
      const eased = progress === 1
        ? 1
        : 1 - Math.pow(2, -10 * progress);

      const current = Math.round(start + (end - start) * eased);
      pctEl.textContent = `${current}%`;
      row.setAttribute('aria-valuenow', current);

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }

    requestAnimationFrame(step);
  }

  /**
   * Trigger the fill animation for a single .gap-row.
   *
   * @param {HTMLElement} row
   */
  function triggerFill(row) {
    const value = parseInt(row.dataset.value || '0', 10);
    const fill = row.querySelector('.gap-bar-fill');
    const pctEl = row.querySelector('.gap-bar-pct');

    if (!fill) return;

    // Set CSS custom property for Scroll-Driven mode
    fill.style.setProperty('--bar-target-width', `${value}%`);

    if (prefersReducedMotion) {
      // Immediately show final state
      fill.style.width = `${value}%`;
      if (pctEl) pctEl.textContent = `${value}%`;
      row.setAttribute('aria-valuenow', value);
      return;
    }

    // Animate fill width (CSS transition handles the easing)
    requestAnimationFrame(() => {
      fill.style.width = `${value}%`;
    });

    // Animate counter
    if (pctEl) {
      animateCounter(row, pctEl, 0, value, COUNTER_DURATION);
    }

    row.setAttribute('aria-valuenow', value);
  }

  /**
   * Initialize a single .gap-row element:
   * - Set aria attributes
   * - Configure target line position
   * - Set up IO observation or immediate trigger
   *
   * @param {HTMLElement} row
   * @param {IntersectionObserver|null} observer
   */
  function initRow(row) {
    const value = parseInt(row.dataset.value || '0', 10);
    const target = row.dataset.target
      ? parseInt(row.dataset.target, 10)
      : null;

    // Accessibility attributes
    row.setAttribute('role', 'progressbar');
    row.setAttribute('aria-valuemin', '0');
    row.setAttribute('aria-valuemax', '100');
    row.setAttribute('aria-valuenow', '0');

    // Label from .gap-label text
    const labelEl = row.querySelector('.gap-label');
    if (labelEl && !row.hasAttribute('aria-label')) {
      row.setAttribute('aria-label', labelEl.textContent.trim());
    }

    // Position target line
    if (target !== null) {
      const targetEl = row.querySelector('.gap-bar-target');
      if (targetEl) {
        targetEl.style.left = `${target}%`;
      }
    } else {
      // Hide target line if no data-target
      const targetEl = row.querySelector('.gap-bar-target');
      if (targetEl) targetEl.style.display = 'none';
    }

    return value;
  }

  /**
   * Initialize the progress bar system for a container.
   *
   * @param {HTMLElement} container — .gap-matrix
   */
  function initProgressBars(container) {
    const rows = Array.from(container.querySelectorAll('.gap-row'));
    if (rows.length === 0) return;

    // Check if Scroll-Driven Animation mode is requested
    const useScrollDriven = container.dataset.scrollDriven === 'true' &&
                            supportsScrollDriven;

    if (useScrollDriven) {
      // Add class to activate CSS @keyframes + animation-timeline
      container.classList.add('scroll-driven');

      // Initialize row attributes but let CSS handle animation
      rows.forEach(row => {
        const value = initRow(row);
        const fill = row.querySelector('.gap-bar-fill');
        if (fill) {
          fill.style.setProperty('--bar-target-width', `${value}%`);
        }
      });
      return;
    }

    // IntersectionObserver mode (default / Firefox fallback)
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            triggerFill(entry.target);
            observer.unobserve(entry.target); // fire once
          }
        });
      },
      {
        threshold: 0.15,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    rows.forEach(row => {
      initRow(row);
      observer.observe(row);
    });
  }

  // ── Auto-init ──────────────────────────────────────────────
  function autoInit() {
    const containers = document.querySelectorAll('.gap-matrix');
    containers.forEach(initProgressBars);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }

  // ── Public API ─────────────────────────────────────────────
  window.initProgressBars = initProgressBars;
  window.triggerFill = triggerFill;

})();
