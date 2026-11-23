"""Chicken hand with a flat payment (hk-chicken-v2): every win pays the same, and the table is ranked by win rate.

hk-chicken-v1 paid by faan like HKMA, so a chicken-hand table rewarded big hands. v2 keeps the 0-faan minimum
and pays every win the same way: the winner collects 3 and each other seat pays 1, whether the win was self-drawn
or off a discard. Its headline is win rate, and its head-to-heads rank by who won the hand.
"""

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, hkma_profile, hkma_table, house_table

from hkbench import bench, fingerprint, site, stats
from hkbench.engine.payment import table_payments
from hkbench.engine.profile import load_profile
from hkbench.engine.scorer import score_hand
from hkbench.engine.tiles import parse_tile as P
from hkbench.engine.types import Meld, MeldKind, PlayerState, WinSource
from hkbench.tables import list_tables, load_table

from test_chicken import CHICKEN_ELEVEN, OPEN_PONG, chicken_hand, counts, scoring

_cache = {}


def flat_profile():
    if "f" not in _cache:
        _cache["f"] = load_profile(ROOT / "tables" / "hk-chicken-v2" / "rules.json")
    return _cache["f"]


def flat_table():
    return load_table("hk-chicken-v2")


def meta(spec, name=None):
    return bench.bot_meta(spec, name=name, track="bots", kind=None, trained_on=None, description=None,
                          cwd=None, hash_dir=None, hash_override=None)


class RulesFile(unittest.TestCase):
    def test_it_is_hkma_with_a_zero_minimum_and_a_flat_payment(self):
        flat, hkma = copy.deepcopy(flat_profile().data), copy.deepcopy(hkma_profile().data)
        self.assertEqual((flat["win"]["minimum_faan"], hkma["win"]["minimum_faan"]), (0, 3))
        for d in (flat, hkma):
            for key in ("profile_id", "version", "description", "derived_from"):
                d.pop(key, None)
            d["win"].pop("minimum_faan")
            d["payments"].pop("table")
            d["payments"].pop("discarder_pays")
            d["payments"].pop("self_draw_multiplier")
            d["payments"].pop("note", None)
        self.assertEqual(flat, hkma)

    def test_every_row_of_the_payment_table_is_one(self):
        p = flat_profile()
        self.assertEqual(sorted(p.payment_table), list(range(14)))
        self.assertEqual(set(p.payment_table.values()), {1})
        self.assertEqual(p.self_draw_multiplier, 3)
        self.assertEqual(p.data["payments"]["discarder_pays"], "equal")
        self.assertEqual(hkma_profile().data["payments"]["discarder_pays"], "all")

    def test_it_names_where_it_came_from(self):
        derived = flat_profile().data["derived_from"]
        self.assertEqual(derived["profile"], "hk-hkma-v1")
        self.assertEqual(derived["rules_hash"], hkma_profile().rules_hash)
        self.assertIn("minimum_faan", derived["change"])

    def test_it_is_a_new_set_of_rules(self):
        v1 = load_profile(ROOT / "tables" / "hk-chicken-v1" / "rules.json")
        self.assertNotEqual(flat_profile().rules_sha256, v1.rules_sha256)
        self.assertEqual(flat_profile().data["win"], v1.data["win"])  # the same wins, paid differently


