/**
 * web-dual-panel — dual-panel.js
 * Dual panel layout interactions:
 *   - Reads data-panels JSON and builds DOM from template
 *   - WAAPI staggered panel entrance (0ms left, 120ms right)
 *   - Per-panel list item stagger with IntersectionObserver
 *   - Optional comparison slider (drag + touch)
 *   - prefers-reduced-motion: skips all animations
 */

(function () {
  'use strict';

  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Build panel card from data object ─────────────────────── */
  function buildPanelCard(panelData, index) {
    const card = document.createElement('div');
    card.className = 'panel-card glass-card-static';
    card.setAttribute('aria-label', panelData.title || `Panel ${index + 1}`);

    // Header
    const header = document.createElement('div');
    header.className = 'panel-header';

    if (panelData.icon) {
      const badge = document.createElement('div');
      badge.className = 'icon-badge icon-badge--lg';
      badge.dataset.accent  = panelData.accent || 'cyan';
      badge.dataset.animate = '';
      badge.textContent     = panelData.icon;
      header.appendChild(badge);
    }

    if (panelData.title) {
      const title = document.createElement('h3');
      title.className   = 'panel-title';
      title.textContent = panelData.title;
      header.appendChild(title);
    }

    card.appendChild(header);

    // Description
    if (panelData.description) {
      const desc = document.createElement('p');
      desc.className   = 'panel-description';
      desc.textContent = panelData.description;
      card.appendChild(desc);
    }

    // List items
    if (Array.isArray(panelData.items) && panelData.items.length) {
      const ul = document.createElement('ul');
      ul.className  = 'panel-list';
      ul.setAttribute('aria-label', `${panelData.title || 'Panel'} items`);

      panelData.items.forEach((text) => {
        const li = document.createElement('li');
        const isPositive = text.startsWith('+') || text.startsWith('✓') || text.startsWith('✅');
        li.className  = isPositive
          ? 'panel-list-item panel-list-item--positive'
          : 'panel-list-item';
        li.textContent = text;
        ul.appendChild(li);
      });

      card.appendChild(ul);
    }

    return card;
  }

  /* ── Build DOM from data-panels JSON ───────────────────────── */
  function buildPanels(dualPanel) {
    const json = dualPanel.dataset.panels;
    if (!json) return;

    let panels;
    try {
      panels = JSON.parse(json);
    } catch (e) {
      console.warn('web-dual-panel: invalid JSON in data-panels', e);
      return;
    }

    if (!Array.isArray(panels) || panels.length !== 2) return;

    // Replace static HTML with generated cards
    dualPanel.innerHTML = '';
    panels.forEach((panelData, i) => {
      dualPanel.appendChild(buildPanelCard(panelData, i));
    });
  }

  /* ── Animate card entrance ──────────────────────────────────── */
  function animatePanelEntrance(card, delayMs) {
    if (REDUCED_MOTION) {
      card.removeAttribute('data-pending-animation');
      card.style.opacity  = '1';
      card.style.transform = 'none';
      return;
    }

    card.animate(
      [
        { opacity: 0, transform: 'translateY(16px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ],
      {
        duration: 600,
        delay:    delayMs,
        easing:   'cubic-bezier(0.16, 1, 0.3, 1)',
        fill:     'forwards'
      }
    ).onfinish = () => card.removeAttribute('data-pending-animation');
  }

  /* ── Animate list items ─────────────────────────────────────── */
  function animateListItems(card, baseDelayMs) {
    if (REDUCED_MOTION) return;

    const items = card.querySelectorAll('.panel-list-item');
    items.forEach((item, i) => {
      item.animate(
        [
          { opacity: 0, transform: 'translateX(8px)' },
          { opacity: 1, transform: 'translateX(0)' }
        ],
        {
          duration: 350,
          delay:    baseDelayMs + 80 + i * 60,
          easing:   'cubic-bezier(0.16, 1, 0.3, 1)',
          fill:     'forwards'
        }
      ).onfinish = () => item.removeAttribute('data-pending-animation');
    });
  }

  /* ── Comparison slider ──────────────────────────────────────── */
  function initComparisonSlider(dualPanel) {
    const cards = dualPanel.querySelectorAll('.panel-card');
    if (cards.length < 2) return;

    const left   = cards[0];
    const slider = document.createElement('div');
    slider.className = 'dual-panel-slider';
    slider.setAttribute('role', 'separator');
    slider.setAttribute('aria-label', 'Comparison slider — drag to reveal');
    dualPanel.appendChild(slider);

    let isDragging = false;

    function updatePosition(clientX) {
      const rect    = dualPanel.getBoundingClientRect();
      const percent = Math.min(Math.max((clientX - rect.left) / rect.width, 0.05), 0.95);
      left.style.clipPath    = `inset(0 ${(1 - percent) * 100}% 0 0)`;
      slider.style.left      = `${percent * 100}%`;
    }

    slider.addEventListener('mousedown',  () => { isDragging = true; });
    slider.addEventListener('touchstart', () => { isDragging = true; }, { passive: true });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      updatePosition(e.clientX);
    });

    window.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      updatePosition(e.touches[0].clientX);
    }, { passive: true });

    window.addEventListener('mouseup',  () => { isDragging = false; });
    window.addEventListener('touchend', () => { isDragging = false; });

    // Keyboard accessible
    slider.setAttribute('tabindex', '0');
    slider.addEventListener('keydown', (e) => {
      const rect    = dualPanel.getBoundingClientRect();
      const current = parseFloat(slider.style.left || '50%') / 100;
      const step    = (e.key === 'ArrowLeft' || e.key === 'ArrowDown') ? -0.05 : 0.05;
      if (!['ArrowLeft', 'ArrowRight', 'ArrowDown', 'ArrowUp'].includes(e.key)) return;
      e.preventDefault();
      updatePosition(rect.left + (current + step) * rect.width);
    });
  }

  /* ── Initialize a single dual panel ────────────────────────── */
  function initDualPanel(dualPanel) {
    // Build DOM from JSON if data-panels present
    buildPanels(dualPanel);

    const cards = dualPanel.querySelectorAll('.panel-card');
    if (!cards.length) return;

    // Set pending state on cards and list items
    if (!REDUCED_MOTION) {
      cards.forEach(card => {
        card.dataset.pendingAnimation = '';
        card.querySelectorAll('.panel-list-item')
            .forEach(li => { li.dataset.pendingAnimation = ''; });
      });
    }

    // IntersectionObserver triggers entrance (once)
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;

          const panel = entry.target;
          const allCards = panel.querySelectorAll('.panel-card');

          allCards.forEach((card, index) => {
            const delay = index === 0 ? 0 : 120;
            animatePanelEntrance(card, delay);
            animateListItems(card, delay);
          });

          observer.unobserve(panel);
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    );

    observer.observe(dualPanel);

    // Optional comparison slider
    if (dualPanel.dataset.comparison !== undefined) {
      initComparisonSlider(dualPanel);
    }
  }

  /* ── Auto-init ───────────────────────────────────────────────── */
  function init() {
    document.querySelectorAll('.dual-panel').forEach(initDualPanel);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.DualPanel = { init };

})();
