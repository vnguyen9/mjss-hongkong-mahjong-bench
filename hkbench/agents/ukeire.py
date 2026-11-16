"""Speed bots that count tiles. Discard the tile that leaves the hand closest to winning.

``UkeireBot`` breaks ties by how many live tiles would improve the hand. ``DeficiencyBot``
only looks at distance to a complete hand. Both take a win when they can. When the choice is
a claim (pong, kong, chow or pass) they pick at random from the legal actions.
"""

from __future__ import annotations

from typing import List

from hkbench.agents.shanten import deficiency, ukeire
from hkbench.seeds import Rng
from hkbench.view import SeatView


def _after_discard(concealed: List[int], t: int) -> List[int]:
    c = concealed.copy()
    c[t] -= 1
    return c


class DeficiencyBot:
    name = "deficiency"

    def __init__(self, profile) -> None:
        self.profile = profile

    def decide(self, view: SeatView) -> int:
        legal = view.legal
        if 1 in legal:
            return 1
        discards = [a for a in legal if 2 <= a <= 35]
        if not discards:
            return Rng(view.rng_seed).choice(legal)
        best_a, best_d = discards[0], 99
        for a in discards:
            d = deficiency(_after_discard(view.hand, a - 2), view.melds)
            if d < best_d:
                best_d = d
                best_a = a
        return best_a


class UkeireBot:
    name = "ukeire"

    def __init__(self, profile) -> None:
        self.profile = profile

    def decide(self, view: SeatView) -> int:
        legal = view.legal
        if 1 in legal:
            return 1
        discards = [a for a in legal if 2 <= a <= 35]
        if not discards:
            return Rng(view.rng_seed).choice(legal)
        best_a, best_key = discards[0], None
        for a in discards:
            c = _after_discard(view.hand, a - 2)
            d = deficiency(c, view.melds)
            u, _ = ukeire(c, view.melds, view.unseen)
            key = (-d, u)
            if best_key is None or key > best_key:
                best_key = key
                best_a = a
        return best_a
