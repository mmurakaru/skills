---
name: no-visual-diff
description: Prove a code change renders identically before and after, so any real visual difference is caught and routed to a designer. Use when verifying a change is visually no-op, checking before/after parity on a component or page, or gating a refactor, dependency bump, or styling migration PR.
---

# no-visual-diff

Prove a component renders identically before and after your change.

Prereq: `browser-harness` on PATH; the component reachable at a running dev server. Capture `before` and `after` on the **same machine** (pixel pass is noisy across machines).

Snapshot **before you start**, do the work, snapshot **after** — one dev server, same URL, no worktrees needed.

## Run

1. **browser-harness** — capture the untouched component (`before`), then re-run after the change (`after`):
   `URL=<url> SEL='<exact-selector>' OUT=/tmp/nvd/before browser-harness < scripts/capture.py`
2. **style-diff** (primary gate, deterministic computed styles) — `node scripts/style-diff.mjs /tmp/nvd/before.styles.json /tmp/nvd/after.styles.json`
3. **odiff** (backup gate, pixels) — `npx --yes odiff-bin /tmp/nvd/before.png /tmp/nvd/after.png /tmp/nvd/diff.png --aa`

## Verdict

- Both exit 0 → no visual diff → mechanical, reviewer-only.
- `style-diff` exit 1 → prints the exact `element property: before → after` → designer decision.
- `odiff` exit 22 → pixels moved (paint/stacking/overflow that computed styles can't see) → `Read /tmp/nvd/diff.png`.

Use an **exact** selector (`section[aria-label="…"]`, unique class) — generic tags also match app chrome.
