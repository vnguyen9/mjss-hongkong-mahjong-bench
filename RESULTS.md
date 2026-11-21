# Results: 20 to 21 November 2026

The run finished at 05:34 EST on 21 November 2026. It used bench version 1.1.0 (`hmac-sha256-v2`), Python 3.9.6 and 10 workers on one Apple-silicon Mac. There are 42 duplicate runs and nine head-to-head runs across three tables, on public and private decks.

`Fu-2.3M-HKMA-1` finished first on points a hand on every table and deck. It is hosted by the maintainers; its results carry only a supplied hash and hide its start command. It was trained on HKMA Classical rules. House and Chicken hand use rules it was not trained for.

## Duplicate results

Each deal is played four times on the same wall, once from each seat. Points a hand are measured against the frozen reference field. The 95% intervals use deals as the independent unit. Points cannot be compared across tables because their payouts differ. Draw rate is the fraction of games that ended without a winner. Limit hands counts hands that reached the table's cap.

The source links identify each run. `native` is the recorded isolation for the in-process reference bots; program bots used `sandbox`.

### `hk-hkma-v1`

The following rows use the public deck.

| Bot | Points a hand [95% interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +17.45 [+16.77, +18.13] | 46.6% | 3.4% | 33.1% | 85 | 2,000 | unverified | sandbox | [20261121T004505](results/hk-hkma-v1__Fu-2.3M-HKMA-1__public__20261121T004505.json) |
| `python_example` | +2.87 [+2.43, +3.30] | 10.9% | 4.6% | 64.4% | 101 | 2,000 | unverified | sandbox | [20261121T001201](results/hk-hkma-v1__python_example__public__20261121T001201.json) |
| `faan_aware` | +1.56 [+1.33, +1.79] | 16.7% | 4.4% | 58.6% | 3 | 2,000 | unverified | native | [20261121T000455](results/hk-hkma-v1__faan_aware__public__20261121T000455.json) |
| `ukeire` | -0.93 [-1.10, -0.77] | 4.3% | 4.7% | 68.5% | 4 | 2,000 | unverified | native | [20261121T000312](results/hk-hkma-v1__ukeire__public__20261121T000312.json) |
| `deficiency` | -0.98 [-1.15, -0.82] | 4.0% | 4.7% | 68.9% | 4 | 2,000 | unverified | native | [20261121T000132](results/hk-hkma-v1__deficiency__public__20261121T000132.json) |
| `shallow_search` | -1.01 [-1.32, -0.71] | 3.5% | 4.5% | 71.4% | 0 | 400 | unverified | native | [20261121T001918](results/hk-hkma-v1__shallow_search__public__20261121T001918.json) |
| `random` | -1.89 [-2.05, -1.73] | 0.0% | 4.8% | 71.9% | 0 | 2,000 | unverified | native | [20261121T000004](results/hk-hkma-v1__random__public__20261121T000004.json) |

The following rows use the private deck.

| Bot | Points a hand [95% interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
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

| Bot | Points a hand [95% interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +16.83 [+15.95, +17.71] | 37.0% | 4.6% | 22.9% | 4 | 2,000 | unverified | sandbox | [20261121T041028](results/hk-house-v1__Fu-2.3M-HKMA-1__public__20261121T041028.json) |
| `python_example` | +2.35 [+1.83, +2.87] | 13.7% | 6.6% | 39.9% | 2 | 2,000 | unverified | sandbox | [20261121T034023](results/hk-house-v1__python_example__public__20261121T034023.json) |
| `faan_aware` | +1.65 [+1.38, +1.93] | 22.8% | 5.7% | 32.8% | 1 | 2,000 | unverified | native | [20261121T033407](results/hk-house-v1__faan_aware__public__20261121T033407.json) |
| `ukeire` | -0.76 [-0.95, -0.57] | 12.3% | 5.9% | 40.2% | 0 | 2,000 | unverified | native | [20261121T033235](results/hk-house-v1__ukeire__public__20261121T033235.json) |
| `shallow_search` | -0.79 [-1.21, -0.36] | 13.7% | 6.2% | 37.2% | 0 | 400 | unverified | native | [20261121T034656](results/hk-house-v1__shallow_search__public__20261121T034656.json) |
| `deficiency` | -0.85 [-1.04, -0.65] | 11.2% | 6.1% | 40.8% | 0 | 2,000 | unverified | native | [20261121T033114](results/hk-house-v1__deficiency__public__20261121T033114.json) |
| `random` | -2.95 [-3.11, -2.79] | 0.1% | 7.3% | 46.6% | 0 | 2,000 | unverified | native | [20261121T033004](results/hk-house-v1__random__public__20261121T033004.json) |

The following rows use the private deck.

| Bot | Points a hand [95% interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +17.67 [+16.76, +18.58] | 37.4% | 4.9% | 22.8% | 8 | 2,000 | verified | sandbox | [20261121T045103](results/hk-house-v1__Fu-2.3M-HKMA-1__private__20261121T045103.json) |
| `python_example` | +2.79 [+2.25, +3.33] | 13.8% | 5.6% | 39.5% | 3 | 2,000 | verified | sandbox | [20261121T042116](results/hk-house-v1__python_example__private__20261121T042116.json) |
| `faan_aware` | +1.57 [+1.30, +1.83] | 21.8% | 5.4% | 33.8% | 0 | 2,000 | verified | native | [20261121T041517](results/hk-house-v1__faan_aware__private__20261121T041517.json) |
| `shallow_search` | -0.35 [-0.73, +0.03] | 15.0% | 4.9% | 39.1% | 0 | 400 | verified | native | [20261121T042717](results/hk-house-v1__shallow_search__private__20261121T042717.json) |
| `ukeire` | -0.85 [-1.04, -0.66] | 12.1% | 5.7% | 40.2% | 0 | 2,000 | verified | native | [20261121T041402](results/hk-house-v1__ukeire__private__20261121T041402.json) |
| `deficiency` | -0.93 [-1.14, -0.71] | 11.9% | 5.7% | 40.1% | 0 | 2,000 | verified | native | [20261121T041244](results/hk-house-v1__deficiency__private__20261121T041244.json) |
| `random` | -2.82 [-2.95, -2.69] | 0.1% | 7.0% | 47.4% | 0 | 2,000 | verified | native | [20261121T041134](results/hk-house-v1__random__private__20261121T041134.json) |

### `hk-chicken-v1`

The following rows use the public deck.

| Bot | Points a hand [95% interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +0.67 [+0.58, +0.76] | 48.5% | 13.0% | 0.5% | 0 | 2,000 | unverified | sandbox | [20261121T074943](results/hk-chicken-v1__Fu-2.3M-HKMA-1__public__20261121T074943.json) |
| `faan_aware` | +0.37 [+0.22, +0.52] | 27.2% | 17.8% | 2.2% | 6 | 2,000 | unverified | native | [20261121T071254](results/hk-chicken-v1__faan_aware__public__20261121T071254.json) |
| `python_example` | +0.22 [-0.00, +0.44] | 8.9% | 23.2% | 4.9% | 27 | 2,000 | unverified | sandbox | [20261121T071919](results/hk-chicken-v1__python_example__public__20261121T071919.json) |
| `shallow_search` | +0.14 [+0.00, +0.28] | 33.4% | 16.6% | 1.3% | 0 | 400 | unverified | native | [20261121T072546](results/hk-chicken-v1__shallow_search__public__20261121T072546.json) |
| `ukeire` | -0.22 [-0.31, -0.14] | 23.5% | 18.5% | 2.9% | 1 | 2,000 | unverified | native | [20261121T071144](results/hk-chicken-v1__ukeire__public__20261121T071144.json) |
| `deficiency` | -0.28 [-0.37, -0.19] | 22.2% | 19.0% | 2.9% | 1 | 2,000 | unverified | native | [20261121T071033](results/hk-chicken-v1__deficiency__public__20261121T071033.json) |
| `random` | -1.19 [-1.28, -1.10] | 0.2% | 24.5% | 5.8% | 0 | 2,000 | unverified | native | [20261121T070932](results/hk-chicken-v1__random__public__20261121T070932.json) |

The following rows use the private deck.

| Bot | Points a hand [95% interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +0.64 [+0.55, +0.73] | 47.8% | 13.5% | 0.5% | 0 | 2,000 | verified | sandbox | [20261121T083021](results/hk-chicken-v1__Fu-2.3M-HKMA-1__private__20261121T083021.json) |
| `faan_aware` | +0.41 [+0.30, +0.52] | 27.4% | 18.0% | 2.0% | 0 | 2,000 | verified | native | [20261121T075356](results/hk-chicken-v1__faan_aware__private__20261121T075356.json) |
| `shallow_search` | +0.13 [+0.00, +0.26] | 32.5% | 15.1% | 1.1% | 0 | 400 | verified | native | [20261121T080634](results/hk-chicken-v1__shallow_search__private__20261121T080634.json) |
| `python_example` | -0.14 [-0.34, +0.05] | 8.8% | 23.1% | 4.9% | 18 | 2,000 | verified | sandbox | [20261121T080017](results/hk-chicken-v1__python_example__private__20261121T080017.json) |
| `ukeire` | -0.17 [-0.25, -0.09] | 24.0% | 19.0% | 2.8% | 0 | 2,000 | verified | native | [20261121T075248](results/hk-chicken-v1__ukeire__private__20261121T075248.json) |
| `deficiency` | -0.18 [-0.26, -0.10] | 22.1% | 18.2% | 3.1% | 0 | 2,000 | verified | native | [20261121T075142](results/hk-chicken-v1__deficiency__private__20261121T075142.json) |
| `random` | -1.19 [-1.27, -1.12] | 0.4% | 25.7% | 5.6% | 0 | 2,000 | verified | native | [20261121T075043](results/hk-chicken-v1__random__private__20261121T075043.json) |

## Head-to-head results

Each pair plays 300 deals in all six seat pairs. Ratings use Bradley-Terry on the Elo scale, with 95% bootstrap intervals from whole deals. Rank is 1 plus the number of bots whose interval lies entirely above that bot's interval. Overlapping intervals share a rank. The public five-bot runs and public six-bot runs are separate runs; ratings belong to the field in that run.

### `hk-hkma-v1`, public, 5 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-hkma-v1__h2h__public__20261121T013727.json).

| Bot | Rating [95% interval] | Rank |
|---|---|---|
| `faan_aware` | +58.6 [+55.0, +62.7] | 1 |
| `python_example` | +14.3 [+11.4, +17.2] | 2 |
| `ukeire` | -12.1 [-15.2, -9.4] | 3 |
| `deficiency` | -14.6 [-17.1, -12.1] | 3 |
| `random` | -46.1 [-48.6, -43.4] | 5 |

### `hk-hkma-v1`, public, 6 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-hkma-v1__h2h__public__20261121T023322.json).

| Bot | Rating [95% interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +156.3 [+151.3, +161.5] | 1 |
| `faan_aware` | +24.6 [+21.1, +28.6] | 2 |
| `python_example` | -14.2 [-17.3, -11.0] | 3 |
| `ukeire` | -42.3 [-45.4, -39.3] | 4 |
| `deficiency` | -45.8 [-48.7, -42.9] | 4 |
| `random` | -78.6 [-81.6, -75.8] | 6 |

### `hk-hkma-v1`, private, 6 bots

This run is verified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-hkma-v1__h2h__private__20261121T032901.json).

| Bot | Rating [95% interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +151.6 [+147.0, +156.4] | 1 |
| `faan_aware` | +25.2 [+21.5, +29.1] | 2 |
| `python_example` | -9.8 [-13.1, -6.6] | 3 |
| `ukeire` | -43.6 [-46.4, -40.5] | 4 |
| `deficiency` | -47.7 [-50.1, -45.1] | 4 |
| `random` | -75.7 [-78.3, -73.0] | 6 |

### `hk-house-v1`, public, 5 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-house-v1__h2h__public__20261121T050310.json).

| Bot | Rating [95% interval] | Rank |
|---|---|---|
| `faan_aware` | +74.1 [+69.3, +79.2] | 1 |
| `python_example` | +11.0 [+7.0, +15.0] | 2 |
| `ukeire` | +9.9 [+5.8, +14.0] | 2 |
| `deficiency` | +0.3 [-3.2, +3.9] | 4 |
| `random` | -95.2 [-98.7, -91.5] | 5 |

### `hk-house-v1`, public, 6 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-house-v1__h2h__public__20261121T060610.json).

| Bot | Rating [95% interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +111.4 [+106.0, +116.8] | 1 |
| `faan_aware` | +52.2 [+47.5, +57.0] | 2 |
| `python_example` | -8.8 [-12.7, -4.5] | 3 |
| `ukeire` | -12.1 [-16.6, -8.3] | 3 |
| `deficiency` | -22.2 [-25.8, -18.0] | 5 |
| `random` | -120.5 [-124.3, -117.2] | 6 |

### `hk-house-v1`, private, 6 bots

This run is verified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-house-v1__h2h__private__20261121T070833.json).

| Bot | Rating [95% interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +106.7 [+101.1, +112.1] | 1 |
| `faan_aware` | +50.7 [+45.9, +55.5] | 2 |
| `ukeire` | -9.3 [-13.4, -5.3] | 3 |
| `python_example` | -12.0 [-16.1, -8.2] | 3 |
| `deficiency` | -21.4 [-24.8, -18.1] | 5 |
| `random` | -114.6 [-118.2, -111.0] | 6 |

### `hk-chicken-v1`, public, 5 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-chicken-v1__h2h__public__20261121T084217.json).

| Bot | Rating [95% interval] | Rank |
|---|---|---|
| `faan_aware` | +93.1 [+88.4, +98.2] | 1 |
| `ukeire` | +75.0 [+70.4, +80.0] | 2 |
| `deficiency` | +62.2 [+57.3, +66.9] | 3 |
| `python_example` | -51.9 [-57.3, -46.6] | 4 |
| `random` | -178.4 [-183.4, -173.2] | 5 |

### `hk-chicken-v1`, public, 6 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-chicken-v1__h2h__public__20261121T093909.json).

| Bot | Rating [95% interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +156.4 [+150.3, +162.0] | 1 |
| `faan_aware` | +60.0 [+54.6, +65.5] | 2 |
| `ukeire` | +41.8 [+37.1, +45.7] | 3 |
| `deficiency` | +29.3 [+25.0, +33.7] | 4 |
| `python_example` | -80.7 [-85.6, -75.7] | 5 |
| `random` | -206.8 [-211.3, -201.9] | 6 |

### `hk-chicken-v1`, private, 6 bots

This run is verified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-chicken-v1__h2h__private__20261121T103422.json).

| Bot | Rating [95% interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +164.6 [+158.0, +170.8] | 1 |
| `faan_aware` | +60.1 [+54.6, +65.4] | 2 |
| `ukeire` | +36.1 [+31.2, +41.1] | 3 |
| `deficiency` | +25.6 [+21.0, +30.1] | 4 |
| `python_example` | -78.4 [-83.6, -73.2] | 5 |
| `random` | -208.0 [-212.6, -203.5] | 6 |

## Fairness checks

A new private deck contained 10,000 independent random 64-bit seeds, made with `scripts/make_private_deck.py`. It was kept outside the repository and is not published. The reference field matched its pinned hashes, and the engine reproduced each table's fingerprint before scoring. The bench refuses to score if either check fails.

For private runs, each decision's `rng_seed` and each game's `game_id` came from HMAC-SHA256 under a per-run secret key that no bot sees. A bot cannot work back from these identifiers to the deal. Public runs use a fixed public key so they can be reproduced.

Every program bot (`python_example` and `Fu-2.3M-HKMA-1`) started fresh for every game and ran under `scripts/sandbox/macos.sh`. It had no network or child processes, could write only to its own empty folder, and could not read the deck file. Reference bots ran inside the bench.

All 51 runs passed the fair-play check with 0 decision changes and 0 view mismatches, and none exceeded the fault limit. Every private run is tagged verified. All 283,800 public games in 27 public logs replayed with `hkbench verify-log` with 0 mismatches.

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
| `hk-chicken-v1` | private | random | [20261121T075043](results/hk-chicken-v1__random__private__20261121T075043.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | private | deficiency | [20261121T075142](results/hk-chicken-v1__deficiency__private__20261121T075142.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | private | ukeire | [20261121T075248](results/hk-chicken-v1__ukeire__private__20261121T075248.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | private | faan_aware | [20261121T075356](results/hk-chicken-v1__faan_aware__private__20261121T075356.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | private | python_example | [20261121T080017](results/hk-chicken-v1__python_example__private__20261121T080017.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | private | shallow_search | [20261121T080634](results/hk-chicken-v1__shallow_search__private__20261121T080634.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | private | Fu-2.3M-HKMA-1 | [20261121T083021](results/hk-chicken-v1__Fu-2.3M-HKMA-1__private__20261121T083021.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | private | 6-bot head-to-head | [20261121T103422](results/hk-chicken-v1__h2h__private__20261121T103422.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |
| `hk-chicken-v1` | public | random | [20261121T070932](results/hk-chicken-v1__random__public__20261121T070932.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | public | deficiency | [20261121T071033](results/hk-chicken-v1__deficiency__public__20261121T071033.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | public | ukeire | [20261121T071144](results/hk-chicken-v1__ukeire__public__20261121T071144.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | public | faan_aware | [20261121T071254](results/hk-chicken-v1__faan_aware__public__20261121T071254.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | public | python_example | [20261121T071919](results/hk-chicken-v1__python_example__public__20261121T071919.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | public | shallow_search | [20261121T072546](results/hk-chicken-v1__shallow_search__public__20261121T072546.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | public | Fu-2.3M-HKMA-1 | [20261121T074943](results/hk-chicken-v1__Fu-2.3M-HKMA-1__public__20261121T074943.json) | passed | 300 | 0 | 0 | 0 | 0 |
| `hk-chicken-v1` | public | 5-bot head-to-head | [20261121T084217](results/hk-chicken-v1__h2h__public__20261121T084217.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |
| `hk-chicken-v1` | public | 6-bot head-to-head | [20261121T093909](results/hk-chicken-v1__h2h__public__20261121T093909.json) | passed (all bots) | not recorded | not recorded | not recorded | not recorded | 0 |

A verified tag means the run used private deals, passed the hidden-tile fair-play check and stayed within the fault limit. Program bots also need a sandbox. The check changes hidden tiles while keeping the bot's view unchanged and asks for the decision again. It mainly checks the harness; it can also catch a bot that accesses hidden state through another channel or ignores the supplied random seed.

The tag does not audit a bot's code or prove that it had the same thinking time, tools or help as a human. The hosted bot's implementation is private, and its supplied hash is not an independent audit. The field consists of three scripted bots with crude claim play and no defence. These scores measure play against that field, not strength against careful humans or adapting opponents. The bench measures single hands, with the rulebook gaps described in [RULES.md](RULES.md). See the [benchmark card's limits](BENCHMARK_CARD.md#known-limits).

## Check a public result

This command reproduces the public `faan_aware` row on `hk-hkma-v1`:

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
