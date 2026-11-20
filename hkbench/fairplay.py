"""The fair-play check: does a bot's choice depend on tiles it cannot see?

Before a bot is scored, the bench plays it in real games against the table's field, on deals drawn
from a secret made for this check alone (never a known range, never a public deal). At chosen
decisions it re-shuffles every hidden tile (the other three concealed hands and the live wall) into a
new arrangement that looks identical to the seat, and asks the bot again, in a fresh process that has
first been sent that seat's earlier messages of the game. Four things are checked:

1. The view the bench builds is identical for every arrangement. If it is not, the bench leaks.
2. The bot gives the same answer to the identical view every time.
3. The bot gives the same answer to each earlier message of the game as it did when it played it.
4. The bot gives a legal, on-time answer.

Any changed answer rejects the bot. Because the protocol only carries the seat view, a bot that
plays honestly can only fail this by being random without using ``rng_seed``, or by keeping state
that changes its answer. A bot that reads the hidden state some other way (a shared file, the
bench's memory, a network service) is caught when the answers move with the hidden tiles.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import struct
import time
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

from hkbench.engine.game import GameState
from hkbench.engine.profile import RulesProfile
from hkbench.engine.tile_instance import STANDARD_INSTANCES, TileLocation
from hkbench.players import Player, make_player
from hkbench import runkey
from hkbench.seeds import Rng, dealer_for_index, wind_for_index
from hkbench.view import build_view

#: ``hkbench fairplay --debug-fixed-check`` uses this secret. It makes the check's deals the same every time, so
#: a bot could recognise them: for reproducing a result only, never used when a bot is scored.
DEBUG_CHECK_SECRET = hashlib.sha256(b"hkbench-fairplay-debug-check").digest()
DEFAULT_POINTS = 100
DEFAULT_RESHUFFLES = 2

# The clock and the pause the replay uses; tests swap them.
_now = time.monotonic
_sleep = time.sleep
#: A recorded pause longer than this is not repeated (a pause that long is the bot's or the machine's, not the bench's).
MAX_REPLAY_GAP_S = 2.0

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


def public_ranges(tables_dir) -> List[Tuple[int, int]]:
    from hkbench.tables import list_tables

    out = []
    for t in list_tables(tables_dir):
        r = t.public_range
        out.append((r["start"], r["start"] + r["count"]))
    return out


def check_deal_seed(secret: bytes, index: int, ranges: List[Tuple[int, int]]) -> int:
    """The seed of the check's ``index``-th deal: 64 bits from ``secret``, outside every public range."""
    attempt = 0
    while True:
        digest = hmac.new(secret, b"hkbench-check-deal" + struct.pack(">QI", index, attempt), hashlib.sha256).digest()
        seed = int.from_bytes(digest[:8], "big")
        if not any(lo <= seed < hi for lo, hi in ranges):
            return seed
        attempt += 1


def _check_rng(secret: bytes) -> Rng:
    return Rng(int.from_bytes(hmac.new(secret, b"hkbench-check-rng", hashlib.sha256).digest()[:8], "big"))


def _seeds(run_key: bytes, table_id: str, index: int, seq: int) -> Dict[str, Any]:
    """The game_id and rng_seed a position carries, made exactly as a real game makes them."""
    return {"game_id": runkey.game_id(run_key, table_id, index, runkey.FAIRPLAY_ARRANGEMENT),
            "rng_seed": runkey.decision_seed(run_key, table_id, index, runkey.FAIRPLAY_ARRANGEMENT, seq)}


def collect_points(profile: RulesProfile, table_id: str, count: int, seed: int = 1,
                   run_key: bytes = runkey.PUBLIC_RUN_KEY) -> List[Tuple[GameState, int, int, int]]:
    """Decision points from games of reference bots: (state, actor, deal index, seq). For tests of the reshuffle.

    ``check`` does not use this: it plays the bot being checked.
    """
    rng = Rng(seed)
    secret = struct.pack(">Q", seed)
    players = [make_player("ref:" + name, table_id, profile)
               for name in ("ukeire", "faan_aware", "random", "ukeire")]
    points: List[Tuple[GameState, int, int, int]] = []
    index = 0
    while len(points) < count:
        state = GameState.new_game(profile, seed=check_deal_seed(secret, index, []), dealer=dealer_for_index(index),
                                   prevailing_wind=wind_for_index(index))
        seq = 0
        per_game = 0
        while not state.is_terminal() and len(points) < count:
            actor = state.current_actor()
            assert isinstance(actor, int)
            msg = build_view(state, actor, seq=seq, table_id=table_id, **_seeds(run_key, table_id, index, seq))
            if len(msg["legal"]) >= 2 and rng.randrange(8) == 0 and per_game < 12:
                points.append((state.clone(), actor, index, seq))
                per_game += 1
            action, _ = players[actor].decide(msg)
            state.apply_action(action)
            seq += 1
        index += 1
    return points


