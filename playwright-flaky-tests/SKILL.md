---
name: playwright-flaky-tests
description: Reproduce, diagnose, and fix flaky Playwright e2e tests. Use when tests pass locally but fail on CI, when investigating intermittent test failures, or when asked to harden e2e tests.
argument-hint: @spec-file
disable-model-invocation: true
---

# Fix Flaky Playwright Tests

Target spec: $ARGUMENTS
Strip any leading `@` from the path. Call the cleaned path `SPEC`.

## Workflow

Iterative loop: reproduce → diagnose → fix → verify. Repeat until stable.

### 1. Read the spec and its page objects

Read `SPEC` and any page objects it imports. Identify potential flakiness sources against [patterns.md](patterns.md).

### 2. Verify local environment

If the first test run fails with unexpected data (wrong segments, 502, stale state), ask the user to fully reset the mock environment. This requires a password and must be run manually:

```bash
# Wipe persistent volumes (postgres, redis, etc.) to clear stale data
docker compose -f envmocks/docker/docker-compose.yml down -v

# Rebuild from scratch
npm run setup:mock-env
```

Without `-v`, database volumes persist stale data across restarts. CI always starts clean — locally you must wipe volumes to match.

Wait for the user to confirm it's done before proceeding.

Also check mock isolation: if tests rely on shared default mappings (no per-test stubs), use `--workers=1`.

### 3. Run the stress test (baseline)

Start without throttling to establish a baseline failure rate:

```bash
npx playwright test SPEC --repeat-each=20 --retries=0 --workers=1 --reporter=list -x
```

If all pass, escalate pressure incrementally:
- Increase workers: `--workers=4`, then `--workers=8` (only if mock isolation allows)
- Increase repetitions: `--repeat-each=50`
- Add CPU throttling (see below)

Stop escalating once failures appear.

### 4. Add CPU throttling if needed

If stress test passes without throttling, add CDP throttling to simulate CI. Insert temporarily in the test's `beforeEach`:

```ts
const cdpSession = await page.context().newCDPSession(page);
await cdpSession.send('Emulation.setCPUThrottlingRate', { rate: 4 });
```

Start at `rate: 4`, increase to 6 if still passing. **Remove before committing.**

### 5. Diagnose failures

Inspect traces and screenshots: `npx playwright show-report`

Or debug interactively (no repeat-each): `npx playwright test SPEC --ui`

Match failures to patterns in [patterns.md](patterns.md).

### 6. Apply fixes

Fix one pattern at a time. Keep changes minimal and targeted.

### 7. Verify

Re-run the same stress test that produced failures. If it passes, increase pressure:

```bash
npx playwright test SPEC --repeat-each=50 --retries=0 --workers=1 -x
```

Target: 0 failures across 50 reps at the highest pressure level that previously failed.

If failures persist, return to step 5.

## Reference

- `--repeat-each=N` — run each test N times
- `--retries=0` — disable auto-retry to expose true failures
- `--workers=N` — parallel workers (default: 50% of CPU cores)
- `-x` — stop on first failure
- `--fail-on-flaky-tests` — fail if any test is flagged flaky
