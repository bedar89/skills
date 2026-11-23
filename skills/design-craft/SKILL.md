---
name: design-craft
description: "Design coherent, distinctive application interfaces and carry the agreed design through implementation and rendered verification. Use for new app design, substantial UI changes, meaningful design alternatives, or visual consistency reviews. Not for routine copy edits, mechanical fixes, or backend work."
---

# Design craft

Add design judgment to the existing engineering workflow. Use the project's real components and constraints; do not replace its workflow with a new toolchain. Complete the agreed scope, including its responsive behavior and relevant states. Do not silently substitute an MVP, static shell, or reduced feature set.

Choose the authorized mode before proceeding. Research and critique produce evidence and recommendations in the response or requested report, without changing project files. Exploration may create isolated mock artifacts and stops at the selection gate. Implementation may change the approved project surface and repair in-scope defects; it can include necessary preliminary research and mocks, while preserving the selection gate. Apply the sections below within that mode; invoking this skill does not authorize a transition to another mode.

## Establish the design target

- Identify whether the request is research, critique, exploration, or implementation. A review does not authorize edits. Preserve repository permissions and approval gates.
- Inspect the current rendered interface when available, project instructions, approved designs, tokens, components, and styling dependencies. Separate current implementation from historical mocks. Follow existing browser-tool routing; inspect an existing preview only when its target and permitted use are established.
- For a new project, establish the users, main jobs, content density, important journeys, roles, and delivery scope before choosing a visual system. Infer what the brief and repository establish; ask only for missing decisions that materially change the design. State reasonable defaults without making the user complete a design questionnaire.
- Distinguish example incidents and fixture data from product requirements. Turn an example into a default, category, or permanent choice only when the product need is established.
- Explicitly choose the device strategy from the task: phone-led, desktop-led with a considered compact layout, or equally important across sizes. If the brief gives no narrower target, design for phone, tablet, and desktop. Responsive quality is part of delivery, not later polish.
- Establish a concise design brief: target outcome, surfaces and states in scope, identity to preserve or establish, device strategy, constraints, and acceptance evidence. In research/critique, keep it in the response; in exploration, with the mocks; in implementation, use the project's existing design owner or task notes. Do not create a parallel specification when one exists.

## Establish direction before styling

For an existing product, extend its approved visual language. Treat an already selected concrete design within the requested scope as an implementation target, not an invitation to restart exploration. An approved house style or flow alone does not approve a new substantial screen or interaction; apply the relevant mock-selection gate to that change. A redesign requires an explicit redesign brief.

For a new product or unresolved direction, examine a few relevant references. Prefer real application journeys to decorative landing pages; available local sources are valid when external access is unavailable or prohibited. Identify the source and screens or behavior actually inspected, and state missing access rather than implying inspection. Explain what each reference contributes to this product: information structure, density, typography, navigation, or interaction. Separate useful principles from features and styling that do not fit. Do not impose Linear, Apple, a fashionable font pair, a card grid, or a particular library as the default answer.

Choose dependencies after understanding the design. Reuse suitable project components. Consider an existing styled library or unstyled primitives when they solve actual interaction needs; weigh visual control, accessibility, stack fit, licensing, maintenance, and migration cost. No paid dependency or unrelated installation as a side effect.

## Explore real alternatives when needed

Follow the user's and repository's mock-selection rules. For a substantial unresolved design choice, prepare distinct standalone HTML alternatives before editing real app components. Keep them local and separate from the active app. Use the project's real assets and styling where practical; state any approximation. Default to ordinary HTML files, not a review service or decision form. Use a collaborative review tool only when requested.

Before building, name the design question and the difference each alternative explores. Usually two or three are enough; honor an explicit requested count. Differences must change composition, hierarchy, interaction, density, or typographic character. Three colors of the same layout are one direction.

Compare the same meaningful content and task across alternatives. Show representative screens, difficult content, and compact and wide layouts so a direction can be judged beyond its opening screen. Controls needed to judge the design question must work locally; do not rebuild every product feature in each alternative. Label simulated data and behavior. Never present mock interactions as real backend behavior.

Inspect the alternatives yourself. Replace indistinguishable or visibly weak options before presenting them. Explain where each works, its cost, and your recommendation. Let the user inspect at actual size and choose; stop at the applicable selection gate. Reuse the chosen target on later implementation requests unless new feedback changes it. Do not add an image-generation round as a compulsory intermediary.

Record what the selection approves: direction, interaction, composition, or exact implementation, including explicit exceptions. Directional approval allows repairing criticized states within that direction; do not reproduce those states or reopen the whole choice to fix them.

## Build a project system, then complete the work

Read [the craft reference](references/interface-craft.md) when designing, implementing, or visually reviewing a surface. Apply the relevant parts; do not run a full redesign for a narrow correction.

During authorized implementation, keep intentional decisions in the existing design owner, shared tokens, components, and representative states. Reuse complete patterns such as selecting an episode or recovering a failed submission, not only buttons. Examples should import real components when practical rather than maintain copied implementations. Consolidate repeated rules at their owner; do not fix each screen with unrelated overrides.

For implementation, complete every agreed journey and affected caller. Include the loading, empty, validation, success, access, and failure/recovery states that can actually occur. Derive this set from the product's behavior; do not invent irrelevant screens. Use realistic content and data boundaries. Do not leave dead controls, unannounced placeholders, or mobile behavior deferred to a later phase.

## Prove the design in the rendered product

- Compare the implementation with the selected target and adjacent product screens. Check hierarchy, composition, typography, spacing, density, and consistency; name specific elements, not claims such as "premium" or "polished".
- Exercise the affected journey, including back/edit/cancel, relevant errors and recovery, and keyboard use. Run applicable repository checks. Separate fixture, browser, provider, and physical-device evidence.
- Inspect compact, intermediate, and wide layouts for the chosen device strategy, plus relevant zoom and long-content cases. Check controls and open panels, not just the initial page. A shrinking screenshot or passing build does not prove responsive behavior.
- During implementation, fix in-scope defects and recheck what changed. In critique, report defects and their smallest suitable correction without applying it. Report unrelated defects without silently expanding scope. If the design input, browser, or a required backend is unavailable, state the exact gap; source inspection alone cannot establish visual or functional acceptance.
- Read back the completed scope and evidence. Report what is implemented, what was observed, and any remaining blocker. Do not call it complete while agreed behavior is missing or unverified. Do not promise flawless design from a checklist.
