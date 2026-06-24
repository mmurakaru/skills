---
name: pr-review
description: Ranked GitHub PR review (max 3-5 findings, blocker/consideration/nit). Use when the user says "/pr-review", "review this PR", "review PR <number/URL>", or asks for a quick PR review with idiomatic suggestions.
---

# PR review

Always:

- confirm the review branch up-front, pull existing PR comments to dedupe against prior feedback
- scan the codebase for existing patterns to cite via permalinks
- Fetch latest docs for any touched React-ecosystem primitives (React, React Query, TanStack Router, Next.js).

If an org overlay exists at `references/<org>.md`, load it first - it adds org-specific guidelines to check, extra Phase 3 detection signals, and stack-specific anti-patterns on top of the flow below.

Friendly-colleague PR review, capped at 3-5 findings, paste-ready for GitHub.

**House style: ultra-minimal.** A `nit:` is one short line with maybe inline code. A `consideration:` is 1-2 sentences. A `blocker:` is 2-3 sentences plus repro and optional suggestion. GitHub already shows the file:line anchor and the diff hunk — never restate them in the comment body.

## When to invoke

- User says `/pr-review`, "review this PR", "review PR `<num>`", "review the PR at `<url>`".
- User wants a quick read on a PR they're not the author of, with idiomatic suggestions.

## When NOT to invoke

- **Formal multi-axis review** (correctness / readability / architecture / security / perf rubric) - use the built-in `/code-review`.
- **Multi-PR batch review** - this skill is one PR per invocation; large batches need a different shape.

## Argument parsing

Accepts:
- `/pr-review <number>` - PR in the current repo (e.g. `/pr-review 7527`).
- `/pr-review <github-url>` - any GitHub PR URL.
- `/pr-review` - no argument, defaults to the PR for the current branch via `gh pr list --head $(git branch --show-current)`.

## Phase 1: Branch confirmation (always)

The user explicitly asked to be asked every time. Never skip, even when branches match.

Run:
```bash
git branch --show-current
```

If invoked with a PR number / URL, get the head branch:
```bash
gh pr view <pr> --json headRefName,baseRefName,headRepository
```

Also check whether the user already has a worktrees folder for this repo - the convention is `~/Documents/Development/<repo>-worktrees/` (e.g. `autopilot-worktrees/`). Detect with:
```bash
git worktree list
ls ~/Documents/Development/<repo>-worktrees/ 2>/dev/null
```

If the worktrees folder exists OR the user has previously used worktrees on this repo, **include the worktree option** in the question. Always confirm before creating - never auto-create.

Then ask via `AskUserQuestion`:

> Q: "Branch state for review:
>
> - Current local branch: `<current>`
> - PR head branch: `<head>`
>
> Where do you want to review?"
>
> Options (include worktree only when the folder convention is detected):
> - **Create a worktree** *(recommended when the folder convention exists)* - `git worktree add ~/Documents/Development/<repo>-worktrees/<short-key>-review <head-branch>`. Isolates the review tree so the user's main checkout stays untouched. Use `<short-key>` derived from the branch name (e.g. `EXP-1908` from `fix/EXP-1908`, or the head branch slug if no ticket key).
> - **Stay on current branch** - sufficient for diff-based review, codebase pattern scan runs against your current checkout.
> - **Switch to PR head** - `git fetch && git checkout <head>`. Use when you want the codebase scan to reflect the PR's tree but don't need a separate worktree.
> - **Cancel** - stop the review.

If invoked without an argument, ask: "Auto-detect a PR for branch `<current>`, or specify a PR number / URL?"

**Worktree handling notes:**
- If the chosen worktree path already exists, ask whether to reuse it or pick a different name - never blow it away.
- After creating the worktree, run all subsequent file reads, `rg` scans, and codebase pattern citations from inside the worktree path so the review reflects the PR's tree state.
- The original working directory stays untouched; the user can keep working on their main checkout in parallel.

## Phase 2: Fetch PR data

Three calls:

```bash
gh pr view <pr> --json title,body,files,headRefName,baseRefName,author,number,url,headRepository,headRefOid
gh pr diff <pr>
gh pr view <pr> --comments
```

Cache `headRefOid` (the SHA of the PR head) - you'll need it for permalink generation in Phase 6.

## Phase 3: Detect frontend context

Scan the diff's touched-file list for primitive signals. Multiple primitives can match.

| Primitive | Signal |
|-----------|--------|
| React | `.tsx` / `.jsx` files; hooks (`useState`, `useEffect`, `useRef`, `forwardRef`); ref-as-prop; `<Suspense>` |
| React Query | imports from `@tanstack/react-query`; `useQuery`, `useMutation`, `useSuspenseQuery`, `useInfiniteQuery`, `queryOptions` |
| TanStack Router | imports from `@tanstack/react-router`; `createFileRoute`, `Link`, `useNavigate`, `loader`, `beforeLoad`, search params |
| Next.js | `app/`, `pages/`, `next.config.*`; `Server Component`, `'use server'`, `'use client'` directives |
| Vite (dev tooling) | `vite.config.*`; `defineConfig`; a `Plugin` / `configureServer` / `server.middlewares` block; `import.meta.env.MODE`; dev-proxy / middleware changes |

