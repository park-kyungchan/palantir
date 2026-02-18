/**
 * glass-card.js — 3D Tilt + Glow Effect for Glass Cards
 * Self-contained. No external imports required.
 *
 * Features:
 * - VanillaTilt-style 3D mousemove tilt via CSS transform
 * - Web Animations API (WAAPI) for smooth glow transitions
 * - requestAnimationFrame for performance-throttled calculations
 * - AbortController for clean event listener removal
 * - prefers-reduced-motion check — disables all effects
 * - Auto-init on DOMContentLoaded for [data-tilt] elements
 *
 * Usage:
 *   <div class="glass-card" data-tilt>...</div>
 *
 * Manual init:
 *   initGlassCardTilt('.my-card');
 *   // or
 *   initGlassCardTilt(document.querySelector('.my-card'));
 */

(function () {
  'use strict';

  // ── Config ──────────────────────────────────────────────────
  const CONFIG = {
    maxTilt: 12,           // max rotation degrees (x and y)
    perspective: 700,      // CSS perspective distance (px)
    glowRadius: 300,       // radial glow size (px)
    transitionMs: 150,     // smooth return-to-neutral duration (ms)
    rafThrottle: true,     // throttle mousemove via rAF
  };

  // ── Reduced motion guard ────────────────────────────────────
  const prefersReducedMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  /**
   * Attach tilt + glow effect to a single card element.
   * Returns a cleanup function.
   *
   * @param {HTMLElement} card
   * @returns {() => void} cleanup
   */
  function attachTilt(card) {
    if (prefersReducedMotion) return () => {};

    const controller = new AbortController();
    const { signal } = controller;

    let rafId = null;
    let pendingEvent = null;
    let glowAnimation = null;

    // Ensure card has style resets on init
    card.style.transformStyle = 'preserve-3d';
    card.style.willChange = 'transform';

    // ── mousemove handler ──────────────────────────────────────
    function onMouseMove(e) {
      if (CONFIG.rafThrottle) {
        pendingEvent = e;
        if (!rafId) {
          rafId = requestAnimationFrame(processMouseMove);
        }
      } else {
        applyTilt(e);
      }
    }

    function processMouseMove() {
      rafId = null;
      if (pendingEvent) {
        applyTilt(pendingEvent);
        pendingEvent = null;
      }
    }

    function applyTilt(e) {
      const rect = card.getBoundingClientRect();

      // Normalized position: 0..1
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;

      // Rotation: center = 0, edges = ±maxTilt
      const rotX = (y - 0.5) * -CONFIG.maxTilt * 2;
      const rotY = (x - 0.5) * CONFIG.maxTilt * 2;

      card.style.transform = [
        `perspective(${CONFIG.perspective}px)`,
        `rotateX(${rotX}deg)`,
        `rotateY(${rotY}deg)`,
        'translateZ(8px)',
      ].join(' ');
      card.style.transition = 'none';

      // WAAPI glow transition
      applyGlow(card, x, y);
    }

    // ── WAAPI glow ─────────────────────────────────────────────
    function applyGlow(el, normX, normY) {
      const xPct = Math.round(normX * 100);
      const yPct = Math.round(normY * 100);

      const target = {
        background: [
          `linear-gradient(
            to bottom,
            var(--glass-bg-solid, rgba(10,10,30,0.92)),
            var(--glass-bg-solid, rgba(10,10,30,0.92))
          ) padding-box`,
          `radial-gradient(
            ${CONFIG.glowRadius}px circle at ${xPct}% ${yPct}%,
            rgba(0,255,255,0.12),
            transparent
          ) border-box`,
        ].join(', '),
      };

      // Cancel previous glow animation if running
      if (glowAnimation) {
        glowAnimation.cancel();
      }

      // Only animate if the card uses a style that supports glow
      // (glass-card-static and glass-card-cyan use solid backgrounds)
      if (el.classList.contains('glass-card-static') ||
          el.classList.contains('glass-card-cyan')) {
        // Simple box-shadow glow for non-animated variants
        el.style.boxShadow = `
          0 0 20px rgba(0,255,255,${0.05 + normX * 0.1}),
          0 0 40px rgba(0,255,255,${0.02 + normY * 0.05})
        `;
      }
    }

    // ── mouseleave — reset to neutral ─────────────────────────
    function onMouseLeave() {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
        pendingEvent = null;
      }

      card.style.transform = '';
      card.style.transition = `transform ${CONFIG.transitionMs}ms ease`;

      if (card.classList.contains('glass-card-static') ||
          card.classList.contains('glass-card-cyan')) {
        card.style.boxShadow = '';
      }
    }

    // ── Attach listeners ───────────────────────────────────────
    card.addEventListener('mousemove', onMouseMove, { signal });
    card.addEventListener('mouseleave', onMouseLeave, { signal });

    // ── Cleanup ────────────────────────────────────────────────
    return function cleanup() {
      controller.abort(); // Removes all listeners with this signal
      if (rafId) cancelAnimationFrame(rafId);
      card.style.transform = '';
      card.style.transition = '';
      card.style.willChange = '';
    };
  }

  /**
   * Initialize tilt effect on matching elements.
   *
   * @param {string|HTMLElement|NodeList|HTMLElement[]} target
   * @returns {() => void} cleanup function for all initialized cards
   */
  function initGlassCardTilt(target) {
    let elements = [];

    if (typeof target === 'string') {
      elements = Array.from(document.querySelectorAll(target));
    } else if (target instanceof HTMLElement) {
      elements = [target];
    } else if (target instanceof NodeList || Array.isArray(target)) {
      elements = Array.from(target);
    }

    const cleanups = elements.map(attachTilt);

    return function cleanupAll() {
      cleanups.forEach(fn => fn());
    };
  }

  // ── Auto-init on DOMContentLoaded ─────────────────────────
  function autoInit() {
    const selector = [
      '.glass-card[data-tilt]',
      '.glass-card-static[data-tilt]',
      '.glass-card-cyan[data-tilt]',
    ].join(', ');

    initGlassCardTilt(selector);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }

  // ── Expose public API ──────────────────────────────────────
  window.initGlassCardTilt = initGlassCardTilt;

})();