class EveryWinPaysTheSame(unittest.TestCase):
    def paid(self, r, source, winner=0):
        """The scorer's settlement as the table pays it."""
        return table_payments(r.payments, source, winner, flat_profile())

    def test_a_chicken_hand_off_a_discard_collects_three_one_from_each_seat(self):
        r = score_hand(chicken_hand(), P("s8"), WinSource.DISCARD, 0, 0, discarder=3, profile=flat_profile())
        self.assertEqual(scoring(r), {})
        self.assertTrue(r.meets_minimum)
        self.assertEqual(self.paid(r, WinSource.DISCARD), [3, -1, -1, -1])  # the discarder (seat 3) pays no more than the others

    def test_a_limit_hand_off_a_discard_pays_the_same(self):
        big = PlayerState(concealed=counts("E E E S S S W W W N N m5 m6 m7"), melds=[], flowers=[], seat=0)
        r = score_hand(big, None, WinSource.DISCARD, 0, 0, discarder=2, profile=flat_profile())
        self.assertEqual(r.capped_faan, 10)  # the faan are still found
        self.assertEqual(self.paid(r, WinSource.DISCARD), [3, -1, -1, -1])

    def test_a_self_drawn_hand_pays_the_same_as_a_discard_win(self):
        r = score_hand(chicken_hand(), P("s8"), WinSource.SELF_DRAW, 0, 0, profile=flat_profile())
        self.assertGreaterEqual(r.capped_faan, 1)  # Self-Drawn scores a faan, and it still pays the same
        self.assertEqual(self.paid(r, WinSource.SELF_DRAW), [3, -1, -1, -1])

    def test_every_faan_level_pays_the_same_by_discard_and_by_self_draw(self):
        from hkbench.engine.scorer import settle_payments
        for faan in range(0, 14):
            with self.subTest(faan=faan):
                d = table_payments(settle_payments(faan, WinSource.DISCARD, 1, 2, flat_profile()), WinSource.DISCARD, 1, flat_profile())
                s = table_payments(settle_payments(faan, WinSource.SELF_DRAW, 1, None, flat_profile()), WinSource.SELF_DRAW, 1, flat_profile())
                self.assertEqual(d, [-1, 3, -1, -1])
                self.assertEqual(s, [-1, 3, -1, -1])

    def test_faan_do_not_change_the_payment_of_the_same_hand(self):
        # The same hand on HKMA's payment table would pay 8 for 3 faan; here it pays 3, like a chicken hand.
        dragons = Meld(MeldKind.PONG, (P("C"),) * 3, from_seat=3, claimed_tile=P("C"))
        player = PlayerState(concealed=counts(CHICKEN_ELEVEN), melds=[dragons], flowers=[], seat=0)
        r = score_hand(player, P("s8"), WinSource.DISCARD, 0, 0, discarder=3, profile=flat_profile())
        self.assertEqual(scoring(r), {"dragon_pong": 1})
        self.assertEqual(self.paid(r, WinSource.DISCARD), [3, -1, -1, -1])

    def test_the_other_tables_are_paid_as_the_scorer_settles_them(self):
        r = score_hand(chicken_hand(), P("s8"), WinSource.DISCARD, 0, 0, discarder=3, profile=load_profile(ROOT / "tables" / "hk-chicken-v1" / "rules.json"))
        self.assertEqual(r.payments, [1, 0, 0, -1])
        self.assertEqual(table_payments(r.payments, WinSource.DISCARD, 0, hkma_profile()), [1, 0, 0, -1])

    def test_payments_always_sum_to_zero_in_play(self):
        wins = 0
        for index in range(40):
            rec = fingerprint.play_fingerprint_deal(flat_profile(), index)
            self.assertEqual(sum(rec["payments"]), 0)
            if rec["cause"] == "win":
                wins += 1
                self.assertEqual(sorted(rec["payments"]), [-1, -1, -1, 3], rec)
                self.assertEqual(rec["payments"][rec["winner"]], 3)
        self.assertGreater(wins, 0)


