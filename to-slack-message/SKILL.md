---
name: to-slack-message
license: MIT
description: Draft a short Slack message from the current task. Use when the user says /to-slack-message or wants to post a concise update or set of questions to a channel.
---

One-line intro: what you're doing + [link](https://example.com). cc @owner (optional)

Category (e.g. Needs input):
- point - [permalink](https://example.com) - @person (tag only if actionable)
- open question?

Category (e.g. Decisions):
- point (state the fact/number, not the reasoning)

Keep it short: intro <= 2 lines, bullets 1-2 lines. Plain text, single hyphens. Permalink every claim (code -> commit-pinned URL). Resolve @mentions to real user IDs. Default to a draft; send only when confirmed.
