const { expect } = require('@playwright/test');

// Every page the site serves, with the title it should carry.
const PAGES = [
    { path: '/index.html', title: 'Home - DevOps Demo Site' },
    { path: '/about.html', title: 'About - DevOps Demo Site' },
    { path: '/contact.html', title: 'Contact - DevOps Demo Site' },
    { path: '/users.html', title: 'Users - DevOps Demo Site' },
    { path: '/games.html', title: 'Games - DevOps Demo Site' },
    { path: '/tetris.html', title: 'Tetris - DevOps Demo Site' },
    { path: '/infinite_runner.html', title: 'Infinite Runner - DevOps Demo Site' },
    { path: '/private/index.html', title: 'Class Materials - DevOps Demo Site' },
];

// Noise that says nothing about whether the site works: json-server serves no
// favicon, the picsum placeholders are decorative and remote, and Chrome probes
// /.well-known/appspecific/com.chrome.devtools.json under automation.
//
// These patterns are matched against the failing resource's URL as well as the
// message text. That matters: for a failed request Chromium's message text is
// only "Failed to load resource: the server responded with a status of 404
// (Not Found)" -- the URL lives in message.location(), so matching on text
// alone silently never matches.
const IGNORED_ERRORS = [
    /favicon/i,
    /picsum\.photos/i,
    /\.well-known\//i,
];

/**
 * Collect console errors and uncaught exceptions. Call before navigating,
 * then assert on the returned array at the end of the test.
 */
function watchForErrors(page) {
    const errors = [];

    const keep = (text) => !IGNORED_ERRORS.some((pattern) => pattern.test(text));

    page.on('pageerror', (error) => {
        const text = `pageerror: ${error.message}`;
        if (keep(text)) { errors.push(text); }
    });

    page.on('console', (message) => {
        if (message.type() !== 'error') { return; }
        // Include the resource URL so the filters above can see it, and so a real
        // failure reports which URL broke instead of a bare "Failed to load resource".
        const url = (message.location() && message.location().url) || '';
        const text = url ? `console: ${message.text()} [${url}]` : `console: ${message.text()}`;
        if (keep(text)) { errors.push(text); }
    });

    return errors;
}

/**
 * Drag a finger across an element. Playwright's touchscreen can tap but not swipe,
 * so the touch sequence is dispatched in the page.
 */
async function swipe(page, selector, { dx = 0, dy = 0, steps = 8, holdMs = 0 } = {}) {
    await page.evaluate(
        async ({ selector, dx, dy, steps, holdMs }) => {
            const element = document.querySelector(selector);
            const rect = element.getBoundingClientRect();
            const startX = rect.left + rect.width / 2 - dx / 2;
            const startY = rect.top + rect.height / 2 - dy / 2;

            const fire = (type, x, y) => {
                const touch = new Touch({
                    identifier: 1,
                    target: element,
                    clientX: x,
                    clientY: y,
                });
                element.dispatchEvent(new TouchEvent(type, {
                    touches: type === 'touchend' ? [] : [touch],
                    changedTouches: [touch],
                    bubbles: true,
                    cancelable: true,
                }));
            };

            fire('touchstart', startX, startY);
            for (let i = 1; i <= steps; i++) {
                fire('touchmove', startX + (dx * i) / steps, startY + (dy * i) / steps);
                await new Promise((resolve) => setTimeout(resolve, 16));
            }
            if (holdMs) {
                await new Promise((resolve) => setTimeout(resolve, holdMs));
            }
            fire('touchend', startX + dx, startY + dy);
        },
        { selector, dx, dy, steps, holdMs }
    );
}

/** Hold a finger on an element without moving it. */
async function touchHold(page, selector, { offsetX = 0, offsetY = 0, holdMs = 300 } = {}) {
    await page.evaluate(
        async ({ selector, offsetX, offsetY, holdMs }) => {
            const element = document.querySelector(selector);
            const rect = element.getBoundingClientRect();
            const x = rect.left + rect.width / 2 + offsetX;
            const y = rect.top + rect.height / 2 + offsetY;

            const fire = (type) => {
                const touch = new Touch({ identifier: 2, target: element, clientX: x, clientY: y });
                element.dispatchEvent(new TouchEvent(type, {
                    touches: type === 'touchend' ? [] : [touch],
                    changedTouches: [touch],
                    bubbles: true,
                    cancelable: true,
                }));
            };

            fire('touchstart');
            await new Promise((resolve) => setTimeout(resolve, holdMs));
            fire('touchend');
        },
        { selector, offsetX, offsetY, holdMs }
    );
}

/** Read an integer out of a stat element such as #score. */
async function statValue(page, selector) {
    const text = await page.locator(selector).innerText();
    return parseInt(text.replace(/[^0-9-]/g, ''), 10);
}

function expectNoErrors(errors) {
    expect(errors, `unexpected browser errors:\n${errors.join('\n')}`).toEqual([]);
}

module.exports = { PAGES, watchForErrors, expectNoErrors, swipe, touchHold, statValue };
