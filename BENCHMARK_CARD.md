# Benchmark card: Hong Kong Mahjong Bench

## Purpose

The bench measures how well a player plays Hong Kong Mahjong, with an interval around the score. The player can be a bot, an LLM or a human. The number is points a hand against a fixed set of opponents, under rules that are named on every row.

It is meant for comparing players with each other and for watching one player improve. It is not a measure of fun, of style, or of strength against the best human players.

## What is measured

The headline is points a hand against the frozen field. The player takes one seat. Three reference bots take the others. Every deal is played four times on the same wall, the player taking each seat once. The score of a deal is the player's average points over its four games. The headline is the mean of those, with a 95% interval.

The bench also reports win rate, deal-in rate (how often the player's discard was the winning tile), self-draw win rate, draw rate, average points of a win, average faan of a win, and limit hands (hands that reached the table's cap).

Head-to-head runs give two bots two seats each and play every way of seating them (six seat pairs) on the same wall. All pairs are played, and a Bradley-Terry rating with a bootstrap interval is fitted to the results. A bot's rank is 1 plus the number of bots whose interval lies entirely above it, so bots whose intervals overlap share a rank.

## Rules

There are three tables, and every result row says which one it was scored on. `RULES.md` has every faan value, the cap, the minimum, the payout and the flower rules.

| Table | What it is | State |
|---|---|---|
| `hk-hkma-v1` | The Hong Kong Mahjong Association's classical rules: 3 faan to win, cap 10, the discarder pays the whole hand, flowers do not score. This is the headline track. It is not the rulebook in every detail: `RULES.md` lists the gaps (no 包, a concealed kong keeps a hand closed, and others). | scoring |
| `hk-house-v1` | House rules: flowers score, limit hands are graded 6, 8, 10 and 13, cap 13, Seven Pairs is a hand. | scoring |
| `hk-chicken-v1` | Chicken hand: `hk-hkma-v1` with one change, a minimum of 0 faan, so a complete hand with no scoring pattern (a chicken hand, 雞糊) wins and pays the 0-faan row. Faan still score and pay as usual (cap 10), so it is not a table where every win pays the same. | scoring |

A table is frozen when it is released. A change to the rules, the engine, the field or the deal schedule makes a new table (`v2`). A released table is never edited.

## The reference field

Three scripted bots read only their own seat view, the same message an outside bot gets:

| Bot | What it does |
|---|---|
| `faan_aware` | Counts tiles to a complete hand, prefers waits that reach the faan minimum, keeps dragons and its own wind, and claims only what fits its suit. |
| `ukeire` | Throws the tile that leaves the hand closest to winning, ties broken by how many live tiles help. Claims at random. |
| `deficiency` | Throws the tile that leaves the hand closest to winning, nothing else. Claims at random. |

The field is pinned: `tables/hk-hkma-v1/table.json` holds a hash of each bot's source files, and the bench refuses to score if one has changed.

We chose these three after running the maintainers' scripted bots against one strong opponent (4,608 games each). We kept the strongest that read only their own view. `faan_aware` was clearly ahead of the rest. `shallow_search` and `ukeire` finished level within noise, and `shallow_search` costs about 100 times the time, so it is a baseline row and not in the field. `wait_aware` scored higher than any of them but it reads other players' hidden hands, so it is not shipped. `kstep2` plays identically to `ukeire`, so it is not listed.

Every row in this card and on the board was re-scored under 1.1.0 (`hmac-sha256-v2`, see "What a bot is sent") on 20 and 21 November 2026, on a new private deck of independent random seeds. The 1.0.0 rows (`splitmix-v1`) are in the repository's history. A bot that is a program (the Python example and `Fu-2.3M-HKMA-1`) ran in the macOS sandbox with the deck unreadable; the reference bots run inside the bench. Public rows moved by up to 0.4 points a hand for the baselines and 0.6 for `Fu-2.3M-HKMA-1`, because the bots draw other random numbers. Private rows are on new deals; the largest move is `Fu-2.3M-HKMA-1` on House, +16.37 to +17.67, where each row's interval is about plus or minus 0.9. The ranking did not change: `Fu-2.3M-HKMA-1` is first on every table and deck, and the Python example and `faan_aware` lead the baselines.

