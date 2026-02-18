/**
 * chip.js — Optional Interactive Filter for Chip Components
 * Self-contained. No external imports required.
 *
 * Features:
 * - Click-to-toggle active state on chips within a filter group
 * - Event delegation — single listener per container
 * - Web Animations API (WAAPI) for smooth active transitions
 * - Custom event 'chipfilter' dispatched on filter change
 * - Multi-select mode via data-multi="true" on container
 * - prefers-reduced-motion respects user preference
 * - AbortController for cleanup
 *
 * Usage:
 *   <!-- Single-select (default) -->
 *   <div class="hero-chips" data-filter-group="category">
 *     <span class="chip chip--cyan chip--active" data-filter-value="all">All</span>
 *     <span class="chip" data-filter-value="math">Math</span>
 *   </div>
 *
 *   <!-- Multi-select -->
 *   <div class="hero-chips" data-filter-group="tags" data-multi="true">
 *     <span class="chip" data-filter-value="tag1">Tag 1</span>
 *     <span class="chip" data-filter-value="tag2">Tag 2</span>
 *   </div>
 *
 *   <!-- Listen for filter events -->
 *   document.querySelector('[data-filter-group="category"]')
 *     .addEventListener('chipfilter', (e) => {
 *       console.log(e.detail.value);    // string (single) or string[] (multi)
 *       console.log(e.detail.selected); // array of selected chips
 *     });
 */

(function () {
  'use strict';

  const prefersReducedMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  // ── WAAPI transition for active state ─────────────────────
  function animateChip(chip, toActive) {
    if (prefersReducedMotion) return;

    const keyframes = toActive
      ? [
          { opacity: 0.6, transform: 'scale(0.95)' },
          { opacity: 1,   transform: 'scale(1.04)' },
          { opacity: 1,   transform: 'scale(1)' },
        ]
      : [
          { opacity: 1,   transform: 'scale(1)' },
          { opacity: 0.7, transform: 'scale(0.97)' },
          { opacity: 1,   transform: 'scale(1)' },
        ];

    chip.animate(keyframes, {
      duration: 200,
      easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      fill: 'none',
    });
  }

  /**
   * Initialize a single filter group container.
   *
   * @param {HTMLElement} container
   * @returns {() => void} cleanup
   */
  function initFilterGroup(container) {
    const isMulti = container.dataset.multi === 'true';
    const controller = new AbortController();

    function onClick(e) {
      const chip = e.target.closest('[data-filter-value]');
      if (!chip || !container.contains(chip)) return;

      e.preventDefault();

      const allChips = Array.from(
        container.querySelectorAll('[data-filter-value]')
      );

      if (isMulti) {
        // Multi-select: toggle clicked chip
        const wasActive = chip.classList.contains('chip--active');
        animateChip(chip, !wasActive);
        chip.classList.toggle('chip--active');
      } else {
        // Single-select: deactivate others, activate clicked
        allChips.forEach(c => {
          if (c !== chip && c.classList.contains('chip--active')) {
            animateChip(c, false);
            c.classList.remove('chip--active');
          }
        });

        if (!chip.classList.contains('chip--active')) {
          animateChip(chip, true);
          chip.classList.add('chip--active');
        }
      }

      // Collect selected values
      const selected = allChips.filter(c =>
        c.classList.contains('chip--active')
      );
      const values = selected.map(c => c.dataset.filterValue);

      // Dispatch custom event
      container.dispatchEvent(
        new CustomEvent('chipfilter', {
          bubbles: true,
          detail: {
            value: isMulti ? values : (values[0] || null),
            selected,
            group: container.dataset.filterGroup,
          },
        })
      );
    }

    container.addEventListener('click', onClick, { signal: controller.signal });

    // Keyboard support: Enter / Space activate chip
    container.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        const chip = e.target.closest('[data-filter-value]');
        if (chip) {
          e.preventDefault();
          chip.click();
        }
      }
    }, { signal: controller.signal });

    // Set initial ARIA role on chips
    container.querySelectorAll('[data-filter-value]').forEach(chip => {
      chip.setAttribute('role', isMulti ? 'checkbox' : 'radio');
      chip.setAttribute('tabindex', '0');
      chip.setAttribute(
        'aria-checked',
        chip.classList.contains('chip--active') ? 'true' : 'false'
      );
    });

    // Update aria-checked when chip--active changes
    // (MutationObserver for dynamic updates)
    const mutObs = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.type === 'attributes' &&
            mutation.attributeName === 'class') {
          const el = mutation.target;
          if (el.hasAttribute('data-filter-value')) {
            el.setAttribute(
              'aria-checked',
              el.classList.contains('chip--active') ? 'true' : 'false'
            );
          }
        }
      });
    });

    mutObs.observe(container, {
      attributes: true,
      attributeFilter: ['class'],
      subtree: true,
    });

    return function cleanup() {
      controller.abort();
      mutObs.disconnect();
    };
  }

  /**
   * Initialize all filter groups on the page.
   * @returns {() => void} cleanup for all groups
   */
  function initChipFilters() {
    const containers = Array.from(
      document.querySelectorAll('[data-filter-group]')
    );
    const cleanups = containers.map(initFilterGroup);

    return function cleanupAll() {
      cleanups.forEach(fn => fn());
    };
  }

  // ── Auto-init ──────────────────────────────────────────────
  function autoInit() {
    initChipFilters();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }

  // ── Public API ─────────────────────────────────────────────
  window.initChipFilters = initChipFilters;
  window.initFilterGroup = initFilterGroup;

})();
