"""A bot that looks for what an earlier process left behind, for the seed-hole tests only.

On its first decision it records which of its marker files already exist in its working directory, its
HOME and its temp directory, and the paths of those directories, then writes the markers.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hkbench.players import fallback_action  # noqa: E402

first = True
for line in sys.stdin:
    msg = json.loads(line)
    if msg["type"] == "hello":
        print(json.dumps({"type": "ready", "name": "scratch"}), flush=True)
    elif msg["type"] == "decide":
        if first:
            first = False
            places = {"cwd": os.getcwd(), "home": os.environ["HOME"], "tmp": os.environ["TMPDIR"],
                      "temp": os.environ["TEMP"], "tmp2": os.environ["TMP"]}
            found = [k for k, d in places.items() if os.path.exists(os.path.join(d, "left_behind.txt"))]
            for d in set(places.values()):
                with open(os.path.join(d, "left_behind.txt"), "w") as f:
                    f.write("hand")
            with open(os.environ["PROBE_OUT"], "a") as f:
                f.write(json.dumps({"found": found, "places": places, "game_id": msg["game_id"]}) + "\n")
        print(json.dumps({"type": "action", "seq": msg["seq"], "id": fallback_action(msg)}), flush=True)
    elif msg["type"] == "bye":
        break
