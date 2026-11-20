"""Chicken-hand rules (hk-chicken-v1): a complete hand with no scoring pattern may win.

The table is HKMA Classical with one change, ``win.minimum_faan: 0``. A chicken hand wins and pays
the 0-faan row there, and is refused on hk-hkma-v1. Faan still score as usual, and the two
tables that were already published keep their pins and fingerprints.
"""

import copy
import json
import unittest

from helpers import ROOT, hkma_profile, hkma_table, house_profile, house_table

from hkbench import fingerprint
from hkbench.engine.game import PendingOffer, new_game
from hkbench.engine.profile import load_profile
from hkbench.engine.scorer import can_declare_win, score_hand
from hkbench.engine.tiles import parse_tile as P
from hkbench.engine.types import Meld, MeldKind, Phase, PlayerState, WinSource
from hkbench.fingerprint import score_corpus_hand
from hkbench.tables import load_table

_cache = {}


def chicken_profile():
    if "c" not in _cache:
        _cache["c"] = load_profile(ROOT / "tables" / "hk-chicken-v1" / "rules.json")
    return _cache["c"]


def chicken_table():
    return load_table("hk-chicken-v1")


def counts(text):
    c = [0] * 34
    for t in text.split():
        c[P(t)] += 1
    return c


# An open pong of 1-circles, three chows in three suits and a pair of 8-bamboo: no flush, no
# honours, no dragon or wind pong, not all chows, not all pongs, not concealed. It scores nothing.
OPEN_PONG = Meld(MeldKind.PONG, (P("p1"),) * 3, from_seat=3, claimed_tile=P("p1"))
CHICKEN_TEN = "m2 m3 m4 p5 p6 p7 s3 s4 s5 s8"  # waiting on s8, the pair
CHICKEN_ELEVEN = CHICKEN_TEN + " s8"


def chicken_hand():
    return PlayerState(concealed=counts(CHICKEN_ELEVEN), melds=[OPEN_PONG], flowers=[], seat=0)


def scoring(result):
    """The faan items that count for something. The scorer also lists no_flowers at 0 on a table where flowers do not score."""
    return {p.name: p.faan for p in result.patterns if p.faan}


def score(profile, source=WinSource.DISCARD):
    return score_hand(chicken_hand(), P("s8"), source, 0, 0, discarder=None if source == WinSource.SELF_DRAW else 3,
                      profile=profile)


class RulesFile(unittest.TestCase):
    def test_it_is_hkma_with_one_change(self):
        chicken, hkma = copy.deepcopy(chicken_profile().data), copy.deepcopy(hkma_profile().data)
        self.assertEqual(chicken["win"]["minimum_faan"], 0)
        self.assertEqual(hkma["win"]["minimum_faan"], 3)
        for d in (chicken, hkma):
            for key in ("profile_id", "description", "derived_from"):
                d.pop(key)
            d["win"].pop("minimum_faan")
        self.assertEqual(chicken, hkma)

    def test_it_names_where_it_came_from(self):
        derived = chicken_profile().data["derived_from"]
        self.assertEqual(derived["profile"], "hk-hkma-v1")
        self.assertEqual(derived["rules_hash"], hkma_profile().rules_hash)
        self.assertIn("minimum_faan", derived["change"])

    def test_it_is_not_the_no_faan_hit_and_run_table(self):
        p = chicken_profile()
        self.assertEqual((p.minimum_faan, p.faan_cap), (0, 10))
        self.assertGreater(p.patterns["pure_one_suit"], 0)
        self.assertEqual(p.payment_table[0], 1)
        self.assertGreater(p.payment_table[10], p.payment_table[3])

    def test_the_table_is_active_and_pinned(self):
        t = chicken_table()
        self.assertEqual(t.status, "active")
        self.assertEqual(t.profile.rules_sha256, t.data["rules_sha256"])
        self.assertEqual(t.pinned_fingerprint()["rules_sha256"], t.data["rules_sha256"])
        t.verify_field()
        self.assertFalse(chicken_profile().seven_pairs)

    def test_its_public_deals_do_not_overlap_the_other_tables(self):
        ranges = [(tbl.public_range["start"], tbl.public_range["start"] + tbl.public_range["count"])
                  for tbl in (hkma_table(), house_table(), chicken_table())]
        for i, (lo, hi) in enumerate(ranges):
            for lo2, hi2 in ranges[i + 1:]:
                self.assertTrue(hi <= lo2 or hi2 <= lo)


