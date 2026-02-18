/**
 * web-icon-badge — icon-badge.js
 * Optional JS for entrance animation + cursor-follow glow
 * No external dependencies. Auto-initializes on DOMContentLoaded.
 */

const IconBadge = (() => {
  'use strict';

  /* ── Reduced motion detection ───────────────────────────────── */
  const prefersReducedMotion = () =>
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── IntersectionObserver entrance animation ─────────────────
   * Triggers WAAPI fade-in-up for elements with [data-animate]
   * Unobserves after first intersection (once-only)
   * ──────────────────────────────────────────────────────────── */
  function initEntranceAnimations() {
    const badges = document.querySelectorAll('.icon-badge[data-animate]');
    if (!badges.length) return;

    if (prefersReducedMotion()) {
      badges.forEach(el => {
        el.style.opacity = '1';
        el.style.transform = 'none';
      });
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;

          const el = entry.target;
          const delay = parseInt(el.dataset.animateDelay ?? '0', 10);

          el.animate(
            [
              { opacity: 0, transform: 'translateY(12px) scale(0.85)' },
              { opacity: 1, transform: 'translateY(0) scale(1)' },
            ],
            {
              duration: 500,
              delay,
              easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)', /* ease-bounce */
              fill: 'forwards',
            }
          );

          observer.unobserve(el);
        });
      },
      { threshold: 0.15 }
    );

    badges.forEach((el) => observer.observe(el));
  }

  /* ── Cursor-follow glow effect ───────────────────────────────
   * Elements with [data-cursor-glow] emit a soft glow that
   * follows the mouse cursor using CSS box-shadow offset.
   * Lightweight: only updates box-shadow (compositor-friendly).
   * ──────────────────────────────────────────────────────────── */
  function initCursorGlow() {
    const badges = document.querySelectorAll('.icon-badge[data-cursor-glow]');
    if (!badges.length || prefersReducedMotion()) return;

    badges.forEach((badge) => {
      badge.addEventListener('mousemove', (e) => {
        const rect  = badge.getBoundingClientRect();
        const cx    = rect.left + rect.width  / 2;
        const cy    = rect.top  + rect.height / 2;
        const dx    = (e.clientX - cx) / rect.width  * 12;
        const dy    = (e.clientY - cy) / rect.height * 12;

        badge.style.setProperty(
          'box-shadow',
          `${dx}px ${dy}px 28px color-mix(in oklch, var(--badge-accent, var(--neon-cyan)) 55%, transparent),
           inset 0 1px 0 color-mix(in oklch, white 14%, transparent)`
        );
      });

      badge.addEventListener('mouseleave', () => {
        badge.style.removeProperty('box-shadow');
      });
    });
  }

  /* ── Public API ──────────────────────────────────────────────── */
  function init() {
    initEntranceAnimations();
    initCursorGlow();
  }

  /* ── Auto-init on DOM ready ──────────────────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  return { init };
})();