class TheTable(unittest.TestCase):
    def test_it_is_active_pinned_and_ranked_by_win_rate(self):
        t = flat_table()
        self.assertEqual(t.status, "active")
        self.assertEqual(t.metric, "win_rate")
        self.assertEqual(t.profile.rules_sha256, t.data["rules_sha256"])
        self.assertEqual(t.pinned_fingerprint()["rules_sha256"], t.data["rules_sha256"])
        t.verify_field()
        self.assertEqual(t.field, hkma_table().field)
        self.assertEqual(hkma_table().metric, "points_per_hand")
        self.assertEqual(house_table().metric, "points_per_hand")

    def test_its_fingerprint_reproduces_and_is_new(self):
        t = flat_table()
        fp = fingerprint.verify(t)
        self.assertEqual(fp["sha256"], t.pinned_fingerprint()["sha256"])
        self.assertEqual((fp["deals"], fp["hands"]), (300, 42))
        v1 = load_table("hk-chicken-v1")
        self.assertNotEqual(fp["sha256"], v1.pinned_fingerprint()["sha256"])
        self.assertNotEqual(fp["rules_sha256"], v1.pinned_fingerprint()["rules_sha256"])

    def test_it_has_a_fresh_public_range(self):
        ranges = {t.id: (t.public_range["start"], t.public_range["start"] + t.public_range["count"]) for t in list_tables()}
        lo, hi = ranges["hk-chicken-v2"]
        self.assertEqual((lo, hi), (4000000, 4100000))
        for tid, (lo2, hi2) in ranges.items():
            if tid != "hk-chicken-v2":
                self.assertTrue(hi <= lo2 or hi2 <= lo, tid)

    def test_the_old_table_is_retired_but_still_loads(self):
        v1 = load_table("hk-chicken-v1")
        self.assertEqual(v1.superseded_by, "hk-chicken-v2")
        self.assertIsNone(flat_table().superseded_by)
        v1.verify_field()
        self.assertEqual(fingerprint.verify(v1)["sha256"], v1.pinned_fingerprint()["sha256"])  # its logs still replay


class WinRateIsTheHeadline(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp))

    def test_the_headline_is_win_rate_with_its_interval(self):
        r = bench.score(flat_table(), "ref:ukeire", meta("ref:ukeire"), deals=8, results_dir=self.tmp,
                        skip_fairplay=True, quiet=True)
        h = r["headline"]
        self.assertEqual(h["metric_id"], "win_rate")
        self.assertIn("win rate", h["metric"])
        self.assertNotIn("points_per_hand", h)
        self.assertEqual(h["win_rate"], r["stats"]["win_rate"]["mean"])
        self.assertEqual(h["ci95"], r["stats"]["win_rate"]["ci95"])
        self.assertLessEqual(h["ci95"][0], h["win_rate"])
        self.assertLessEqual(h["win_rate"], h["ci95"][1])
        self.assertIn("deal_in_rate", r["stats"])

    def test_points_tables_keep_points_a_hand(self):
        r = bench.score(hkma_table(), "ref:ukeire", meta("ref:ukeire"), deals=3, results_dir=self.tmp,
                        skip_fairplay=True, quiet=True)
        self.assertEqual(r["headline"]["metric_id"], "points_per_hand")
        self.assertIn("points_per_hand", r["headline"])

    def test_every_win_pays_the_same_in_the_logged_games(self):
        r = bench.score(flat_table(), "ref:faan_aware", meta("ref:faan_aware"), deals=10, results_dir=self.tmp,
                        skip_fairplay=True, quiet=True)
        import gzip
        with gzip.open(str(self.tmp / r["log"]), "rt") as f:
            f.readline()
            games = [json.loads(line) for line in f]
        wins = [g for g in games if g["winner"] is not None]
        self.assertTrue(wins)
        for g in wins:
            self.assertEqual(g["payments"][g["winner"]], 3)
            self.assertEqual(sorted(g["payments"]), [-1, -1, -1, 3])

    def test_points_a_hand_are_a_straight_line_in_win_rate(self):
        # Whoever wins collects 3 and everyone else pays 1, so a game's points for a seat are 4 x (won) - 1, or 0 in a draw.
        r = bench.score(flat_table(), "ref:faan_aware", meta("ref:faan_aware"), deals=10, results_dir=self.tmp,
                        skip_fairplay=True, quiet=True)
        import gzip
        with gzip.open(str(self.tmp / r["log"]), "rt") as f:
            f.readline()
            games = [json.loads(line) for line in f]
        for g in games:
            for seat in range(4):
                expected = 0 if g["winner"] is None else (3 if g["winner"] == seat else -1)
                self.assertEqual(g["payments"][seat], expected)

    def test_the_cli_prints_a_win_rate(self):
        from test_bench import run_cli
        code, out, _err = run_cli("score", "--table", "hk-chicken-v2", "--bot", "ref:random", "--deals", "4",
                                  "--skip-fairplay", "--no-write", "--results-dir", str(self.tmp))
        self.assertEqual(code, 0)
        self.assertIn("win rate", out)
        self.assertIn("deal-in", out)
        self.assertNotIn("points a hand", out)


