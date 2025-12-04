import { test, expect } from '@playwright/test';

test('error handling flow', async ({ page }) => {
    await page.goto('/');

    // Input invalid number (0)
    await page.getByPlaceholder('Enter a number').fill('0');

    // Click analyze (should be prevented or show error)
    // Note: HTML input type="number" min="1" might prevent submission, 
    // but we test the API error handling if forced or via UI feedback.

    // Let's try a large number that might cause timeout or specific error if backend limits it
    await page.getByPlaceholder('Enter a number').fill('1000001');
    await page.getByRole('button', { name: 'Analyze Number' }).click();

    // Expect error message
    await expect(page.getByText('Number too large')).toBeVisible();
});
