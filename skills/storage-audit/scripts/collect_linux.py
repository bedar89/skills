#!/usr/bin/env python3
"""Metadata-only Linux/WSL storage collector. Never performs cleanup."""
import argparse
import collections
import datetime as dt
import hashlib
import heapq
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import time


def command(argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=8)
        return {"command": argv, "status": "ok" if p.returncode == 0 else "failed",
                "output": p.stdout[:400000], "exit_code": p.returncode}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"command": argv, "status": type(e).__name__}


def collect(roots, seconds, large_mib, rules_path, output):
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    deadline = time.monotonic() + seconds
    home = str(Path.home())
    rules = json.loads(Path(rules_path).read_text())["linux"]
    rules = sorted([(os.path.abspath(os.path.expanduser(p)), a, k, b)
                    for p, a, k, b in rules], key=lambda r: -len(r[0]))
    requested = list(dict.fromkeys(os.path.abspath(os.path.expanduser(p)) for p in roots))
    memory_mounts=set()
    try:
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            fields, kind=line.split(' - ',1)
            if kind.split()[0] in ('tmpfs','ramfs','proc','sysfs','devtmpfs'):
                memory_mounts.add(fields.split()[4].replace('\\040',' '))
    except (OSError, ValueError):
        pass
    selected, excluded = [], []
    for p in sorted(requested, key=lambda p: (len(p), p)):
        try:
            if p in memory_mounts:
                excluded.append({"path":p,"reason":"memory-filesystem-does-not-consume-disk"})
                continue
            if os.path.islink(p) or not os.path.isdir(p):
                excluded.append({"path": p, "reason": "not-a-directory-or-symlink"})
                continue
            dev = os.stat(p).st_dev
            if any(p.startswith(r + "/") and os.stat(r).st_dev == dev for r in selected):
                excluded.append({"path": p, "reason": "covered-by-parent"})
            else:
                selected.append(p)
        except OSError:
            excluded.append({"path": p, "reason": "inaccessible"})
    components, seen, large, coverage = {}, set(), [], []
    for root in selected:
        row = {"root": root, "complete": True, "files": 0, "errors": 0,
               "skipped": collections.Counter(), "examples": []}
        dev = os.stat(root).st_dev
        stack = [root]
        while stack:
            if time.monotonic() >= deadline:
                row["complete"] = False
                row["skipped"]["deadline"] += len(stack)
                break
            directory = stack.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if time.monotonic() >= deadline:
                            row["complete"] = False
                            row["skipped"]["deadline"] += 1
                            break
                        try:
                            s = entry.stat(follow_symlinks=False)
                            if stat.S_ISLNK(s.st_mode):
                                row["skipped"]["symlink"] += 1
                                continue
                            if s.st_dev != dev:
                                row["skipped"]["other-filesystem"] += 1
                                row["complete"] = False
                                continue
                            if stat.S_ISDIR(s.st_mode):
                                stack.append(entry.path)
                                continue
                            if not stat.S_ISREG(s.st_mode):
                                continue
                            if os.path.abspath(entry.path) == os.path.abspath(output):
                                continue
                            owner = next((r for r in rules if entry.path == r[0] or
                                          entry.path.startswith(r[0] + "/")), None)
                            if owner:
                                bucket, app, kind, boundary = owner
                            else:
                                rel = os.path.relpath(entry.path, root).split(os.sep)
                                bucket = os.path.join(root, *rel[:min(2, len(rel) - 1)])
                                app, kind, boundary = "Unmapped", "unclassified", False
                            c = components.setdefault(bucket, {
                                "id": hashlib.sha256(bucket.encode()).hexdigest()[:16],
                                "path": bucket, "app": app, "kind": kind,
                                "boundary": boundary, "logical_bytes": 0,
                                "allocated_bytes": 0, "files": 0, "old_180d_bytes": 0,
                                "latest_mtime": 0, "root": root})
                            c["logical_bytes"] += s.st_size
                            identity = (s.st_dev, s.st_ino)
                            if identity not in seen:
                                seen.add(identity)
                                c["allocated_bytes"] += s.st_blocks * 512
                            c["files"] += 1
                            c["latest_mtime"] = max(c["latest_mtime"], s.st_mtime)
                            if time.time() - s.st_mtime > 180 * 86400:
                                c["old_180d_bytes"] += s.st_size
                            row["files"] += 1
                            if s.st_size >= large_mib * 1048576:
                                heapq.heappush(large, (s.st_size, entry.path))
                                if len(large) > 100:
                                    heapq.heappop(large)
                        except OSError as e:
                            row["errors"] += 1
                            row["complete"] = False
                            if len(row["examples"]) < 8:
                                row["examples"].append({"path": entry.path, "error": type(e).__name__})
            except OSError as e:
                row["complete"] = False
                row["errors"] += 1
                if len(row["examples"]) < 8:
                    row["examples"].append({"path": directory, "error": type(e).__name__})
        row["skipped"] = dict(row["skipped"])
        coverage.append(row)
    volumes = []
    for root in selected:
        usage = shutil.disk_usage(root)
        volumes.append({"id": str(os.stat(root).st_dev), "path": root,
                        "total_bytes": usage.total, "free_bytes": usage.free})
    volumes = list({v["id"]: v for v in volumes}.values())
    processes = []
    for p in Path("/proc").glob("[0-9]*"):
        try:
            if p.stat().st_uid != os.getuid():
                continue
            refs = {}
            for key in ("exe", "cwd"):
                try:
                    refs[key] = os.readlink(p / key)
                except OSError:
                    pass
            fds = []
            try:
                for fd in (p / "fd").iterdir():
                    target = os.readlink(fd)
                    if target.startswith("/") and len(fds) < 20:
                        fds.append(target)
            except OSError:
                pass
            processes.append({"pid": int(p.name), **refs, "open_paths_sample": fds})
        except OSError:
            pass
    inventories = []
    if shutil.which("dpkg-query"):
        inventories.append(command(["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Installed-Size}\n"]))
    elif shutil.which("rpm"):
        inventories.append(command(["rpm", "-qa", "--qf", "%{NAME}\t%{VERSION}\t%{SIZE}\n"]))
    if shutil.which("findmnt"):
        inventories.append(command(["findmnt", "--json", "--output", "TARGET,SOURCE,FSTYPE"]))
    if shutil.which("systemctl"):
        inventories.append(command(["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--plain"]))
        inventories.append(command(["systemctl", "--user", "list-units", "--type=service", "--all", "--no-pager", "--plain"]))
    return {"schema": 1, "captured_at": started, "host": platform.node(),
            "platform": "linux", "context": os.environ.get("WSL_DISTRO_NAME", "native"),
            "user": Path.home().name, "os": platform.platform(), "home": home,
            "volumes": volumes, "components": list(components.values()),
            "large_files": [{"path": p, "logical_bytes": n} for n, p in sorted(large, reverse=True)],
            "processes": processes, "inventories": inventories, "coverage": coverage,
            "excluded_roots": excluded,
            "limits": ["No human-use history collected; mtime is file activity only.",
                       "Allocated bytes deduplicate inodes, not reflinks; directory metadata excluded.",
                       "Open paths are a sample, not proof that a candidate is inactive.",
                       "Inventory commands have separate 8-second limits and may truncate at 400000 characters.",
                       "Containers, other users, secondary mounts and non-system packages need targeted follow-up."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", action="append")
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--large-mib", type=float, default=100)
    parser.add_argument("--rules", default=str(Path(__file__).resolve().parent.parent / "assets/apps.json"))
    args = parser.parse_args()
    if args.seconds <= 0 or args.large_mib < 0:
        parser.error("seconds must be positive and large-mib nonnegative")
    output = Path(args.output).absolute()
    if output.exists():
        parser.error("output already exists; use a new snapshot path")
    result = collect(args.root or [str(Path.home()), "/var", "/usr", "/opt", "/nix", "/tmp", "/srv"],
                     args.seconds, args.large_mib, args.rules, output)
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved {len(result['components'])} components to {output}")


if __name__ == "__main__":
    main()
