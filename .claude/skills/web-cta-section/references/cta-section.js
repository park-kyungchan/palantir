/**
 * web-cta-section — cta-section.js
 * CTA section interactions:
 *   - IntersectionObserver scroll-reveal entrance (WAAPI)
 *   - Magnetic button mousemove attraction effect
 *   - Primary button hover glow pulse (WAAPI)
 *   - Particle burst on primary button click
 *   - prefers-reduced-motion: skips all animations
 */

(function () {
  'use strict';

  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Particle burst ─────────────────────────────────────────── */
  function spawnParticles(btn) {
    if (REDUCED_MOTION) return;

    const rect  = btn.getBoundingClientRect();
    const cx    = rect.left + rect.width  / 2;
    const cy    = rect.top  + rect.height / 2;
    const count = 16;

    for (let i = 0; i < count; i++) {
      const particle = document.createElement('span');
      particle.setAttribute('aria-hidden', 'true');

      const angle    = (i / count) * 360;
      const distance = 40 + Math.random() * 60;
      const dx       = Math.cos((angle * Math.PI) / 180) * distance;
      const dy       = Math.sin((angle * Math.PI) / 180) * distance;
      const size     = 4 + Math.random() * 4;
      const hue      = Math.random() > 0.5 ? '#00ffff' : '#ff00ff';

      Object.assign(particle.style, {
        position:       'fixed',
        left:           `${cx}px`,
        top:            `${cy}px`,
        width:          `${size}px`,
        height:         `${size}px`,
        borderRadius:   '50%',
        background:     hue,
        pointerEvents:  'none',
        zIndex:         '9999',
        boxShadow:      `0 0 6px ${hue}`,
      });

      document.body.appendChild(particle);

      particle.animate(
        [
          { transform: 'translate(-50%, -50%) scale(1)', opacity: 1 },
          {
            transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(0)`,
            opacity:    0
          }
        ],
        { duration: 600, easing: 'cubic-bezier(0, 0, 0.2, 1)', fill: 'forwards' }
      ).onfinish = () => particle.remove();
    }
  }

  /* ── Magnetic button effect ─────────────────────────────────── */
  function initMagneticBtn(btn) {
    if (REDUCED_MOTION) return;

    const STRENGTH = 0.25; // 25% attraction
    let raf = null;

    btn.addEventListener('mousemove', (e) => {
      const rect = btn.getBoundingClientRect();
      const dx   = e.clientX - (rect.left + rect.width  / 2);
      const dy   = e.clientY - (rect.top  + rect.height / 2);

      if (raf) cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        btn.style.transform = `translate(${dx * STRENGTH}px, ${dy * STRENGTH}px)`;
      });
    });

    btn.addEventListener('mouseleave', () => {
      if (raf) cancelAnimationFrame(raf);
      btn.animate(
        [
          { transform: btn.style.transform || 'translate(0,0)' },
          { transform: 'translate(0, 0)' }
        ],
        { duration: 300, easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)', fill: 'forwards' }
      );
      btn.style.transform = '';
    });
  }

  /* ── Scroll-reveal entrance ─────────────────────────────────── */
  function animateEntrance(inner) {
    if (REDUCED_MOTION) {
      inner.removeAttribute('data-pending-animation');
      inner.style.opacity  = '1';
      inner.style.transform = 'none';
      return;
    }

    inner.animate(
      [
        { opacity: 0, transform: 'translateY(24px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ],
      {
        duration: 700,
        easing:   'cubic-bezier(0.16, 1, 0.3, 1)',
        fill:     'forwards'
      }
    ).onfinish = () => inner.removeAttribute('data-pending-animation');
  }

  /* ── Initialize a single CTA section ───────────────────────── */
  function initCTA(section) {
    const inner   = section.querySelector('.cta-inner');
    const primary = section.querySelector('.cta-btn-primary');

    if (!inner) return;

    // Mark for entrance animation (CSS hides it via data-pending-animation)
    if (!REDUCED_MOTION) {
      inner.dataset.pendingAnimation = '';
    }

    // Scroll-reveal
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          animateEntrance(inner);
          observer.unobserve(section);
        });
      },
      { threshold: 0.2, rootMargin: '0px 0px -40px 0px' }
    );

    observer.observe(section);

    // Magnetic + particle burst on primary button
    if (primary) {
      if (primary.classList.contains('cta-btn-magnetic')) {
        initMagneticBtn(primary);
      }

      if (primary.dataset.particles !== undefined) {
        primary.addEventListener('click', () => spawnParticles(primary));
      }
    }
  }

  /* ── Auto-init ───────────────────────────────────────────────── */
  function init() {
    document.querySelectorAll('.cta-section').forEach(initCTA);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.CTASection = { init, spawnParticles };

})();
