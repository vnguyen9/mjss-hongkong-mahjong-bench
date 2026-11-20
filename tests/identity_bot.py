"""A bot whose answers depend on which process it is, for the seed-hole tests only.

Each answer is a pure function of the message and of a number drawn when the process started, so the
same position can get different answers from two processes. Asked again in a fresh process, it gives other answers to the
messages it answered before.
"""

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hkbench.players import fallback_action  # noqa: E402

SALT = int(uuid.uuid4().hex[:8], 16)

for line in sys.stdin:
    msg = json.loads(line)
    if msg["type"] == "hello":
        print(json.dumps({"type": "ready", "name": "identity"}), flush=True)
    elif msg["type"] == "decide":
        legal = [a["id"] for a in msg["legal"]]
        pick = legal[(msg["seq"] * 7 + SALT) % len(legal)]
        print(json.dumps({"type": "action", "seq": msg["seq"], "id": pick}), flush=True)
    elif msg["type"] == "bye":
        break
