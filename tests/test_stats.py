"""The statistics, checked on synthetic data where the answer is known."""

import math
import unittest

from helpers import ROOT  # noqa: F401  (puts the repo on sys.path)

from hkbench import stats
from hkbench.seeds import Rng


def normal(rng, mu, sd):
    """Box-Muller."""
    u1 = (rng.next_u64() + 1) / (2 ** 64 + 1)
    u2 = rng.next_u64() / 2 ** 64
    return mu + sd * math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)


class MeanCI(unittest.TestCase):
    def test_t_critical_values(self):
        for df, expected in [(1, 12.7062), (2, 4.3027), (5, 2.5706), (10, 2.2281), (30, 2.0423), (100, 1.9840)]:
            self.assertAlmostEqual(stats.t_critical_95(df), expected, places=3)

    def test_known_small_sample(self):
        r = stats.mean_ci([1, 2, 3, 4, 5])
        self.assertAlmostEqual(r["mean"], 3.0)
        self.assertAlmostEqual(r["se"], 0.7071068, places=6)
        self.assertAlmostEqual(r["ci95"][0], 3 - 2.7764451 * 0.7071068, places=4)
        self.assertAlmostEqual(r["ci95"][1], 3 + 2.7764451 * 0.7071068, places=4)

    def test_intervals_cover_the_truth_about_95_percent_of_the_time(self):
        rng = Rng(2026)
        mu, covered, runs = 2.0, 0, 600
        for _ in range(runs):
            sample = [normal(rng, mu, 10.0) for _ in range(40)]
            lo, hi = stats.mean_ci(sample)["ci95"]
            covered += lo <= mu <= hi
        self.assertGreater(covered / runs, 0.92)
        self.assertLess(covered / runs, 0.98)

    def test_one_sample_has_no_interval(self):
        self.assertIsNone(stats.mean_ci([3.0])["ci95"])
        self.assertIsNone(stats.mean_ci([])["mean"])


class Clustering(unittest.TestCase):
    def make(self, deal_sd, game_sd, deals, seed):
        """Four games per deal that share a deal effect. True mean is zero."""
        rng = Rng(seed)
        records = []
        for d in range(deals):
            effect = normal(rng, 0.0, deal_sd)
            for rot in range(4):
                records.append({"deal": d, "v": effect + normal(rng, 0.0, game_sd)})
        return records

    def test_per_deal_averages_the_four_games(self):
        recs = [{"deal": 0, "v": 1}, {"deal": 0, "v": 3}, {"deal": 1, "v": 10}, {"deal": 1, "v": 20}]
        self.assertEqual(stats.per_deal(recs, lambda r: r["v"]), [2.0, 15.0])

    def test_naive_game_level_interval_is_too_narrow_when_games_share_a_deal(self):
        # Large deal effect, small game noise: the four games of a deal are nearly the same number.
        recs = self.make(deal_sd=10.0, game_sd=1.0, deals=200, seed=3)
        clustered = stats.mean_ci(stats.per_deal(recs, lambda r: r["v"]))["se"]
        naive = stats.mean_ci([r["v"] for r in recs])["se"]
        self.assertGreater(clustered, 1.7 * naive)  # the truth is about 2x wider than the naive number

    def test_clustered_interval_covers_the_truth(self):
        covered, runs = 0, 300
        for k in range(runs):
            recs = self.make(deal_sd=8.0, game_sd=3.0, deals=40, seed=1000 + k)
            lo, hi = stats.mean_ci(stats.per_deal(recs, lambda r: r["v"]))["ci95"]
            covered += lo <= 0.0 <= hi
        self.assertGreater(covered / runs, 0.91)
        self.assertLess(covered / runs, 0.99)


