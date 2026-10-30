const { defineConfig, devices } = require('@playwright/test');

// Smoke tests run against the DEPLOYED site, not a local json-server.
// They exist to catch drift between what the tests run on and what production runs,
// which is exactly how /users came to serve HTML for a week while the suite was green.
//
//   npm run test:smoke                       -> https://aidan.aitrainingcourses.ie
//   SMOKE_BASE_URL=https://other npm run test:smoke
module.exports = defineConfig({
    testDir: './tests/smoke',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,   // tolerate a transient network blip in CI
    reporter: [['list']],

    use: {
        baseURL: process.env.SMOKE_BASE_URL || 'https://aidan.aitrainingcourses.ie',
        trace: 'on-first-retry',
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],

    // Deliberately no webServer: nothing is started, nothing is deployed.
});
