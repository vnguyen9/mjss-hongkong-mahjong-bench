"""Shanten / ukeire / deficiency helpers (34-tile)."""

from __future__ import annotations

from functools import lru_cache

from hkbench.engine.tiles import is_suited
from hkbench.engine.types import Meld
from hkbench.engine.win import _can_win_cached, waits


_SHANTEN_CAP = 8

# Memo for every shanten/ukeire/deficiency query. Bounded so a worker stays small.
_SOLVE_CACHE_SIZE = 1 << 16


@lru_cache(maxsize=_SOLVE_CACHE_SIZE)
def _solve(counts: tuple[int, ...], sets: int, pair: bool, target_sets: int) -> int:
    """Minimum additional tile changes to reach ``target_sets`` sets plus a pair.

    A memoized pure function replacing the previous branch-and-bound recursion. The
    old version pruned on ``depth >= best``, which only ever skipped branches that
    could not improve the incumbent — so the minimum is unchanged, while distinct
    search paths that converge on the same ``(counts, sets, pair)`` state now collapse
    to one cache entry instead of being re-explored.

    Results are capped by the caller at ``_SHANTEN_CAP`` to match the old initial
    ``best = 8``, which made any true minimum of 8 or more report as exactly 8.
    """
    if sets == target_sets:
        if pair:
            return 0
        for count in counts:
            if count >= 2:
                return 0
        return 1
    t0 = -1
    for i in range(34):
        if counts[i]:
            t0 = i
            break
    if t0 < 0:
        return (0 if pair else 1) + (target_sets - sets)

    work = list(counts)
    n0 = work[t0]
    best = _SHANTEN_CAP * 4  # any finite sentinel above every reachable result

    # use as pong
    if n0 >= 3:
        work[t0] = n0 - 3
        best = min(best, _solve(tuple(work), sets + 1, pair, target_sets))
    elif n0 == 2:
        work[t0] = 0
        best = min(best, 1 + _solve(tuple(work), sets + 1, pair, target_sets))
    else:  # n0 == 1
        work[t0] = 0
        best = min(best, 2 + _solve(tuple(work), sets + 1, pair, target_sets))
    work[t0] = n0

    # chow
    if t0 <= 26 and t0 % 9 <= 6:
        need = 0
        restore = []
        for x in (t0, t0 + 1, t0 + 2):
            if work[x] > 0:
                work[x] -= 1
                restore.append(x)
            else:
                need += 1
        best = min(best, need + _solve(tuple(work), sets + 1, pair, target_sets))
        for x in restore:
            work[x] += 1

    # pair
    if not pair:
        if n0 >= 2:
            work[t0] = n0 - 2
            best = min(best, _solve(tuple(work), sets, True, target_sets))
        else:  # n0 == 1
            work[t0] = 0
            best = min(best, 1 + _solve(tuple(work), sets, True, target_sets))
        work[t0] = n0

    # discard this tile
    work[t0] = n0 - 1
    best = min(best, 1 + _solve(tuple(work), sets, pair, target_sets))
    work[t0] = n0
    return best


def _standard_shanten_uncached(concealed: list[int], n_exposed: int) -> int:
    if _can_win_cached(tuple(concealed), n_exposed):
        return -1
    return min(_SHANTEN_CAP, _solve(tuple(concealed), 0, False, 4 - n_exposed))


def _standard_shanten_legacy(concealed: list[int], n_exposed: int) -> int:
    """Original branch-and-bound. Retained as the reference oracle for tests."""
    if _can_win_cached(tuple(concealed), n_exposed):
        return -1

    # Search minimum changes — use BFS on deficiency-style for small depth
    best = 8
    target_sets = 4 - n_exposed

    # Mutate/undo throughout instead of copying the 34-element counts vector at every
    # branch. The search shape, visit order and results are unchanged; only the
    # allocation is removed. Generator expressions are unrolled into plain loops for the
    # same reason.
    def dfs(counts: list[int], sets: int, pair: bool, depth: int) -> None:
        nonlocal best
        if depth >= best:
            return
        # lower bound
        if sets == target_sets and pair:
            best = min(best, depth)
            return
        if sets == target_sets and not pair:
            # need pair
            has_pair_candidate = False
            for c in counts:
                if c >= 2:
                    has_pair_candidate = True
                    break
            best = min(best, depth if has_pair_candidate else depth + 1)
            return
        t0 = -1
        for i in range(34):
            if counts[i] > 0:
                t0 = i
                break
        if t0 < 0:
            best = min(best, depth + (0 if pair else 1) + (target_sets - sets))
            return
        n0 = counts[t0]
        # use as pong
        if n0 >= 3:
            counts[t0] = n0 - 3
            dfs(counts, sets + 1, pair, depth)
            counts[t0] = n0
        elif n0 == 2:
            counts[t0] = 0
            dfs(counts, sets + 1, pair, depth + 1)  # need 1 more for pong
            counts[t0] = n0
        elif n0 == 1:
            counts[t0] = 0
            dfs(counts, sets + 1, pair, depth + 2)
            counts[t0] = n0
        # chow
        if t0 <= 26 and t0 % 9 <= 6:
            b, c2 = t0 + 1, t0 + 2
            # counts[t0] > 0 always holds here (t0 is the first non-empty tile), so the
            # original `have` guard was always satisfied.
            need = 0
            restore = []
            for x in (t0, b, c2):
                if counts[x] > 0:
                    counts[x] -= 1
                    restore.append(x)
                else:
                    need += 1
            dfs(counts, sets + 1, pair, depth + need)
            for x in restore:
                counts[x] += 1
        # pair
        if not pair and n0 >= 2:
            counts[t0] = n0 - 2
            dfs(counts, sets, True, depth)
            counts[t0] = n0
        elif not pair and n0 == 1:
            counts[t0] = 0
            dfs(counts, sets, True, depth + 1)
            counts[t0] = n0
        # discard this tile
        counts[t0] = n0 - 1
        dfs(counts, sets, pair, depth + 1)
        counts[t0] = n0

    dfs(concealed.copy(), 0, False, 0)
    return best


@lru_cache(maxsize=1 << 18)
def _standard_shanten_cached(concealed: tuple[int, ...], n_exposed: int) -> int:
    return _standard_shanten_uncached(list(concealed), n_exposed)


def standard_shanten(concealed: list[int], exposed: list[Meld]) -> int:
    """Approximate shanten for standard hands (not thirteen orphans).

    Uses recursive set extraction; 0 = tenpai, -1 = complete (14 tiles).
    """
    return _standard_shanten_cached(tuple(concealed), len(exposed))


def ukeire(concealed13: list[int], exposed: list[Meld], remaining: list[int]) -> tuple[int, list[int]]:
    """Return (total live outs, wait tiles) for a 13-tile hand.

    Uncached itself (`remaining` changes nearly every call); the expensive
    `waits()` underneath is memoized.
    """
    w = waits(concealed13, exposed)
    total = sum(remaining[t] for t in w)
    return total, w


@lru_cache(maxsize=1 << 18)
def _deficiency_cached(concealed: tuple[int, ...], n_exposed: int) -> int:
    s = _standard_shanten_cached(concealed, n_exposed)
    if s < 0:
        return 0
    return max(0, s)


def deficiency(concealed: list[int], exposed: list[Meld] | None = None) -> int:
    """Minimum tile changes to a complete structural hand (paper-style)."""
    return _deficiency_cached(tuple(concealed), len(exposed) if exposed else 0)
