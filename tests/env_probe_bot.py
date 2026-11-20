"""A bot that reports its own process, for the seed-hole tests only.

On every ``decide`` it appends one JSON line to the file named by PROBE_OUT: the names of its
environment variables, its process id, a random id made when it started, and the game it was asked about.
"""

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hkbench.players import fallback_action  # noqa: E402

BORN = uuid.uuid4().hex

for line in sys.stdin:
    msg = json.loads(line)
    if msg["type"] == "hello":
        print(json.dumps({"type": "ready", "name": "probe"}), flush=True)
    elif msg["type"] == "decide":
        with open(os.environ["PROBE_OUT"], "a") as f:
            f.write(json.dumps({"env": sorted(os.environ), "pid": os.getpid(), "born": BORN,
                                "game_id": msg["game_id"], "seq": msg["seq"],
                                "values": [v for k, v in os.environ.items() if k.startswith("HKBENCH")]}) + "\n")
        print(json.dumps({"type": "action", "seq": msg["seq"], "id": fallback_action(msg)}), flush=True)
    elif msg["type"] == "bye":
        break
