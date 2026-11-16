"""The numbers: means with intervals that respect duplicate play, and Bradley-Terry ranks.

Why clustered. The four games of a deal are the same wall played from four seats (and the six
games of a head-to-head deal are the same wall with six seat pairs). They are not independent.
Every interval here treats the *deal* as the unit: one number per deal, then the ordinary
standard error of those numbers.

Standard library only.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from hkbench.seeds import Rng


# --- Student t ---------------------------------------------------------------------------------


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_front = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x)
    front = math.exp(ln_front)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    """P(T <= t) for Student t with ``df`` degrees of freedom."""
    x = df / (df + t * t)
    tail = 0.5 * _betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


def t_critical_95(df: int) -> float:
    """Two-sided 95 percent critical value of Student t with ``df`` degrees of freedom."""
    if df < 1:
        return float("nan")
    lo, hi = 0.0, 200.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, float(df)) < 0.975:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# --- clustered means ---------------------------------------------------------------------------


def mean_ci(values: Sequence[float]) -> Dict[str, Any]:
    """Mean of one number per deal, with its standard error and 95% interval."""
    n = len(values)
    if n == 0:
        return {"mean": None, "se": None, "ci95": None, "n": 0}
    m = sum(values) / n
    if n < 2:
        return {"mean": m, "se": None, "ci95": None, "n": n}
    var = sum((v - m) ** 2 for v in values) / (n - 1)
    se = math.sqrt(var / n)
    half = t_critical_95(n - 1) * se
    return {"mean": m, "se": se, "ci95": [m - half, m + half], "n": n}


def per_deal(records: Iterable[Dict[str, Any]], value) -> List[float]:
    """Average ``value(record)`` within each deal, in deal order."""
    sums: Dict[int, float] = {}
    counts: Dict[int, int] = {}
    for r in records:
        d = r["deal"]
        sums[d] = sums.get(d, 0.0) + value(r)
        counts[d] = counts.get(d, 0) + 1
    return [sums[d] / counts[d] for d in sorted(sums)]


# --- the headline for a scored bot -------------------------------------------------------------


def focal_seat(record: Dict[str, Any], key: str = "bot") -> int:
    return record["seats"].index(key)


def duplicate_summary(records: Sequence[Dict[str, Any]], faan_cap: int, key: str = "bot") -> Dict[str, Any]:
    """Everything reported for one scored bot, from its duplicate-play game records."""
    def seat(r: Dict[str, Any]) -> int:
        return focal_seat(r, key)

    pay = lambda r: float(r["payments"][seat(r)])
    won = lambda r: 1.0 if r["winner"] == seat(r) else 0.0
    dealt_in = lambda r: 1.0 if (r["winner"] is not None and r["discarder"] == seat(r)) else 0.0
    selfdrawn = lambda r: 1.0 if (r["winner"] == seat(r) and r["discarder"] is None) else 0.0
    drawn = lambda r: 1.0 if r["winner"] is None else 0.0
    limit = lambda r: 1.0 if (r["winner"] == seat(r) and r["faan"] >= faan_cap) else 0.0

    games = len(records)
    wins = [r for r in records if r["winner"] == seat(r)]
    out: Dict[str, Any] = {
        "games": games,
        "deals": len({r["deal"] for r in records}),
        "points_per_hand": mean_ci(per_deal(records, pay)),
        "win_rate": mean_ci(per_deal(records, won)),
        "deal_in_rate": mean_ci(per_deal(records, dealt_in)),
        "self_draw_win_rate": mean_ci(per_deal(records, selfdrawn)),
        "draw_rate": mean_ci(per_deal(records, drawn)),
        "limit_hand_rate": mean_ci(per_deal(records, limit)),
        "wins": len(wins),
        "limit_hands": sum(1 for r in wins if r["faan"] >= faan_cap),
        "average_win_points": (sum(r["payments"][seat(r)] for r in wins) / len(wins)) if wins else None,
        "average_win_faan": (sum(r["faan"] for r in wins) / len(wins)) if wins else None,
        "decisions": sum(r["decisions"][seat(r)] for r in records),
    }
    faults: Dict[str, int] = {}
    for r in records:
        for k, n in r["faults"][seat(r)].items():
            faults[k] = faults.get(k, 0) + n
    out["faults"] = faults
    return out


# --- head to head and Bradley-Terry ------------------------------------------------------------


def team_outcome(payment: float) -> float:
    """1 if the team won the hand, 0 if it lost, 0.5 for a draw or a hand that nets to nothing."""
    if payment > 0:
        return 1.0
    if payment < 0:
        return 0.0
    return 0.5


def bradley_terry(names: Sequence[str], wins: Dict[Tuple[str, str], float], iterations: int = 500) -> Dict[str, float]:
    """Bradley-Terry strengths by the MM algorithm (Hunter, 2004).

    ``wins[(a, b)]`` is how many games a beat b (ties count half to each side). Returns a rating on
    the Elo scale (400 / ln 10 per natural-log unit), centred so the ratings average to zero.
    """
    n = len(names)
    idx = {nm: i for i, nm in enumerate(names)}
    w = [[0.0] * n for _ in range(n)]
    for (a, b), v in wins.items():
        w[idx[a]][idx[b]] += v
    p = [1.0] * n
    total_wins = [sum(w[i]) for i in range(n)]
    for _ in range(iterations):
        new = []
        for i in range(n):
            denom = 0.0
            for j in range(n):
                if i == j:
                    continue
                games = w[i][j] + w[j][i]
                if games:
                    denom += games / (p[i] + p[j])
            # A bot that never lost (or never won) has an unbounded rating; the floor keeps it finite.
            new.append(max(total_wins[i], 0.5) / denom if denom else p[i])
        geo = math.exp(sum(math.log(x) for x in new) / n)
        new = [x / geo for x in new]
        if max(abs(a - b) for a, b in zip(new, p)) < 1e-10:
            p = new
            break
        p = new
    scale = 400.0 / math.log(10)
    return {nm: scale * math.log(p[idx[nm]]) for nm in names}


def bootstrap_bt(
    names: Sequence[str],
    pair_deals: Dict[Tuple[str, str], List[Tuple[float, float]]],
    resamples: int = 500,
    seed: int = 20260101,
) -> Dict[str, Any]:
    """Ratings with 95% intervals, resampling whole deals within each pair.

    ``pair_deals[(a, b)]`` has one ``(a_points, games)`` per deal: the points ``a`` scored against
    ``b`` summed over the deal's games and how many games that is. Here ``a_points`` is the
    deal's total of 1/0.5/0 outcomes for a, so b's is ``games - a_points``.
    """
    def fit(sample: Dict[Tuple[str, str], List[Tuple[float, float]]]) -> Dict[str, float]:
        wins: Dict[Tuple[str, str], float] = {}
        for (a, b), deals in sample.items():
            a_pts = sum(d[0] for d in deals)
            g = sum(d[1] for d in deals)
            wins[(a, b)] = a_pts
            wins[(b, a)] = g - a_pts
        return bradley_terry(names, wins)

    point = fit(pair_deals)
    rng = Rng(seed)
    draws: Dict[str, List[float]] = {nm: [] for nm in names}
    for _ in range(resamples):
        sample = {}
        for pair, deals in pair_deals.items():
            n = len(deals)
            sample[pair] = [deals[rng.randrange(n)] for _ in range(n)]
        r = fit(sample)
        for nm in names:
            draws[nm].append(r[nm])
    out: Dict[str, Any] = {}
    for nm in names:
        xs = sorted(draws[nm])
        lo = xs[int(0.025 * (len(xs) - 1))]
        hi = xs[int(round(0.975 * (len(xs) - 1)))]
        out[nm] = {"rating": point[nm], "ci95": [lo, hi]}
    return out


def shared_ranks(rows: Dict[str, Dict[str, Any]], higher_is_better: bool = True) -> Dict[str, int]:
    """Rank 1 + the number of rows whose interval is entirely better. Overlapping rows share a rank."""
    out: Dict[str, int] = {}
    for a, ra in rows.items():
        better = 0
        for b, rb in rows.items():
            if a == b:
                continue
            if higher_is_better:
                if rb["ci95"][0] > ra["ci95"][1]:
                    better += 1
            else:
                if rb["ci95"][1] < ra["ci95"][0]:
                    better += 1
        out[a] = 1 + better
    return out
