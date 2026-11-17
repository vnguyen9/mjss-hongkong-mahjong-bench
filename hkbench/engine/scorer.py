"""Faan scoring and payment settlement."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from hkbench.engine.profile import RulesProfile
from hkbench.engine.tiles import is_honor, is_suited, is_terminal_or_honor, seat_for_bonus, suit_of
from hkbench.engine.types import (
    Meld,
    MeldKind,
    PatternHit,
    PlayerState,
    ScoreResult,
    WinSource,
)
from hkbench.engine.win import (
    Decomposition,
    is_nine_gates,
    is_seven_pairs,
    is_thirteen_orphans,
    structural_wins,
)


def _all_meld_tiles(decomp: Decomposition, exposed: list[Meld]) -> list[tuple[str, tuple[int, ...]]]:
    melds: list[tuple[str, tuple[int, ...]]] = list(decomp.concealed_melds)
    for m in exposed:
        if m.kind == MeldKind.CHOW:
            melds.append(("chow", m.tiles))
        else:
            t = m.tiles[0]
            kind = "kong" if m.is_kong() else "pong"
            melds.append((kind, (t, t, t) if kind == "pong" else (t, t, t, t)))
    return melds


def _condition_hits(
    win_source: WinSource,
    last_tile: bool,
    after_kong: bool,
    after_double_kong: bool,
    profile: RulesProfile,
) -> List[PatternHit]:
    """The win-condition items that still count on a limit hand: Self-Drawn, Robbing a Kong,
    Last Tile from the Wall, and the kong replacement items."""
    hits: List[PatternHit] = []
    if win_source == WinSource.SELF_DRAW:
        hits.append(PatternHit("self_draw", profile.patterns["self_draw"]))
    if win_source == WinSource.ROB_KONG:
        hits.append(PatternHit("rob_kong", profile.patterns["rob_kong"]))
    if last_tile:
        hits.append(PatternHit("last_tile", profile.patterns["last_tile"]))
    if after_double_kong:
        hits.append(PatternHit("double_kong", profile.patterns["double_kong"]))
    elif after_kong:
        hits.append(PatternHit("kong_replacement", profile.patterns["kong_replacement"]))
    return hits


def _is_limit_name(name: str, profile: RulesProfile) -> bool:
    return name in profile.limit_hands


def score_hand(
    player: PlayerState,
    winning_tile: int | None,
    win_source: WinSource,
    seat_wind: int,
    prevailing_wind: int,
    discarder: int | None = None,
    *,
    winner_seat: int | None = None,
    last_tile: bool = False,
    after_kong: bool = False,
    after_double_kong: bool = False,
    heavenly: bool = False,
    earthly: bool = False,
    profile: RulesProfile | None = None,
) -> ScoreResult:
    """Score a completed hand. `player.concealed` must include the winning tile when applicable.

    ``winner_seat`` is the winner's ABSOLUTE seat index, in the same coordinate system as
    ``discarder``.

    ``PlayerState.seat`` is the seat WIND, not the absolute index: the engine builds players as
    ``PlayerState(seat=(i - dealer) % 4)``. Pass ``winner_seat`` whenever the dealer is not seat 0
    so the payment vector is written in absolute seats.

    Defaults to ``player.seat`` for callers that only score dealer-0 hands.
    """
    if profile is None:
        raise ValueError("score_hand needs a rules profile")
    if winner_seat is None:
        winner_seat = player.seat
    patterns: list[PatternHit] = []
    is_limit = False

    # Flower-only wins
    if win_source == WinSource.FLOWER_SEVEN:
        patterns.append(PatternHit("seven_flowers", profile.flower_patterns["seven_flowers"]))
        patterns.append(PatternHit("self_draw", profile.patterns["self_draw"]))
        return _finalize(patterns, False, win_source, winner_seat, discarder, profile, player.melds)
    if win_source == WinSource.FLOWER_EIGHT:
        patterns.append(PatternHit("eight_flowers", profile.flower_patterns["eight_flowers"]))
        return _finalize(patterns, True, win_source, winner_seat, discarder, profile, player.melds)

    concealed = player.concealed
    exposed = player.melds

    if is_thirteen_orphans(concealed) and not exposed:
        patterns.append(PatternHit("thirteen_orphans", profile.patterns["thirteen_orphans"]))
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return _finalize(patterns, True, win_source, winner_seat, discarder, profile, player.melds)

    if is_nine_gates(concealed) and not exposed:
        patterns.append(PatternHit("nine_gates", profile.patterns["nine_gates"]))
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return _finalize(patterns, True, win_source, winner_seat, discarder, profile, player.melds)

    decomps = structural_wins(concealed, exposed)
    # Seven Pairs is a second way to be complete, only where the table plays it.
    seven_pairs_win = profile.seven_pairs and not exposed and is_seven_pairs(concealed)
    if not decomps and not seven_pairs_win:
        return ScoreResult(
            patterns=[],
            total_faan=0,
            capped_faan=0,
            meets_minimum=False,
            is_limit=False,
            payments=[0, 0, 0, 0],
            win_source=win_source,
            winner=player.seat,
            discarder=discarder,
        )

    # Heaven/earth only after the hand is structurally complete
    if heavenly:
        patterns.append(PatternHit("heavenly_hand", profile.patterns["heavenly_hand"]))
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return _finalize(patterns, True, win_source, winner_seat, discarder, profile, player.melds)
    if earthly:
        patterns.append(PatternHit("earthly_hand", profile.patterns["earthly_hand"]))
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return _finalize(patterns, True, win_source, winner_seat, discarder, profile, player.melds)

    # Pick the decomposition that maximizes faan
    best: ScoreResult | None = None
    for decomp in decomps:
        hits = _score_decomp(
            decomp,
            player,
            win_source,
            seat_wind,
            prevailing_wind,
            last_tile=last_tile,
            after_kong=after_kong,
            after_double_kong=after_double_kong,
            profile=profile,
        )
        cand = _finalize(hits[0], hits[1], win_source, winner_seat, discarder, profile, player.melds)
        if best is None or cand.capped_faan > best.capped_faan:
            best = cand
    if seven_pairs_win:
        # The same tiles can also read as four sets and a pair (112233 445566 77), so Seven Pairs
        # competes with the ordinary readings and the richer one wins. It is compared on raw faan,
        # so two readings that both reach the cap still resolve to the richer one and name it. The
        # payment is the same either way.
        hits = _score_seven_pairs(
            player,
            win_source,
            seat_wind,
            last_tile=last_tile,
            after_kong=after_kong,
            after_double_kong=after_double_kong,
            profile=profile,
        )
        cand = _finalize(hits[0], hits[1], win_source, winner_seat, discarder, profile, player.melds)
        if best is None or cand.total_faan > best.total_faan:
            best = cand
    assert best is not None
    return best


def _score_seven_pairs(
    player: PlayerState,
    win_source: WinSource,
    seat_wind: int,
    *,
    last_tile: bool,
    after_kong: bool,
    after_double_kong: bool,
    profile: RulesProfile,
) -> tuple[list[PatternHit], bool]:
    """Score a Seven Pairs reading.

    Seven Pairs is worth ``patterns.seven_pairs`` and stacks with everything else that matches:
    the flush items, then how the hand was won, Fully Concealed and the flowers. There are no
    sets, so no set patterns apply.

    * One suit and no honours adds Full Flush, one suit plus honours adds Half Flush. They are
      added to the Seven Pairs value, not instead of it.
    * Only honours (the seven honour types, the only way to make it) is All Honours, a limit
      hand: it keeps just how the hand was won, then takes the cap.
    * Only terminals and honours scores Mixed Orphans at the Mixed Orphans value plus the
      All Pongs value. A Seven Pairs hand holds no pongs, so the rules file's bare Mixed Orphans
      value would undercount it; this keeps the value a player reads off the table.
    * All terminals without honours cannot be seven different pairs (there are only six
      terminals), so Pure Orphans cannot occur.
    """
    tiles = [t for t, n in enumerate(player.concealed) for _ in range(n)]
    suits = {suit_of(t) for t in tiles if suit_of(t) is not None}
    has_honor = any(is_honor(t) for t in tiles)

    if all(is_honor(t) for t in tiles):
        patterns = [PatternHit("all_honors", profile.patterns["all_honors"])]
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return patterns, True

    patterns = [PatternHit("seven_pairs", profile.patterns["seven_pairs"])]
    if all(is_terminal_or_honor(t) for t in tiles):
        patterns.append(
            PatternHit("mixed_orphans", profile.patterns["mixed_orphans"] + profile.patterns["all_pong"])
        )
    if len(suits) == 1 and not has_honor:
        patterns.append(PatternHit("pure_one_suit", profile.patterns["pure_one_suit"]))
    elif len(suits) == 1 and has_honor:
        patterns.append(PatternHit("mixed_one_suit", profile.patterns["mixed_one_suit"]))
    patterns.extend(
        _win_condition_patterns(
            player, win_source, seat_wind, last_tile, after_kong, after_double_kong,
            fully_concealed=True, profile=profile,
        )
    )
    return patterns, False


def _score_decomp(
    decomp: Decomposition,
    player: PlayerState,
    win_source: WinSource,
    seat_wind: int,
    prevailing_wind: int,
    *,
    last_tile: bool,
    after_kong: bool,
    after_double_kong: bool,
    profile: RulesProfile,
) -> tuple[list[PatternHit], bool]:
    patterns: list[PatternHit] = []
    melds = _all_meld_tiles(decomp, player.melds)
    pair = decomp.pair
    is_limit = False

    # Kong count / all kongs
    kong_count = sum(1 for m in player.melds if m.is_kong())
    # concealed kongs in decomp aren't separate if not declared — only declared melds
    if kong_count == 4:
        patterns.append(PatternHit("all_kongs", profile.patterns["all_kongs"]))
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return patterns, True

    kinds = [k for k, _ in melds]
    all_pong = all(k in ("pong", "kong") for k in kinds)
    all_chow = all(k == "chow" for k in kinds)
    # fully concealed: no open melds (concealed kong allowed)
    open_melds = [m for m in player.melds if m.kind not in (MeldKind.CONCEALED_KONG,)]
    fully_concealed = len(open_melds) == 0

    # Collect all tiles in hand for suit analysis
    tile_types: list[int] = []
    for k, tiles in melds:
        tile_types.extend(tiles[:3] if k != "kong" else tiles[:3])
    if pair >= 0:
        tile_types.extend([pair, pair])

    suits = {suit_of(t) for t in tile_types if suit_of(t) is not None}
    honors_only = all(is_honor(t) for t in tile_types)
    has_honor = any(is_honor(t) for t in tile_types)
    terminals_honors_only = all(is_terminal_or_honor(t) for t in tile_types)
    terminals_only = all(t in (0, 8, 9, 17, 18, 26) for t in tile_types)

    # Winds: great (limit 13) before all_honors (10)
    wind_pongs = [t for k, tiles in melds if k in ("pong", "kong") for t in [tiles[0]] if 27 <= t <= 30]
    wind_pair = pair if 27 <= pair <= 30 else None
    unique_wind_pongs = set(wind_pongs)
    if len(unique_wind_pongs) == 4:
        patterns.append(PatternHit("great_winds", profile.patterns["great_winds"]))
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return patterns, True
    if len(unique_wind_pongs) == 3 and wind_pair is not None and wind_pair not in unique_wind_pongs:
        patterns.append(PatternHit("small_winds", profile.patterns["small_winds"]))

    if honors_only:
        patterns.append(PatternHit("all_honors", profile.patterns["all_honors"]))
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return patterns, True
    if terminals_only and all_pong:
        patterns.append(PatternHit("pure_orphans", profile.patterns["pure_orphans"]))
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return patterns, True

    # four concealed pongs (坎坎糊) — after more specific limit hands
    if (
        all_pong
        and fully_concealed
        and not any(
            m.kind in (MeldKind.PONG, MeldKind.EXPOSED_KONG, MeldKind.ADDED_KONG, MeldKind.CHOW)
            for m in player.melds
        )
    ):
        patterns.append(PatternHit("four_concealed_pongs", profile.patterns["four_concealed_pongs"]))
        patterns.extend(_condition_hits(win_source, last_tile, after_kong, after_double_kong, profile))
        return patterns, True

    # Dragons
    dragon_pongs = [t for k, tiles in melds if k in ("pong", "kong") for t in [tiles[0]] if 31 <= t <= 33]
    dragon_pair = pair if 31 <= pair <= 33 else None
    unique_dragons = set(dragon_pongs)
    if len(unique_dragons) == 3:
        patterns.append(PatternHit("great_dragons", profile.patterns["great_dragons"]))
    elif len(unique_dragons) == 2 and dragon_pair is not None and dragon_pair not in unique_dragons:
        patterns.append(PatternHit("small_dragons", profile.patterns["small_dragons"]))

    # Suit patterns
    if len(suits) == 1 and not has_honor:
        patterns.append(PatternHit("pure_one_suit", profile.patterns["pure_one_suit"]))
    elif len(suits) == 1 and has_honor:
        patterns.append(PatternHit("mixed_one_suit", profile.patterns["mixed_one_suit"]))

    if all_pong:
        patterns.append(PatternHit("all_pong", profile.patterns["all_pong"]))
    if all_chow:
        patterns.append(PatternHit("common_hand", profile.patterns["common_hand"]))
    if terminals_honors_only and all_pong and not terminals_only:
        patterns.append(PatternHit("mixed_orphans", profile.patterns["mixed_orphans"]))

    # Dragon / wind pongs (value tiles)
    for t in unique_dragons:
        patterns.append(PatternHit("dragon_pong", profile.patterns["dragon_pong"]))
    for t in unique_wind_pongs:
        if t == 27 + seat_wind:
            patterns.append(PatternHit("seat_wind", profile.patterns["seat_wind"]))
        if t == 27 + prevailing_wind:
            patterns.append(PatternHit("prevailing_wind", profile.patterns["prevailing_wind"]))

    # Winning conditions and flowers (shared with the Seven Pairs reading)
    patterns.extend(
        _win_condition_patterns(
            player, win_source, seat_wind, last_tile, after_kong, after_double_kong,
            fully_concealed=fully_concealed, profile=profile,
        )
    )

    return patterns, is_limit


def _win_condition_patterns(
    player: PlayerState,
    win_source: WinSource,
    seat_wind: int,
    last_tile: bool,
    after_kong: bool,
    after_double_kong: bool,
    *,
    fully_concealed: bool,
    profile: RulesProfile,
) -> List[PatternHit]:
    """How the win arrived, Fully Concealed, and the flowers: the tail every reading shares."""
    hits: List[PatternHit] = []
    if win_source == WinSource.SELF_DRAW:
        hits.append(PatternHit("self_draw", profile.patterns["self_draw"]))
    if win_source == WinSource.ROB_KONG:
        hits.append(PatternHit("rob_kong", profile.patterns["rob_kong"]))
    if fully_concealed:
        hits.append(PatternHit("fully_concealed", profile.patterns["fully_concealed"]))
    if last_tile:
        hits.append(PatternHit("last_tile", profile.patterns["last_tile"]))
    if after_double_kong:
        hits.append(PatternHit("double_kong", profile.patterns["double_kong"]))
    elif after_kong:
        hits.append(PatternHit("kong_replacement", profile.patterns["kong_replacement"]))
    hits.extend(_flower_patterns(player.flowers, seat_wind, profile))
    return hits


def _flower_patterns(flowers: list[int], seat_wind: int, profile: RulesProfile) -> list[PatternHit]:
    hits: list[PatternHit] = []
    if not flowers:
        hits.append(PatternHit("no_flowers", profile.flower_patterns["no_flowers"]))
        return hits

    fl = [b for b in flowers if b < 4]
    se = [b for b in flowers if b >= 4]
    all_fl = len(set(fl)) == 4
    all_se = len(set(se)) == 4

    if all_fl:
        hits.append(PatternHit("all_flowers", profile.flower_patterns["all_flowers"]))
    else:
        for b in fl:
            if seat_for_bonus(b) == seat_wind:
                hits.append(PatternHit("seat_flower", profile.flower_patterns["seat_flower"]))
    if all_se:
        hits.append(PatternHit("all_seasons", profile.flower_patterns["all_seasons"]))
    else:
        for b in se:
            if seat_for_bonus(b) == seat_wind:
                hits.append(PatternHit("seat_season", profile.flower_patterns["seat_season"]))
    return hits


def _apply_exclusions(patterns: list[PatternHit], profile: RulesProfile, is_limit: bool) -> list[PatternHit]:
    names = {p.name for p in patterns}
    # If any limit hand present, drop wind/dragon/flower extras except the limit itself + win conditions that stack per profile
    limit_hit = [p for p in patterns if p.name in profile.limit_hands]
    if limit_hit or is_limit:
        keep = set(profile.limit_hands) | {"self_draw", "last_tile", "rob_kong", "kong_replacement", "double_kong"}
        # For limit, typically only the limit pattern counts (plus maybe win condition for heavenly etc.)
        patterns = [p for p in patterns if p.name in profile.limit_hands or p.name in ("self_draw", "rob_kong", "last_tile", "kong_replacement", "double_kong")]
        # Keep only highest limit if multiple
        limits = [p for p in patterns if p.name in profile.limit_hands]
        if limits:
            best = max(limits, key=lambda p: p.faan)
            patterns = [best] + [p for p in patterns if p.name not in profile.limit_hands]
        return patterns

    # Remove implied patterns
    remove: set[str] = set()
    for name, implied in profile.implied.items():
        if name in names:
            remove.update(implied)
    return [p for p in patterns if p.name not in remove]


def _finalize(
    patterns: list[PatternHit],
    is_limit: bool,
    win_source: WinSource,
    winner: int,
    discarder: int | None,
    profile: RulesProfile,
    melds: Sequence[Meld] = (),
) -> ScoreResult:
    patterns = _apply_exclusions(patterns, profile, is_limit)
    # Deduplicate identical pattern names that shouldn't stack (except dragon_pong etc. already separate hits)
    total = sum(p.faan for p in patterns)
    # great_dragons / small_dragons already include base; dragon_pong still stacks per Wikipedia
    capped = min(total, profile.faan_cap)
    meets = capped >= profile.minimum_faan
    payments = (
        settle_payments(capped, win_source, winner, discarder, profile)
        if meets
        else [0, 0, 0, 0]
    )
    return ScoreResult(
        patterns=patterns,
        total_faan=total,
        capped_faan=capped,
        meets_minimum=meets,
        is_limit=is_limit or any(p.name in profile.limit_hands for p in patterns),
        payments=payments,
        win_source=win_source,
        winner=winner,
        discarder=discarder,
    )



def settle_payments(
    faan: int,
    win_source: WinSource,
    winner: int,
    discarder: Optional[int],
    profile: RulesProfile,
) -> List[int]:
    """Return the net payment vector for seats 0..3 (absolute seat indexes).

    Discard win (and robbing a kong): the discarder pays the whole table value to the winner.
    Self-draw (and a flower win): the winner collects ``self_draw_multiplier`` times the table
    value, split as evenly as possible between the three others; any remainder is taken one
    point at a time from the seats after the winner, in turn order.
    """
    table = profile.payment_table
    base = table.get(faan, table[profile.faan_cap])
    pay = [0, 0, 0, 0]
    if win_source in (WinSource.SELF_DRAW, WinSource.FLOWER_SEVEN, WinSource.FLOWER_EIGHT):
        total = int(base * profile.self_draw_multiplier)
        each = total // 3
        rem = total - each * 3
        for s in range(4):
            if s != winner:
                pay[s] -= each
        i = 0
        while rem > 0:
            s = (winner + 1 + i) % 4
            if s != winner:
                pay[s] -= 1
                rem -= 1
            i += 1
        pay[winner] = -sum(pay)
    else:
        if discarder is None:
            raise ValueError("discarder required for discard/rob win")
        pay[discarder] = -base
        pay[winner] = base
    return pay


def can_declare_win(
    player: PlayerState,
    winning_tile: int | None,
    win_source: WinSource,
    seat_wind: int,
    prevailing_wind: int,
    **kwargs,
) -> bool:
    result = score_hand(player, winning_tile, win_source, seat_wind, prevailing_wind, **kwargs)
    return result.meets_minimum
