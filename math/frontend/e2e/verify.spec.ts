import { test, expect } from '@playwright/test';

test('Backend Health Check', async ({ request }) => {
  // Port 8080
  const response = await request.get('http://127.0.0.1:8080/health');
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.status).toBe('ok');
});

test('Frontend Load Check', async ({ page }) => {
  // Port 3000
  await page.goto('http://127.0.0.1:3000');
  await expect(page).toHaveTitle('Prime Visualizer');
  await expect(page.locator('text=Prime Visualizer')).toBeVisible({ timeout: 10000 });
});