"""Deterministic construction of rare engine positions for tests.

Some terminal branches are effectively unreachable by fuzzing: reaching them needs competent
play from two seats at once. The rob-kong win is the canonical example. Building such
positions directly gives cheap, high-volume coverage of exactly the branch that matters.
"""

from __future__ import annotations

from helpers import hkma_profile
from hkbench.engine.tile_instance import STANDARD_INSTANCES, TileLocation
from hkbench.engine.types import Meld, MeldKind, Phase, PlayerState
from hkbench.engine.game import GameState
from hkbench.engine.game_types import ChanceOutcome

# A robbable tile must sit strictly inside a suit so a closed chow wait (t-1, t+1)
# exists. This is not an arbitrary restriction: before an ADDED_KONG all four copies
# of the tile are with the declarer, so the winner physically cannot hold one. A
# legitimate rob-kong win therefore can never be a pair- or pong-completion on the
# robbed tile — only a run completion.
ROBBABLE_TILES: tuple[int, ...] = tuple(
    t for t in range(27) if 1 <= t % 9 <= 7
)


def build_rob_kong_position(
    *,
    robbed_tile: int,
    declarer: int = 0,
    winner: int = 1,
    dealer: int = 0,
) -> GameState:
    """Return a ``SELF_ACTION`` state where ``declarer`` can rob-kong ``robbed_tile``.

    ``declarer`` holds an exposed PONG of ``robbed_tile`` plus the 4th copy concealed,
    so ADDED_KONG is legal. ``winner`` is concealed-tenpai on a closed chow wait that
    only ``robbed_tile`` completes, with a dragon pong and a seat-wind pong to clear the
    profile's 3-faan minimum. The other two seats hold all-distinct junk so they can
    never be reaction-eligible.
    """
    if robbed_tile not in ROBBABLE_TILES:
        raise ValueError(
            f"robbed_tile {robbed_tile} needs both neighbours in-suit; "
            f"pick from ROBBABLE_TILES"
        )
    if declarer == winner:
        raise ValueError("declarer and winner must differ")

    avail = [4] * 34
    cursor = [0] * 34

    def take(tile: int, count: int) -> list[int]:
        """Reserve ``count`` physical instances of ``tile`` (ids ``4t .. 4t+3``)."""
        if avail[tile] < count:
            raise ValueError(f"tile {tile} has {avail[tile]} left, needed {count}")
        avail[tile] -= count
        ids = [4 * tile + cursor[tile] + k for k in range(count)]
        cursor[tile] += count
        return ids

    # Tiles adjacent to the wait are kept out of every filler hand so no other seat
    # accidentally becomes able to chow or win on the robbed tile.
    forbidden = {robbed_tile + d for d in (-2, -1, 0, 1, 2)}

    pong_ids = take(robbed_tile, 3)  # declarer's exposed PONG
    declarer_fourth = take(robbed_tile, 1)  # the copy that becomes the kong

    winner_seat = (winner - dealer) % 4
    wind = 27 + winner_seat
    winner_ids = take(wind, 3)
    dragon = next(d for d in (31, 32, 33) if avail[d] >= 3)
    winner_ids += take(dragon, 3)
    winner_ids += take(robbed_tile - 1, 1) + take(robbed_tile + 1, 1)
    filler_pong = next(
        t for t in range(34) if t not in forbidden and t != wind and avail[t] >= 3
    )
    winner_ids += take(filler_pong, 3)
    filler_pair = next(
        t for t in range(34) if t not in forbidden and t != wind and avail[t] >= 2
    )
    winner_ids += take(filler_pair, 2)  # 3+3+2+3+2 = 13

    def distinct_junk(count: int) -> list[int]:
        """All-distinct tiles, so the holder is far from any winning shape."""
        ids: list[int] = []
        for tile in range(34):
            if len(ids) >= count:
                break
            if tile in forbidden or avail[tile] < 1:
                continue
            ids += take(tile, 1)
        if len(ids) < count:
            raise ValueError("ran out of distinct filler tiles")
        return ids

    # Declarer sits at SELF_ACTION with one meld, so 11 concealed tiles.
    declarer_ids = declarer_fourth + distinct_junk(10)
    hands = {declarer: declarer_ids, winner: winner_ids}
    for seat in range(4):
        if seat not in (declarer, winner):
            hands[seat] = distinct_junk(13)

    players = [PlayerState(seat=(i - dealer) % 4) for i in range(4)]
    locations = [TileLocation.LIVE_WALL] * 144
    concealed_ids: list[list[int]] = [[] for _ in range(4)]
    meld_ids: list[list[list[int]]] = [[] for _ in range(4)]

    placed: set[int] = set()
    for seat, ids in hands.items():
        for iid in ids:
            concealed_ids[seat].append(iid)
            locations[iid] = TileLocation.CONCEALED
            players[seat].concealed[STANDARD_INSTANCES[iid].tile_type] += 1
            placed.add(iid)

    # The PONG's from_seat is cosmetic here but must be a real other seat, since
    # _revert_added_kong_for_rob preserves it when reverting the meld.
    pong_from = (declarer + 3) % 4
    players[declarer].melds.append(
        Meld(MeldKind.PONG, (robbed_tile,) * 3, pong_from, robbed_tile)
    )
    # The meld claims a tile, so history must show that seat discarding it — otherwise the
    # fixture is a state no sequence of play could produce, and `check_invariants`'
    # claimed-tile rule correctly rejects it. The tile is deliberately NOT put back in the
    # river: a claimed discard leaves the river and lives on only in history, which is
    # exactly the post-claim shape this fixture is standing in for.
    seeded_history = [(pong_from, robbed_tile)]
    meld_ids[declarer].append(list(pong_ids))
    for iid in pong_ids:
        locations[iid] = TileLocation.EXPOSED_MELD
        placed.add(iid)

    # Bonus tiles go to the middle of the wall so neither a front draw nor a rear
    # kong-replacement draw could ever surface one and perturb the scenario.
    rest = [i for i in range(144) if i not in placed]
    regular = [i for i in rest if not STANDARD_INSTANCES[i].is_bonus]
    bonus = [i for i in rest if STANDARD_INSTANCES[i].is_bonus]
    mid = len(regular) // 2
    wall_order = regular[:mid] + bonus + regular[mid:]

    return GameState(
        profile=hkma_profile(),
        players=players,
        wall_order=wall_order,
        wall_front=0,
        wall_rear=len(wall_order),
        locations=locations,
        concealed_ids=concealed_ids,
        meld_ids=meld_ids,
        discard_history=seeded_history,
        phase=Phase.SELF_ACTION,
        current_player=declarer,
        dealer=dealer,
        prevailing_wind=0,
        turn=8,
        first_turn=False,
        chance=ChanceOutcome(
            mode="supplied_wall", seed=0, wall_instance_ids=tuple(wall_order)
        ),
    )


