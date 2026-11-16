"""A deliberately dishonest bot, for the fair-play tests only. It lives in tests/, not examples/.

The protocol gives a bot only its own seat's view, so this bot needs a second channel: the test
harness writes the other seats' concealed hands to the file named by HKBENCH_TEST_LEAK before every
decision. The bot reads that file. It never discards a tile any opponent could win on, and among
the safe tiles it throws the one the opponents hold the most of.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hkbench.engine.win import waits  # noqa: E402


def decide(msg):
    legal = {a["id"]: a for a in msg["legal"]}
    if 1 in legal:
        return 1
    if msg["phase"] == "claim":
        return 0
    with open(os.environ["HKBENCH_TEST_LEAK"]) as f:
        hands = json.load(f)["hands"]
    live = set()
    held = [0] * 34
    for h in hands:
        if sum(h) % 3 == 1:
            live.update(waits(h, []))
        for t in range(34):
            held[t] += h[t]
    discards = [a for a in msg["legal"] if a["kind"] == "discard"]
    safe = [a for a in discards if a["tile"] not in live] or discards
    return max(safe, key=lambda a: (held[a["tile"]], -a["id"]))["id"]


for line in sys.stdin:
    msg = json.loads(line)
    if msg["type"] == "hello":
        print(json.dumps({"type": "ready", "name": "cheater"}), flush=True)
    elif msg["type"] == "decide":
        print(json.dumps({"type": "action", "seq": msg["seq"], "id": decide(msg)}), flush=True)
    elif msg["type"] == "bye":
        break
