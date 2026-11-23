"""The engine fingerprint.

Before a table scores anything, the engine plays a fixed set of deals and scores a fixed set of
hands. A hash of every outcome must match the one pinned in ``tables/<id>/fingerprint.json``. If
the rules, the engine, or the deal shuffle changed in any way that matters, it will not match,
and scoring refuses to run.

The deals are played by a policy that needs nothing but the engine (see ``_choose``), with every
choice drawn from a hash of the deal's seed and the step number.
The hands are the scoring corpus (``tests/fixtures/hands.json``) plus
the limit hands, scored under the table's rules.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from hkbench.engine.game import GameState
from hkbench.engine.profile import RulesProfile
from hkbench.engine.payment import table_payments
from hkbench.engine.scorer import score_hand
from hkbench.engine.tiles import BONUS_NAMES, parse_tile
from hkbench.engine.types import Meld, MeldKind, PlayerState, WinSource
from hkbench.seeds import dealer_for_index, wind_for_index

FINGERPRINT_VERSION = 1
FINGERPRINT_DEALS = 300
FINGERPRINT_SEED_START = 9_000_000_000
HANDS_FILE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "hands.json"


def _pick(seed: int, step: int, n: int) -> int:
    digest = hashlib.sha256(("%d:%d" % (seed, step)).encode()).digest()
    return int.from_bytes(digest[:4], "big") % n


def _choose(state: GameState, actor: int, seed: int, step: int) -> int:
    """A policy that needs only the engine, and still finishes hands now and then.

    Win when legal. On a claim: take a pong or kong half the time, a chow a quarter of the
    time. On a turn: sometimes declare a kong, otherwise throw a tile that is part of the
    fewest copies in hand (ties broken by the hash), so hands grow pairs and triplets.
    """
    legal = state.legal_actions(actor)
    if 1 in legal:
        return 1
    if state.phase.name == "REACTION":
        claims = [a for a in legal if a >= 36]
        if claims and _pick(seed, step, 4) < 2:
            pongs = [a for a in claims if a in (57, 58)]
            return pongs[0] if pongs else claims[_pick(seed, step + 7, len(claims))]
        return 0
    kongs = [a for a in legal if a >= 59]
    if kongs and _pick(seed, step, 2) == 0:
        return kongs[0]
    hand = state.players[actor].concealed
    discards = [a for a in legal if 2 <= a <= 35]
    fewest = min(hand[a - 2] for a in discards)
    pool = [a for a in discards if hand[a - 2] == fewest]
    return pool[_pick(seed, step, len(pool))]


def play_fingerprint_deal(profile: RulesProfile, index: int) -> Dict[str, Any]:
    seed = FINGERPRINT_SEED_START + index
    state = GameState.new_game(profile, seed=seed, dealer=dealer_for_index(index),
                               prevailing_wind=wind_for_index(index))
    step = 0
    while not state.is_terminal():
        actor = state.current_actor()
        assert isinstance(actor, int)
        state.apply_action(_choose(state, actor, seed, step))
        step += 1
    r = state.terminal
    assert r is not None
    return {
        "seed": seed,
        "steps": step,
        "cause": r.cause,
        "winner": r.winner,
        "discarder": r.discarder,
        "faan": r.faan,
        "payments": list(r.payments),
        "patterns": [[p["name"], p["faan"]] for p in r.pattern_breakdown],
        "wall_remaining": state.wall_remaining(),
        "flowers": [len(p.flowers) for p in state.players],
        "melds": [len(p.melds) for p in state.players],
    }


def _hand_player(case: Dict[str, Any]):
    concealed = [0] * 34
    for tok in case["concealed"]:
        concealed[parse_tile(tok)] += 1
    melds = []
    for m in case.get("melds", []):
        tiles = tuple(parse_tile(t) for t in m["tiles"])
        melds.append(Meld(MeldKind[m["kind"]], tiles, m.get("from_seat"),
                          parse_tile(m["claimed_tile"]) if m.get("claimed_tile") else None))
    flowers = [BONUS_NAMES.index(t) for t in case.get("flowers", [])]
    return PlayerState(concealed=concealed, melds=melds, flowers=flowers, seat=0)


def score_corpus_hand(profile: RulesProfile, case: Dict[str, Any]) -> Dict[str, Any]:
    player = _hand_player(case)
    res = score_hand(
        player, None, WinSource[case["win_source"]],
        seat_wind=case["seat_wind"], prevailing_wind=case["prevailing_wind"],
        discarder=case.get("discarder"),
        last_tile=case.get("last_tile", False), after_kong=case.get("after_kong", False),
        after_double_kong=case.get("after_double_kong", False),
        heavenly=case.get("heavenly", False), earthly=case.get("earthly", False),
        profile=profile,
    )
    return {
        "id": case["id"],
        "patterns": [[p.name, p.faan] for p in res.patterns],
        "total": res.total_faan,
        "faan": res.capped_faan,
        "ok": res.meets_minimum,
        "limit": res.is_limit,
        "payments": table_payments(res.payments, WinSource[case["win_source"]], res.winner, profile),
    }


def compute(profile: RulesProfile, deals: int = FINGERPRINT_DEALS) -> Dict[str, Any]:
    games = [play_fingerprint_deal(profile, i) for i in range(deals)]
    cases = json.loads(HANDS_FILE.read_text(encoding="utf-8"))["cases"]
    hands = [score_corpus_hand(profile, c) for c in cases]
    blob = json.dumps({"games": games, "hands": hands}, sort_keys=True, separators=(",", ":"))
    return {
        "fingerprint_version": FINGERPRINT_VERSION,
        "rules_sha256": profile.rules_sha256,
        "deals": deals,
        "hands": len(hands),
        "wins": sum(1 for g in games if g["cause"] == "win"),
        "sha256": hashlib.sha256(blob.encode()).hexdigest(),
    }


class FingerprintMismatch(RuntimeError):
    pass


def verify(table) -> Dict[str, Any]:
    """Recompute the table's fingerprint and compare it to the pinned one."""
    pinned = table.pinned_fingerprint()
    now = compute(table.profile, pinned["deals"])
    if now["sha256"] != pinned["sha256"] or now["rules_sha256"] != pinned["rules_sha256"]:
        raise FingerprintMismatch(
            "engine fingerprint for %s does not match (pinned %s, got %s). "
            "The engine or the rules changed; scoring will not run." % (table.id, pinned["sha256"][:12], now["sha256"][:12])
        )
    return now
