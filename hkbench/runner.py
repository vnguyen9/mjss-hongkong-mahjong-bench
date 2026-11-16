"""Playing one game: four players at four seats, one deal, one result."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hkbench.engine.game import GameState
from hkbench.engine.profile import RulesProfile
from hkbench.players import Player
from hkbench.seeds import splitmix64
from hkbench.tables import Deal
from hkbench.view import build_view

MAX_DECISIONS = 2000


def decision_seed(deal_seed: int, arrangement: int, seq: int) -> int:
    """The seed a decision message carries for the bot's own randomness (below 2**31)."""
    _, out = splitmix64(((deal_seed & 0xFFFFFFFFFFFF) << 16) ^ (arrangement << 12) ^ seq)
    return out & 0x7FFFFFFF


def play_game(
    table_id: str,
    profile: RulesProfile,
    deal: Deal,
    players: List[Player],
    *,
    arrangement: int,
    seed_key: Optional[int] = None,
    record_actions: bool = False,
    check_invariants: bool = False,
    on_decision=None,
) -> Dict[str, Any]:
    """Play one hand to the end and return its record.

    ``players[s]`` sits at absolute seat ``s``. ``arrangement`` labels which rotation or seat pair
    this is within the deal (it names the game). ``seed_key`` picks the per-decision seeds; it defaults
    to ``arrangement``. Head-to-head games that mirror each other share a key, so a bot played
    against itself draws the same random numbers on both sides.
    ``on_decision(state, seat, msg)`` is called before each decision; the fair-play tests use it.
    """
    state = GameState.new_game(profile, seed=deal.seed, dealer=deal.dealer,
                               prevailing_wind=deal.prevailing_wind)
    game_id = "%s/d%d/a%d" % (table_id, deal.index, arrangement)
    faults: List[Dict[str, int]] = [{} for _ in range(4)]
    actions: List[List[int]] = []
    decisions = [0, 0, 0, 0]
    seq = 0
    while not state.is_terminal():
        actor = state.current_actor()
        if not isinstance(actor, int):
            raise RuntimeError("a live game has no one to act")
        msg = build_view(state, actor, game_id=game_id, seq=seq,
                         rng_seed=decision_seed(deal.seed, arrangement if seed_key is None else seed_key, seq), table_id=table_id)
        if on_decision is not None:
            on_decision(state, actor, msg)
        action, fault = players[actor].decide(msg)
        if fault:
            faults[actor][fault] = faults[actor].get(fault, 0) + 1
        state.apply_action(action)
        if check_invariants:
            state.check_invariants().raise_if_failed()
        if record_actions:
            actions.append([actor, action])
        decisions[actor] += 1
        seq += 1
        if seq > MAX_DECISIONS:
            raise RuntimeError("a game ran past %d decisions" % MAX_DECISIONS)

    r = state.terminal
    assert r is not None
    rec: Dict[str, Any] = {
        "deal": deal.index,
        "arrangement": arrangement,
        "dealer": deal.dealer,
        "prevailing_wind": deal.prevailing_wind,
        "cause": r.cause,
        "winner": r.winner,
        "discarder": r.discarder,
        "win_source": r.win_source.name if r.win_source else None,
        "faan": r.faan,
        "patterns": [[p["name"], p["faan"]] for p in r.pattern_breakdown],
        "payments": list(r.payments),
        "decisions": decisions,
        "wall_remaining": state.wall_remaining(),
        "faults": faults,
    }
    if record_actions:
        rec["seed"] = deal.seed
        rec["actions"] = actions
    for seat, p in enumerate(players):
        msg = {"type": "game_over", "game_id": game_id, "cause": r.cause,
               "winner": None if r.winner is None else (r.winner - seat) % 4,
               "discarder": None if r.discarder is None else (r.discarder - seat) % 4,
               "faan": r.faan, "patterns": rec["patterns"], "payment": r.payments[seat]}
        p.game_over(msg)
    return rec
