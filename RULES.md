# Rules

Three tables, one engine. This file is what each table plays, in full, and where `hk-hkma-v1` is **not** the HKMA rulebook.

The rulebook is the Hong Kong Mahjong Association's *Hong Kong Mahjong (Classical Mahjong)*, latest version 17 May 2023, pp.20 to 24 (score calculation, the faan list, the Faan-to-Score table). The numbers below were checked against it by hand.

## How a hand is played (every table)

* **13-tile Hong Kong Mahjong.** 144 tiles: 4 each of 27 suit tiles and 7 honour tiles, and 8 flowers and seasons. Four players. A winning hand is four melds and a pair, or Thirteen Orphans. Seven Pairs is not a hand in `hk-hkma-v1` or `hk-chicken-v1`.
* **One game is one hand.** The bench plays single hands. Each deal fixes the dealer and the prevailing wind (`dealer = deal number mod 4`, `prevailing wind = (deal number / 4) mod 4`). There is no dealer rotation, no match score and no penalty system.
* **The deal.** The dealer is East and discards first, after drawing a 14th tile. Each seat is dealt 13 tiles.
* **Opening flowers.** After the deal, flowers and seasons in the opening hands are shown and replaced with tiles from the back of the wall. The dealer replaces first, then the next seat, and so on in turn order. Each seat keeps replacing until it holds no flower (a replacement that is a flower is replaced again), and the rounds repeat until no seat holds one.
* **Flowers drawn in play.** A flower drawn later, from the wall or as a kong replacement, is shown and replaced at once from the back of the wall.
* **Turns.** Draw, then win, declare a kong, or discard. Concealed and added kongs are declared on your own turn and draw a replacement from the back of the wall.
* **Claims on a discard.** Win beats pong and kong; pong and kong beat chow. A chow can only be claimed from the player who acts just before you. Two players who can win on the same tile: only the nearest after the discarder wins. A fourth tile added to a pong can be robbed by a player who wins on it.
* **No dead wall.** The hand ends in a draw when there is no tile left to draw. A draw pays nothing. The very last discard can still be claimed.
* **Winning needs the minimum faan.** The win action is only offered when the hand is complete and reaches the table's minimum (3 faan on HKMA and House, 0 on `hk-chicken-v1`). A bot cannot make a false win.
* **Counting.** The hand is scored in the way that gives the most faan. Every faan item that applies is counted (rulebook: the Total Compound Principle), except where a limit hand replaces them. The total is capped, then looked up in the payment table.
* **Concealed kongs are shown** to every player in the protocol (at a real table they are placed in the meld area).

## `hk-hkma-v1`: HKMA Classical (the headline table)

Derived from the HKMA rules profile (`hkma_classical_v1`, rules hash 37da1ff2ce3d1424) with one change: the seven and eight flower instant wins are switched off, because the rulebook has no flower win. The rules file is `tables/hk-hkma-v1/rules.json`.

<!-- rules:hk-hkma-v1:begin -->
Minimum to win: **3 faan**. Cap: **10 faan**.

