"""Playing one game: four players at four seats, one deal, one result."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hkbench.engine.game import GameState
from hkbench.engine.game_types import GameEventKind
from hkbench.engine.tiles import bonus_name, tile_name
from hkbench.engine.types import MeldKind
from hkbench.engine.profile import RulesProfile
from hkbench.players import Player
from hkbench import runkey
from hkbench.tables import Deal
from hkbench.view import build_view

MAX_DECISIONS = 2000


def winning_hand(state: GameState) -> Dict[str, Any]:
    """The winner's hand at the end of a won game: what a training set wants beside the patterns.

    ``melds`` are [kind, tiles, seat the claimed tile came from or null]; ``concealed`` is the winner's
    concealed tiles with the winning tile in it; ``winning_tile`` is null for a flower win; ``winner_draws``
    counts the winner's own draws from the engine's DRAW events.
    """
    winner = state.terminal.winner
    player = state.players[winner]
    wins = [e for e in state.events if e.kind == GameEventKind.WIN]
    tile = wins[-1].tile_type if wins else None
    return {
        "melds": [[MeldKind(m.kind).name.lower(), [tile_name(t) for t in m.tiles], m.from_seat]
                  for m in player.melds],
        "concealed": [tile_name(t) for t, n in enumerate(player.concealed) for _ in range(n)],
        "winning_tile": None if tile is None else tile_name(tile),
        "flowers": [bonus_name(b) for b in player.flowers],
        "winner_draws": sum(1 for e in state.events if e.kind == GameEventKind.DRAW and e.seat == winner),
    }


def play_game(
    table_id: str,
    profile: RulesProfile,
    deal: Deal,
    players: List[Player],
    *,
    arrangement: int,
    seed_key: Optional[int] = None,
    run_key: bytes = runkey.PUBLIC_RUN_KEY,
    record_actions: bool = False,
    training_log: bool = False,
    check_invariants: bool = False,
    on_decision=None,
) -> Dict[str, Any]:
    """Play one hand to the end and return its record.

    ``players[s]`` sits at absolute seat ``s``. ``arrangement`` labels which rotation or seat pair
    this is within the deal (it names the game). ``seed_key`` picks the per-decision seeds; it defaults
    to ``arrangement``. Head-to-head games that mirror each other share a key, so a bot played
    against itself draws the same random numbers on both sides. ``run_key`` keys both the seeds and the
    game's id (``hkbench.runkey``): the deal's own seed is never an input to anything a bot is sent.
    ``on_decision(state, seat, msg)`` is called before each decision; the fair-play tests use it.
    ``training_log`` adds the winner's melds, concealed tiles, winning tile, flowers and draw count to the
    record of a won game (see ``winning_hand``). It is off by default and changes nothing else.
    """
    state = GameState.new_game(profile, seed=deal.seed, dealer=deal.dealer,
                               prevailing_wind=deal.prevailing_wind)
    game_id = runkey.game_id(run_key, table_id, deal.index, arrangement)
    key = arrangement if seed_key is None else seed_key
    faults: List[Dict[str, int]] = [{} for _ in range(4)]
    actions: List[List[int]] = []
    decisions = [0, 0, 0, 0]
    seq = 0
    while not state.is_terminal():
        actor = state.current_actor()
        if not isinstance(actor, int):
            raise RuntimeError("a live game has no one to act")
        msg = build_view(state, actor, game_id=game_id, seq=seq,
                         rng_seed=runkey.decision_seed(run_key, table_id, deal.index, key, seq), table_id=table_id)
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
    if training_log and r.winner is not None:
        rec.update(winning_hand(state))
    for seat, p in enumerate(players):
        msg = {"type": "game_over", "game_id": game_id, "cause": r.cause,
               "winner": None if r.winner is None else (r.winner - seat) % 4,
               "discarder": None if r.discarder is None else (r.discarder - seat) % 4,
               "faan": r.faan, "patterns": rec["patterns"], "payment": r.payments[seat]}
        p.game_over(msg)
    return rec
