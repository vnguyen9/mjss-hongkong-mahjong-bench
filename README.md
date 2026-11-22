<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/assets/banner-light.svg">
  <img src="docs/assets/banner-light.svg" alt="Hong Kong Mahjong Bench" width="900">
</picture>

A fair way to compare Hong Kong Mahjong players: bots today, LLMs and humans next.

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/licence-MIT-20785b" alt="MIT licence"></a>
  <img src="https://img.shields.io/badge/Python-3.9%2B-20785b" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/version-1.1.0-20785b" alt="Version 1.1.0">
  <img src="https://img.shields.io/badge/protocol-hkbench--1-20785b" alt="Protocol hkbench-1">
</p>
<p><a href="site/index.html">Leaderboard</a> · <a href="RESULTS.md">Results</a> · <a href="BENCHMARK_CARD.md">Benchmark card</a> · <a href="RULES.md">Rules</a> · <a href="SUBMITTING.md">Submit a bot</a> · <a href="https://mahjongsensei.co">Mahjong Sensei</a></p>
</div>

## Why this exists

We make [Mahjong Sensei](https://mahjongsensei.co), a Hong Kong Mahjong app ([App Store](https://apps.apple.com/us/app/mahjong-sensei/id6792996894)), and `Fu-2.3M-HKMA-1` is the bot you play against in it. Each time we trained a new version, we needed to know whether it really played better. There was no benchmark for Hong Kong Mahjong; most public mahjong AI work is about Japanese Riichi. So we built this rules engine, scorer and harness for our own bot, and we're opening it up so anyone can measure theirs the same way. It's MIT licensed and contains nothing private. LLM and human tracks come next.

Mahjong is noisy. A strong player can lose a whole session on bad tiles, so counting wins takes an enormous number of games. Duplicate play takes most of that luck out: every wall is played four times, with the bot in each seat once. The score is points a hand against a fixed field of reference bots, with a 95% interval over deals. Rules differ from table to table, so every row names its rule set: HKMA Classical, House or Chicken hand. [RULES.md](RULES.md) has the details.

Scores only mean something if a bot can't cheat or tune itself to the test. Verified rows are played on a private deck that nobody outside sees. A bot is told only what its own seat can see, and the fair-play check re-deals the hidden tiles and asks again, so a bot that peeks gets caught. Every bot starts fresh each game, and program bots run in a sandbox. Version 1.1.0 [closed a hole](CHANGELOG.md#110-2026-11-21) that could have let a bot rebuild the private walls.

It helps with training too. The yardstick never moves, so you can compare saved versions of a bot on deals it never trained on and trust that a gain is real. Public decks and `verify-log` make every public number reproducible, and `--training-log` saves the full record of every won hand on public deals, ready to train on. Head-to-head ratings compare bots directly. The protocol is plain JSON lines, so a program in any language can play.

## Results

<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/results-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/assets/results-light.svg">
  <img src="docs/assets/results-light.svg" alt="Verified private-deck points a hand for every bot on HKMA Classical, House and Chicken hand." width="640">
</picture>
</div>

Each panel has its own scale, because rules and payouts differ between tables. The whiskers are the intervals. [Rebuild the chart](scripts/render_charts.py) with `python3 scripts/render_charts.py`.

Verified private-deck results from 20 to 22 November 2026, on version 1.1.0. For each table: `Fu-2.3M-HKMA-1` and the best of the other bots.

| Table | Bot | Points a hand [interval] | Win | Deal-in |
|---|---|---|---|---|
| `hk-hkma-v1` | `Fu-2.3M-HKMA-1` | +17.75 [+17.08, +18.42] | 47.2% | 3.4% |
| `hk-hkma-v1` | `hk-mahjong-lab-PIMC-256` | +13.69 [+12.50, +14.87] | 53.0% | 2.4% |
| `hk-house-v1` | `Fu-2.3M-HKMA-1` | +17.67 [+16.76, +18.58] | 37.4% | 4.9% |
| `hk-house-v1` | `hk-mahjong-lab-PIMC-256` | +15.09 [+13.03, +17.16] | 42.5% | 4.2% |
| `hk-chicken-v1` | `Fu-2.3M-HKMA-1` | +0.64 [+0.55, +0.73] | 47.8% | 13.5% |
| `hk-chicken-v1` | `LuckyCat-lc34` | +2.15 [+1.84, +2.47] | 11.4% | 22.1% |

`Fu-2.3M-HKMA-1` leads on HKMA Classical and House. On Chicken hand every outside bot beats it. Fu was trained on HKMA rules, and House and Chicken hand are rules it never trained on.

### Outside bots

Eight bots from two other projects are on the leaderboard and the chart. Five come from [Lucky Cat Mahjong](https://huggingface.co/codenameyau/lucky-cat-mahjong): `LuckyCat-lc32`, `LuckyCat-lc34`, `NeuralCat-NC9`, `NeuralCat-NC10` and the rule-based `LuckyCat-JorgeYau`. Three come from [hk-mahjong-lab](https://github.com/bpy13/hk-mahjong-lab): the rule-based `hk-mahjong-lab-value`, and its search player at 128 and 256 samples a decision. We ran them ourselves from their authors' public code. The authors didn't submit them, and they're welcome to replace them with their own entries. [RESULTS.md](RESULTS.md#outside-bots-on-the-bench) has the method, every number and the few places where our adapters had to approximate.

## Why the run is fair

The private deck was new and stayed secret. Program bots ran in a sandbox with no network and no way to read the deck. Lucky Cat's bots start a JavaScript process from Python, so their sandbox allows that one child process. Every run passed the fair-play check, no bot went over the fault limit, and every private run is verified. Every public game replays exactly: 283,800 from the 1.1.0 re-score and 153,600 from the outside bots. Before scoring, the bench checked the reference bots' pinned hashes and the engine's fingerprint.

[RESULTS.md](RESULTS.md) has every bot on both decks, the head-to-head ratings, what the verified tag does and doesn't prove, and the commands to check the public runs yourself.

## Three rule sets

| Table | Rules | State |
|---|---|---|
| `hk-hkma-v1` | HKMA Classical: 3 faan to win, cap 10, discarder pays the whole hand, flowers do not score | scoring |
| `hk-house-v1` | House: flowers score, limit hands graded, cap 13, Seven Pairs is a hand | scoring |
| `hk-chicken-v1` | Chicken hand: HKMA Classical with a 0-faan minimum, so a hand with no scoring pattern wins; faan still score and pay | scoring |

HKMA Classical is the headline because it has a citable rulebook. `RULES.md` lists every faan value, the payout, and the places where `hk-hkma-v1` is not the rulebook.

## Quick start

You need Python 3.9 or newer. There are no packages to install.

```
git clone https://github.com/vnguyen9/mjss-hongkong-mahjong-bench.git
cd mjss-hongkong-mahjong-bench
python -m unittest discover -s tests          # or: python -m pytest tests
```

Reproduce a row of the leaderboard with one command (about a minute for the fast bots):

```
python -m hkbench score --table hk-hkma-v1 --bot ref:ukeire --deals 200 --workers 2
```

It prints points a hand with its interval, win rate, deal-in rate, average win and limit hands. It also writes one result file and a compressed log of every game to `results/`. The run is tagged **unverified**, because it used the public deals.

Each log line is one game: the deal, the arrangement, who won and how, the faan and its `patterns` (`[name, faan]` pairs), the payments, and on public deals the seed and the full action list, so `verify-log` can replay it. To train on the games, add `--training-log` (to `score` or `h2h`; off by default, and with it off the logs are unchanged). Each won game's line then also carries the winner's `melds` (`[kind, tiles, seat the claimed tile came from]`), `concealed` tiles with the winning tile in them, `winning_tile` (null for a flower win), `flowers`, and `winner_draws`, the winner's own draw count from the engine's events. Tiles use the engine's names (`m1`..`m9`, `s1`.., `p1`.., `E S W N`, `C F P`). Seed plus actions rebuild any state, so nothing else is stored. The setting is for public deals: on a private deck the flag is ignored and the log stays outcome-only. The `game_over` message a bot receives (`protocol/PROTOCOL.md`) does not change.

## Submit a bot

Read [the submission guide](SUBMITTING.md) for the protocol, fair-play checks and the files to include.

You can score your own bot with any program that reads one JSON object per line on stdin and writes one per line on stdout (`protocol/PROTOCOL.md`):

```
python -m hkbench score --table hk-hkma-v1 \
    --bot "python examples/bots/python_bot.py" --name my_bot --trained-on "none" --deals 200 --workers 2
python -m hkbench score --table hk-hkma-v1 --bot "node examples/bots/javascript_bot.js" --deals 50
```

Other commands:

```
python -m hkbench h2h --table hk-hkma-v1 --bot a=ref:ukeire --bot b="python examples/bots/python_bot.py" --deals 100
python -m hkbench fairplay --table hk-hkma-v1 --bot "python examples/bots/python_bot.py"
python -m hkbench fingerprint --table hk-hkma-v1          # does this engine reproduce the table's fingerprint?
python -m hkbench verify-log results/logs/<file>.jsonl.gz # replay every game in a log
python -m hkbench site                                    # rebuild site/leaderboard.json and site/index.html
python -m hkbench tables                                  # list tables, check the reference field pins
```

(`python -m hkbench` works everywhere; `hkbench` is installed by `pip install -e .`.)

## How a row is scored

1. The reference bots must match their pinned hashes, and the engine must reproduce the table's fingerprint: 300 fixed deals and 42 fixed hands, hashed. If either fails, nothing is scored.
2. The bench plays the bot in real games on secret deals, re-shuffles every hidden tile (the other hands and the wall) at chosen decision points into a new arrangement that looks the same from the bot's seat, and asks again. A changed answer rejects the bot.
3. The bot takes one seat and the three field bots fill the others. Every deal is played from all four seats.
4. The bench computes one average per deal, then the mean and its interval over deals. The four games of a deal are not independent, so the deal is the unit.

Public deals are in the repository. The deal deck used for **verified** rows is private and is read from a file outside the repository (`--private-seeds`, or the `HKBENCH_PRIVATE_SEEDS` environment variable). Make one with `python scripts/make_private_deck.py --count 10000 --out /path/outside/the/repo/deck.json`: independent random seeds, never a start and a count (the bench refuses that old form).

A bot never sees the deal's seed. Each decision's `rng_seed` and each game's `game_id` are HMAC-SHA256 outputs under a per-run key: random for a private deck and held only by the bench, fixed and public for a public deck so public runs repeat exactly. A program bot is started afresh for every game and given only a short allowlist of environment variables (`--bot-env NAME` hands over more). Results record `"rng_scheme": "hmac-sha256-v2"`.

## What is in here

```
hkbench/           the engine, the harness, the reference bots, the CLI
tables/            frozen, versioned tables: rules, field pins, deal range, engine fingerprint
protocol/          PROTOCOL.md and schema.json
scripts/           render_rules.py, render_charts.py, make_private_deck.py, and sandbox/macos.sh
docs/assets/       the banner and results chart, light and dark
examples/bots/     a Python bot and a JavaScript bot that pass the harness
results/           one JSON per scored run, and compressed per-game logs
site/              the static leaderboard (index.html and leaderboard.json)
tests/             scoring goldens, engine fingerprint, statistics, protocol, fair play, determinism
```

More: `BENCHMARK_CARD.md` (what the bench measures and where it is weak), `RULES.md`, [`SUBMITTING.md`](SUBMITTING.md), `CHANGELOG.md`.

## Tracks

The leaderboard has three tracks: **Bots**, **LLMs** and **Humans**. Only the Bots track has results so far.

## Citation

```bibtex
@misc{hongkongmahjongbench2026,
  title = {Hong Kong Mahjong Bench},
  year = {2026},
  howpublished = {\url{https://github.com/vnguyen9/mjss-hongkong-mahjong-bench}},
  note = {Version 1.1.0}
}
```
