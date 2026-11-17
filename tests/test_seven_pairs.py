"""Seven Pairs at hk-house-v1, and its absence at hk-hkma-v1.

The expected values are worked out by hand from the House rules file: Seven Pairs is 4 faan, it
stacks with the flush items, Self-Drawn, Closed Hand, Last Tile and the flowers, All Honours by
Seven Pairs is a limit hand that keeps how it was won, and the total is capped at 13.
"""

import unittest

from helpers import hkma_profile, house_profile, house_table

from hkbench import fingerprint
from hkbench.engine.game import new_game
from hkbench.engine.scorer import can_declare_win, score_hand
from hkbench.engine.tiles import BONUS_NAMES, parse_tile as P
from hkbench.engine.types import Meld, MeldKind, Phase, PlayerState, WinSource
from hkbench.engine.win import can_win_structurally, is_seven_pairs
from hkbench.seeds import Rng

MIXED = "m1 m1 m3 m3 m5 m5 s2 s2 s4 s4 p6 p6 p8 p8"  # three suits, no honours
FULL_FLUSH = "m1 m1 m2 m2 m4 m4 m5 m5 m7 m7 m8 m8 m9 m9"
HALF_FLUSH = "m1 m1 m2 m2 m4 m4 m5 m5 m7 m7 m8 m8 E E"
ALL_HONOURS = "E E S S W W N N C C F F P P"
MIXED_TERMINALS = "m1 m1 m9 m9 s1 s1 s9 s9 p1 p1 p9 p9 E E"
TWO_READINGS = "m1 m1 m2 m2 m3 m3 m4 m4 m5 m5 m6 m6 m7 m7"  # also 123 123 456 456 77


def counts(text):
    c = [0] * 34
    for t in text.split():
        c[P(t)] += 1
    return c


def hand(text, flowers=(), melds=()):
    return PlayerState(concealed=counts(text), melds=list(melds), flowers=[BONUS_NAMES.index(f) for f in flowers], seat=0)


def score(text, source=WinSource.DISCARD, profile=None, flowers=(), melds=(), **flags):
    return score_hand(hand(text, flowers, melds), None, source, 0, 0,
                      discarder=None if source == WinSource.SELF_DRAW else 3,
                      profile=profile or house_profile(), **flags)


def named(result):
    return {p.name: p.faan for p in result.patterns}


# (name, hand, source, flowers, flags, expected patterns, expected total faan)
CASES = [
    ("plain discard win", MIXED, WinSource.DISCARD, (), {},
     {"seven_pairs": 4, "fully_concealed": 1, "no_flowers": 1}, 6),
    ("plain self-draw", MIXED, WinSource.SELF_DRAW, (), {},
     {"seven_pairs": 4, "self_draw": 1, "fully_concealed": 1, "no_flowers": 1}, 7),
    ("seat flower replaces no-flowers", MIXED, WinSource.DISCARD, ("Fl1",), {},
     {"seven_pairs": 4, "fully_concealed": 1, "seat_flower": 1}, 6),
    ("a flower for another seat pays nothing", MIXED, WinSource.DISCARD, ("Fl2",), {},
     {"seven_pairs": 4, "fully_concealed": 1}, 5),
    ("full flush stacks 7 on 4", FULL_FLUSH, WinSource.DISCARD, (), {},
     {"seven_pairs": 4, "pure_one_suit": 7, "fully_concealed": 1, "no_flowers": 1}, 13),
    ("full flush self-draw is 14 and caps at 13", FULL_FLUSH, WinSource.SELF_DRAW, (), {},
     {"seven_pairs": 4, "pure_one_suit": 7, "self_draw": 1, "fully_concealed": 1, "no_flowers": 1}, 14),
    ("half flush stacks 3 on 4", HALF_FLUSH, WinSource.DISCARD, (), {},
     {"seven_pairs": 4, "mixed_one_suit": 3, "fully_concealed": 1, "no_flowers": 1}, 9),
    ("half flush self-draw", HALF_FLUSH, WinSource.SELF_DRAW, (), {},
     {"seven_pairs": 4, "mixed_one_suit": 3, "self_draw": 1, "fully_concealed": 1, "no_flowers": 1}, 10),
    ("all honours is a limit hand and drops everything else", ALL_HONOURS, WinSource.DISCARD, (), {},
     {"all_honors": 10}, 10),
    ("all honours by self-draw keeps self-draw", ALL_HONOURS, WinSource.SELF_DRAW, (), {},
     {"all_honors": 10, "self_draw": 1}, 11),
    ("terminals and honours score 4 on top of the 4", MIXED_TERMINALS, WinSource.DISCARD, (), {},
     {"seven_pairs": 4, "mixed_orphans": 4, "fully_concealed": 1, "no_flowers": 1}, 10),
    ("last tile", MIXED, WinSource.DISCARD, (), {"last_tile": True},
     {"seven_pairs": 4, "fully_concealed": 1, "last_tile": 1, "no_flowers": 1}, 7),
    ("robbing a kong", MIXED, WinSource.ROB_KONG, (), {},
     {"seven_pairs": 4, "rob_kong": 1, "fully_concealed": 1, "no_flowers": 1}, 7),
    ("seven pairs beats the ordinary reading of the same tiles", TWO_READINGS, WinSource.DISCARD, (), {},
     {"seven_pairs": 4, "pure_one_suit": 7, "fully_concealed": 1, "no_flowers": 1}, 13),
    ("a heavenly hand is a limit hand that keeps self-draw", MIXED, WinSource.SELF_DRAW, (), {"heavenly": True},
     {"heavenly_hand": 13, "self_draw": 1}, 14),
]


