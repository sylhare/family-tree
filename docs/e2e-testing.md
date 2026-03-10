# E2E Testing with Playwright

End-to-end tests run against the live UI using [Playwright](https://playwright.dev).

## Prerequisites

### UI-only (no backend needed for smoke test)

```bash
cd ui && npm run dev
```

### Full stack

```bash
docker compose up -d
```

## Running Tests

```bash
cd ui

# Headless (CI-friendly)
npm run e2e

# Interactive UI mode
npm run e2e:ui
```

## What the Smoke Test Covers

`e2e/app.spec.ts`:
- Navigates to `/`
- Asserts the `Family Tree Manager` heading is visible
- Captures a full-page screenshot → `docs/screenshots/app.png`

## First-time Setup

Install Playwright and the Chromium browser (only needed once):

```bash
cd ui
npm install
npx playwright install --with-deps chromium
```

## Further Reading

- [Playwright docs](https://playwright.dev)
- [Configuration reference](https://playwright.dev/docs/test-configuration)
