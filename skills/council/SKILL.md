---
name: council
description: Trigger this if the user says 'council'.
---

# Council

Before an audit, address outstanding PR comments, fix known issues, and run
relevant checks. Give council the updated implementation; do not defer known
fixes until reviews return. If the user wants to discard the implementation
and explore new ideas, skip fixes to code being replaced.

Bring in three delegates, all on high: GPT-6.1 Sol through the Codex
subscription, Claude Opus 5.5 through OpenRouter, and Gemini 4 Carbon through
OpenRouter. Resolve the actual provider IDs and effort options from the runtime
catalog. These are deliberately different perspectives. Three
modelmakers do not require three separate T3 provider connections. Honor any
more specific members named by the user.

In T3 Code, use `orchestrator_capabilities` to resolve the current provider,
model IDs, and effort options. Use native Codex children when supported and
`delegate_task` for the OpenRouter members, following the runtime's rules.
Outside T3, use the available equivalent routes. If an agreed member cannot
run, report it instead of duplicating another member. If Codex is genuinely
unavailable or limited, the same Sol model through OpenRouter is an allowed
backup. Report the failed route and the backup used. A task failure or a
disagreeing review is not a provider outage. Do not use a separate OpenAI API
connection as backup.

Give each delegate the request and relevant context. For review or feedback,
keep their work read-only. Collect their responses and summarize the useful
findings, disagreements, and recommended next steps.

Do not wait idle. When a result arrives, check its findings against the code
at once and decide what to fix while the other delegates run. Do not edit
files while a delegate still reviews the same checkout. If the user's
instructions mark a delegate as non-blocking, do not wait for it; treat a
late result as feedback and do not record its score.

For a code review, ask each delegate for a score out of 10.
Count each full review pass as one round.
A fresh review after fixes starts a new round.

If the work ends in a pull request, put the results in the PR description.
Put this section before the model and harness line at the end:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Claude Opus | 7/10 | 9/10 |
| GPT Sol | 8/10 | 10/10 |
| Gemini 4 Carbon | 7/10 | 9/10 |
```

If a delegate gives no score, write `no score`. Do not invent one.
If the PR is open, edit the description. Do not post a comment for this.
If there is no PR, put the same results in the final reply only.

If you agree with their recommendations, make the changes and request a fresh
review after. Continue this process until all delegates are satisfied with the
outcome.

Do not let repeated reviews result in scope creep. It is your job to fight to
keep scope limited.