| Faan item | Faan |
|---|---|
| All Sequences | 1 |
| Closed Hand | 1 |
| Self-Drawn | 1 |
| Triplet of Dragons (each triplet) | 1 |
| Triplet of the player's own wind | 1 |
| Triplet of the prevailing wind | 1 |
| All Terminals and Honours (all triplets) | 1 |
| Robbing a Kong | 1 |
| Win on the replacement tile after a kong | 1 |
| Last Tile from the Wall | 1 |
| Semi-Flush (one suit plus honours) | 3 |
| All Triplets | 3 |
| Small Dragons | 3 |
| Big Dragons | 5 |
| Flush (one suit, no honours) | 7 |
| All Honours \* | 10 |
| Small Winds | 10 |
| Big Winds \* | 10 |
| All Concealed Triplets \* | 10 |
| All Quads \* | 10 |
| All Terminals \* | 10 |
| Bless of Heaven (dealer wins on the first draw) \* | 10 |
| Bless of Earth (win on the dealer's first discard) \* | 10 |
| Thirteen Orphans \* | 10 |
| After Consecutive Kan | 10 |
| Nine Gates \* | 10 |

\* Limit hand. Only this item counts, plus Self-Drawn, Last Tile from the Wall, Robbing a Kong and the kong items.

| Flower item | Faan |
|---|---|
| Flower matching the player's seat | 0 |
| Season matching the player's seat | 0 |
| No flowers or seasons | 0 |
| All four flowers | 0 |
| All four seasons | 0 |
| Seven flowers or seasons (instant win) | 0 |
| Eight flowers and seasons (instant win) | 0 |

| Faan | Discarder pays everything | Self-drawn: each of the three pays | Self-drawn: winner collects |
|---|---|---|---|
| 3 | 8 | 4 | 12 |
| 4 | 16 | 8 | 24 |
| 5 | 24 | 12 | 36 |
| 6 | 32 | 16 | 48 |
| 7 | 48 | 24 | 72 |
| 8 | 64 | 32 | 96 |
| 9 | 96 | 48 | 144 |
| 10 | 128 | 64 | 192 |
<!-- rules:hk-hkma-v1:end -->

* **Payout.** The discarder pays the whole hand ("Full Liability of Chuck"). On a self-draw, the winner collects 1.5 times the discard value, split equally by the other three. The same applies to a win by robbing a kong, which is paid by the player who added the tile.
* **Points are one quarter of the rulebook's.** The rulebook's table is 32, 64, 96, 128, 192, 256, 384, 512 for 3 to 10 faan, and half of that from each of three players when self-drawn. Here it is 8, 16, 24, 32, 48, 64, 96, 128. Every ratio is the same. Multiply by 4 for rulebook points.
* **Flowers score nothing.** They are still drawn and replaced, and they still shorten the wall.
* **Limit hands.** Every ceiling hand pays the cap (10 faan). A limit hand still counts Self-Drawn, Last Tile from the Wall, Robbing a Kong and the kong items, and the total is then capped, so a self-drawn limit hand is 11 on paper and pays 10. A hand worth more than 10 faan on paper pays 10.
* **Small Winds and After Consecutive Kan** are 10 faan items in the rulebook. The engine does not flag them as limit hands, so other faan can be counted beside them. Because the total is capped at 10, the payment is the same.

### Where `hk-hkma-v1` is not the rulebook

This is the honest list. Each item is pinned by a test in `tests/test_scoring.py` (`KnownGaps`), so it cannot be fixed by accident: fixing one means a new table version.

1. **No 包 (Pao, liability).** The rulebook (pp.20 to 21) makes a player who discards the tile that gives another player a fourth meld, or a third dragon meld, liable for the whole hand if that player later self-draws, and forbids some claims when a liability is involved (p.15). None of this is modelled. Pao changes who pays, not what the winner collects. In a head-to-head match it can move points between teams, and it makes the discarder of a key tile pay more than here.
2. **A concealed kong keeps the hand "closed".** Rulebook 1.2: a concealed kong counts as a melded meld, so the hand is not closed and does not score Closed Hand. Here it still scores Closed Hand (1 faan), and All Concealed Triplets (6.4: no quads) is still possible with a concealed kong.
3. **All Concealed Triplets ignores which tile won.** Rulebook 6.4: a triplet completed from another player's discard is not concealed, so a two-pair wait must be self-drawn. Here a hand of four concealed triplets scores 10 faan even when a discard completed one of them.
4. **Last Tile from the Wall also counts on a discard win.** Rulebook 1.9: it is for drawing the last tile. Here it is also given to a win on the discard that follows the last draw (+1 faan).
5. **Nine Gates does not check the wait.** Rulebook 6.11: on a discard win the hand must have been waiting on all nine tiles. Here any completed Nine Gates shape scores.
6. **Only an added kong can be robbed.** Rulebook: a concealed kong may be robbed by a Thirteen Orphans hand. Here it cannot.
7. **Bless of Heaven and Bless of Earth ignore concealed kongs.** The rulebook requires that the dealer has not declared a concealed kan. Here the dealer may have.
8. **Kongs after a claim.** Rulebook p.12: a concealed or promoted kan cannot be declared after melding. Here it can be declared on the turn that follows a claim.
9. **No shifting-meld restriction.** Rulebook p.18: after a meld you may not discard the same tile, or one that forms a sequence with it. Not enforced.
10. **Two players can win on the same discard.** The rulebook does not say what happens. Here only the nearest after the discarder wins.
11. **Not modelled at all:** match structure (dealer rotation, repeat hands, the revolution), points deducted for fouls and cards, and every procedural rule about the physical table (cutting the wall, reaction time).

What matches the rulebook: the faan values of all 14 items worth 1, 3, 5 or 7 faan; the 11 ceiling hands at 10 faan; the 3-faan minimum; the 10-faan cap; the discarder paying the whole hand; the self-drawn split; flowers scoring nothing; no Seven Pairs; the claim priority (win, then pong and kong, then chow).

### Differences from the source engine

The engine comes from the maintainers' own training package. These are the changes made for the bench: a Bless of Heaven hand was accepted but scored as an ordinary hand (it now scores 10 faan); a settlement that does not sum to zero now stops the run instead of being repaired; the deal shuffle is the bench's own and does not depend on the Python version; flower instant wins are off.

## `hk-house-v1`: House

House rules are the rule set the Mahjong Sensei app plays: flowers score, limit hands are graded, the cap is 13, and Seven Pairs is a hand. The values below are `tables/hk-house-v1/rules.json`.

The House track exists to keep one thing visible: the maintainer's own bot, Fu-2.3M-HKMA-1, was trained on HKMA rules, and a bot trained without flower faan and without Seven Pairs is at an advantage on the HKMA table. Scoring every bot on both tables shows how much a rule set suits the bot.

<!-- rules:hk-house-v1:begin -->
Minimum to win: **3 faan**. Cap: **13 faan**.

| Faan item | Faan |
|---|---|
| All Sequences | 1 |
| Seven Pairs (seven different pairs, concealed) | 4 |
| Closed Hand | 1 |
| Self-Drawn | 1 |
| Triplet of Dragons (each triplet) | 1 |
| Triplet of the player's own wind | 1 |
| Triplet of the prevailing wind | 1 |
| All Terminals and Honours (all triplets) | 1 |
| Robbing a Kong | 1 |
| Win on the replacement tile after a kong | 1 |
| Last Tile from the Wall | 1 |
| Semi-Flush (one suit plus honours) | 3 |
| All Triplets | 3 |
| Small Dragons | 3 |
| Big Dragons | 5 |
| Flush (one suit, no honours) | 7 |
| All Honours \* | 10 |
| Small Winds | 6 |
| Big Winds \* | 13 |
| All Concealed Triplets \* | 10 |
| All Quads \* | 13 |
| All Terminals \* | 10 |
| Bless of Heaven (dealer wins on the first draw) \* | 13 |
| Bless of Earth (win on the dealer's first discard) \* | 13 |
| Thirteen Orphans \* | 13 |
| After Consecutive Kan | 8 |
| Nine Gates \* | 10 |

\* Limit hand. Only this item counts, plus Self-Drawn, Last Tile from the Wall, Robbing a Kong and the kong items.

| Flower item | Faan |
|---|---|
| Flower matching the player's seat | 1 |
| Season matching the player's seat | 1 |
| No flowers or seasons | 1 |
| All four flowers | 2 |
| All four seasons | 2 |
| Seven flowers or seasons (instant win) | 3 |
| Eight flowers and seasons (instant win) | 13 |

| Faan | Discarder pays everything | Self-drawn: each of the three pays | Self-drawn: winner collects |
|---|---|---|---|
| 3 | 8 | 4 | 12 |
| 4 | 16 | 8 | 24 |
| 5 | 24 | 12 | 36 |
| 6 | 32 | 16 | 48 |
| 7 | 48 | 24 | 72 |
| 8 | 64 | 32 | 96 |
| 9 | 96 | 48 | 144 |
| 10 | 128 | 64 | 192 |
| 11 | 192 | 96 | 288 |
| 12 | 256 | 128 | 384 |
| 13 | 384 | 192 | 576 |
<!-- rules:hk-house-v1:end -->

* **Seven Pairs.** Seven different pairs, 4 faan. Four of a kind is not two pairs, so a hand holding all four of a tile is not Seven Pairs. It must be fully concealed: a declared meld of any kind, a concealed kong too, rules it out. It stacks with what else the hand has:
  * One suit with no honours adds Flush (7), so 4 + 7. One suit plus honours adds Semi-Flush (3).
  * Only terminals and honours adds 4 for All Terminals and Honours, since a Seven Pairs hand holds no triplets.
  * Only honours (the seven honour tiles) is All Honours, a limit hand: it counts 10, plus Self-Drawn, Last Tile from the Wall, Robbing a Kong and the kong items, then the cap. A self-drawn All Honours by Seven Pairs is 11.
  * Self-Drawn, Closed Hand, Last Tile from the Wall, Robbing a Kong and the flower items all apply as for any other hand.
  * Bless of Heaven and Bless of Earth also apply to a Seven Pairs hand, and count as limit hands do for any hand.
  * The same fourteen tiles can sometimes also be read as four sets and a pair (112233 445566 77 in one suit). Both readings are scored and the one with more faan counts, compared before the cap, so a hand that reaches the cap by either reading is named for the richer one. The payment is the same.
  * A bot may win with Seven Pairs by self-draw or on a discard like any other hand. The scripted reference bots do not aim for it, which is why their play is the same on both tables.
* **Payout.** Same as HKMA: the discarder pays the whole hand, self-draw is 1.5 times, split three ways. The table values are the same as `hk-hkma-v1`'s and continue to 13 faan.
* **Flowers score.** One faan for the player's own seat flower or season, one for having none, two for all four flowers or all four seasons, three for seven, and eight is a limit hand worth 13.
* **Same engine.** House does not claim to be the rulebook, but the engine behaves the same way: there is no 包, and gaps 2 to 11 above describe it too.

## `hk-chicken-v1`: Chicken hand

HKMA Classical with exactly one change: **the minimum to win is 0 faan.** A complete hand with no scoring pattern, a chicken hand (雞糊, "chicken win"), wins, and everything else is as on `hk-hkma-v1`: cap 10, flowers score nothing, no Seven Pairs, the discarder pays the whole hand, the same faan values and the same payment table. The rules file is `tables/hk-chicken-v1/rules.json`, and it says in `derived_from` that it came from `hk-hkma-v1` (rules hash 43e4e01c50dce4d3) and what changed.

Why it is here: a table where any complete hand may win plays differently from one with a 3-faan bar, because a hand is never stuck below the minimum and a cheap win is always available. It shows whether a bot, a model or a person is built for a 3-faan game or can play the quick game too. It is **not** the no-minimum "hit and run" game where every win pays the same: here a 3-faan hand still pays 8, a limit hand 128, and a chicken hand 1, so building a big hand still pays.

<!-- rules:hk-chicken-v1:begin -->
Minimum to win: **0 faan**. Cap: **10 faan**.

| Faan item | Faan |
|---|---|
| All Sequences | 1 |
| Closed Hand | 1 |
| Self-Drawn | 1 |
| Triplet of Dragons (each triplet) | 1 |
| Triplet of the player's own wind | 1 |
| Triplet of the prevailing wind | 1 |
| All Terminals and Honours (all triplets) | 1 |
| Robbing a Kong | 1 |
| Win on the replacement tile after a kong | 1 |
| Last Tile from the Wall | 1 |
| Semi-Flush (one suit plus honours) | 3 |
| All Triplets | 3 |
| Small Dragons | 3 |
| Big Dragons | 5 |
| Flush (one suit, no honours) | 7 |
| All Honours \* | 10 |
| Small Winds | 10 |
| Big Winds \* | 10 |
| All Concealed Triplets \* | 10 |
| All Quads \* | 10 |
| All Terminals \* | 10 |
| Bless of Heaven (dealer wins on the first draw) \* | 10 |
| Bless of Earth (win on the dealer's first discard) \* | 10 |
| Thirteen Orphans \* | 10 |
| After Consecutive Kan | 10 |
| Nine Gates \* | 10 |

\* Limit hand. Only this item counts, plus Self-Drawn, Last Tile from the Wall, Robbing a Kong and the kong items.

| Flower item | Faan |
|---|---|
| Flower matching the player's seat | 0 |
| Season matching the player's seat | 0 |
| No flowers or seasons | 0 |
| All four flowers | 0 |
| All four seasons | 0 |
| Seven flowers or seasons (instant win) | 0 |
| Eight flowers and seasons (instant win) | 0 |

| Faan | Discarder pays everything | Self-drawn: each of the three pays | Self-drawn: winner collects |
|---|---|---|---|
| 0 (a chicken hand) | 1 | not possible | not possible |
| 1 | 2 | 1 | 3 |
| 2 | 4 | 2 | 6 |
| 3 | 8 | 4 | 12 |
| 4 | 16 | 8 | 24 |
| 5 | 24 | 12 | 36 |
| 6 | 32 | 16 | 48 |
| 7 | 48 | 24 | 72 |
| 8 | 64 | 32 | 96 |
| 9 | 96 | 48 | 144 |
| 10 | 128 | 64 | 192 |
<!-- rules:hk-chicken-v1:end -->

* **What counts as a chicken hand.** Four melds and a pair that score no faan item at all: not all sequences, not all triplets, no dragon triplet, no triplet of the player's own wind or the prevailing wind, no flush, no limit hand, and flowers score nothing. Self-Drawn and Closed Hand are one faan each, so a chicken hand is always won on a discard, with at least one meld claimed from another player. A hand that is not complete is still not a win: a lower minimum does not make Seven Pairs, or a hand one tile short, a hand.
* **Payout.** The discarder pays 1 point for a chicken hand (the 0-faan row of the same table), and the rest as on HKMA: 8 for 3 faan up to 128 at the cap.
* **Same engine, same gaps.** Gaps 1 to 11 above describe this table too.
* **The reference field is the same three bots, unchanged.** They take a win whenever the engine offers one, so on this table they declare a chicken hand, and they read the table's rules, so what counts as a hand ready to win moves with the minimum.
