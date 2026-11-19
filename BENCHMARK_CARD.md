# Benchmark card: Hong Kong Mahjong Bench

## Purpose

To say, with an interval, how well a player plays Hong Kong Mahjong. The player can be a bot, a language model or a person. The number is points a hand against a fixed set of opponents, under rules that are named on every row.

It is meant for comparing players with each other and for watching one player improve. It is not a measure of fun, of style, or of strength against the best human players.

## What is measured

**Headline: points a hand against the frozen field.** The player takes one seat. Three reference bots take the others. Every deal is played four times on the same wall, the player taking each seat once. The score of a deal is the player's average points over its four games. The headline is the mean of those, with a 95% interval.

Also reported: win rate, deal-in rate (how often the player's discard was the winning tile), self-draw win rate, draw rate, average points of a win, average faan of a win, and limit hands (hands that reached the table's cap).

**Head to head.** Two bots, two seats each, every way of seating them (six seat pairs), on the same wall. All pairs are played, and a Bradley-Terry rating with a bootstrap interval is fitted to the results. A bot's rank is 1 plus the number of bots whose interval lies entirely above it, so bots whose intervals overlap share a rank.

## Rules

Two tables, named on every row. `RULES.md` has every faan value, the cap, the minimum, the payout and the flower rules.

| Table | What it is | State |
|---|---|---|
| `hk-hkma-v1` | The Hong Kong Mahjong Association's classical rules: 3 faan to win, cap 10, the discarder pays the whole hand, flowers do not score. **The headline track.** It is not the rulebook in every detail: `RULES.md` lists the gaps (no 包, a concealed kong keeps a hand closed, and others). | scoring |
| `hk-house-v1` | House rules: flowers score, limit hands are graded 6, 8, 10 and 13, cap 13, Seven Pairs is a hand. | scoring |

A table is frozen when it is released. A change to the rules, the engine, the field or the deal schedule makes a new table (`v2`). A released table is never edited.

## The reference field

Three scripted bots read only their own seat view, the same message an outside bot gets:

| Bot | What it does |
|---|---|
| `faan_aware` | Counts tiles to a complete hand, prefers waits that reach the faan minimum, keeps dragons and its own wind, and claims only what fits its suit. |
| `ukeire` | Throws the tile that leaves the hand closest to winning, ties broken by how many live tiles help. Claims at random. |
| `deficiency` | Throws the tile that leaves the hand closest to winning, nothing else. Claims at random. |

The field is pinned: `tables/hk-hkma-v1/table.json` holds a hash of each bot's source files, and the bench refuses to score if one has changed.

Why these three. We ran the maintainers' scripted bots against one strong opponent (4,608 games each) and kept the strongest that read only their own view. `faan_aware` was clearly ahead of the rest. `shallow_search` and `ukeire` finished level within noise, and `shallow_search` costs about 100 times the time, so it is a baseline row and not in the field. `wait_aware` scored higher than any of them but it reads other players' hidden hands, so it is not shipped. `kstep2` plays identically to `ukeire`, so it is not listed.

Baseline rows on `hk-hkma-v1` (public deals, so **unverified**; points a hand against the field with a 95% interval):

| Bot | Points a hand | 95% interval | Win | Deal-in | Deals |
|---|---|---|---|---|---|
| `python_example` | +2.50 | [+2.06, +2.95] | 10.3% | 5.0% | 2,000 |
| `faan_aware` | +1.41 | [+1.17, +1.65] | 15.9% | 4.2% | 2,000 |
| `ukeire` | -0.96 | [-1.12, -0.80] | 4.6% | 4.7% | 2,000 |
| `deficiency` | -0.99 | [-1.16, -0.82] | 4.3% | 4.8% | 2,000 |
| `shallow_search` | -1.19 | [-1.50, -0.87] | 3.3% | 4.7% | 400 |
| `random` | -1.79 | [-1.92, -1.65] | 0.1% | 4.7% | 2,000 |

A bot scored against a field that contains it plays itself, so `faan_aware`, `ukeire` and `deficiency` are rows against two other field bots and a copy of themselves. Head to head, over 300 deals each pair, the ranks are `faan_aware` first, the Python example second, `ukeire` and `deficiency` sharing third, and `random` last. These rows reproduce byte for byte on Python 3.9 and 3.11 (`hkbench score ... --deals 2000`).

Baseline rows on `hk-house-v1`, the same bots and the same 2,000 deals (400 for `shallow_search`):

