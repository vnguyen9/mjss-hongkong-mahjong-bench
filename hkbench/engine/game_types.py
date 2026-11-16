"""Simulator v2 public types: events, terminal results, replay, invariants."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from hkbench.engine.types import RoundResult, ScoreResult, WinSource


class DrawKind(str, Enum):
    ORDINARY = "ordinary"
    FLOWER_REPLACEMENT = "flower_replacement"
    KONG_REPLACEMENT = "kong_replacement"


class GameEventKind(str, Enum):
    DEAL = "deal"
    DRAW = "draw"
    FLOWER = "flower"
    REPLACEMENT = "replacement"
    DISCARD = "discard"
    CHOW = "chow"
    PONG = "pong"
    KONG = "kong"
    ADDED_KONG = "added_kong"
    CONCEALED_KONG = "concealed_kong"
    PASS = "pass"
    WIN = "win"
    EXHAUSTIVE = "exhaustive"


@dataclass(frozen=True)
class GameEventV2:
    kind: GameEventKind
    seat: int
    tile_type: int | None = None
    instance_id: int | None = None
    draw_kind: DrawKind | None = None
    data: tuple[Any, ...] = ()


@dataclass(frozen=True)
class ChanceOutcome:
    """Explicit wall outcome: either sampled seed or supplied instance order."""

    mode: str  # sampled_wall | supplied_wall
    seed: int | None = None
    wall_instance_ids: tuple[int, ...] | None = None


@dataclass(frozen=True)
class ReplayActionV2:
    """One successfully applied player decision in an authoritative replay."""

    actor: int
    action_id: int


@dataclass
class TerminalResult:
    cause: str  # win | exhaustive
    winner: int | None
    discarder: int | None
    win_source: WinSource | None
    pattern_breakdown: list[dict[str, Any]]
    faan: int
    payments: list[int]  # length 4, must sum to 0
    score: ScoreResult | None = None

    def to_round_result(self) -> RoundResult:
        return RoundResult(cause=self.cause, score=self.score, payments=list(self.payments))

    def to_dict(self) -> dict[str, Any]:
        return {
            "cause": self.cause,
            "winner": self.winner,
            "discarder": self.discarder,
            "win_source": self.win_source.name if self.win_source else None,
            "pattern_breakdown": list(self.pattern_breakdown),
            "faan": self.faan,
            "payments": list(self.payments),
            "score": self.score.to_dict() if self.score else None,
        }


@dataclass
class ReplayV2:
    rules_hash: str
    rules_profile_id: str
    chance: ChanceOutcome
    initial_dealer: int
    prevailing_wind: int
    actions: list[ReplayActionV2] = field(default_factory=list)
    events: list[GameEventV2] = field(default_factory=list)
    terminal: TerminalResult | None = None


@dataclass
class InvariantReport:
    ok: bool
    messages: list[str] = field(default_factory=list)

    def raise_if_failed(self) -> None:
        if not self.ok:
            raise AssertionError("; ".join(self.messages))
