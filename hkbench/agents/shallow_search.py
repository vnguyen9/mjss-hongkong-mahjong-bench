"""One-ply expectimax over the unseen tiles.

For each discard it averages, over a sample of up to 20 draw types (weighted by how many of
each are unseen), the best follow-up discard. The sample is drawn from the decision's
``rng_seed``, so the same view always gets the same answer.
"""

from __future__ import annotations

from typing import Any, List

from hkbench.agents.shanten import deficiency, ukeire
from hkbench.seeds import Rng
from hkbench.view import SeatView


def _after_discard(concealed: List[int], tile: int) -> List[int]:
    c = concealed.copy()
    c[tile] -= 1
    return c


def _dec_remaining(remaining: List[int], tile: int) -> List[int]:
    r = remaining.copy()
    r[tile] = max(0, r[tile] - 1)
    return r


class ShallowSearchBot:
    name = "shallow_search"

    def __init__(self, profile, max_draw_types: int = 20) -> None:
        self.profile = profile
        self.max_draw_types = max_draw_types

    def decide(self, view: SeatView) -> int:
        legal = view.legal
        if 1 in legal:
            return 1
        discards = [a for a in legal if 2 <= a <= 35]
        rng = Rng(view.rng_seed)
        if not discards:
            return rng.choice(legal)

        remaining = list(view.unseen)
        draw_types = self._sample_draw_types(remaining, rng)

        best_action = discards[0]
        best_value = float("-inf")
        for action in discards:
            concealed = _after_discard(view.hand, action - 2)
            value = self._discard_value(concealed, view.melds, remaining, draw_types)
            if value > best_value:
                best_value = value
                best_action = action
        return best_action

    def _sample_draw_types(self, remaining: List[int], rng: Rng) -> List[int]:
        live = [tile for tile, count in enumerate(remaining) if count > 0]
        if len(live) <= self.max_draw_types:
            return live
        selected = set()
        total = sum(remaining)
        while len(selected) < self.max_draw_types and total > 0:
            pick = rng.randrange(total)
            acc = 0
            for tile, count in enumerate(remaining):
                if count <= 0:
                    continue
                acc += count
                if pick < acc:
                    selected.add(tile)
                    break
        return sorted(selected)

    def _discard_value(self, concealed13: List[int], melds: Any, remaining: List[int],
                       draw_types: List[int]) -> float:
        d = deficiency(concealed13, melds)
        u, _ = ukeire(concealed13, melds, remaining)
        immediate = -float(d) + 0.01 * float(u)
        if not draw_types:
            return immediate
        weight_total = sum(remaining[tile] for tile in draw_types) or 1
        expected = 0.0
        for draw in draw_types:
            weight = remaining[draw]
            if weight <= 0:
                continue
            after_draw = concealed13.copy()
            after_draw[draw] += 1
            expected += weight * self._best_after_draw(after_draw, melds, _dec_remaining(remaining, draw))
        return immediate + expected / weight_total

    def _best_after_draw(self, concealed14: List[int], melds: Any, remaining: List[int]) -> float:
        best = float("-inf")
        for discard in range(34):
            if concealed14[discard] <= 0:
                continue
            concealed13 = _after_discard(concealed14, discard)
            d = deficiency(concealed13, melds)
            u, _ = ukeire(concealed13, melds, remaining)
            best = max(best, -float(d) + 0.01 * float(u))
        return best
