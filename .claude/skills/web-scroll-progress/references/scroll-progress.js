/**
 * web-scroll-progress — scroll-progress.js
 * JS fallback for scroll progress bar.
 *
 * Only activates when CSS scroll-driven animation is NOT supported
 * (Firefox as of early 2026). Silently exits in Chrome/Edge/Safari.
 *
 * Features:
 * - CSS.supports() guard: zero overhead in modern browsers
 * - Passive scroll listener: no blocking of main thread
 * - Sets width% on #scroll-progress element
 *
 * Requirements:
 * - <div id="scroll-progress"> in the page (from scroll-progress.html)
 * - scroll-progress.css loaded (provides base styles)
 *
 * No dependencies. Self-contained IIFE.
 */

(function initScrollProgress() {
  'use strict';

  // Skip if CSS scroll-driven animation is supported (Chrome/Edge/Safari)
  if (CSS.supports('animation-timeline', 'scroll()')) return;

  const bar = document.getElementById('scroll-progress');
  if (!bar) return;

  function updateProgress() {
    const scrollTop = window.scrollY;
    const docHeight =
      document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    bar.style.width = pct + '%';

    // Update ARIA value for screen readers
    bar.setAttribute('aria-valuenow', Math.round(pct));
  }

  window.addEventListener('scroll', updateProgress, { passive: true });

  // Set initial value on load
  updateProgress();
})();
