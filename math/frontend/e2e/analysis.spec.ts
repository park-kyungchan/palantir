import { test, expect } from '@playwright/test';

test('analyze number flow', async ({ page }) => {
    await page.goto('/');

    // Check title
    await expect(page.getByText('Math Visualizer')).toBeVisible();

    // Input number
    await page.getByPlaceholder('Enter a number').fill('42');

    // Click analyze
    await page.getByRole('button', { name: 'Analyze Number' }).click();

    // Verify result card appears
    await expect(page.getByText('42 is Composite')).toBeVisible();

    // Verify factors
    await expect(page.getByText('Prime Factors')).toBeVisible();
    const factors = ['2', '3', '7'];
    for (const factor of factors) {
        await expect(page.getByText(factor, { exact: true })).toBeVisible();
    }
});
