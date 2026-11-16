"""Canonical game types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import Any


class MeldKind(IntEnum):
    CHOW = 0
    PONG = 1
    EXPOSED_KONG = 2
    CONCEALED_KONG = 3
    ADDED_KONG = 4


class Phase(IntEnum):
    DEAL = 0
    DRAW = 1
    SELF_ACTION = 2
    REACTION = 3
    RESOLVE = 4
    TERMINAL = 5


class WinSource(IntEnum):
    DISCARD = 0
    SELF_DRAW = 1
    ROB_KONG = 2
    FLOWER_SEVEN = 3
    FLOWER_EIGHT = 4


class Seat(IntEnum):
    EAST = 0
    SOUTH = 1
    WEST = 2
    NORTH = 3


@dataclass(frozen=True)
class Meld:
    kind: MeldKind
    tiles: tuple[int, ...]  # Tile34 ids; for chow sorted ascending
    from_seat: int | None = None  # seat that discarded the claimed tile
    claimed_tile: int | None = None

    def is_concealed(self) -> bool:
        return self.kind == MeldKind.CONCEALED_KONG

    def is_kong(self) -> bool:
        return self.kind in (
            MeldKind.EXPOSED_KONG,
            MeldKind.CONCEALED_KONG,
            MeldKind.ADDED_KONG,
        )

    def is_pong_or_kong(self) -> bool:
        return self.kind != MeldKind.CHOW

    def tile_type(self) -> int:
        """Representative tile (for pong/kong) or first of chow."""
        if self.kind == MeldKind.CHOW:
            return self.tiles[0]
        return self.tiles[0]


@dataclass
class PlayerState:
    concealed: list[int] = field(default_factory=lambda: [0] * 34)  # counts
    melds: list[Meld] = field(default_factory=list)
    flowers: list[int] = field(default_factory=list)  # bonus ids 0..7
    seat: int = 0
    score: int = 0

    def concealed_count(self) -> int:
        return sum(self.concealed)

    def clone(self) -> PlayerState:
        return PlayerState(
            concealed=self.concealed.copy(),
            melds=list(self.melds),
            flowers=list(self.flowers),
            seat=self.seat,
            score=self.score,
        )


@dataclass(frozen=True)
class PatternHit:
    name: str
    faan: int


@dataclass
class ScoreResult:
    patterns: list[PatternHit]
    total_faan: int
    capped_faan: int
    meets_minimum: bool
    is_limit: bool
    payments: list[int]  # net for seats 0..3
    win_source: WinSource
    winner: int
    discarder: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "patterns": [{"name": p.name, "faan": p.faan} for p in self.patterns],
            "total_faan": self.total_faan,
            "capped_faan": self.capped_faan,
            "meets_minimum": self.meets_minimum,
            "is_limit": self.is_limit,
            "payments": list(self.payments),
            "win_source": self.win_source.name,
            "winner": self.winner,
            "discarder": self.discarder,
        }


@dataclass
class RoundResult:
    cause: str  # win | exhaustive
    score: ScoreResult | None
    payments: list[int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cause": self.cause,
            "score": self.score.to_dict() if self.score else None,
            "payments": list(self.payments),
        }


class EventKind(str, Enum):
    DEAL = "deal"
    DRAW = "draw"
    DISCARD = "discard"
    CHOW = "chow"
    PONG = "pong"
    KONG = "kong"
    ADDED_KONG = "added_kong"
    CONCEALED_KONG = "concealed_kong"
    FLOWER = "flower"
    WIN = "win"
    PASS = "pass"
    EXHAUSTIVE = "exhaustive"


@dataclass(frozen=True)
class Event:
    kind: EventKind
    seat: int
    tile: int | None = None
    data: tuple[Any, ...] = ()


NUM_ACTIONS = 127
# 0 Pass, 1 Win, 2-35 Discard, 36-56 Chow, 57 Pong, 58 Kong,
# 59-92 Concealed Kong, 93-126 Added Kong
