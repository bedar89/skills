# Evidence and accounting

## App footprint

A component is a disjoint set of measured files, attributed by an exact path
rule, an installer location, or a reviewed owner. Parent-looking paths in the
collector output can represent only their own bucket; they exclude nested
cache buckets. Never use such a bucket's byte count to authorize deleting its
whole parent. Only `boundary: true` entries identify a complete cache boundary,
and an incomplete scan still invalidates their apparent completeness.

Keep installation, runtime versions, sessions, databases, caches, logs, projects,
backups and container images/volumes distinguishable. Preserve unmapped data
instead of guessing. The report includes all package records separately; a
package manager estimate is not another component to add to measured files.

Linux logical bytes count path entries. Allocated file bytes count unique
`(device, inode)` identities, exclude directory/filesystem metadata and assign
shared links to their first encountered bucket. Per-app allocated values are
therefore not authoritative reclaimable bytes. Linux reflink sharing is not
resolved. Windows enumeration measures logical file lengths; NTFS compression,
sparse allocation and hardlinks make these an upper bound, not physical usage.
Use native allocated-byte/identity investigation for large ambiguous Windows
targets if the approval depends on an exact saving. Volume free space is the
final host-level measurement.

WSL `df` capacity is virtual. The Linux filesystem is guest content inside a
host VHDX. Show them in separate contexts. Never add the host VHD and its guest
contents, or compare their free-space deltas as if they were the same disk.
`fstrim` reports discarded ranges; that number is not space reclaimed on C:.

## Use evidence

| Evidence | What it supports | What it does not support |
| --- | --- | --- |
| Running executable or service | Active now, possibly background activity | A human opened the app |
| Windows BAM execution record for this user's exact executable | Execution observed at a timestamp | Complete history or last interactive use |
| Package/registry install date | Installation metadata | Last use or uninstall safety |
| Latest component mtime | File activity, possibly sync/updater/indexer | App execution or human use |
| No process or execution record | No evidence in the inspected sources | Never used, abandoned or safe to delete |

Do not read browser history, messages, shell history, session contents, tokens,
private keys or credentials to infer use. A request for disk sizes does not
authorize such content inspection. BAM is optional and version-dependent;
permission failures and missing records must stay visible. Collector process
records contain executable paths only, not command-line arguments or secrets.

## Coverage and proposals

The collector records scan roots, deadlines, denied paths, skipped mounts,
reparse/cloud paths and unavailable tools. Sampling and time limits cannot
justify a complete-app total. Scan the largest missing surface once with an
explicit narrower scope. Do not sum overlapping roots or silently merge scans
from different machines. A physically shared file is not a duplicate-delete
candidate. Only call distinct copies duplicates after comparing content and
confirming which copies provide recovery or ownership.

Automatic cache suggestions are investigation candidates with a byte ceiling,
not approval-ready instructions. Resolve active usage, package semantics,
re-downloadability and non-cache children. For uninstall proposals show the
installed app, its measured associated data, kept/deleted histories, services,
dependencies and recovery route. An uninstaller may retain all app data.
