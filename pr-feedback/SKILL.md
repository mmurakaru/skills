---
name: pr-feedback
description: Address reviewer feedback on a PR end-to-end: verify each claim, fix, test, then wait for explicit approval before pushing and posting replies. Inverse of `pr-review`. Use when the user says "/pr-feedback", "address PR feedback", or pastes a PR link to handle the review.
---

# PR feedback

End-to-end loop for addressing reviewer feedback on a PR. The author runs this when reviewers have left comments and they want to close them in one focused pass.

This skill is the symmetrical counterpart to `pr-review`: that one *writes* feedback, this one *addresses* it.

## When to invoke

- `/pr-feedback <number>` or `/pr-feedback <github-url>` or `/pr-feedback` (current branch).
- User pastes a PR URL and says "address comments", "handle the feedback", "respond to the review".
- User explicitly says "/pr-feedback" or asks to triage and address review threads on a PR.

## When NOT to invoke

- **Reviewing a PR** (writing feedback): use `pr-review` instead.
- **Pre-PR self-review** (no reviewer comments yet): out of scope - this skill addresses existing reviewer feedback.
- **One trivial comment** the user already knows how to fix: skip the skill, just fix it.

## Argument parsing

Accepts:
- `/pr-feedback <number>` - PR number in the current repo.
- `/pr-feedback <github-url>` - any GitHub PR URL.
- `/pr-feedback` - no arg, defaults to the PR for the current branch via `gh pr list --head $(git branch --show-current) --json number,url`.

## Hard rules

- **Never push without explicit user approval** in the same conversation turn. Push is gated on the user's "ok push", "ship it", "go ahead" after seeing the diff summary.
- **Never reply or resolve threads before pushing.** Replies that reference an unpushed SHA confuse reviewers. Order is: commit → user approval → push → reply → resolve.
- **One reply per thread, concise.** Default to `addressed: <short-sha>`. Add a one-line "why" only when (a) the user picked an option among alternatives, (b) the comment was rejected/deferred, or (c) the reviewer asked a question that needs a textual answer.
- **Only resolve threads the user authored a code change for, or where the discussion is genuinely closed.** Deferred / open-question threads stay unresolved.
- **Verify claims before acting.** A reviewer saying "X is wrong" is a hypothesis, not a fact. See Phase 2.
- **Trust but verify reviewer-attributed bot output.** Comments labelled "Claude", "CodeRabbit", etc. are AI-generated and can be plausibly wrong - run the same verification as for any other claim.

## Phase 1: Pull the conversation

```sh
# PR meta
gh pr view <pr> --json number,title,headRefName,headRefOid,state,url

# All review comments (inline + replies)
gh api repos/<owner>/<repo>/pulls/<pr>/comments --paginate

# Top-level conversation comments
gh api repos/<owner>/<repo>/issues/<pr>/comments --paginate

# Review summaries (state-of-review messages)
gh pr view <pr> --json reviews
```

Filter to **open** threads only. A thread is open when:
- The latest comment in the chain is not from the PR author dismissing it.
- The thread isn't marked resolved via GraphQL.

To check resolved state:

```sh
gh api graphql -f query='
query { repository(owner:"<owner>", name:"<repo>") { pullRequest(number:<pr>) {
  reviewThreads(first:100) { nodes { id isResolved comments(first:1) { nodes { databaseId } } } }
} } }'
```

Group comments by reviewer. Within each reviewer, sort by file path so related concerns cluster. Note thread IDs alongside comment IDs - you'll need both later.

## Phase 2: Verify each claim

For every open thread, before changing code, classify the claim and verify:

| Claim type | Verification |
|---|---|
| "Library X behaves like Y" | `WebSearch` for the library's current docs / changelog; `Read` the installed `node_modules/<lib>/dist/index.d.ts` or `.js` to confirm. |
| "Codebase convention is Z" | `Grep` for the pattern across the repo. Cite a permalink to a canonical example in your reply. |
| "This is unsafe / a regression" | Reproduce with a focused test or a `grep` for the precise pre-condition. Don't assume the reviewer ran the path. |
| "Nit: X duplicated" | Confirm the duplication is real (literal duplication, not coincidental similarity). |
| "Question: do we need X?" | Investigate the usage; come back with "yes - here's why" or "no - dropping". Don't punt. |
| Bot-attributed claims (Claude, CodeRabbit) | Same verification as human claims. Bots hallucinate; assume nothing. |

