# Changelog

## Unreleased

* The hosted bot `h1` is now named `Fu-2.3M-HKMA-1`: family, size (2.3M parameters), the rules it trained on, and version. Its result files, logs and head-to-head entries are renamed; no game, score or hash changed.

## 1.0.0 (2026-11-16)

First release.

* Rules engine and scorer, adapted for the bench with private development artifacts excluded.
* Table `hk-hkma-v1` (HKMA Classical): rules, a frozen field of three reference bots (`faan_aware`, `ukeire`, `deficiency`) pinned by source hash, a public deal range, and an engine fingerprint of 300 deals and 42 hands.
* Table `hk-house-v1` (House): flowers score, limit hands are graded, cap 13, and Seven Pairs is a hand (4 faan, seven different pairs, concealed only, stacking with flushes, Self-Drawn, Closed Hand and flowers; All Honours by Seven Pairs is a limit hand). Same three-bot field, its own pins and fingerprint, and the same baseline rows as HKMA.
* Duplicate scoring, head-to-head matches with Bradley-Terry ranks and bootstrap intervals, deal-clustered intervals, the hidden-tile fair-play check, public and private deal decks, result and log files.
* Protocol `hkbench-1`, with example bots in Python and JavaScript.
* Static leaderboard (`site/`) with Bots, LLMs and Humans tracks.
* Baseline rows on both tables, public deals (unverified): random, deficiency, ukeire and faan_aware and the Python example bot at 2,000 deals each, shallow_search at 400, and a 300-deal head-to-head of five of them, on each table. They reproduce byte for byte on Python 3.9 and 3.11.

Changes from the source engine:

* Fixed: a Bless of Heaven hand (the dealer wins on the first draw) was accepted but scored as an ordinary hand. It now scores 10 faan on HKMA and 13 on House.
* Fixed: a settlement that does not sum to zero stops the run. It used to be repaired quietly.
* Changed: the deal shuffle is the bench's own SplitMix64 Fisher-Yates, so a seed is the same deal on every Python version.
* Fixed: opening flowers are replaced dealer first, in turn order, each seat until it holds none. The engine used to start at seat 0 whatever the dealer. This changes the dealt hands whenever the dealer is not seat 0 and a flower is dealt.
* Fixed: a limit hand dropped Self-Drawn, Last Tile from the Wall, Robbing a Kong and the kong items. They now count, then the cap applies. No money changes on `hk-hkma-v1` (its limits already sit at the cap); on House (cap 13) a self-drawn 10-faan limit is 11. This changed the `faan_aware` source, so the field pin and the engine fingerprint were re-made. The table is still v1: it had not been published.
* Added: Seven Pairs (`is_seven_pairs`, scored in `_score_seven_pairs`), played only where a table's rules file says `win.seven_pairs: true`. It competes with the ordinary reading of the same tiles on raw faan, so a hand that reaches the cap either way is named for the richer one. The HKMA table is unchanged by it: its engine fingerprint over 300 deals is the same before and after. The field's source hashes moved with the engine, so both tables' pins and fingerprints were made after it, and the baseline rows were rerun.
* Changed: on `hk-hkma-v1` the seven and eight flower instant wins are off, because the rulebook has no flower win.
* Changed: the reference bots read the same seat view an outside bot gets, and draw their randomness from the decision's `rng_seed`. `wait_aware`, which reads other players' hidden hands, is not included.
