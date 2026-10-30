const { test, expect } = require('@playwright/test');
const { PAGES, watchForErrors, expectNoErrors } = require('./helpers');

// ---------------------------------------------------------------- Every page loads

for (const { path, title } of PAGES) {
    test(`${path} loads cleanly`, async ({ page }) => {
        const errors = watchForErrors(page);

        const response = await page.goto(path);
        expect(response.status()).toBe(200);

        await expect(page).toHaveTitle(title);
        await expect(page.locator('nav.navbar')).toBeVisible();
        await expect(page.locator('footer')).toBeVisible();
        await expect(page.locator('h1')).toBeVisible();

        expectNoErrors(errors);
    });
}

// ---------------------------------------------------------------- Links resolve

// The navbar is duplicated by hand across every page, so a typo'd href is the most
// likely regression on this site and is otherwise invisible until someone clicks it.
test('every internal link resolves', async ({ page, request, baseURL }) => {
    const checked = new Map();

    for (const { path } of PAGES) {
        await page.goto(path);

        const hrefs = await page.locator('a[href]').evaluateAll((anchors) =>
            anchors.map((a) => a.getAttribute('href'))
        );

        for (const href of hrefs) {
            if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) {
                continue;
            }

            const resolved = new URL(href, new URL(path, baseURL)).toString();
            if (!resolved.startsWith(baseURL)) { continue; }   // external link, not ours to verify
            if (checked.has(resolved)) { continue; }

            const response = await request.get(resolved);
            checked.set(resolved, response.status());
        }
    }

    const broken = [...checked.entries()].filter(([, status]) => status !== 200);
    expect(broken, `broken links: ${JSON.stringify(broken)}`).toEqual([]);
    expect(checked.size).toBeGreaterThan(5);   // guard against the crawl silently finding nothing
});

test('every local image resolves', async ({ page, request, baseURL }) => {
    const checked = new Map();

    for (const { path } of PAGES) {
        await page.goto(path);

        const sources = await page.locator('img[src]').evaluateAll((images) =>
            images.map((img) => img.getAttribute('src'))
        );

        for (const src of sources) {
            if (!src || /^https?:/i.test(src)) { continue; }   // picsum placeholders are remote by design
            const resolved = new URL(src, new URL(path, baseURL)).toString();
            if (checked.has(resolved)) { continue; }

            const response = await request.get(resolved);
            checked.set(resolved, response.status());
        }
    }

    const missing = [...checked.entries()].filter(([, status]) => status !== 200);
    expect(missing, `missing images: ${JSON.stringify(missing)}`).toEqual([]);
    expect(checked.size).toBeGreaterThan(0);
});

// ---------------------------------------------------------------- Navigation

test('navbar reaches every public page', async ({ page, isMobile }) => {
    // On a narrow viewport the navbar is collapsed behind the toggler, so the
    // links are not clickable until it is opened. Exercising that is the point.
    const openNav = async () => {
        if (!isMobile) { return; }
        await page.locator('.navbar-toggler').click();
        await expect(page.locator('#mainNav')).toBeVisible();
    };

    await page.goto('/index.html');

    for (const label of ['About', 'Contact', 'Users', 'Games']) {
        await openNav();
        await page.locator('nav.navbar').getByRole('link', { name: label, exact: true }).click();
        await expect(page).toHaveTitle(`${label} - DevOps Demo Site`);
        await page.goto('/index.html');
    }
});

test('games page links to both games', async ({ page }) => {
    await page.goto('/games.html');

    await expect(page.locator('a[href="tetris.html"]').first()).toBeVisible();
    await expect(page.locator('a[href="infinite_runner.html"]').first()).toBeVisible();

    // Each card wraps both the image and the title in a link to the same page, but
    // Bootstrap's .stretched-link on the title covers the whole card and intercepts
    // the click -- so that is the one a user actually hits.
    await page.locator('a.stretched-link[href="tetris.html"]').click();
    await expect(page).toHaveTitle('Tetris - DevOps Demo Site');
});

// ---------------------------------------------------------------- API

test('json-server serves the users collection', async ({ request }) => {
    const response = await request.get('/users');
    expect(response.status()).toBe(200);

    const users = await response.json();
    expect(Array.isArray(users)).toBe(true);
    expect(users.length).toBe(4);
    expect(users.map((u) => u.name)).toEqual(['Alice', 'Bob', 'Carol', 'Dan']);
});