class HeadToHeadByWins(unittest.TestCase):
    def test_a_team_wins_the_hand_whoever_paid(self):
        a_wins_off_b = {"winner": 0, "discarder": 1, "seats": ["A", "B", "A", "B"]}
        a_wins_off_a = {"winner": 0, "discarder": 2, "seats": ["A", "B", "A", "B"]}  # paid by its own partner: net zero
        b_wins = {"winner": 3, "discarder": None, "seats": ["A", "B", "A", "B"]}
        draw = {"winner": None, "discarder": None, "seats": ["A", "B", "A", "B"]}
        self.assertEqual([stats.team_win_outcome(r, "A") for r in (a_wins_off_b, a_wins_off_a, b_wins, draw)], [1.0, 1.0, 0.0, 0.5])
        self.assertEqual([stats.team_win_outcome(r, "B") for r in (a_wins_off_b, a_wins_off_a, b_wins, draw)], [0.0, 0.0, 1.0, 0.5])

    def test_the_head_to_head_on_this_table_ranks_by_wins(self):
        bots = [(n, "ref:" + n, meta("ref:" + n)) for n in ("random", "ukeire")]
        r = bench.h2h(flat_table(), bots, deals=10, results_dir=Path(tempfile.mkdtemp()), skip_fairplay=True,
                      resamples=40, write=False, quiet=True)
        self.assertEqual(r["ranked_by"], "wins")
        p = r["pairs"][0]
        self.assertIn("a_win_rate_per_seat", p)
        self.assertNotIn("a_points_per_hand_per_seat", p)
        self.assertEqual(p["a_game_wins"] + p["b_game_wins"] + p["ties"], p["games"])
        # A win by either team is never a tie here, so ties are only the drawn hands.
        self.assertEqual(r["bradley_terry"]["ukeire"]["rank"], 1)

    def test_a_points_table_still_ranks_by_points(self):
        bots = [(n, "ref:" + n, meta("ref:" + n)) for n in ("random", "ukeire")]
        r = bench.h2h(hkma_table(), bots, deals=4, results_dir=Path(tempfile.mkdtemp()), skip_fairplay=True,
                      resamples=20, write=False, quiet=True)
        self.assertEqual(r["ranked_by"], "points")
        self.assertIn("a_points_per_hand_per_seat", r["pairs"][0])


