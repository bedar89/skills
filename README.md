# Bedar's skills

The skills I use to build software, review changes, understand code, and maintain
my own systems. This personal collection contains my own skills and selected
upstream skills. The [sources](#sources) below credit their authors. Skills are
adapted for my workflow, including Forgejo support and model choices.

Each skill has its own folder with instructions and any scripts, references, or
assets it needs. The catalog links open the skill instructions.

Forgejo is the main repository for this collection. A public GitHub mirror is
planned so the skills can be read without logging in.

[Use a skill](#use-a-skill) · [Browse the collection](#browse-the-collection) ·
[Install](#install) · [Make changes](#make-changes)

## Use a skill

In Codex, name the skill with `$` and describe the result you want:

```text
$teach Explain how authentication works in this project and why it was built this way.

$better-layout Review this settings screen. Make the grouping and reading order clearer.

$council Review this proposal. Report the findings without changing any files.
```

Council uses Codex, Anthropic, and Google reviewers by default. That requires
the model access stated in its instructions. You can request Codex-only reviewers.

Choose a skill for the task at hand. Some skills call others: `teach` uses `how`
and `why`, while `full-send` uses `sol-loop`, `file-pr`, and `babysit-pr`.

Project instructions and the scope of the request still apply. For delivery,
`full-stop` ends with a PR ready for review; `full-send` continues through merge.

## Browse the collection

### Plan and build

| Skill | What it does |
| --- | --- |
| [define-goal](skills/define-goal/SKILL.md) | Turn an idea into a concrete goal with measurable success criteria. |
| [in-your-own-words](skills/in-your-own-words/SKILL.md) | Check that the agent understands the goal before work starts. |
| [architect](skills/architect/SKILL.md) | Work out types, interfaces, and module boundaries before implementation. |
| [arena](skills/arena/SKILL.md) | Compare parallel attempts and combine the strongest parts. |
| [swarm](skills/swarm/SKILL.md) | Split independent work across agents and return one report. |
| [figure-it-out](skills/figure-it-out/SKILL.md) | Develop a verifiable approach for a large or unfamiliar task. |
| [poteto-mode](skills/poteto-mode/SKILL.md) | Apply detailed engineering playbooks for investigation, implementation, and delivery. |

### Design interfaces

| Skill | What it does |
| --- | --- |
| [design-craft](skills/design-craft/SKILL.md) | Carry an interface from design choices through implementation and visual checks. |
| [better-layout](skills/better-layout/SKILL.md) | Improve grouping, alignment, reading order, and responsive structure. |
| [better-ui](skills/better-ui/SKILL.md) | Refine surfaces, icons, shadows, and motion. |
| [show-me](skills/show-me/SKILL.md) | Explain a topic through diagrams, code sketches, or focused HTML artifacts. |

### Check code and behavior

| Skill | What it does |
| --- | --- |
| [tdd](skills/tdd/SKILL.md) | Use a failing test to guide a change when requested or when a cheap regression test fits. |
| [typescript-best-practices](skills/typescript-best-practices/SKILL.md) | Apply TypeScript rules when reading or changing TypeScript code. |
| [benchmark-checklist](skills/benchmark-checklist/SKILL.md) | Check what a benchmark measures before trusting its result. |
| [create-verification-skill](skills/create-verification-skill/SKILL.md) | Create a project skill that exercises the app through its real interface. |
| [maintain-verification-skill](skills/maintain-verification-skill/SKILL.md) | Compare a project's verification skill with the source and running app. |
| [constraint-driven-development](skills/constraint-driven-development/SKILL.md) | Define quality requirements and the checks that enforce them. |
| [source-driven-development](skills/source-driven-development/SKILL.md) | Verify version-dependent choices against official docs and the installed runtime. |
| [observability-and-instrumentation](skills/observability-and-instrumentation/SKILL.md) | Add the logs, metrics, or traces needed to understand runtime behavior. |

### Review and learn

| Skill | What it does |
| --- | --- |
| [council](skills/council/SKILL.md) | Gather independent reviews and work through the findings. |
| [sol-loop](skills/sol-loop/SKILL.md) | Repeat review with one reviewer until the findings are resolved. |
| [interrogate](skills/interrogate/SKILL.md) | Challenge a change or design and prove the findings through execution. |
| [deslop](skills/deslop/SKILL.md) | Remove unnecessary additions and style drift from the branch diff. |
| [no-comments](skills/no-comments/SKILL.md) | Review comments and look for constraints that belong in code. |
| [correct](skills/correct/SKILL.md) | Prevent a recurring mistake through structure, types, lint, or tests. |
| [reflect](skills/reflect/SKILL.md) | Review a session for lessons that belong in existing skills. |

### Work with pull requests

| Skill | What it does |
| --- | --- |
| [file-pr](skills/file-pr/SKILL.md) | Open a concise PR that explains the problem, change, and proof. |
| [babysit-pr](skills/babysit-pr/SKILL.md) | Follow a PR through CI and review, and address actionable failures. |
| [full-stop](skills/full-stop/SKILL.md) | Finish the work and leave a PR ready for a human to merge. |
| [full-send](skills/full-send/SKILL.md) | Finish, verify, review, publish, monitor, and merge the change. |
| [modernize](skills/modernize/SKILL.md) | Bring an old PR up to date and reassess whether it still belongs. |
| [takeover](skills/takeover/SKILL.md) | Continue an existing PR, branch, or agent thread. |
| [leaving-pr-comments](skills/leaving-pr-comments/SKILL.md) | Format comments posted on Forgejo or GitHub. |

### Explain, write, and hand over

| Skill | What it does |
| --- | --- |
| [how](skills/how/SKILL.md) | Trace how a subsystem works and where responsibilities belong. |
| [why](skills/why/SKILL.md) | Find the history and evidence behind a design decision. |
| [teach](skills/teach/SKILL.md) | Combine how something works with why it was built that way. |
| [bro](skills/bro/SKILL.md) | Restate the last explanation in plain language. |
| [technical-writing](skills/technical-writing/SKILL.md) | Write and review technical documentation. |
| [unslop](skills/unslop/SKILL.md) | Cut filler, inflated language, and common agent-writing habits. |
| [recall](skills/recall/SKILL.md) | Reconstruct recent work from history and the current state. |
| [handoff-small](skills/handoff-small/SKILL.md) | Save a brief session handoff in a temporary file. |
| [show-me-your-work](skills/show-me-your-work/SKILL.md) | Keep a reviewable record of decisions during long tasks. |

### Personal tools

| Skill | What it does |
| --- | --- |
| [storage-audit](skills/storage-audit/SKILL.md) | Investigate disk usage and prepare evidence-backed cleanup choices. |
| [watch-youtube](skills/watch-youtube/SKILL.md) | Discuss a YouTube video using its images, speech, and timestamps. |
| [i-have-adhd](skills/i-have-adhd/SKILL.md) | Adapt replies with clear next actions, numbered steps, and fewer tangents. |

### Engineering principles

These focused skills cover recurring decisions. Other skills can load them when
needed, so they remain separate files in the collection.

<details>
<summary>Browse the 24 principles</summary>

| Principle | Apply it when |
| --- | --- |
| [attack-the-premise](skills/principle-attack-the-premise/SKILL.md) | Repeated fixes fail because they share an untested assumption. |
| [boundary-discipline](skills/principle-boundary-discipline/SKILL.md) | Deciding where validation and error handling belong. |
| [build-the-lever](skills/principle-build-the-lever/SKILL.md) | A script or tool can carry out or prove nontrivial work. |
| [encode-lessons-in-structure](skills/principle-encode-lessons-in-structure/SKILL.md) | The same correction keeps returning. |
| [exhaust-the-design-space](skills/principle-exhaust-the-design-space/SKILL.md) | A new interaction or architecture needs competing prototypes. |
| [experience-first](skills/principle-experience-first/SKILL.md) | Weighing user experience against scope and implementation convenience. |
| [explain-the-number](skills/principle-explain-the-number/SKILL.md) | Measuring something or acting on a measurement. |
| [fix-root-causes](skills/principle-fix-root-causes/SKILL.md) | Tracing a symptom back to the first incorrect state. |
| [foundational-thinking](skills/principle-foundational-thinking/SKILL.md) | Choosing core data structures before writing logic. |
| [guard-the-context-window](skills/principle-guard-the-context-window/SKILL.md) | Large outputs and repeated reads consume the working context. |
| [laziness-protocol](skills/principle-laziness-protocol/SKILL.md) | A refactor risks adding unnecessary abstractions or layers. |
| [make-operations-idempotent](skills/principle-make-operations-idempotent/SKILL.md) | An operation must tolerate retries, crashes, or partial completion. |
| [migrate-callers-then-delete-legacy-apis](skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | Replacing an internal API that still has callers. |
| [minimize-reader-load](skills/principle-minimize-reader-load/SKILL.md) | Code requires too many layers or hidden assumptions to follow. |
| [model-the-domain](skills/principle-model-the-domain/SKILL.md) | Stateful logic or repeated branches suggest a missing domain model. |
| [never-block-on-the-human](skills/principle-never-block-on-the-human/SKILL.md) | Considering a permission question for authorized, reversible work. |
| [outcome-oriented-execution](skills/principle-outcome-oriented-execution/SKILL.md) | A migration needs to converge on its target architecture. |
| [prove-it-works](skills/principle-prove-it-works/SKILL.md) | Checking the real result before declaring a task complete. |
| [redesign-from-first-principles](skills/principle-redesign-from-first-principles/SKILL.md) | Integrating a new requirement into an existing design. |
| [separate-before-serializing-shared-state](skills/principle-separate-before-serializing-shared-state/SKILL.md) | Concurrent workers might write to the same state. |
| [sequence-verifiable-units](skills/principle-sequence-verifiable-units/SKILL.md) | Breaking a large change into units with observable results. |
| [subtract-before-you-add](skills/principle-subtract-before-you-add/SKILL.md) | Removing dead code and redundant checks before adding a replacement. |
| [test-behavior-not-implementation](skills/principle-test-behavior-not-implementation/SKILL.md) | Writing or reviewing a test. |
| [type-system-discipline](skills/principle-type-system-discipline/SKILL.md) | Designing types or function signatures in a statically typed language. |

</details>

## Install

To read or copy instructions, browse the skill folders. No installation is needed.

For Codex, clone this repository and place the selected folders from `skills/`
in `~/.agents/skills/`. You can copy the folders or create directory symlinks to
this clone. Keep each complete folder, including any scripts, references, and
assets. Retain the applicable author and license notices from [NOTICE.md](NOTICE.md)
and any license supplied with the skill. Preserve existing skills with the same
name instead of overwriting them.
See the [Codex skills documentation](https://learn.chatgpt.com/docs/build-skills.md)
for discovery locations and installation through the built-in skill installer.

Some skills call others. For example, `teach` needs `how`, `why`, and `unslop`.
`full-send` uses `sol-loop`, `file-pr`, `babysit-pr`, and, when posting review
replies, `leaving-pr-comments`. Install the dependencies named in each invoked
skill too. Installing the complete collection keeps those bundled dependencies
available. Model choices are
written in the relevant skills and do not change the client's model settings.

This collection has no custom installer. Placing the skill folders does not
change global repository instructions or client settings. Configure those separately.
Copying skills creates independent copies; directory links read updates from
this clone. If an update does not appear in Codex, restart it.

Some skills need tools such as Python, Bun, FFmpeg, yt-dlp, `tea` for Forgejo,
or `gh` for GitHub. Their instructions list the requirements. Both Python PR
watchers use Unix file locks and need Linux, macOS, or WSL. They do not run under native Windows Python. The GitHub PR helper
stops when required checks are bound to a specific app. Use the host's full
check tools for that policy.

## Make changes

If you have access to the main Forgejo repository, make changes and open pull
requests there. Once available, use the GitHub mirror for reading. Keep mirror credentials
outside Git.

Edit skills in [skills/](skills/) directly. Keep changes within the requested
scope and retain the original author and license notices for external material.
Keep supporting files beside the instructions they belong to:

```text
skills/<name>/
  SKILL.md       Instructions and when to use the skill
  references/    Supporting material, if needed
  scripts/       Executable helpers, if needed
  assets/        Templates and other files, if needed
```

For a new skill, create a folder with matching frontmatter:

```yaml
---
name: my-skill
description: What the skill does and when to use it.
---
```

Add it to the catalog above. Before renaming or removing a skill,
check which other skills call it and remove its old installation link.
For example, `technical-writing` uses `unslop`, and `full-stop` uses `full-send`.
Keep referenced files together and run a helper's own checks when its behavior changes.

Repository instructions are in [AGENTS.md](AGENTS.md). Original author and license
notices are preserved in [NOTICE.md](NOTICE.md).

There is no automatic upstream update process.

## Checks

The [validation workflow](.forgejo/workflows/validate.yml) checks skill names and
descriptions using a YAML parser and verifies inline and reference-style local
file links outside code examples. It runs the
Python helper scenarios and the Bun watcher and plan tests, plus a strict
TypeScript check. It runs on pull requests and pushes to `main`.

The [credential scan](.forgejo/workflows/secrets.yml) uses Gitleaks to check new
pull-request commits for recognizable tokens and keys. It runs locally on the
CI runner, requires no Gitleaks account or API key, and redacts findings in logs.
It does not identify every kind of personal information.

These checks do not prove that an agent follows a skill correctly. They do not
execute paid model calls, live media downloads, or the Windows PowerShell tests.
External URLs and links to page sections are not checked automatically. Verify
the affected behavior separately when changing those parts.

## License

Bedar's original code, skills, documentation, and contributions use the
[MIT license](LICENSE). External material retains its original license.
[NOTICE.md](NOTICE.md) preserves author and license notices. The Apache 2.0
license for `define-goal` remains [beside that skill](skills/define-goal/LICENSE.txt).

## Sources

This collection includes skills based on work by:

- [Lauren Tan, pstack](https://github.com/backnotprop/pstack).
- [Theo Browne, tstack](https://github.com/t3dotgg/tstack).
- [OpenAI, skills](https://github.com/openai/skills).
- [Ayoub Ghriss, i-have-adhd](https://github.com/ayghri/i-have-adhd).
- [HumanLayer, skills](https://github.com/humanlayer/skills).
- [Addy Osmani, agent-skills](https://github.com/addyosmani/agent-skills).
- [Jakub Krehel, skills](https://github.com/jakubkrehel/skills).
- [Cursor, cursor-team-kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit).

Local adaptations include Forgejo support, model choices written per skill,
and removal of a separate observability checklist. This is a personal
collection, maintained independently of those upstream projects.