If a claim doesn't hold up after verification, the right reply is *"investigated, here's what the code actually does, keeping current shape"* — not silent compliance. The reviewer learns more from a "no, because..." than a no-op fix.

## Phase 3: Apply changes

- Group fixes by file so the diff reads coherently.
- Run `npm run lint && npm run typecheck` (or repo equivalent) after each meaningful chunk - catch issues before the user reviews.
- Run targeted tests for the changed files. Full suite at the end if the project has a fast-enough one.
- For behavior changes (vs pure refactors), add or amend a unit test that locks the new behavior in. Mention these in the summary.
- For e2e tests: scan `tests/e2e/` for assertions that touch the affected flow. Note explicitly whether they need amendment or already pass with the new behavior.

## Phase 4: Summary to user (before push)

Output a punch list, one line per thread:

```
Comments (N open):
  ✓ #<id>  <reviewer>:<file>:<line>  <one-line summary of what changed>
  ✓ #<id>  <reviewer>:<file>:<line>  <kept current, here's why>
  ⏸ #<id>  <reviewer>:<file>:<line>  <deferred to follow-up - reason>
```

Then:

```
Commit: <short-sha> (local only, not pushed)
Tests: <X> passed, <Y> failed
Lint:  clean | <count> errors
Type:  clean | <count> errors

Ready to push when you approve. Manual QA path: <suggest one minimal smoke test against the feature being reviewed>.
```

**Stop here. Wait for the user's explicit "ok push" or equivalent.** Do not push, do not reply, do not resolve.

## Phase 5: After approval

In order:

1. `git push`.
2. Capture the pushed SHA from `git rev-parse HEAD`. Use the short form (10 chars) for replies.
3. Post one reply per thread:
   - Default: `addressed: <short-sha>`
   - With one-line context only when:
     - You rejected/deferred the comment (cite reason)
     - You picked among options (cite which and why)
     - The reviewer asked a question with no code change (answer it)
   - Use `gh api repos/<owner>/<repo>/pulls/<pr>/comments/<comment-id>/replies -f body=...`
4. Resolve threads where the work is fully done. Open-question threads, deferred work, threads the user wants to discuss further — leave unresolved.
   ```sh
   gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "<thread-id>"}) { thread { isResolved } } }'
   ```
5. Report back: which threads got pushed/replied/resolved, which are still open and why.

## Concise replies - examples

| Comment kind | Reply |
|---|---|
| Nit, fixed | `addressed: 4c90913705` |
| Bug, fixed + test | `addressed: 4c90913705` |
| Picked one of reviewer's options | `addressed: 4c90913705 - went with option B (ring) per <reason>` |
| Verified false alarm, no change | `Looked into this - <one-line: what the code actually does>. Keeping current shape.` |
| Deferred to follow-up | `Filed as follow-up <issue-url>; out of scope for this PR.` |
| Reviewer asked a question | `<one-line answer, no commit hash needed if no code changed>` |

## Anti-patterns to avoid

- **Inventing justifications.** Don't write "Lupo signed off" if you don't have a link. If you don't know, say "no sign-off yet, holding".
- **Massive paragraph replies.** Reviewers re-read the comment, they don't need a re-explanation.
- **Replying before push.** Comments with `addressed: <sha>` where the SHA isn't on the remote yet are noise.
- **Silently dismissing claims.** If you disagree, say so with one line of reasoning. Don't just leave the thread.
- **Resolving threads with open questions.** Resolution = "no further discussion intended". If the reviewer might want to push back, leave it.
- **Bulk-resolving without per-thread reasoning.** Each resolve should map to a specific addressed: hash or a stated rationale.

## Composes with

- `pr-review` - the inverse: writes feedback. This skill addresses what that one (or a human) wrote.
- `octocat` / `gh` - underlying mechanics for fetching PR data and posting replies.
- Commit message style + branch hygiene during the loop: per the global CLAUDE.md conventions.
