## General Guidelines

- Use single hyphens (-), not em dashes (—).
- In long Markdown, put each sentence on its own line; keep normal Markdown structure.
- Commits use the user's identity only - no Co-Authored-By, Signed-off-by, or Claude/Anthropic trailers.
- Never hand-edit CHANGELOG.md or files marked auto-generated.
- Favor quality, simplicity, robustness, scalability, and long-term maintainability over development cost.
- When E2E testing, be picky about the UI and chase pixel perfection - fix anything that looks off, even if unrelated.
- Hold the same bar for lint, test failures, and flakiness: fix them even when not caused by your change.
- Start bug fixes by reproducing E2E, as close to real user conditions as possible.
- If the user rejects a hypothesis, STOP guessing - search the web or read more code. Don't go in circles on AX-tree, DOM, or framework internals.
- Prefer concrete code reads + web searches over speculative pattern-matching.
- Verify technical claims against source or official docs before asserting; cite a source for stats and root causes, and state confidence.
- Use the repo's PR template (`.github/pull_request_template.md`); don't pass `--body` to `gh pr create` when one exists.
- In PR reviews, verify each finding via source/permalinks, keep only essential nits, and never post comments or approvals until explicitly authorized.
- Flag only code-review issues with concrete repro or real impact - no hedged "latent bug" findings.
- Prefer concise prose over tables in audits and reports unless a table is clearly justified.
- Comments: one line max, WHY only when non-obvious; if it needs more than a line, rename instead.
- Don't start servers, run unrequested setup, or act beyond the ask; for a location or status question, just answer it.
- Never put secrets/tokens inline in commands - use env vars or references.
- Treat memory as point-in-time context, not current truth. Verify against current files before relying on it; if it conflicts with what you observe, trust observation and update or remove the stale memory.

## Tooling & Stack

- Tailwind: use unbracketed spacing-scale values (`leading-11`, not `leading-[30px]`).
- Strapi: use the Strapi MCP server for uploads/content, not guessed REST routes; the admin token needs the admin /upload route.
- To drive Chrome or capture screenshots/video, default to browser-harness (installed, invokable via skill): https://github.com/browser-use/browser-harness

## Opinions & Voice

- For tasks that benefit from my viewpoints, read ~/OPINIONS.md.
- When posting as me, read ~/VOICE.md for my writing style.
