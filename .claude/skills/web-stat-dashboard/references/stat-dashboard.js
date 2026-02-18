/**
 * web-stat-dashboard — stat-dashboard.js
 * Animated stat counter grid:
 *   - Reads data-stats JSON and builds DOM from template
 *   - IntersectionObserver triggers countUp + stagger entrance
 *   - requestAnimationFrame countUp with easeOutExpo
 *   - WAAPI staggered card entrance animations
 *   - Number formatting: commas + K/M suffixes
 *   - prefers-reduced-motion: skips all animations
 */

(function () {
  'use strict';

  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── easeOutExpo tween ──────────────────────────────────────── */
  function easeOutExpo(t) {
    return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
  }

  /* ── Number formatting ──────────────────────────────────────── */
  function formatNumber(n) {
    return n.toLocaleString('en-US');
  }

  /* ── CountUp animation ──────────────────────────────────────── */
  function countUp(el, target, suffix, duration) {
    if (REDUCED_MOTION) {
      el.textContent = formatNumber(target) + suffix;
      return;
    }

    const start = performance.now();

    el.classList.add('is-counting');

    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased    = easeOutExpo(progress);
      const current  = Math.round(eased * target);

      el.textContent = formatNumber(current) + suffix;

      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = formatNumber(target) + suffix;
        el.classList.remove('is-counting');
        // Restore gradient text
        el.style.removeProperty('color');
      }
    }

    requestAnimationFrame(tick);
  }

  /* ── Card entrance animation (WAAPI) ───────────────────────── */
  function animateCardEntrance(card, index) {
    if (REDUCED_MOTION) {
      card.style.opacity = '1';
      card.style.transform = 'none';
      return;
    }

    card.animate(
      [
        { opacity: 0, transform: 'translateY(20px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ],
      {
        duration: 600,
        delay: index * 80,
        easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
        fill: 'forwards'
      }
    );
  }

  /* ── Build DOM from JSON ────────────────────────────────────── */
  function buildCards(dashboard) {
    const statsJson = dashboard.dataset.stats;
    if (!statsJson) return; // use static HTML

    let stats;
    try {
      stats = JSON.parse(statsJson);
    } catch (e) {
      console.warn('web-stat-dashboard: invalid JSON in data-stats', e);
      return;
    }

    // Clear existing children (static fallback HTML)
    dashboard.innerHTML = '';

    const accentColors = ['cyan', 'purple', 'magenta', 'green', 'orange', 'red'];

    stats.forEach((stat, index) => {
      const card = document.createElement('div');
      card.className = 'stat-card glass-card-static';
      card.setAttribute('aria-label', `${stat.label}: ${stat.value}${stat.suffix || ''}`);
      card.dataset.pendingAnimation = '';

      const accent = accentColors[index % accentColors.length];

      // Icon badge
      const badge = document.createElement('div');
      badge.className = 'icon-badge icon-badge--lg';
      badge.dataset.accent = accent;
      badge.dataset.animate = '';
      badge.textContent = stat.icon || '📊';

      // Counter value
      const value = document.createElement('div');
      value.className = 'stat-value';
      value.dataset.target = stat.value;
      value.dataset.suffix = stat.suffix || '';
      value.textContent = formatNumber(stat.value) + (stat.suffix || '');

      // Label
      const label = document.createElement('div');
      label.className = 'stat-label';
      label.textContent = stat.label;

      card.appendChild(badge);
      card.appendChild(value);
      card.appendChild(label);

      // Trend indicator
      if (stat.trend === 'up' || stat.trend === 'down') {
        const trend = document.createElement('div');
        trend.className = `stat-trend stat-trend--${stat.trend}`;
        trend.textContent = stat.trend === 'up' ? '▲' : '▼';
        trend.setAttribute('aria-label', `Trending ${stat.trend}`);
        card.appendChild(trend);
      }

      dashboard.appendChild(card);
    });
  }

  /* ── Initialize a single dashboard ─────────────────────────── */
  function initDashboard(dashboard) {
    // Build cards from JSON if present
    buildCards(dashboard);

    const animate = dashboard.dataset.animate !== 'false';
    const cards   = dashboard.querySelectorAll('.stat-card');

    if (!cards.length) return;

    // Set initial hidden state (CSS handles via data-pending-animation)
    cards.forEach(card => {
      if (!REDUCED_MOTION) {
        card.style.opacity = '0';
      }
    });

    // IntersectionObserver — triggers on viewport entry (once)
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;

          const dashEl = entry.target;
          const allCards = dashEl.querySelectorAll('.stat-card');

          allCards.forEach((card, index) => {
            // Entrance animation
            animateCardEntrance(card, index);

            // CountUp after entrance delay
            if (animate) {
              const valueEl = card.querySelector('.stat-value');
              if (!valueEl) return;

              const target = parseInt(valueEl.dataset.target || '0', 10);
              const suffix = valueEl.dataset.suffix || '';
              const delay  = REDUCED_MOTION ? 0 : index * 80 + 200;

              setTimeout(() => {
                countUp(valueEl, target, suffix, 1200);
              }, delay);
            }

            // Remove pending state
            card.removeAttribute('data-pending-animation');
          });

          observer.unobserve(dashEl);
        });
      },
      {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
      }
    );

    observer.observe(dashboard);
  }

  /* ── Auto-init ───────────────────────────────────────────────── */
  function init() {
    document.querySelectorAll('.stat-dashboard').forEach(initDashboard);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.StatDashboard = { init, countUp };

})();
