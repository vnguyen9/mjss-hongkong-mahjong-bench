# Hong Kong Mahjong Bench

A fair way to compare Hong Kong Mahjong players: bots today, language models and people next.

The headline number is **points a hand against a frozen field of reference bots**, in duplicate play, with a 95% interval. Every deal is played four times on the same wall, with the player under test in each seat once. Every row says which rules it was scored under and whether the deals were private.

This repository holds the rules engine, the scorer and the harness. It is MIT licensed. It has no training code and no model weights.

## Two rule sets

| Table | Rules | State |
|---|---|---|
| `hk-hkma-v1` | HKMA Classical: 3 faan to win, cap 10, discarder pays the whole hand, flowers do not score | scoring |
| `hk-house-v1` | House: flowers score, limit hands graded, cap 13, Seven Pairs is a hand | scoring |

HKMA Classical is the headline because it has a citable rulebook. `RULES.md` lists every faan value, the payout, and the places where `hk-hkma-v1` is not the rulebook.

## Quick start

Python 3.9 or newer. No packages to install.

```
git clone <this repository>
cd mjss-hongkong-mahjong-bench
python -m unittest discover -s tests          # or: python -m pytest tests
```

Reproduce a row of the leaderboard with one command (about a minute for the fast bots):

```
python -m hkbench score --table hk-hkma-v1 --bot ref:ukeire --deals 200 --workers 2
```

It prints points a hand with its 95% interval, win rate, deal-in rate, average win and limit hands. It also writes one result file and a compressed log of every game to `results/`. The run is tagged **unverified**, because it used the public deals.

Score your own bot. It is any program that reads one JSON object per line on stdin and writes one per line on stdout (`protocol/PROTOCOL.md`):

```
python -m hkbench score --table hk-hkma-v1 \
    --bot "python examples/bots/python_bot.py" --name my_bot --trained-on "none" --deals 200 --workers 2
python -m hkbench score --table hk-hkma-v1 --bot "node examples/bots/javascript_bot.js" --deals 50
```

Other commands:

```
hkbench h2h --table hk-hkma-v1 --bot a=ref:ukeire --bot b="python examples/bots/python_bot.py" --deals 100
hkbench fairplay --table hk-hkma-v1 --bot "python examples/bots/python_bot.py"
hkbench fingerprint --table hk-hkma-v1          # does this engine reproduce the table's fingerprint?
hkbench verify-log results/logs/<file>.jsonl.gz # replay every game in a log
hkbench site                                    # rebuild site/leaderboard.json and site/index.html
hkbench tables                                  # list tables, check the reference field pins
```

(`python -m hkbench` works everywhere; `hkbench` is installed by `pip install -e .`.)

## How a row is scored

1. **Table checks.** The reference bots must match their pinned hashes, and the engine must reproduce the table's fingerprint: 300 fixed deals and 33 fixed hands, hashed. If either fails, nothing is scored.
2. **Fair-play check.** The bench takes real decision points, re-shuffles every hidden tile (the other hands and the wall) into a new arrangement that looks the same from the bot's seat, and asks again. A changed answer rejects the bot.
3. **Duplicate play.** The bot takes one seat, the three field bots fill the others. Every deal is played from all four seats.
4. **Numbers.** One average per deal, then the mean and a 95% interval over deals. The four games of a deal are not independent, so the deal is the unit.

Public deals are in the repository. The deal deck used for **verified** rows is private and is read from a file outside the repository (`--private-seeds`, or the `HKBENCH_PRIVATE_SEEDS` environment variable).

## What is in here

```
hkbench/           the engine, the harness, the reference bots, the CLI
tables/            frozen, versioned tables: rules, field pins, deal range, engine fingerprint
protocol/          PROTOCOL.md and schema.json
examples/bots/     a Python bot and a JavaScript bot that pass the harness
results/           one JSON per scored run, and compressed per-game logs
site/              the static leaderboard (index.html and leaderboard.json)
tests/             scoring goldens, engine fingerprint, statistics, protocol, fair play, determinism
```

More: `BENCHMARK_CARD.md` (what the bench measures and where it is weak), `RULES.md`, `SUBMITTING.md`, `CHANGELOG.md`.

## Tracks

The leaderboard has three tracks: **Bots**, **LLMs** and **Humans**. Bots has rows. LLMs and Humans are coming.
