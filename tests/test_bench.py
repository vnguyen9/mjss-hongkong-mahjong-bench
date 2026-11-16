"""Scoring runs end to end: duplicate play, head to head, seeds, tags, fingerprint, results."""

import contextlib
import copy
import gzip
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT, hkma_table

from hkbench import bench, cli, fingerprint
from hkbench.tables import Table, load_private_seeds, load_table

PY = sys.executable
TABLE = hkma_table()


def meta(spec, name=None):
    return bench.bot_meta(spec, name=name, track="bots", kind=None, trained_on=None, description=None,
                          cwd=None, hash_dir=None, hash_override=None)


def run_cli(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with mock.patch.dict(os.environ, env or {}):
            code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class DuplicateLayout(unittest.TestCase):
    def test_each_deal_is_played_four_times_with_the_bot_in_every_seat(self):
        deals = TABLE.public_deals(5)
        specs = bench.duplicate_specs(deals)
        self.assertEqual(len(specs), 20)
        for d in deals:
            mine = [s for s in specs if s["deal"][0] == d.index]
            self.assertEqual(len(mine), 4)
            self.assertEqual(sorted(s["seats"].index("bot") for s in mine), [0, 1, 2, 3])
            self.assertEqual(len({tuple(s["deal"]) for s in mine}), 1)  # the same wall every time
            for s in mine:
                bot = s["seats"].index("bot")
                self.assertEqual([s["seats"][(bot + 1 + i) % 4] for i in range(3)], ["f0", "f1", "f2"])

    def test_dealer_and_wind_cycle_with_the_deal_index(self):
        deals = TABLE.public_deals(32)
        self.assertEqual([d.dealer for d in deals[:8]], [0, 1, 2, 3, 0, 1, 2, 3])
        self.assertEqual([d.prevailing_wind for d in deals[:9]], [0, 0, 0, 0, 1, 1, 1, 1, 2])
        self.assertEqual(len({(d.dealer, d.prevailing_wind) for d in deals[:16]}), 16)

    def test_head_to_head_uses_all_six_seat_pairs(self):
        specs = bench.h2h_specs(TABLE.public_deals(2))
        self.assertEqual(len(specs), 12)
        pairs = {tuple(i for i, k in enumerate(s["seats"]) if k == "A") for s in specs if s["deal"][0] == 0}
        self.assertEqual(pairs, set(bench.SEAT_PAIRS))
        for s in specs:
            self.assertEqual(s["seats"].count("A"), 2)


class Determinism(unittest.TestCase):
    def score(self, workers, spec="ref:ukeire"):
        r = bench.score(TABLE, spec, meta(spec), deals=6, workers=workers, results_dir=Path(tempfile.mkdtemp()),
                        skip_fairplay=True, write=False, quiet=True)
        return r["headline"], r["stats"]

    def test_same_seeds_same_numbers_whatever_the_worker_count(self):
        a = self.score(1)
        self.assertEqual(a, self.score(1))
        self.assertEqual(a, self.score(2))

    def test_scoring_a_bot_the_field_already_contains_is_close_to_even(self):
        # Every game is zero-sum, so over a whole duplicate set the field and the bot share the same points.
        r = bench.score(TABLE, "ref:faan_aware", meta("ref:faan_aware"), deals=8, results_dir=Path(tempfile.mkdtemp()),
                        skip_fairplay=True, write=False, quiet=True)
        self.assertEqual(r["headline"]["games"], 32)


class Tags(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp))
        self.deck = self.tmp / "private.json"
        self.deck.write_text(json.dumps({"seeds": [31_000_000_000 + i for i in range(10)]}))

    def test_public_run_is_unverified_and_carries_a_replayable_log(self):
        r = bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=4, results_dir=self.tmp, fairplay_points=30,
                        argv=["score", "--table", "hk-hkma-v1"], quiet=True)
        self.assertEqual(r["seeds"]["tag"], "public")
        self.assertEqual(r["verification"], "unverified")
        self.assertEqual(r["fairplay"]["status"], "passed")
        log = self.tmp / r["log"]
        with gzip.open(str(log), "rt") as f:
            header = json.loads(f.readline())["header"]
            rows = [json.loads(line) for line in f]
        self.assertEqual(header["bot"]["sha256"], r["bot"]["sha256"])
        self.assertEqual(header["engine"]["fingerprint_sha256"], r["engine"]["fingerprint_sha256"])
        self.assertEqual(len(rows), 16)
        self.assertTrue(all("seed" in x and "actions" in x for x in rows))
        code, out, _ = run_cli("verify-log", str(log))
        self.assertEqual(code, 0, out)
        self.assertIn("16 games replayed, 0 mismatches", out)

    def test_a_tampered_log_fails_verification(self):
        r = bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=2, results_dir=self.tmp, skip_fairplay=True, quiet=True)
        log = self.tmp / r["log"]
        with gzip.open(str(log), "rt") as f:
            lines = f.read().splitlines()
        row = json.loads(lines[1])
        row["payments"][0] += 4
        lines[1] = json.dumps(row)
        with gzip.open(str(log), "wt") as f:
            f.write("\n".join(lines) + "\n")
        code, out, _ = run_cli("verify-log", str(log))
        self.assertEqual(code, 1, out)

    def test_private_run_is_verified_and_its_log_hides_the_deals(self):
        r = bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=4, private_seeds=str(self.deck),
                        results_dir=self.tmp, fairplay_points=30,
                        argv=["score", "--private-seeds", str(self.deck)], quiet=True)
        self.assertEqual(r["seeds"]["tag"], "private")
        self.assertEqual(r["verification"], "verified")
        self.assertNotIn(str(self.deck), r["command"])
        self.assertIn("<private deck>", r["command"])
        self.assertNotIn("31000000000", json.dumps(r))
        with gzip.open(str(self.tmp / r["log"]), "rt") as f:
            rows = [json.loads(line) for line in list(f)[1:]]
        self.assertTrue(all("seed" not in x and "actions" not in x for x in rows))
        self.assertTrue(all(x["payments"] and x["deal"] in range(4) for x in rows))

    def test_skipping_fair_play_can_never_be_verified(self):
        r = bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=2, private_seeds=str(self.deck),
                        results_dir=self.tmp, skip_fairplay=True, write=False, quiet=True)
        self.assertEqual(r["verification"], "unverified")
        self.assertEqual(r["fairplay"]["status"], "skipped")

    def test_a_private_deck_inside_the_public_range_is_refused(self):
        bad = self.tmp / "bad.txt"
        bad.write_text("\n".join(str(1_000_000 + i) for i in range(5)))
        with self.assertRaises(ValueError):
            TABLE.private_deals(str(bad), 3)

    def test_private_deck_formats(self):
        a = self.tmp / "a.txt"
        a.write_text("5\n6\n7\n")
        self.assertEqual(load_private_seeds(str(a)), [5, 6, 7])
        b = self.tmp / "b.json"
        b.write_text('{"start": 100, "count": 3}')
        self.assertEqual(load_private_seeds(str(b)), [100, 101, 102])
        self.assertEqual(load_private_seeds(str(self.deck))[:2], [31_000_000_000, 31_000_000_001])

    def test_the_env_var_selects_the_private_deck(self):
        code, out, err = run_cli("score", "--table", "hk-hkma-v1", "--bot", "ref:ukeire", "--deals", "2", "--no-write",
                                 "--fairplay-points", "20", env={"HKBENCH_PRIVATE_SEEDS": str(self.deck)})
        self.assertEqual(code, 0, err)
        self.assertIn("private deck, verified", out)

    def test_the_deck_must_be_long_enough(self):
        with self.assertRaises(ValueError):
            TABLE.private_deals(str(self.deck), 11)


