"""The random baseline: a uniform pick among the legal actions."""

from __future__ import annotations

from hkbench.seeds import Rng
from hkbench.view import SeatView


class RandomBot:
    name = "random"

    def __init__(self, profile) -> None:
        self.profile = profile

    def decide(self, view: SeatView) -> int:
        return Rng(view.rng_seed).choice(view.legal)
