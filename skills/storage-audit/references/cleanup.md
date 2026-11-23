# Approved cleanup and recovery

An audit or report selection never executes deletion. After the user approves a
named set, keep a local manifest of stable IDs, literal absolute paths, measured
bytes, effect, recovery and exclusions. Reuse that authorization in the same
session; ask only when scope, impact, ownership or interruption changes.

Immediately before mutation, verify path resolution, symlink/reparse parents,
current sizes, expected children, tracked/uncommitted project data and active
references. Check process executable, cwd, loaded mappings and open handles,
not just a process name. A cache can contain a live runtime: `uvx` environments,
npm `_npx` servers, browser automation installations and editor server versions
are examples. Do not break them to remove a warning or force an in-use cache.

Prefer native cleanup with explicit paths or profiles. Examples include `uv
cache clean --cache-dir <approved>`, npm cache clean with the approved cache,
`go clean -cache` with explicit GOCACHE and `go clean -modcache` with the approved
GOPATH. Keep automatic Go toolchain downloads disabled during cache cleanup.
For caches without a native per-directory operation, remove only the verified
literal cache root. A project's `.local-state` can also contain databases,
profiles, screenshots and evidence; never delete that parent as a shortcut.

Record every outcome and remeasure. Compare Git status and the affected app
interface, confirm excluded data remains reachable, and retain the manifest
outside any filesystem about to be stopped. Do not claim that the predicted
sum of files is the observed disk-space gain.

## WSL compaction

Only after explicit authorization for the interruption, prove the registered
distro's exact VHD path. Check for an already running compaction before starting
another. Prepare an elevated Windows-side worker with a persistent status file,
exclusive-VHD access check, error capture and service restoration in `finally`.
Save the handoff and baseline outside WSL; shutdown can kill this agent.

Inside the approved distro run `fstrim -v /` as root. Stop WSL and prevent the
WSL service from remounting the image while compacting. On a detached dynamic
VHD, use the available supported `Optimize-VHD -Mode Full` or reviewed diskpart
procedure. Never unregister a distro, convert the image or alter sparse-image
settings as an inferred cleanup step. Restore the original service state,
start the distro and verify mounting, tool health, retained data and actual host
free space. Read the worker status after reconnect before retrying anything.

If Linux data was deleted without compaction, report that its freed capacity is
inside the guest. It is not yet proven reclaimed host storage. Leave a failed
or unavailable verification explicit, with the exact recovery state.
