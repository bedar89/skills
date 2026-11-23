---
name: storage-audit
description: Audit workstation storage across Windows and WSL or Linux, group app installations with their caches, sessions and other data, and present evidence-backed cleanup proposals or measured results visually.
---

# Storage audit

Use an inventory, not a list of directories to delete. Explain the complete
footprint of an app and what the user would lose by removing each part.
The collectors and report generator are read-only apart from their output files.
They never uninstall, prune, trim, stop services, compact disks or delete data.

## Start with the disk, not examples

For a broad request such as "what is eating my disk", treat named apps as
examples, not scope limits. First establish the physical disk and partition
layout, actual capacity/used/free bytes of every mounted fixed volume, and the
largest top-level directories and root files. Explain where the whole disk goes
before zooming into app ownership. A single app scan is only a smoke test, not
delivery of a disk audit.

On Windows run the fast whole-volume survey once per relevant fixed volume,
then collect installed-app and process metadata without another recursive scan:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/measure_windows_tree.ps1 -Root C:\ -OutputPath C:\Users\example\storage-review\tree.json
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/collect_windows.ps1 -InventoryOnly -OutputPath C:\Users\example\storage-review\windows.json
```

Use the proven user's private output directory, not the example literally.
Pair this volume survey with the Windows inventory through `report.py --survey
tree.json --input windows.json`. Additional fixed volumes need their own survey
and report. Directory rows are subtree totals and overlap; only direct-file
buckets may be added. Show Windows system files, installed programs, user data,
development residue, VM/container disks, free space and the net accounting gap.
Never silently assign inaccessible space or logical/physical differences to
"other files" as though measured.

Follow the largest branches, including unknown owners outside standard roots.
Look for development dependencies across projects/worktrees, archived source,
build outputs, package-manager stores, multiple runtime versions, recovery
copies, downloads/media, app profiles and logs. Classify these after discovery.
`node_modules` inside a shipped app is installation data, and a browser backup
is recovery data. Neither becomes disposable because its name resembles a cache.
For WSL first measure the host image, then explain its guest contents separately.
Do not add the guest breakdown to the host total.

## Establish scope and collect

Prove the hostname, OS, user, mounted volumes and WSL distro before measuring.
Honor an existing diagnosis-only scope. Creating this report grants no cleanup
permission. Keep raw JSON and HTML local and private; never upload them for proof.

Run the applicable collectors with a new private output directory outside the
scanned roots when practical. The scan has a time budget and reports partial
coverage rather than pretending to have examined every file.
Resolve script paths against this skill directory, not the caller's workspace.

```sh
python3 scripts/collect_linux.py --output /tmp/storage-review/linux.json
```

Windows, either from Windows PowerShell or WSL interop:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/collect_windows.ps1 -OutputPath C:\Users\example\storage-review\windows.json
```

Adapt the output path to the proven user. Do not assume that example paths name
the intended device. For a narrow rescan, pass explicit `--root` values to the
Linux collector or `-Roots` to PowerShell. Never scan a WSL-mounted Windows drive
with Linux `du` when native Windows enumeration is available. Do not launch
overlapping scans to compensate for slow progress. See [collection.md](references/collection.md)
for additional package, container, service, large-file and usage investigations.

## Reconcile the evidence

Read [evidence.md](references/evidence.md) before interpreting results.

- Use disk free-space measurements for actual host capacity and reclaimed space.
  Directory logical bytes, allocated file blocks, registry estimates and VHD
  length answer different questions. Never add Linux contents to its host VHD.
- Bring installation, versions, cache, sessions, work, backups and logs together
  by app. Automatic rules identify only known owners. Inspect unmapped large
  components and explicitly add justified rules; do not attribute shared Python,
  Node or Nix stores to one app that happens to use them.
- Show installed-package records alongside measured data. Missing or overlapping
  install paths mean the footprint is incomplete, not zero. Apps without an
  uninstall record can still have several GiB of data.
- Last execution, a currently running process, file modification, installation
  date and last human use are separate evidence. Unknown is a valid result.
  Lack of observed use is never proof that an app can be removed.
- Cover volume totals, directories, large files, software/package inventories,
  running apps and services, caches, versions, archives and containers. Mark
  unavailable, denied, skipped or budget-limited checks and resolve the largest
  unexplained surfaces before presenting a broad audit as complete.

## Produce the review surface

```sh
python3 scripts/report.py --input /tmp/storage-review/linux.json --input /path/to/windows.json --output /tmp/storage-review/report.html --json /tmp/storage-review/report.json
```

Use `--before` with earlier collector JSON to show volume free-space deltas.
Compare the same machine, context and volume. Capture the before measurement
immediately before an approved action; unrelated background changes remain a
limit of the observed delta. No invented baseline or guaranteed savings.

Read [report.md](references/report.md) to attach evidence-backed proposals or
interpret snapshot accounting and before/after comparisons.
The report offers app search, component details, usage evidence, coverage and
unselected proposal checkboxes. Selection produces a review request with stable
IDs and exact paths. It does not execute or authorize deletion. If Lavish is
available, open the local HTML and keep its feedback poll active during review;
otherwise the copyable request works without Lavish. Follow available preview
and HTML-render tools for inline delivery. Inspect desktop and mobile rendering,
and both light and dark modes in the standalone/Lavish page as well as the
embedded preview. Standalone text and background must follow the same theme;
a transparent iframe background can otherwise turn dark-mode text white-on-white.

For a detailed proposal, annotate the relevant findings with verified impact,
recovery and scope. Do not offer an entire app directory for removal merely
because some children are disposable. A browser profile, conversation database,
project, recovery archive or container volume is not a cache.

## Execute only an approved selection

Read [cleanup.md](references/cleanup.md) only when cleanup is requested. An
approval applies to the named targets and consequences, not adjacent directories
or other devices. Reuse authorization already present in the session; do not
ask again for the same list. Recheck paths, ownership, active references and
current measurements immediately before action. Use native cleanup commands
where available, preserve active runtimes and record an outcome for every ID.

Re-measure and verify app behavior or the exact affected interface. Report
host-space gain separately from free space inside a still-large WSL image.
WSL shutdown or compaction needs explicit interruption authorization and a
Windows-side recovery/status record because it can kill the agent itself.