The baseline rows on `hk-hkma-v1` use public deals, so they are **unverified**. They report points a hand against the field with a 95% interval:

| Bot | Points a hand | 95% interval | Win | Deal-in | Deals |
|---|---|---|---|---|---|
| `python_example` | +2.87 | [+2.43, +3.30] | 10.9% | 4.6% | 2,000 |
| `faan_aware` | +1.56 | [+1.33, +1.79] | 16.7% | 4.4% | 2,000 |
| `ukeire` | -0.93 | [-1.10, -0.77] | 4.3% | 4.7% | 2,000 |
| `deficiency` | -0.98 | [-1.15, -0.82] | 4.0% | 4.7% | 2,000 |
| `shallow_search` | -1.01 | [-1.32, -0.71] | 3.5% | 4.5% | 400 |
| `random` | -1.89 | [-2.05, -1.73] | 0.0% | 4.8% | 2,000 |

A bot scored against a field that contains it plays itself, so `faan_aware`, `ukeire` and `deficiency` are rows against two other field bots and a copy of themselves. Head to head, over 300 deals each pair, the ranks are `faan_aware` first, the Python example second, `ukeire` and `deficiency` sharing third, and `random` last. Every public game in them replays with `hkbench verify-log`.

The baseline rows on `hk-house-v1` use the same bots and the same 2,000 deals (400 for `shallow_search`):

| Bot | Points a hand | 95% interval | Win | Deal-in | Deals |
|---|---|---|---|---|---|
| `python_example` | +2.35 | [+1.83, +2.87] | 13.7% | 6.6% | 2,000 |
| `faan_aware` | +1.65 | [+1.38, +1.93] | 22.8% | 5.7% | 2,000 |
| `ukeire` | -0.76 | [-0.95, -0.57] | 12.3% | 5.9% | 2,000 |
| `shallow_search` | -0.79 | [-1.21, -0.36] | 13.7% | 6.2% | 400 |
| `deficiency` | -0.85 | [-1.04, -0.65] | 11.2% | 6.1% | 2,000 |
| `random` | -2.95 | [-3.11, -2.79] | 0.1% | 7.3% | 2,000 |

On House the head-to-head ranks are `faan_aware` first, `ukeire` and the Python example sharing second, `deficiency` fourth and `random` last. Flowers add a faan to nearly every hand (one for holding none, one for each seat flower), so 3 faan is easy to reach and far more hands are won than on HKMA (33% to 47% of games end in a draw, against 59% to 72%). The reference bots do not aim for Seven Pairs, but they declare it when a hand is complete. It ended 8 or 9 games in 8,000 (about 0.1%) in the public rows for the field bots and `random`, and 190 in 8,000 (2.4%) in the Python example's row, since that bot keeps pairs.

The `hk-chicken-v1` baseline runs use the same bots and 2,000 deals (400 for `shallow_search`). The table gives points a hand against the field with a 95% interval, on the public deals (unverified) and on the private deck (verified):

| Bot | Public points a hand | Private points a hand | Win (public) | Deal-in (public) |
|---|---|---|---|---|
| `faan_aware` | +0.37 [+0.22, +0.52] | +0.41 [+0.30, +0.52] | 27.2% | 17.8% |
| `python_example` | +0.22 [-0.00, +0.44] | -0.14 [-0.34, +0.05] | 8.9% | 23.2% |
| `shallow_search` | +0.14 [+0.00, +0.28] | +0.13 [+0.00, +0.26] | 33.4% | 16.6% |
| `ukeire` | -0.22 [-0.31, -0.14] | -0.17 [-0.25, -0.09] | 23.5% | 18.5% |
| `deficiency` | -0.28 [-0.37, -0.19] | -0.18 [-0.26, -0.10] | 22.2% | 19.0% |
| `random` | -1.19 [-1.28, -1.10] | -1.19 [-1.27, -1.12] | 0.2% | 24.5% |

The five-bot public head-to-head run used 300 deals and gave these ratings: `faan_aware` +93.1 (rank 1), `ukeire` +75.0 (rank 2), `deficiency` +62.2 (rank 3), the Python example -51.9 (rank 4), `random` -178.4 (rank 5).

