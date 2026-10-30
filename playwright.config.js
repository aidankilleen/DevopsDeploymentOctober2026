const { defineConfig, devices } = require('@playwright/test');

// The suite drives a local json-server started from webfiles/, exactly as the VM runs it.
// Nothing here touches the live site.
module.exports = defineConfig({
    testDir: './tests',
    // Smoke specs target the deployed site and have their own config
    // (playwright.smoke.config.js); they must never run as part of the local suite.
    testIgnore: '**/smoke/**',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: 0,
    reporter: [['list'], ['html', { open: 'never' }]],

    use: {
        baseURL: 'http://127.0.0.1:3000',
        trace: 'on-first-retry',
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
        {
            // Pixel 5 brings touch emulation with it, which is the point: the touch
            // handling in tetris.html and infinite_runner.html is where the bugs were.
            name: 'mobile',
            use: { ...devices['Pixel 5'] },
        },
    ],

    webServer: {
        // npx resolves the pinned local json-server (0.16.3, same as the VM),
        // so the suite does not depend on a global install.
        // --host is pinned to IPv4 deliberately: json-server's default 'localhost' binds
        // ::1 only on Windows, which does not match baseURL and collides with any
        // json-server already running from a working session.
        command: 'npx json-server --watch --host 127.0.0.1 --port 3000 db.json',
        cwd: 'webfiles',
        url: 'http://127.0.0.1:3000/index.html',
        // A json-server is often already running on 3000 during a working session;
        // without this every run would fail on a port clash.
        reuseExistingServer: true,
        timeout: 60 * 1000,
    },
});
