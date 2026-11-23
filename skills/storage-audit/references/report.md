# Report data and proposals

For a broad Windows disk audit, use an inventory-only snapshot together with
`--survey <measure_windows_tree.json>`. The survey must name the same host.
Enrichment adds each directory's direct-file bytes once, groups installations
using measured paths and package metadata, and retains unknown owners visibly.
The interactive folder tree shows directories of at least 50 MiB, with smaller
children aggregated; the raw survey preserves all rows. Its subtree totals
overlap and must never be summed as components. One volume survey is supported
per report; produce separate reports when multiple fixed volumes are relevant.
The physical used/free measurement and logical folder totals remain separate.

The bundled report is a portable, offline artifact with no network dependencies.
It uses T3 theme variables when embedded and a restrained system-font fallback
when opened standalone. No production app interface is being redesigned.

Collectors emit schema 1. Each snapshot names a host, platform, context, user,
capture timestamp, volumes, components, coverage and limits. A component ID is
a stable path hash within that platform; always retain its snapshot identity
alongside it. Measured components are disjoint file buckets, not subtree totals.
Installed-package estimates remain separate. The renderer accepts one current
snapshot per context, to reject accidental addition of overlapping rescans.
Replace an incomplete snapshot with a complete rescan; do not append it.

Use `--before previous.json` to compare the same context's volume ID and total
capacity. The before snapshot must be older. A missing match gives no delta.
A volume ID is not hardware identity proof: independently confirm the target,
especially across reboots or when drive letters or Linux device numbers change.

After investigating a candidate, supply `--proposals local-proposals.json` with
a list such as this. Every component ID must occur in a supplied snapshot.

```json
[
  {
    "id": "P-01",
    "label": "Review pip cache cleanup",
    "target": {"host": "example", "platform": "linux", "context": "native", "user": "example"},
    "component_ids": ["replace-with-real-component-id"],
    "paths": ["/home/example/.cache/pip"],
    "impact": "Cached packages must be downloaded again. No projects selected.",
    "recovery": "Download from the configured package index; offline use would be affected.",
    "evidence": "Record exact host/context, completed measurement, child inspection and active-reference checks here."
  }
]
```

The report does not treat this metadata as independently verified. The agent
must establish the cited facts. A selection requests a concrete proposal only,
never approval to execute it. After discussing consequences, explicit cleanup
approval names the IDs, exact scope, target context and allowed interruption.
Keep a separate outcome manifest with one result per approved ID and exclusions.

For uninstall proposals include installation and associated data, services and
dependencies. Say which histories remain, what an uninstaller removes, what
requires separate deletion, and how recovery works. Never infer uninstall
savings by adding package estimates to measured component sizes.

Reports contain private paths and package/process metadata. Outputs refuse to
overwrite existing files. Linux report files use mode 0600. On Windows, run the
Python renderer in a private destination with a verified user-only ACL because
POSIX mode bits do not establish Windows ACL privacy. The Windows collector sets
its JSON file ACL to the current user and SYSTEM. Do not publish these artifacts.
