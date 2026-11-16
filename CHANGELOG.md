# Changelog

## 1.0.0 (2026-11-16)

First release.

* Rules engine and scorer, taken from the maintainers' own Hong Kong Mahjong package and cleaned for the bench: no training code, no models, no encoders.
* Table `hk-hkma-v1` (HKMA Classical): rules, a frozen field of three reference bots (`faan_aware`, `ukeire`, `deficiency`) pinned by source hash, a public deal range, and an engine fingerprint of 300 deals and 30 hands.
* Table `hk-house-v1` (House): defined, marked pending Seven Pairs scoring. It does not score.
* Duplicate scoring, head-to-head matches with Bradley-Terry ranks and bootstrap intervals, deal-clustered intervals, the hidden-tile fair-play check, public and private deal decks, result and log files.
* Protocol `hkbench-1`, with example bots in Python and JavaScript.
* Static leaderboard (`site/`) with Bots, LLMs and Humans tracks.
* Baseline rows on `hk-hkma-v1`: random, deficiency, ukeire, faan_aware, shallow_search, and the Python example bot.

Changes from the source engine:

* Fixed: a Bless of Heaven hand (the dealer wins on the first draw) was accepted but scored as an ordinary hand. It now scores 10 faan on HKMA and 13 on House.
* Fixed: a settlement that does not sum to zero stops the run. It used to be repaired quietly.
* Changed: the deal shuffle is the bench's own SplitMix64 Fisher-Yates, so a seed is the same deal on every Python version.
* Changed: on `hk-hkma-v1` the seven and eight flower instant wins are off, because the rulebook has no flower win.
* Changed: the reference bots read the same seat view an outside bot gets, and draw their randomness from the decision's `rng_seed`. `wait_aware`, which reads other players' hidden hands, is not included.
