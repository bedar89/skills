# Forgejo PR operations

Use this reference when the checkout or supplied PR URL identifies a Forgejo
instance. Resolve the host, owner, repository, head, and base from the real
remote and PR. For an unknown host, verify the forge before choosing tools.
GitHub and Origin commands in the
calling skill apply only to their supported hosts.

Prefer connected Forgejo tools that address the target instance. Otherwise use
an existing authenticated `tea` login for that host, with explicit `--login` and
`--repo`. Keep credentials in the configured client. Read the returned PR URL
and verify its host and repository before acting on it.

## Create, read, and update

Use the instance's `/swagger.v1.json` for its API contract. Paths below are
relative to `/api/v1/`:

- `GET repos/{owner}/{repo}/pulls/{index}` reads the PR, including `base.ref`,
  `base.sha`, `head.sha`, `state`, `draft`, `mergeable`, and `merged`.
- `POST repos/{owner}/{repo}/pulls` creates a PR with explicit `head`, `base`,
  `title`, and `body`. Check for an existing PR first.
- `PATCH repos/{owner}/{repo}/pulls/{index}` edits the body, title, or base.
- `GET repos/{owner}/{repo}/commits/{sha}/statuses` reads checks for that head.
- `GET repos/{owner}/{repo}/branches/{branch}` reads effective required checks
  and approval count. Follow pagination when reading statuses and reviews.
- `GET repos/{owner}/{repo}/pulls/{index}/reviews` reads review decisions.
  Its `/{id}/comments` endpoint reads inline comments and their resolution.
- `GET repos/{owner}/{repo}/issues/{index}/comments` reads conversation comments.

For CLI reads, for example:

```sh
tea api --login <login> --repo <owner/repo> 'repos/{owner}/{repo}/pulls/<index>'
```

Use structured tool arguments for writes. With `tea api`, put the exact JSON
body in a private temporary file and pass `--data @<file> --method POST` or
`--method PATCH`. Use returned URLs; Forgejo PR links use `/pulls/<index>`.
An unavailable supported tool or API is a blocker, not a reason to try `gh`.

## Watch and assess readiness

A status question gets one status pass, not a watcher. When monitoring is requested,
follow the runtime's watcher rules. Use a harness watcher only when it supports
this Forgejo instance. The GitHub watchers bundled by tstack and pstack do not
read Forgejo. The parent PR owner watches; delegated reviewers do not.

When the harness has no suitable watcher, use
`../../babysit-pr/scripts/forgejo-pr-wait` relative to this reference:

```sh
forgejo-pr-wait <pr-url> --login <login> --until ready
```

Use the script's absolute path. It only makes GET requests, reports real events,
and exits 0 when ready or merged, 1 when attention is needed, and 2 on invalid
input or a duplicate watcher. `--until green` covers checks only;
`--until any-change` returns after a new event. Restart after handling an event
or pushing a fix. Use one watcher per PR and release it on handoff.

Before reporting readiness, read the current head, base, exact-head checks,
required approvals, unresolved feedback, and mergeability. Check freshness
against the actual remote base. Missing or unreadable evidence stays unknown.
The helper's verdict does not replace repository-specific review or test gates.
For a stack, assess the lowest unmerged PR; the GitHub queued-stack watcher is
not a Forgejo stack monitor.

## Comments and merging

Post conversation comments with the connected comment tool or the issues
comments endpoint. Use the instance schema for inline review replies and
resolution; GitHub's reply endpoint is not interchangeable. Apply
[leaving-pr-comments](../../leaving-pr-comments/SKILL.md) when posting on the
user's behalf and read back the comment URL before resolving feedback.

Merge only within the user's authorization and repository protections. Use the
connected merge tool or `POST repos/{owner}/{repo}/pulls/{index}/merge`, with the
allowed `Do` method, expected `head_commit_id`, and `force_merge: false`.
A scheduled merge request is not a completed merge. Read back `merged`,
`merge_commit_sha`, and the actual base before reporting success. For a stack,
land one PR at a time, then retarget its child to the intended base and recheck.

For `full-stop`, cancel an existing scheduled merge through
`DELETE repos/{owner}/{repo}/pulls/{index}/merge` when present. Inspect the live
UI or a supported API to confirm scheduling state; the ordinary PR payload does
not expose it on every version. Do not enable scheduled merge or infer that it
is disabled merely because the PR is open.

API paths were checked against Bedar's live instance schema on 2026-11-17.
See [Forgejo API usage](https://forgejo.org/docs/latest/user/api/usage/) for API
versioning, pagination, and schema discovery.
