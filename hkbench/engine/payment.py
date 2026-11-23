"""What a table does with the payments the scorer settled.

The scorer settles every win the HKMA way: a discard win is paid in full by the discarder, a self-drawn win is
split between the three others. A table whose rules file says ``payments.discarder_pays: "equal"`` has the three
losers pay the same on a discard win too, so every win moves the table value three times over to the winner, one
share from each other seat. ``hk-chicken-v2`` is that table. Every other table keeps the scorer's payments as they are.
"""

from __future__ import annotations

from typing import List, Sequence

from hkbench.engine.profile import RulesProfile
from hkbench.engine.types import WinSource


def table_payments(payments: Sequence[int], win_source: WinSource, winner: int, profile: RulesProfile) -> List[int]:
    pay = list(payments)
    if profile.discarder_pays != "equal" or win_source in (WinSource.SELF_DRAW, WinSource.FLOWER_SEVEN, WinSource.FLOWER_EIGHT):
        return pay
    base = pay[winner]
    if base <= 0:
        return pay
    out = [-base] * 4
    out[winner] = 3 * base
    return out
