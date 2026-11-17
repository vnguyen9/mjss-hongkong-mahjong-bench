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
| `hk-house-v1` | House rules: flowers score, limit hands are graded 6, 8, 10 and 13, cap 13, Seven Pairs is a hand. | pending Seven Pairs scoring |

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

Baseline rows on the board (public deals, so **unverified**; points a hand against the field with a 95% interval):

| Bot | Points a hand | 95% interval | Win | Deal-in | Deals |
|---|---|---|---|---|---|
| `python_example` | +2.47 | [+2.03, +2.91] | 10.1% | 5.0% | 2,000 |
| `faan_aware` | +1.73 | [+1.48, +1.98] | 16.7% | 4.2% | 2,000 |
| `ukeire` | -0.85 | [-1.01, -0.69] | 4.6% | 4.4% | 2,000 |
| `deficiency` | -0.90 | [-1.06, -0.73] | 4.3% | 4.7% | 2,000 |
| `shallow_search` | -1.30 | [-1.65, -0.94] | 3.4% | 4.6% | 400 |
| `random` | -1.84 | [-1.98, -1.69] | 0.0% | 5.0% | 2,000 |

A bot scored against a field that contains it plays itself, so `faan_aware`, `ukeire` and `deficiency` are rows against two other field bots and a copy of themselves. Head to head, over 300 deals each pair, the ranks are `faan_aware` first, the Python example second, `ukeire` and `deficiency` sharing third, and `random` last. These rows reproduce byte for byte on Python 3.9 and 3.11 (`hkbench score ... --deals 2000`).

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

* **The maintainers' own bot is scored here.** Mahjong Sensei's bot (h1) is hosted: it is scored through this harness and its weights are private. It was trained on the HKMA rules, with no flower faan and no Seven Pairs, so it is at an advantage on the HKMA table. The House table exists to keep that visible. Read a row beside its `trained on` field.
* **The field is fixed and not strong.** Points against three scripted bots say how a player does against that kind of opponent. They say less about play against careful humans, or against opponents that adapt.
* **The field's claim play is crude.** `ukeire` and `deficiency` claim at random, and no field bot plays defence. A bot can profit from that without being good.
* **Single hands.** There is no dealer rotation, no match, no fouls and no table talk. A strategy that depends on the score of a match is not measured.
* **Points are one quarter of the rulebook's.** Every ratio is the same.
* **Gaps from the rulebook.** `hk-hkma-v1` has no 包 (liability) and several smaller differences, listed in `RULES.md`. A bot's row on it is a row under those rules.
* **Most hands are draws, and big hands decide the score.** Between 59% and 71% of baseline games end in a draw, because 3 faan is a high bar. The bots that win do so in 0% to 17% of games. A strong bot's edge is in the few big hands, so intervals are wide at low deal counts. 2,000 deals gave intervals of about plus or minus 0.15 to 0.45 points a hand for the baselines.
* **Points a hand and head-to-head ranks can disagree.** The first values big hands. The second counts which team came out ahead. In the baselines the Python example bot collects more points a hand than `faan_aware` against the field (+2.47 against +1.73, because it plays for triplets and gets 104 limit hands against 9), yet head to head `faan_aware` wins more games (441 to 239 out of 1,800) with the points level. Read both.
* **The example bot beats the field.** A short hand-written bot that keeps pairs and claims dragon and wind pongs finishes ahead of the field's best bot on points a hand. The field is a reference point, not a ceiling.
* **Time limits depend on hardware.** The limit is wall-clock time per decision (10 seconds). A bot that needs more will be asked to run on our machine with its own limit, which is then recorded.
* **Language models and people are not scored yet.** Those tracks need cost per hand and a place to play. They are empty.
* **Third-party bots are not listed without their authors' agreement.** None of their code, weights or results are in this repository. The protocol is documented so they can submit (`SUBMITTING.md`).

## Results format

One JSON per scored run in `results/` (schema `hkbench-result-1`) and a gzip JSON-lines log of every game in `results/logs/`. A result records the bot and its hash, the table, the rules hash, the field hashes, the deal tag and count, verification, the fair-play outcome, faults, the exact command, and the engine fingerprint. Public-deck logs carry each deal's seed and every action, and `hkbench verify-log` replays them.

## Maintenance

Maintained by Mahjong Sensei. Open an issue to report a rules error, a scoring bug, or a submission.
