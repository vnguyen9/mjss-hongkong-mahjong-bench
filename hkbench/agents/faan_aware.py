"""Faan-aware bot: ukeire speed, plus a push toward hands that reach the faan minimum.

It prefers waits that complete a scoring hand, keeps value tiles (dragons, its own wind and the
prevailing wind) and its main suit, and claims pongs and chows only when they fit.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from hkbench.agents.shanten import deficiency, ukeire
from hkbench.engine.scorer import can_declare_win, score_hand
from hkbench.engine.tiles import is_honor, suit_of
from hkbench.engine.types import MeldKind, PlayerState, WinSource
from hkbench.engine.win import waits
from hkbench.seeds import Rng
from hkbench.view import SeatView


def _after_discard(concealed: list[int], t: int) -> list[int]:
    c = concealed.copy()
    c[t] -= 1
    return c


def _value_tile_bonus(t: int, seat_wind: int, prevailing_wind: int) -> float:
    if 31 <= t <= 33:  # dragons
        return 3.0
    if 27 <= t <= 30:
        bonus = 0.0
        if t == 27 + seat_wind:
            bonus += 2.0
        if t == 27 + prevailing_wind:
            bonus += 2.0
        return bonus if bonus else 0.5
    return 0.0


def _suit_commitment(concealed: list[int], melds) -> tuple[int | None, float]:
    """Dominant suit among suited tiles; commitment score."""
    counts = [0, 0, 0]
    for t, n in enumerate(concealed):
        s = suit_of(t)
        if s is not None:
            counts[s] += n
    for m in melds:
        if m.kind == MeldKind.CHOW:
            s = suit_of(m.tiles[0])
            if s is not None:
                counts[s] += 3
        else:
            s = suit_of(m.tiles[0])
            if s is not None:
                counts[s] += 3
    total = sum(counts) or 1
    best = max(range(3), key=lambda i: counts[i])
    return best, counts[best] / total


def _pongish_ratio(concealed: list[int], melds) -> float:
    pairs_trips = sum(1 for n in concealed if n >= 2)
    open_pongs = sum(1 for m in melds if m.kind != MeldKind.CHOW)
    return pairs_trips + 1.5 * open_pongs


def _faan_ready_outs(
    concealed13: list[int],
    player: PlayerState,
    seat_wind: int,
    prevailing_wind: int,
    rem: list[int],
    profile: Any,
) -> tuple[int, float]:
    """Live outs that complete a scoring win under ``profile``, and the expected faan weight."""
    w = waits(concealed13, player.melds)
    live = 0
    exp_faan = 0.0
    for t in w:
        if rem[t] <= 0:
            continue
        c = concealed13.copy()
        c[t] += 1
        trial = PlayerState(
            concealed=c,
            melds=list(player.melds),
            flowers=list(player.flowers),
            seat=player.seat,
        )
        # Prefer self-draw scoring package for readiness
        if can_declare_win(
            trial,
            t,
            WinSource.SELF_DRAW,
            seat_wind=seat_wind,
            prevailing_wind=prevailing_wind,
            profile=profile,
        ):
            sc = score_hand(
                trial,
                t,
                WinSource.SELF_DRAW,
                seat_wind=seat_wind,
                prevailing_wind=prevailing_wind,
                profile=profile,
            )
            live += rem[t]
            exp_faan += rem[t] * sc.capped_faan
        elif can_declare_win(
            trial,
            t,
            WinSource.DISCARD,
            seat_wind=seat_wind,
            prevailing_wind=prevailing_wind,
            discarder=(player.seat + 3) % 4,
            profile=profile,
        ):
            sc = score_hand(
                trial,
                t,
                WinSource.DISCARD,
                seat_wind=seat_wind,
                prevailing_wind=prevailing_wind,
                discarder=(player.seat + 3) % 4,
                profile=profile,
            )
            live += rem[t]
            exp_faan += rem[t] * sc.capped_faan
    return live, exp_faan


def _keep_score(t: int, concealed: list[int], seat_wind: int, prevailing_wind: int, dom_suit: int | None) -> float:
    """How painful it is to discard tile t (higher = keep)."""
    score = _value_tile_bonus(t, seat_wind, prevailing_wind)
    n = concealed[t]
    if n >= 3:
        score += 4.0  # almost pong
    elif n == 2:
        score += 2.0
    s = suit_of(t)
    if dom_suit is not None and s == dom_suit:
        score += 1.5
    if s is not None and dom_suit is not None and s != dom_suit:
        score -= 1.0  # off-suit easier to pitch
    if is_honor(t) and _value_tile_bonus(t, seat_wind, prevailing_wind) == 0:
        score -= 0.5  # guest wind
    return score


class FaanAwareBot:
    name = "faan_aware"

    def __init__(self, profile) -> None:
        self.profile = profile

    def decide(self, view: SeatView) -> int:
        legal = view.legal
        if 1 in legal:
            return 1

        seat_wind = view.seat_wind
        prev = view.prevailing_wind

        if view.phase == "claim":
            return self._reaction(view, legal, seat_wind, prev)

        pl = PlayerState(concealed=list(view.hand), melds=list(view.melds),
                         flowers=list(view.flowers), seat=seat_wind)
        discards = [a for a in legal if 2 <= a <= 35]
        if not discards:
            # Only kongs are on offer: prefer the kong of a value tile.
            if any(59 <= a <= 126 for a in legal):
                best = None
                best_s = -1.0
                for a in legal:
                    if 59 <= a <= 92:
                        t = a - 59
                        s = _value_tile_bonus(t, seat_wind, prev)
                        if s > best_s:
                            best_s, best = s, a
                    elif 93 <= a <= 126:
                        t = a - 93
                        s = _value_tile_bonus(t, seat_wind, prev) + 1.0
                        if s > best_s:
                            best_s, best = s, a
                if best is not None:
                    return best
            return Rng(view.rng_seed).choice(legal)

        rem = view.unseen
        dom_suit, commit = _suit_commitment(pl.concealed, pl.melds)
        pongish = _pongish_ratio(pl.concealed, pl.melds)

        best_a = discards[0]
        best_key = None
        for a in discards:
            t = a - 2
            c = _after_discard(pl.concealed, t)
            d = deficiency(c, pl.melds)
            u, _ = ukeire(c, pl.melds, rem)
            # The expensive scan for scoring waits only runs near tenpai.
            if d <= 1:
                live_faan, exp_faan = _faan_ready_outs(c, pl, seat_wind, prev, rem, self.profile)
            else:
                live_faan, exp_faan = 0, 0.0
            keep = _keep_score(t, pl.concealed, seat_wind, prev, dom_suit)

            offsuit_bonus = 0.0
            st = suit_of(t)
            if commit >= 0.55 and st is not None and st != dom_suit:
                offsuit_bonus = 2.0
            if pongish >= 4 and st is not None:
                if pl.concealed[t] == 1:
                    offsuit_bonus += 0.5

            key = (
                -d,
                live_faan,
                exp_faan,
                u,
                offsuit_bonus - keep,
            )
            if best_key is None or key > best_key:
                best_key = key
                best_a = a
        return best_a

    def _reaction(self, view: SeatView, legal: List[int], seat_wind: int, prev: int) -> int:
        tile = view.offer_tile
        assert tile is not None
        hand = view.hand
        melds = view.melds
        if 58 in legal and _value_tile_bonus(tile, seat_wind, prev) >= 2.0:
            return 58
        if 57 in legal:
            dom, commit = _suit_commitment(hand, melds)
            val = _value_tile_bonus(tile, seat_wind, prev)
            st = suit_of(tile)
            if val >= 2.0:
                return 57
            if commit >= 0.5 and st == dom:
                return 57
            if _pongish_ratio(hand, melds) >= 4 and hand[tile] >= 2:
                return 57
        chows = [a for a in legal if 36 <= a <= 56]
        if chows:
            dom, commit = _suit_commitment(hand, melds)
            st = suit_of(tile)
            if commit >= 0.45 and st == dom and _pongish_ratio(hand, melds) < 5:
                return chows[0]
        if 0 in legal:
            return 0
        return Rng(view.rng_seed).choice(legal)
