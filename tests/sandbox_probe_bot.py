"""A bot that tries things a sandbox must stop, for the macOS sandbox tests only.

Usage: ``sandbox_probe_bot.py SIBLING_DIR DENIED_FILE OTHER_FILE OUTSIDE_FILE``. It runs its probes before it
answers ``hello`` and reports the results as JSON in the ``name`` of its ``ready`` message, then plays the
bench's fallback move. With ``HOLD=1`` it ignores ``bye`` and sleeps, so a test can stop it from outside.
"""

import json
import os
import socket
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hkbench.players import fallback_action  # noqa: E402


def attempt(f):
    try:
        f()
        return "allowed"
    except OSError as e:
        return "denied"


def probes(sibling, denied, other, outside):
    r = {}
    r["write_outside"] = attempt(lambda: open(outside, "w").write("x"))
    r["write_scratch"] = attempt(lambda: open("scratch.txt", "w").write("x"))
    r["read_sibling"] = attempt(lambda: open(os.path.join(sibling, "secret.txt")).read())
    r["stat_sibling"] = attempt(lambda: os.stat(sibling))
    r["list_parent"] = attempt(lambda: os.listdir(os.path.dirname(os.path.realpath(os.environ["HOME"]))))
    r["read_denied"] = attempt(lambda: open(denied).read())
    r["read_other"] = attempt(lambda: open(other).read())
    r["connect"] = attempt(lambda: socket.create_connection((".".join(["127", "0", "0", "1"]), 9), timeout=1))
    r["fork"] = attempt(lambda: os.fork())
    r["subprocess"] = attempt(lambda: subprocess.run(["/bin/echo", "hi"], capture_output=True, check=True))
    r["scratch"] = os.path.realpath(os.getcwd())
    r["home_is_scratch"] = os.path.realpath(os.environ["HOME"]) == r["scratch"] == os.path.realpath(os.environ["TMPDIR"])
    return r


results = None
for line in sys.stdin:
    msg = json.loads(line)
    if msg["type"] == "hello":
        results = probes(*sys.argv[1:5])
        print(json.dumps({"type": "ready", "name": json.dumps(results)}), flush=True)
    elif msg["type"] == "decide":
        print(json.dumps({"type": "action", "seq": msg["seq"], "id": fallback_action(msg)}), flush=True)
    elif msg["type"] == "bye":
        if os.environ.get("HOLD"):
            time.sleep(60)
        break
