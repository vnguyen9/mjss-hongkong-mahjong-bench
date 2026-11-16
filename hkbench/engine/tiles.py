"""Tile identity helpers.

Regular tiles 0..33:
  0-8   characters (man) 1-9
  9-17  bamboo (sou) 1-9
  18-26 dots (pin) 1-9
  27-30 winds E S W N
  31-33 dragons 中 發 白

Bonus tiles 0..7:
  0-3 flowers 梅蘭菊竹 (seat 1-4)
  4-7 seasons 春夏秋冬 (seat 1-4)
"""

from __future__ import annotations

from typing import Iterable

NUM_REGULAR = 34
NUM_BONUS = 8
COPIES = 4

MAN, SOU, PIN = 0, 9, 18
WINDS = range(27, 31)
DRAGONS = range(31, 34)
HONORS = range(27, 34)
TERMINALS = (0, 8, 9, 17, 18, 26)

TILE_NAMES = (
    [f"m{i}" for i in range(1, 10)]
    + [f"s{i}" for i in range(1, 10)]
    + [f"p{i}" for i in range(1, 10)]
    + ["E", "S", "W", "N", "C", "F", "P"]
)

BONUS_NAMES = ["Fl1", "Fl2", "Fl3", "Fl4", "Se1", "Se2", "Se3", "Se4"]


def tile_name(t: int) -> str:
    return TILE_NAMES[t]


def bonus_name(b: int) -> str:
    return BONUS_NAMES[b]


def is_suited(t: int) -> bool:
    return 0 <= t <= 26


def is_honor(t: int) -> bool:
    return 27 <= t <= 33


def is_terminal_or_honor(t: int) -> bool:
    return t in TERMINALS or is_honor(t)


def suit_of(t: int) -> int | None:
    if 0 <= t <= 8:
        return 0
    if 9 <= t <= 17:
        return 1
    if 18 <= t <= 26:
        return 2
    return None


def rank_of(t: int) -> int | None:
    if is_suited(t):
        return (t % 9) + 1
    return None


def parse_tile(token: str) -> int:
    """Parse compact names like m1, s9, p5, E, C, Fl1, Se2."""
    token = token.strip()
    if token in TILE_NAMES:
        return TILE_NAMES.index(token)
    if token in BONUS_NAMES:
        raise ValueError(f"bonus tile {token} is not a regular Tile34")
    # allow uppercase suit
    t = token.lower()
    if len(t) == 2 and t[0] in "msp" and t[1].isdigit():
        suit = {"m": 0, "s": 9, "p": 18}[t[0]]
        return suit + int(t[1]) - 1
    raise ValueError(f"unknown tile token: {token}")


def parse_tiles(tokens: Iterable[str]) -> list[int]:
    return [parse_tile(t) for t in tokens]


def full_wall() -> list[int]:
    """144-tile wall: 4 of each regular + one of each bonus (bonus as 100+id)."""
    wall = [t for t in range(NUM_REGULAR) for _ in range(COPIES)]
    wall.extend(100 + b for b in range(NUM_BONUS))
    return wall


def is_bonus_code(code: int) -> bool:
    return code >= 100


def bonus_id(code: int) -> int:
    return code - 100


def bonus_code(b: int) -> int:
    return 100 + b


def seat_for_bonus(b: int) -> int:
    """0=East ... 3=North for flower/season identity."""
    return b % 4