class ChickenHandScores(unittest.TestCase):
    def test_the_hand_scores_nothing_on_either_table(self):
        for profile in (chicken_profile(), hkma_profile()):
            with self.subTest(profile.profile_id):
                r = score(profile)
                self.assertEqual(scoring(r), {})
                self.assertEqual((r.total_faan, r.capped_faan), (0, 0))

    def test_it_wins_on_chicken_and_pays_the_zero_faan_row(self):
        r = score(chicken_profile())
        self.assertTrue(r.meets_minimum)
        self.assertEqual(chicken_profile().payment_table[0], 1)
        self.assertEqual(r.payments, [1, 0, 0, -1])  # the discarder (seat 3) pays the whole hand
        self.assertEqual(sum(r.payments), 0)

    def test_it_is_refused_on_hkma(self):
        r = score(hkma_profile())
        self.assertFalse(r.meets_minimum)
        self.assertEqual(r.payments, [0, 0, 0, 0])
        self.assertFalse(can_declare_win(chicken_hand(), P("s8"), WinSource.DISCARD, 0, 0, discarder=3, profile=hkma_profile()))
        self.assertTrue(can_declare_win(chicken_hand(), P("s8"), WinSource.DISCARD, 0, 0, discarder=3, profile=chicken_profile()))

    def test_it_is_refused_on_house_too(self):
        self.assertFalse(score(house_profile()).meets_minimum)

    def test_faan_still_score_and_pay_as_usual(self):
        # The same hand with the open pong swapped for a dragon pong is worth one faan: a win on the chicken table,
        # still refused on HKMA, and paid from the 1-faan row.
        dragon_pong = Meld(MeldKind.PONG, (P("C"),) * 3, from_seat=3, claimed_tile=P("C"))
        player = PlayerState(concealed=counts(CHICKEN_ELEVEN), melds=[dragon_pong], flowers=[], seat=0)
        for profile, one_faan_ok in ((chicken_profile(), True), (hkma_profile(), False)):
            with self.subTest(profile.profile_id):
                r = score_hand(player, P("s8"), WinSource.DISCARD, 0, 0, discarder=3, profile=profile)
                self.assertEqual(scoring(r), {"dragon_pong": 1})
                self.assertEqual(r.meets_minimum, one_faan_ok)
                if one_faan_ok:
                    self.assertEqual(r.payments, [profile.payment_table[1], 0, 0, -profile.payment_table[1]])
        # A hand over the HKMA minimum is paid the same on both tables, and the cap is still 10.
        big = PlayerState(concealed=counts("E E E S S S W W W N N m5 m6 m7"), melds=[], flowers=[], seat=0)
        a = score_hand(big, None, WinSource.DISCARD, 0, 0, discarder=2, profile=hkma_profile())
        b = score_hand(big, None, WinSource.DISCARD, 0, 0, discarder=2, profile=chicken_profile())
        self.assertEqual((a.patterns, a.capped_faan, a.payments), (b.patterns, b.capped_faan, b.payments))
        self.assertEqual(b.capped_faan, 10)

    def test_a_chicken_hand_is_always_a_discard_win_with_a_meld_showing(self):
        # Self-Drawn and Closed Hand are one faan each, so a win with either is not a chicken hand.
        self_drawn = score(chicken_profile(), WinSource.SELF_DRAW)
        self.assertEqual(scoring(self_drawn), {"self_draw": 1})
        closed = PlayerState(concealed=counts("m2 m3 m4 p5 p6 p7 s3 s4 s5 p1 p1 p1 s8 s8"), melds=[], flowers=[], seat=0)
        r = score_hand(closed, P("s8"), WinSource.DISCARD, 0, 0, discarder=3, profile=chicken_profile())
        self.assertEqual(scoring(r), {"fully_concealed": 1})


