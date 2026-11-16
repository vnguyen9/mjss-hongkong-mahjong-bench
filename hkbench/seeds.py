"""Deals from seeds.

A seed makes a wall, and nothing else. The shuffle is the bench's own (SplitMix64 feeding a
Fisher-Yates shuffle), not Python's ``random``, so the same seed is the same deal on every
Python version and could be rebuilt in any language.

A deal also needs a dealer and a prevailing wind. Those come from the deal's index in its
deck: ``dealer = index % 4`` and ``prevailing_wind = (index // 4) % 4``.
"""

from __future__ import annotations

from typing import List

_MASK = (1 << 64) - 1


def splitmix64(state: int) -> "tuple[int, int]":
    """One SplitMix64 step. Returns (next_state, output)."""
    state = (state + 0x9E3779B97F4A7C15) & _MASK
    z = state
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
    return state, z ^ (z >> 31)


def wall_for_seed(seed: int) -> List[int]:
    """The 144 tile instance ids in wall order for ``seed``."""
    state = seed & _MASK
    wall = list(range(144))
    for i in range(143, 0, -1):
        state, out = splitmix64(state)
        j = out % (i + 1)
        wall[i], wall[j] = wall[j], wall[i]
    return wall


def dealer_for_index(index: int) -> int:
    return index % 4


def wind_for_index(index: int) -> int:
    return (index // 4) % 4


class Rng:
    """A tiny deterministic generator (SplitMix64), used by the reference bots.

    Python's ``random`` is allowed to change between versions. This is not.
    """

    def __init__(self, seed: int) -> None:
        self._state = seed & _MASK

    def next_u64(self) -> int:
        self._state, out = splitmix64(self._state)
        return out

    def randrange(self, n: int) -> int:
        if n <= 0:
            raise ValueError("randrange needs n > 0")
        return self.next_u64() % n

    def choice(self, seq):
        return seq[self.randrange(len(seq))]
