"""A bot that plays its own moves, not the reference bots', and checks the game it is shown, for the seed-hole tests only.

It always throws the highest-numbered legal discard, passes on every claim and wins when it can. It
remembers the discard it chose, and in its next message that discard must be on the table. Every
message that breaks this is written to the file named by PROBE_OUT, so a check that feeds a bot a game
that did not follow its own moves is seen.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def choose(msg):
    legal = [a["id"] for a in msg["legal"]]
    if 1 in legal:
        return 1
    if msg["phase"] == "claim":
        return 0 if 0 in legal else legal[0]
    discards = [a for a in legal if 2 <= a <= 35]
    return max(discards) if discards else legal[0]


def main():
    last_discard = None
    for line in sys.stdin:
        msg = json.loads(line)
        if msg["type"] == "hello":
            print(json.dumps({"type": "ready", "name": "consistent"}), flush=True)
        elif msg["type"] == "decide":
            if last_discard is not None:
                ok = any(d["p"] == 0 and d["tile"] == last_discard for d in msg["discards"])
                if not ok:
                    with open(os.environ["PROBE_OUT"], "a") as f:
                        f.write(json.dumps({"inconsistent": True, "seq": msg["seq"], "wanted": last_discard}) + "\n")
            action = choose(msg)
            last_discard = action - 2 if 2 <= action <= 35 else None
            print(json.dumps({"type": "action", "seq": msg["seq"], "id": action}), flush=True)
        elif msg["type"] == "bye":
            break


if __name__ == "__main__":
    main()