class DuplicateSummary(unittest.TestCase):
    def game(self, deal, winner, discarder, faan, payments, seats=("bot", "f0", "f1", "f2")):
        return {"deal": deal, "seats": list(seats), "winner": winner, "discarder": discarder, "faan": faan,
                "payments": payments, "decisions": [10, 10, 10, 10], "faults": [{}, {}, {}, {}]}

    def test_rates_and_averages(self):
        recs = [
            self.game(0, 0, None, 10, [192, -64, -64, -64]),   # bot self-draws a limit hand
            self.game(0, 1, 0, 3, [-8, 8, 0, 0]),              # bot deals in
            self.game(0, None, None, 0, [0, 0, 0, 0]),         # draw
            self.game(0, 2, None, 4, [-8, -8, 24, -8]),        # a field bot self-draws
        ]
        s = stats.duplicate_summary(recs, faan_cap=10)
        self.assertEqual(s["games"], 4)
        self.assertAlmostEqual(s["points_per_hand"]["mean"], (192 - 8 + 0 - 8) / 4)
        self.assertAlmostEqual(s["win_rate"]["mean"], 0.25)
        self.assertAlmostEqual(s["deal_in_rate"]["mean"], 0.25)
        self.assertAlmostEqual(s["draw_rate"]["mean"], 0.25)
        self.assertEqual(s["limit_hands"], 1)
        self.assertEqual(s["average_win_points"], 192.0)
        self.assertEqual(s["average_win_faan"], 10.0)


class BradleyTerry(unittest.TestCase):
    def test_recovers_known_strengths_from_expected_counts(self):
        true = {"a": 4.0, "b": 2.0, "c": 1.0}
        n = 1_000_000.0
        wins = {}
        for i in true:
            for j in true:
                if i != j:
                    wins[(i, j)] = n * true[i] / (true[i] + true[j])
        r = stats.bradley_terry(["a", "b", "c"], wins)
        scale = 400 / math.log(10)
        self.assertAlmostEqual(r["a"] - r["b"], scale * math.log(2), places=2)
        self.assertAlmostEqual(r["b"] - r["c"], scale * math.log(2), places=2)
        self.assertAlmostEqual(sum(r.values()), 0.0, places=6)

    def simulate(self, strengths, deals, seed):
        rng = Rng(seed)
        names = list(strengths)
        out = {}
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                p = strengths[a] / (strengths[a] + strengths[b])
                rows = []
                for _ in range(deals):
                    pts = sum(1.0 if rng.randrange(10 ** 6) / 10 ** 6 < p else 0.0 for _ in range(6))
                    rows.append((pts, 6.0))
                out[(a, b)] = rows
        return names, out

    def test_ranks_split_when_bots_differ_and_share_when_they_do_not(self):
        names, pair_deals = self.simulate({"strong": 6.0, "mid": 2.0, "twin1": 1.0, "twin2": 1.0}, deals=150, seed=5)
        res = stats.bootstrap_bt(names, pair_deals, resamples=300)
        ranks = stats.shared_ranks(res)
        self.assertEqual(ranks["strong"], 1)
        self.assertEqual(ranks["mid"], 2)
        self.assertEqual(ranks["twin1"], ranks["twin2"])  # same strength: intervals overlap, shared rank
        self.assertEqual(ranks["twin1"], 3)
        # The point estimates are close to the truth.
        scale = 400 / math.log(10)
        self.assertAlmostEqual(res["strong"]["rating"] - res["mid"]["rating"], scale * math.log(3), delta=40)
        for nm in names:
            lo, hi = res[nm]["ci95"]
            self.assertLessEqual(lo, res[nm]["rating"])
            self.assertGreaterEqual(hi, res[nm]["rating"])

    def test_shared_rank_rule(self):
        rows = {"a": {"ci95": [10, 20]}, "b": {"ci95": [15, 25]}, "c": {"ci95": [0, 5]}}
        self.assertEqual(stats.shared_ranks(rows), {"a": 1, "b": 1, "c": 3})

    def test_bootstrap_is_reproducible(self):
        names, pair_deals = self.simulate({"x": 2.0, "y": 1.0}, deals=40, seed=9)
        self.assertEqual(stats.bootstrap_bt(names, pair_deals, resamples=50),
                         stats.bootstrap_bt(names, pair_deals, resamples=50))


if __name__ == "__main__":
    unittest.main()