def build_multi_claim_position(
    *,
    tile: int,
    discarder: int = 0,
    pong_seat: int | None = None,
    chow_seat: int | None = None,
    win_seats: tuple[int, ...] = (),
    dealer: int = 0,
) -> GameState:
    """Return a ``SELF_ACTION`` state where ``discarder`` holds ``tile`` and several seats
    are primed to claim it, so discarding it opens a genuine multi-claimant race.

    Claim priority is the one branch of the engine with no direct coverage: the test that
    named it was ``assert True``, deferring to "golden claim fixtures" that do not exist.
    Fuzzing cannot fill the gap — a race needs two seats to be *simultaneously* competent
    on the same tile, which is the same reason the v7 rob-kong settlement bug survived
    10,000,000 random actions.

    ``win_seats`` are made concealed-tenpai on a closed ``(tile-1, tile+1)`` chow wait that
    only ``tile`` completes, each clearing the 3-faan minimum from a *disjoint* group of
    honours so two winners never compete for copies:

    - the first uses a prevailing-wind pung, its own seat-wind pung and one dragon pung
    - the second uses two other dragon pungs and its own seat-wind pung

    ``pong_seat`` gets two concealed copies of ``tile``; ``chow_seat`` — which must sit to
    the discarder's immediate left, the only seat a chow is legal for — gets ``tile-2`` and
    ``tile-1``. Every other hand is all-distinct junk drawn from outside the wait's
    neighbourhood, so no seat becomes accidentally eligible.
    """
    if tile not in ROBBABLE_TILES:
        raise ValueError(f"tile {tile} needs both neighbours in-suit; pick from ROBBABLE_TILES")
    if chow_seat is not None and chow_seat != (discarder + 1) % 4:
        raise ValueError("chow is only ever legal for the seat to the discarder's left")
    claimants = [s for s in (pong_seat, chow_seat, *win_seats) if s is not None]
    if discarder in claimants:
        raise ValueError("the discarder cannot claim its own discard")
    if len(set(claimants)) != len(claimants):
        raise ValueError("each seat may hold at most one claiming role")
    if len(win_seats) > 2:
        raise ValueError("this builder supplies disjoint 3-faan groups for at most 2 winners")

    avail = [4] * 34
    cursor = [0] * 34

    def take(t: int, count: int) -> list[int]:
        if avail[t] < count:
            raise ValueError(f"tile {t} has {avail[t]} left, needed {count}")
        avail[t] -= count
        ids = [4 * t + cursor[t] + k for k in range(count)]
        cursor[t] += count
        return ids

    # Keep the wait's neighbourhood out of every filler hand, exactly as the rob-kong
    # builder does, so junk seats can never chow or win on the discard.
    forbidden = {tile + d for d in (-2, -1, 0, 1, 2)}

    hands: dict[int, list[int]] = {}
    discarder_ids = take(tile, 1)  # the tile that will be discarded

    # Disjoint honour groups. Group 0 leans on the prevailing wind; group 1 on two dragons.
    for order, seat in enumerate(win_seats):
        seat_wind = 27 + ((seat - dealer) % 4)
        ids: list[int] = []
        if order == 0:
            prevailing = 27  # dealer 0 / prevailing East throughout this builder
            if seat_wind == prevailing:
                raise ValueError("first win seat must not be the prevailing-wind seat")
            ids += take(prevailing, 3) + take(seat_wind, 3) + take(31, 3)
        else:
            ids += take(32, 3) + take(33, 3) + take(seat_wind, 3)
        ids += take(tile - 1, 1) + take(tile + 1, 1)  # the closed wait
        pair = next(
            t for t in range(34)
            if t not in forbidden and avail[t] >= 2 and t not in (27, 31, 32, 33)
        )
        ids += take(pair, 2)
        hands[seat] = ids  # 3+3+3+2+2 = 13

    if pong_seat is not None:
        hands[pong_seat] = take(tile, 2)
    if chow_seat is not None:
        hands.setdefault(chow_seat, [])
        hands[chow_seat] += take(tile - 2, 1) + take(tile - 1, 1)

    def distinct_junk(count: int) -> list[int]:
        ids: list[int] = []
        for t in range(34):
            if len(ids) >= count:
                break
            if t in forbidden or avail[t] < 1:
                continue
            ids += take(t, 1)
        if len(ids) < count:
            raise ValueError("ran out of distinct filler tiles")
        return ids

    # Discarder is at SELF_ACTION with no melds, so 14 concealed tiles.
    hands[discarder] = discarder_ids + distinct_junk(13)
    for seat in range(4):
        hands.setdefault(seat, [])
        if len(hands[seat]) < 13:
            hands[seat] = hands[seat] + distinct_junk(13 - len(hands[seat]))

    players = [PlayerState(seat=(i - dealer) % 4) for i in range(4)]
    locations = [TileLocation.LIVE_WALL] * 144
    concealed_ids: list[list[int]] = [[] for _ in range(4)]
    placed: set[int] = set()
    for seat, ids in hands.items():
        for iid in ids:
            concealed_ids[seat].append(iid)
            locations[iid] = TileLocation.CONCEALED
            players[seat].concealed[STANDARD_INSTANCES[iid].tile_type] += 1
            placed.add(iid)

    rest = [i for i in range(144) if i not in placed]
    regular = [i for i in rest if not STANDARD_INSTANCES[i].is_bonus]
    bonus = [i for i in rest if STANDARD_INSTANCES[i].is_bonus]
    mid = len(regular) // 2
    wall_order = regular[:mid] + bonus + regular[mid:]

    return GameState(
        profile=hkma_profile(),
        players=players,
        wall_order=wall_order,
        wall_front=0,
        wall_rear=len(wall_order),
        locations=locations,
        concealed_ids=concealed_ids,
        meld_ids=[[] for _ in range(4)],
        phase=Phase.SELF_ACTION,
        current_player=discarder,
        dealer=dealer,
        prevailing_wind=0,
        turn=8,
        first_turn=False,
        chance=ChanceOutcome(
            mode="supplied_wall", seed=0, wall_instance_ids=tuple(wall_order)
        ),
    )
