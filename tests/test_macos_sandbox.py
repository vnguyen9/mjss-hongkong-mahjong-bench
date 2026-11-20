"""The macOS sandbox (scripts/sandbox/macos.sh): what it must stop, and that an honest bot still plays through it.

Runs only on macOS with /usr/bin/sandbox-exec; skipped elsewhere.
"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

from helpers import ROOT, hkma_table
from test_bench import meta

from hkbench import bench
from hkbench.players import ProcessPlayer

PY = sys.executable
TABLE = hkma_table()
WRAPPER = ROOT / "scripts" / "sandbox" / "macos.sh"
AVAILABLE = sys.platform == "darwin" and os.access("/usr/bin/sandbox-exec", os.X_OK)


def parent_dir():
    """Where the wrapper keeps its scratch directories (see the script)."""
    base = os.environ.get("HKSANDBOX_PARENT") or tempfile.gettempdir()
    return os.path.join(os.path.realpath(base), "hkbench-sandbox-%d" % os.getuid())


@unittest.skipUnless(AVAILABLE, "needs macOS sandbox-exec")
class MacSandbox(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp))
        self.denied = self.tmp / "deck.json"
        self.denied.write_text("private")
        self.other = self.tmp / "other.txt"
        self.other.write_text("readable")
        self.outside = self.tmp / "outside.txt"
        os.makedirs(parent_dir(), mode=0o700, exist_ok=True)
        # another launch's directory: it carries a live process id, so the wrapper's clean-up leaves it alone
        self.sibling = Path(parent_dir()) / ("%d-sibling" % os.getpid())
        self.sibling.mkdir(mode=0o700, exist_ok=True)
        (self.sibling / "secret.txt").write_text("not yours")
        self.addCleanup(shutil.rmtree, str(self.sibling), True)

    def sandbox(self, *opts):
        return " ".join([str(WRAPPER)] + list(opts) + ["--"])

    def probe(self, hold=False):
        cmd = "%s %s %s %s %s %s" % (PY, ROOT / "tests" / "sandbox_probe_bot.py", self.sibling, self.denied,
                                      self.other, self.outside)
        env = {"HOLD": "1"} if hold else {}
        return ProcessPlayer(cmd, TABLE.id, sandbox=self.sandbox("--deny-read", str(self.denied)), env=env)

    def test_what_the_sandbox_stops_and_what_it_leaves(self):
        p = self.probe()
        try:
            r = json.loads(p.name)
        finally:
            p.close()
        self.assertEqual(r["write_outside"], "denied")
        self.assertFalse(self.outside.exists())
        self.assertEqual(r["write_scratch"], "allowed")
        self.assertEqual(r["read_sibling"], "denied")
        self.assertEqual(r["stat_sibling"], "denied")
        self.assertEqual(r["list_parent"], "denied")
        self.assertEqual(r["read_denied"], "denied")
        self.assertEqual(r["read_other"], "allowed")
        self.assertEqual(r["connect"], "denied")
        self.assertEqual(r["fork"], "denied")
        self.assertEqual(r["subprocess"], "denied")
        self.assertTrue(r["home_is_scratch"])
        self.assertEqual(os.path.dirname(r["scratch"]), parent_dir())

    def test_the_scratch_is_removed_when_the_bot_ends_and_when_it_is_stopped(self):
        p = self.probe()
        scratch = json.loads(p.name)["scratch"]
        self.assertTrue(os.path.isdir(scratch))
        p.close()
        for _ in range(40):
            if not os.path.exists(scratch):
                break
            time.sleep(0.05)
        self.assertFalse(os.path.exists(scratch))
        p = self.probe(hold=True)  # ignores bye, so the bench has to stop it
        scratch = json.loads(p.name)["scratch"]
        p.close()
        for _ in range(60):
            if not os.path.exists(scratch):
                break
            time.sleep(0.05)
        self.assertFalse(os.path.exists(scratch))
        self.assertFalse(os.path.exists(scratch + ".sb"))

    def test_a_bot_plays_a_scored_run_through_it(self):
        py_bot = "%s %s" % (PY, ROOT / "examples" / "bots" / "python_bot.py")
        r = bench.score(TABLE, py_bot, meta(py_bot), deals=2, skip_fairplay=True, quiet=True, write=False,
                        results_dir=self.tmp, sandbox=self.sandbox(), workers=1)
        self.assertEqual(r["isolation"], "sandbox")
        self.assertEqual(r["headline"]["games"], 8)
        self.assertEqual(r["faults"]["faults"], {})

    def test_it_refuses_a_deny_read_it_cannot_resolve_and_unknown_options(self):
        import subprocess
        for args in (["--deny-read", "/no/such/dir/deck.json", "--", "/usr/bin/true"], ["--bogus", "--", "/usr/bin/true"],
                     ["--"]):
            code = subprocess.run([str(WRAPPER)] + args, capture_output=True).returncode
            self.assertEqual(code, 2, args)


if __name__ == "__main__":
    unittest.main()