Draws almost disappear: 1% to 6% of baseline games end in a draw (0.5% for `Fu-2.3M-HKMA-1`), against 59% to 72% on HKMA. About a third of all wins (31% to 36% in the baseline rows) are chicken hands worth 1 point, and another 42% to 46% are worth 1 faan, so a point a hand is small here and the intervals are tight: about plus or minus 0.1 for the field bots at 2,000 deals. Points a hand are not comparable with the other tables' (a 3-faan win pays 8 on all three, a chicken hand 1). `shallow_search` wins the most games of the baselines (33%) and still scores barely above zero, because its wins are cheap, and the Python example wins 9% of games and scores what it does through its limit hands (18 to 27 in 8,000 games).

## Mahjong Sensei's hosted bot: Fu-2.3M-HKMA-1

`Fu-2.3M-HKMA-1` is the bot that ships in Mahjong Sensei, hosted here. The name gives its family (Fu), size (2.3M parameters), training rules (HKMA) and version (1). It trained on 1.3B decisions. It runs through the same protocol as any other bot; the result files hide how it is started and carry only its supplied hash. It was trained on HKMA Classical rules, with flowers dealt and replaced but no flower faan, and no Seven Pairs. The `trained on` field matters: on the HKMA table it plays the rules it was trained for, and on the House and Chicken-hand tables it is playing rules it was not trained for.

The following rows give points a hand against the field with a 95% interval. The private rows are **verified** and use 2,000 deals, with every baseline re-run on the same deals. Public rows are unverified.

| Table | Deck | Fu-2.3M-HKMA-1 points a hand | Win | Deal-in | Best baseline (points a hand) |
|---|---|---|---|---|---|
| `hk-hkma-v1` | private, verified | +17.75 [+17.08, +18.42] | 47.2% | 3.4% | `python_example` +2.54 |
| `hk-hkma-v1` | public, unverified | +17.45 [+16.77, +18.13] | 46.6% | 3.4% | `python_example` +2.87 |
| `hk-house-v1` | private, verified | +17.67 [+16.76, +18.58] | 37.4% | 4.9% | `python_example` +2.79 |
| `hk-house-v1` | public, unverified | +16.83 [+15.95, +17.71] | 37.0% | 4.6% | `python_example` +2.35 |
| `hk-chicken-v1` | private, verified | +0.64 [+0.55, +0.73] | 47.8% | 13.5% | `faan_aware` +0.41 |
| `hk-chicken-v1` | public, unverified | +0.67 [+0.58, +0.76] | 48.5% | 13.0% | `faan_aware` +0.37 |

The head-to-head runs used 300 deals (Bradley-Terry, Elo scale), with `Fu-2.3M-HKMA-1` added to the five bots above. On both tables and both decks `Fu-2.3M-HKMA-1` is rank 1 and `faan_aware` rank 2. On the verified HKMA deck the ratings are `Fu-2.3M-HKMA-1` +151.6, `faan_aware` +25.2, `python_example` -9.8, `ukeire` -43.6, `deficiency` -47.7, `random` -75.7; on the verified House deck `Fu-2.3M-HKMA-1` +106.7, `faan_aware` +50.7, `ukeire` -9.3, `python_example` -12.0, `deficiency` -21.4, `random` -114.6. The five-bot head-to-head runs are in `results/` too. On `hk-chicken-v1`, again on both decks, `Fu-2.3M-HKMA-1` is rank 1 and `faan_aware` rank 2; on the verified deck the ratings are `Fu-2.3M-HKMA-1` +164.6, `faan_aware` +60.1, `ukeire` +36.1, `deficiency` +25.6, `python_example` -78.4, `random` -208.0.

The bench's seat view is turned into `Fu-2.3M-HKMA-1`'s own observation by a wrapper that the maintainers keep with the bot. Before scoring, `Fu-2.3M-HKMA-1` through the bench and `Fu-2.3M-HKMA-1` in its own engine chose the same move on every position where both engines offer the same legal moves (13,984 of 13,984 on HKMA, 13,684 of 13,684 on House). On the House table the bench also offers a win that the trained rules cannot declare (a hand that reaches 3 faan with flowers, or Seven Pairs); those positions are the only ones where the two differ.

