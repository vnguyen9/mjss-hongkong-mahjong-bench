"""A bot that is honest only when it deals, for the seed-hole tests only.

As dealer its answers are a function of the message. As any other seat it answers at random from the operating system, so a check that only ever seats it as dealer would pass it.
"""

import json
import os
import random
import sys

for line in sys.stdin:
    msg = json.loads(line)
    if msg["type"] == "hello":
        print(json.dumps({"type": "ready", "name": "dealer-gate"}), flush=True)
    elif msg["type"] == "decide":
        legal = [a["id"] for a in msg["legal"]]
        if msg["dealer"] == 0:
            pick = legal[msg["seq"] % len(legal)]
        else:
            pick = random.SystemRandom().choice(legal)
        print(json.dumps({"type": "action", "seq": msg["seq"], "id": pick}), flush=True)
    elif msg["type"] == "bye":
        break
