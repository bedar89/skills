# Collection routes

Use independent evidence, not repeated recursive scans of the same directories.
Choose routes relevant to the proven platform. All commands below are read-only
unless explicitly described as cleanup in the separate cleanup reference.

## Built-in collectors

`measure_windows_tree.ps1` surveys an entire proven Windows volume using native
.NET metadata enumeration. It records all directory direct-file and subtree
logical bytes, the largest files, denied paths, skipped reparse/offline entries
and a deadline. Subtree rows overlap. Report enrichment uses direct-file bytes
exactly once, then retains folders of at least 50 MiB for interactive navigation.
The complete raw JSON retains smaller directories. Follow up excluded paths
only when they can change the conclusion; never hydrate cloud data just to scan.
Get-Disk/Get-Partition and DriveInfo establish disk/partition/volume capacity
separately. Root pagefiles and secondary disk images must not disappear from
an app-only inventory. Native allocation queries for dominant sparse/compressed
files help reconcile logical totals with actual used capacity.

`collect_linux.py` scans the home directory, `/var`, `/usr`, `/opt`, `/nix`, `/tmp` and `/srv`
when present. It stays on each root's filesystem, skips symlinks, records
unique inode blocks, large files, age aggregates and active executable/cwd/fd
references. Package metadata comes from `dpkg-query` or `rpm`; services come
from systemd. Defaults can be overridden with `--root`, `--seconds` and
`--large-mib`. Output directories are created privately; output JSON contains
paths and metadata, never file contents.

`collect_windows.ps1` uses native .NET enumeration. Its default roots are the
current user profile, both Program Files directories, ProgramData and Windows.
It skips reparse points and offline/cloud recall entries rather than hydrating
them. Installed apps come from HKCU/HKLM uninstall registry keys, never
`Win32_Product` because that can trigger MSI repair. Processes expose executable
paths only. Services expose names/states, not command lines. BAM records are
restricted to the current user's SID and explicitly marked as execution evidence.
Fixed volumes and registered WSL images are reported separately. Registry
EstimatedSize is an installer estimate, not a measured total. A deadline produces
partial results with coverage notes, not an exception discarding all progress.
Use `-InventoryOnly` when pairing metadata with a whole-volume tree survey.

Run the Windows script via a Windows-native path; a script stored in WSL can be
addressed through its `wslpath -w` result. Do not start stopped distros to collect
their usage without permission, and do not assume the default distro is the
target. Never stop WSL during an audit.

## Targeted follow-up

- **Unknown app paths:** inspect the largest unmapped buckets, uninstall
  InstallLocation, Start menu shortcut targets and existing project docs. Add
  only evidence-backed exact/prefix mappings in `assets/apps.json` or pass
  `--rules` with a local extension. Inspect a boundary's actual children before
  suggesting removal.
- **Nix:** `nix path-info --json` for an explicit closure, profile metadata and
  GC roots explain retained data. `nix-store --gc --print-dead` can clean stale
  root metadata even when it deletes no store contents; disclose that side
  effect and do not call it strictly read-only. Never run actual GC in an audit.
  Abandoned build directories are separate from the store and need process/PID
  proof before any later cleanup.
- **Docker/Podman:** inspect the current local context and query `system df -v`
  only when the daemon is already available. Record image, build-cache and
  volume sizes and shared layers. Never start Docker, pull images or prune as
  part of measurement. Volumes can contain irreplaceable databases.
- **Non-system installations:** inspect existing tool metadata for npm global
  packages, uv tools, pipx, Conda environments, Flatpak, Snap and Nix profiles
  when those tools are installed. Use local listing commands, never installation,
  upgrades, environment activation or network-backed package discovery. On
  Windows supplement uninstall records with `Get-AppxPackage` for the current
  user and existing winget/Chocolatey/Scoop manifests where relevant. Pair
  manifests with actual executable paths and data directories; app-store and
  CLI copies may coexist. Record this route as unavailable or unexamined if it
  was not run. A system-package inventory alone is not complete.
- **Services:** correlate already-running services with their executable, data,
  logs and dependencies using local metadata. Do not emit command lines or
  environment values, and never stop a service to measure it. Per-user and
  system services are separate. Container daemons may hold space in deleted
  but open files; inspect file-descriptor metadata with permission, without
  reading contents. Unlinked files and filesystem metadata help explain gaps
  between directory totals and actual volume usage.
- **Package versions:** compare actual running executable paths, current
  symlinks, package-manager manifests and installed versions. Multiple versions
  alone do not prove an old runtime is unused; editors and MCP servers may keep
  running from earlier installations.
- **Windows system data:** pagefile, swap, hibernation, WinSxS, Installer and
  recovery partitions are not ordinary files to delete. Use Windows' supported
  analysis interfaces if these dominate. Do not change sleep, recovery or
  virtual-memory policy to make an audit look successful.
- **Large and old files:** collector large-file rows and old-byte counts guide
  inspection. Old mtime is neither last access nor last app use. Archives,
  encrypted backups, VM disks and media need an owner/retention decision.
- **Duplicate candidates:** start with equal size and plausible duplicate paths.
  Content hashing is an optional targeted read, not a default full-disk pass.
  Check file identities/hardlinks and recovery purpose before claiming savings.

Complete the report's coverage notes with the result of relevant follow-up
routes. If installed apps, containers, usage records or a secondary volume were
not inspected, name that limit instead of presenting the audit as exhaustive.