On `hk-chicken-v1`, the bot has one input that says which rules are in force, a no-faan bit. It was never trained with the bit on. For this table the maintainers set it the way the Mahjong Sensei app sets it for its own zero-minimum table (the Beginner table): the bit is on, and the inputs that count how many of its outs would win are computed under this table's own rules (minimum 0 faan, cap 10). It was chosen once, from the app's rule, and the other setting was not run, so the row is not the better of two. The same check as above, run on this table (replaying 66 bench games, 4,109 positions), found the bot through the bench and in its own engine identical on every position: inputs, legal moves and choices. A different setting could score differently, and the bot is not trained for this table, so its row measures how the HKMA-trained player copes with it. Because the supplied hash covers the wrapper, the bot on this table carries a different hash from its other rows.

## Deals

* Deals 0 to 99,999 of each table's public deck are in the repository (the seed is computed from the table's public range). Anyone can reproduce a row on them. A run on public deals is tagged **unverified**.
* The deck used for scored rows is private. It is read from a file outside the repository (`--private-seeds` or `HKBENCH_PRIVATE_SEEDS`), is refused if it overlaps the public range (a seed must be an integer in [0, 2^64); a larger or negative number would be another spelling of a public seed), and is never committed. Make it with `scripts/make_private_deck.py`: independent random 64-bit seeds, no start and count (a deck in that form is refused, because one guessed seed would give every deal). A run on private deals that also passed the fair-play check and made no excess faults is tagged **verified**. The log of a private run holds each game's outcome by deal number, and no deal, wall or action, so publishing it does not reveal the deck.
* Deal `i` has dealer `i mod 4` and prevailing wind `(i / 4) mod 4`. A deal is a 144-tile wall from a 64-bit seed with the bench's own shuffle, the same on every Python version.

Repeated scoring can wear out a private deck because bots can be tuned against its results. Retire it and make a new one when a table is superseded, or when a bot has been scored on it enough times to matter.

## How the numbers are computed

