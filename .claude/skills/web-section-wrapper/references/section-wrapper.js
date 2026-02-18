/**
 * web-section-wrapper — section-wrapper.js
 * Scroll-reveal entrance fallback (Firefox) + nav-dot integration.
 *
 * This script handles TWO concerns:
 * 1. CSS scroll-driven animation fallback via IntersectionObserver (Firefox only).
 *    Silently exits in Chrome/Edge/Safari where CSS scroll-driven animations are supported.
 * 2. Nav-dot registration: dispatches CustomEvent('section:register') for each section,
 *    picked up by floating-nav-dots.js if loaded. Safe no-op if web-nav-dots is absent.
 *
 * Features:
 * - CSS.supports() guard: zero overhead in modern browsers
 * - Adds .section-wrapper--js-ready to activate hidden start states in CSS fallback
 * - IntersectionObserver adds .section-wrapper--visible when section header enters viewport
 * - Dispatches section:register CustomEvent for nav-dot coordination
 * - Respects prefers-reduced-motion (reveal immediately, skip animation)
 *
 * Requirements:
 * - section-wrapper.css loaded (provides .section-wrapper--js-ready and .section-wrapper--visible)
 * - .section-wrapper[data-section-id] present in DOM
 *
 * No dependencies. Self-contained IIFE.
 */

(function initSectionWrapper() {
  'use strict';

  const prefersReducedMotion =
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const sections = document.querySelectorAll('.section-wrapper[data-section-id]');
  if (!sections.length) return;

  // ── Nav-dot registration ──────────────────────────────────────────────────
  // Dispatch section:register for each section so floating-nav-dots.js can
  // track active sections. If web-nav-dots is not loaded, the event is ignored.
  sections.forEach((section) => {
    const id = section.dataset.sectionId;
    const titleEl = section.querySelector('.section-title');
    const label = titleEl ? titleEl.textContent.trim() : id;

    document.dispatchEvent(
      new CustomEvent('section:register', {
        detail: { id, label, element: section },
        bubbles: false,
      })
    );
  });

  // ── Scroll-reveal fallback ────────────────────────────────────────────────
  // Exit if CSS scroll-driven animations are supported (Chrome/Edge/Safari).
  // These browsers handle the reveal entirely in CSS — no JS needed.
  if (CSS.supports('animation-timeline', 'view()')) return;

  // If reduced motion: reveal all section headers immediately, skip animation.
  if (prefersReducedMotion) {
    sections.forEach((section) => {
      section.classList.add('section-wrapper--visible');
    });
    return;
  }

  // Add class that activates hidden start states in CSS
  sections.forEach((section) => {
    section.classList.add('section-wrapper--js-ready');
  });

  // Track which sections have been revealed (avoid re-animating on re-intersection)
  const revealed = new WeakSet();

  // Single observer for all sections — efficient, avoids per-section observers.
  // Trigger when section header area enters the viewport.
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !revealed.has(entry.target)) {
          entry.target.classList.add('section-wrapper--visible');
          revealed.add(entry.target);
          observer.unobserve(entry.target); // Stop observing once revealed
        }
      });
    },
    {
      threshold: 0.1,
      rootMargin: '0px 0px -60px 0px',
    }
  );

  sections.forEach((section) => observer.observe(section));
})();
