import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from collect_linux import collect
from report import reconcile, attach_survey


class StorageTests(unittest.TestCase):
    def test_disjoint_buckets_hardlinks_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            cache = root / "cache"
            cache.mkdir()
            (root / "data").write_bytes(b"x" * 8192)
            (cache / "wheel").write_bytes(b"y" * 8192)
            os.link(cache / "wheel", cache / "wheel-hardlink")
            (root / "loop").symlink_to(root, target_is_directory=True)
            rules = Path(tmp) / "rules.json"
            rules.write_text(json.dumps({"linux": [[str(cache), "App", "cache", True],
                                                    [str(root), "App", "data", False]]}))
            result = collect([str(root), str(cache)], 10, 0, rules, Path(tmp) / "out.json")
            self.assertEqual(sum(c["logical_bytes"] for c in result["components"]), 24576)
            self.assertEqual(sum(c["allocated_bytes"] for c in result["components"]),
                             (root / "data").stat().st_blocks * 512 + (cache / "wheel").stat().st_blocks * 512)
            self.assertEqual(sum(c["files"] for c in result["components"]), 3)
            self.assertEqual(result["coverage"][0]["skipped"]["symlink"], 1)
            self.assertEqual(result["excluded_roots"][0]["reason"], "covered-by-parent")
            result = collect([str(root)], 0, 0, rules, Path(tmp) / "out.json")
            self.assertFalse(result["coverage"][0]["complete"])

    def snapshot(self, context="native"):
        return {"schema": 1, "host": "fixture", "platform": "linux", "context": context,
                "user": "example", "captured_at": "2026-10-21T10:00:00+00:00", "os": "fixture",
                "components": [{"id": "data", "app": "Codex", "path": "/test/.codex",
                                "kind": "data", "logical_bytes": 100, "allocated_bytes": 200,
                                "files": 1, "latest_mtime": 1}],
                "processes": [{"exe": "/test/.codex-other/program"}],
                "volumes": [{"id": "one", "path": "/", "total_bytes": 1000, "free_bytes": 500}],
                "coverage": [], "large_files": [], "limits": [], "excluded_roots": []}

    def test_context_accounting_and_execution_boundaries(self):
        s = self.snapshot()
        old = copy.deepcopy(s)
        old["captured_at"] = "2026-10-21T09:00:00+00:00"
        old["volumes"][0]["free_bytes"] = 300
        result = reconcile([s, self.snapshot("WSL")], [old])
        self.assertEqual(result["snapshots"][0]["comparison"][0]["free_delta"], 200)
        self.assertEqual(result["snapshots"][1]["comparison"], [])
        self.assertEqual(result["snapshots"][0]["apps"][0]["running"], [])
        with self.assertRaises(ValueError):
            reconcile([s, s], [])
        with self.assertRaises(ValueError):
            reconcile([s], [s])

    def test_portable_report_script_injection_and_private_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = Path(tmp) / "input.json", Path(tmp) / "report.html"
            s = self.snapshot()
            s["components"][0]["path"] = '</script><script>window.INJECTED=true</script>'
            source.write_text(json.dumps(s))
            cmd = [sys.executable, str(Path(__file__).parent / "report.py"), "--input", str(source), "--output", str(out)]
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertNotIn('</script><script>window.INJECTED', out.read_text())
            self.assertEqual(out.stat().st_mode & 0o777, 0o600)
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_proposals_are_bound_to_the_target_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, proposals, out = (Path(tmp) / name for name in ("input.json", "proposals.json", "report.html"))
            s = self.snapshot()
            source.write_text(json.dumps(s))
            proposal = {"id": "P-01", "label": "Review data", "paths": ["/test/.codex"],
                        "impact": "History would be lost", "recovery": "Backup required",
                        "evidence": "Fixture only", "component_ids": ["data"],
                        "target": {k: s[k] for k in ("host", "platform", "context", "user")}}
            proposal["target"]["context"] = "another-distro"
            proposals.write_text(json.dumps([proposal]))
            cmd = [sys.executable, str(Path(__file__).parent / "report.py"), "--input", str(source),
                   "--proposals", str(proposals), "--output", str(out)]
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(out.exists())
            proposal["target"]["context"] = s["context"]
            proposals.write_text(json.dumps([proposal]))
            subprocess.run(cmd, check=True, capture_output=True)

    def test_whole_volume_survey_counts_direct_bytes_once(self):
        snapshot=self.snapshot()
        snapshot.update(platform="windows", context="host", components=[], home="C:\\Users\\example",
                        packages=[{"name":"Tool", "install_location":"C:\\Apps\\Tool"}])
        def node(path,parent,direct,total,files):
            return {"path":path,"parent":parent,"direct_bytes":direct,"subtree_logical_bytes":total,
                    "files":files,"errors":0,"skipped":0,"complete":True}
        survey={"root":"C:\\","captured_at":snapshot["captured_at"],"result":{
            "directories":[node("C:\\",-1,10,35,4),node("C:\\Apps",0,0,25,3),
                           node("C:\\Apps\\Tool",1,20,20,2),node("C:\\Apps\\misc",1,5,5,1)],
            "large_files":[],"file_count":4,"errors":[],"deadline_reached":False}}
        attach_survey(snapshot,survey)
        self.assertEqual(sum(c["logical_bytes"] for c in snapshot["components"]),35)
        self.assertEqual(sum(c["files"] for c in snapshot["components"]),4)
        self.assertEqual(next(c for c in snapshot["components"] if c["app"]=="Tool")["logical_bytes"],20)
        with self.assertRaises(ValueError):
            attach_survey(snapshot,survey)


if __name__ == "__main__":
    unittest.main()