The four games of a deal share a wall, and the six games of a head-to-head deal share a wall. They are not independent. Every interval therefore uses **one number per deal**, then the standard error of those numbers (Student's t, 95%). This is tested on synthetic data where the answer is known (`tests/test_stats.py`), including a case where treating games as independent is wrong by a factor of about two.

Bradley-Terry ratings use game outcomes (win, loss, or half for a draw or a hand that nets to nothing) and resample whole deals within each pair for the intervals.

## What a bot is sent

A bot is sent its seat's view and two identifiers, and neither reveals the deal. `rng_seed` is the low 31 bits of an HMAC-SHA256 of the table, deal number, arrangement and decision number under a run key; `game_id` is another HMAC of the same inputs, as 32 hex digits. The key is 32 random bytes per private run, held only by the bench's processes and never written to a result, a log or the environment.

A public run uses a fixed, public key so it repeats exactly. Version 1.0.0 derived `rng_seed` from the deal's seed and named the deal in `game_id`, so a bot could rebuild the private wall; see `CHANGELOG.md`.

Every bot that is a program is started fresh for every seat of every game, with an environment limited to `PATH`, `LANG`, `LC_*` and `SYSTEMROOT` plus what the run names, and a new empty directory as its working directory, `HOME` and temp directory (deleted afterwards). It runs in its own process group and the bench kills the whole group when the game ends, so it cannot carry a file, a daemon or a held pipe from one game to the next, or from one seat to the other. This closes the channels inside the protocol.

A bot run natively can still write elsewhere on disk it has access to, reach another process of the same user (the scratch directories sit under one private parent, which another user cannot enter and the same user can), start a process in a new session that survives the kill, or read the bench's files or memory as the same operating-system user. Pure Python cannot sandbox those operations. Official private-deck scores use `--sandbox CMD`, a command prefix for every bot launch. Each bot process gets its own sandbox; for example, a Docker container with no network, a read-only file system and the bot directory mounted read-only. `SUBMITTING.md` gives the recipe. A private-deck run of a program bot without it is refused unless `--native-unsafe` is given, and a result records `"isolation": "sandbox"` or `"native"`. `game_over` is sent at the end of a scored game and not in the fair-play check, so a bot that could keep state across processes could tell them apart after it has answered; the sandbox is what removes that. In-process reference bots are the bench's own code and need none.

## Fair play

The protocol sends a bot only what its seat could see. Before scoring, the bench plays the bot in real games against the field. The deals come from a secret made for the check, so they are not known and cannot be recognised. At chosen decision points, the bench re-deals every hidden tile and asks again in a new process. That process first receives the seat's earlier messages, following the bot's own moves with the pauses the game had. The bot sits at every position against the dealer, as it does during scoring. Any changed answer, either at the chosen position or to an earlier message, rejects the bot. The check also confirms that the bench's own message does not change. Because the message cannot carry hidden tiles, this mainly proves the harness. It does catch a bot that reaches the hidden state some other way, or one that is random without using the seed: the tests include a bot that cheats through a side channel and show it is caught.

The check does not stop a bot from being run with more thinking time, tools or help than a human would have. It does not read a bot's code. A submitted bot runs on our machine with no network.

## Known limits

* The hosted bot (Fu-2.3M-HKMA-1) is scored through this harness and its implementation is private. It was trained on the HKMA rules, with no flower faan and no Seven Pairs, so it is at an advantage on the HKMA table. The House table exists to keep that visible. Read a row beside its `trained on` field.
* The field is fixed and not strong. Points against three scripted bots say how a player does against that kind of opponent. They say less about play against careful humans, or against opponents that adapt.
* The field's claim play is crude. `ukeire` and `deficiency` claim at random, and no field bot plays defence. A bot can profit from that without being good.
* The bench scores single hands. There is no dealer rotation, no match, no fouls and no table talk. A strategy that depends on the score of a match is not measured.
* Points are one quarter of the rulebook's. Every ratio is the same.
* `hk-hkma-v1` has no 包 (liability) and several smaller differences, listed in `RULES.md`. A bot's row on it is a row under those rules.
* On the chicken-hand table a point is small. A chicken hand pays 1, a 1-faan hand 2, so the field bots' points a hand sit between -1.2 and +0.7 and most wins are cheap. The row shows who wins and who stays out of discarding, more than who builds the big hand. The scripted field was not tuned for a 0-faan minimum: the bots take any win offered, and `faan_aware` still counts ready hands under the table's rules.
* On HKMA most hands are draws, and big hands decide the score. Between 59% and 72% of baseline games end in a draw, because 3 faan is a high bar (on House the figure is 33% to 47%). The bots that win do so in 0% to 17% of games. A strong bot's edge is in the few big hands, so intervals are wide at low deal counts. 2,000 deals gave intervals of about plus or minus 0.15 to 0.45 points a hand for the baselines.
* Points a hand and head-to-head ranks can disagree. The first values big hands. The second counts which team came out ahead. In the baselines the Python example bot collects more points a hand than `faan_aware` against the field (+2.87 against +1.56, because it plays for triplets and gets 101 limit hands against 3), yet head to head `faan_aware` wins more games (450 to 223 out of 1,800) with the points level. Read both.
* The example bot beats the field. A short hand-written bot that keeps pairs and claims dragon and wind pongs finishes ahead of the field's best bot on points a hand. The field provides a reference score that stronger bots can exceed.
* Time limits depend on hardware. The limit is wall-clock time per decision (10 seconds). A bot that needs more will be asked to run on our machine with its own limit, which is then recorded.
* LLMs and humans are not scored yet. Those tracks need cost per hand and a place to play. They are empty.
* Third-party bots are not listed without their authors' agreement. None of their code, model files or results are in this repository. The protocol is documented so they can submit (`SUBMITTING.md`).

The [20 to 21 November 2026 results](RESULTS.md) list every run and the fairness checks.

## Results format

Each scored run writes one JSON file in `results/` (schema `hkbench-result-1`) and a gzip JSON-lines log of every game in `results/logs/`. A result records its seed scheme (`rng_scheme`: `hmac-sha256-v2`, or `splitmix-v1` for a file made before 1.1.0, which has no such field), the bot and its hash, the table, the rules hash, the field hashes, the deal tag and count, verification, the fair-play outcome, faults, the exact command, and the engine fingerprint. Public-deck logs carry each deal's seed and every action, and `hkbench verify-log` replays them.

## Maintenance

Maintained by Mahjong Sensei. Open an issue to report a rules error, a scoring bug, or a submission.
