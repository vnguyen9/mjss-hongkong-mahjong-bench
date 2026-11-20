"""A stand-in for a sandbox wrapper such as ``docker run``, for the seed-hole tests only.

Usage: ``sandbox_wrapper.py BOT COMMAND...``. It records each launch in the file named by SANDBOX_LOG.
By default it replaces itself with the bot. With SANDBOX_MODE=term it runs the bot as a child instead
and, like ``docker run`` passing a signal to its container, stops the child when it is sent SIGTERM and writes TERM to the log.
"""

import os
import signal
import subprocess
import sys

log = os.environ.get("SANDBOX_LOG")
argv = sys.argv[1:]
if log:
    with open(log, "a") as f:
        f.write("launch %d\n" % os.getpid())
if os.environ.get("SANDBOX_MODE") == "term":
    child = subprocess.Popen(argv)

    def on_term(_sig, _frame):
        if log:
            with open(log, "a") as f:
                f.write("TERM\n")
        child.kill()
        sys.exit(0)

    signal.signal(signal.SIGTERM, on_term)
    sys.exit(child.wait())
os.execvp(argv[0], argv)
