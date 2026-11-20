"""A bot that attacks the old seed scheme, for the seed-hole tests only. It lives in tests/, not examples/.

Before 1.1.0 every ``rng_seed`` was SplitMix64 of the deal's seed, and ``game_id`` named the deal and the
arrangement. This bot is told (by CHEAT_TEST_RANGE, "lo,count") that the private deck lies in a small
range, and tries every seed in it against the first two ``rng_seed`` values it sees, under every
arrangement. A seed that fits both is "recovered": with it the bot could rebuild the wall. It writes
what it found, one JSON line per game, to the file named by CHEAT_TEST_OUT, and otherwise plays the
bench's fallback move.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hkbench.players import fallback_action  # noqa: E402
from hkbench.seeds import splitmix64  # noqa: E402


def old_decision_seed(deal_seed, arrangement, seq):
    """The 1.0.0 function, copied here as the attacker's model of the scheme."""
    _, out = splitmix64(((deal_seed & 0xFFFFFFFFFFFF) << 16) ^ (arrangement << 12) ^ seq)
    return out & 0x7FFFFFFF


def invert(observed, candidates, arrangements=(0, 1, 2, 3)):
    """The deal seed in ``candidates`` that explains every (seq, rng_seed) in ``observed``, or None."""
    for seed in candidates:
        for arr in arrangements:
            if all(old_decision_seed(seed, arr, seq) == rng for seq, rng in observed):
                return seed
    return None


def main():
    lo, count = (int(x) for x in os.environ["CHEAT_TEST_RANGE"].split(","))
    seen = []
    for line in sys.stdin:
        msg = json.loads(line)
        if msg["type"] == "hello":
            print(json.dumps({"type": "ready", "name": "seed-cheater"}), flush=True)
        elif msg["type"] == "decide":
            seen.append((msg["seq"], msg["rng_seed"]))
            if len(seen) == 2:
                found = invert(seen, range(lo, lo + count))
                with open(os.environ["CHEAT_TEST_OUT"], "a") as f:
                    f.write(json.dumps({"game_id": msg["game_id"], "recovered": found}) + "\n")
            print(json.dumps({"type": "action", "seq": msg["seq"], "id": fallback_action(msg)}), flush=True)
        elif msg["type"] == "bye":
            break


if __name__ == "__main__":
    main()
