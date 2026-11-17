"""Scoring: the hand-checked HKMA goldens, the rulebook's score table, and the known gaps."""

import json
import unittest
from pathlib import Path

from helpers import hkma_profile

from hkbench.engine.scorer import score_hand, settle_payments
from hkbench.engine.tiles import parse_tile as P
from hkbench.engine.types import Meld, MeldKind, PlayerState, WinSource
from hkbench.fingerprint import score_corpus_hand

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Faan-to-Score table, HKMA rulebook p.24: faan -> (chuck, self-drawn each of three).
RULEBOOK = {3: (32, 16), 4: (64, 32), 5: (96, 48), 6: (128, 64), 7: (192, 96), 8: (256, 128), 9: (384, 192), 10: (512, 256)}


def player(conc, melds=(), flowers=()):
    counts = [0] * 34
    for t in conc.split():
        counts[P(t)] += 1
    return PlayerState(concealed=counts, melds=list(melds), flowers=list(flowers), seat=0)


class GoldenHands(unittest.TestCase):
    def test_every_golden_hand(self):
        data = json.loads((FIXTURES / "golden_hkma.json").read_text())
        self.assertGreaterEqual(len(data["cases"]), 30)
        profile = hkma_profile()
        for case in data["cases"]:
            got = score_corpus_hand(profile, case)
            exp = case["expect"]
            with self.subTest(case=case["id"]):
                self.assertEqual(got["patterns"], exp["patterns"])
                self.assertEqual(got["total"], exp["total_faan"])
                self.assertEqual(got["faan"], exp["faan"])
                self.assertEqual(got["ok"], exp["meets_minimum"])
                self.assertEqual(got["limit"], exp["limit"])
                self.assertEqual(got["payments"], exp["payments"])
                self.assertEqual(sum(got["payments"]), 0)


