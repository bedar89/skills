import { mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, utimesSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { expect, test } from "bun:test";

const audit = join(import.meta.dir, "worktree-audit.sh");

test.each([
	["ignored", "hold-contents"],
	["untracked", "hold-contents"],
	["clean", "review-clean"],
	["spaces", "review-clean"],
	["local-ref-snapshot", "review-clean"],
	["index-snapshot", "review-clean"],
])("audit preserves %s worktrees for review", (kind, expectedBucket) => {
	const root = mkdtempSync(join(tmpdir(), "worktree-content-test-"));
	const bin = join(root, "bin");
	const env = { ...process.env, PATH: bin + ":" + (process.env.PATH ?? ""), HOME: join(root, "home"), GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1", GIT_CONFIG_COUNT: "0" };
	const primary = join(root, kind === "spaces" ? "project with spaces" : "project");
	const worktree = join(root, kind === "spaces" ? "task with spaces" : "task");
	const git = (...args: string[]) => {
		const result = spawnSync("git", args, { cwd: root, env, encoding: "utf8" });
		expect(result.status).toBe(0);
		return result.stdout.trim();
	};
	try {
		mkdirSync(bin);
		for (const name of ["origin", "gh"]) writeFileSync(join(bin, name), "#!/bin/sh\nprintf '[]\\n'\n", { mode: 0o700 });
		git("init", "-q", "-b", "main", primary);
		git("-C", primary, "config", "user.name", "Fixture");
		git("-C", primary, "config", "user.email", "fixture@example.invalid");
		writeFileSync(join(primary, ".gitignore"), "private.env\n");
		git("-C", primary, "add", ".");
		git("-C", primary, "commit", "-qm", "fixture");
		git("-C", primary, "worktree", "add", "-q", "-b", "task", worktree, "main");
		let base = "main";
		let previousRef = "";
		if (kind === "local-ref-snapshot") {
			const remote = join(root, "remote.git");
			git("init", "-q", "--bare", "-b", "main", remote);
			git("-C", primary, "remote", "add", "origin", remote);
			git("-C", primary, "push", "-q", "origin", "main");
			previousRef = git("-C", primary, "rev-parse", "refs/remotes/origin/main");
			writeFileSync(join(primary, "later.txt"), "later remote state\n");
			git("-C", primary, "add", "later.txt");
			git("-C", primary, "commit", "-qm", "advance remote");
			git("-C", primary, "push", "-q", "origin", "main");
			git("-C", primary, "update-ref", "refs/remotes/origin/main", previousRef);
			base = "origin/main";
		}
		const valuable = join(worktree, kind === "ignored" ? "private.env" : "first-draft.md");
		if (kind === "ignored" || kind === "untracked") writeFileSync(valuable, "Irreplaceable fixture content\n");
		const index = git("-C", worktree, "rev-parse", "--git-path", "index");
		if (kind === "index-snapshot") {
			const later = new Date(Date.now() + 60000);
			utimesSync(join(worktree, ".gitignore"), later, later);
		}
		const indexBytes = readFileSync(index);
		const indexMtime = statSync(index).mtimeMs;
		const result = spawnSync("bash", [audit, "-b", base, primary], { cwd: root, env, encoding: "utf8" });
		expect(result.status).toBe(0);
		const rows = result.stdout.split("\n").filter(line => !line.startsWith("SIZE") && line.includes("\t"));
		expect(rows.length).toBe(1);
		expect(rows[0].split("\t")[7]).toBe(expectedBucket);
		if (kind === "ignored" || kind === "untracked") expect(readFileSync(valuable, "utf8")).toBe("Irreplaceable fixture content\n");
		if (kind === "index-snapshot") {
			expect(readFileSync(index)).toEqual(indexBytes);
			expect(statSync(index).mtimeMs).toBe(indexMtime);
		}
		if (kind === "local-ref-snapshot") expect(git("-C", primary, "rev-parse", "refs/remotes/origin/main")).toBe(previousRef);
	} finally {
		rmSync(root, { recursive: true, force: true });
	}
});
