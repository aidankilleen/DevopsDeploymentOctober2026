const { test, expect } = require('@playwright/test');
const { watchForErrors, expectNoErrors, swipe, statValue } = require('./helpers');

// The canvas cannot be meaningfully pixel-asserted, so everything here is checked
// through the DOM the game already updates: #score, #lines, #level and the buttons.

test.beforeEach(async ({ page }) => {
    await page.goto('/tetris.html');
    await expect(page.locator('#board')).toBeVisible();
});

test('starts in a clean state', async ({ page }) => {
    const errors = watchForErrors(page);
    await page.reload();

    await expect(page.locator('#score')).toHaveText('0');
    await expect(page.locator('#lines')).toHaveText('0');
    await expect(page.locator('#level')).toHaveText('1');
    await expect(page.locator('#next')).toBeVisible();
    await expect(page.locator('#pauseBtn')).toHaveText('Pause');

    expectNoErrors(errors);
});

test('soft drop scores one point per press', async ({ page }) => {
    // Proves the keydown handler, collision checks and game loop are all live:
    // softDrop() only awards a point when the piece actually had room to fall.
    for (let i = 0; i < 3; i++) {
        await page.keyboard.press('ArrowDown');
    }

    await expect(page.locator('#score')).toHaveText('3');
});

test('hard drop scores more than a soft drop', async ({ page }) => {
    const before = await statValue(page, '#score');
    await page.keyboard.press(' ');

    const after = await statValue(page, '#score');
    expect(after).toBeGreaterThan(before + 1);
});

test('rotation and movement do not throw', async ({ page }) => {
    const errors = watchForErrors(page);

    for (const key of ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'x', 'z']) {
        await page.keyboard.press(key);
    }

    // Still responsive afterwards.
    await page.keyboard.press('ArrowDown');
    expect(await statValue(page, '#score')).toBeGreaterThan(0);

    expectNoErrors(errors);
});

test('pause stops the game and resumes', async ({ page }) => {
    const pauseBtn = page.locator('#pauseBtn');

    await pauseBtn.click();
    await expect(pauseBtn).toHaveText('Resume');

    // Input is ignored while paused.
    const paused = await statValue(page, '#score');
    await page.keyboard.press('ArrowDown');
    expect(await statValue(page, '#score')).toBe(paused);

    await pauseBtn.click();
    await expect(pauseBtn).toHaveText('Pause');

    await page.keyboard.press('ArrowDown');
    expect(await statValue(page, '#score')).toBeGreaterThan(paused);
});

test('restart clears the score', async ({ page }) => {
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowDown');
    expect(await statValue(page, '#score')).toBeGreaterThan(0);

    await page.locator('#restartBtn').click();
    await expect(page.locator('#score')).toHaveText('0');
    await expect(page.locator('#level')).toHaveText('1');
});

test('keyboard shortcuts do not scroll the page', async ({ page }) => {
    // Space and the arrow keys are preventDefault-ed; if that ever regresses the
    // page jumps around under the player.
    await page.keyboard.press(' ');
    await page.keyboard.press('ArrowDown');

    const scrollY = await page.evaluate(() => window.scrollY);
    expect(scrollY).toBe(0);
});

// ---------------------------------------------------------------- Touch

test.describe('touch controls', () => {
    test.skip(({ isMobile }) => !isMobile, 'touch gestures only run in the mobile project');

    test('dragging down soft drops', async ({ page }) => {
        const errors = watchForErrors(page);

        await swipe(page, '#playfield', { dy: 160, steps: 10 });

        expect(await statValue(page, '#score')).toBeGreaterThan(0);
        expectNoErrors(errors);
    });

    test('dragging sideways does not drop the piece', async ({ page }) => {
        // The gesture locks to one axis; a sloppy horizontal drag must not score.
        await swipe(page, '#playfield', { dx: 120, steps: 10 });

        await expect(page.locator('#score')).toHaveText('0');
    });

    test('tapping rotates without error and leaves the game responsive', async ({ page }) => {
        const errors = watchForErrors(page);

        const box = await page.locator('#board').boundingBox();
        await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);

        await expect(page.locator('#score')).toHaveText('0');   // a tap is a rotate, not a drop

        await swipe(page, '#playfield', { dy: 120, steps: 8 });
        expect(await statValue(page, '#score')).toBeGreaterThan(0);

        expectNoErrors(errors);
    });

    test('the playfield swallows touch gestures so the page cannot scroll', async ({ page }) => {
        await swipe(page, '#playfield', { dy: 200, steps: 12 });
        expect(await page.evaluate(() => window.scrollY)).toBe(0);
    });
});
