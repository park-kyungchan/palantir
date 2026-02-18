/**
 * web-floating-orbs — floating-orbs.js
 * Optional mouse parallax for floating background orbs.
 *
 * Activation: set data-parallax="true" on the .bg-orbs container.
 * Without data-parallax, this script does nothing.
 *
 * Features:
 * - Mouse-move parallax via WAAPI (hardware-accelerated, off-thread)
 * - Lerp smoothing (0.08) for organic easing
 * - requestAnimationFrame loop only runs while cursor is moving
 * - Automatically disabled for prefers-reduced-motion users
 * - Depth multipliers: orb--1 (least) to orb--3 (most)
 *
 * Requirements:
 * - .bg-orbs[data-parallax="true"] container with .bg-orb children
 * - floating-orbs.css loaded (provides base layout + float animations)
 *
 * No dependencies. Self-contained IIFE.
 */

(function initOrbParallax() {
  'use strict';

  const container = document.querySelector('.bg-orbs[data-parallax="true"]');
  if (!container) return;

  // Respect user's motion preference
  const prefersReducedMotion =
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) return;

  const orbs = container.querySelectorAll('.bg-orb');
  if (!orbs.length) return;

  /**
   * Parallax depth multipliers per orb index.
   * Higher = more movement = appears closer to viewer.
   * orb--1 (index 0): subtle, 0.015
   * orb--2 (index 1): medium, 0.025
   * orb--3 (index 2): most visible, 0.035
   */
  const depths = [0.015, 0.025, 0.035];

  // Current cursor position normalized to [-0.5, 0.5]
  let targetX = 0;
  let targetY = 0;

  // Smoothed position (lerped toward target)
  let currentX = 0;
  let currentY = 0;

  let rafId = null;

  function onMouseMove(e) {
    targetX = (e.clientX / window.innerWidth) - 0.5;
    targetY = (e.clientY / window.innerHeight) - 0.5;

    // Start animation loop if not already running
    if (!rafId) {
      rafId = requestAnimationFrame(animate);
    }
  }

  function animate() {
    rafId = null;

    // Lerp: smoothly move currentX/Y toward targetX/Y
    currentX += (targetX - currentX) * 0.08;
    currentY += (targetY - currentY) * 0.08;

    orbs.forEach((orb, i) => {
      const depth = depths[i] ?? 0.02;
      const moveX = currentX * window.innerWidth * depth;
      const moveY = currentY * window.innerHeight * depth;

      /**
       * WAAPI: hardware-accelerated transform.
       * duration: 0 + fill: 'forwards' = instant application
       * without triggering CSS transitions or reflow.
       * Runs on the compositor thread — no main thread cost.
       */
      orb.animate(
        [{ transform: `translate(${moveX}px, ${moveY}px)` }],
        { duration: 0, fill: 'forwards' }
      );
    });

    // Continue loop only while still converging
    const dx = Math.abs(targetX - currentX);
    const dy = Math.abs(targetY - currentY);
    if (dx > 0.0001 || dy > 0.0001) {
      rafId = requestAnimationFrame(animate);
    }
  }

  document.addEventListener('mousemove', onMouseMove, { passive: true });
})();