class SevenPairsScoring(unittest.TestCase):
    def test_every_case(self):
        for name, text, source, flowers, flags, expected, total in CASES:
            with self.subTest(name):
                r = score(text, source, flowers=flowers, **flags)
                self.assertEqual(named(r), expected)
                self.assertEqual(r.total_faan, total)
                self.assertEqual(r.capped_faan, min(total, 13))
                self.assertTrue(r.meets_minimum)
                self.assertEqual(sum(r.payments), 0)

    def test_a_self_drawn_all_honours_seven_pairs_is_eleven_and_pays_for_eleven(self):
        # The limit-hand rule and Seven Pairs meet here: All Honours 10 keeps Self-Drawn 1.
        r = score(ALL_HONOURS, WinSource.SELF_DRAW)
        self.assertEqual([(p.name, p.faan) for p in r.patterns], [("all_honors", 10), ("self_draw", 1)])
        self.assertEqual((r.total_faan, r.capped_faan, r.is_limit), (11, 11, True))
        self.assertEqual(r.payments, [288, -96, -96, -96])  # table[11] = 192, times 1.5, split three ways

    def test_all_honours_seven_pairs_keeps_every_win_condition(self):
        r = score(ALL_HONOURS, WinSource.SELF_DRAW, last_tile=True, after_kong=True)
        self.assertEqual([p.name for p in r.patterns], ["all_honors", "self_draw", "last_tile", "kong_replacement"])
        self.assertEqual((r.total_faan, r.capped_faan), (13, 13))
        r = score(ALL_HONOURS, WinSource.ROB_KONG)
        self.assertEqual([p.name for p in r.patterns], ["all_honors", "rob_kong"])
        self.assertEqual(r.capped_faan, 11)
        r = score(ALL_HONOURS, WinSource.SELF_DRAW, last_tile=True, after_double_kong=True)
        self.assertEqual([p.name for p in r.patterns], ["all_honors", "self_draw", "last_tile", "double_kong"])
        self.assertEqual((r.total_faan, r.capped_faan), (20, 13))

    def test_all_honours_seven_pairs_drops_flowers_and_closed_hand(self):
        r = score(ALL_HONOURS, WinSource.DISCARD, flowers=("Fl1", "Fl2", "Fl3", "Fl4"))
        self.assertEqual(named(r), {"all_honors": 10})

    def test_all_honours_by_seven_pairs_is_worth_the_same_as_by_sets(self):
        sets = score("E E E S S S W W W C C C F F", WinSource.SELF_DRAW)
        pairs = score(ALL_HONOURS, WinSource.SELF_DRAW)
        self.assertEqual((sets.capped_faan, sets.payments), (pairs.capped_faan, pairs.payments))

    def test_when_both_readings_reach_the_cap_the_richer_one_is_named(self):
        # 11223344556677, self-drawn, last tile, all four flowers. As sets: All Sequences 1 + Flush 7
        # + Self-Drawn 1 + Closed Hand 1 + Last Tile 1 + four flowers 2 = 13. As pairs: 4 + 7 + 1 + 1 + 1 + 2 = 16.
        flowers = ("Fl1", "Fl2", "Fl3", "Fl4")
        r = score(TWO_READINGS, WinSource.SELF_DRAW, flowers=flowers, last_tile=True)
        self.assertIn("seven_pairs", named(r))
        self.assertEqual((r.total_faan, r.capped_faan), (16, 13))
        house_sets_only = score("m1 m2 m3 m1 m2 m3 m4 m5 m6 m4 m5 m6 m7 m7", WinSource.SELF_DRAW, flowers=flowers,
                                last_tile=True)
        self.assertEqual(house_sets_only.capped_faan, 13)
        self.assertEqual(house_sets_only.payments, r.payments)  # the same money either way

    def test_the_ordinary_reading_of_the_overlap_hand_alone_is_worth_less(self):
        from hkbench.engine.profile import profile_from_dict
        import copy

        data = copy.deepcopy(house_profile().data)
        data["win"]["seven_pairs"] = False
        ordinary = score(TWO_READINGS, profile=profile_from_dict(data))
        self.assertEqual((ordinary.total_faan, "seven_pairs" in named(ordinary)), (10, False))


