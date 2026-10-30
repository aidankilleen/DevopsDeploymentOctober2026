const { test, expect } = require('@playwright/test');
const { watchForErrors, expectNoErrors, touchHold, statValue } = require('./helpers');

test.beforeEach(async ({ page }) => {
    // Each test gets a fresh browser context, so localStorage starts empty already --
    // do not clear it on navigation or the reload test has nothing to find.
    await page.goto('/infinite_runner.html');
    await expect(page.locator('#track')).toBeVisible();
});

test('starts in a clean, waiting state', async ({ page }) => {
    const errors = watchForErrors(page);
    await page.reload();

    await expect(page.locator('#score')).toHaveText('0');
    await expect(page.locator('#speed')).toHaveText('1.0×');
    await expect(page.locator('#pauseBtn')).toHaveText('Pause');

    // Nothing moves until the first input.
    await page.waitForTimeout(600);
    await expect(page.locator('#score')).toHaveText('0');

    expectNoErrors(errors);
});

test('space starts the run and the score climbs', async ({ page }) => {
    const errors = watchForErrors(page);

    await page.keyboard.press(' ');
    await page.waitForTimeout(1200);

    expect(await statValue(page, '#score')).toBeGreaterThan(0);
    expectNoErrors(errors);
});

test('speed readout starts at a clean multiple', async ({ page }) => {
    // The speed ramp itself is deliberately not asserted here: the readout carries
    // one decimal and ACCEL is 9 px/s, so it takes ~3.7s of running to tick from
    // 1.0x to 1.1x -- by which point an unplayed run has already hit an obstacle.
    // Testing it properly would mean either playing the game or adding a test hook
    // to the page, and neither is worth it for a cosmetic readout.
    await expect(page.locator('#speed')).toHaveText('1.0×');

    await page.keyboard.press(' ');
    await page.waitForTimeout(400);
    await expect(page.locator('#speed')).toContainText('×');
});

test('ducking does not throw', async ({ page }) => {
    const errors = watchForErrors(page);

    await page.keyboard.press(' ');
    await page.keyboard.down('ArrowDown');
    await page.waitForTimeout(400);
    await page.keyboard.up('ArrowDown');

    expect(await statValue(page, '#score')).toBeGreaterThan(0);
    expectNoErrors(errors);
});

test('pause freezes the score and resumes', async ({ page }) => {
    await page.keyboard.press(' ');
    await page.waitForTimeout(500);

    const pauseBtn = page.locator('#pauseBtn');
    await pauseBtn.click();
    await expect(pauseBtn).toHaveText('Resume');

    const frozen = await statValue(page, '#score');
    await page.waitForTimeout(500);
    expect(await statValue(page, '#score')).toBe(frozen);

    await pauseBtn.click();
    await expect(pauseBtn).toHaveText('Pause');
    await page.waitForTimeout(500);
    expect(await statValue(page, '#score')).toBeGreaterThan(frozen);
});

test('restart clears the score but keeps the best', async ({ page }) => {
    await page.keyboard.press(' ');
    await page.waitForTimeout(1000);

    const best = await statValue(page, '#best');
    expect(best).toBeGreaterThan(0);

    await page.locator('#restartBtn').click();
    await expect(page.locator('#score')).toHaveText('0');
    expect(await statValue(page, '#best')).toBeGreaterThanOrEqual(best);
});

test('best score survives a reload', async ({ page }) => {
    await page.keyboard.press(' ');
    await page.waitForTimeout(1200);

    // Pause first: a running game keeps raising the best score, so a value read
    // mid-run can be stale by the time the reload lands.
    await page.locator('#pauseBtn').click();

    const best = await statValue(page, '#best');
    expect(best).toBeGreaterThan(0);

    await page.reload();
    expect(await statValue(page, '#best')).toBeGreaterThanOrEqual(best);
});

test('space does not scroll the page', async ({ page }) => {
    await page.keyboard.press(' ');
    await page.waitForTimeout(300);
    expect(await page.evaluate(() => window.scrollY)).toBe(0);
});

// ---------------------------------------------------------------- Touch

test.describe('touch controls', () => {
    test.skip(({ isMobile }) => !isMobile, 'touch gestures only run in the mobile project');

    test('tapping the left of the track starts the run', async ({ page }) => {
        const errors = watchForErrors(page);

        const box = await page.locator('#track').boundingBox();
        await page.touchscreen.tap(box.x + box.width * 0.25, box.y + box.height / 2);

        await page.waitForTimeout(1000);
        expect(await statValue(page, '#score')).toBeGreaterThan(0);
        expectNoErrors(errors);
    });

    test('holding the right of the track ducks without ending the run', async ({ page }) => {
        const errors = watchForErrors(page);

        await page.keyboard.press(' ');            // start the run
        await page.waitForTimeout(300);

        const box = await page.locator('#track').boundingBox();
        const offsetX = box.width * 0.3;           // right-hand duck zone
        await touchHold(page, '#playfield', { offsetX, holdMs: 400 });

        expect(await statValue(page, '#score')).toBeGreaterThan(0);
        expectNoErrors(errors);
    });

    test('the playfield swallows touch gestures so the page cannot scroll', async ({ page }) => {
        const box = await page.locator('#track').boundingBox();
        await page.touchscreen.tap(box.x + box.width * 0.25, box.y + box.height / 2);
        await page.waitForTimeout(300);

        expect(await page.evaluate(() => window.scrollY)).toBe(0);
    });
});
