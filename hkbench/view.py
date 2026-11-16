"""What a seat is allowed to see.

``build_view`` turns the engine's full state into the message a bot receives. It reads only
what a player at a real table could see: their own concealed tiles, every discard, every
shown meld and flower, the wind and dealer, how many tiles are left in the wall, and their
own legal actions. It never reads another seat's concealed tiles or the wall's order.

Players are numbered relative to the viewer: 0 is you, 1 plays after you, 2 sits across,
3 plays just before you. ``from`` fields use the same numbering.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hkbench.engine.actions import CHOW_PATTERNS, ActionKind, action_from_id
from hkbench.engine.game import GameState
from hkbench.engine.tile_instance import STANDARD_INSTANCES
from hkbench.engine.types import Meld, MeldKind, Phase

PROTOCOL = "hkbench-1"

_DRAW_KINDS = {"ordinary": "wall", "flower_replacement": "flower_replacement",
               "kong_replacement": "kong_replacement"}


def describe_action(action_id: int) -> Dict[str, Any]:
    """One legal action as the protocol shows it."""
    a = action_from_id(action_id)
    d: Dict[str, Any] = {"id": a.action_id, "kind": a.kind.name.lower()}
    if a.kind in (ActionKind.DISCARD, ActionKind.CONCEALED_KONG, ActionKind.ADDED_KONG):
        d["tile"] = a.tile
    elif a.kind == ActionKind.CHOW:
        d["tiles"] = list(CHOW_PATTERNS[a.chow_index or 0])
    return d


def _meld_dict(m: Meld, viewer: int, owner: int) -> Dict[str, Any]:
    d: Dict[str, Any] = {"kind": m.kind.name.lower(), "tiles": list(m.tiles)}
    d["from"] = None if m.from_seat is None else (m.from_seat - viewer) % 4
    return d


def build_view(
    state: GameState,
    seat: int,
    *,
    game_id: str,
    seq: int,
    rng_seed: int,
    table_id: str,
) -> Dict[str, Any]:
    """The ``decide`` message for ``seat`` at the current decision."""
    if state.phase not in (Phase.SELF_ACTION, Phase.REACTION):
        raise ValueError("no decision to show")
    me = state.players[seat]
    rel = [(seat + i) % 4 for i in range(4)]

    river_ids = [set(state.river[s]) for s in range(4)]
    discards: List[Dict[str, Any]] = []
    for (hist_seat, tile), iid in zip(state.discard_history, state.discard_instances):
        discards.append(
            {"p": (hist_seat - seat) % 4, "tile": tile, "claimed": iid not in river_ids[hist_seat]}
        )

    # Everything on the table that this seat can count: melds and the tiles still in rivers.
    visible = [0] * 34
    for s in range(4):
        for m in state.players[s].melds:
            if m.kind == MeldKind.CHOW:
                for t in m.tiles:
                    visible[t] += 1
            else:
                visible[m.tiles[0]] += 4 if m.is_kong() else 3
        for iid in state.river[s]:
            visible[STANDARD_INSTANCES[iid].tile_type] += 1
    unseen = [max(0, 4 - me.concealed[t] - visible[t]) for t in range(34)]

    others = []
    for p in range(1, 4):
        s = rel[p]
        pl = state.players[s]
        others.append(
            {
                "p": p,
                "seat_wind": pl.seat,
                "hand_size": pl.concealed_count(),
                "melds": [_meld_dict(m, seat, s) for m in pl.melds],
                "flowers": list(pl.flowers),
            }
        )

    phase = "turn" if state.phase == Phase.SELF_ACTION else "claim"
    drawn = state.last_draw if (phase == "turn" and state.current_player == seat) else None
    draw_kind = None
    if drawn is not None and state.last_draw_kind is not None:
        draw_kind = _DRAW_KINDS[state.last_draw_kind.value]

    offer: Optional[Dict[str, Any]] = None
    if phase == "claim" and state.offer is not None:
        offer = {
            "tile": state.offer.tile,
            "from": (state.offer.from_seat - seat) % 4,
            "kind": "added_kong" if state.offer.rob_kong else "discard",
        }

    return {
        "protocol": PROTOCOL,
        "type": "decide",
        "table": table_id,
        "game_id": game_id,
        "seq": seq,
        "rng_seed": rng_seed,
        "phase": phase,
        "prevailing_wind": state.prevailing_wind,
        "dealer": (state.dealer - seat) % 4,
        "wall_remaining": state.wall_remaining(),
        "you": {
            "seat_wind": me.seat,
            "hand": list(me.concealed),
            "drawn": drawn,
            "draw_kind": draw_kind,
            "melds": [_meld_dict(m, seat, seat) for m in me.melds],
            "flowers": list(me.flowers),
        },
        "others": others,
        "discards": discards,
        "offer": offer,
        "unseen": unseen,
        "legal": [describe_action(a) for a in state.legal_actions(seat)],
    }


class SeatView:
    """A ``decide`` message with typed accessors, for bots written in Python."""

    def __init__(self, msg: Dict[str, Any]) -> None:
        self.msg = msg
        you = msg["you"]
        self.seat_wind: int = you["seat_wind"]
        self.prevailing_wind: int = msg["prevailing_wind"]
        self.hand: List[int] = list(you["hand"])
        self.drawn: Optional[int] = you["drawn"]
        self.flowers: List[int] = list(you["flowers"])
        self.melds: List[Meld] = [
            Meld(MeldKind[m["kind"].upper()], tuple(m["tiles"]), m["from"], None)
            for m in you["melds"]
        ]
        self.unseen: List[int] = list(msg["unseen"])
        self.phase: str = msg["phase"]
        self.legal: List[int] = [a["id"] for a in msg["legal"]]
        self.offer_tile: Optional[int] = msg["offer"]["tile"] if msg["offer"] else None
        self.wall_remaining: int = msg["wall_remaining"]
        self.rng_seed: int = msg["rng_seed"]
