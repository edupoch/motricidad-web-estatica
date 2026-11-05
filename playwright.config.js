import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  snapshotPathTemplate: 'baseline/{arg}{ext}',
  updateSnapshots: 'none',
  timeout: 120000,
  workers: 4,
  fullyParallel: true,
  reporter: 'line',
  webServer: process.env.TARGET
    ? undefined
    : { command: 'python3 -m http.server 8765 -d docs', port: 8765, reuseExistingServer: false, stdout: 'ignore', stderr: 'ignore' },
});
