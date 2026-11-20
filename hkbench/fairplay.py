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
from hkbench import runkey
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


def _seeds(run_key: bytes, table_id: str, index: int, seq: int) -> Dict[str, Any]:
    """The game_id and rng_seed a position carries, made exactly as a real game makes them."""
    return {"game_id": runkey.game_id(run_key, table_id, index, runkey.FAIRPLAY_ARRANGEMENT),
            "rng_seed": runkey.decision_seed(run_key, table_id, index, runkey.FAIRPLAY_ARRANGEMENT, seq)}


def _collect(profile: RulesProfile, table_id: str, count: int, seed: int, run_key: bytes):
    """Decision points with their history: (state, actor, deal index, seq, the actor's earlier messages)."""
    rng = Rng(seed)
    players = [make_player("ref:" + name, table_id, profile)
               for name in ("ukeire", "faan_aware", "random", "ukeire")]
    points = []
    index = 0
    while len(points) < count:
        deal_seed = FAIRPLAY_SEED_START + index
        state = GameState.new_game(profile, seed=deal_seed, dealer=dealer_for_index(index),
                                   prevailing_wind=wind_for_index(index))
        seq = 0
        per_game = 0
        seen: List[List[Dict[str, Any]]] = [[], [], [], []]
        while not state.is_terminal() and len(points) < count:
            actor = state.current_actor()
            assert isinstance(actor, int)
            msg = build_view(state, actor, seq=seq, table_id=table_id, **_seeds(run_key, table_id, index, seq))
            # Skip forced moves and keep the sample spread over the game: about one point in eight.
            if len(msg["legal"]) >= 2 and rng.randrange(8) == 0 and per_game < 12:
                points.append((state.clone(), actor, index, seq, list(seen[actor])))
                per_game += 1
            seen[actor].append(msg)
            action, _ = players[actor].decide(msg)
            state.apply_action(action)
            seq += 1
        index += 1
    return points


def collect_points(profile: RulesProfile, table_id: str, count: int, seed: int = 1,
                   run_key: bytes = runkey.PUBLIC_RUN_KEY) -> List[Tuple[GameState, int, int, int]]:
    """Real decision points: (state, actor, deal index, seq). Games are played by three reference bots."""
    return [p[:4] for p in _collect(profile, table_id, count, seed, run_key)]


def check(
    table,
    bot_spec: str,
    *,
    points: int = DEFAULT_POINTS,
    reshuffles: int = DEFAULT_RESHUFFLES,
    on_decision: Optional[Hook] = None,
    decision_timeout_s: Optional[float] = None,
    cwd: Optional[str] = None,
    run_key: bytes = runkey.PUBLIC_RUN_KEY,
    bot_env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Run the check on one bot. ``on_decision`` is a test hook called before every ask.

    The positions carry a ``game_id`` and ``rng_seed`` made with the run's key, the way a real game's
    are, so a bot cannot tell it is being checked. Every ask goes to a fresh process, as every game
    does, and that process is first shown the seat's earlier decisions in the game (its answers to
    those do not count), so it starts the way a real game's process starts and sees no position twice.
    """
    profile = table.profile
    pts = _collect(profile, table.id, points, 1, run_key)
    timeout = decision_timeout_s or table.decision_timeout_s

    def ask(msg: Dict[str, Any], history: List[Dict[str, Any]]) -> Tuple[int, Optional[str]]:
        player: Player = make_player(bot_spec, table.id, profile, decision_timeout_s=timeout, cwd=cwd, env=bot_env)
        try:
            for earlier in history:
                player.decide(earlier)
            return player.decide(msg)
        finally:
            player.close()

    rng = Rng(7)
    report: Dict[str, Any] = {
        "points": len(pts), "reshuffles": reshuffles, "asks": 0,
        "view_mismatches": 0, "decision_changes": 0, "faults": 0, "examples": [],
    }
    for state, actor, index, seq, history in pts:
        ids = _seeds(run_key, table.id, index, seq)
        base = build_view(state, actor, seq=seq, table_id=table.id, **ids)
        if on_decision is not None:
            on_decision(state, actor, base)
        first, fault = ask(base, history)
        report["asks"] += 1
        report["faults"] += 1 if fault else 0
        for _ in range(reshuffles):
            variant = reshuffle_hidden(state, actor, rng)
            msg = build_view(variant, actor, seq=seq, table_id=table.id, **ids)
            if msg != base:
                report["view_mismatches"] += 1
                if len(report["examples"]) < 3:
                    report["examples"].append({"kind": "view", "deal": index, "seq": seq})
            if on_decision is not None:
                on_decision(variant, actor, msg)
            again, fault = ask(msg, history)
            report["asks"] += 1
            report["faults"] += 1 if fault else 0
            if again != first:
                report["decision_changes"] += 1
                if len(report["examples"]) < 3:
                    report["examples"].append({"kind": "decision", "deal": index, "seq": seq,
                                               "before": first, "after": again})
    report["passed"] = (report["view_mismatches"] == 0 and report["decision_changes"] == 0
                        and report["faults"] == 0)
    return report