class TheBoard(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp))
        self.results = self.tmp / "results"

    def run_on(self, table, name):
        spec = "ref:" + name
        return bench.score(table, spec, meta(spec), deals=6, results_dir=self.results, skip_fairplay=True, quiet=True)

    def test_a_win_rate_table_is_ranked_by_win_rate_and_the_old_table_is_off_the_board(self):
        self.run_on(flat_table(), "ukeire")
        self.run_on(flat_table(), "random")
        self.run_on(load_table("hk-chicken-v1"), "ukeire")
        self.run_on(hkma_table(), "ukeire")
        out = self.tmp / "site"
        site.build(self.results, out)
        data = json.loads((out / "leaderboard.json").read_text())
        ids = {t["id"]: t for t in data["tables"]}
        self.assertNotIn("hk-chicken-v1", ids)
        self.assertEqual(ids["hk-chicken-v2"]["metric"], "win_rate")
        self.assertEqual(ids["hk-hkma-v1"]["metric"], "points_per_hand")
        self.assertEqual(data["retired_tables"], [{"id": "hk-chicken-v1", "superseded_by": "hk-chicken-v2"}])
        self.assertEqual({r["table"] for r in data["rows"]}, {"hk-chicken-v2", "hk-hkma-v1"})
        flat_rows = [r for r in data["rows"] if r["table"] == "hk-chicken-v2"]
        self.assertEqual({r["metric"] for r in flat_rows}, {"win_rate"})
        self.assertEqual([r["value"] for r in flat_rows], sorted((r["value"] for r in flat_rows), reverse=True))
        for r in flat_rows:
            self.assertEqual(r["value"], r["win_rate"])
            self.assertIsNone(r["points_per_hand"])
        hkma_row = [r for r in data["rows"] if r["table"] == "hk-hkma-v1"][0]
        self.assertEqual(hkma_row["metric"], "points_per_hand")
        self.assertEqual(hkma_row["value"], hkma_row["points_per_hand"])

    def test_the_old_tables_head_to_head_is_off_the_board_too(self):
        bots = [(n, "ref:" + n, meta("ref:" + n)) for n in ("random", "ukeire")]
        for table in (load_table("hk-chicken-v1"), flat_table()):
            bench.h2h(table, bots, deals=3, results_dir=self.results, skip_fairplay=True, resamples=10, quiet=True)
        data = site._h2h(self.results, {"hk-chicken-v2"})
        self.assertEqual([h["table"] for h in data], ["hk-chicken-v2"])
        self.assertEqual(data[0]["ranked_by"], "wins")

    def test_shared_ranks_follow_win_rate_intervals(self):
        rows = [
            {"run_id": "a", "created_utc": "1", "track": "bots", "table": "t", "seed_tag": "public", "value": 0.48,
             "ci95": [0.45, 0.51], "bot": {"name": "x", "sha256": "1"}},
            {"run_id": "b", "created_utc": "2", "track": "bots", "table": "t", "seed_tag": "public", "value": 0.46,
             "ci95": [0.43, 0.49], "bot": {"name": "y", "sha256": "2"}},
            {"run_id": "c", "created_utc": "3", "track": "bots", "table": "t", "seed_tag": "public", "value": 0.20,
             "ci95": [0.18, 0.22], "bot": {"name": "z", "sha256": "3"}},
        ]
        site._rank(rows)
        self.assertEqual({r["bot"]["name"]: r["rank"] for r in rows}, {"x": 1, "y": 1, "z": 3})


class TheChart(unittest.TestCase):
    def test_the_chicken_panel_is_on_a_win_rate_axis(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import render_charts

        def row(table, name, value, lo, hi, deal_in=0.1):
            return {"table": table, "bot": {"name": name}, "value": value, "ci95": [lo, hi], "deal_in_rate": deal_in,
                    "points_per_hand": value if table != "hk-chicken-v2" else None}

        rows = [row("hk-hkma-v1", "a", 5.0, 4.0, 6.0), row("hk-house-v1", "a", 4.0, 3.0, 5.0),
                row("hk-chicken-v2", "b", 0.30, 0.28, 0.32, 0.12), row("hk-chicken-v2", "a", 0.45, 0.42, 0.48, 0.09),
                row("hk-chicken-v1", "old", 9.0, 8.0, 10.0)]
        svg = render_charts.chart(rows)
        self.assertIn("Win rate · 95% CI", svg)
        self.assertIn("Points a hand · 95% CI", svg)
        self.assertIn("45.0%", svg)
        self.assertIn("9.0%", svg)  # the deal-in column
        self.assertNotIn(">old<", svg)  # the retired table is not drawn
        self.assertLess(svg.index(">a<", svg.index("hk-chicken-v2")), svg.index(">b<", svg.index("hk-chicken-v2")))  # best first


if __name__ == "__main__":
    unittest.main()
