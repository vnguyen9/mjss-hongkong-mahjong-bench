# Submitting a bot

A submission is a program that speaks `hkbench-1` (JSON lines over stdin/stdout). We score it on the private deck, in a sandbox with no network, and publish the result file and outcome-only logs. We never publish your code or model files.

## Contract

| | |
|---|---|
| Protocol | `protocol/PROTOCOL.md`, schema in `protocol/schema.json`. Reference bots: `examples/bots/python_bot.py`, `examples/bots/javascript_bot.js` (about 80 lines each). |
| Lifecycle | One process per seat per game. `hello` → `ready` (30 s), then `decide` → `action` until `game_over` and `bye`. The process is killed when the game ends. |
| Time limit | 10 s per decision (`decision_s` in `tables/<table>/table.json`). |
| Faults | A late, malformed or illegal answer is replaced by a fallback move and counted. More than 1 per 1,000 decisions rejects the run. |
| Determinism | The same `decide` history must produce the same action. Take all randomness from `rng_seed`. |
| State | In-game memory of your own seat's earlier messages and answers is allowed. Nothing may come from another game, the clock, the file system or the network. |
| Information | `decide` carries only what the seat can see. `game_id` and `rng_seed` are HMAC-SHA256 outputs under a per-run key and carry no information about the deal. |
| Environment | Fresh empty working directory, `HOME` and temp directory per process. Only `PATH`, `HOME`, `LANG`, `LC_*`, `TMPDIR`, `TEMP`, `TMP` and `SYSTEMROOT` are passed; `--bot-env NAME` adds more, and `HKBENCH_*` is never passed. |

## Fair play

`fairplay` plays real games on secret deals, stops at chosen decisions, re-deals every tile your seat cannot see (the other hands and the wall) into a new arrangement consistent with your view, and asks again. Any changed answer fails the bot. The probe messages are indistinguishable from real play. A bot that reads hidden state, or whose output depends on anything outside the message history and `rng_seed`, fails.

## Test locally

```
python -m hkbench fairplay --table hk-hkma-v1 --bot "<cmd>"
python -m hkbench score    --table hk-hkma-v1 --bot "<cmd>" --name my_bot \
                           --trained-on "<rules it trained on, or none>" --deals 200 --workers 2
```

`fairplay` must pass and `score` must stay under the fault limit. A public-deck `score` gives an **unverified** row that is directly comparable with the board, and its log replays with `verify-log`. Run all three tables; a bot is listed per table.

## What to send

Either a Docker image (send the digest), or a repository or archive with the adapter, pinned dependencies and the install command (state the Python or Node version; we build it in a container). Include:

| Field | Use |
|---|---|
| Name and version | Row label. |
| Track | `bots`, `llms` or `humans`. |
| Trained on | Rule set the bot was trained or tuned for, or `none`. Shown on every row, because training on a table's rules is an advantage on that table. |
| One-line description | Shown on the board. |
| Permission to list | Required. We may also run a bot from its authors' public code; such a row says it was run by the maintainers, and the authors can replace it with their own submission. |

## How a row is produced

1. The reference bots' pinned hashes and the engine fingerprint are checked; any mismatch stops the run.
2. `fairplay` runs inside the sandbox.
3. The bot plays every private deal from all four seats against the frozen field. Optionally, it joins a head-to-head for a Bradley-Terry rating.
4. We publish the result JSON and a log of each game's outcome by deal number. Private logs carry no walls, deals or actions, so the deck stays secret; `--training-log` is ignored on a private deck.
5. The row is tagged **verified**. It carries the command that reproduces it on the public deals.

A bot that fails fair play, exceeds the fault limit or crashes is not listed; we send the reason.

## Sandbox

Private-deck runs of program bots require `--sandbox CMD`, a wrapper placed in front of every launch, one sandbox per process. `--native-unsafe` overrides it, prints a warning and records `"isolation": "native"`; such rows are never verified.

**Docker.** Mount the bot read-only:

```
python -m hkbench score --table hk-hkma-v1 --private-seeds <deck> --bot "python /bot/my_bot.py" --name my_bot \
  --sandbox "docker run --rm -i --init --network none --read-only --tmpfs /tmp --pids-limit 256 --memory 2g --cpus 2 -v /path/to/bot:/bot:ro my-bot-image"
```

Each process gets its own container: no network, read-only root, empty `/tmp`. On stop the bench sends SIGTERM to the `docker run` wrapper, which forwards it, then kills it. The deck, run key and bench files are never in the container. The wrapper plumbing (stdin/stdout forwarding, stop propagation) is covered by tests with a stand-in wrapper; the recipe itself has not been run against every image.

**macOS.** `scripts/sandbox/macos.sh` wraps each launch in `/usr/bin/sandbox-exec` with a per-launch profile:

```
python -m hkbench score --table hk-hkma-v1 --private-seeds /path/to/deck.json --bot "python3 /bot/my_bot.py" --name my_bot \
  --sandbox "scripts/sandbox/macos.sh --deny-read /path/to/deck.json --"
```

| Rule | Detail |
|---|---|
| Writes | Only to a fresh directory under a mode-0700 parent. `HOME`, `TMPDIR`, `TMP` and `TEMP` point at it; it is removed when the bot exits or is stopped. The bot starts there, so pass its script by absolute path or add `--keep-cwd`. |
| Denied | Network, `fork` (`exec` still works), POSIX shared memory, Mach service registration, reads of sibling scratch directories, and every `--deny-read` path. |
| Opt-outs | `--allow-write PATH` for a cache, `--allow-fork` and `--allow-shm` for bots that cannot start without them. |
| Not denied | Other reads. The deck must be listed with `--deny-read` and must not sit anywhere the bot is meant to read. |
| Cost | About 30% on a cheap bot, mostly process start-up (Python example, one worker: 10.4 games/s native, 7.0 sandboxed). Torch bots run unchanged; OpenMP prints a harmless `OMP: Warning #179`. |

`sandbox-exec` is deprecated by Apple but still works.

**Without a sandbox** the bot runs as a normal process of the same user, with a scratch directory, a reduced environment and a process-group kill at game end. That stops accidental state sharing, not cheating: the bot can reach other processes through the file system, a process that calls `setsid` survives the kill, and the bot sees `game_over` after answering. That is why native private-deck runs are not official.

## LLMs

The LLM track is not open yet. It will use the same protocol, record cost per hand and set its own time limit. Until then an LLM can be scored on the Bots track as a wrapped program, with the raised time limit recorded in the result.

## Questions and rule errors

Open an issue.
