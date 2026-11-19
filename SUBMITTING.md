# Submitting a bot

We run submitted bots on our own machines, on the private deals, with no network. You do not send us private model files unless you choose to.

## 1. Make it speak the protocol

Your bot is a program that reads JSON lines on stdin and writes JSON lines on stdout. `protocol/PROTOCOL.md` has every message. `examples/bots/python_bot.py` and `examples/bots/javascript_bot.js` are complete examples.

Two rules matter most:

* **Same message, same answer.** Seed any randomness from `rng_seed`. Do not use the clock, files, the network or memory of earlier hands.
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

**A Docker image.** The image's entry point (or the command we give it) starts your bot and speaks the protocol on stdin and stdout. We run it with no network, a CPU and memory limit, and a read-only file system apart from a scratch directory. Send the image (or a registry path) and the image digest.

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

## 4. What we do with it

1. Check the reference field pins and the engine fingerprint.
2. Run the fair-play check.
3. Play the private deals in duplicate against the frozen field (and head to head against other listed bots if you want a Bradley-Terry rank).
4. Publish a result file and a log of each game's outcome by deal number. The log has no walls, deals or actions, so it does not reveal the private deck.
5. The row is tagged **verified**. The command that reproduces it on the public deals is on the row.

If your bot fails the fair-play check, breaks the protocol too often, or crashes, we tell you why and do not list it.

## LLMs

The LLM track is not open yet. When it is, a language model plays through the same protocol. We will record cost per hand, and the time limit will be set for models. Until then, an LLM bot can be scored in the Bots track by wrapping it as a program, with its time limit raised and recorded in the result.

## Questions and rule errors

Open an issue in this repository.