Org overlays (`references/<org>.md`) may add more primitives to this table.

If NO frontend primitive matches, skip Phase 4.

## Phase 4: Doc fetch (only when matched)

For each matched primitive (max 2; pick the 2 with the most diff hunks), WebFetch ONE relevant doc page. **Always fetch fresh - never trust training data, prior cache, or memory.** APIs in this stack churn (TanStack Router/Query major versions, React 19, Next.js app router shifts).

| Primitive | Canonical doc to fetch first |
|-----------|------------------------------|
| React | https://react.dev/reference/react (then https://react.dev/blog for latest release post if relevant) |
| React Query | https://tanstack.com/query/latest/docs/framework/react/overview (then `.../guides/render-optimizations` for `select` / structural sharing) |
| TanStack Router | https://tanstack.com/router/latest/docs/framework/react/overview |
| Next.js | https://nextjs.org/docs (then https://nextjs.org/blog for latest release if relevant) |
| Zustand | https://github.com/pmndrs/zustand |
| React aria | https://github.com/adobe/react-spectrum |
| Vite (dev tooling) | https://vite.dev/config/ (then `.../guide/api-plugin` for the Plugin hook API, or `.../config/server-options` for proxy/`server.middlewares` changes) |

Hard cap: 4 WebFetches max per run. The skill is fast.

For Vite-config / dev-tooling PRs (middleware, proxy rules, plugin hooks, `import.meta.env.MODE` gating), always check the latest Vite docs - the Plugin API, `configureServer` middleware ordering, and env/mode replacement semantics shift across major versions, so don't review from memory.

## Phase 5: Read existing PR comments and dedupe

Parse the `gh pr view --comments` output. For each existing comment, extract a 1-line topic summary.

During Phase 7 finding generation, drop any candidate finding whose topic semantically overlaps an existing comment. In the final output, surface: "N findings dropped because already raised by `<author>`."

This avoids re-mentioning what others have already said. Important: the user reviews multiple PRs/day and doesn't want to add noise.

## Phase 6: Codebase pattern scan (per candidate finding)

For each candidate finding that proposes a "use X pattern instead of Y" change:

1. Run `rg` for the proposed pattern in the repo to confirm it's already used elsewhere.
   ```bash
   rg -n "<proposed pattern>" --type ts --type tsx
   ```
2. If found in the codebase: capture file:line; generate a permalink:
   ```
   https://github.com/<owner>/<repo>/blob/<headRefOid>/<path>#L<line>
   ```
   Cite in the comment as: "we already do this in [link]".
3. If not found locally but the proposal is from the official docs: cite the docs link only.

For complex pattern searches (cross-file refactors, API usage audits), delegate to an `Explore` subagent.

## Phase 7: Produce review (cap 3-5 findings)

### Tags (taxonomy)

Every finding is tagged with one of three labels. **Never use `blocker:`** - even genuine bugs are framed as `suggestion:` so the tone stays collaborative.

| Tag | When | Body shape |
|-----|------|------------|
| `nit:` | Idiomatic / style / cleanup. Reviewer pasting it would say "totally optional." | **One short line.** Inline code only. No suggestion block unless trivially short. |
| `consideration:` | Worth thinking about - a possible bug, a design tradeoff, a question. May or may not warrant action. | **1-2 sentences.** Optional one-liner caveat ("worth a quick repro before treating as a blocker"). Suggestion block only when the fix is unambiguous. |
| `suggestion:` | Concrete bug or correctness issue with a fix. Used in place of `blocker:` to keep the tone collaborative. | **2-3 sentences:** what's wrong, the repro / measurable impact, and the suggested change as a ```suggestion``` block. |

### Cap

Keep top 3-5 (3 if the diff is small, 5 max for larger PRs). Drop the rest. Surface the count of dropped findings: "+ N nits not surfaced - run again with `--all` if you want them."

### Hedge guard (per CLAUDE.md)

Every finding MUST have a concrete repro path or measurable impact. **NO findings of the form "this could be a latent bug if..." or "theoretical concern about...".** Drop hedge findings silently before they enter the candidate pool.

### Output format

Each finding renders as a self-contained block the user pastes into a GitHub PR review comment at the right file:line anchor. **Ultra-minimal is mandatory.** Reviewers scan; they don't read essays. GitHub already shows the file:line anchor and the diff hunk - never restate them in the comment body.

**Hard length caps per inline comment:**
- `nit:` - one short line, e.g. `**nit:** can be written \`max-w-360\``.
- `consideration:` - 1-2 sentences. No headers. No "current code" snippet. Permalink only if pointing to a *different* file than the one being commented on (sibling references). Optional ```suggestion``` block when the fix is one line.
- `suggestion:` - 2-3 sentences + ```suggestion``` block. Same rules: no headers, no path repetition, no "current code" recap.

**Body templates:**

```markdown
**nit:** <one-line statement with inline `code`>
```

```markdown
**consideration:** <1-2 sentence statement>. <optional 1-sentence caveat or sibling-reference link>.
```

