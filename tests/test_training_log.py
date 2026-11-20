"""``--training-log``: off it changes nothing; on it adds the winning hand to each won game's log record."""

import gzip
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import hkma_table
from test_bench import meta, run_cli

from hkbench import bench
from hkbench.players import make_player
from hkbench.runner import play_game
from hkbench.tables import Deal

TABLE = hkma_table()
NEW = set(bench.TRAINING_FIELDS)


def read_log(path):
    with gzip.open(str(path), "rt") as f:
        header = json.loads(f.readline())["header"]
        return header, [json.loads(line) for line in f]


class TrainingLog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.deck = cls.tmp / "private.json"
        cls.deck.write_text(json.dumps({"seeds": [31_000_000_000 + i for i in range(10)]}))
        argv = ["score", "--table", "hk-hkma-v1"]
        kw = dict(deals=10, skip_fairplay=True, quiet=True, argv=argv)
        cls.off = bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), results_dir=cls.tmp / "off", **kw)
        cls.on = bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), results_dir=cls.tmp / "on",
                             training_log=True, **kw)
        cls.off_header, cls.off_rows = read_log(cls.tmp / "off" / cls.off["log"])
        cls.on_header, cls.on_rows = read_log(cls.tmp / "on" / cls.on["log"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.tmp))

    def test_off_the_log_has_none_of_the_new_fields(self):
        self.assertTrue(self.off_rows)
        for row in self.off_rows:
            self.assertFalse(NEW & set(row))
        self.assertNotIn("training_log", self.off)

    def test_the_flag_changes_the_log_by_exactly_the_new_fields(self):
        # Everything else in the log, the header included, is what it was: the same games, the same bytes.
        self.assertEqual(self.on["training_log"], True)
        self.assertEqual({k: v for k, v in self.on.items() if k != "training_log"}.keys(), self.off.keys())
        stripped = [{k: v for k, v in row.items() if k not in NEW} for row in self.on_rows]
        self.assertEqual(stripped, self.off_rows)
        self.assertEqual(self.on["headline"], self.off["headline"])
        self.assertEqual(self.on_header["run_id"].split("__")[:3], self.off_header["run_id"].split("__")[:3])

    def test_a_won_game_carries_the_winning_hand_and_a_drawn_game_does_not(self):
        wins = [r for r in self.on_rows if r["winner"] is not None]
        self.assertTrue(wins)
        for r in wins:
            self.assertTrue(NEW <= set(r))
            self.assertTrue(r["concealed"])
            if r["winning_tile"] is not None:
                self.assertIn(r["winning_tile"], r["concealed"])
                self.assertEqual(len(r["concealed"]) + 3 * len(r["melds"]), 14)  # a kong counts as a set of three
            self.assertGreaterEqual(r["winner_draws"], 1 if r["win_source"] == "SELF_DRAW" else 0)
            for kind, tiles, from_seat in r["melds"]:
                self.assertIn(kind, ("chow", "pong", "exposed_kong", "concealed_kong", "added_kong"))
                self.assertTrue(all(isinstance(t, str) for t in tiles))
            self.assertEqual(r["faan"], min(sum(f for _, f in r["patterns"]), TABLE.profile.faan_cap))
        for r in self.on_rows:
            if r["winner"] is None:
                self.assertFalse(NEW & set(r))

    def test_a_log_with_the_new_fields_still_replays(self):
        code, out, _ = run_cli("verify-log", str(self.tmp / "on" / self.on["log"]))
        self.assertEqual(code, 0, out)
        self.assertIn("0 mismatches", out)

    def test_a_private_deck_gets_nothing_extra(self):
        r = bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=4, private_seeds=str(self.deck),
                        results_dir=self.tmp / "private", skip_fairplay=True, quiet=True, training_log=True)
        self.assertNotIn("training_log", r)
        _, rows = read_log(self.tmp / "private" / r["log"])
        self.assertTrue(rows)
        for row in rows:
            self.assertFalse(NEW & set(row))
            self.assertNotIn("actions", row)
            self.assertNotIn("seed", row)
        # and even a record that carried the fields would lose them in the private log
        path = self.tmp / "forced.jsonl.gz"
        bench.write_log(path, {"h": 1}, [{"winner": 0, "melds": [], "concealed": ["m1"], "seed": 5}], "private")
        self.assertEqual(read_log(path)[1], [{"winner": 0}])

    def test_the_command_line_flag(self):
        out_dir = self.tmp / "cli"
        code, out, _ = run_cli("score", "--table", "hk-hkma-v1", "--bot", "ref:ukeire", "--deals", "3",
                               "--skip-fairplay", "--results-dir", str(out_dir), "--training-log")
        self.assertEqual(code, 0, out)
        logs = list((out_dir / "logs").glob("*.jsonl.gz"))
        self.assertEqual(len(logs), 1)
        _, rows = read_log(logs[0])
        self.assertTrue(any(NEW <= set(r) for r in rows))
        result = json.loads(next(out_dir.glob("*.json")).read_text())
        self.assertIn("--training-log", result["command"])
        code, out, _ = run_cli("score", "--table", "hk-hkma-v1", "--bot", "ref:ukeire", "--deals", "3",
                               "--skip-fairplay", "--results-dir", str(self.tmp / "cli2"))
        self.assertEqual(code, 0, out)
        _, rows = read_log(next((self.tmp / "cli2" / "logs").glob("*.jsonl.gz")))
        self.assertFalse(any(NEW & set(r) for r in rows))

    def test_the_game_over_message_players_get_is_unchanged(self):
        class Recorder:
            def __init__(self, inner):
                self.inner, self.over = inner, []

            def decide(self, msg):
                return self.inner.decide(msg)

            def game_over(self, msg):
                self.over.append(msg)

            def close(self):
                pass

        profile = TABLE.profile
        seen = {}
        for flag in (False, True):
            bots = [Recorder(make_player("ref:ukeire", TABLE.id, profile)) for _ in range(4)]
            for i in range(6):
                rec = play_game(TABLE.id, profile, Deal(i, 1000000 + i, i % 4, 0), bots, arrangement=0, training_log=flag)
            seen[flag] = [m for b in bots for m in b.over]
            self.assertEqual(bool(NEW & set(rec)), flag and rec["winner"] is not None)
        self.assertEqual(seen[False], seen[True])
        for msg in seen[True]:
            self.assertEqual(set(msg), {"type", "game_id", "cause", "winner", "discarder", "faan", "patterns", "payment"})


if __name__ == "__main__":
    unittest.main()