class Point(NamedTuple):
    """A decision the bot made in a live check game, and what it takes to ask it again."""
    state: GameState
    actor: int
    index: int
    seq: int
    history: List[Tuple[Dict[str, Any], int, float]]  # the seat's earlier messages, the moves it played, the pause before each
    msg: Dict[str, Any]
    action: int
    gap: float  # the pause before this message, as in the history


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
    check_secret: Optional[bytes] = None,
    sandbox: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the check on one bot. ``on_decision`` is a test hook called before every ask.

    The bot plays real games in one seat against the table's field, in a fresh process, on deals
    drawn from ``check_secret`` (32 fresh random bytes unless given; a given one makes the deals
    recognisable, so only a debugging run passes one). Its own answers drive each game. At the chosen
    decisions every hidden tile is dealt again and the bot is asked again in a fresh process, after that
    process has been sent the seat's earlier messages of the game: the answers it gives to those must be the
    ones it played, and its answer to the position must be unchanged. The positions carry a ``game_id`` and
    ``rng_seed`` made with the run's key, as a real game's do.
    """
    profile = table.profile
    timeout = decision_timeout_s or table.decision_timeout_s
    secret = check_secret or os.urandom(32)
    ranges = public_ranges(table.dir.parent)
    rng = _check_rng(secret)
    field = [make_player("ref:" + m["bot"], table.id, profile) for m in table.field]
    report: Dict[str, Any] = {
        "points": 0, "reshuffles": reshuffles, "asks": 0,
        "view_mismatches": 0, "decision_changes": 0, "faults": 0, "examples": [],
    }

    def new_bot() -> Player:
        return make_player(bot_spec, table.id, profile, decision_timeout_s=timeout, cwd=cwd, env=bot_env, sandbox=sandbox)

    def note(example: Dict[str, Any]) -> None:
        if len(report["examples"]) < 3:
            report["examples"].append(example)

    # 1. Play the bot, and keep the decisions to ask again.
    chosen: List[Point] = []
    index = 0
    while len(chosen) < points:
        # Dealer and wind step every four games, the checked seat every game, so the bot sits at every
        # position relative to the dealer (as scoring rotates it) and plays dealer, South, West and North evenly.
        deal_no, rot = divmod(index, 4)
        state = GameState.new_game(profile, seed=check_deal_seed(secret, index, ranges),
                                   dealer=dealer_for_index(deal_no), prevailing_wind=wind_for_index(deal_no))
        bot = new_bot()
        seats: List[Player] = [bot] * 4
        for i in range(3):
            seats[(rot + 1 + i) % 4] = field[i]
        seq = 0
        per_game = 0
        history: List[Tuple[Dict[str, Any], int, float]] = []
        answered_at: Optional[float] = None  # when the bot last answered: the pause before its next message
        try:
            while not state.is_terminal() and len(chosen) < points:
                actor = state.current_actor()
                assert isinstance(actor, int)
                msg = build_view(state, actor, seq=seq, table_id=table.id, **_seeds(run_key, table.id, index, seq))
                if actor == rot and on_decision is not None:
                    on_decision(state, actor, msg)
                sent_at = _now() if actor == rot else 0.0
                action, fault = seats[actor].decide(msg)
                if actor == rot:
                    gap = 0.0 if answered_at is None else max(0.0, sent_at - answered_at)
                    answered_at = _now()
                    report["faults"] += 1 if fault else 0
                    if len(msg["legal"]) >= 2 and rng.randrange(8) == 0 and per_game < 12:
                        chosen.append(Point(state.clone(), actor, index, seq, list(history), msg, action, gap))
                        per_game += 1
                    history.append((msg, action, gap))
                state.apply_action(action)
                seq += 1
        finally:
            bot.close()
        index += 1
    report["points"] = len(chosen)

    # 2. Ask again where the hidden tiles are dealt differently, each time in a fresh process.
    def ask(msg: Dict[str, Any], history: List[Tuple[Dict[str, Any], int, float]], gap: float):
        bot = new_bot()
        replay_changes = faults = 0
        try:
            # The replay waits as long as the game did between each answer and the next message, so
            # the bot cannot tell it by how fast the messages come.
            for earlier, played, before in history:
                _sleep(min(before, MAX_REPLAY_GAP_S))
                answer, fault = bot.decide(earlier)
                faults += 1 if fault else 0
                replay_changes += 1 if answer != played else 0
            _sleep(min(gap, MAX_REPLAY_GAP_S))
            answer, fault = bot.decide(msg)
            return answer, faults + (1 if fault else 0), replay_changes
        finally:
            bot.close()

    report["asks"] += len(chosen)  # the answers given while playing
    for pt in chosen:
        base = pt.msg
        for _ in range(reshuffles):
            variant = reshuffle_hidden(pt.state, pt.actor, rng)
            msg = build_view(variant, pt.actor, seq=pt.seq, table_id=table.id, game_id=base["game_id"],
                             rng_seed=base["rng_seed"])
            if msg != base:
                report["view_mismatches"] += 1
                note({"kind": "view", "deal": pt.index, "seq": pt.seq})
            if on_decision is not None:
                on_decision(variant, pt.actor, msg)
            again, faults, replay_changes = ask(msg, pt.history, pt.gap)
            report["asks"] += 1
            report["faults"] += faults
            if replay_changes:
                report["decision_changes"] += replay_changes
                note({"kind": "replay", "deal": pt.index, "seq": pt.seq, "changed": replay_changes})
            if again != pt.action:
                report["decision_changes"] += 1
                note({"kind": "decision", "deal": pt.index, "seq": pt.seq, "before": pt.action, "after": again})
    report["passed"] = (report["view_mismatches"] == 0 and report["decision_changes"] == 0
                        and report["faults"] == 0)
    return report
