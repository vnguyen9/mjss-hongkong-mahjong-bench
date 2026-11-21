# Submitting a bot

We run submitted bots on our own machines, on the private deals, with no network. You do not send us private model files unless you choose to.

## 1. Make it speak the protocol

Your bot is a program that reads JSON lines on stdin and writes JSON lines on stdout. `protocol/PROTOCOL.md` has every message. `examples/bots/python_bot.py` and `examples/bots/javascript_bot.js` are complete examples.

Two rules matter most:

* **Same message, same answer.** Seed any randomness from `rng_seed`. Do not use the clock, files, the network or memory of earlier hands. Your bot is started fresh for every game, in an empty directory, so there is no memory to use, and `game_id` and `rng_seed` are keyed hashes that tell you nothing about the deal.
* **Answer within 10 seconds,** with the id of a legal action.

## 2. Test it here

```
python -m hkbench fairplay --table hk-hkma-v1 --bot "<your command>"
python -m hkbench score    --table hk-hkma-v1 --bot "<your command>" --name my_bot \
                           --trained-on "<the rules it was trained on>" --deals 200 --workers 2
```

`fairplay` must pass. `score` on the public deals gives an **unverified** row you can compare with the board. It should make no faults (a few per thousand decisions is the limit).

## 3. Send it

Either:

**A Docker image.** The image's entry point (or the command we give it) starts your bot and speaks the protocol on stdin and stdout. We run it with no network, a CPU and memory limit, and a read-only file system apart from a scratch directory. The deal deck is not in the container. Each bot process also gets its own empty scratch directory (its working directory, `HOME` and temp directory), deleted when the game ends. Send the image (or a registry path) and the image digest.

**Code and model files with an adapter.** A repository or archive with your code and model files, a short adapter that speaks the protocol (the examples are about 80 lines), and the commands to install it. State the Python or Node version. We build and run it in a container.

Tell us:

| Item | Why |
|---|---|
| Name and version | Shown on the board. |
| Track | `bots`, `llms` or `humans`. |
| Rules it was trained on (or "none") | Shown on every row. A bot trained on HKMA rules has an edge on the HKMA table; this keeps that visible. |
| What it is, in a sentence | Shown on the board. |
| Whether you want private model files kept private | They stay private either way. We publish only the result file and outcome-only logs. |
| Permission to list it | Third-party bots are not listed until their authors say yes. |

### How we sandbox it

Official private-deck scores are made with a sandbox: `--sandbox CMD` puts a command in front of every launch of your bot, one fresh sandbox per bot process, torn down with it. `hkbench` refuses a private-deck run of a program bot without it (`--native-unsafe` overrides, prints a warning, and the result records `"isolation": "native"` instead of `"sandbox"`). The recipe we use, with the bot's program directory read-only:

```
python -m hkbench score --table hk-hkma-v1 --private-seeds <deck> --bot "python /bot/my_bot.py" --name my_bot \
  --sandbox "docker run --rm -i --init --network none --read-only --tmpfs /tmp --pids-limit 256 --memory 2g --cpus 2 -v /path/to/bot:/bot:ro my-bot-image"
```

Each bot process gets its own container, with no network, a read-only file system apart from an empty `/tmp`, and the bot directory mounted read-only. When the bench stops the bot it sends the `docker run` wrapper SIGTERM (which Docker passes to the container) and then kills it, so the container and everything in it go with it. The deal deck, the run key and the bench's files are not in the container. This recipe has not been run against every image; the plumbing it relies on (a wrapper that forwards stdin and stdout, and is stopped with its process) is tested with a stand-in wrapper.

**On a Mac without Docker:** `scripts/sandbox/macos.sh` runs each bot under `/usr/bin/sandbox-exec` with a profile made for that launch.

```
python -m hkbench score --table hk-hkma-v1 --private-seeds /path/to/deck.json --bot "python3 /bot/my_bot.py" --name my_bot \
  --sandbox "scripts/sandbox/macos.sh --deny-read /path/to/deck.json --"
```

For each bot process it allows writes only to a new empty directory under a shared mode-0700 parent (`HOME`, `TMPDIR`, `TMP` and `TEMP` point at it, the bot starts in it unless you add `--keep-cwd`, and it is removed when the bot ends or is stopped, SIGTERM included). Because the bot starts in that empty directory, give its script by absolute path (the bench leaves relative paths alone under `--sandbox`), or add `--keep-cwd`. It denies the network, `fork` (so a bot cannot start a descendant, a daemon or a process in a new session, while `exec` still works), POSIX shared memory and Mach service registration, any read of the parent's other directories (other bots' scratch cannot be read, listed or stat-ed), and any read of each `--deny-read` path. `--allow-write PATH` opens a cache the bot needs; `--allow-fork` and `--allow-shm` lift those two denials if a bot cannot start without them. stdin and stdout go to the bot untouched.

Limits, plainly. `sandbox-exec` is deprecated by Apple, though it still works. **Reads elsewhere on disk are still allowed**, so the private deck must be named with `--deny-read` and must not sit in a place the bot is meant to read (its program directory, its model files). The bot can still read the bench's own files and anything else the user can; only what you deny is closed. A torch-based bot starts and runs normally (`fork` and shared memory are not needed); OpenMP prints a harmless `OMP: Warning #179` line on stderr because it cannot create its file in `/tmp`. It costs about 30 percent of a cheap bot's speed (the Python example: 10.4 games a second native, 7.0 sandboxed, one worker), mostly process start-up.

Without a sandbox a bot runs as a normal process of the same user. The bench gives it an empty scratch directory and a limited environment and kills its process group at the end of the game, which keeps honest bots honest. It does not stop a bot that means to cheat: another process of the same user can be reached through the file system, a process that starts a new session survives the kill, and the bot can see `game_over` after it has answered. That is why native private-deck runs are marked and are not official.

## 4. What we do with it

1. Check the reference field pins and the engine fingerprint.
2. Run the fair-play check (in the sandbox).
3. Play the private deals in duplicate against the frozen field (and head to head against other listed bots if you want a Bradley-Terry rank).
4. Publish a result file and a log of each game's outcome by deal number. The log has no walls, deals or actions, so it does not reveal the private deck. (`--training-log` adds nothing on a private deck.)
5. The row is tagged **verified** (a run made without a sandbox never is). The command that reproduces it on the public deals is on the row.

If your bot fails the fair-play check, breaks the protocol too often, or crashes, we tell you why and do not list it.

## LLMs

The LLM track is not open yet. When it is, a language model plays through the same protocol. We will record cost per hand, and the time limit will be set for models. Until then, an LLM bot can be scored in the Bots track by wrapping it as a program, with its time limit raised and recorded in the result.

## Questions and rule errors

Open an issue in this repository.
