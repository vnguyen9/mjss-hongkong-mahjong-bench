"""Physical tile instances for simulator v2 (IDs 0..143)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable

from hkbench.engine.tiles import NUM_BONUS, NUM_REGULAR


class TileLocation(IntEnum):
    LIVE_WALL = 0
    REPLACEMENT_END = 1  # rear of wall awaiting replacement draws
    CONCEALED = 2
    EXPOSED_MELD = 3
    RIVER = 4
    FLOWER_AREA = 5
    WINNING_CONTEXT = 6


@dataclass(frozen=True)
class TileInstance:
    """Immutable physical tile. ``instance_id`` is unique in 0..143."""

    instance_id: int
    tile_type: int  # 0..33 regular, or bonus 0..7 when is_bonus
    is_bonus: bool

    def __post_init__(self) -> None:
        if not 0 <= self.instance_id <= 143:
            raise ValueError(f"instance_id out of range: {self.instance_id}")
        if self.is_bonus:
            if not 0 <= self.tile_type < NUM_BONUS:
                raise ValueError(f"bad bonus type {self.tile_type}")
        elif not 0 <= self.tile_type < NUM_REGULAR:
            raise ValueError(f"bad regular type {self.tile_type}")


def build_standard_instances() -> tuple[TileInstance, ...]:
    """Canonical 144-tile set: four of each regular, then eight bonus tiles."""
    tiles: list[TileInstance] = []
    iid = 0
    for t in range(NUM_REGULAR):
        for _ in range(4):
            tiles.append(TileInstance(instance_id=iid, tile_type=t, is_bonus=False))
            iid += 1
    for b in range(NUM_BONUS):
        tiles.append(TileInstance(instance_id=iid, tile_type=b, is_bonus=True))
        iid += 1
    assert iid == 144 and len(tiles) == 144
    return tuple(tiles)


STANDARD_INSTANCES: tuple[TileInstance, ...] = build_standard_instances()


def validate_supplied_wall(instance_ids: Iterable[int]) -> list[int]:
    """Validate a supplied wall of 144 unique instance ids with correct multiplicities."""
    ids = list(instance_ids)
    if len(ids) != 144:
        raise ValueError(f"wall must have 144 tiles, got {len(ids)}")
    if len(set(ids)) != 144:
        raise ValueError("wall instance ids must be unique")
    if sorted(ids) != list(range(144)):
        raise ValueError("wall must be a permutation of 0..143")
    # Multiplicity by type is implied by STANDARD_INSTANCES ordering.
    return ids


def type_code(inst: TileInstance) -> int:
    """Encode as legacy wall code: regular 0..33 or bonus 100+b."""
    if inst.is_bonus:
        return 100 + inst.tile_type
    return inst.tile_type