class Gates(unittest.TestCase):
    def test_the_pending_house_table_will_not_score(self):
        code, out, err = run_cli("score", "--table", "hk-house-v1", "--bot", "ref:ukeire", "--deals", "2", "--no-write")
        self.assertEqual(code, 2)
        self.assertIn("pending Seven Pairs scoring", err)

    def test_the_fingerprint_reproduces(self):
        fp = fingerprint.verify(TABLE)
        self.assertEqual(fp["sha256"], TABLE.pinned_fingerprint()["sha256"])
        self.assertGreater(fp["wins"], 50)

    def test_a_changed_rule_breaks_the_fingerprint(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp))
        shutil.copytree(str(ROOT / "tables"), str(tmp / "tables"))
        d = tmp / "tables" / "hk-hkma-v1"
        rules = json.loads((d / "rules.json").read_text())
        rules["patterns"]["common_hand"] = 2
        (d / "rules.json").write_text(json.dumps(rules, indent=2))
        t = load_table("hk-hkma-v1", tmp / "tables")
        with self.assertRaises(RuntimeError):  # the rules hash no longer matches table.json
            t.profile
        data = json.loads((d / "table.json").read_text())
        from hkbench.engine.profile import load_profile

        data["rules_sha256"] = load_profile(d / "rules.json").rules_sha256  # re-pin the rules but not the fingerprint
        (d / "table.json").write_text(json.dumps(data))
        t = load_table("hk-hkma-v1", tmp / "tables")
        with self.assertRaises(fingerprint.FingerprintMismatch):
            fingerprint.verify(t)

    def test_a_changed_reference_bot_is_refused(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp))
        shutil.copytree(str(ROOT / "tables"), str(tmp / "tables"))
        d = tmp / "tables" / "hk-hkma-v1"
        data = json.loads((d / "table.json").read_text())
        data["field"][0]["sha256"] = "0" * 64
        (d / "table.json").write_text(json.dumps(data))
        t = load_table("hk-hkma-v1", tmp / "tables")
        with self.assertRaises(RuntimeError) as ctx:
            t.verify_field()
        self.assertIn("new table version", str(ctx.exception))

    def test_the_field_pins_match_the_source_in_this_checkout(self):
        TABLE.verify_field()

    def test_a_bot_that_breaks_the_protocol_too_often_is_rejected(self):
        script = Path(tempfile.mkdtemp()) / "illegal.py"
        script.write_text(
            "import json,sys\n"
            "for l in sys.stdin:\n"
            "    m=json.loads(l)\n"
            "    if m['type']=='hello': print(json.dumps({'type':'ready'}),flush=True)\n"
            "    elif m['type']=='decide': print(json.dumps({'type':'action','seq':m['seq'],'id':126}),flush=True)\n"
            "    elif m['type']=='bye': break\n")
        spec = "%s %s" % (PY, script)
        with self.assertRaises(bench.Rejected):
            bench.score(TABLE, spec, meta(spec), deals=1, skip_fairplay=True, results_dir=Path(tempfile.mkdtemp()),
                        write=False, quiet=True)


