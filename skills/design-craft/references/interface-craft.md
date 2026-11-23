# Interface craft reference

Use this to make specific design decisions and inspect their rendered result. Existing approved product rules take precedence over fallback values. A numerical rule supports judgment; it does not establish visual quality by itself.

## Composition and hierarchy

Start with the user's next decision and the information needed to make it. Give that decision visual priority through position, scale, grouping, and contrast. Make supporting information subordinate without making it unreadable. Use a few shared alignment lines and deliberate content widths. Avoid a new container, border, or card for every group when spacing and typography communicate the relationship.

Choose density for the task. A media discovery page can devote space to artwork; a policy table needs scanable comparisons. Translate the intended character into a few visible choices about composition, typography, and imagery so it can be judged in the result. Inspect the whole viewport: avoid oversized headings that displace the task, controls stranded in empty panels, and repetitive labels or helper subtitles. Distinctive design should come from useful composition and product character, not decorative novelty at the expense of comprehension.

## Spacing and dimensions

Reuse the project's scale. Without one, start with a 4px-based family such as 4, 8, 12, 16, 24, 32, 48, and 64px. Define semantic roles for control padding, within-group gaps, between-group gaps, section spacing, and page gutters. Related content should be closer than unrelated sections; do not assign the same gap everywhere.

Derive heights from readable type, line height, padding, and borders. Avoid fixed heights on variable content. Optical alignment, 1px borders, and icon strokes are legitimate exceptions to a spacing scale; document repeated exceptions as a reusable rule instead of accumulating magic numbers. Inspect nested padding and radius relationships so containers and their contents feel aligned.

## Typography with character

Choose a typographic direction for this product, not the agent's habitual font pair. Evaluate the actual alphabet, numerals, punctuation, language coverage, weights, licensing, and loading strategy. Prefer existing suitable fonts; use freely licensed, locally served assets when adding fonts. A second family must have a clear role rather than merely decorate headings.

Define a purposeful hierarchy of display/page title, section title, body, control, and metadata roles. Set family, size, weight, line height, text width, and tracking together. Explore character through proportion, contrast of weights and scales, editorial versus compact composition, and appropriate numeric styling. Creativity does not require adding more fonts.

Start readable body/control text near 16px on phones when no system exists, then judge the actual face and use. Tight display leading or tracking needs rendered inspection for collisions, clipping, and lost word spaces. Keep long reading lines roughly within 45–75 characters where appropriate; short task interfaces need different widths. Check translated labels, multiline titles, large numbers, missing metadata, and 200% zoom. Do not solve density by shrinking essential text.

## Color, surfaces, imagery, and controls

Use semantic tokens for text, surfaces, borders, actions, selection, success, warning, and danger. Preserve meaning across screens and states. A dark background does not require low-contrast labels, and every secondary element need not become a pill. Borders, shadows, and surface layers should clarify grouping or interaction.

Check actual rendered contrast, including translucent layers and artwork: target WCAG AA's 4.5:1 for ordinary text and 3:1 for large text and relevant non-text UI boundaries or states. Use text or semantics in addition to color. Keep hover, focus, pressed/selected, disabled, busy, and error states distinguishable where applicable.

Reuse icon family, stroke, size, and alignment rules. Give icons meaningful accessible names when acting as controls. Primary touch actions should generally offer about 44px targets; inspect compact exceptions and surrounding spacing. Use semantic controls, associate labels and errors with their fields, and provide visible keyboard focus. Modal dialogs need appropriate initial focus, contained keyboard navigation, and focus returned to the invoking control on close. Artwork needs a deliberate aspect ratio, crop, reserved space, and missing-image treatment. Respect reduced motion and avoid continuous decorative animation.

## Responsive behavior, not scaled desktop

Write down how the layout changes when content no longer fits. Decide whether navigation changes form, columns stack, panels become inline disclosures, tables scroll or gain a task-specific compact view, and actions move. Do not hide important functionality merely to make a screenshot fit. Preserve reading order and the user's place when adapting layouts.

Choose breakpoints at observed content pressure, using the project's existing breakpoints where appropriate. For an unrestricted web app, representative checks can include a narrow and ordinary phone around 320–430px, intermediate widths around 768–1024px, and a broad desktop around 1280–1600px. These are samples, not certification of every device; follow an explicitly narrower target.

Inspect page overflow, long unbroken values, open menus/panels, sticky actions, scroll containers, keyboard focus, and zoom. Use shrinkable grid/flex children, sensible wrapping, and content-driven heights. Check touch behavior and avoid hover-only access. For applicable mobile flows, account for safe areas, dynamic viewport height, and the on-screen keyboard. Browser emulation does not prove physical-device behavior.

## Review across screens and states

Render representative real components and screens with ordinary, sparse, long, and dense content. Check whether repeated controls, headings, gutters, statuses, and terminology retain the same meaning. Verify the states and recoveries that the actual journey supports. A component gallery helps consistency; a screenshot proves only its captured state; neither proves the whole application flow.

For an existing product, compare before and after. For a new direction, compare with the chosen reference and state the deliberate departures. When a difference recurs, fix the shared component or token and inspect its consumers rather than adding another per-page patch.
