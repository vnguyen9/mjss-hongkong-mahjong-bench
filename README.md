# Hong Kong Mahjong Bench

A fair way to compare Hong Kong Mahjong players: bots today, language models and people next.

The headline number is **points a hand against a frozen field of reference bots**, in duplicate play, with a 95% interval. Every deal is played four times on the same wall, with the player under test in each seat once. Every row says which rules it was scored under and whether the deals were private.

This repository holds the rules engine, the scorer and the harness. It is MIT licensed and contains no private artifacts.

## Three rule sets

| Table | Rules | State |
|---|---|---|
| `hk-hkma-v1` | HKMA Classical: 3 faan to win, cap 10, discarder pays the whole hand, flowers do not score | scoring |
| `hk-house-v1` | House: flowers score, limit hands graded, cap 13, Seven Pairs is a hand | scoring |
| `hk-chicken-v1` | Chicken hand: HKMA Classical with a 0-faan minimum, so a hand with no scoring pattern wins; faan still score and pay | scoring |

HKMA Classical is the headline because it has a citable rulebook. `RULES.md` lists every faan value, the payout, and the places where `hk-hkma-v1` is not the rulebook.

## Quick start

Python 3.9 or newer. No packages to install.

```
git clone https://github.com/vnguyen9/mjss-hongkong-mahjong-bench.git
cd mjss-hongkong-mahjong-bench
python -m unittest discover -s tests          # or: python -m pytest tests
```

Reproduce a row of the leaderboard with one command (about a minute for the fast bots):

```
python -m hkbench score --table hk-hkma-v1 --bot ref:ukeire --deals 200 --workers 2
```

It prints points a hand with its 95% interval, win rate, deal-in rate, average win and limit hands. It also writes one result file and a compressed log of every game to `results/`. The run is tagged **unverified**, because it used the public deals.

Each log line is one game: the deal, the arrangement, who won and how, the faan and its `patterns` (`[name, faan]` pairs), the payments, and on public deals the seed and the full action list, so `verify-log` can replay it. To train on the games, add `--training-log` (to `score` or `h2h`; off by default, and with it off the logs are unchanged). Each won game's line then also carries the winner's `melds` (`[kind, tiles, seat the claimed tile came from]`), `concealed` tiles with the winning tile in them, `winning_tile` (null for a flower win), `flowers`, and `winner_draws`, the winner's own draw count from the engine's events. Tiles use the engine's names (`m1`..`m9`, `s1`.., `p1`.., `E S W N`, `C F P`). Seed plus actions rebuild any state, so nothing else is stored. The setting is for public deals: on a private deck the flag is ignored and the log stays outcome-only. The `game_over` message a bot receives (`protocol/PROTOCOL.md`) does not change.

Score your own bot. It is any program that reads one JSON object per line on stdin and writes one per line on stdout (`protocol/PROTOCOL.md`):

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

1. **Table checks.** The reference bots must match their pinned hashes, and the engine must reproduce the table's fingerprint: 300 fixed deals and 42 fixed hands, hashed. If either fails, nothing is scored.
2. **Fair-play check.** The bench takes real decision points, re-shuffles every hidden tile (the other hands and the wall) into a new arrangement that looks the same from the bot's seat, and asks again. A changed answer rejects the bot.
3. **Duplicate play.** The bot takes one seat, the three field bots fill the others. Every deal is played from all four seats.
4. **Numbers.** One average per deal, then the mean and a 95% interval over deals. The four games of a deal are not independent, so the deal is the unit.

Public deals are in the repository. The deal deck used for **verified** rows is private and is read from a file outside the repository (`--private-seeds`, or the `HKBENCH_PRIVATE_SEEDS` environment variable). Make one with `python scripts/make_private_deck.py --count 10000 --out /path/outside/the/repo/deck.json`: independent random seeds, never a start and a count (the bench refuses that old form).

A bot never sees the deal's seed. Each decision's `rng_seed` and each game's `game_id` are HMAC-SHA256 outputs under a per-run key: random for a private deck and held only by the bench, fixed and public for a public deck so public runs repeat exactly. A program bot is started afresh for every game and given only a short allowlist of environment variables (`--bot-env NAME` hands over more). Results record `"rng_scheme": "hmac-sha256-v2"`.

## What is in here

```
hkbench/           the engine, the harness, the reference bots, the CLI
tables/            frozen, versioned tables: rules, field pins, deal range, engine fingerprint
protocol/          PROTOCOL.md and schema.json
scripts/           render_rules.py, and make_private_deck.py for a private deal deck
examples/bots/     a Python bot and a JavaScript bot that pass the harness
results/           one JSON per scored run, and compressed per-game logs
site/              the static leaderboard (index.html and leaderboard.json)
tests/             scoring goldens, engine fingerprint, statistics, protocol, fair play, determinism
```

More: `BENCHMARK_CARD.md` (what the bench measures and where it is weak), `RULES.md`, [`SUBMITTING.md`](SUBMITTING.md), `CHANGELOG.md`.

## Tracks

The leaderboard has three tracks: **Bots**, **LLMs** and **Humans**. Bots has rows. LLMs and Humans are coming.