class SevenPairsShape(unittest.TestCase):
    def test_four_of_a_kind_is_not_two_pairs(self):
        four = "m1 m1 m1 m1 m3 m3 m5 m5 s2 s2 s4 s4 p6 p6"
        self.assertFalse(is_seven_pairs(counts(four)))
        r = score(four)
        self.assertFalse(r.meets_minimum)
        self.assertEqual(r.patterns, [])
        self.assertFalse(can_declare_win(hand(four), None, WinSource.DISCARD, 0, 0, discarder=3, profile=house_profile()))

    def test_a_triplet_and_a_single_is_not_seven_pairs(self):
        self.assertFalse(is_seven_pairs(counts("m1 m1 m1 m3 m3 m5 m5 s2 s2 s4 s4 p6 p6 p8")))

    def test_thirteen_or_fifteen_tiles_are_not_seven_pairs(self):
        self.assertFalse(is_seven_pairs(counts(" ".join(MIXED.split()[:-1]))))
        self.assertFalse(is_seven_pairs(counts(MIXED + " p8")))

    def test_any_declared_meld_rules_seven_pairs_out_a_concealed_kong_too(self):
        kong = Meld(MeldKind.CONCEALED_KONG, (P("C"),) * 4)
        r = score(MIXED, WinSource.SELF_DRAW, melds=[kong])
        self.assertFalse(r.meets_minimum)
        self.assertEqual(r.patterns, [])

    def test_the_shared_structural_check_does_not_know_seven_pairs(self):
        self.assertFalse(can_win_structurally(counts(MIXED), []))


class SevenPairsOnlyWhereTheTablePlaysIt(unittest.TestCase):
    def test_hkma_never_scores_it(self):
        self.assertFalse(hkma_profile().seven_pairs)
        for text in (MIXED, FULL_FLUSH, ALL_HONOURS, MIXED_TERMINALS):
            with self.subTest(text):
                r = score(text, WinSource.SELF_DRAW, profile=hkma_profile())
                self.assertEqual((r.patterns, r.meets_minimum), ([], False))

    def test_the_same_overlap_hand_reads_as_sets_on_hkma(self):
        r = score(TWO_READINGS, profile=hkma_profile())
        self.assertNotIn("seven_pairs", named(r))
        self.assertEqual(r.capped_faan, 9)  # All Sequences 1 + Flush 7 + Closed Hand 1; flowers score nothing on HKMA

    def test_house_is_the_only_shipped_table_that_plays_it(self):
        self.assertTrue(house_profile().seven_pairs)
        self.assertEqual(house_profile().patterns["seven_pairs"], 4)
        self.assertNotIn("seven_pairs", hkma_profile().patterns)


def _wall_for_dealer(tiles14):
    """A wall in which the dealer is dealt the first thirteen tiles and draws the fourteenth."""
    copies = [0] * 34
    wall = [None] * 144
    taken = set()

    def instance(tile):
        iid = 4 * tile + copies[tile]
        copies[tile] += 1
        taken.add(iid)
        return iid

    for k in range(13):
        wall[4 * k] = instance(tiles14[k])
    wall[52] = instance(tiles14[13])
    pool = [i for i in range(136) if i not in taken]
    rng = Rng(5)
    for i in range(len(pool) - 1, 0, -1):
        j = rng.randrange(i + 1)
        pool[i], pool[j] = pool[j], pool[i]
    it = iter(pool)
    for idx in range(52):
        if wall[idx] is None:
            wall[idx] = next(it)
    rest = list(it) + list(range(136, 144))
    for idx in range(53, 144):
        wall[idx] = rest[idx - 53]
    return wall


