# Common Flakiness Patterns

## 1. Sequential waits without atomic guarantee

**Problem:** Waiting for elements one-by-one. If the page reloads between steps, earlier waits pass but later ones see stale state.

```ts
// Bad - each wait is independent, no retry from scratch
await expect(iframe).toBeVisible({ timeout: 60000 })
await expect(body).toBeAttached({ timeout: 30000 })
await expect(segment).toBeAttached({ timeout: 10000 })
```

**Fix:** Wrap in `expect().toPass()` for atomic retry:

```ts
await expect(async () => {
  await expect(iframe).toBeVisible({ timeout: 5000 })
  await expect(body).toBeAttached({ timeout: 5000 })
  await expect(segment).toBeAttached({ timeout: 5000 })
}).toPass({ timeout: 60000 })
```

## 2. Point-in-time checks with `.isVisible()`

**Problem:** `.isVisible()` is a one-shot boolean check with no retry. Transient states are easily missed.

```ts
// Bad - checks once, returns false if element is mid-transition
const isReady = await indicator.isVisible()
```

**Fix:** Use `expect().toBeVisible()` which auto-retries:

```ts
await expect(indicator).toBeVisible({ timeout: 5000 })
```

Only use `.isVisible()` for branching logic (feature detection), never for assertions.

## 3. Hard-coded `waitForTimeout()`

**Problem:** Arbitrary delays are either too short (flaky) or too long (slow). CI timing varies.

```ts
// Bad
await page.waitForTimeout(100)
```

**Fix:** Wait for the actual condition:

```ts
await expect(element).toBeVisible({ timeout: 5000 })
```

## 4. Missing wait before interaction

**Problem:** Clicking a menu item before the dropdown is visible.

```ts
// Bad - menu might not be rendered yet
await button.click()
await menuItem.click()
```

**Fix:** Wait for the target to be visible:

```ts
await button.click()
await expect(menuItem).toBeVisible({ timeout: 5000 })
await menuItem.click()
```

## 5. `.first()` on ambiguous locators

**Problem:** `.first()` picks whichever element matches first. Under load, DOM order or timing may vary.

```ts
// Bad - could pick the wrong element
await segments.filter({ hasText: text }).first().hover()
```

**Fix:** Assert the element is visible first, or use a more specific locator:

```ts
const target = segments.filter({ hasText: text }).first()
await expect(target).toBeVisible({ timeout: 5000 })
await target.hover()
```

## 6. Insufficient timeouts for CI

**Problem:** Timeouts tuned for fast local machines are too tight for CI with resource contention.

**Fix:** Increase timeouts for operations involving cross-frame messaging, iframe loads, or network-dependent state. 10s locally often needs 15-20s on CI.

## 7. Iframe interactions

**Problem:** Iframes load asynchronously. The iframe element may be visible but its content not yet ready.

```ts
// Bad - iframe visible doesn't mean content is loaded
await expect(iframe).toBeVisible()
await iframe.locator('.segment').click() // fails: content not loaded
```

**Fix:** Wait for content inside the iframe:

```ts
await expect(async () => {
  await expect(iframe).toBeVisible({ timeout: 5000 })
  await expect(iframeBody).toBeAttached({ timeout: 5000 })
  await expect(iframeSegment).toBeAttached({ timeout: 5000 })
}).toPass({ timeout: 30000 })
```

## 8. Fragile regex selectors

**Problem:** Regex selectors like `filter({ hasText: /German|Spanish|English/i })` can match unintended elements.

**Fix:** Use exact role-based selectors or `getByRole` with `exact: true`:

```ts
const menuItem = page.getByRole('menuitem', { name: 'German', exact: true })
```

## 9. Shared mock state across parallel workers

**Problem:** Multiple workers share the same WireMock container. Tests relying on default mappings see data from other workers' requests.

**Fix:** Either:
- Run with `--workers=1` to isolate
- Create per-test mappings with `priority: 1` scoped to a unique `projectId`
- Reset mappings before the run via `WireMock.resetMappings()`
