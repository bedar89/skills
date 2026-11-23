---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
disable-model-invocation: true
---

# How

Use the selected Codex model and reasoning level for this skill and its ordinary
workers. In Codex, omit model overrides. From another provider, use GPT-6.1 Sol
through the Codex subscription on high unless the user chooses otherwise.
Resolve IDs and options from the runtime catalog. Only genuine Codex
unavailability or limits allow an equivalent model through OpenRouter as backup;
report the route change. Do not use a separate OpenAI API connection as backup.

Explore the codebase to answer "how does X work?" questions.

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

## 1. Explain

Spawn one read-only general-purpose subagent that explores and explains in one pass: `Task` with `subagent_type: generalPurpose` and `readonly: true` in Cursor, `Agent` in Claude Code (`subagent_type: general-purpose`), `task` in OpenCode (`subagent_type: general`), `spawn_agent` in Codex. If your harness has no subagent tool, as in Pi without an extension, do the exploring and writing yourself. Give it the user's question and this brief:

> You are writing an architectural explanation for a senior engineer. Explore the codebase and write an explanation that a senior engineer unfamiliar with this area could read and walk away with a solid mental model. They should understand the architecture well enough to start working in it confidently. You have read-only access to the codebase.

## 2. Present

Present the subagent's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.