| Bot | Points a hand | 95% interval | Win | Deal-in | Deals |
|---|---|---|---|---|---|
| `python_example` | +2.43 | [+1.92, +2.94] | 14.1% | 6.0% | 2,000 |
| `faan_aware` | +1.55 | [+1.28, +1.82] | 22.0% | 5.8% | 2,000 |
| `ukeire` | -0.92 | [-1.09, -0.75] | 12.2% | 5.8% | 2,000 |
| `shallow_search` | -0.94 | [-1.38, -0.50] | 13.9% | 5.9% | 400 |
| `deficiency` | -1.16 | [-1.33, -0.99] | 10.5% | 6.1% | 2,000 |
| `random` | -3.04 | [-3.22, -2.87] | 0.1% | 7.1% | 2,000 |

On House the head-to-head ranks are `faan_aware` first, `ukeire` and the Python example sharing second, `deficiency` fourth and `random` last. Flowers add a faan to nearly every hand (one for holding none, one for each seat flower), so 3 faan is easy to reach and far more hands are won than on HKMA (33% to 46% of games end in a draw, against 59% to 72%). The reference bots do not aim for Seven Pairs, but they declare it when a hand is complete. It ended 6 to 9 games in 8,000 (about 0.1%) in the rows for the field bots and `random`, and 190 in 8,000 (2.4%) in the Python example's row, since that bot keeps pairs.

## Mahjong Sensei's hosted bot: Fu-2.3M-HKMA-1

`Fu-2.3M-HKMA-1` is the bot that ships in Mahjong Sensei, hosted here. The name reads family (Fu), size (2.3M parameters), the rules it trained on (HKMA) and version (1); it trained on 1.3B decisions. It runs through the same protocol as any other bot; the result files hide how it is started and carry only its supplied hash. It was trained on HKMA Classical rules, with flowers dealt and replaced but no flower faan, and no Seven Pairs. Read its row beside `trained on`: on the HKMA table it plays the rules it was trained for, and on the House table it is playing rules it was not trained for.

Rows on the private deck (**verified**; 2,000 deals, with every baseline re-run on the same deals) and, for reference, on the public deals (unverified). Points a hand against the field, 95% interval:

| Table | Deck | Fu-2.3M-HKMA-1 points a hand | Win | Deal-in | Best baseline (points a hand) |
|---|---|---|---|---|---|
| `hk-hkma-v1` | private, verified | +17.36 [+16.70, +18.02] | 47.0% | 3.4% | `python_example` +2.52 |
| `hk-hkma-v1` | public, unverified | +17.67 [+17.00, +18.35] | 47.7% | 3.1% | `python_example` +2.50 |
| `hk-house-v1` | private, verified | +16.37 [+15.56, +17.19] | 37.8% | 4.8% | `python_example` +2.69 |
| `hk-house-v1` | public, unverified | +16.26 [+15.42, +17.09] | 37.3% | 4.9% | `python_example` +2.43 |

Head to head over 300 deals (Bradley-Terry, Elo scale), with `Fu-2.3M-HKMA-1` added to the five bots above: on both tables and both decks `Fu-2.3M-HKMA-1` is rank 1 and `faan_aware` rank 2. On the verified HKMA deck the ratings are `Fu-2.3M-HKMA-1` +150.6, `faan_aware` +25.3, `python_example` -9.4, `ukeire` -42.9, `deficiency` -45.9, `random` -77.6; on the verified House deck `Fu-2.3M-HKMA-1` +103.9, `faan_aware` +48.9, `python_example` -7.4, `ukeire` -9.3, `deficiency` -20.3, `random` -115.8. The earlier five-bot head-to-head runs stay in `results/`.

The bench's seat view is turned into `Fu-2.3M-HKMA-1`'s own observation by a wrapper that the maintainers keep with the bot. Before any number counted, `Fu-2.3M-HKMA-1` through the bench and `Fu-2.3M-HKMA-1` in its own engine chose the same move on every position where both engines offer the same legal moves (13,984 of 13,984 on HKMA, 13,684 of 13,684 on House). On the House table the bench also offers a win that the trained rules cannot declare (a hand that reaches 3 faan with flowers, or Seven Pairs); those positions are the only ones where the two differ.

## Deals

