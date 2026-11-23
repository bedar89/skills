import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { expect, test } from "bun:test";

const checker = join(import.meta.dir, "check-plan.mjs");
const rule =
	"Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.";

const validPlan = `# Demo

## How to read this
One box is one unit of work and names the evidence. Check a box only when its evidence exists. See playbooks/.
${rule}

## Program checklist
### Arm the program
### Spawn owners
### PR mechanics
### Verdict and merge
### Boot recipe
- [ ] Read installed skills from their absolute paths. /loop 1h status message

## PR 1
**Depends on.** None.
**Files.**
- [ ] Do the thing.
**Build.**
- [ ] Do the thing.
**You see.**
- [ ] Do the thing.
**Verify, unit.** ${rule}
- [ ] Check the thing.
**Verify, live.** ${rule} Ten lanes on \`example-model\` at the PR head
${Array.from({ length: 10 }, (_, i) => `- [ ] Lane ${i + 1}. Save \`lane-${i + 1}.png\`. Pass when evidence exists.`).join("\n")}
**Verify, perf.** ${rule}
- [ ] Metric. Recorded.
- [ ] Probe. Recorded.
- [ ] Baseline. Recorded.
- [ ] Rule. Recorded.
**Review gate.** None.
**Merge.**
- [ ] Merge when approved.

## Close the program
Close.

## Appendix Prototype evidence
Recorded.
`;

const runPlan = (example: string, expectedExit: number, plan = validPlan) => {
	const directory = mkdtempSync(join(tmpdir(), "check-plan-test-"));
	const file = join(directory, "plan.md");
	writeFileSync(file, plan + example);
	try {
		const result = spawnSync("node", [checker, file], { encoding: "utf8", cwd: directory });
		expect(result.status).toBe(expectedExit);
		return result;
	} finally {
		rmSync(directory, { recursive: true, force: true });
	}
};

test("requires installed-skill reading in an active checklist item", () => {
	const hidden = validPlan.replace("- [ ] Read installed skills from their absolute paths. /loop 1h status message", "```text\nRead installed skills\n```\n- [ ] /loop 1h status message");
	const result = runPlan("", 1, hidden);
	expect(result.stderr).toContain('Program checklist lacks "Read installed skills"');
});

test.each([
	["HTML comment", "<!--\n- [ ] Read installed skills\n-->"],
	["inline-opening HTML comment", "Example <!--\n- [ ] Read installed skills\n-->"],
	["indented code", "    - [ ] Read installed skills"],
])("does not count installed-skill markers in %s", (_name, hidden) => {
	const plan = validPlan.replace("- [ ] Read installed skills from their absolute paths. /loop 1h status message", hidden + "\n- [ ] /loop 1h status message");
	const result = runPlan("", 1, plan);
	expect(result.stderr).toContain('Program checklist lacks "Read installed skills"');
});

test("runs a copied checker outside the application repository", () => {
	const directory = mkdtempSync(join(tmpdir(), "installed-plan-check-"));
	try {
		const installedDirectory = join(directory, "custom skill");
		mkdirSync(installedDirectory);
		const installedChecker = join(installedDirectory, "check-plan.mjs");
		copyFileSync(checker, installedChecker);
		const file = join(directory, "plan.md");
		writeFileSync(file, validPlan);
		const result = spawnSync("node", [installedChecker, file], { cwd: directory, encoding: "utf8" });
		expect(result.status).toBe(0);
	} finally {
		rmSync(directory, { recursive: true, force: true });
	}
});

test("accepts ordinary, indented, and longer closing fences", () => {
	for (const indent of ["", " ", "  ", "   "])
		runPlan(`${indent}\`\`\`markdown\n## Example only\n${indent}\`\`\`\n`, 0);
	runPlan("```markdown\n## Example only\n````\n", 0);
});

test("accepts nested backticks and tilde info strings", () => {
	runPlan("````markdown\n```markdown\n## Example only\n```\n````\n", 0);
	runPlan("~~~markdown `info`\n## Example only\n ~~~\n", 0);
});

test("keeps mismatched, shorter, and suffixed closers inside the fence", () => {
	runPlan("````markdown\n~~~\n## Example only\n````\n", 0);
	runPlan("````markdown\n```\n## Example only\n````\n", 0);
	runPlan("````markdown\n``` info\n## Example only\n````\n", 0);
});

test("rejects headings and prose outside a proper close", () => {
	for (const suffix of ["  ", "\t"]) {
		const heading = runPlan(`\`\`\`markdown\n## Example only\n\`\`\`${suffix}\n## Example only\n`, 1);
		expect(heading.stderr).toContain('"## Example only" after Close the program is not an appendix');
	}

	const prose = runPlan("```markdown\nThis prose has a mid-sentence colon: inside code\n```\nThis prose has a mid-sentence colon: bad.\n", 1);
	expect(prose.stderr).toContain("mid-sentence colon");
});

test("rejects backtick info strings containing a backtick", () => {
	const result = runPlan("```markdown `invalid`\n## Example only\n```\n", 1);
	expect(result.stderr).toContain('"## Example only" after Close the program is not an appendix');
});

test("ignores prose punctuation inside matching multi-backtick code spans", () => {
	for (const count of [2, 3, 4]) {
		const delimiter = "`".repeat(count);
		runPlan(`Use ${delimiter}echo \`x\`: “quoted” — example${delimiter}.\n`, 0);
	}
});

test("checks prose following a multi-backtick span and unmatched delimiters", () => {
	const outside = runPlan("Use ``echo `x`: y``. Bad: prose.\n", 1);
	expect(outside.stderr).toContain("mid-sentence colon");
	const unmatched = runPlan("Use ``unclosed: bad` here.\n", 1);
	expect(unmatched.stderr).toContain("mid-sentence colon");
});


test.each(["fenced", "indented", "quoted"])("requires visible How to read this instructions instead of %s code", kind => {
	const begin = validPlan.indexOf("\n", validPlan.indexOf("## How to read this")) + 1;
	const end = validPlan.indexOf("## Program checklist");
	const body = validPlan.slice(begin, end).trim();
	const example = kind === "quoted" ? "> ```text\n" + body.split("\n").map(line => "> " + line).join("\n") + "\n> ```\n\n" : kind === "fenced" ? "```text\n" + body + "\n```\n\n" : body.split("\n").map(line => "    " + line).join("\n") + "\n\n";
	const result = runPlan("", 1, validPlan.slice(0, begin) + example + validPlan.slice(end));
	expect(result.stderr).toContain("How to read this lacks");
});


test("accepts an indented closing marker for an open HTML comment", () => {
	runPlan("", 0, validPlan.replace("## How to read this\n", "## How to read this\n<!-- explanation\n    -->\n"));
});


test("does not promote a checklist item after an HTML block opener", () => {
	const plan = validPlan.replace("- [ ] Read installed skills", "<!-- example -->- [ ] Read installed skills");
	const result = runPlan("", 1, plan);
	expect(result.stderr).toContain('Program checklist lacks "Read installed skills"');
});
