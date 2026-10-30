const { test, expect } = require('@playwright/test');
const { watchForErrors, expectNoErrors } = require('./helpers');

test('users table populates from the API', async ({ page }) => {
    const errors = watchForErrors(page);

    await page.goto('/users.html');

    const rows = page.locator('#userRows tr');
    await expect(rows).toHaveCount(4);

    await expect(page.locator('#tableWrapper')).toBeVisible();
    await expect(page.locator('#status')).toBeHidden();

    await expect(rows.nth(0)).toContainText('Alice');
    await expect(rows.nth(0)).toContainText('alice@gmail.com');
    await expect(rows.nth(3)).toContainText('Dan');

    expectNoErrors(errors);
});

test('active flag renders as a badge', async ({ page }) => {
    await page.goto('/users.html');

    const rows = page.locator('#userRows tr');
    await expect(rows).toHaveCount(4);

    // Bob is the only inactive user in db.json.
    await expect(rows.nth(0).locator('.badge')).toHaveText('Active');
    await expect(rows.nth(1).locator('.badge')).toHaveText('Inactive');
    await expect(rows.nth(2).locator('.badge')).toHaveText('Active');
});

// The catch branch in users.html never runs in normal use; this is the only thing
// that exercises it.
test('API failure shows an error instead of an empty table', async ({ page }) => {
    await page.route('**/users', (route) => route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: '{}',
    }));

    await page.goto('/users.html');

    const status = page.locator('#status');
    await expect(status).toBeVisible();
    await expect(status).toHaveClass(/alert-danger/);
    await expect(status).toContainText('Could not load users');
    await expect(page.locator('#tableWrapper')).toBeHidden();
});

test('empty collection shows a warning', async ({ page }) => {
    await page.route('**/users', (route) => route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: '[]',
    }));

    await page.goto('/users.html');

    const status = page.locator('#status');
    await expect(status).toHaveClass(/alert-warning/);
    await expect(status).toContainText('No users were returned');
});
