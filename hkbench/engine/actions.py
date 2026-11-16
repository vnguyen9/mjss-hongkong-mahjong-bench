"""Fixed 127-action encoding."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from hkbench.engine.types import NUM_ACTIONS


class ActionKind(IntEnum):
    PASS = 0
    WIN = 1
    DISCARD = 2
    CHOW = 3
    PONG = 4
    KONG = 5
    CONCEALED_KONG = 6
    ADDED_KONG = 7


# 21 suited chow patterns: for each suit, starts at rank 1..7
CHOW_PATTERNS: list[tuple[int, int, int]] = []
for suit_base in (0, 9, 18):
    for start in range(7):
        CHOW_PATTERNS.append((suit_base + start, suit_base + start + 1, suit_base + start + 2))
assert len(CHOW_PATTERNS) == 21


@dataclass(frozen=True)
class Action:
    action_id: int
    kind: ActionKind
    tile: int | None = None  # discard / kong tile type
    chow_index: int | None = None

    def __repr__(self) -> str:
        return f"Action({self.action_id}, {self.kind.name}, tile={self.tile}, chow={self.chow_index})"


def action_from_id(action_id: int) -> Action:
    if not 0 <= action_id < NUM_ACTIONS:
        raise ValueError(f"action_id out of range: {action_id}")
    if action_id == 0:
        return Action(0, ActionKind.PASS)
    if action_id == 1:
        return Action(1, ActionKind.WIN)
    if 2 <= action_id <= 35:
        return Action(action_id, ActionKind.DISCARD, tile=action_id - 2)
    if 36 <= action_id <= 56:
        return Action(action_id, ActionKind.CHOW, chow_index=action_id - 36)
    if action_id == 57:
        return Action(57, ActionKind.PONG)
    if action_id == 58:
        return Action(58, ActionKind.KONG)
    if 59 <= action_id <= 92:
        return Action(action_id, ActionKind.CONCEALED_KONG, tile=action_id - 59)
    if 93 <= action_id <= 126:
        return Action(action_id, ActionKind.ADDED_KONG, tile=action_id - 93)
    raise ValueError(f"unmapped action_id: {action_id}")


def discard_action(tile: int) -> int:
    return 2 + tile


def chow_action(chow_index: int) -> int:
    return 36 + chow_index


def concealed_kong_action(tile: int) -> int:
    return 59 + tile


def added_kong_action(tile: int) -> int:
    return 93 + tile


def all_actions() -> list[Action]:
    return [action_from_id(i) for i in range(NUM_ACTIONS)]
