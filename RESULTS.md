# Results: 20 to 23 November 2026

The 1.1.0 re-score finished at 05:34 EST on 21 November 2026, on bench version 1.1.0 (`hmac-sha256-v2`), Python 3.9.6 and 10 workers on one Apple-silicon Mac. It has 28 duplicate runs and six head-to-heads on HKMA Classical and House, on both decks. Eight outside bots were added on 21 and 22 November ([below](#outside-bots-on-the-bench)). Chicken hand was replaced on 22 November by `hk-chicken-v2`, where every win pays the same and the table is ranked by win rate. It was re-scored in full on 22 and 23 November, on bench version 1.2.0 and a new private deck: 14 duplicate runs and two head-to-heads for the original bots, 16 more runs for the outside bots, and a 12-bot head-to-head ([below](#hk-chicken-v2)).

Among the original bots, `Fu-2.3M-HKMA-1` came first on every table and deck: on points a hand on HKMA Classical and House, and on win rate on Chicken hand. With the outside bots added, it still leads on HKMA and House. On Chicken hand it shares first place with the three hk-mahjong-lab bots, whose intervals overlap its own, and Lucky Cat's five bots, which led the old points-a-hand ranking of the retired table, are far behind. We host it ourselves, so its results carry only a supplied hash, not its start command. It was trained on HKMA Classical rules; House and Chicken hand are rules it never trained on.

## Duplicate results

Each deal is played four times on the same wall, once from each seat. Points a hand are measured against the frozen reference field, except on Chicken hand, where every win pays the same and the table is ranked by win rate instead. The 95% confidence intervals (CI) count each deal as one sample, because its four games share a wall. Scores cannot be compared across tables because their payouts and rankings differ. Draw rate is the fraction of games that ended without a winner. Limit hands counts hands that reached the table's cap.

The source links identify each run. `native` is the recorded isolation for the in-process reference bots; program bots used `sandbox`.

### `hk-hkma-v1`

The following rows use the public deck.

| Bot | Points a hand [95% CI] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +17.45 [+16.77, +18.13] | 46.6% | 3.4% | 33.1% | 85 | 2,000 | unverified | sandbox | [20261121T004505](results/hk-hkma-v1__Fu-2.3M-HKMA-1__public__20261121T004505.json) |
| `python_example` | +2.87 [+2.43, +3.30] | 10.9% | 4.6% | 64.4% | 101 | 2,000 | unverified | sandbox | [20261121T001201](results/hk-hkma-v1__python_example__public__20261121T001201.json) |
| `faan_aware` | +1.56 [+1.33, +1.79] | 16.7% | 4.4% | 58.6% | 3 | 2,000 | unverified | native | [20261121T000455](results/hk-hkma-v1__faan_aware__public__20261121T000455.json) |
| `ukeire` | -0.93 [-1.10, -0.77] | 4.3% | 4.7% | 68.5% | 4 | 2,000 | unverified | native | [20261121T000312](results/hk-hkma-v1__ukeire__public__20261121T000312.json) |
| `deficiency` | -0.98 [-1.15, -0.82] | 4.0% | 4.7% | 68.9% | 4 | 2,000 | unverified | native | [20261121T000132](results/hk-hkma-v1__deficiency__public__20261121T000132.json) |
| `shallow_search` | -1.01 [-1.32, -0.71] | 3.5% | 4.5% | 71.4% | 0 | 400 | unverified | native | [20261121T001918](results/hk-hkma-v1__shallow_search__public__20261121T001918.json) |
| `random` | -1.89 [-2.05, -1.73] | 0.0% | 4.8% | 71.9% | 0 | 2,000 | unverified | native | [20261121T000004](results/hk-hkma-v1__random__public__20261121T000004.json) |

The following rows use the private deck.

| Bot | Points a hand [95% CI] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +17.75 [+17.08, +18.42] | 47.2% | 3.4% | 33.1% | 68 | 2,000 | verified | sandbox | [20261121T012618](results/hk-hkma-v1__Fu-2.3M-HKMA-1__private__20261121T012618.json) |
| `python_example` | +2.54 [+2.11, +2.97] | 9.8% | 4.5% | 65.5% | 99 | 2,000 | verified | sandbox | [20261121T005620](results/hk-hkma-v1__python_example__private__20261121T005620.json) |
| `faan_aware` | +1.61 [+1.37, +1.84] | 16.4% | 4.6% | 58.3% | 6 | 2,000 | verified | native | [20261121T005018](results/hk-hkma-v1__faan_aware__private__20261121T005018.json) |
| `ukeire` | -0.72 [-0.88, -0.55] | 4.8% | 4.5% | 68.9% | 3 | 2,000 | verified | native | [20261121T004858](results/hk-hkma-v1__ukeire__private__20261121T004858.json) |
| `deficiency` | -0.91 [-1.07, -0.75] | 4.4% | 4.6% | 68.6% | 1 | 2,000 | verified | native | [20261121T004738](results/hk-hkma-v1__deficiency__private__20261121T004738.json) |
| `shallow_search` | -0.94 [-1.24, -0.65] | 3.2% | 3.8% | 70.1% | 0 | 400 | verified | native | [20261121T010257](results/hk-hkma-v1__shallow_search__private__20261121T010257.json) |
| `random` | -1.81 [-1.95, -1.67] | 0.1% | 4.9% | 72.0% | 0 | 2,000 | verified | native | [20261121T004622](results/hk-hkma-v1__random__private__20261121T004622.json) |

### `hk-house-v1`

The following rows use the public deck.

| Bot | Points a hand [95% CI] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +16.83 [+15.95, +17.71] | 37.0% | 4.6% | 22.9% | 4 | 2,000 | unverified | sandbox | [20261121T041028](results/hk-house-v1__Fu-2.3M-HKMA-1__public__20261121T041028.json) |
| `python_example` | +2.35 [+1.83, +2.87] | 13.7% | 6.6% | 39.9% | 2 | 2,000 | unverified | sandbox | [20261121T034023](results/hk-house-v1__python_example__public__20261121T034023.json) |
| `faan_aware` | +1.65 [+1.38, +1.93] | 22.8% | 5.7% | 32.8% | 1 | 2,000 | unverified | native | [20261121T033407](results/hk-house-v1__faan_aware__public__20261121T033407.json) |
| `ukeire` | -0.76 [-0.95, -0.57] | 12.3% | 5.9% | 40.2% | 0 | 2,000 | unverified | native | [20261121T033235](results/hk-house-v1__ukeire__public__20261121T033235.json) |
| `shallow_search` | -0.79 [-1.21, -0.36] | 13.7% | 6.2% | 37.2% | 0 | 400 | unverified | native | [20261121T034656](results/hk-house-v1__shallow_search__public__20261121T034656.json) |
| `deficiency` | -0.85 [-1.04, -0.65] | 11.2% | 6.1% | 40.8% | 0 | 2,000 | unverified | native | [20261121T033114](results/hk-house-v1__deficiency__public__20261121T033114.json) |
| `random` | -2.95 [-3.11, -2.79] | 0.1% | 7.3% | 46.6% | 0 | 2,000 | unverified | native | [20261121T033004](results/hk-house-v1__random__public__20261121T033004.json) |

The following rows use the private deck.

| Bot | Points a hand [95% CI] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +17.67 [+16.76, +18.58] | 37.4% | 4.9% | 22.8% | 8 | 2,000 | verified | sandbox | [20261121T045103](results/hk-house-v1__Fu-2.3M-HKMA-1__private__20261121T045103.json) |
| `python_example` | +2.79 [+2.25, +3.33] | 13.8% | 5.6% | 39.5% | 3 | 2,000 | verified | sandbox | [20261121T042116](results/hk-house-v1__python_example__private__20261121T042116.json) |
| `faan_aware` | +1.57 [+1.30, +1.83] | 21.8% | 5.4% | 33.8% | 0 | 2,000 | verified | native | [20261121T041517](results/hk-house-v1__faan_aware__private__20261121T041517.json) |
| `shallow_search` | -0.35 [-0.73, +0.03] | 15.0% | 4.9% | 39.1% | 0 | 400 | verified | native | [20261121T042717](results/hk-house-v1__shallow_search__private__20261121T042717.json) |
| `ukeire` | -0.85 [-1.04, -0.66] | 12.1% | 5.7% | 40.2% | 0 | 2,000 | verified | native | [20261121T041402](results/hk-house-v1__ukeire__private__20261121T041402.json) |
| `deficiency` | -0.93 [-1.14, -0.71] | 11.9% | 5.7% | 40.1% | 0 | 2,000 | verified | native | [20261121T041244](results/hk-house-v1__deficiency__private__20261121T041244.json) |
| `random` | -2.82 [-2.95, -2.69] | 0.1% | 7.0% | 47.4% | 0 | 2,000 | verified | native | [20261121T041134](results/hk-house-v1__random__private__20261121T041134.json) |

### `hk-chicken-v2`

Chicken hand. The minimum is 0 faan and every win pays the same: the winner collects 3 and each other seat pays 1, whether the win was self-drawn or off a discard. Rows are ranked by win rate, the share of games the bot won. Because the payment is flat, points a hand would only be 4 x win rate - (1 - draw rate). This table replaced `hk-chicken-v1` (see [what changed](#what-changed-from-hk-chicken-v1)).

The following rows use the public deck.

| Bot | Win rate [95% CI] | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | 49.3% [48.2%, 50.3%] | 13.2% | 0.6% | 1 | 2,000 | unverified | sandbox | [20261123T040306](results/hk-chicken-v2__Fu-2.3M-HKMA-1__public__20261123T040306.json) |
| `shallow_search` | 33.4% [31.0%, 35.8%] | 17.4% | 1.5% | 0 | 400 | unverified | native | [20261123T031225](results/hk-chicken-v2__shallow_search__public__20261123T031225.json) |
| `faan_aware` | 27.4% [26.5%, 28.3%] | 18.9% | 2.1% | 3 | 2,000 | unverified | native | [20261123T025154](results/hk-chicken-v2__faan_aware__public__20261123T025154.json) |
| `ukeire` | 23.2% [22.4%, 24.1%] | 18.7% | 2.8% | 0 | 2,000 | unverified | native | [20261123T024932](results/hk-chicken-v2__ukeire__public__20261123T024932.json) |
| `deficiency` | 22.1% [21.3%, 23.0%] | 19.0% | 2.9% | 0 | 2,000 | unverified | native | [20261123T024558](results/hk-chicken-v2__deficiency__public__20261123T024558.json) |
| `python_example` | 8.4% [7.8%, 9.0%] | 23.8% | 5.1% | 23 | 2,000 | unverified | sandbox | [20261123T025948](results/hk-chicken-v2__python_example__public__20261123T025948.json) |
| `random` | 0.2% [0.1%, 0.3%] | 25.2% | 5.8% | 0 | 2,000 | unverified | native | [20261123T024352](results/hk-chicken-v2__random__public__20261123T024352.json) |

The following rows use the private deck.

| Bot | Win rate [95% CI] | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | 49.0% [48.0%, 50.1%] | 13.5% | 0.6% | 3 | 2,000 | verified | sandbox | [20261123T070750](results/hk-chicken-v2__Fu-2.3M-HKMA-1__private__20261123T070750.json) |
| `shallow_search` | 31.4% [29.2%, 33.7%] | 17.5% | 1.9% | 0 | 400 | verified | native | [20261123T062619](results/hk-chicken-v2__shallow_search__private__20261123T062619.json) |
| `faan_aware` | 26.8% [25.9%, 27.7%] | 18.6% | 2.1% | 2 | 2,000 | verified | native | [20261123T061213](results/hk-chicken-v2__faan_aware__private__20261123T061213.json) |
| `ukeire` | 23.4% [22.5%, 24.3%] | 18.7% | 2.7% | 1 | 2,000 | verified | native | [20261123T061027](results/hk-chicken-v2__ukeire__private__20261123T061027.json) |
| `deficiency` | 22.7% [21.8%, 23.6%] | 20.1% | 2.6% | 1 | 2,000 | verified | native | [20261123T060844](results/hk-chicken-v2__deficiency__private__20261123T060844.json) |
| `python_example` | 8.4% [7.8%, 9.0%] | 22.8% | 5.1% | 11 | 2,000 | verified | sandbox | [20261123T061714](results/hk-chicken-v2__python_example__private__20261123T061714.json) |
| `random` | 0.2% [0.1%, 0.4%] | 26.4% | 5.3% | 0 | 2,000 | verified | native | [20261123T060712](results/hk-chicken-v2__random__private__20261123T060712.json) |

#### What changed from `hk-chicken-v1`

`hk-chicken-v1` paid by faan, so a bot that built big hands scored more than a bot that won more often. Its files stay in `results/` and its logs still replay, but it is off the board, the chart and this page. The bots play the same on both tables, because a bot is never told the payment; the order moves because the ranking changed. This table gives the private-deck rows for every bot that was on the old table, old rank by points a hand beside new rank by win rate. Ranks follow the rule used everywhere on this page: 1 plus the number of bots whose 95% interval lies entirely above the bot's.

| Bot | v1: points a hand | v1 rank | v2: win rate | v2 rank | v2 deal-in |
|---|---|---|---|---|---|
| `hk-mahjong-lab-PIMC-128` | +1.06 | 6 | 52.1% | 1 | 12.4% |
| `hk-mahjong-lab-value` | +0.84 | 6 | 50.8% | 1 | 12.2% |
| `Fu-2.3M-HKMA-1` | +0.64 | 9 | 49.0% | 1 | 13.5% |
| `hk-mahjong-lab-PIMC-256` | +1.13 | 5 | 48.8% | 1 | 12.2% |
| `shallow_search` | +0.13 | 11 | 31.4% | 5 | 17.5% |
| `faan_aware` | +0.41 | 10 | 26.8% | 6 | 18.6% |
| `ukeire` | -0.17 | 12 | 23.4% | 7 | 18.7% |
| `deficiency` | -0.18 | 12 | 22.7% | 7 | 20.1% |
| `LuckyCat-JorgeYau` | +1.70 | 1 | 16.3% | 9 | 17.4% |
| `LuckyCat-lc34` | +2.15 | 1 | 11.9% | 10 | 22.5% |
| `NeuralCat-NC10` | +1.94 | 1 | 11.5% | 10 | 19.8% |
| `LuckyCat-lc32` | +1.88 | 1 | 11.2% | 10 | 22.8% |
| `NeuralCat-NC9` | +1.90 | 1 | 9.9% | 12 | 21.0% |
| `python_example` | -0.14 | 11 | 8.4% | 14 | 22.8% |
| `random` | -1.19 | 15 | 0.2% | 15 | 26.4% |

The five Lucky Cat bots held the top rank by points a hand, because their wins included big hands. They win only 10% to 16% of games. By win rate they are in the lower half, and `LuckyCat-JorgeYau` is the best of them. The three hk-mahjong-lab bots and `Fu-2.3M-HKMA-1` win about half of all games, and their intervals overlap, so they share first place.

## Head-to-head results

Each pair plays 300 deals in all six seat pairs. Ratings use Bradley-Terry on the Elo scale, with 95% CIs from bootstrapping whole deals. On HKMA Classical and House a team wins a hand when it has more points. On Chicken hand a team wins a hand when one of its two seats wins it, whoever pays, and a drawn hand is a tie. Rank is 1 plus the number of bots whose interval lies entirely above that bot's interval. Overlapping intervals share a rank. The public five-bot runs and public six-bot runs are separate runs; ratings belong to the field in that run. Chicken hand has one public six-bot run and one private six-bot run.

### `hk-hkma-v1`, public, 5 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-hkma-v1__h2h__public__20261121T013727.json).

| Bot | Rating [95% CI] | Rank |
|---|---|---|
| `faan_aware` | +58.6 [+55.0, +62.7] | 1 |
| `python_example` | +14.3 [+11.4, +17.2] | 2 |
| `ukeire` | -12.1 [-15.2, -9.4] | 3 |
| `deficiency` | -14.6 [-17.1, -12.1] | 3 |
| `random` | -46.1 [-48.6, -43.4] | 5 |

### `hk-hkma-v1`, public, 6 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-hkma-v1__h2h__public__20261121T023322.json).

| Bot | Rating [95% CI] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +156.3 [+151.3, +161.5] | 1 |
| `faan_aware` | +24.6 [+21.1, +28.6] | 2 |
| `python_example` | -14.2 [-17.3, -11.0] | 3 |
| `ukeire` | -42.3 [-45.4, -39.3] | 4 |
| `deficiency` | -45.8 [-48.7, -42.9] | 4 |
| `random` | -78.6 [-81.6, -75.8] | 6 |

### `hk-hkma-v1`, private, 6 bots

This run is verified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-hkma-v1__h2h__private__20261121T032901.json).

| Bot | Rating [95% CI] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +151.6 [+147.0, +156.4] | 1 |
| `faan_aware` | +25.2 [+21.5, +29.1] | 2 |
| `python_example` | -9.8 [-13.1, -6.6] | 3 |
| `ukeire` | -43.6 [-46.4, -40.5] | 4 |
| `deficiency` | -47.7 [-50.1, -45.1] | 4 |
| `random` | -75.7 [-78.3, -73.0] | 6 |

### `hk-house-v1`, public, 5 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-house-v1__h2h__public__20261121T050310.json).

| Bot | Rating [95% CI] | Rank |
|---|---|---|
| `faan_aware` | +74.1 [+69.3, +79.2] | 1 |
| `python_example` | +11.0 [+7.0, +15.0] | 2 |
| `ukeire` | +9.9 [+5.8, +14.0] | 2 |
| `deficiency` | +0.3 [-3.2, +3.9] | 4 |
| `random` | -95.2 [-98.7, -91.5] | 5 |

### `hk-house-v1`, public, 6 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-house-v1__h2h__public__20261121T060610.json).

| Bot | Rating [95% CI] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +111.4 [+106.0, +116.8] | 1 |
| `faan_aware` | +52.2 [+47.5, +57.0] | 2 |
| `python_example` | -8.8 [-12.7, -4.5] | 3 |
| `ukeire` | -12.1 [-16.6, -8.3] | 3 |
| `deficiency` | -22.2 [-25.8, -18.0] | 5 |
| `random` | -120.5 [-124.3, -117.2] | 6 |

### `hk-house-v1`, private, 6 bots

This run is verified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-house-v1__h2h__private__20261121T070833.json).

| Bot | Rating [95% CI] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +106.7 [+101.1, +112.1] | 1 |
| `faan_aware` | +50.7 [+45.9, +55.5] | 2 |
| `ukeire` | -9.3 [-13.4, -5.3] | 3 |
| `python_example` | -12.0 [-16.1, -8.2] | 3 |
| `deficiency` | -21.4 [-24.8, -18.1] | 5 |
| `random` | -114.6 [-118.2, -111.0] | 6 |

### `hk-chicken-v2`, public, 6 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-chicken-v2__h2h__public__20261123T104306.json).

| Bot | Rating [95% CI] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +259.2 [+252.0, +266.7] | 1 |
| `faan_aware` | +97.7 [+90.9, +104.6] | 2 |
| `ukeire` | +58.8 [+53.1, +66.0] | 3 |
| `deficiency` | +42.1 [+36.6, +48.1] | 4 |
| `python_example` | -121.0 [-127.2, -114.1] | 5 |
| `random` | -336.8 [-344.7, -330.0] | 6 |

### `hk-chicken-v2`, private, 6 bots

This run is verified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-chicken-v2__h2h__private__20261123T121813.json).

| Bot | Rating [95% CI] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +258.7 [+250.3, +267.5] | 1 |
| `faan_aware` | +91.3 [+85.0, +97.7] | 2 |
| `ukeire` | +58.8 [+52.7, +64.9] | 3 |
| `deficiency` | +46.7 [+41.9, +52.7] | 3 |
| `python_example` | -118.1 [-125.5, -111.4] | 5 |
| `random` | -337.4 [-344.7, -330.7] | 6 |

## Fairness checks

A new private deck contained 10,000 independent random 64-bit seeds, made with `scripts/make_private_deck.py`. It was kept outside the repository and is not published. The reference field matched its pinned hashes, and the engine reproduced each table's fingerprint before scoring. The bench refuses to score if either check fails.

For private runs, each decision's `rng_seed` and each game's `game_id` came from HMAC-SHA256 under a per-run secret key that no bot sees. A bot cannot work back from these identifiers to the deal. Public runs use a fixed public key so they can be reproduced.

Every program bot in the original run (`python_example` and `Fu-2.3M-HKMA-1`) started fresh for every game and ran under `scripts/sandbox/macos.sh`. It had no network or child processes, could write only to its own empty folder, and could not read the deck file. Reference bots ran inside the bench.

All 50 original runs (the 28 HKMA and House duplicate runs, six head-to-heads, and the 14 duplicate runs and two head-to-heads on `hk-chicken-v2`) passed the fair-play check with 0 decision changes and 0 view mismatches, and none exceeded the fault limit. Every private run is tagged verified. All 265,800 public games in 26 public logs replayed with `hkbench verify-log` with 0 mismatches. (The 1.1.0 re-score had 283,800 in 27 logs; the 94,600 on the retired Chicken hand table are replaced by the 76,600 on `hk-chicken-v2`, which has one public head-to-head, not two.)

The table below gives the evidence recorded in each result JSON. Duplicate runs record the full fair-play counts and used two reshuffles at each checked point. Head-to-head files record only `passed` for each bot, so their counts are shown as “not recorded” rather than inferred from another run. Faults are summed across bots for head-to-head runs. Fair-play faults and scored-play faults are separate counts.

| Table | Deck | Bot or field | Source | Fair play | Asks | Decision changes | View mismatches | Fair-play faults | Scored-play faults |
|---|---|---|---|---|---|---|---|---|---|
| `hk-hkma-v1` | private | random | [20261121T004622](results/hk-hkma-v1__random__private__20261121T004622.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | private | deficiency | [20261121T004738](results/hk-hkma-v1__deficiency__private__20261121T004738.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | private | ukeire | [20261121T004858](results/hk-hkma-v1__ukeire__private__20261121T004858.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | private | faan_aware | [20261121T005018](results/hk-hkma-v1__faan_aware__private__20261121T005018.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | private | python_example | [20261121T005620](results/hk-hkma-v1__python_example__private__20261121T005620.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | private | shallow_search | [20261121T010257](results/hk-hkma-v1__shallow_search__private__20261121T010257.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | private | Fu-2.3M-HKMA-1 | [20261121T012618](results/hk-hkma-v1__Fu-2.3M-HKMA-1__private__20261121T012618.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | private | 6-bot head-to-head | [20261121T032901](results/hk-hkma-v1__h2h__private__20261121T032901.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |
| `hk-hkma-v1` | public | random | [20261121T000004](results/hk-hkma-v1__random__public__20261121T000004.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | public | deficiency | [20261121T000132](results/hk-hkma-v1__deficiency__public__20261121T000132.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | public | ukeire | [20261121T000312](results/hk-hkma-v1__ukeire__public__20261121T000312.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | public | faan_aware | [20261121T000455](results/hk-hkma-v1__faan_aware__public__20261121T000455.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | public | python_example | [20261121T001201](results/hk-hkma-v1__python_example__public__20261121T001201.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | public | shallow_search | [20261121T001918](results/hk-hkma-v1__shallow_search__public__20261121T001918.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | public | Fu-2.3M-HKMA-1 | [20261121T004505](results/hk-hkma-v1__Fu-2.3M-HKMA-1__public__20261121T004505.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-hkma-v1` | public | 5-bot head-to-head | [20261121T013727](results/hk-hkma-v1__h2h__public__20261121T013727.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |
| `hk-hkma-v1` | public | 6-bot head-to-head | [20261121T023322](results/hk-hkma-v1__h2h__public__20261121T023322.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |
| `hk-house-v1` | private | random | [20261121T041134](results/hk-house-v1__random__private__20261121T041134.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | private | deficiency | [20261121T041244](results/hk-house-v1__deficiency__private__20261121T041244.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | private | ukeire | [20261121T041402](results/hk-house-v1__ukeire__private__20261121T041402.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | private | faan_aware | [20261121T041517](results/hk-house-v1__faan_aware__private__20261121T041517.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | private | python_example | [20261121T042116](results/hk-house-v1__python_example__private__20261121T042116.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | private | shallow_search | [20261121T042717](results/hk-house-v1__shallow_search__private__20261121T042717.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | private | Fu-2.3M-HKMA-1 | [20261121T045103](results/hk-house-v1__Fu-2.3M-HKMA-1__private__20261121T045103.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | private | 6-bot head-to-head | [20261121T070833](results/hk-house-v1__h2h__private__20261121T070833.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |
| `hk-house-v1` | public | random | [20261121T033004](results/hk-house-v1__random__public__20261121T033004.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | public | deficiency | [20261121T033114](results/hk-house-v1__deficiency__public__20261121T033114.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | public | ukeire | [20261121T033235](results/hk-house-v1__ukeire__public__20261121T033235.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | public | faan_aware | [20261121T033407](results/hk-house-v1__faan_aware__public__20261121T033407.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | public | python_example | [20261121T034023](results/hk-house-v1__python_example__public__20261121T034023.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | public | shallow_search | [20261121T034656](results/hk-house-v1__shallow_search__public__20261121T034656.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | public | Fu-2.3M-HKMA-1 | [20261121T041028](results/hk-house-v1__Fu-2.3M-HKMA-1__public__20261121T041028.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-house-v1` | public | 5-bot head-to-head | [20261121T050310](results/hk-house-v1__h2h__public__20261121T050310.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |
| `hk-house-v1` | public | 6-bot head-to-head | [20261121T060610](results/hk-house-v1__h2h__public__20261121T060610.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |
| `hk-chicken-v2` | private | random | [20261123T060712](results/hk-chicken-v2__random__private__20261123T060712.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | private | deficiency | [20261123T060844](results/hk-chicken-v2__deficiency__private__20261123T060844.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | private | ukeire | [20261123T061027](results/hk-chicken-v2__ukeire__private__20261123T061027.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | private | faan_aware | [20261123T061213](results/hk-chicken-v2__faan_aware__private__20261123T061213.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | private | python_example | [20261123T061714](results/hk-chicken-v2__python_example__private__20261123T061714.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | private | shallow_search | [20261123T062619](results/hk-chicken-v2__shallow_search__private__20261123T062619.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | private | Fu-2.3M-HKMA-1 | [20261123T070750](results/hk-chicken-v2__Fu-2.3M-HKMA-1__private__20261123T070750.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | public | random | [20261123T024352](results/hk-chicken-v2__random__public__20261123T024352.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | public | deficiency | [20261123T024558](results/hk-chicken-v2__deficiency__public__20261123T024558.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | public | ukeire | [20261123T024932](results/hk-chicken-v2__ukeire__public__20261123T024932.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | public | faan_aware | [20261123T025154](results/hk-chicken-v2__faan_aware__public__20261123T025154.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | public | python_example | [20261123T025948](results/hk-chicken-v2__python_example__public__20261123T025948.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | public | shallow_search | [20261123T031225](results/hk-chicken-v2__shallow_search__public__20261123T031225.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | public | Fu-2.3M-HKMA-1 | [20261123T040306](results/hk-chicken-v2__Fu-2.3M-HKMA-1__public__20261123T040306.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v2` | private | 6-bot head-to-head | [20261123T121813](results/hk-chicken-v2__h2h__private__20261123T121813.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |
| `hk-chicken-v2` | public | 6-bot head-to-head | [20261123T104306](results/hk-chicken-v2__h2h__public__20261123T104306.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |

A verified tag means the run used private deals, passed the hidden-tile fair-play check and stayed within the fault limit. Program bots also need a sandbox. The check changes hidden tiles while keeping the bot's view unchanged and asks for the decision again. It mainly checks the harness; it can also catch a bot that accesses hidden state through another channel or ignores the supplied random seed.

The tag does not audit a bot's code or prove that it had the same thinking time, tools or help as a human. The hosted bot's implementation is private, and its supplied hash is not an independent audit. The field consists of three scripted bots with crude claim play and no defence. These scores measure play against that field, not strength against careful humans or adapting opponents. The bench measures single hands, with the rulebook gaps described in [RULES.md](RULES.md). See the [benchmark card's limits](BENCHMARK_CARD.md#known-limits).

## Check a public result

This command reproduces the public `faan_aware` row on `hk-hkma-v1`. We ran it again after the run finished and got the same numbers to the last digit.

```
python -m hkbench score --table hk-hkma-v1 --bot ref:faan_aware --deals 2000 --workers 10
```

Replay any public log by giving its file name to `verify-log`. For example:

```
python -m hkbench verify-log results/logs/hk-hkma-v1__faan_aware__public__20261121T000455.jsonl.gz
python -m hkbench fingerprint --table hk-hkma-v1
python -m hkbench tables
```

`verify-log` rebuilds games from their seeds and actions and checks the recorded payments. `fingerprint` checks that the engine reproduces the table's fixed deals and hands. `tables` lists the tables and checks the reference field pins. Use the other table ids to check their fingerprints.

Outsiders cannot re-run private rows because the deck is secret. Private logs contain outcomes without seeds or actions, so they cannot be replayed with `verify-log` either. A private deck can also wear out through repeated tuning against its results; it should be retired when a table is superseded or after enough repeated scoring to matter.

## Outside bots on the bench

On 21 and 22 November 2026 we ran eight bots from two other projects through the bench: the same protocol and the same deals, scored by `hkbench` like every other row. They are on the leaderboard and the chart. Five come from [Lucky Cat Mahjong](https://huggingface.co/codenameyau/lucky-cat-mahjong) and three from [hk-mahjong-lab](https://github.com/bpy13/hk-mahjong-lab); `LuckyCat-JorgeYau` and `hk-mahjong-lab-value` are rule-based. We ran them from their authors' public code. The authors didn't submit them, and they can replace them with their own entries at any time. Neither project has a licence, so none of their code or weights, and none of our adapters for them, are in this repository.

Each bot played all three tables, on the public deck and then the secret deck, 2,000 deals a run. The PIMC search players are slow, so they played 400. That makes 48 runs, plus a 100-deal head-to-head on each table's secret deck. Every run had 0 faults, passed the fair-play check and ran in the sandbox, every secret-deck run is verified, and every public game replays exactly. Lucky Cat's bots start a JavaScript process from Python, so their sandbox allows that one child process.

Before scoring, we checked each adapter against the harness we had used for our earlier matches with these bots. Lucky Cat made the same move on all of about 139,000 decisions, and hk-mahjong-lab's value bot on all of about 30,000. PIMC differed on 0.6% to 1.7% of decisions. Every difference came from two facts the bench's message doesn't carry (see below): with the same two facts hidden from the old harness, the differences went away.

The tables give points a hand on the secret deck against the reference field, as everywhere else on this page, except Chicken hand, which gives win rate. Each bot links to its result file. For comparison, `Fu-2.3M-HKMA-1` scores +17.75 on HKMA, +17.67 on House and a 49.0% win rate on Chicken hand.

### HKMA Classical, secret deck

| Bot | Points a hand | 95% CI | Deals | Faults/decisions |
|---|---|---|---|---|
| [`hk-mahjong-lab-PIMC-256`](results/hk-hkma-v1__hk-mahjong-lab-PIMC-256__private__20261122T083043.json) | +13.69 | [+12.50, +14.87] | 400 | 0/37,832 |
| [`hk-mahjong-lab-PIMC-128`](results/hk-hkma-v1__hk-mahjong-lab-PIMC-128__private__20261122T075727.json) | +13.46 | [+12.23, +14.70] | 400 | 0/37,885 |
| [`LuckyCat-lc34`](results/hk-hkma-v1__LuckyCat-lc34__private__20261121T223054.json) | +11.46 | [+10.86, +12.05] | 2,000 | 0/198,872 |
| [`NeuralCat-NC10`](results/hk-hkma-v1__NeuralCat-NC10__private__20261121T224751.json) | +11.38 | [+10.68, +12.08] | 2,000 | 0/203,844 |
| [`hk-mahjong-lab-value`](results/hk-hkma-v1__hk-mahjong-lab-value__private__20261121T230118.json) | +11.23 | [+10.75, +11.71] | 2,000 | 0/188,847 |
| [`NeuralCat-NC9`](results/hk-hkma-v1__NeuralCat-NC9__private__20261121T223923.json) | +11.16 | [+10.45, +11.87] | 2,000 | 0/205,319 |
| [`LuckyCat-lc32`](results/hk-hkma-v1__LuckyCat-lc32__private__20261121T222306.json) | +10.60 | [+10.03, +11.17] | 2,000 | 0/199,779 |
| [`LuckyCat-JorgeYau`](results/hk-hkma-v1__LuckyCat-JorgeYau__private__20261121T225525.json) | +8.91 | [+8.33, +9.48] | 2,000 | 0/210,897 |

### House, secret deck

| Bot | Points a hand | 95% CI | Deals | Faults/decisions |
|---|---|---|---|---|
| [`hk-mahjong-lab-PIMC-256`](results/hk-house-v1__hk-mahjong-lab-PIMC-256__private__20261122T150207.json) | +15.09 | [+13.03, +17.16] | 400 | 0/35,224 |
| [`NeuralCat-NC9`](results/hk-house-v1__NeuralCat-NC9__private__20261122T015325.json) | +12.81 | [+11.62, +13.99] | 2,000 | 0/185,998 |
| [`NeuralCat-NC10`](results/hk-house-v1__NeuralCat-NC10__private__20261122T020144.json) | +12.79 | [+11.67, +13.91] | 2,000 | 0/184,742 |
| [`hk-mahjong-lab-PIMC-128`](results/hk-house-v1__hk-mahjong-lab-PIMC-128__private__20261122T090321.json) | +12.72 | [+11.19, +14.25] | 400 | 0/34,979 |
| [`hk-mahjong-lab-value`](results/hk-house-v1__hk-mahjong-lab-value__private__20261122T021501.json) | +11.70 | [+10.90, +12.49] | 2,000 | 0/175,398 |
| [`LuckyCat-lc34`](results/hk-house-v1__LuckyCat-lc34__private__20261122T014500.json) | +10.87 | [+10.13, +11.62] | 2,000 | 0/181,787 |
| [`LuckyCat-lc32`](results/hk-house-v1__LuckyCat-lc32__private__20261122T013716.json) | +10.40 | [+9.67, +11.14] | 2,000 | 0/183,073 |
| [`LuckyCat-JorgeYau`](results/hk-house-v1__LuckyCat-JorgeYau__private__20261122T020909.json) | +10.04 | [+9.11, +10.97] | 2,000 | 0/188,844 |

### Chicken hand, secret deck

Win rate and deal-in rate on `hk-chicken-v2`, ranked by win rate. Every win pays the same there.

| Bot | Win rate | 95% CI | Deal-in | Deals | Faults/decisions |
|---|---|---|---|---|---|
| [`hk-mahjong-lab-PIMC-128`](results/hk-chicken-v2__hk-mahjong-lab-PIMC-128__private__20261123T083715.json) | 52.1% | [49.7%, 54.6%] | 12.4% | 400 | 0/23,418 |
| [`hk-mahjong-lab-value`](results/hk-chicken-v2__hk-mahjong-lab-value__private__20261123T082010.json) | 50.8% | [49.8%, 51.9%] | 12.2% | 2,000 | 0/114,158 |
| [`hk-mahjong-lab-PIMC-256`](results/hk-chicken-v2__hk-mahjong-lab-PIMC-256__private__20261123T090829.json) | 48.8% | [46.4%, 51.2%] | 12.2% | 400 | 0/23,114 |
| [`LuckyCat-JorgeYau`](results/hk-chicken-v2__LuckyCat-JorgeYau__private__20261123T081321.json) | 16.3% | [15.6%, 17.1%] | 17.4% | 2,000 | 0/138,286 |
| [`LuckyCat-lc34`](results/hk-chicken-v2__LuckyCat-lc34__private__20261123T073326.json) | 11.9% | [11.2%, 12.6%] | 22.5% | 2,000 | 0/135,103 |
| [`NeuralCat-NC10`](results/hk-chicken-v2__NeuralCat-NC10__private__20261123T080146.json) | 11.5% | [10.8%, 12.2%] | 19.8% | 2,000 | 0/135,992 |
| [`LuckyCat-lc32`](results/hk-chicken-v2__LuckyCat-lc32__private__20261123T072045.json) | 11.2% | [10.5%, 11.9%] | 22.8% | 2,000 | 0/135,656 |
| [`NeuralCat-NC9`](results/hk-chicken-v2__NeuralCat-NC9__private__20261123T074744.json) | 9.9% | [9.2%, 10.5%] | 21.0% | 2,000 | 0/136,577 |

### Secret-deck head-to-heads

Here the bots play each other: five reference bots, `Fu-2.3M-HKMA-1` and the six outside bots other than PIMC, which is too slow for a field this size. Bradley-Terry ratings compare them directly. `hk-mahjong-lab-value` and Fu share first place on all three tables; value's rating is a little higher, but the intervals overlap. The Chicken hand table rates bots by who won the hand, not by points.

#### `hk-chicken-v2`

This run is verified with isolation `sandbox`. It used 100 deals per pair. [Source JSON](results/hk-chicken-v2__h2h__private__20261123T145355.json).

| Bot | Rating [95% CI] | Rank |
|---|---|---|
| `hk-mahjong-lab-value` | +269.0 [+258.9, +279.6] | 1 |
| `Fu-2.3M-HKMA-1` | +253.8 [+244.4, +263.3] | 1 |
| `faan_aware` | +104.8 [+96.4, +113.1] | 3 |
| `ukeire` | +61.2 [+53.4, +69.0] | 4 |
| `deficiency` | +46.5 [+39.5, +53.2] | 5 |
| `LuckyCat-JorgeYau` | -22.8 [-31.1, -14.7] | 6 |
| `LuckyCat-lc34` | -54.5 [-62.9, -46.3] | 7 |
| `LuckyCat-lc32` | -59.7 [-68.0, -52.1] | 7 |
| `NeuralCat-NC10` | -60.6 [-69.1, -52.7] | 7 |
| `NeuralCat-NC9` | -85.5 [-94.0, -77.1] | 10 |
| `python_example` | -113.9 [-121.9, -105.6] | 11 |
| `random` | -338.3 [-346.4, -330.8] | 12 |

#### `hk-hkma-v1`

[Source JSON](results/hk-hkma-v1__h2h__private__20261122T004409.json).

| Bot | Rating | 95% CI | Rank |
|---|---|---|---|
| `hk-mahjong-lab-value` | +112.81 | [+106.66, +119.02] | 1 |
| `Fu-2.3M-HKMA-1` | +105.78 | [+99.81, +112.42] | 1 |
| `LuckyCat-lc34` | +55.28 | [+49.46, +61.61] | 3 |
| `LuckyCat-lc32` | +47.41 | [+41.40, +53.11] | 3 |
| `NeuralCat-NC10` | +30.00 | [+24.57, +35.42] | 5 |
| `LuckyCat-JorgeYau` | +23.81 | [+17.72, +29.56] | 5 |
| `NeuralCat-NC9` | +22.64 | [+17.19, +27.79] | 5 |
| `faan_aware` | -30.18 | [-34.90, -25.29] | 8 |
| `python_example` | -58.74 | [-64.10, -53.58] | 9 |
| `ukeire` | -89.47 | [-94.10, -85.36] | 10 |
| `deficiency` | -91.56 | [-95.70, -87.18] | 10 |
| `random` | -127.78 | [-132.35, -123.45] | 12 |

#### `hk-house-v1`

[Source JSON](results/hk-house-v1__h2h__private__20261122T035801.json).

| Bot | Rating | 95% CI | Rank |
|---|---|---|---|
| `hk-mahjong-lab-value` | +81.86 | [+76.08, +88.49] | 1 |
| `Fu-2.3M-HKMA-1` | +72.46 | [+67.18, +78.99] | 1 |
| `LuckyCat-lc34` | +32.57 | [+26.04, +39.69] | 3 |
| `LuckyCat-JorgeYau` | +29.97 | [+23.52, +35.80] | 3 |
| `LuckyCat-lc32` | +27.91 | [+21.67, +34.49] | 3 |
| `NeuralCat-NC10` | +23.67 | [+17.83, +29.72] | 3 |
| `NeuralCat-NC9` | +23.07 | [+16.93, +28.70] | 3 |
| `faan_aware` | +10.21 | [+4.32, +16.01] | 8 |
| `ukeire` | -42.16 | [-47.68, -36.79] | 9 |
| `python_example` | -49.55 | [-56.11, -43.89] | 9 |
| `deficiency` | -55.36 | [-60.66, -50.02] | 10 |
| `random` | -154.65 | [-159.77, -149.43] | 12 |

### Where the adapters approximate

Lucky Cat remembers its own seat's earlier messages within a game, such as its current plan and whether it has committed to a big hand. The protocol now allows that. Without the memory, 3% to 7% of its moves change.

Lucky Cat's engine wants to know when an opponent declared a concealed kong. The message shows the kong but not when it happened, so the adapter uses that opponent's discard count at Lucky Cat's previous decision. It can be a few discards late.

hk-mahjong-lab's library ends a hand at seven flowers. The bench's rules let a seat show more, which happens in about 1 game in 600. When it does, the adapter hides the extra flowers from the library and counts them as wall tiles.

The message doesn't say whether a discard was the tile just drawn, or how deep a chain of kongs goes. PIMC's search uses both, so here it plays without them.

### Their rules, not ours

These rows measure each bot on the bench's tables, not on its own. Lucky Cat's bots were built for a 3 faan minimum, flower faan, Seven Pairs and a full-spicy payout. hk-mahjong-lab plays a 10 faan cap and models a single East hand. `Fu-2.3M-HKMA-1` trained on HKMA rules, which gives it a home advantage there.

## Earlier matches in our own harness

Before the bench rows above, we played these bots in our own evaluation harness on 16 and 19 November 2026. The bench rows replace them, and we keep them for the record. They are not on the leaderboard, and they use that harness's own point scale, so they can't be compared with the bench numbers.

The matches used duplicate two-against-two play. Two Fu-2.3M-HKMA-1 seats played two seats of one outside bot, and every wall was played from all six seatings. A deal is six games on one wall, and the intervals are t-intervals over deals. The reported lead is the team of two seats' points a game, with positive values meaning Fu-2.3M-HKMA-1 is ahead. Halve it for a single seat.

The walls came from our own seed range, separate from the bench's private deck. Unless a row says otherwise, the rules were our HKMA Classical table, with no flower faan, no Seven Pairs and a 10 faan cap. The 3-faan with flowers table has a 3 faan minimum, flowers score and the cap is 13 faan. Fu-2.3M-HKMA-1 played its best move every time, with no sampling. Every run finished with 0 failed games.

Each outside bot used its authors' own code. Lucky Cat's bots ran in their own JavaScript, and hk-mahjong-lab's bots were built from its public Rust source. Each bot received only what its seat could see. Before scoring, every move replayed identically on 5,374 real decisions from Lucky Cat's engine, and on 5,295 more from its newest release. The hk-mahjong-lab value bot matched its own engine on 320 of 320 positions, and its PIMC solver matched on 210 of 210. Shuffling every hidden tile changed no bot's decision.

Lucky Cat lc32 and Neural Cat NC9 came from the [Lucky Cat Mahjong models page](https://huggingface.co/codenameyau/lucky-cat-mahjong). Lucky Cat lc34 and Neural Cat NC10 came from the release that wrote their published 100,000-game dataset; their engine replays 2,346 of those hands exactly. Jorge Yau is their rule-based bot. The other project is [hk-mahjong-lab](https://github.com/bpy13/hk-mahjong-lab).

### HKMA team matches

The following games were played on 16 November 2026.

| Outside bot | Fu-2.3M-HKMA-1 team lead, points a game | 95% CI | Games |
|---|---|---|---|
| Lucky Cat lc32 | +6.78 | [+6.16, +7.39] | 9,216 |
| Lucky Cat lc34 | +5.73 | [+4.82, +6.65] | 4,608 |
| Neural Cat NC9 | +6.44 | [+5.03, +7.85] | 2,304 |
| Neural Cat NC10 | +5.68 | [+4.65, +6.71] | 4,608 |
| Jorge Yau | +8.00 | [+7.08, +8.93] | 4,608 |
| hk-mahjong-lab value | +3.48 | [+2.62, +4.33] | 4,608 |

The following hk-mahjong-lab PIMC runs were played on 19 November 2026 and replace the smaller 16 November runs. The number in each solver's name is its samples per decision.

| Outside bot | Fu-2.3M-HKMA-1 team lead, points a game | 95% CI | Games |
|---|---|---|---|
| PIMC-64 | +2.36 | [+1.77, +2.96] | 9,216 |
| PIMC-128 | +2.49 | [+1.89, +3.09] | 9,216 |
| PIMC-256 | +1.45 | [+0.85, +2.04] | 9,216 |

### Team matches on other rules

| Outside bot | Table | Date (2026) | Fu-2.3M-HKMA-1 team lead, points a game | 95% CI | Games |
|---|---|---|---|---|---|
| hk-mahjong-lab PIMC-128 | 3-faan with flowers | 19 November | +1.86 | [+0.57, +3.16] | 4,608 |
| hk-mahjong-lab PIMC-128 | House | 19 November | +6.06 | [+2.06, +10.05] | 4,608 |
| Lucky Cat lc32 | 3-faan with flowers | 16 November | +9.28 | [+8.12, +10.44] | 4,608 |
| Lucky Cat lc34 | 3-faan with flowers | 16 November | +7.10 | [+5.83, +8.37] | 4,608 |

### Four bots at one table

These HKMA sets used one seat per bot, with every deal played from all 24 seatings and 2,304 games per set. These rows report points a hand per seat, rather than a team's lead.

| Set | Bot | Points a hand per seat | 95% CI |
|---|---|---|---|
| 1 | Fu-2.3M-HKMA-1 | +5.4 | [+4.3, +6.5] |
| 1 | Neural Cat NC9 | −1.6 | [−2.7, −0.5] |
| 1 | Jorge Yau | −1.7 | [−2.9, −0.6] |
| 1 | Lucky Cat lc32 | −2.1 | [−3.1, −1.0] |
| 2 | Fu-2.3M-HKMA-1 | +5.1 | [+3.9, +6.4] |
| 2 | Neural Cat NC10 | −0.7 | [−1.8, +0.5] |
| 2 | Lucky Cat lc34 | −1.7 | [−2.8, −0.6] |
| 2 | Jorge Yau (newer release) | −2.8 | [−3.7, −1.8] |

### Caveats

These results measure the outside bots on our tables. Lucky Cat's bots were built for a 3 faan minimum, flower faan, Seven Pairs and a full-spicy payout. The hk-mahjong-lab project plays a 10 faan cap and models only a single East hand. Fu-2.3M-HKMA-1 trained on the HKMA rules used here, which gives it a home edge. On Lucky Cat's own table, its published dataset ranks Neural Cat first and Lucky Cat lc34 last.

The hk-mahjong-lab bots win more hands than Fu-2.3M-HKMA-1 (about 49 to 51% against 42 to 43%), but their wins are smaller, so they lose on points. Lucky Cat wins 35 to 38% of hands and Neural Cat about 25%.
