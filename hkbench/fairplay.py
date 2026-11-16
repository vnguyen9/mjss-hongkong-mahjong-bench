"""The fair-play check: does a bot's choice depend on tiles it cannot see?

Before a bot is scored, the bench picks real decision points from real games. At each one it
re-shuffles every hidden tile (the other three concealed hands and the live wall) into a new
arrangement that looks identical to the seat, and asks the bot again. Three things are checked:

1. The view the bench builds is identical for every arrangement. If it is not, the bench leaks.
2. The bot gives the same answer to the identical view every time.
3. The bot gives a legal, on-time answer.

Any changed answer rejects the bot. Because the protocol only carries the seat view, a bot that
plays honestly can only fail this by being random without using ``rng_seed``, or by keeping state
that changes its answer. A bot that reads the hidden state some other way (a shared file, the
bench's memory, a network service) is caught when the answers move with the hidden tiles.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from hkbench.engine.game import GameState
from hkbench.engine.profile import RulesProfile
from hkbench.engine.tile_instance import STANDARD_INSTANCES, TileLocation
from hkbench.players import Player, make_player
from hkbench.runner import decision_seed
from hkbench.seeds import Rng, dealer_for_index, wind_for_index
from hkbench.view import build_view

FAIRPLAY_SEED_START = 8_000_000_000
DEFAULT_POINTS = 100
DEFAULT_RESHUFFLES = 2

Hook = Callable[[GameState, int, Dict[str, Any]], None]


def reshuffle_hidden(state: GameState, seat: int, rng: Rng) -> GameState:
    """A copy of ``state`` in which every tile ``seat`` cannot see has been dealt again.

    The other seats keep their hand sizes. The wall keeps its length. Everything the seat can
    see stays exactly as it was.
    """
    s = state.clone()
    others = [x for x in range(4) if x != seat]
    sizes = {o: len(s.concealed_ids[o]) for o in others}
    wall_slice = s.wall_order[s.wall_front:s.wall_rear]
    pool = [iid for o in others for iid in s.concealed_ids[o]] + list(wall_slice)
    regular = [iid for iid in pool if not STANDARD_INSTANCES[iid].is_bonus]
    bonus = [iid for iid in pool if STANDARD_INSTANCES[iid].is_bonus]
    for i in range(len(regular) - 1, 0, -1):
        j = rng.randrange(i + 1)
        regular[i], regular[j] = regular[j], regular[i]
    need = sum(sizes.values())
    hands, rest = regular[:need], regular[need:]
    wall_new = rest + bonus
    for i in range(len(wall_new) - 1, 0, -1):
        j = rng.randrange(i + 1)
        wall_new[i], wall_new[j] = wall_new[j], wall_new[i]
    pos = 0
    for o in others:
        ids = hands[pos:pos + sizes[o]]
        pos += sizes[o]
        s.concealed_ids[o] = ids
        counts = [0] * 34
        for iid in ids:
            counts[STANDARD_INSTANCES[iid].tile_type] += 1
            s.locations[iid] = TileLocation.CONCEALED
        s.players[o].concealed = counts
    s.wall_order[s.wall_front:s.wall_rear] = wall_new
    for iid in wall_new:
        s.locations[iid] = TileLocation.LIVE_WALL
    return s


def collect_points(profile: RulesProfile, table_id: str, count: int, seed: int = 1) -> List[Tuple[GameState, int, int, int]]:
    """Real decision points: (state, actor, deal index, seq). Games are played by three reference bots."""
    rng = Rng(seed)
    players = [make_player("ref:" + name, table_id, profile)
               for name in ("ukeire", "faan_aware", "random", "ukeire")]
    points: List[Tuple[GameState, int, int, int]] = []
    index = 0
    while len(points) < count:
        deal_seed = FAIRPLAY_SEED_START + index
        state = GameState.new_game(profile, seed=deal_seed, dealer=dealer_for_index(index),
                                   prevailing_wind=wind_for_index(index))
        seq = 0
        per_game = 0
        while not state.is_terminal() and len(points) < count:
            actor = state.current_actor()
            assert isinstance(actor, int)
            msg = build_view(state, actor, game_id="fairplay", seq=seq,
                             rng_seed=decision_seed(deal_seed, 0, seq), table_id=table_id)
            # Skip forced moves and keep the sample spread over the game: about one point in eight.
            if len(msg["legal"]) >= 2 and rng.randrange(8) == 0 and per_game < 12:
                points.append((state.clone(), actor, index, seq))
                per_game += 1
            action, _ = players[actor].decide(msg)
            state.apply_action(action)
            seq += 1
        index += 1
    return points


def check(
    table,
    bot_spec: str,
    *,
    points: int = DEFAULT_POINTS,
    reshuffles: int = DEFAULT_RESHUFFLES,
    on_decision: Optional[Hook] = None,
    decision_timeout_s: Optional[float] = None,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the check on one bot. ``on_decision`` is a test hook called before every ask."""
    profile = table.profile
    pts = collect_points(profile, table.id, points)
    player: Player = make_player(bot_spec, table.id, profile,
                                 decision_timeout_s=decision_timeout_s or table.decision_timeout_s, cwd=cwd)
    rng = Rng(7)
    report: Dict[str, Any] = {
        "points": len(pts), "reshuffles": reshuffles, "asks": 0,
        "view_mismatches": 0, "decision_changes": 0, "faults": 0, "examples": [],
    }
    try:
        for state, actor, index, seq in pts:
            deal_seed = FAIRPLAY_SEED_START + index
            base = build_view(state, actor, game_id="fairplay", seq=seq,
                              rng_seed=decision_seed(deal_seed, 0, seq), table_id=table.id)
            if on_decision is not None:
                on_decision(state, actor, base)
            first, fault = player.decide(base)
            report["asks"] += 1
            report["faults"] += 1 if fault else 0
            for _ in range(reshuffles):
                variant = reshuffle_hidden(state, actor, rng)
                msg = build_view(variant, actor, game_id="fairplay", seq=seq,
                                 rng_seed=decision_seed(deal_seed, 0, seq), table_id=table.id)
                if msg != base:
                    report["view_mismatches"] += 1
                    if len(report["examples"]) < 3:
                        report["examples"].append({"kind": "view", "deal": index, "seq": seq})
                if on_decision is not None:
                    on_decision(variant, actor, msg)
                again, fault = player.decide(msg)
                report["asks"] += 1
                report["faults"] += 1 if fault else 0
                if again != first:
                    report["decision_changes"] += 1
                    if len(report["examples"]) < 3:
                        report["examples"].append({"kind": "decision", "deal": index, "seq": seq,
                                                   "before": first, "after": again})
    finally:
        player.close()
    report["passed"] = (report["view_mismatches"] == 0 and report["decision_changes"] == 0
                        and report["faults"] == 0)
    return report
