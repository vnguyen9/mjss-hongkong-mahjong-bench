"""Exact-output regression for the shanten, waits and decomposition code the reference bots use.

The golden corpus (``fixtures/golden_shanten.json``) pins exact equality, not approximate agreement.
"""

import json
import unittest
from pathlib import Path

from hkbench.agents.shanten import _standard_shanten_legacy, _standard_shanten_uncached, deficiency, standard_shanten
from hkbench.engine.win import can_win_structurally, structural_wins, waits
from hkbench.seeds import Rng

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "golden_shanten.json"


class ShantenGolden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        payload = json.loads(GOLDEN.read_text(encoding="utf-8"))
        assert payload["schema"] == "golden_shanten_v1"
        cls.records = payload["records"]

    def test_corpus_is_substantial(self):
        self.assertGreaterEqual(len(self.records), 1000)
        self.assertTrue(any(r["can_win_structurally"] for r in self.records))
        self.assertTrue(any(r["waits"] for r in self.records))
        self.assertGreaterEqual({r["n_exposed"] for r in self.records}, {0, 1, 2, 3, 4})

    def test_outputs_match_golden(self):
        for i, rec in enumerate(self.records):
            concealed = rec["concealed"]
            exposed = [None] * rec["n_exposed"]
            actual = {
                "standard_shanten": standard_shanten(concealed, exposed),
                "deficiency": deficiency(concealed, exposed),
                "waits": list(waits(concealed, exposed)),
                "can_win_structurally": can_win_structurally(concealed, exposed),
                "n_decompositions": len(structural_wins(concealed, exposed)),
            }
            expected = {key: rec[key] for key in actual}
            self.assertEqual(actual, expected, "record %d: %s" % (i, concealed))

    def test_waits_agree_with_can_win(self):
        for rec in self.records[:300]:
            concealed = list(rec["concealed"])
            exposed = [None] * rec["n_exposed"]
            derived = []
            for tile in range(34):
                if concealed[tile] >= 4:
                    continue
                probe = list(concealed)
                probe[tile] += 1
                if can_win_structurally(probe, exposed):
                    derived.append(tile)
            self.assertEqual(derived, list(waits(concealed, exposed)))


class ShantenProperties(unittest.TestCase):
    def test_chows_never_cross_suits(self):
        counts = [0] * 34
        for tile in (7, 8, 9, 10, 11, 16, 17, 18, 31, 31):
            counts[tile] += 1
        self.assertFalse(can_win_structurally(counts, [None]))

    def test_memoized_shanten_matches_the_plain_search(self):
        rng = Rng(4242)
        for i in range(1500):
            n_exposed = i % 5
            size = 13 - 3 * n_exposed + (i % 2)
            if size <= 0:
                continue
            wall = [t for t in range(34) for _ in range(4)]
            for k in range(len(wall) - 1, 0, -1):
                j = rng.randrange(k + 1)
                wall[k], wall[j] = wall[j], wall[k]
            counts = [0] * 34
            for tile in wall[:size]:
                counts[tile] += 1
            self.assertEqual(_standard_shanten_uncached(list(counts), n_exposed),
                             _standard_shanten_legacy(list(counts), n_exposed), counts)

    def test_thirteen_orphans_has_a_thirteen_way_wait(self):
        orphans = (0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33)
        counts = [0] * 34
        for tile in orphans:
            counts[tile] += 1
        self.assertEqual(list(waits(counts, [])), list(orphans))
        counts[0] += 1
        self.assertTrue(can_win_structurally(counts, []))

    def test_honours_make_only_triplets(self):
        complete = [0] * 34
        for tile in (27, 27, 27, 28, 28, 28, 29, 29, 29, 30, 30, 30, 31, 31):
            complete[tile] += 1
        self.assertTrue(can_win_structurally(complete, []))
        broken = [0] * 34
        for tile in (27, 27, 28, 28, 29, 29, 29, 30, 30, 30, 31, 31, 31, 32):
            broken[tile] += 1
        self.assertFalse(can_win_structurally(broken, []))


if __name__ == "__main__":
    unittest.main()
