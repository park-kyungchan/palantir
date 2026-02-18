/**
 * web-split-layout — split-layout.js
 * Sticky split layout interactions:
 *   - IntersectionObserver: active section tracking → left TOC highlight
 *   - requestAnimationFrame: scroll progress bar for right panel
 *   - WAAPI: entrance animation on both panels
 *   - Mobile tabs: show/hide panels on tab click
 *   - prefers-reduced-motion: all animations disabled
 */

(function () {
  'use strict';

  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /**
   * Initialize all .split-layout instances on the page.
   */
  function init() {
    document.querySelectorAll('.split-layout').forEach(initSplitLayout);
  }

  function initSplitLayout(layout) {
    const left    = layout.querySelector('.split-left');
    const right   = layout.querySelector('.split-right');
    const toc     = layout.querySelector('.split-toc');
    const progBar = layout.querySelector('.split-progress-bar');

    if (!left || !right) return;

    // Entrance animation
    if (!REDUCED_MOTION) {
      animateEntrance(left, 0);
      animateEntrance(right, 80);
    }

    // Scroll progress bar (tracks right panel scroll)
    if (progBar) {
      trackScrollProgress(right, progBar);
    }

    // TOC section highlighting
    if (toc) {
      initSectionTracking(layout, right, toc);
    }

    // Mobile tabs
    const mobileMode = layout.dataset.mobile;
    if (mobileMode === 'tabs') {
      initMobileTabs(layout, left, right);
    }
  }


  /* ── Entrance animation (WAAPI) ─────────────────────────────── */

  function animateEntrance(el, delayMs) {
    el.setAttribute('data-animate', '');

    el.animate(
      [
        { opacity: 0, transform: 'translateY(16px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ],
      {
        duration: 600,
        delay: delayMs,
        easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
        fill: 'forwards'
      }
    );
  }


  /* ── Scroll progress (right panel → progress bar) ───────────── */

  function trackScrollProgress(rightPanel, progressBar) {
    let rafId = null;

    function update() {
      const el      = rightPanel;
      const scrollTop  = el.scrollTop;
      const scrollMax  = el.scrollHeight - el.clientHeight;
      const pct = scrollMax > 0 ? (scrollTop / scrollMax) * 100 : 0;
      progressBar.style.width = pct.toFixed(1) + '%';
      rafId = null;
    }

    // Right panel may itself scroll, or the window scrolls past a sticky element.
    // Listen on both the right panel and window scroll.
    function onScroll() {
      if (!rafId) {
        rafId = requestAnimationFrame(update);
      }
    }

    rightPanel.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('scroll', onScroll, { passive: true });

    // Initial state
    update();
  }


  /* ── Section tracking (IntersectionObserver → TOC highlight) ── */

  function initSectionTracking(layout, rightPanel, toc) {
    const sections = rightPanel.querySelectorAll('[data-section]');
    if (!sections.length) return;

    const tocItems = toc.querySelectorAll('.split-toc-item[data-section]');
    const tocMap   = {};
    tocItems.forEach(item => {
      tocMap[item.dataset.section] = item;
    });

    let activeSection = null;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const id = entry.target.dataset.section;
            if (id && id !== activeSection) {
              // Remove active from previous
              if (activeSection && tocMap[activeSection]) {
                tocMap[activeSection].classList.remove('is-active');
              }
              // Set active
              activeSection = id;
              if (tocMap[id]) {
                tocMap[id].classList.add('is-active');
              }
            }
          }
        });
      },
      {
        threshold: 0.3,
        rootMargin: '0px 0px -40% 0px'
      }
    );

    sections.forEach(section => observer.observe(section));
  }


  /* ── Mobile tabs ─────────────────────────────────────────────── */

  function initMobileTabs(layout, left, right) {
    // Only activate on small viewports
    const mq = window.matchMedia('(max-width: 768px)');
    if (!mq.matches) return;

    // Build tab nav
    const tabNav = document.createElement('div');
    tabNav.className = 'split-tabs-nav';

    const btnOverview = document.createElement('button');
    btnOverview.className = 'split-tab-btn is-active';
    btnOverview.textContent = 'Overview';
    btnOverview.setAttribute('aria-pressed', 'true');

    const btnContent = document.createElement('button');
    btnContent.className = 'split-tab-btn';
    btnContent.textContent = 'Content';
    btnContent.setAttribute('aria-pressed', 'false');

    tabNav.appendChild(btnOverview);
    tabNav.appendChild(btnContent);
    layout.insertAdjacentElement('beforebegin', tabNav);

    // Initial visibility
    left.classList.add('is-tab-active');

    function switchTo(showLeft) {
      left.classList.toggle('is-tab-active', showLeft);
      right.classList.toggle('is-tab-active', !showLeft);
      btnOverview.classList.toggle('is-active', showLeft);
      btnContent.classList.toggle('is-active', !showLeft);
      btnOverview.setAttribute('aria-pressed', String(showLeft));
      btnContent.setAttribute('aria-pressed', String(!showLeft));
    }

    btnOverview.addEventListener('click', () => switchTo(true));
    btnContent.addEventListener('click', () => switchTo(false));
  }


  /* ── Auto-init ───────────────────────────────────────────────── */

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose for manual init
  window.SplitLayout = { init };

})();
