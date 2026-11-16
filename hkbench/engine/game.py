"""The game engine: one Hong Kong Mahjong hand, with every physical tile tracked.

API:
  new_game / current_actor / legal_actions / apply_action
  terminal_result / serialize_replay / replay / check_invariants

The engine knows everything. What a player is allowed to see is built by ``hkbench.view``.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from hkbench.engine.actions import (
    CHOW_PATTERNS,
    Action,
    ActionKind,
    action_from_id,
    added_kong_action,
    chow_action,
    concealed_kong_action,
    discard_action,
)
from hkbench.engine.profile import RulesProfile
from hkbench.engine.tile_instance import (
    STANDARD_INSTANCES,
    TileInstance,
    TileLocation,
    type_code,
    validate_supplied_wall,
)
from hkbench.engine.types import (
    NUM_ACTIONS,
    Meld,
    MeldKind,
    Phase,
    PlayerState,
    WinSource,
)
from hkbench.engine.scorer import can_declare_win, score_hand
from hkbench.engine.win import can_win_structurally
from hkbench.engine.game_types import (
    ChanceOutcome,
    DrawKind,
    GameEventKind,
    GameEventV2,
    InvariantReport,
    ReplayActionV2,
    ReplayV2,
    TerminalResult,
)


@dataclass
class PendingOffer:
    tile: int
    from_seat: int
    instance_id: int | None = None
    rob_kong: bool = False


@dataclass
class GameState:
    """Complete round state, hidden tiles included."""

    profile: RulesProfile
    players: list[PlayerState]
    # Physical wall as instance ids; live front grows via wall_front, rear via wall_rear
    wall_order: list[int]
    wall_front: int = 0
    wall_rear: int = 144  # exclusive end index for rear draws (decrement)
    locations: list[TileLocation] = field(default_factory=list)
    # Physical river instance ids per seat (claimed tiles removed)
    river: list[list[int]] = field(default_factory=lambda: [[] for _ in range(4)])
    # Ordered discard history (type + seat) retained even after claims
    discard_history: list[tuple[int, int]] = field(default_factory=list)
    # Concealed hand as instance ids per seat (bonus never here)
    concealed_ids: list[list[int]] = field(default_factory=lambda: [[] for _ in range(4)])
    # Meld instance ids parallel to PlayerState.melds
    meld_ids: list[list[list[int]]] = field(default_factory=lambda: [[] for _ in range(4)])
    flower_ids: list[list[int]] = field(default_factory=lambda: [[] for _ in range(4)])
    phase: Phase = Phase.DEAL
    current_player: int = 0
    dealer: int = 0
    prevailing_wind: int = 0
    turn: int = 0
    last_draw: int | None = None
    last_draw_instance: int | None = None
    last_draw_kind: DrawKind | None = None
    offer: PendingOffer | None = None
    pending_reactions: dict[int, int] = field(default_factory=dict)
    reaction_eligible: list[int] = field(default_factory=list)
    events: list[GameEventV2] = field(default_factory=list)
    replay_actions: list[ReplayActionV2] = field(default_factory=list)
    seed: int = 0
    chance: ChanceOutcome = field(default_factory=lambda: ChanceOutcome(mode="sampled_wall", seed=0))
    after_kong: bool = False
    after_double_kong: bool = False
    first_turn: bool = True
    east_discarded: bool = False
    terminal: TerminalResult | None = None
    # Parallel to ``discard_history``: the physical tile behind each discard, so a view can say
    # which discards were later claimed into a meld.
    discard_instances: List[int] = field(default_factory=list)

    # --- construction ---
    @classmethod
    def new_game(
        cls,
        ruleset: RulesProfile,
        seed: int = 0,
        supplied_wall: Optional[List[int]] = None,
        dealer: int = 0,
        prevailing_wind: int = 0,
    ) -> "GameState":
        """Deal one hand.

        The wall is a permutation of the 144 tile instances. When none is supplied it is
        made from ``seed`` by the bench's own shuffle (``hkbench.seeds.wall_for_seed``), so a
        seed means the same deal on every Python version.
        """
        if ruleset is None:
            raise ValueError("new_game needs a rules profile")
        profile = ruleset
        if supplied_wall is None:
            from hkbench.seeds import wall_for_seed

            supplied_wall = wall_for_seed(seed)
        wall = validate_supplied_wall(supplied_wall)
        chance = ChanceOutcome(mode="supplied_wall", seed=seed, wall_instance_ids=tuple(wall))
        players = [PlayerState(seat=(i - dealer) % 4) for i in range(4)]
        locations = [TileLocation.LIVE_WALL] * 144
        state = cls(
            profile=profile,
            players=players,
            wall_order=wall,
            wall_front=0,
            wall_rear=144,
            locations=locations,
            seed=seed or 0,
            chance=chance,
            dealer=dealer,
            prevailing_wind=prevailing_wind,
            current_player=dealer,
        )
        state._deal()
        return state

    def clone(self) -> GameState:
        return copy.deepcopy(self)

    # --- queries ---
    def is_terminal(self) -> bool:
        return self.phase == Phase.TERMINAL

    def current_actor(self) -> int | str | None:
        if self.phase == Phase.TERMINAL:
            return "terminal"
        if self.phase == Phase.SELF_ACTION:
            return self.current_player
        if self.phase == Phase.REACTION:
            for s in self.reaction_eligible:
                if s not in self.pending_reactions:
                    return s
            return None
        return None

    def wall_remaining(self) -> int:
        return max(0, self.wall_rear - self.wall_front)

    def legal_actions(self, player: int | None = None) -> list[int]:
        actor = self.current_actor() if player is None else player
        if actor is None or actor == "terminal" or self.is_terminal():
            return []
        assert isinstance(actor, int)
        mask = self.legal_mask(actor)
        return [i for i, v in enumerate(mask) if v]

    def legal_mask(self, player: int) -> list[bool]:
        mask = [False] * NUM_ACTIONS
        if self.phase == Phase.SELF_ACTION and player == self.current_player:
            pl = self.players[player]
            if self._can_self_win(player):
                mask[1] = True
            for t in range(34):
                if pl.concealed[t] == 4:
                    mask[concealed_kong_action(t)] = True
                if pl.concealed[t] >= 1 and any(
                    m.kind == MeldKind.PONG and m.tiles[0] == t for m in pl.melds
                ):
                    mask[added_kong_action(t)] = True
            for t in range(34):
                if pl.concealed[t] > 0:
                    mask[discard_action(t)] = True
        elif self.phase == Phase.REACTION and player in self.reaction_eligible:
            mask[0] = True
            assert self.offer is not None
            tile = self.offer.tile
            pl = self.players[player]
            if self._can_claim_win(player):
                mask[1] = True
            if not self.offer.rob_kong:
                if pl.concealed[tile] >= 2:
                    mask[57] = True
                if pl.concealed[tile] >= 3:
                    mask[58] = True
                if player == (self.offer.from_seat + 1) % 4:
                    for idx, pat in enumerate(CHOW_PATTERNS):
                        if tile in pat and self._can_chow(player, idx, tile):
                            mask[chow_action(idx)] = True
        return mask

    def apply_action(self, action_id: int) -> GameState:
        if self.is_terminal():
            raise RuntimeError("terminal")
        actor = self.current_actor()
        if not isinstance(actor, int):
            raise RuntimeError("no actor")
        if action_id not in self.legal_actions(actor):
            raise ValueError(f"illegal action {action_id} for seat {actor}")
        # Snapshot for malformed-action safety is the caller's responsibility;
        # we only mutate after legality check.
        action = action_from_id(action_id)
        if self.phase == Phase.SELF_ACTION:
            self._apply_self(actor, action)
        elif self.phase == Phase.REACTION:
            self.submit_reaction(actor, action_id)
        else:
            raise RuntimeError(f"cannot act in phase {self.phase}")
        self.replay_actions.append(ReplayActionV2(actor=actor, action_id=action_id))
        return self

    def submit_reaction(self, player: int, action_id: int) -> None:
        if self.phase != Phase.REACTION:
            raise RuntimeError("not in reaction")
        if player not in self.reaction_eligible:
            raise ValueError("not eligible")
        if action_id not in self.legal_actions(player):
            raise ValueError("illegal reaction")
        self.pending_reactions[player] = action_id
        if action_id == 0:
            self.events.append(GameEventV2(GameEventKind.PASS, player))
        if len(self.pending_reactions) == len(self.reaction_eligible):
            self._resolve_reactions()

    @property
    def terminal_result(self) -> TerminalResult | None:
        return self.terminal

    @property
    def result(self) -> TerminalResult | None:
        return self.terminal

    def serialize_replay(self) -> ReplayV2:
        return ReplayV2(
            rules_hash=self.profile.rules_hash,
            rules_profile_id=self.profile.profile_id,
            chance=self.chance,
            initial_dealer=self.dealer,
            prevailing_wind=self.prevailing_wind,
            actions=list(self.replay_actions),
            events=list(self.events),
            terminal=self.terminal,
        )

    def check_invariants(self) -> InvariantReport:
        messages: list[str] = []
        # Every instance exactly one location
        loc_counts = {loc: 0 for loc in TileLocation}
        for iid, loc in enumerate(self.locations):
            loc_counts[loc] += 1
        # Reconstruct occupancy sets
        occupied: dict[int, TileLocation] = {}

        def claim(iid: int, loc: TileLocation, label: str) -> None:
            if iid in occupied:
                messages.append(f"duplicate occupancy {iid} ({occupied[iid].name} vs {label})")
            occupied[iid] = loc

        for idx in range(self.wall_front, self.wall_rear):
            claim(self.wall_order[idx], TileLocation.LIVE_WALL, "wall")
        for s in range(4):
            for iid in self.concealed_ids[s]:
                claim(iid, TileLocation.CONCEALED, f"concealed[{s}]")
            for meld in self.meld_ids[s]:
                for iid in meld:
                    claim(iid, TileLocation.EXPOSED_MELD, f"meld[{s}]")
            for iid in self.river[s]:
                claim(iid, TileLocation.RIVER, f"river[{s}]")
            for iid in self.flower_ids[s]:
                claim(iid, TileLocation.FLOWER_AREA, f"flower[{s}]")

        if len(occupied) != 144 and self.phase != Phase.DEAL:
            # During mid-game all 144 must be accounted; wall slice + areas
            missing = set(range(144)) - set(occupied)
            # Tiles already drawn past rear or before front that aren't placed are bugs
            if missing:
                # Allow nothing missing
                messages.append(f"unaccounted instances: {sorted(missing)[:8]}...")

        # Type counts from instances ≤ 4 / bonus ≤ 1
        type_counts = [0] * 34
        bonus_counts = [0] * 8
        for iid in occupied:
            inst = STANDARD_INSTANCES[iid]
            if inst.is_bonus:
                bonus_counts[inst.tile_type] += 1
            else:
                type_counts[inst.tile_type] += 1
        for t, n in enumerate(type_counts):
            if n > 4:
                messages.append(f"type {t} physical count {n}")
        for b, n in enumerate(bonus_counts):
            if n > 1:
                messages.append(f"bonus {b} duplicated")

        # PlayerState counts must match concealed instance types
        for s in range(4):
            counts = [0] * 34
            for iid in self.concealed_ids[s]:
                inst = STANDARD_INSTANCES[iid]
                if inst.is_bonus:
                    messages.append(f"bonus in concealed seat {s}")
                else:
                    counts[inst.tile_type] += 1
            if counts != self.players[s].concealed:
                messages.append(f"concealed count mismatch seat {s}")

        # Every claimed meld must trace to a real prior discard.
        #
        # `_apply_claim` removes the claimed instance from the discarder's physical river but
        # deliberately leaves `discard_history` intact, so history is the complete record of
        # what was ever discarded and by whom. A chow/pong/exposed-kong meld therefore has to
        # be covered by a matching (from_seat, tile) entry in it. Multiplicity matters: two
        # melds claiming the same tile from the same seat need two such discards.
        #
        # Concealed kongs carry `from_seat is None` and are correctly skipped. Added kongs
        # upgrade a pong in place and preserve the original `from_seat` (`:659`), so they
        # still map to the single discard that started the pong.
        #
        # Until now this was guarded only by the `RuntimeError` in `_apply_claim`, which fires
        # only when the instance id AND the type fallback both miss. A meld whose claimed tile
        # did not correspond to the offer would otherwise pass every gate.
        history_pairs: dict[tuple[int, int], int] = {}
        for hist_seat, hist_tile in self.discard_history:
            key = (hist_seat, hist_tile)
            history_pairs[key] = history_pairs.get(key, 0) + 1
        for s in range(4):
            for meld in self.players[s].melds:
                if meld.from_seat is None or meld.claimed_tile is None:
                    continue
                key = (meld.from_seat, meld.claimed_tile)
                remaining = history_pairs.get(key, 0)
                if remaining <= 0:
                    messages.append(
                        f"meld seat {s} {meld.kind.name} claims tile {meld.claimed_tile} "
                        f"from seat {meld.from_seat} with no matching discard in history"
                    )
                else:
                    history_pairs[key] = remaining - 1

        if self.terminal is not None:
            if sum(self.terminal.payments) != 0:
                messages.append(f"payments not zero-sum: {self.terminal.payments}")

        if self.phase == Phase.SELF_ACTION:
            n = self.players[self.current_player].concealed_count()
            if n <= 0 or n > 14:
                messages.append(f"self-action hand size {n}")

        return InvariantReport(ok=not messages, messages=messages)

    # --- internals ---
    def _inst(self, iid: int) -> TileInstance:
        return STANDARD_INSTANCES[iid]

    def _draw_front(self) -> int:
        if self.wall_front >= self.wall_rear:
            raise RuntimeError("wall empty")
        iid = self.wall_order[self.wall_front]
        self.wall_front += 1
        return iid

    def _draw_rear(self) -> int:
        if self.wall_front >= self.wall_rear:
            raise RuntimeError("wall empty")
        self.wall_rear -= 1
        return self.wall_order[self.wall_rear]

    def _deal(self) -> None:
        for _ in range(13):
            for s in range(4):
                seat = (self.dealer + s) % 4
                self._give_instance(seat, self._draw_front(), DrawKind.ORDINARY, during_deal=True)
        self._replace_flowers_until_stable(during_deal=True)
        self.events.append(GameEventV2(GameEventKind.DEAL, self.dealer))
        self.phase = Phase.DRAW
        self.current_player = self.dealer
        self._draw_for_current(DrawKind.ORDINARY)

    def _give_instance(
        self,
        seat: int,
        iid: int,
        draw_kind: DrawKind,
        *,
        during_deal: bool = False,
    ) -> None:
        inst = self._inst(iid)
        if inst.is_bonus:
            self.locations[iid] = TileLocation.FLOWER_AREA
            self.flower_ids[seat].append(iid)
            self.players[seat].flowers.append(inst.tile_type)
            self.events.append(
                GameEventV2(
                    GameEventKind.FLOWER,
                    seat,
                    tile_type=inst.tile_type,
                    instance_id=iid,
                    draw_kind=draw_kind,
                )
            )
            # Seven/eight-flower instant wins are profile-gated. hk_3faan_v2 sets
            # both flags true, so its behaviour is unchanged; hk_nofaan_v1 turns
            # the deal-time check off.
            flower_rules = self.profile.data.get("flower_rules", {})
            check_flower_win = bool(
                flower_rules.get("check_seven_eight_during_deal", True)
                if during_deal
                else flower_rules.get("check_seven_eight_during_replacement", True)
            )
            if check_flower_win:
                if len(self.players[seat].flowers) >= 8:
                    self._win(seat, WinSource.FLOWER_EIGHT, None, winning_tile=None)
                    return
                if len(self.players[seat].flowers) >= 7:
                    self._win(seat, WinSource.FLOWER_SEVEN, None, winning_tile=None)
                    return
        else:
            self.locations[iid] = TileLocation.CONCEALED
            self.concealed_ids[seat].append(iid)
            self.players[seat].concealed[inst.tile_type] += 1
            if not during_deal:
                self.last_draw = inst.tile_type
                self.last_draw_instance = iid
                self.last_draw_kind = draw_kind
                self.events.append(
                    GameEventV2(
                        GameEventKind.DRAW,
                        seat,
                        tile_type=inst.tile_type,
                        instance_id=iid,
                        draw_kind=draw_kind,
                    )
                )

    def _replace_flowers_until_stable(self, *, during_deal: bool) -> None:
        changed = True
        while changed and not self.is_terminal():
            changed = False
            for seat in range(4):
                while (
                    not self.is_terminal()
                    and self.players[seat].concealed_count() < 13
                    and self.wall_remaining() > 0
                ):
                    iid = self._draw_rear()
                    before = len(self.players[seat].flowers)
                    self._give_instance(
                        seat, iid, DrawKind.FLOWER_REPLACEMENT, during_deal=during_deal
                    )
                    changed = True
                    if self.is_terminal():
                        return
                    # If it was a flower, loop continues because concealed_count still low
                    if len(self.players[seat].flowers) == before:
                        # regular tile filled a slot
                        break

    def _draw_for_current(self, kind: DrawKind) -> None:
        if self.is_terminal():
            return
        if self.wall_remaining() <= 0:
            self._exhaustive()
            return
        seat = self.current_player
        # Ordinary draws from front; replacements from rear
        while not self.is_terminal():
            if self.wall_remaining() <= 0:
                self._exhaustive()
                return
            iid = self._draw_rear() if kind != DrawKind.ORDINARY else self._draw_front()
            inst = self._inst(iid)
            if inst.is_bonus:
                self._give_instance(seat, iid, kind)
                if self.is_terminal():
                    return
                # Flower always requires rear replacement next
                kind = DrawKind.FLOWER_REPLACEMENT
                continue
            self._give_instance(seat, iid, kind)
            self.phase = Phase.SELF_ACTION
            return

    def _take_concealed_of_type(self, seat: int, tile: int, n: int) -> list[int]:
        taken: list[int] = []
        remaining: list[int] = []
        for iid in self.concealed_ids[seat]:
            inst = self._inst(iid)
            if not inst.is_bonus and inst.tile_type == tile and len(taken) < n:
                taken.append(iid)
            else:
                remaining.append(iid)
        if len(taken) != n:
            raise RuntimeError(f"cannot take {n} of type {tile} from seat {seat}")
        self.concealed_ids[seat] = remaining
        self.players[seat].concealed[tile] -= n
        return taken

    def _apply_self(self, seat: int, action: Action) -> None:
        pl = self.players[seat]
        if action.kind == ActionKind.WIN:
            self._win(
                seat,
                WinSource.SELF_DRAW,
                None,
                winning_tile=self.last_draw,
                last_tile=self.wall_remaining() == 0,
                after_kong=self.after_kong,
                after_double_kong=self.after_double_kong,
                heavenly=self._is_heavenly(seat),
            )
            return
        if action.kind == ActionKind.CONCEALED_KONG:
            t = action.tile
            assert t is not None and pl.concealed[t] == 4
            ids = self._take_concealed_of_type(seat, t, 4)
            for iid in ids:
                self.locations[iid] = TileLocation.EXPOSED_MELD
            pl.melds.append(Meld(MeldKind.CONCEALED_KONG, (t, t, t, t)))
            self.meld_ids[seat].append(ids)
            self.events.append(
                GameEventV2(GameEventKind.CONCEALED_KONG, seat, tile_type=t)
            )
            was_after = self.after_kong
            self.after_kong = True
            self.after_double_kong = was_after
            self.phase = Phase.DRAW
            self._draw_for_current(DrawKind.KONG_REPLACEMENT)
            return
        if action.kind == ActionKind.ADDED_KONG:
            t = action.tile
            assert t is not None
            ids = self._take_concealed_of_type(seat, t, 1)
            for i, m in enumerate(pl.melds):
                if m.kind == MeldKind.PONG and m.tiles[0] == t:
                    pl.melds[i] = Meld(MeldKind.ADDED_KONG, (t, t, t, t), m.from_seat, t)
                    self.meld_ids[seat][i] = self.meld_ids[seat][i] + ids
                    for iid in ids:
                        self.locations[iid] = TileLocation.EXPOSED_MELD
                    break
            self.events.append(GameEventV2(GameEventKind.ADDED_KONG, seat, tile_type=t))
            self.offer = PendingOffer(tile=t, from_seat=seat, rob_kong=True)
            self._open_reaction(exclude=seat)
            return
        if action.kind == ActionKind.DISCARD:
            t = action.tile
            assert t is not None and pl.concealed[t] > 0
            ids = self._take_concealed_of_type(seat, t, 1)
            iid = ids[0]
            self.locations[iid] = TileLocation.RIVER
            self.river[seat].append(iid)
            self.discard_history.append((seat, t))
            self.discard_instances.append(iid)
            self.last_draw = None
            self.last_draw_instance = None
            self.last_draw_kind = None
            self.after_kong = False
            self.after_double_kong = False
            self.events.append(
                GameEventV2(
                    GameEventKind.DISCARD, seat, tile_type=t, instance_id=iid
                )
            )
            if seat == self.dealer and self.first_turn:
                self.east_discarded = True
            self.turn += 1
            self.offer = PendingOffer(
                tile=t, from_seat=seat, instance_id=iid, rob_kong=False
            )
            self._open_reaction(exclude=seat)
            return
        raise RuntimeError(f"unhandled self action {action}")

    def _open_reaction(self, exclude: int) -> None:
        self.pending_reactions = {}
        assert self.offer is not None
        self.phase = Phase.REACTION
        eligible: list[int] = []
        for s in range(4):
            if s == exclude:
                continue
            self.reaction_eligible = [s]
            mask = self.legal_mask(s)
            if any(mask[i] for i in range(1, NUM_ACTIONS)):
                eligible.append(s)
        self.reaction_eligible = eligible
        if not self.reaction_eligible:
            self._resolve_reactions()

    def _resolve_reactions(self) -> None:
        assert self.offer is not None
        offer = self.offer
        wins: list[int] = []
        pong_or_kong: list[tuple[int, str]] = []
        chows: list[tuple[int, int]] = []
        for s, aid in self.pending_reactions.items():
            act = action_from_id(aid)
            if act.kind == ActionKind.WIN:
                wins.append(s)
            elif act.kind == ActionKind.KONG:
                pong_or_kong.append((s, "kong"))
            elif act.kind == ActionKind.PONG:
                pong_or_kong.append((s, "pong"))
            elif act.kind == ActionKind.CHOW:
                chows.append((s, act.chow_index or 0))

        def seat_dist(s: int) -> int:
            return (s - offer.from_seat) % 4

        if wins:
            winner = min(wins, key=seat_dist)
            src = WinSource.ROB_KONG if offer.rob_kong else WinSource.DISCARD
            earthly = (
                offer.from_seat == self.dealer
                and winner != self.dealer
                and self.east_discarded
                and self.turn <= 1
                and not offer.rob_kong
            )
            self._win(
                winner,
                src,
                offer.from_seat,
                winning_tile=offer.tile,
                last_tile=self.wall_remaining() == 0,
                earthly=earthly,
            )
            return

        if offer.rob_kong:
            self.offer = None
            self.pending_reactions = {}
            self.reaction_eligible = []
            was_after = self.after_kong
            self.after_kong = True
            self.after_double_kong = was_after
            self.current_player = offer.from_seat
            self.phase = Phase.DRAW
            self._draw_for_current(DrawKind.KONG_REPLACEMENT)
            return

        # Pong and Kong share one priority class — nearest seat wins regardless of kind
        claim_seat = None
        claim_kind = None
        chow_idx = None
        if pong_or_kong:
            claim_seat, claim_kind = min(pong_or_kong, key=lambda x: seat_dist(x[0]))
        elif chows:
            claim_seat, chow_idx = min(chows, key=lambda x: seat_dist(x[0]))
            claim_kind = "chow"

        if claim_seat is None:
            self.offer = None
            self.pending_reactions = {}
            self.reaction_eligible = []
            self.first_turn = False
            self.current_player = (offer.from_seat + 1) % 4
            self.phase = Phase.DRAW
            self._draw_for_current(DrawKind.ORDINARY)
            return

        self._apply_claim(claim_seat, claim_kind, offer, chow_idx)

    def _apply_claim(
        self,
        seat: int,
        kind: str | None,
        offer: PendingOffer,
        chow_idx: int | None,
    ) -> None:
        tile = offer.tile
        from_seat = offer.from_seat
        # Remove claimed tile from physical river (history retained)
        if offer.instance_id is not None and offer.instance_id in self.river[from_seat]:
            self.river[from_seat].remove(offer.instance_id)
            claimed_id = offer.instance_id
        else:
            # Fallback: pop last matching type from discarder's river
            claimed_id = None
            for iid in reversed(self.river[from_seat]):
                if self._inst(iid).tile_type == tile:
                    self.river[from_seat].remove(iid)
                    claimed_id = iid
                    break
            if claimed_id is None:
                raise RuntimeError("claimed tile missing from river")

        pl = self.players[seat]
        if kind == "pong":
            ids = self._take_concealed_of_type(seat, tile, 2) + [claimed_id]
            for iid in ids:
                self.locations[iid] = TileLocation.EXPOSED_MELD
            pl.melds.append(Meld(MeldKind.PONG, (tile, tile, tile), from_seat, tile))
            self.meld_ids[seat].append(ids)
            self.events.append(GameEventV2(GameEventKind.PONG, seat, tile_type=tile, instance_id=claimed_id))
        elif kind == "kong":
            ids = self._take_concealed_of_type(seat, tile, 3) + [claimed_id]
            for iid in ids:
                self.locations[iid] = TileLocation.EXPOSED_MELD
            pl.melds.append(
                Meld(MeldKind.EXPOSED_KONG, (tile, tile, tile, tile), from_seat, tile)
            )
            self.meld_ids[seat].append(ids)
            self.events.append(GameEventV2(GameEventKind.KONG, seat, tile_type=tile, instance_id=claimed_id))
            self.offer = None
            self.pending_reactions = {}
            self.reaction_eligible = []
            self.current_player = seat
            self.after_kong = True
            self.phase = Phase.DRAW
            self._draw_for_current(DrawKind.KONG_REPLACEMENT)
            return
        elif kind == "chow":
            assert chow_idx is not None
            pat = CHOW_PATTERNS[chow_idx]
            ids = [claimed_id]
            for t in pat:
                if t != tile:
                    ids.extend(self._take_concealed_of_type(seat, t, 1))
            for iid in ids:
                self.locations[iid] = TileLocation.EXPOSED_MELD
            pl.melds.append(Meld(MeldKind.CHOW, pat, from_seat, tile))
            self.meld_ids[seat].append(ids)
            self.events.append(
                GameEventV2(GameEventKind.CHOW, seat, tile_type=tile, data=(chow_idx,))
            )
        self.offer = None
        self.pending_reactions = {}
        self.reaction_eligible = []
        self.current_player = seat
        self.last_draw = None
        self.phase = Phase.SELF_ACTION

    def _can_chow(self, seat: int, chow_idx: int, tile: int) -> bool:
        pat = CHOW_PATTERNS[chow_idx]
        if tile not in pat:
            return False
        pl = self.players[seat]
        for t in pat:
            if t == tile:
                continue
            if pl.concealed[t] < 1:
                return False
        return True

    def _is_heavenly(self, seat: int) -> bool:
        """The dealer wins on the first draw, before anyone has discarded."""
        return seat == self.dealer and self.turn == 0 and not self.discard_history

    def _can_self_win(self, seat: int) -> bool:
        pl = self.players[seat]
        if not can_win_structurally(pl.concealed, pl.melds):
            return False
        heavenly = self._is_heavenly(seat)
        return can_declare_win(
            pl,
            self.last_draw,
            WinSource.SELF_DRAW,
            seat_wind=pl.seat,
            prevailing_wind=self.prevailing_wind,
            after_kong=self.after_kong,
            after_double_kong=self.after_double_kong,
            heavenly=heavenly,
            last_tile=self.wall_remaining() == 0,
            profile=self.profile,
        )

    def _can_claim_win(self, seat: int) -> bool:
        assert self.offer is not None
        pl = self.players[seat]
        c = pl.concealed.copy()
        c[self.offer.tile] += 1
        trial = PlayerState(
            concealed=c, melds=list(pl.melds), flowers=list(pl.flowers), seat=pl.seat
        )
        src = WinSource.ROB_KONG if self.offer.rob_kong else WinSource.DISCARD
        earthly = (
            self.offer.from_seat == self.dealer
            and seat != self.dealer
            and self.turn <= 1
            and not self.offer.rob_kong
        )
        return can_declare_win(
            trial,
            self.offer.tile,
            src,
            seat_wind=pl.seat,
            prevailing_wind=self.prevailing_wind,
            discarder=self.offer.from_seat,
            earthly=earthly,
            last_tile=self.wall_remaining() == 0,
            profile=self.profile,
        )

    def _revert_added_kong_for_rob(self, winner_seat: int) -> None:
        """Undo the declarer's ADDED_KONG upgrade when the kong is robbed.

        ``_apply_self``'s ADDED_KONG branch appends the 4th physical instance onto the
        declarer's existing PONG. When another seat robs it, that instance belongs to
        the winner's hand, so the meld must shrink back to a 3-tile PONG and the
        instance must move across. Only the physical bookkeeping changes here:
        ``players[from_seat].concealed`` was already decremented by
        ``_take_concealed_of_type`` at declaration, and the declarer's hand
        legitimately stays one tile smaller after being robbed.
        """
        assert self.offer is not None
        from_seat = self.offer.from_seat
        tile = self.offer.tile
        declarer = self.players[from_seat]
        for i, meld in enumerate(declarer.melds):
            if meld.kind == MeldKind.ADDED_KONG and meld.tiles[0] == tile:
                ids = self.meld_ids[from_seat][i]
                robbed_id = ids[-1]  # the instance appended by the ADDED_KONG branch
                self.meld_ids[from_seat][i] = ids[:-1]
                declarer.melds[i] = Meld(
                    MeldKind.PONG, (tile, tile, tile), meld.from_seat, tile
                )
                self.locations[robbed_id] = TileLocation.WINNING_CONTEXT
                self.concealed_ids[winner_seat].append(robbed_id)
                return
        raise RuntimeError(
            f"rob-kong win on tile {tile} with no matching ADDED_KONG on seat {from_seat}"
        )

    def _win(
        self,
        seat: int,
        source: WinSource,
        discarder: int | None,
        *,
        winning_tile: int | None,
        **kwargs: Any,
    ) -> None:
        pl = self.players[seat]
        if source in (WinSource.DISCARD, WinSource.ROB_KONG) and self.offer:
            # Move claimed/offer tile into hand for scoring
            if self.offer.rob_kong:
                # The offered tile is not in a river — it is the 4th instance sitting in
                # the declarer's ADDED_KONG meld. Both sides of the move must happen
                # atomically: appending it to the winner without pulling it out of the
                # meld would trade a "concealed count mismatch" for a "duplicate
                # occupancy" / "type physical count 5" failure instead.
                self._revert_added_kong_for_rob(seat)
            elif self.offer.instance_id is not None:
                iid = self.offer.instance_id
                if iid in self.river[self.offer.from_seat]:
                    self.river[self.offer.from_seat].remove(iid)
                self.locations[iid] = TileLocation.WINNING_CONTEXT
                self.concealed_ids[seat].append(iid)
            pl.concealed[self.offer.tile] += 1
            winning_tile = self.offer.tile
        score = score_hand(
            pl,
            winning_tile=winning_tile,
            win_source=source,
            seat_wind=pl.seat,
            prevailing_wind=self.prevailing_wind,
            discarder=discarder,
            # ABSOLUTE seat, matching `discarder`. `pl.seat` is the seat WIND and differs
            # from the absolute index whenever the dealer is not seat 0.
            winner_seat=seat,
            profile=self.profile,
            **kwargs,
        )
        payments = list(score.payments)
        if sum(payments) != 0:
            # A scorer that loses or invents points is a bug in the engine. Stop the run.
            raise RuntimeError(f"settlement does not sum to zero: {payments}")
        self.events.append(
            GameEventV2(GameEventKind.WIN, seat, tile_type=winning_tile)
        )
        self.terminal = TerminalResult(
            cause="win",
            winner=seat,
            discarder=discarder,
            win_source=source,
            pattern_breakdown=[{"name": p.name, "faan": p.faan} for p in score.patterns],
            faan=score.capped_faan,
            payments=payments,
            score=score,
        )
        for i, p in enumerate(payments):
            self.players[i].score += p
        self.phase = Phase.TERMINAL
        self.offer = None

    def _exhaustive(self) -> None:
        self.events.append(GameEventV2(GameEventKind.EXHAUSTIVE, self.current_player))
        self.terminal = TerminalResult(
            cause="exhaustive",
            winner=None,
            discarder=None,
            win_source=None,
            pattern_breakdown=[],
            faan=0,
            payments=[0, 0, 0, 0],
            score=None,
        )
        self.phase = Phase.TERMINAL


def new_game(
    ruleset: RulesProfile,
    seed: int = 0,
    supplied_wall: Optional[List[int]] = None,
    dealer: int = 0,
    prevailing_wind: int = 0,
) -> GameState:
    return GameState.new_game(
        ruleset=ruleset,
        seed=seed,
        supplied_wall=supplied_wall,
        dealer=dealer,
        prevailing_wind=prevailing_wind,
    )


def replay(record: ReplayV2, profile: RulesProfile) -> GameState:
    """Rebuild a round from its physical wall and successfully applied actions.

    The replay is deliberately strict: the rules identity, acting seat, emitted
    events, and terminal result must all match the serialized record.
    """
    selected_profile = profile
    if record.rules_profile_id != selected_profile.profile_id:
        raise ValueError(
            f"replay rules profile mismatch: {record.rules_profile_id} != "
            f"{selected_profile.profile_id}"
        )
    if record.rules_hash != selected_profile.rules_hash:
        raise ValueError("replay rules hash mismatch")
    if record.chance.wall_instance_ids is None:
        raise ValueError("replay requires the complete physical wall")

    state = new_game(
        ruleset=selected_profile,
        seed=record.chance.seed,
        supplied_wall=list(record.chance.wall_instance_ids),
        dealer=record.initial_dealer,
        prevailing_wind=record.prevailing_wind,
    )
    for index, step in enumerate(record.actions):
        actor = state.current_actor()
        if actor != step.actor:
            raise ValueError(
                f"replay actor mismatch at action {index}: {actor} != {step.actor}"
            )
        state.apply_action(step.action_id)

    if state.events != record.events:
        raise ValueError("replay event stream mismatch")
    if state.terminal != record.terminal:
        raise ValueError("replay terminal result mismatch")
    # Preserve provenance: reconstruction uses the serialized physical wall,
    # but the replayed state still represents the original chance mode.
    state.chance = record.chance
    return state
