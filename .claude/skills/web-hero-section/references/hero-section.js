/**
 * web-hero-section — hero-section.js
 * Staggered WAAPI entrance for hero section elements.
 *
 * Features:
 * - Staggered entrance: eyebrow → title → subtitle → chips → cta → scroll indicator
 * - Scroll indicator: click/keyboard → smooth scroll to next section
 * - Automatically disabled for prefers-reduced-motion users (CSS already shows elements)
 * - View Transitions API: intercepts [data-view-transition] links for page-morph
 *
 * Requirements:
 * - hero-section.css loaded (provides start states: opacity 0, translateY)
 * - .hero-section element present in DOM
 *
 * No dependencies. Self-contained IIFE.
 */

(function initHeroSection() {
  'use strict';

  // Respect user's motion preference.
  // CSS already shows elements via prefers-reduced-motion: reduce,
  // so we exit early — no JS animation needed.
  const prefersReducedMotion =
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) return;

  const hero = document.querySelector('.hero-section');
  if (!hero) return;

  /**
   * Fade-up animation via WAAPI (hardware-accelerated, off-thread).
   * Animates from hidden CSS start state (opacity 0 + translateY) to visible.
   *
   * @param {Element} el      - Element to animate (null-safe)
   * @param {number}  delay   - Delay in ms before animation starts
   * @param {Object}  [opts]  - Optional overrides: duration, fromY
   * @returns {Animation|null}
   */
  function fadeUp(el, delay, opts = {}) {
    if (!el) return null;
    const { duration = 600, fromY = 20 } = opts;
    return el.animate(
      [
        { opacity: 0, transform: `translateY(${fromY}px)` },
        { opacity: 1, transform: 'translateY(0)' },
      ],
      {
        duration,
        delay,
        easing: 'cubic-bezier(0.16, 1, 0.3, 1)', // ease-out-expo
        fill: 'forwards',
      }
    );
  }

  /**
   * Fade-in animation — opacity only, no vertical movement.
   */
  function fadeIn(el, delay, opts = {}) {
    if (!el) return null;
    const { duration = 500 } = opts;
    return el.animate(
      [{ opacity: 0 }, { opacity: 1 }],
      {
        duration,
        delay,
        easing: 'ease-out',
        fill: 'forwards',
      }
    );
  }

  // ── Elements ──────────────────────────────────────────────────
  const eyebrow   = hero.querySelector('.hero-eyebrow');
  const title     = hero.querySelector('.hero-title');
  const subtitle  = hero.querySelector('.hero-subtitle');
  const chipsRow  = hero.querySelector('.hero-chips');
  const chips     = chipsRow ? [...chipsRow.querySelectorAll('.chip')] : [];
  const cta       = hero.querySelector('.hero-cta');
  const indicator = hero.querySelector('.hero-scroll-indicator');

  // ── Entrance sequence ─────────────────────────────────────────
  // Timing:
  //   t=0ms    eyebrow fades up (translateY 10→0)
  //   t=100ms  title fades up (gradient already applied via CSS)
  //   t=250ms  subtitle fades up
  //   t=380ms  chips row fades in; children stagger scale-pop (60ms each)
  //   t=ctaDelay  CTA fades up
  //   after CTA   scroll indicator fades in, then bounces

  fadeUp(eyebrow,  0,   { fromY: 10, duration: 500 });
  fadeUp(title,    100, { fromY: 20 });
  fadeUp(subtitle, 250, { fromY: 15 });
  fadeIn(chipsRow, 380);

  // Stagger individual chips with a scale-pop effect
  chips.forEach((chip, i) => {
    chip.animate(
      [
        { opacity: 0, transform: 'scale(0.8)' },
        { opacity: 1, transform: 'scale(1)' },
      ],
      {
        duration: 300,
        delay: 420 + i * 60,
        easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)', // spring
        fill: 'forwards',
      }
    );
  });

  // CTA: after last chip settles
  const ctaDelay = 420 + chips.length * 60 + 60;
  const ctaAnim  = fadeUp(cta, ctaDelay, { fromY: 10, duration: 500 });

  // Scroll indicator: enters after CTA, then adds bounce class
  if (indicator && ctaAnim) {
    ctaAnim.finished.then(() => {
      const indicatorAnim = fadeIn(indicator, 0, { duration: 400 });
      if (indicatorAnim) {
        indicatorAnim.finished.then(() => {
          indicator.classList.add('hero-scroll-indicator--bouncing');
        });
      }
    }).catch(() => {
      // Animation cancelled (e.g. page navigated away) — ignore
    });
  }

  // ── Scroll indicator interaction ──────────────────────────────
  if (indicator) {
    // Ensure keyboard accessibility
    if (!indicator.getAttribute('tabindex')) {
      indicator.setAttribute('tabindex', '0');
    }
    if (!indicator.getAttribute('role')) {
      indicator.setAttribute('role', 'button');
    }

    function scrollToNext() {
      const next = hero.nextElementSibling;
      if (next) {
        next.scrollIntoView({ behavior: 'smooth' });
      } else {
        window.scrollBy({ top: window.innerHeight, behavior: 'smooth' });
      }
    }

    indicator.addEventListener('click', scrollToNext);
    indicator.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        scrollToNext();
      }
    });
  }

  // ── View Transitions API ──────────────────────────────────────
  // Intercepts <a data-view-transition> clicks for hero-title morph.
  // The CSS view-transition-name: hero-title on h1 enables the morph.
  // Usage: <a href="/page" data-view-transition>Link</a>
  if (document.startViewTransition) {
    document.querySelectorAll('a[data-view-transition]').forEach((link) => {
      link.addEventListener('click', (e) => {
        const href = link.href;
        if (!href || href === window.location.href) return;
        e.preventDefault();
        document.startViewTransition(() => {
          window.location.href = href;
        });
      });
    });
  }
})();
