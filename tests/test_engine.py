"""Engine tests: deals, claims, rob-kong, replay, invariants, and the heavenly-hand fix."""

from __future__ import annotations

import copy
import unittest

from helpers import hkma_profile
from scenarios import ROBBABLE_TILES, build_multi_claim_position, build_rob_kong_position

from hkbench.engine.actions import added_kong_action, discard_action
from hkbench.engine.game import GameState, new_game, replay
from hkbench.engine.tile_instance import STANDARD_INSTANCES, validate_supplied_wall
from hkbench.engine.types import Meld, MeldKind, Phase, WinSource
from hkbench.seeds import Rng, wall_for_seed


ROBBED_TILE = 19  # p2: the tile seat 0 kongs and seat 1 robs


class EngineTests(unittest.TestCase):
    def test_new_game_and_invariants(self):
        state = new_game(hkma_profile(), seed=123)
        assert state.profile.profile_id == "hk-hkma-v1"
        assert state.wall_remaining() > 0
        rep = state.check_invariants()
        assert rep.ok, rep.messages


    def test_supplied_wall_validation(self):
        wall = list(range(144))
        validate_supplied_wall(wall)
        state = new_game(hkma_profile(), seed=0, supplied_wall=wall)
        assert state.chance.mode == "supplied_wall"


    def test_malformed_action_no_mutation(self):
        state = new_game(hkma_profile(), seed=11)
        actor = state.current_actor()
        assert isinstance(actor, int)
        before = copy.deepcopy(state.players[actor].concealed)
        illegal = next(i for i in range(127) if not state.legal_mask(actor)[i])
        try:
            state.apply_action(illegal)
            assert False, "expected ValueError"
        except ValueError:
            assert state.players[actor].concealed == before


    def test_pong_and_kong_cannot_race_on_the_same_discard(self):
        """Why there is no pong-vs-kong race test: the position is unreachable.

        A pong needs 2 concealed copies and a kong needs 3. One copy is on the table as the
        discard, leaving 3 — so a kong claimant consumes every remaining copy and no second
        seat can hold the 2 a pong needs. `_resolve_reactions` puts pong and kong in one
        priority class broken by seat distance, and that tie-break is
        exercised by the win/pong and pong/chow races below; the pong-vs-kong cell of it is
        vacuous. This test pins the arithmetic so the claim is checked rather than asserted.
        """
        state = build_multi_claim_position(tile=4, discarder=0, pong_seat=1)
        state.apply_action(discard_action(4))
        assert state.phase == Phase.REACTION

        # Four copies exist in total, and the discard accounts for one, so at most three are
        # held anywhere else. A kong claimant needs 3 concealed and a pong claimant 2, i.e. 5
        # between two distinct seats — one more than exists, before even counting the discard.
        held = [state.players[s].concealed[4] for s in range(4)]
        in_river = sum(
            1 for s in range(4) for iid in state.river[s]
            if STANDARD_INSTANCES[iid].tile_type == 4
        )
        assert sum(held) + in_river <= 4, (held, in_river)
        assert in_river == 1, "the offered tile is on the table"

        kong_capable = {s for s in range(4) if held[s] >= 3}
        pong_capable = {s for s in range(4) if held[s] >= 2}
        assert not (kong_capable and pong_capable - kong_capable), (kong_capable, pong_capable)

        # And the engine agrees: no state can offer pong to one seat and kong to another.
        offered_pong = {s for s in state.reaction_eligible if state.legal_mask(s)[57]}
        offered_kong = {s for s in state.reaction_eligible if state.legal_mask(s)[58]}
        assert not (offered_pong - offered_kong and offered_kong)


    def test_nearest_seat_wins_a_two_winner_race(self):
        """截糊 — one winner, the nearest seat after the discarder.

        An explicit product decision in the table's rules with no test
        behind it until now. Seats 1 and 2 are both tenpai on the same closed chow wait and
        both declare; seat 1 is one seat from the discarder, seat 2 is two.
        """
        state = build_multi_claim_position(tile=4, discarder=0, win_seats=(1, 2))
        assert state.check_invariants().ok
        state.apply_action(discard_action(4))
        assert sorted(state.reaction_eligible) == [1, 2]
        assert state.legal_mask(1)[1] and state.legal_mask(2)[1], "both seats must be able to win"

        for seat in list(state.reaction_eligible):
            state.apply_action(1)

        assert state.terminal is not None
        assert state.terminal.winner == 1, "nearest seat after the discarder takes the win"
        assert state.terminal.discarder == 0
        assert state.terminal.win_source == WinSource.DISCARD
        # One winner only: exactly one seat is paid, and the table balances.
        assert sum(1 for p in state.terminal.payments if p > 0) == 1
        assert sum(state.terminal.payments) == 0
        assert state.check_invariants().ok, state.check_invariants().messages


    def test_win_outranks_pong_even_from_a_farther_seat(self):
        """Win beats pong/kong regardless of distance ."""
        state = build_multi_claim_position(tile=4, discarder=0, pong_seat=1, win_seats=(2,))
        state.apply_action(discard_action(4))
        assert state.legal_mask(1)[57], "seat 1 must be able to pong"
        assert state.legal_mask(2)[1], "seat 2 must be able to win"

        for seat in list(state.reaction_eligible):
            state.apply_action(1 if state.legal_mask(seat)[1] else 57)

        assert state.terminal is not None
        assert state.terminal.winner == 2, "the win outranks a nearer pong"
        assert not state.players[1].melds, "the losing pong must not have been applied"
        assert state.check_invariants().ok, state.check_invariants().messages


    def test_pong_outranks_chow(self):
        """Pong beats chow even when the chow claimant sits nearer ."""
        state = build_multi_claim_position(tile=4, discarder=0, chow_seat=1, pong_seat=2)
        state.apply_action(discard_action(4))
        assert any(state.legal_mask(1)[36:57]), "seat 1 (left of discarder) must be able to chow"
        assert state.legal_mask(2)[57], "seat 2 must be able to pong"

        for seat in list(state.reaction_eligible):
            mask = state.legal_mask(seat)
            if mask[57]:
                state.apply_action(57)
            else:
                state.apply_action(next(i for i in range(36, 57) if mask[i]))

        assert state.terminal is None
        assert [m.kind for m in state.players[2].melds] == [MeldKind.PONG]
        assert not state.players[1].melds, "the losing chow must not have been applied"
        assert state.check_invariants().ok, state.check_invariants().messages


    def test_claimed_meld_must_trace_to_a_prior_discard(self):
        """Every claimed meld has to correspond to a real earlier discard by that seat.

        Until this landed the rule was guarded only by the `RuntimeError` at `_apply_claim`,
        which fires only when the offer's instance id AND the type fallback both miss — so a
        meld recording the wrong `from_seat` or `claimed_tile` passed every gate. The negative
        half matters more than the positive: an invariant that cannot fail is the `assert True`
        this file just lost.
        """
        state = build_multi_claim_position(tile=4, discarder=0, chow_seat=1, pong_seat=2)
        state.apply_action(discard_action(4))
        for seat in list(state.reaction_eligible):
            mask = state.legal_mask(seat)
            state.apply_action(57 if mask[57] else next(i for i in range(36, 57) if mask[i]))

        assert state.players[2].melds[0].from_seat == 0
        assert state.check_invariants().ok, state.check_invariants().messages

        # Same meld, attributed to a seat that never discarded a 4.
        tampered = copy.deepcopy(state)
        meld = tampered.players[2].melds[0]
        tampered.players[2].melds[0] = Meld(meld.kind, meld.tiles, 3, meld.claimed_tile)
        report = tampered.check_invariants()
        assert not report.ok
        assert any("no matching discard" in m for m in report.messages), report.messages

        # Same meld, claiming a tile that was never discarded at all.
        tampered = copy.deepcopy(state)
        meld = tampered.players[2].melds[0]
        tampered.players[2].melds[0] = Meld(meld.kind, meld.tiles, meld.from_seat, 30)
        report = tampered.check_invariants()
        assert not report.ok
        assert any("no matching discard" in m for m in report.messages), report.messages


    def test_claimed_meld_invariant_counts_multiplicity(self):
        """Two melds claiming the same tile from the same seat need two discards, not one."""
        state = build_multi_claim_position(tile=4, discarder=0, pong_seat=2)
        state.apply_action(discard_action(4))
        state.apply_action(57)
        assert state.check_invariants().ok

        # Duplicate the single legitimate pong. One discard cannot cover both.
        state.players[1].melds.append(state.players[2].melds[0])
        report = state.check_invariants()
        assert not report.ok
        assert any("no matching discard" in m for m in report.messages), report.messages


    def test_instance_catalog(self):
        assert len(STANDARD_INSTANCES) == 144
        assert STANDARD_INSTANCES[0].tile_type == 0
        assert STANDARD_INSTANCES[143].is_bonus


    def test_rob_kong_fixture_is_itself_legal(self):
        """Guards the regression test below: proves the built position is valid, so a
        failure there isolates to the ADDED_KONG -> WIN transition, not the setup."""
        state = build_rob_kong_position(robbed_tile=ROBBED_TILE, declarer=0, winner=1)
        rep = state.check_invariants()
        assert rep.ok, rep.messages


    def test_rob_kong_win_conserves_tile_instances(self):
        """A rob-kong win moves the stolen tile from the declarer's added kong into the winner's hand."""
        state = build_rob_kong_position(robbed_tile=ROBBED_TILE, declarer=0, winner=1)

        # Act through real code paths: _apply_self -> _open_reaction -> _resolve_reactions -> _win
        state.apply_action(added_kong_action(ROBBED_TILE))
        assert state.phase == Phase.REACTION
        assert state.reaction_eligible == [1], state.reaction_eligible
        state.submit_reaction(1, 1)  # ActionKind.WIN

        assert state.is_terminal()
        assert state.terminal is not None
        assert state.terminal.winner == 1
        assert state.terminal.win_source == WinSource.ROB_KONG

        rep = state.check_invariants()
        assert rep.ok, rep.messages

        # The stolen instance moved declarer's meld -> winner's hand, and the meld
        # reverted from a 4-tile ADDED_KONG back to a 3-tile PONG.
        robbed_id = 4 * ROBBED_TILE + 3
        assert robbed_id in state.concealed_ids[1]
        assert robbed_id not in state.meld_ids[0][0]
        assert state.players[0].melds[0].kind == MeldKind.PONG
        assert len(state.players[0].melds[0].tiles) == 3
        assert len(state.meld_ids[0][0]) == 3

        # Faan/payment were never affected by this bug — pin them so the fix stays scoped.
        assert state.terminal.faan == 4  # dragon pong, seat wind pong, rob kong, closed hand
        assert sum(state.terminal.payments) == 0
        assert state.terminal.payments[1] > 0 and state.terminal.payments[0] < 0


    def test_rob_kong_holds_across_tiles_and_seats(self):
        """Same branch across every robbable tile and seat pairing, not just one fixture."""
        checked = 0
        for robbed in ROBBABLE_TILES:
            for declarer, winner in ((0, 1), (1, 3), (2, 0), (3, 2)):
                state = build_rob_kong_position(
                    robbed_tile=robbed, declarer=declarer, winner=winner
                )
                assert state.check_invariants().ok
                state.apply_action(added_kong_action(robbed))
                assert state.reaction_eligible == [winner], (robbed, declarer, winner)
                state.submit_reaction(winner, 1)
                assert state.terminal is not None
                assert state.terminal.win_source == WinSource.ROB_KONG
                rep = state.check_invariants()
                assert rep.ok, (robbed, declarer, winner, rep.messages)
                assert sum(state.terminal.payments) == 0
                checked += 1
        assert checked == len(ROBBABLE_TILES) * 4


    def test_replay_roundtrip_records_actions_and_exact_events(self):
        state = new_game(hkma_profile(), seed=812)
        steps = 0
        while not state.is_terminal() and steps < 2_000:
            actor = state.current_actor()
            assert isinstance(actor, int)
            state.apply_action(state.legal_actions(actor)[0])
            steps += 1
        record = state.serialize_replay()
        rebuilt = replay(record, hkma_profile())
        assert record.actions
        assert rebuilt.events == state.events
        assert rebuilt.terminal == state.terminal
        assert rebuilt.serialize_replay() == record

    def test_walls_are_the_same_on_every_python(self):
        # Pinned so a change to the shuffle (or a port of it to another language) is noticed.
        self.assertEqual(wall_for_seed(0)[:8], [73, 7, 55, 63, 8, 110, 80, 15])
        self.assertEqual(wall_for_seed(1000000)[:8], [53, 41, 32, 124, 28, 50, 21, 22])
        self.assertEqual(wall_for_seed(2**40 + 5)[-4:], [133, 87, 90, 122])
        for seed in (0, 1, 99, 123456789):
            self.assertEqual(sorted(wall_for_seed(seed)), list(range(144)))

    def test_heavenly_hand_is_scored_as_a_limit_hand(self):
        """The dealer completes a hand on the first draw. It scores 10 faan, not its plain faan.

        The hand (123m 456m 789m 111p 55s) is only 2 faan when self-drawn, so scoring it as an
        ordinary hand would pay nothing. The rulebook's Bless of Heaven is 10 faan.
        """
        profile = hkma_profile()
        dealer_tiles = [0, 1, 2, 3, 4, 5, 6, 7, 8, 18, 18, 18, 13, 13]  # 14 tiles, the last is the first draw
        copies = [0] * 34
        wall = [None] * 144
        taken = set()

        def instance(tile):
            iid = 4 * tile + copies[tile]
            copies[tile] += 1
            taken.add(iid)
            return iid

        for k in range(13):
            wall[4 * k] = instance(dealer_tiles[k])
        wall[52] = instance(dealer_tiles[13])
        # Fill everyone else's hands with tiles that cannot win, then the rest of the wall.
        pool = [i for i in range(136) if i not in taken]
        rng = Rng(5)
        for i in range(len(pool) - 1, 0, -1):
            j = rng.randrange(i + 1)
            pool[i], pool[j] = pool[j], pool[i]
        bonus = list(range(136, 144))
        it = iter(pool)
        for idx in range(144):
            if wall[idx] is None and idx < 52:
                wall[idx] = next(it)
        rest = list(it) + bonus
        for idx in range(53, 144):
            wall[idx] = rest[idx - 53]
        state = new_game(profile, seed=0, supplied_wall=wall, dealer=0)
        self.assertIsInstance(state.current_actor(), int)
        self.assertEqual(state.current_actor(), 0)
        self.assertIn(1, state.legal_actions(0))
        state.apply_action(1)
        t = state.terminal
        self.assertEqual(t.cause, "win")
        self.assertEqual([p["name"] for p in t.pattern_breakdown], ["heavenly_hand"])
        self.assertEqual(t.faan, 10)
        self.assertEqual(t.payments, [192, -64, -64, -64])

    def test_random_play_keeps_every_tile_accounted_for(self):
        rng = Rng(11)
        profile = hkma_profile()
        wins = 0
        for deal in range(25):
            state = new_game(profile, seed=500 + deal, dealer=deal % 4, prevailing_wind=(deal // 4) % 4)
            while not state.is_terminal():
                actor = state.current_actor()
                legal = state.legal_actions(actor)
                state.apply_action(rng.choice(legal))
                report = state.check_invariants()
                self.assertTrue(report.ok, report.messages)
            self.assertEqual(sum(state.terminal.payments), 0)
            wins += state.terminal.cause == "win"
        self.assertGreaterEqual(wins, 0)

    def test_flowers_substitute_but_never_end_the_hand_under_hkma(self):
        """HKMA has no seven or eight flower win. Seven flowers in one hand just keep substituting."""
        profile = hkma_profile()
        self.assertFalse(profile.data["flower_rules"]["check_seven_eight_during_deal"])
        self.assertFalse(profile.data["flower_rules"]["check_seven_eight_during_replacement"])
        self.assertEqual(profile.flower_patterns["seven_flowers"], 0)
        self.assertEqual(profile.flower_patterns["eight_flowers"], 0)


if __name__ == "__main__":
    unittest.main()
