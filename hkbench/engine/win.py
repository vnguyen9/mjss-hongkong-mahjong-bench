"""Win legality and hand decomposition."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from hkbench.engine.tiles import HONORS, is_suited, is_terminal_or_honor
from hkbench.engine.types import Meld, MeldKind

# The thirteen tiles a thirteen-orphans hand is built from; kept in sync with
# is_thirteen_orphans below.
_ORPHAN_TILES: tuple[int, ...] = (0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33)


@dataclass(frozen=True)
class Decomposition:
    """One structural parse of a winning hand."""

    pair: int
    concealed_melds: tuple[tuple[str, tuple[int, ...]], ...]  # ("chow"|"pong", tiles)
    # exposed melds come from PlayerState


def counts_from_tiles(tiles: list[int]) -> list[int]:
    c = [0] * 34
    for t in tiles:
        c[t] += 1
    return c


def hand_tile_count(concealed: list[int], melds: list[Meld], waiting: bool = False) -> int:
    """Tiles that should be present for a closed+open hand.

    Standard: 13 + 1 winning tile in concealed (or 14 after draw), minus exposed meld tiles
    already removed from concealed. We track exposed melds separately; concealed holds only
    unmelded tiles.
    """
    exposed = 0
    for m in melds:
        if m.is_kong():
            exposed += 3  # kong replaces a pong structurally for hand shape (4 physical)
        else:
            exposed += 3
    # For shape checks we care about "sets needed"
    return sum(concealed) + exposed


def is_thirteen_orphans(concealed: list[int]) -> bool:
    """13 orphans: one of each terminal/honor + one duplicate."""
    needed = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
    total = 0
    has_pair = False
    for t in needed:
        n = concealed[t]
        if n == 0 or n > 2:
            return False
        if n == 2:
            if has_pair:
                return False
            has_pair = True
        total += n
    # no other tiles
    if sum(concealed) != 14 or total != 14:
        return False
    return has_pair


def is_seven_pairs(concealed: list[int]) -> bool:
    """Seven Pairs: fourteen concealed tiles that make seven different pairs.

    Four of a kind is not two pairs, so a tile held four times fails the shape. This only
    answers the shape. Whether a table scores it is the profile's call
    (``RulesProfile.seven_pairs``), and the caller must also hold no melds: a declared meld,
    a concealed kong included, rules Seven Pairs out.
    """
    if sum(concealed) != 14:
        return False
    pairs = 0
    for n in concealed:
        if n == 0:
            continue
        if n != 2:
            return False
        pairs += 1
    return pairs == 7


def is_nine_gates(concealed: list[int]) -> bool:
    """Concealed 1112345678999 + any same suit."""
    if sum(concealed) != 14:
        return False
    suit_base = None
    for base in (0, 9, 18):
        if sum(concealed[base : base + 9]) == 14:
            suit_base = base
            break
    if suit_base is None:
        return False
    # must have at least 1112345678999
    need = [3, 1, 1, 1, 1, 1, 1, 1, 3]
    extra = 0
    for i in range(9):
        n = concealed[suit_base + i]
        if n < need[i]:
            return False
        extra += n - need[i]
    return extra == 1


def _remove_meld(c: list[int], tiles: tuple[int, ...]) -> bool:
    for t in tiles:
        if c[t] <= 0:
            return False
        c[t] -= 1
    return True


def _find_decomps(c: list[int], melds_needed: int) -> list[Decomposition]:
    """Recursive search for melds + pair in remaining concealed counts."""
    results: list[Decomposition] = []

    def search(counts: list[int], remaining: int, acc: list[tuple[str, tuple[int, ...]]], pair: int | None):
        if remaining == 0:
            if pair is not None and sum(counts) == 0:
                results.append(Decomposition(pair=pair, concealed_melds=tuple(acc)))
            return
        # find first tile present
        t0 = next((i for i, n in enumerate(counts) if n > 0), None)
        if t0 is None:
            return
        # try pair if not yet chosen and remaining melds leave exactly 2 tiles for pair... 
        # Actually we pick pair first at top level.
        # pong
        if counts[t0] >= 3:
            nc = counts.copy()
            nc[t0] -= 3
            search(nc, remaining - 1, acc + [("pong", (t0, t0, t0))], pair)
        # chow
        if is_suited(t0) and (t0 % 9) <= 6:
            a, b, c2 = t0, t0 + 1, t0 + 2
            if counts[a] and counts[b] and counts[c2]:
                nc = counts.copy()
                nc[a] -= 1
                nc[b] -= 1
                nc[c2] -= 1
                search(nc, remaining - 1, acc + [("chow", (a, b, c2))], pair)

    # try each possible pair
    for t in range(34):
        if c[t] >= 2:
            nc = c.copy()
            nc[t] -= 2
            search(nc, melds_needed, [], t)
    return results


@lru_cache(maxsize=1 << 16)
def _suit_fully_decomposes(counts: tuple[int, ...]) -> bool:
    """Can one suit's 9-tile vector be fully partitioned into pongs and runs?

    Memoized on the 9-tuple rather than the full 34-vector, so the cache is dense and
    shared across every hand containing the same suit shape.
    """
    first = -1
    for i in range(9):
        if counts[i]:
            first = i
            break
    if first < 0:
        return True
    work = list(counts)
    if work[first] >= 3:
        work[first] -= 3
        if _suit_fully_decomposes(tuple(work)):
            return True
        work[first] += 3
    if first <= 6 and work[first + 1] and work[first + 2]:
        work[first] -= 1
        work[first + 1] -= 1
        work[first + 2] -= 1
        if _suit_fully_decomposes(tuple(work)):
            return True
    return False


def _groups_fully_decompose(c: list[int]) -> bool:
    """Every tile consumed by complete sets, checked one tile-group at a time.

    Runs never cross a suit boundary and pongs are single-tile, so the decomposition
    factorizes into man / sou / pin / honours. Each group must therefore hold a multiple
    of three tiles and decompose on its own — which also fixes each group's set count,
    so there is nothing left to search across groups.
    """
    for t in range(27, 34):
        # Honours admit no runs, so a fully-consumed honour type holds exactly 0 or 3.
        # (Four of a kind cannot be consumed: a pong leaves one tile stranded.)
        if c[t] and c[t] != 3:
            return False
    for base in (0, 9, 18):
        segment = c[base : base + 9]
        total = segment[0] + segment[1] + segment[2] + segment[3] + segment[4] \
            + segment[5] + segment[6] + segment[7] + segment[8]
        if total % 3:
            return False
        if total and not _suit_fully_decomposes(tuple(segment)):
            return False
    return True


def _find_any_decomp(c: list[int], melds_needed: int) -> bool:
    """Existence-only version of _find_decomps with early exit.

    ``melds_needed`` is implied rather than searched: the sole caller
    (``_can_win_cached``) has already established ``sum(c) == melds_needed * 3 + 2``, so
    once the pair is removed the remainder is exactly ``melds_needed`` sets' worth of
    tiles. Fully consuming them therefore yields exactly that many sets.
    """
    if sum(c) != melds_needed * 3 + 2:
        return False
    for t in range(34):
        if c[t] >= 2:
            c[t] -= 2  # mutate/undo: this hot path allocated a 34-list per branch
            ok = _groups_fully_decompose(c)
            c[t] += 2
            if ok:
                return True
    return False


# NOTE: every function below depends on `exposed` only through len(exposed)
# (meld contents never affect structural legality), so caches key on the count.


def _structural_wins_uncached(
    concealed: list[int],
    n_exposed: int,
) -> list[Decomposition]:
    if is_thirteen_orphans(concealed) and not n_exposed:
        return [Decomposition(pair=-1, concealed_melds=(("thirteen_orphans", ()),))]
    if is_nine_gates(concealed) and not n_exposed:
        return [Decomposition(pair=-2, concealed_melds=(("nine_gates", ()),))]

    needed = 4 - n_exposed
    if needed < 0:
        return []
    total_concealed = sum(concealed)
    # each remaining set = 3, pair = 2
    if total_concealed != needed * 3 + 2:
        return []
    return _find_decomps(concealed, needed)


@lru_cache(maxsize=1 << 16)
def _structural_wins_cached(
    concealed: tuple[int, ...], n_exposed: int
) -> tuple[Decomposition, ...]:
    return tuple(_structural_wins_uncached(list(concealed), n_exposed))


def structural_wins(
    concealed: list[int],
    exposed: list[Meld],
) -> list[Decomposition]:
    """Return all standard 4-set+pair decompositions of concealed+exposed.

    `concealed` must include the winning tile (14 tiles total shape accounting for exposed).
    """
    return list(_structural_wins_cached(tuple(concealed), len(exposed)))


@lru_cache(maxsize=1 << 18)
def _can_win_cached(concealed: tuple[int, ...], n_exposed: int) -> bool:
    c = list(concealed)
    if is_thirteen_orphans(c) and not n_exposed:
        return True
    if is_nine_gates(c) and not n_exposed:
        return True
    needed = 4 - n_exposed
    if needed < 0:
        return False
    if sum(c) != needed * 3 + 2:
        return False
    return _find_any_decomp(c, needed)


def can_win_structurally(concealed: list[int], exposed: list[Meld]) -> bool:
    return _can_win_cached(tuple(concealed), len(exposed))


def _wait_candidates(concealed13: list[int], n_exposed: int) -> list[int]:
    """Tiles that could possibly complete this hand.

    A drawn tile has to join *something*: a pair or pong (so at least one copy is
    already held), or a run (so an in-suit neighbour within two is held). A tile meeting
    neither condition cannot complete any set, so probing it is wasted work — this
    typically cuts the 34 probes to roughly a third.

    Thirteen orphans is the exception: its winning tile need not be held or adjacent to
    anything, so every terminal/honour stays a candidate for a fully concealed hand.
    """
    candidate = [False] * 34
    for t in range(34):
        if concealed13[t] <= 0:
            continue
        candidate[t] = True
        if t <= 26:  # suited: runs reach two tiles either side, within the same suit
            base = (t // 9) * 9
            for offset in (-2, -1, 1, 2):
                neighbour = t + offset
                if base <= neighbour < base + 9:
                    candidate[neighbour] = True
    if not n_exposed:
        for t in _ORPHAN_TILES:
            candidate[t] = True
    return [t for t in range(34) if candidate[t]]


def _waits_uncached(concealed13: list[int], n_exposed: int) -> list[int]:
    out = []
    probe = list(concealed13)
    for t in _wait_candidates(concealed13, n_exposed):
        if concealed13[t] >= 4:
            continue
        probe[t] += 1  # mutate/undo instead of copying the 34-vector per probe
        if _can_win_cached(tuple(probe), n_exposed):
            out.append(t)
        probe[t] -= 1
    return out


@lru_cache(maxsize=1 << 16)
def _waits_cached(
    concealed13: tuple[int, ...], n_exposed: int
) -> tuple[int, ...]:
    return tuple(_waits_uncached(list(concealed13), n_exposed))


def waits(concealed13: list[int], exposed: list[Meld]) -> list[int]:
    """Tiles that complete a structural win from a 13-tile hand."""
    return list(_waits_cached(tuple(concealed13), len(exposed)))