````markdown
**suggestion:** <1-2 sentence statement of the bug>. <1 sentence repro / impact>.

```suggestion
<proposed code, replacing the commented line(s) exactly>
```
````

**What to cut, ruthlessly:**
- Section headers (`### suggestion:`, `**File:**`, `**Reference:**`, `**Suggested change:**`) - the inline tag IS the header.
- `**File**: path:line ([permalink])` lines - GitHub shows it already.
- "Did you consider..." preamble - the `consideration:` tag already softens.
- "Worse, X. Also, Y. And note Z." stacked qualifiers - keep one.
- Restating PR-description intent back at the author - they wrote it.
- "Concrete impact:" / "Real impact:" labels - just state the impact.
- Quoting the diff back. The diff is already on screen.

**Scannable-in-3-seconds test:** if your inline comment doesn't fit in 4 visible lines without scrolling, it's too long. Trim until it does.

For multi-line changes that don't fit a single ` ```suggestion` block (suggestion blocks must replace exactly the lines being commented on), write a `.diff` file at `~/Documents/notes/current/pr-<num>-suggestion-<n>.diff` and reference it in the comment: "Diff drafted at `<path>` - apply with `git apply <path>` to review locally."

When the finding is illustrative (proposes a new component / refactor that doesn't replace specific lines), use ` ```tsx` (or `ts` / `js`) not ` ```suggestion` - GitHub will try to apply suggestion blocks as line replacements and the anchor will be wrong.

## Phase 8: Final assembled review note

Write to `~/Documents/notes/current/pr-<num>-review.md`. This file is the user's index: each finding is one `### <tag>: <one-line summary>` heading with the permalink, followed by the ultra-minimal inline-comment body underneath. The body is what gets pasted into GitHub - it stays inside the Phase 7 caps even in the local doc.

```markdown
# PR review: <PR title> (#<num>)

PR: <url>
Head: `<sha>`

---

### <tag>: <one-line summary>

[`<path>:<line>`](<permalink>) - <ultra-minimal inline-comment body matching the Phase 7 template for the chosen tag>

```suggestion
<proposed code>
```

---

### <tag>: ...

## Dedup'd (already raised by <author>)

- <one-liner per dedup'd finding, with permalink and brief note>

## Pulled (would need verification before posting)

- <one-liner per finding that has a load-bearing unverified assumption>
```

The heading carries the permalink so the local index is scannable, but the inline body underneath is what the user pastes. Suggestion blocks render as one-click apply in the GitHub UI.

If an org overlay was loaded, append any closing note it specifies.

## Composing with other skills

- **`react-doctor`** - if Phase 3 matched React signals, optionally invoke to run React Doctor on PR head vs base and surface newly-introduced diagnostics.
- **`octocat`** - for any non-trivial `gh` invocations beyond the three calls in Phase 2.
- **`/code-review`** (built-in) - if the user wants a formal multi-axis rubric.
- **`text-to-diagram`** - if a finding is easier to explain with a sequence / state diagram, generate one and embed.

## Tone discipline

- The `nit:` / `consideration:` / `suggestion:` tags ARE the tone. They carry the softness so the prose doesn't need to.
- "We already do this in [link]" > "You should follow our conventions."
- Cite the doc / changelog with a date so the user knows you fetched it fresh.
- **Never use `blocker:`.** Even real bugs ship as `suggestion:`. The user reviews multiple PRs/day and wants to stay collaborative.

## Hard rules

- **No hedge findings.** Per CLAUDE.md: if you cannot articulate the concrete repro path or measurable impact, drop the finding. "Latent bug" / "theoretical concern" / "could be" without specifics is not allowed.
- **Always WebFetch fresh docs** in Phase 4. Never cite a doc URL you haven't opened this session.
- **Cite means link.** Any phrase like "per the docs", "as the spec says", "according to <library>", "the README states" MUST be a markdown link to the exact doc URL you fetched. No bare "per the docs" claims - the reader has to be able to verify the citation in one click. Same rule for codebase claims: "we already do this" / "see <file>" needs a permalink to the head SHA.
- **Never auto-post to GitHub.** Output is paste-ready; the user posts. If the user explicitly asks to post (e.g. "add these as PR comments", "post them"), it's OK to post via `gh api repos/<owner>/<repo>/pulls/<num>/reviews` with `event: COMMENT` and a `comments` array of `{path, start_line, line, start_side, side, body}` entries. When you post, post the **inline body including the `**<tag>:**` prefix** (the tag IS the comment opener now). Don't post the heading line, the permalink line, or anything from the local review note above the body.
- **Cap is firm at 5.** If you find 12 issues, surface "+ 7 not surfaced". Don't bury the user.
- **Permalinks anchor to the PR head SHA**, not to `main`. If the file moves later, the permalink still resolves to what was reviewed.
- **Audit your own assumptions before posting.** If a finding has a load-bearing assumption you didn't verify (e.g. backend PATCH semantics, library runtime behavior you only inferred from types), move it to the "Pulled" section instead of posting it.
- **Clean up the worktree when the review is done.** If Phase 1 created a worktree, `git worktree remove <path>` once the review (and any posting/approval) is complete - don't leave review worktrees lying around.