* **Public deals.** Deals 0 to 99,999 of each table's public deck are in the repository (the seed is computed from the table's public range). Anyone can reproduce a row on them. A run on public deals is tagged **unverified**.
* **Private deals.** The deck used for scored rows is private. It is read from a file outside the repository (`--private-seeds` or `HKBENCH_PRIVATE_SEEDS`), is refused if it overlaps the public range, and is never committed. A run on private deals that also passed the fair-play check and made no excess faults is tagged **verified**. The log of a private run holds each game's outcome by deal number, and no deal, wall or action, so publishing it does not reveal the deck.
* **Schedule.** Deal `i` has dealer `i mod 4` and prevailing wind `(i / 4) mod 4`. A deal is a 144-tile wall from a 64-bit seed with the bench's own shuffle, the same on every Python version.

A private deck wears out if it is reused many times: results on it can be tuned against. Retire it and make a new one when a table is superseded, or when a bot has been scored on it enough times to matter.

## How the numbers are computed

The four games of a deal share a wall, and the six games of a head-to-head deal share a wall. They are not independent. Every interval therefore uses **one number per deal**, then the standard error of those numbers (Student's t, 95%). This is tested on synthetic data where the answer is known (`tests/test_stats.py`), including a case where treating games as independent is wrong by a factor of about two.

Bradley-Terry ratings use game outcomes (win, loss, or half for a draw or a hand that nets to nothing) and resample whole deals within each pair for the intervals.

## Fair play

The protocol sends a bot only what its seat could see. Before a bot is scored the bench also re-deals every hidden tile at real decision points and asks again; any changed answer rejects the bot, and the check also confirms that the bench's own message does not change. Because the message cannot carry hidden tiles, this mainly proves the harness. It does catch a bot that reaches the hidden state some other way, or one that is random without using the seed: the tests include a bot that cheats through a side channel and show it is caught.

The check does not stop a bot from being run with more thinking time, tools or help than a person would have. It does not read a bot's code. A submitted bot runs on our machine with no network.

## Known limits

* **A hosted bot is scored here.** The hosted bot (Fu-2.3M-HKMA-1) is scored through this harness and its implementation is private. It was trained on the HKMA rules, with no flower faan and no Seven Pairs, so it is at an advantage on the HKMA table. The House table exists to keep that visible. Read a row beside its `trained on` field.
* **The field is fixed and not strong.** Points against three scripted bots say how a player does against that kind of opponent. They say less about play against careful humans, or against opponents that adapt.
* **The field's claim play is crude.** `ukeire` and `deficiency` claim at random, and no field bot plays defence. A bot can profit from that without being good.
* **Single hands.** There is no dealer rotation, no match, no fouls and no table talk. A strategy that depends on the score of a match is not measured.
* **Points are one quarter of the rulebook's.** Every ratio is the same.
* **Gaps from the rulebook.** `hk-hkma-v1` has no 包 (liability) and several smaller differences, listed in `RULES.md`. A bot's row on it is a row under those rules.
* **On HKMA most hands are draws, and big hands decide the score.** Between 59% and 72% of baseline games end in a draw, because 3 faan is a high bar (on House the figure is 33% to 46%). The bots that win do so in 0% to 16% of games. A strong bot's edge is in the few big hands, so intervals are wide at low deal counts. 2,000 deals gave intervals of about plus or minus 0.15 to 0.45 points a hand for the baselines.
* **Points a hand and head-to-head ranks can disagree.** The first values big hands. The second counts which team came out ahead. In the baselines the Python example bot collects more points a hand than `faan_aware` against the field (+2.50 against +1.41, because it plays for triplets and gets 105 limit hands against 4), yet head to head `faan_aware` wins more games (450 to 223 out of 1,800) with the points level. Read both.
* **The example bot beats the field.** A short hand-written bot that keeps pairs and claims dragon and wind pongs finishes ahead of the field's best bot on points a hand. The field is a reference point, not a ceiling.
* **Time limits depend on hardware.** The limit is wall-clock time per decision (10 seconds). A bot that needs more will be asked to run on our machine with its own limit, which is then recorded.
* **Language models and people are not scored yet.** Those tracks need cost per hand and a place to play. They are empty.
* **Third-party bots are not listed without their authors' agreement.** None of their code, model files or results are in this repository. The protocol is documented so they can submit (`SUBMITTING.md`).

## Results format

One JSON per scored run in `results/` (schema `hkbench-result-1`) and a gzip JSON-lines log of every game in `results/logs/`. A result records the bot and its hash, the table, the rules hash, the field hashes, the deal tag and count, verification, the fair-play outcome, faults, the exact command, and the engine fingerprint. Public-deck logs carry each deal's seed and every action, and `hkbench verify-log` replays them.

## Maintenance

Maintained by Mahjong Sensei. Open an issue to report a rules error, a scoring bug, or a submission.
