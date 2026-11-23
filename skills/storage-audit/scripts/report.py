#!/usr/bin/env python3
"""Render local collector snapshots as a portable, non-executing review."""
import argparse
import datetime as dt
import json
import ntpath
import os
import hashlib
from pathlib import Path


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if data.get("schema") != 1 or data.get("platform") not in ("linux", "windows"):
        raise ValueError(f"Unsupported collector snapshot: {path}")
    for key in ("host", "context", "user", "captured_at", "volumes", "components", "coverage"):
        if key not in data:
            raise ValueError(f"Missing {key}: {path}")
    dt.datetime.fromisoformat(data["captured_at"].replace("Z", "+00:00"))
    return data


def identity(data):
    return tuple(data[k] for k in ("host", "platform", "context", "user"))


def normal(path, platform):
    return path.replace("\\", "/").rstrip("/").lower() if platform == "windows" else path.rstrip("/")


def within(path, prefix, platform):
    a, b = normal(path, platform), normal(prefix, platform)
    return a == b or a.startswith(b + "/")


def attach_survey(snapshot, survey):
    if snapshot["components"]:
        raise ValueError("Survey enrichment requires an inventory-only snapshot, to avoid double counting")
    nodes = survey["result"]["directories"]
    child_files = [0] * len(nodes)
    for node in nodes:
        if node["parent"] >= 0:
            child_files[node["parent"]] += node["files"]
    rules = []
    source = json.loads((Path(__file__).resolve().parent.parent / "assets/apps.json").read_text())["windows"]
    for path, app, kind, boundary in source:
        for name, value in snapshot.get("environment_paths", {}).items():
            path = path.replace("%" + name + "%", value)
        if "%" not in path:
            rules.append((path, app, kind, boundary))
    for package in snapshot.get("packages", []):
        loc = (package.get("install_location") or "").rstrip("\\")
        if len(loc) > 8 and ntpath.isabs(loc) and ntpath.dirname(loc) not in ("", loc) and loc.lower() not in (
            "c:\\program files", "c:\\program files (x86)", "c:\\windows", snapshot.get("home", "").lower()):
            rules.append((loc, package["name"], "installation", False))
    rules.sort(key=lambda r: -len(r[0]))
    buckets = {}
    root = survey["root"].rstrip("\\")
    home = snapshot.get("home", "")
    for index, node in enumerate(nodes):
        if not node["direct_bytes"] and node["files"] == child_files[index]:
            continue
        path = node["path"]
        owner = next((r for r in rules if within(path, r[0], "windows")), None)
        if owner:
            bucket, app, kind, boundary = owner
        else:
            if home and within(path, home, "windows"):
                parts = ntpath.relpath(path, home).split("\\")
                depth = 3 if parts[0].lower() == "appdata" else 1
                bucket = ntpath.join(home, *parts[:depth])
            else:
                parts = ntpath.relpath(path, root + "\\").split("\\")
                bucket = ntpath.normpath(ntpath.join(root + "\\", *parts[:2]))
            app, kind, boundary = "Niet toegewezen · " + ntpath.relpath(bucket, root + "\\"), "unclassified", False
            if normal(path, "windows") == normal(survey["root"], "windows"):
                app, kind = "Systeembestanden in schijfhoofdmap", "system"
        component = buckets.setdefault(bucket.lower(), {"id": hashlib.sha256(bucket.lower().encode()).hexdigest()[:16],
            "path": bucket, "app": app, "kind": kind, "boundary": boundary, "logical_bytes": 0,
            "allocated_bytes": None, "files": 0, "latest_mtime": 0, "root": survey["root"]})
        component["logical_bytes"] += node["direct_bytes"]
        component["files"] += node["files"] - child_files[index]
    snapshot["components"] = list(buckets.values())
    snapshot["large_files"] = [{"path": f["path"], "logical_bytes": f["bytes"]} for f in survey["result"]["large_files"]]
    top = nodes[0]
    snapshot["coverage"] = [{"root": survey["root"], "complete": top["complete"], "files": top["files"],
        "errors": top["errors"], "skipped": {"reparse_or_offline": top["skipped"], "deadline": survey["result"]["deadline_reached"]}}]
    retained = [i for i, n in enumerate(nodes) if n["subtree_logical_bytes"] >= 50 * 1048576 or i == 0]
    mapping = {old: new for new, old in enumerate(retained)}
    tree = [{**nodes[i], "parent": mapping.get(nodes[i]["parent"], -1)} for i in retained]
    snapshot["survey"] = {"root": survey["root"], "directories": tree,
        "logical_bytes": top["subtree_logical_bytes"], "file_count": survey["result"]["file_count"],
        "captured_at": survey["captured_at"], "display_threshold_mib": 50, "errors": survey["result"]["errors"]}