class ChickenHandInPlay(unittest.TestCase):
    def claim_state(self, profile):
        state = new_game(profile, seed=7, dealer=0)
        claimer = 2
        pl = state.players[claimer]
        pl.concealed = counts(CHICKEN_TEN)
        pl.melds = [Meld(MeldKind.PONG, (P("p1"),) * 3, from_seat=3, claimed_tile=P("p1"))]
        pl.flowers = []
        state.phase = Phase.REACTION
        state.offer = PendingOffer(tile=P("s8"), from_seat=1)
        state.reaction_eligible = [claimer]
        return state, claimer

    def test_the_engine_offers_the_win_on_chicken_and_not_on_hkma(self):
        for profile, offered in ((chicken_profile(), True), (hkma_profile(), False)):
            with self.subTest(profile.profile_id):
                state, claimer = self.claim_state(profile)
                self.assertEqual(1 in state.legal_actions(claimer), offered)

    def test_declaring_it_ends_the_game_with_the_zero_faan_payment(self):
        state, claimer = self.claim_state(chicken_profile())
        self.assertEqual(state.current_actor(), claimer)
        state.apply_action(1)
        t = state.terminal
        self.assertEqual(t.cause, "win")
        self.assertEqual((t.winner, t.discarder, t.faan), (claimer, 1, 0))
        self.assertEqual(t.payments, [0, -1, 1, 0])
        self.assertEqual([p for p in t.pattern_breakdown if p["faan"]], [])


class FingerprintsAndPins(unittest.TestCase):
    def test_the_new_fingerprint_reproduces(self):
        t = chicken_table()
        fp = fingerprint.verify(t)
        self.assertEqual(fp["sha256"], t.pinned_fingerprint()["sha256"])
        self.assertEqual((fp["deals"], fp["hands"]), (300, 42))
        # More hands win when the minimum is 0.
        self.assertGreater(fp["wins"], json.loads((ROOT / "tables" / "hk-hkma-v1" / "fingerprint.json").read_text())["wins"])

    def test_the_two_existing_tables_keep_their_pins_and_fingerprints(self):
        # These values are the ones the tables carried before hk-chicken-v1 was added.
        expected = {
            "hk-hkma-v1": ("43e4e01c50dce4d3dde5ba4f07d728e533e8c92ddb095372b3d718933ae16882",
                           "c22def21b784b7f30b671ba90c8ed3f4a62277f97f758c312913e2d290a7187c"),
            "hk-house-v1": ("6318ed16cdaf40f09692c5873ae58400513b9fbaffe0da7efe1a20464a2872e6",
                            "40776e78617bb1ec4df7d98caa83e70a9bf3f7b0db5c825007d5fac74aa93637"),
        }
        field = {"faan_aware": "972ea29c307f20fd5a3b68468d82e32865ead34267e49023d5f02372154fc1c6",
                 "ukeire": "6f07353dbde5ac9b90193266241103304b5ae2281480f53f6c6273cfef72e648",
                 "deficiency": "6f07353dbde5ac9b90193266241103304b5ae2281480f53f6c6273cfef72e648"}
        for tid, (rules_sha, fp_sha) in expected.items():
            with self.subTest(tid):
                t = load_table(tid)
                self.assertEqual(t.data["rules_sha256"], rules_sha)
                self.assertEqual(t.profile.rules_sha256, rules_sha)
                self.assertEqual(t.pinned_fingerprint()["sha256"], fp_sha)
                self.assertEqual(fingerprint.verify(t)["sha256"], fp_sha)
                self.assertEqual({m["bot"]: m["sha256"] for m in t.field}, field)
                t.verify_field()

    def test_the_field_is_the_same_as_hkma(self):
        self.assertEqual(chicken_table().field, hkma_table().field)

    def test_every_corpus_hand_agrees_with_hkma_at_or_above_its_minimum(self):
        cases = json.loads((ROOT / "tests" / "fixtures" / "hands.json").read_text())["cases"]
        below = not_wins = 0
        for case in cases:
            h = score_corpus_hand(hkma_profile(), case)
            c = score_corpus_hand(chicken_profile(), case)
            with self.subTest(case["id"]):
                if not c["ok"]:
                    # Not a complete hand on HKMA's rules (Seven Pairs, a four of a kind read as two pairs):
                    # a lower minimum does not make it a win.
                    not_wins += 1
                    self.assertEqual(c, h)
                    self.assertEqual(c["total"], 0)
                    continue
                self.assertEqual((c["patterns"], c["total"], c["faan"], c["limit"]), (h["patterns"], h["total"], h["faan"], h["limit"]))
                self.assertEqual(sum(c["payments"]), 0)
                if h["ok"]:
                    self.assertEqual(c["payments"], h["payments"])
                else:
                    below += 1
                    self.assertEqual(h["payments"], [0, 0, 0, 0])
                    self.assertGreater(max(c["payments"]), 0)
        self.assertGreater(below, 0)  # the corpus does hold complete hands under the HKMA minimum
        self.assertGreater(not_wins, 0)  # and hands that are not complete under HKMA's rules, which stay refused


if __name__ == "__main__":
    unittest.main()