class SevenPairsInPlay(unittest.TestCase):
    def test_a_dealer_dealt_seven_pairs_wins_on_house_and_not_on_hkma(self):
        tiles = [P(t) for t in MIXED.split()]
        for profile, can in ((house_profile(), True), (hkma_profile(), False)):
            with self.subTest(profile.profile_id):
                state = new_game(profile, seed=0, supplied_wall=_wall_for_dealer(tiles), dealer=0)
                self.assertEqual(state.current_actor(), 0)
                self.assertEqual(1 in state.legal_actions(0), can)
        state = new_game(house_profile(), seed=0, supplied_wall=_wall_for_dealer(tiles), dealer=0)
        state.apply_action(1)
        t = state.terminal
        self.assertEqual(t.cause, "win")
        self.assertEqual([p["name"] for p in t.pattern_breakdown], ["heavenly_hand", "self_draw"])
        self.assertEqual((t.faan, t.payments), (13, [576, -192, -192, -192]))
        self.assertTrue(state.check_invariants().ok)

    def test_a_self_drawn_all_honours_seven_pairs_in_a_real_game(self):
        tiles = [P(t) for t in ALL_HONOURS.split()]
        state = new_game(house_profile(), seed=0, supplied_wall=_wall_for_dealer(tiles), dealer=0)
        state.apply_action(1)
        # The dealer's first draw makes it Bless of Heaven (13), which also keeps Self-Drawn.
        self.assertEqual([p["name"] for p in state.terminal.pattern_breakdown], ["heavenly_hand", "self_draw"])

    def test_a_discard_that_completes_seven_pairs_can_be_claimed_only_on_house(self):
        from hkbench.engine.game import PendingOffer

        for profile, can in ((house_profile(), True), (hkma_profile(), False)):
            with self.subTest(profile.profile_id):
                state = new_game(profile, seed=7, dealer=0)
                claimer = 2
                state.players[claimer].concealed = counts(" ".join(MIXED.split()[:-1]))  # six pairs and a lone p8
                state.phase = Phase.REACTION
                state.offer = PendingOffer(tile=P("p8"), from_seat=1)
                state.reaction_eligible = [claimer]
                self.assertEqual(1 in state.legal_actions(claimer), can)

    def test_a_declared_meld_stops_the_self_draw_win(self):
        kong = Meld(MeldKind.CONCEALED_KONG, (P("C"),) * 4)
        state = new_game(house_profile(), seed=7, dealer=0)
        seat = state.current_actor()
        state.players[seat].concealed = counts(MIXED)
        state.players[seat].melds = [kong]
        self.assertNotIn(1, state.legal_actions(seat))


class HouseFingerprint(unittest.TestCase):
    def test_the_house_fingerprint_reproduces(self):
        table = house_table()
        fp = fingerprint.verify(table)
        self.assertEqual(fp["sha256"], table.pinned_fingerprint()["sha256"])

    def test_the_corpus_pins_seven_pairs_scoring(self):
        import json
        from helpers import ROOT

        cases = {c["id"]: c for c in json.loads((ROOT / "tests" / "fixtures" / "hands.json").read_text())["cases"]}
        want = {
            "seven_pairs_discard": (6, ["seven_pairs", "fully_concealed", "no_flowers"]),
            "seven_pairs_all_honors_self_draw": (11, ["all_honors", "self_draw"]),
            "seven_pairs_full_flush": (13, ["seven_pairs", "pure_one_suit", "fully_concealed", "no_flowers"]),
            "four_of_a_kind_is_not_two_pairs": (0, []),
        }
        for cid, (faan, names) in want.items():
            got = fingerprint.score_corpus_hand(house_profile(), cases[cid])
            self.assertEqual((got["faan"], [p[0] for p in got["patterns"]]), (faan, names), cid)
            on_hkma = fingerprint.score_corpus_hand(hkma_profile(), cases[cid])
            self.assertEqual((on_hkma["ok"], on_hkma["patterns"]), (False, []), cid)

    def test_play_on_house_reaches_seven_pairs_wins(self):
        # The fixed policy builds pairs, so over the fingerprint's deals some wins are Seven Pairs.
        wins = 0
        for i in range(120):
            g = fingerprint.play_fingerprint_deal(house_profile(), i)
            if any(name in ("seven_pairs",) or (name == "all_honors" and g["melds"] == [0, 0, 0, 0])
                   for name, _ in g["patterns"]):
                wins += 1
        self.assertGreater(wins, 0)


if __name__ == "__main__":
    unittest.main()