def reconcile(snapshots, before):
    ids = [identity(s) for s in snapshots]
    if len(set(ids)) != len(ids):
        raise ValueError("Use one snapshot per host/platform/context/user; replace earlier rescans instead of adding them")
    prior = {identity(s): s for s in before}
    if len(prior) != len(before):
        raise ValueError("Ambiguous before snapshots for the same context")
    for data in snapshots:
        apps = {}
        for component in data["components"]:
            if component["logical_bytes"] < 0:
                raise ValueError("Negative component bytes")
            if component["app"] == "Unmapped":
                home=data.get("home", "")
                if home and within(component["path"], home, data["platform"]):
                    name=os.path.relpath(component["path"],home).split(os.sep)[0]
                else:
                    name=component.get("root", component["path"])
                component["app"]="Niet toegewezen · "+name
            app = apps.setdefault(component["app"], {"name": component["app"], "logical_bytes": 0,
                                                       "components": [], "running": [], "execution": []})
            app["logical_bytes"] += component["logical_bytes"]
            app["components"].append(component)
        for app in apps.values():
            paths = [c["path"] for c in app["components"]]
            app["running"] = [p for p in data.get("processes", []) if p.get("exe") and
                              any(within(p["exe"], path, data["platform"]) for path in paths)]
            app["execution"] = [e for e in data.get("execution", []) if
                                any(within(e["path"], path, data["platform"]) for path in paths)]
        data["apps"] = sorted(apps.values(), key=lambda a: -a["logical_bytes"])
        data["comparison"] = []
        old = prior.get(identity(data))
        if old:
            now_time = dt.datetime.fromisoformat(data["captured_at"].replace("Z", "+00:00"))
            old_time = dt.datetime.fromisoformat(old["captured_at"].replace("Z", "+00:00"))
            if old_time >= now_time:
                raise ValueError("Before snapshot must predate the current snapshot")
            for volume in data["volumes"]:
                match = next((v for v in old["volumes"] if v["id"] == volume["id"] and
                              v["total_bytes"] == volume["total_bytes"]), None)
                if match:
                    data["comparison"].append({"volume": volume["path"], "before_at": old["captured_at"],
                                               "before_free": match["free_bytes"], "after_free": volume["free_bytes"],
                                               "free_delta": volume["free_bytes"] - match["free_bytes"]})
    return {"schema": 1, "snapshots": snapshots}


def write_private(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w", encoding="utf-8") as f:
        f.write(content)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", action="append", required=True)
    p.add_argument("--before", action="append", default=[])
    p.add_argument("--output", required=True)
    p.add_argument("--json")
    p.add_argument("--proposals", help="Local JSON list of reviewed proposals; see references/report.md")
    p.add_argument("--survey", help="Whole-volume Windows tree survey; paired with its inventory-only input")
    args = p.parse_args()
    try:
        snapshots = [load(f) for f in args.input]
        if args.survey:
            survey = json.loads(Path(args.survey).read_text(encoding="utf-8-sig"))
            match = next((s for s in snapshots if s["platform"] == "windows" and
                          s["host"].casefold() == survey["host"].casefold()), None)
            if not match or survey.get("kind") != "directory-survey":
                raise ValueError("Survey must match an inventory-only Windows input on the same host")
            attach_survey(match, survey)
        result = reconcile(snapshots, [load(f) for f in args.before])
        proposals = json.loads(Path(args.proposals).read_text()) if args.proposals else []
        ids = set()
        for proposal in proposals:
            for field in ("id", "label", "paths", "impact", "recovery", "evidence", "component_ids", "target"):
                if not proposal.get(field):
                    raise ValueError(f"Proposal requires {field}")
            target = proposal["target"]
            snapshot = next((s for s in result["snapshots"] if identity(s) == identity(target)), None)
            known = {c["id"] for c in snapshot["components"]} if snapshot else set()
            if proposal["id"] in ids or not set(proposal["component_ids"]).issubset(known):
                raise ValueError("Duplicate proposal ID or unknown component ID")
            if any(not (ntpath.isabs(path) if target["platform"] == "windows" else path.startswith("/"))
                   for path in proposal["paths"]):
                raise ValueError("Proposal paths must be absolute within their target platform")
            ids.add(proposal["id"])
        result["proposals"] = proposals
        template = (Path(__file__).resolve().parent.parent / "assets/report.html").read_text()
        # Prevent HTML/script termination even when paths or package names are hostile.
        payload = json.dumps(result, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
        html = template.replace("__STORAGE_DATA__", payload)
        if Path(args.output).exists() or (args.json and Path(args.json).exists()):
            raise ValueError("Output exists; use a new report path")
        write_private(args.output, html)
        if args.json:
            write_private(args.json, json.dumps(result, indent=2))
    except (ValueError, KeyError, OSError) as e:
        p.error(str(e))
    print(f"Saved private report to {args.output}")


if __name__ == "__main__":
    main()
