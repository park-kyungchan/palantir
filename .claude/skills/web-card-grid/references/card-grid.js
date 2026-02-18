/**
 * web-card-grid — card-grid.js
 * IntersectionObserver fallback for card grid scroll-reveal (Firefox).
 *
 * This script ONLY activates when CSS scroll-driven animations are NOT supported
 * (Firefox as of early 2026). It silently exits in Chrome/Edge/Safari.
 *
 * Features:
 * - CSS.supports() guard: zero overhead in modern browsers
 * - Adds .card-grid--js-ready to activate hidden start states in CSS fallback
 * - IntersectionObserver adds .is-visible to each [data-grid-item] on intersection
 * - Sets --item-delay CSS var for per-item stagger within each observed row
 * - Respects prefers-reduced-motion (skip animation, reveal immediately)
 *
 * Requirements:
 * - card-grid.css loaded (provides .card-grid--js-ready and .is-visible styles)
 * - .card-grid[role="list"] with [data-grid-item] children present in DOM
 *
 * No dependencies. Self-contained IIFE.
 */

(function initCardGrid() {
  'use strict';

  // Exit if CSS scroll-driven animations are supported (Chrome/Edge/Safari).
  // These browsers handle reveal entirely in CSS — no JS needed.
  if (CSS.supports('animation-timeline', 'scroll()')) return;

  // Respect user's motion preference: reveal all items immediately, skip animation.
  const prefersReducedMotion =
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const grids = document.querySelectorAll('.card-grid');
  if (!grids.length) return;

  grids.forEach((grid) => {
    const items = grid.querySelectorAll('[data-grid-item]');
    if (!items.length) return;

    if (prefersReducedMotion) {
      // No animation: ensure all items are visible immediately
      items.forEach((item) => {
        item.classList.add('is-visible');
      });
      return;
    }

    // Add class that activates hidden start states in CSS
    grid.classList.add('card-grid--js-ready');

    // Determine the column count to calculate stagger delay per row position.
    // We re-read this on each observation to handle resize gracefully.
    function getColumnCount() {
      const gridStyle = getComputedStyle(grid);
      const cols = gridStyle.gridTemplateColumns.split(' ').length;
      return cols || 1;
    }

    // Track which items have been revealed (avoid re-animating on re-intersection)
    const revealed = new WeakSet();

    // We observe items in a single shared observer for efficiency.
    // When an item enters the viewport, we reveal it with a stagger delay
    // based on its column position within the current row.
    const observer = new IntersectionObserver(
      (entries) => {
        // Group entries by their approximate vertical position (row grouping)
        // to calculate per-row column index for stagger.
        const entering = entries.filter(
          (e) => e.isIntersecting && !revealed.has(e.target)
        );
        if (!entering.length) return;

        const colCount = getColumnCount();
        const rowMap = new Map(); // rowTop → [{item, colIndex}]

        entering.forEach((entry) => {
          const rect = entry.boundingClientRect;
          // Round to nearest 4px to group items in the same visual row
          const rowKey = Math.round(rect.top / 4) * 4;
          if (!rowMap.has(rowKey)) rowMap.set(rowKey, []);
          rowMap.get(rowKey).push(entry.target);
        });

        // For each row group, assign column-based stagger delays
        rowMap.forEach((rowItems) => {
          rowItems.forEach((item, i) => {
            const colIndex = i % colCount;
            item.style.setProperty('--item-delay', `${colIndex * 80}ms`);
            item.classList.add('is-visible');
            revealed.add(item);
            observer.unobserve(item); // Stop observing once revealed
          });
        });
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    items.forEach((item) => observer.observe(item));
  });
})();
