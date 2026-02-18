/**
 * web-nav-dots — nav-dots.js
 * Section navigation dot controller.
 *
 * Features:
 * - IntersectionObserver tracks active section (scroll spy)
 * - Click/Enter/Space handlers for smooth scroll
 * - prefers-reduced-motion: uses 'instant' scroll behavior
 *
 * Requirements:
 * - .nav-dot elements with data-section="<section-id>" attributes
 * - Matching <section id="<section-id>"> elements in the page
 * - nav-dots.css for visual styles
 *
 * No dependencies. Self-contained IIFE.
 */

(function initNavDots() {
  'use strict';

  const navDots = document.querySelectorAll('.nav-dot[data-section]');
  if (!navDots.length) return;

  const prefersReducedMotion =
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── Click / keyboard: scroll to target section ──────────────
  navDots.forEach(dot => {
    dot.addEventListener('click', () => {
      const target = document.getElementById(dot.dataset.section);
      if (!target) return;
      target.scrollIntoView({
        behavior: prefersReducedMotion ? 'instant' : 'smooth'
      });
    });

    // Keyboard support: Enter and Space trigger click
    dot.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        dot.click();
      }
    });
  });

  // ── IntersectionObserver: active section tracking ──────────
  const sectionIds = [...navDots].map(d => d.dataset.section);
  const sections = sectionIds
    .map(id => document.getElementById(id))
    .filter(Boolean);

  if (!sections.length) return;

  /**
   * Scroll spy: marks the dot whose section is most visible.
   * threshold: 0.4 — section must be 40% in view to become active.
   * rootMargin: reduces the bottom of the viewport so the active
   *   section transitions earlier as you scroll down.
   */
  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const activeId = entry.target.id;
          navDots.forEach(dot => {
            dot.classList.toggle('active', dot.dataset.section === activeId);
          });
        }
      });
    },
    {
      threshold: 0.4,
      rootMargin: '0px 0px -30% 0px'
    }
  );

  sections.forEach(section => observer.observe(section));
})();
