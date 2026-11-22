# Results: 20 to 22 November 2026

The 1.1.0 re-score finished at 05:34 EST on 21 November 2026, on bench version 1.1.0 (`hmac-sha256-v2`), Python 3.9.6 and 10 workers on one Apple-silicon Mac. It has 42 duplicate runs and nine head-to-heads across the three tables, on both decks. Eight outside bots were added on 21 and 22 November ([below](#outside-bots-on-the-bench)).

Among the original bots, `Fu-2.3M-HKMA-1` came first on points a hand on every table and deck. With the outside bots added, it still leads on HKMA and House, but every outside bot beats it on Chicken hand. We host it ourselves, so its results carry only a supplied hash, not its start command. It was trained on HKMA Classical rules; House and Chicken hand are rules it never trained on.

## Duplicate results

Each deal is played four times on the same wall, once from each seat. Points a hand are measured against the frozen reference field. The 95% intervals use deals as the independent unit. Points cannot be compared across tables because their payouts differ. Draw rate is the fraction of games that ended without a winner. Limit hands counts hands that reached the table's cap.

The source links identify each run. `native` is the recorded isolation for the in-process reference bots; program bots used `sandbox`.

### `hk-hkma-v1`

The following rows use the public deck.

| Bot | Points a hand [interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +17.45 [+16.77, +18.13] | 46.6% | 3.4% | 33.1% | 85 | 2,000 | unverified | sandbox | [20261121T004505](results/hk-hkma-v1__Fu-2.3M-HKMA-1__public__20261121T004505.json) |
| `python_example` | +2.87 [+2.43, +3.30] | 10.9% | 4.6% | 64.4% | 101 | 2,000 | unverified | sandbox | [20261121T001201](results/hk-hkma-v1__python_example__public__20261121T001201.json) |
| `faan_aware` | +1.56 [+1.33, +1.79] | 16.7% | 4.4% | 58.6% | 3 | 2,000 | unverified | native | [20261121T000455](results/hk-hkma-v1__faan_aware__public__20261121T000455.json) |
| `ukeire` | -0.93 [-1.10, -0.77] | 4.3% | 4.7% | 68.5% | 4 | 2,000 | unverified | native | [20261121T000312](results/hk-hkma-v1__ukeire__public__20261121T000312.json) |
| `deficiency` | -0.98 [-1.15, -0.82] | 4.0% | 4.7% | 68.9% | 4 | 2,000 | unverified | native | [20261121T000132](results/hk-hkma-v1__deficiency__public__20261121T000132.json) |
| `shallow_search` | -1.01 [-1.32, -0.71] | 3.5% | 4.5% | 71.4% | 0 | 400 | unverified | native | [20261121T001918](results/hk-hkma-v1__shallow_search__public__20261121T001918.json) |
| `random` | -1.89 [-2.05, -1.73] | 0.0% | 4.8% | 71.9% | 0 | 2,000 | unverified | native | [20261121T000004](results/hk-hkma-v1__random__public__20261121T000004.json) |

The following rows use the private deck.

| Bot | Points a hand [interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
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

| Bot | Points a hand [interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +16.83 [+15.95, +17.71] | 37.0% | 4.6% | 22.9% | 4 | 2,000 | unverified | sandbox | [20261121T041028](results/hk-house-v1__Fu-2.3M-HKMA-1__public__20261121T041028.json) |
| `python_example` | +2.35 [+1.83, +2.87] | 13.7% | 6.6% | 39.9% | 2 | 2,000 | unverified | sandbox | [20261121T034023](results/hk-house-v1__python_example__public__20261121T034023.json) |
| `faan_aware` | +1.65 [+1.38, +1.93] | 22.8% | 5.7% | 32.8% | 1 | 2,000 | unverified | native | [20261121T033407](results/hk-house-v1__faan_aware__public__20261121T033407.json) |
| `ukeire` | -0.76 [-0.95, -0.57] | 12.3% | 5.9% | 40.2% | 0 | 2,000 | unverified | native | [20261121T033235](results/hk-house-v1__ukeire__public__20261121T033235.json) |
| `shallow_search` | -0.79 [-1.21, -0.36] | 13.7% | 6.2% | 37.2% | 0 | 400 | unverified | native | [20261121T034656](results/hk-house-v1__shallow_search__public__20261121T034656.json) |
| `deficiency` | -0.85 [-1.04, -0.65] | 11.2% | 6.1% | 40.8% | 0 | 2,000 | unverified | native | [20261121T033114](results/hk-house-v1__deficiency__public__20261121T033114.json) |
| `random` | -2.95 [-3.11, -2.79] | 0.1% | 7.3% | 46.6% | 0 | 2,000 | unverified | native | [20261121T033004](results/hk-house-v1__random__public__20261121T033004.json) |

The following rows use the private deck.

| Bot | Points a hand [interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
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

| Bot | Points a hand [interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| `Fu-2.3M-HKMA-1` | +0.67 [+0.58, +0.76] | 48.5% | 13.0% | 0.5% | 0 | 2,000 | unverified | sandbox | [20261121T074943](results/hk-chicken-v1__Fu-2.3M-HKMA-1__public__20261121T074943.json) |
| `faan_aware` | +0.37 [+0.22, +0.52] | 27.2% | 17.8% | 2.2% | 6 | 2,000 | unverified | native | [20261121T071254](results/hk-chicken-v1__faan_aware__public__20261121T071254.json) |
| `python_example` | +0.22 [-0.00, +0.44] | 8.9% | 23.2% | 4.9% | 27 | 2,000 | unverified | sandbox | [20261121T071919](results/hk-chicken-v1__python_example__public__20261121T071919.json) |
| `shallow_search` | +0.14 [+0.00, +0.28] | 33.4% | 16.6% | 1.3% | 0 | 400 | unverified | native | [20261121T072546](results/hk-chicken-v1__shallow_search__public__20261121T072546.json) |
| `ukeire` | -0.22 [-0.31, -0.14] | 23.5% | 18.5% | 2.9% | 1 | 2,000 | unverified | native | [20261121T071144](results/hk-chicken-v1__ukeire__public__20261121T071144.json) |
| `deficiency` | -0.28 [-0.37, -0.19] | 22.2% | 19.0% | 2.9% | 1 | 2,000 | unverified | native | [20261121T071033](results/hk-chicken-v1__deficiency__public__20261121T071033.json) |
| `random` | -1.19 [-1.28, -1.10] | 0.2% | 24.5% | 5.8% | 0 | 2,000 | unverified | native | [20261121T070932](results/hk-chicken-v1__random__public__20261121T070932.json) |

The following rows use the private deck.

| Bot | Points a hand [interval] | Win | Deal-in | Draw | Limit hands | Deals | Verification | Isolation | Source |
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

| Bot | Rating [interval] | Rank |
|---|---|---|
| `faan_aware` | +58.6 [+55.0, +62.7] | 1 |
| `python_example` | +14.3 [+11.4, +17.2] | 2 |
| `ukeire` | -12.1 [-15.2, -9.4] | 3 |
| `deficiency` | -14.6 [-17.1, -12.1] | 3 |
| `random` | -46.1 [-48.6, -43.4] | 5 |

### `hk-hkma-v1`, public, 6 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-hkma-v1__h2h__public__20261121T023322.json).

| Bot | Rating [interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +156.3 [+151.3, +161.5] | 1 |
| `faan_aware` | +24.6 [+21.1, +28.6] | 2 |
| `python_example` | -14.2 [-17.3, -11.0] | 3 |
| `ukeire` | -42.3 [-45.4, -39.3] | 4 |
| `deficiency` | -45.8 [-48.7, -42.9] | 4 |
| `random` | -78.6 [-81.6, -75.8] | 6 |

### `hk-hkma-v1`, private, 6 bots

This run is verified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-hkma-v1__h2h__private__20261121T032901.json).

| Bot | Rating [interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +151.6 [+147.0, +156.4] | 1 |
| `faan_aware` | +25.2 [+21.5, +29.1] | 2 |
| `python_example` | -9.8 [-13.1, -6.6] | 3 |
| `ukeire` | -43.6 [-46.4, -40.5] | 4 |
| `deficiency` | -47.7 [-50.1, -45.1] | 4 |
| `random` | -75.7 [-78.3, -73.0] | 6 |

### `hk-house-v1`, public, 5 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-house-v1__h2h__public__20261121T050310.json).

| Bot | Rating [interval] | Rank |
|---|---|---|
| `faan_aware` | +74.1 [+69.3, +79.2] | 1 |
| `python_example` | +11.0 [+7.0, +15.0] | 2 |
| `ukeire` | +9.9 [+5.8, +14.0] | 2 |
| `deficiency` | +0.3 [-3.2, +3.9] | 4 |
| `random` | -95.2 [-98.7, -91.5] | 5 |

### `hk-house-v1`, public, 6 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-house-v1__h2h__public__20261121T060610.json).

| Bot | Rating [interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +111.4 [+106.0, +116.8] | 1 |
| `faan_aware` | +52.2 [+47.5, +57.0] | 2 |
| `python_example` | -8.8 [-12.7, -4.5] | 3 |
| `ukeire` | -12.1 [-16.6, -8.3] | 3 |
| `deficiency` | -22.2 [-25.8, -18.0] | 5 |
| `random` | -120.5 [-124.3, -117.2] | 6 |

### `hk-house-v1`, private, 6 bots

This run is verified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-house-v1__h2h__private__20261121T070833.json).

| Bot | Rating [interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +106.7 [+101.1, +112.1] | 1 |
| `faan_aware` | +50.7 [+45.9, +55.5] | 2 |
| `ukeire` | -9.3 [-13.4, -5.3] | 3 |
| `python_example` | -12.0 [-16.1, -8.2] | 3 |
| `deficiency` | -21.4 [-24.8, -18.1] | 5 |
| `random` | -114.6 [-118.2, -111.0] | 6 |

### `hk-chicken-v1`, public, 5 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-chicken-v1__h2h__public__20261121T084217.json).

| Bot | Rating [interval] | Rank |
|---|---|---|
| `faan_aware` | +93.1 [+88.4, +98.2] | 1 |
| `ukeire` | +75.0 [+70.4, +80.0] | 2 |
| `deficiency` | +62.2 [+57.3, +66.9] | 3 |
| `python_example` | -51.9 [-57.3, -46.6] | 4 |
| `random` | -178.4 [-183.4, -173.2] | 5 |

### `hk-chicken-v1`, public, 6 bots

This run is unverified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-chicken-v1__h2h__public__20261121T093909.json).

| Bot | Rating [interval] | Rank |
|---|---|---|
| `Fu-2.3M-HKMA-1` | +156.4 [+150.3, +162.0] | 1 |
| `faan_aware` | +60.0 [+54.6, +65.5] | 2 |
| `ukeire` | +41.8 [+37.1, +45.7] | 3 |
| `deficiency` | +29.3 [+25.0, +33.7] | 4 |
| `python_example` | -80.7 [-85.6, -75.7] | 5 |
| `random` | -206.8 [-211.3, -201.9] | 6 |

### `hk-chicken-v1`, private, 6 bots

This run is verified with isolation `sandbox`. It used 300 deals per pair. [Source JSON](results/hk-chicken-v1__h2h__private__20261121T103422.json).

| Bot | Rating [interval] | Rank |
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

Every program bot in the original run (`python_example` and `Fu-2.3M-HKMA-1`) started fresh for every game and ran under `scripts/sandbox/macos.sh`. It had no network or child processes, could write only to its own empty folder, and could not read the deck file. Reference bots ran inside the bench.

All 51 original runs passed the fair-play check with 0 decision changes and 0 view mismatches, and none exceeded the fault limit. Every private run is tagged verified. All 283,800 public games in 27 public logs replayed with `hkbench verify-log` with 0 mismatches.

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

The tables give points a hand on the secret deck against the reference field, as everywhere else on this page. Each bot links to its result file. For comparison, `Fu-2.3M-HKMA-1` scores +17.75 on HKMA, +17.67 on House and +0.64 on Chicken hand.

### HKMA Classical, secret deck

| Bot | Points a hand | Interval | Deals | Faults/decisions |
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

| Bot | Points a hand | Interval | Deals | Faults/decisions |
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

| Bot | Points a hand | Interval | Deals | Faults/decisions |
|---|---|---|---|---|
| [`LuckyCat-lc34`](results/hk-chicken-v1__LuckyCat-lc34__private__20261122T045707.json) | +2.15 | [+1.84, +2.47] | 2,000 | 0/135,355 |
| [`NeuralCat-NC10`](results/hk-chicken-v1__NeuralCat-NC10__private__20261122T051042.json) | +1.94 | [+1.58, +2.29] | 2,000 | 0/137,024 |
| [`NeuralCat-NC9`](results/hk-chicken-v1__NeuralCat-NC9__private__20261122T050353.json) | +1.90 | [+1.55, +2.25] | 2,000 | 0/137,658 |
| [`LuckyCat-lc32`](results/hk-chicken-v1__LuckyCat-lc32__private__20261122T045040.json) | +1.88 | [+1.60, +2.16] | 2,000 | 0/136,162 |
| [`LuckyCat-JorgeYau`](results/hk-chicken-v1__LuckyCat-JorgeYau__private__20261122T051659.json) | +1.70 | [+1.41, +1.99] | 2,000 | 0/139,764 |
| [`hk-mahjong-lab-PIMC-256`](results/hk-chicken-v1__hk-mahjong-lab-PIMC-256__private__20261122T153252.json) | +1.13 | [+0.84, +1.41] | 400 | 0/22,913 |
| [`hk-mahjong-lab-PIMC-128`](results/hk-chicken-v1__hk-mahjong-lab-PIMC-128__private__20261122T091949.json) | +1.06 | [+0.86, +1.26] | 400 | 0/23,001 |
| [`hk-mahjong-lab-value`](results/hk-chicken-v1__hk-mahjong-lab-value__private__20261122T052203.json) | +0.84 | [+0.76, +0.93] | 2,000 | 0/114,844 |

### Secret-deck head-to-heads

Here the bots play each other: five reference bots, `Fu-2.3M-HKMA-1` and the six outside bots other than PIMC, which is too slow for a field this size. Bradley-Terry ratings compare them directly. `hk-mahjong-lab-value` and Fu share first place on all three tables; value's rating is a little higher, but the intervals overlap.

#### `hk-chicken-v1`

[Source JSON](results/hk-chicken-v1__h2h__private__20261122T065116.json).

| Bot | Rating | Interval | Rank |
|---|---|---|---|
| `hk-mahjong-lab-value` | +168.76 | [+161.84, +176.81] | 1 |
| `Fu-2.3M-HKMA-1` | +165.51 | [+158.76, +173.11] | 1 |
| `faan_aware` | +68.24 | [+61.49, +74.92] | 3 |
| `ukeire` | +46.50 | [+40.30, +52.51] | 4 |
| `deficiency` | +34.81 | [+28.54, +41.17] | 4 |
| `LuckyCat-JorgeYau` | -13.28 | [-19.32, -6.74] | 6 |
| `NeuralCat-NC10` | -33.68 | [-39.85, -27.48] | 7 |
| `LuckyCat-lc34` | -35.94 | [-42.56, -29.13] | 7 |
| `LuckyCat-lc32` | -49.76 | [-56.94, -42.86] | 9 |
| `NeuralCat-NC9` | -53.74 | [-59.82, -47.06] | 9 |
| `python_example` | -83.05 | [-89.66, -76.57] | 11 |
| `random` | -214.37 | [-220.63, -208.34] | 12 |

#### `hk-hkma-v1`

[Source JSON](results/hk-hkma-v1__h2h__private__20261122T004409.json).

| Bot | Rating | Interval | Rank |
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

| Bot | Rating | Interval | Rank |
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

| Outside bot | Fu-2.3M-HKMA-1 team lead, points a game | Interval | Games |
|---|---|---|---|
| Lucky Cat lc32 | +6.78 | [+6.16, +7.39] | 9,216 |
| Lucky Cat lc34 | +5.73 | [+4.82, +6.65] | 4,608 |
| Neural Cat NC9 | +6.44 | [+5.03, +7.85] | 2,304 |
| Neural Cat NC10 | +5.68 | [+4.65, +6.71] | 4,608 |
| Jorge Yau | +8.00 | [+7.08, +8.93] | 4,608 |
| hk-mahjong-lab value | +3.48 | [+2.62, +4.33] | 4,608 |

The following hk-mahjong-lab PIMC runs were played on 19 November 2026 and replace the smaller 16 November runs. The number in each solver's name is its samples per decision.

| Outside bot | Fu-2.3M-HKMA-1 team lead, points a game | Interval | Games |
|---|---|---|---|
| PIMC-64 | +2.36 | [+1.77, +2.96] | 9,216 |
| PIMC-128 | +2.49 | [+1.89, +3.09] | 9,216 |
| PIMC-256 | +1.45 | [+0.85, +2.04] | 9,216 |

### Team matches on other rules

| Outside bot | Table | Date (2026) | Fu-2.3M-HKMA-1 team lead, points a game | Interval | Games |
|---|---|---|---|---|---|
| hk-mahjong-lab PIMC-128 | 3-faan with flowers | 19 November | +1.86 | [+0.57, +3.16] | 4,608 |
| hk-mahjong-lab PIMC-128 | House | 19 November | +6.06 | [+2.06, +10.05] | 4,608 |
| Lucky Cat lc32 | 3-faan with flowers | 16 November | +9.28 | [+8.12, +10.44] | 4,608 |
| Lucky Cat lc34 | 3-faan with flowers | 16 November | +7.10 | [+5.83, +8.37] | 4,608 |

### Four bots at one table

These HKMA sets used one seat per bot, with every deal played from all 24 seatings and 2,304 games per set. These rows report points a hand per seat, rather than a team's lead.

| Set | Bot | Points a hand per seat | Interval |
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
