const { test, expect } = require('@playwright/test');

// Read-only checks against the deployed site. Nothing here writes, deploys or
// changes server state.

const PAGES = [
    '/index.html',
    '/about.html',
    '/contact.html',
    '/users.html',
    '/games.html',
    '/tetris.html',
    '/infinite_runner.html',
];

// ---------------------------------------------------------------- The API contract

// This is the check that matters most. On 2026-10-30 the VM was running
// json-server 1.0.0-beta.15, which serves public/ with HTML extension fallback
// ahead of the REST router -- so GET /users returned public/users.html with a
// 200 status, and users.html's fetch died on `<` while the local suite stayed
// green against the pinned 0.16.3. Status alone would not have caught it;
// the content type is the tell.
test('/users serves JSON, not the users page', async ({ request }) => {
    const response = await request.get('/users');

    expect(response.status()).toBe(200);
    expect(
        response.headers()['content-type'],
        'if this says text/html, the VM is serving users.html for /users -- check the json-server version'
    ).toContain('application/json');

    const users = await response.json();
    expect(Array.isArray(users)).toBe(true);
    expect(users.length).toBe(4);
    expect(users.map((u) => u.name)).toEqual(['Alice', 'Bob', 'Carol', 'Dan']);
});

test('user ids are numbers, as the local json-server returns them', async ({ request }) => {
    // json-server 1.x returns ids as strings; 0.16.3 returns numbers. A mismatch
    // here means the deployed version has drifted from the pinned one again.
    const response = await request.get('/users/1');
    expect(response.status()).toBe(200);

    const user = await response.json();
    expect(typeof user.id).toBe('number');
    expect(user.name).toBe('Alice');
});

// ---------------------------------------------------------------- Pages

for (const path of PAGES) {
    test(`${path} is served`, async ({ request }) => {
        const response = await request.get(path);
        expect(response.status()).toBe(200);
        expect(response.headers()['content-type']).toContain('text/html');
    });
}

test('local images are deployed', async ({ request }) => {
    for (const path of ['/img/image.png', '/img/tetris.svg', '/img/runner.svg']) {
        const response = await request.get(path);
        expect(response.status(), `${path} is missing from the deploy`).toBe(200);
    }
});

// ---------------------------------------------------------------- End to end

test('users page renders the table from the live API', async ({ page }) => {
    // The browser-level version of the API check: proves the page and the API
    // agree in production, which is precisely what broke.
    await page.goto('/users.html');

    await expect(page.locator('#userRows tr')).toHaveCount(4);
    await expect(page.locator('#tableWrapper')).toBeVisible();
    await expect(page.locator('#status')).toBeHidden();
    await expect(page.locator('#userRows tr').first()).toContainText('Alice');
});

test('games are reachable from the games page', async ({ page }) => {
    await page.goto('/games.html');

    await page.locator('a.stretched-link[href="tetris.html"]').click();
    await expect(page).toHaveTitle('Tetris - DevOps Demo Site');
    await expect(page.locator('#board')).toBeVisible();
});

// ---------------------------------------------------------------- Access control

test('/private/ is behind basic auth', async ({ request }) => {
    const response = await request.get('/private/', { failOnStatusCode: false });

    expect(response.status(), '/private/ is not password protected').toBe(401);
    expect(response.headers()['www-authenticate']).toContain('Basic');
});

test('/private/ opens with the class credentials', async ({ playwright }) => {
    // Opt-in: the password is not committed. Supply it to run this check.
    //   SMOKE_PRIVATE_PASSWORD=... npm run test:smoke
    test.skip(!process.env.SMOKE_PRIVATE_PASSWORD, 'set SMOKE_PRIVATE_PASSWORD to run');

    const context = await playwright.request.newContext({
        baseURL: process.env.SMOKE_BASE_URL || 'https://aidan.aitrainingcourses.ie',
        httpCredentials: {
            username: process.env.SMOKE_PRIVATE_USER || 'class',
            password: process.env.SMOKE_PRIVATE_PASSWORD,
        },
    });

    const response = await context.get('/private/');
    expect(response.status()).toBe(200);
    await context.dispose();
});

// ---------------------------------------------------------------- Transport

test('http redirects to https', async ({ playwright }) => {
    const context = await playwright.request.newContext({ ignoreHTTPSErrors: false });
    const base = (process.env.SMOKE_BASE_URL || 'https://aidan.aitrainingcourses.ie')
        .replace(/^https:/, 'http:');

    const response = await context.get(`${base}/index.html`, { maxRedirects: 0, failOnStatusCode: false });

    expect(response.status()).toBe(301);
    expect(response.headers()['location']).toMatch(/^https:/);
    await context.dispose();
});
