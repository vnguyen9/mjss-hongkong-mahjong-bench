"""The documents match the rules files, the leaderboard builds, and nothing private is in the tree."""

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, hkma_profile, hkma_table, house_profile

sys.path.insert(0, str(ROOT / "scripts"))
from render_rules import render  # noqa: E402

from hkbench import bench, site  # noqa: E402


class RulesDocument(unittest.TestCase):
    def test_rules_md_tables_are_generated_from_the_rules_files(self):
        text = (ROOT / "RULES.md").read_text(encoding="utf-8")
        for tid in ("hk-hkma-v1", "hk-house-v1", "hk-chicken-v2"):
            m = re.search(r"<!-- rules:%s:begin -->\n(.*?)\n<!-- rules:%s:end -->" % (tid, tid), text, re.S)
            self.assertIsNotNone(m, tid)
            self.assertEqual(m.group(1), render(tid), "RULES.md is out of date for %s: run scripts/render_rules.py" % tid)

    def test_the_gaps_listed_in_rules_md_are_the_ones_pinned_by_tests(self):
        text = (ROOT / "RULES.md").read_text(encoding="utf-8")
        for phrase in ("No 包", "concealed kong keeps", "All Concealed Triplets ignores", "Last Tile from the Wall also counts",
                       "Nine Gates does not check", "Only an added kong", "Bless of Heaven and Bless of Earth ignore",
                       "Kongs after a claim", "shifting-meld"):
            self.assertIn(phrase, text)

    def test_house_table_is_active_and_scores_seven_pairs(self):
        t = json.loads((ROOT / "tables" / "hk-house-v1" / "table.json").read_text())
        self.assertEqual(t["status"], "active")
        self.assertNotIn("pending_reason", t)
        self.assertTrue((ROOT / "tables" / "hk-house-v1" / "rules.json").exists())
        self.assertFalse((ROOT / "tables" / "hk-house-v1" / "rules.pending.json").exists())
        self.assertTrue(house_profile().seven_pairs)
        self.assertFalse(hkma_profile().seven_pairs)


class Leaderboard(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp))
        self.results = self.tmp / "results"

    def make(self, spec, name):
        meta = bench.bot_meta(spec, name=name, track="bots", kind=None, trained_on="none", description=None,
                              cwd=None, hash_dir=None, hash_override=None)
        return bench.score(hkma_table(), spec, meta, deals=6, results_dir=self.results, skip_fairplay=True, quiet=True)

    def test_build_writes_json_and_a_self_contained_page(self):
        self.make("ref:random", "random")
        self.make("ref:faan_aware", "faan_aware")
        out = self.tmp / "site"
        index = site.build(self.results, out)
        data = json.loads((out / "leaderboard.json").read_text())
        self.assertEqual(data["schema"], "hkbench-leaderboard-1")
        self.assertEqual([t["id"] for t in data["tracks"]], ["bots", "llms", "humans"])
        self.assertEqual({t["id"]: t["status"] for t in data["tables"]}, {"hk-chicken-v2": "active", "hk-hkma-v1": "active", "hk-house-v1": "active"})
        self.assertEqual(len(data["rows"]), 2)
        for row in data["rows"]:
            for key in ("rank", "track", "table", "rules_track", "verification", "seed_tag", "ci95", "metric", "value", "points_per_hand", "games"):
                self.assertIn(key, row)
            self.assertEqual(row["verification"], "unverified")
        html = index.read_text()
        m = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
        self.assertEqual(json.loads(m.group(1))["rows"], data["rows"])
        self.assertEqual(html.count("</script>"), 2)
        self.assertIn("Coming", site.TRACKS[1]["note"])
        self.assertIn("Coming", site.TRACKS[2]["note"])

    def test_latest_run_per_bot_wins_and_ranks_are_shared_when_intervals_overlap(self):
        rows = [
            {"run_id": "a", "created_utc": "1", "track": "bots", "table": "t", "seed_tag": "public", "value": 5.0, "points_per_hand": 5.0,
             "ci95": [3.0, 7.0], "bot": {"name": "x", "sha256": "1"}},
            {"run_id": "b", "created_utc": "2", "track": "bots", "table": "t", "seed_tag": "public", "value": 4.0, "points_per_hand": 4.0,
             "ci95": [2.0, 6.0], "bot": {"name": "y", "sha256": "2"}},
            {"run_id": "c", "created_utc": "3", "track": "bots", "table": "t", "seed_tag": "public", "value": -9.0, "points_per_hand": -9.0,
             "ci95": [-11.0, -7.0], "bot": {"name": "z", "sha256": "3"}},
            {"run_id": "d", "created_utc": "9", "track": "bots", "table": "t", "seed_tag": "public", "value": -8.0, "points_per_hand": -8.0,
             "ci95": [-10.0, -6.0], "bot": {"name": "z", "sha256": "3"}},
        ]
        latest = site._latest(rows)
        self.assertEqual(sorted(r["run_id"] for r in latest), ["a", "b", "d"])
        site._rank(latest)
        ranks = {r["bot"]["name"]: r["rank"] for r in latest}
        self.assertEqual(ranks, {"x": 1, "y": 1, "z": 3})


class Privacy(unittest.TestCase):
    """Nothing that belongs to the maintainers' private systems is in the tree."""

    FORBIDDEN = [
        r"/Users/", r"\bTrello\b", r"trello\.com", r"[Ff]irebase", r"[Aa]pp ?[Cc]heck", r"api[_-]?key", r"\bsk-[A-Za-z0-9]{8,}",
        r"AIza[0-9A-Za-z_-]{20,}", r"@(gmail|icloud|lumio)", r"\.mlmodel", r"\.mlpackage", r"\.pt\b", r"\.ckpt", r"checkpoint",
        r"ppo_", r"neo_d1", r"neo_h1", r"mahjong_ai", r"mjss_v9", r"\bD1\b", r"Xcode ?Cloud", r"TestFlight",
        r"lumiodatalabs", r"clarkwkw/mahjong-ai", r"training code", r"model weights",
        r"BEGIN (RSA|PRIVATE)", r"password", r"(?:127\.0\.0\.1|localhost|(?:\d{1,3}\.){3}\d{1,3})",
    ]

    def test_no_private_strings_anywhere_in_the_tree(self):
        pattern = re.compile("|".join(self.FORBIDDEN))
        hits = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or ".pytest_cache" in path.parts:
                continue
            if path.relative_to(ROOT).parts[0] == "build":  # git-ignored scratch space, not the tree
                continue
            if path.suffix in (".gz",) or path.name == "test_docs_site.py":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                hits.append("%s is a binary file" % path.relative_to(ROOT))
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits.append("%s:%d: %s" % (path.relative_to(ROOT), n, line.strip()[:100]))
        self.assertEqual(hits, [])

    def test_result_logs_carry_no_private_paths(self):
        import gzip

        for log in (ROOT / "results").glob("logs/*.jsonl.gz"):
            with gzip.open(str(log), "rt") as f:
                text = f.read()
            for forbidden in self.FORBIDDEN:
                self.assertIsNone(re.search(forbidden, text, re.I), "%s contains %s" % (log, forbidden))
            self.assertNotIn("/home/", text)


if __name__ == "__main__":
    unittest.main()