class PaymentTable(unittest.TestCase):
    def test_matches_the_rulebook_at_one_quarter_scale(self):
        profile = hkma_profile()
        for faan, (chuck, selfdrawn) in RULEBOOK.items():
            with self.subTest(faan=faan):
                disc = settle_payments(faan, WinSource.DISCARD, winner=0, discarder=2, profile=profile)
                self.assertEqual(disc, [chuck // 4, 0, -(chuck // 4), 0])
                sd = settle_payments(faan, WinSource.SELF_DRAW, winner=1, discarder=None, profile=profile)
                self.assertEqual(sd, [-(selfdrawn // 4), 3 * (selfdrawn // 4), -(selfdrawn // 4), -(selfdrawn // 4)])

    def test_every_settlement_is_zero_sum(self):
        profile = hkma_profile()
        for faan in range(3, 14):
            for winner in range(4):
                for src in (WinSource.SELF_DRAW, WinSource.DISCARD, WinSource.ROB_KONG):
                    for discarder in [None] if src == WinSource.SELF_DRAW else [d for d in range(4) if d != winner]:
                        pay = settle_payments(faan, src, winner, discarder, profile)
                        self.assertEqual(sum(pay), 0)
                        self.assertGreater(pay[winner], 0)

    def test_the_cap_is_ten_and_the_minimum_is_three(self):
        profile = hkma_profile()
        self.assertEqual(profile.faan_cap, 10)
        self.assertEqual(profile.minimum_faan, 3)
        # A hand worth 16 faan on paper (small winds 10 + semi-flush 3 + ...) is paid as 10.
        r = score_hand(player("E E E S S S W W W N N m5 m6 m7"), None, WinSource.DISCARD, 0, 0, discarder=2, profile=profile)
        self.assertGreater(r.total_faan, 10)
        self.assertEqual(r.capped_faan, 10)
        self.assertEqual(r.payments[0], profile.payment_table[10])


class RulebookFaan(unittest.TestCase):
    """One check per faan item in the rulebook (pp.22-24), so a changed value is caught by name."""

    def faan(self, conc, melds=(), flowers=(), source=WinSource.SELF_DRAW, **flags):
        r = score_hand(player(conc, melds, flowers), None, source, 0, 0,
                       discarder=None if source == WinSource.SELF_DRAW else 1, profile=hkma_profile(), **flags)
        return {h.name: h.faan for h in r.patterns}, r.capped_faan

    def test_one_faan_items(self):
        names, _ = self.faan("m1 m2 m3 m4 m5 m6 p1 p2 p3 s1 s2 s3 s5 s5")
        for n in ("common_hand", "self_draw", "fully_concealed"):
            self.assertEqual(names[n], 1)
        names, _ = self.faan("m1 m2 m3 m4 m5 m6 p1 p2 p3 C C C s5 s5")
        self.assertEqual(names["dragon_pong"], 1)
        names, _ = self.faan("E E E m1 m2 m3 p4 p5 p6 s7 s8 s9 C C")
        self.assertEqual((names["seat_wind"], names["prevailing_wind"]), (1, 1))  # overlap scores 2
        names, _ = self.faan("m1 m2 m3 m4 m5 m6 p1 p2 p3 C C C s5 s5", source=WinSource.SELF_DRAW, last_tile=True)
        self.assertEqual(names["last_tile"], 1)
        names, _ = self.faan("m1 m2 m3 m4 m5 m6 p1 p2 p3 C C C s5 s5", after_kong=True)
        self.assertEqual(names["kong_replacement"], 1)
        names, _ = self.faan("m1 m2 m3 m4 m5 m6 p1 p2 p3 C C C s5 s5", source=WinSource.ROB_KONG)
        self.assertEqual(names["rob_kong"], 1)
        names, _ = self.faan("m1 m1 m1 m9 m9 m9 s1 s1 s1 p9 p9 p9 C C", melds=())
        self.assertIn("four_concealed_pongs", names)

    def test_three_five_seven_faan_items(self):
        names, _ = self.faan("m1 m2 m3 m4 m5 m6 m7 m8 m9 E E E m1 m1", source=WinSource.DISCARD)
        self.assertEqual(names["mixed_one_suit"], 3)
        melds = [Meld(MeldKind.PONG, (P("m1"),) * 3, 1, P("m1"))]
        names, _ = self.faan("m2 m2 m2 p5 p5 p5 s8 s8 s8 W W", melds=melds, source=WinSource.DISCARD)
        self.assertEqual(names["all_pong"], 3)
        names, _ = self.faan("C C C F F F P P m1 m2 m3 s4 s5 s6", source=WinSource.DISCARD)
        self.assertEqual((names["small_dragons"], names["dragon_pong"]), (3, 1))  # 3 + 2 pongs = 5
        names, _ = self.faan("C C C F F F P P P m2 m3 m4 s5 s5", source=WinSource.DISCARD)
        self.assertEqual(names["great_dragons"], 5)  # + 3 pongs = 8
        names, total = self.faan("m1 m2 m3 m2 m3 m4 m5 m6 m7 m7 m8 m9 m9 m9", source=WinSource.DISCARD)
        self.assertEqual(names["pure_one_suit"], 7)

    def test_every_ceiling_hand_pays_ten(self):
        hands = {
            "all_honors": "E E E S S S W W W C C C F F",
            "great_winds": "E E E S S S W W W N N N C C",
            "thirteen_orphans": "m1 m9 s1 s9 p1 p9 E S W N C F P P",
            "nine_gates": "m1 m1 m1 m2 m3 m4 m5 m6 m7 m8 m9 m9 m9 m5",
        }
        for name, conc in hands.items():
            with self.subTest(name):
                names, faan = self.faan(conc)
                self.assertEqual(names[name], 10)
                self.assertEqual(faan, 10)
        names, faan = self.faan("E E E S S S W W W N N m5 m6 m7", source=WinSource.DISCARD)
        self.assertEqual((names["small_winds"], faan), (10, 10))
        names, faan = self.faan("m1 m1 m1 p1 p1 p1 s1 s1 s1 m9 m9 m9 p9 p9")
        self.assertEqual(faan, 10)  # all terminals
        _, faan = self.faan("m1 m2 m3 m4 m5 m6 p1 p2 p3 s1 s2 s3 s5 s5", heavenly=True)
        self.assertEqual(faan, 10)
        _, faan = self.faan("m1 m2 m3 m4 m5 m6 p1 p2 p3 s1 s2 s3 s5 s5", source=WinSource.DISCARD, earthly=True)
        self.assertEqual(faan, 10)
        _, faan = self.faan("m1 m2 m3 m4 m5 m6 p1 p2 p3 s1 s2 s3 s5 s5", after_kong=True, after_double_kong=True)
        self.assertGreaterEqual(faan, 10)  # after consecutive kan: 10
        kongs = [Meld(MeldKind.EXPOSED_KONG, (P(t),) * 4, 1, P(t)) for t in ("m1", "m5", "p3", "s7")]
        names, faan = self.faan("C C", melds=kongs, source=WinSource.DISCARD)
        self.assertEqual((names["all_kongs"], faan), (10, 10))

    def test_flowers_never_score(self):
        every = ["Fl1", "Fl2", "Fl3", "Fl4", "Se1", "Se2", "Se3", "Se4"]
        from hkbench.engine.tiles import BONUS_NAMES

        flowers = [BONUS_NAMES.index(n) for n in every]
        names, faan = self.faan("m1 m2 m3 m4 m5 m6 p1 p2 p3 s1 s2 s3 s5 s5", flowers=flowers)
        self.assertEqual(faan, 3)  # all sequences + self-drawn + closed hand, nothing from 8 flowers
        self.assertTrue(all(v == 0 for k, v in names.items() if "flower" in k or "season" in k))


HOUSE_RULES = Path(__file__).resolve().parent.parent / "tables" / "hk-house-v1" / "rules.pending.json"


class LimitHandsKeepTheirWinConditions(unittest.TestCase):
    """A limit hand still counts Self-Drawn, Last Tile, Robbing a Kong and the kong items, then the cap applies."""

    def house(self):
        from hkbench.engine.profile import profile_from_dict

        return profile_from_dict(json.loads(HOUSE_RULES.read_text()))

    def score(self, conc, profile, source=WinSource.SELF_DRAW, **flags):
        return score_hand(player(conc), None, source, 0, 0, discarder=None if source == WinSource.SELF_DRAW else 1,
                          profile=profile, **flags)

    def test_a_self_drawn_ten_faan_limit_is_eleven_on_a_cap_13_table(self):
        house = self.house()
        self.assertEqual(house.faan_cap, 13)
        for name, conc in (("nine_gates", "m1 m1 m1 m2 m3 m4 m5 m6 m7 m8 m9 m9 m9 m5"),
                           ("all_honors", "E E E S S S W W W C C C F F"),
                           ("four_concealed_pongs", "m1 m1 m1 m3 m3 m3 p5 p5 p5 s7 s7 s7 E E")):
            with self.subTest(name):
                r = self.score(conc, house)
                self.assertEqual([(h.name, h.faan) for h in r.patterns], [(name, 10), ("self_draw", 1)])
                self.assertEqual(r.capped_faan, 11)
                self.assertEqual(r.payments, [288, -96, -96, -96])  # table[11] = 192, self-drawn x1.5

    def test_the_same_hands_stay_at_ten_on_hkma(self):
        for conc in ("m1 m1 m1 m2 m3 m4 m5 m6 m7 m8 m9 m9 m9 m5", "E E E S S S W W W C C C F F"):
            r = self.score(conc, hkma_profile())
            self.assertEqual(r.total_faan, 11)
            self.assertEqual(r.capped_faan, 10)
            self.assertEqual(r.payments, [192, -64, -64, -64])

    def test_other_win_conditions_count_on_a_limit_hand(self):
        house = self.house()
        r = self.score("E E E S S S W W W C C C F F", house, source=WinSource.DISCARD, last_tile=True)
        self.assertEqual([h.name for h in r.patterns], ["all_honors", "last_tile"])
        self.assertEqual(r.capped_faan, 11)
        r = self.score("E E E S S S W W W C C C F F", house, after_kong=True)
        self.assertEqual([h.name for h in r.patterns], ["all_honors", "self_draw", "kong_replacement"])
        self.assertEqual(r.capped_faan, 12)

    def test_a_limit_at_the_cap_stays_at_the_cap(self):
        house = self.house()
        r = self.score("m1 m9 s1 s9 p1 p9 E S W N C F P P", house)
        self.assertEqual(r.total_faan, 14)  # thirteen orphans 13 + self-drawn 1
        self.assertEqual(r.capped_faan, 13)


class KnownGaps(unittest.TestCase):
    """What the engine does today where the HKMA rulebook says something else.

    Each test pins the engine's behaviour and names the rulebook line. If one starts failing, the
    gap was fixed: update RULES.md and the table's version in the same change.
    """

    def test_concealed_kong_still_counts_as_a_closed_hand(self):
        # Rulebook 1.2: a concealed kan counts as a melded meld, so the hand is not closed.
        kong = Meld(MeldKind.CONCEALED_KONG, (P("C"),) * 4)
        r = score_hand(player("m2 m3 m4 p5 p6 p7 s1 s2 s3 E E", [kong]), None, WinSource.SELF_DRAW, 0, 0,
                       profile=hkma_profile())
        self.assertIn("fully_concealed", [h.name for h in r.patterns])
        self.assertEqual(r.capped_faan, 3)  # the rulebook gives 2 here: below the minimum

    def test_four_concealed_triplets_ignores_which_tile_won(self):
        # Rulebook 6.4: a triplet completed from another player's discard is not concealed.
        r = score_hand(player("m1 m1 m1 m3 m3 m3 p5 p5 p5 s7 s7 s7 N N"), P("s7"), WinSource.DISCARD, 0, 0,
                       discarder=1, profile=hkma_profile())
        self.assertEqual([h.name for h in r.patterns], ["four_concealed_pongs"])

    def test_last_tile_also_counts_on_a_discard_win(self):
        # Rulebook 1.9: Last Tile from Wall is a win by drawing the last tile.
        r = score_hand(player("m1 m2 m3 m4 m5 m6 p1 p2 p3 C C C s2 s2"), None, WinSource.DISCARD, 0, 1,
                       discarder=1, last_tile=True, profile=hkma_profile())
        self.assertIn("last_tile", [h.name for h in r.patterns])

    def test_nine_gates_does_not_check_the_wait(self):
        # Rulebook 6.11: on a discard win the hand must have been waiting on all nine tiles.
        r = score_hand(player("m1 m1 m1 m2 m3 m4 m5 m6 m7 m8 m9 m9 m9 m5"), P("m1"), WinSource.DISCARD, 0, 0,
                       discarder=1, profile=hkma_profile())
        self.assertEqual([h.name for h in r.patterns], ["nine_gates"])

    def test_there_is_no_pao(self):
        # Rulebook "Pao (Liability)": not modelled. The discarder of a fourth-meld tile pays nothing extra.
        self.assertNotIn("bao", hkma_profile().data)


if __name__ == "__main__":
    unittest.main()