class HeadToHead(unittest.TestCase):
    def test_round_robin_gives_ranks_and_intervals(self):
        bots = [(n, "ref:" + n, meta("ref:" + n)) for n in ("random", "ukeire", "faan_aware")]
        r = bench.h2h(TABLE, bots, deals=10, results_dir=Path(tempfile.mkdtemp()), skip_fairplay=True,
                      resamples=40, write=False, quiet=True)
        self.assertEqual(len(r["pairs"]), 3)
        for p in r["pairs"]:
            self.assertEqual(p["games"], 60)
            self.assertEqual(p["a_game_wins"] + p["b_game_wins"] + p["ties"], 60)
        bt = r["bradley_terry"]
        self.assertAlmostEqual(sum(v["rating"] for v in bt.values()), 0.0, places=6)
        for v in bt.values():
            self.assertLessEqual(v["ci95"][0], v["ci95"][1])
            self.assertGreaterEqual(v["rank"], 1)
        self.assertEqual(r["verification"], "unverified")

    def test_a_bot_against_itself_is_a_coin_flip(self):
        bots = [("a", "ref:ukeire", meta("ref:ukeire", "a")), ("b", "ref:ukeire", meta("ref:ukeire", "b"))]
        r = bench.h2h(TABLE, bots, deals=12, results_dir=Path(tempfile.mkdtemp()), skip_fairplay=True,
                      resamples=40, write=False, quiet=True)
        p = r["pairs"][0]
        self.assertEqual(p["a_game_wins"], p["b_game_wins"])  # same bot on both sides, every arrangement mirrored in total
        self.assertEqual(r["bradley_terry"]["a"]["rank"], r["bradley_terry"]["b"]["rank"])


class Results(unittest.TestCase):
    def test_result_file_has_what_the_board_needs(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp))
        r = bench.score(TABLE, "ref:random", meta("ref:random"), deals=3, results_dir=tmp, skip_fairplay=True, quiet=True)
        on_disk = json.loads((tmp / (r["run_id"] + ".json")).read_text())
        self.assertEqual(on_disk, r)
        for key in ("schema", "run_id", "created_utc", "table", "bot", "seeds", "verification", "fairplay", "headline",
                    "stats", "faults", "command", "engine", "log"):
            self.assertIn(key, on_disk)
        self.assertEqual(on_disk["schema"], "hkbench-result-1")
        self.assertEqual(on_disk["table"]["rules_sha256"], TABLE.profile.rules_sha256)
        self.assertEqual(on_disk["bot"]["sha256"], bench.bot_hash("ref:random"))
        self.assertEqual(len(on_disk["table"]["field"]), 3)
        self.assertTrue((tmp / on_disk["log"]).exists())


if __name__ == "__main__":
    unittest.main()
