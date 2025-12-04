import { test, expect } from '@playwright/test';

test('system health check', async ({ request }) => {
    // Check Backend Health (Direct API)
    const response = await request.get('http://localhost:8000/');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.message).toContain('Math API');
});
