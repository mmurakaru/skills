---
name: curating-bookmarks
license: MIT
description: Review, declutter and reorganize Chrome bookmarks. Use when the user wants to audit, clean up, bulk-delete, or restructure their Chrome bookmarks.
---

# Curating Bookmarks

Edit bookmarks through Chrome's `chrome.bookmarks` API - **never** by editing the `Bookmarks` JSON file. Chrome Sync reverts direct file edits on next launch.

## 1. Pick the profile

- Bookmarks live at `~/Library/Application Support/Google/Chrome/<profile>/Bookmarks`.
- Read each profile's `Preferences` → `account_info[].email` to tell work from personal. Confirm with the user.

## 2. Kick off with an HTML report

- Parse the `Bookmarks` JSON (folder tree + urls + `date_added`).
- Generate one self-contained HTML catalogue: every item defaults to **keep**, with per-item + per-folder keep/delete toggles, search, live counts, and a **Submit** button that downloads `bookmark-decisions.json`. No external calls (private URLs).
- Open it, let the user triage, read the downloaded file back.

## 3. Apply via the API

- Open `chrome://bookmarks/` - only this privileged page has `chrome.bookmarks` bound. Run calls via CDP `Runtime.evaluate` (use the `browser-harness` skill's `js(...)`).
- Match targets by **URL** (+ title/parent folder to disambiguate dupes) - `id` and `guid` change after a Sync round-trip.
- Delete with `chrome.bookmarks.remove(id)`; reorganize with `.create()` / `.move()` / `.update()`.
- A single long Promise looping many calls may return `None` while the ops finish async - verify with a fresh `getTree()`, not the return value.

## 4. Verify

- Re-read the live tree: confirm the count and that intended keeps survived.
- Tell the user to keep Chrome open a minute so Sync commits to the server (and propagates to their devices).
