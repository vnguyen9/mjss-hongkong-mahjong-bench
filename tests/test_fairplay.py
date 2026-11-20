"""The fair-play check: honest bots pass, a bot that reads hidden tiles is caught."""

import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT, hkma_table

from hkbench import bench, fairplay
from hkbench.engine.tile_instance import STANDARD_INSTANCES
from hkbench.seeds import Rng

PY = sys.executable
TABLE = hkma_table()


def leak_hook(path):
    def hook(state, actor, msg):
        hands = [list(state.players[s].concealed) for s in range(4) if s != actor]
        Path(path).write_text(json.dumps({"hands": hands}))
    return hook


class Reshuffle(unittest.TestCase):
    def test_hidden_tiles_move_and_everything_visible_stays(self):
        pts = fairplay.collect_points(TABLE.profile, TABLE.id, 25)
        moved = 0
        rng = Rng(1)
        for state, actor, _idx, _seq in pts:
            other = fairplay.reshuffle_hidden(state, actor, rng)
            self.assertTrue(other.check_invariants().ok, other.check_invariants().messages)
            self.assertEqual(other.players[actor].concealed, state.players[actor].concealed)
            self.assertEqual(other.wall_remaining(), state.wall_remaining())
            for s in range(4):
                self.assertEqual(sum(other.players[s].concealed), sum(state.players[s].concealed))
                self.assertEqual(other.players[s].melds, state.players[s].melds)
                self.assertEqual(other.players[s].flowers, state.players[s].flowers)
            self.assertEqual(other.river, state.river)
            moved += any(other.players[s].concealed != state.players[s].concealed for s in range(4) if s != actor)
        self.assertGreater(moved, 20)

    def test_the_original_state_is_untouched(self):
        state, actor, _i, _s = fairplay.collect_points(TABLE.profile, TABLE.id, 1)[0]
        before = state.clone()
        fairplay.reshuffle_hidden(state, actor, Rng(2))
        self.assertEqual(state.wall_order, before.wall_order)
        self.assertEqual(state.concealed_ids, before.concealed_ids)


class Honest(unittest.TestCase):
    def test_reference_and_example_bots_pass(self):
        for spec in ("ref:random", "ref:ukeire", "ref:faan_aware", "ref:deficiency",
                     "%s %s" % (PY, ROOT / "examples" / "bots" / "python_bot.py")):
            with self.subTest(bot=spec):
                rep = fairplay.check(TABLE, spec, points=40)
                self.assertTrue(rep["passed"], rep)
                self.assertEqual(rep["view_mismatches"], 0)
                self.assertEqual(rep["decision_changes"], 0)
                self.assertGreaterEqual(rep["asks"], 40 * 3)


class Cheating(unittest.TestCase):
    def setUp(self):
        fd, self.leak = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        self.addCleanup(os.remove, self.leak)
        self.cheater = "%s %s" % (PY, ROOT / "tests" / "cheat_bot.py")

    def test_a_bot_that_reads_hidden_hands_is_caught(self):
        rep = fairplay.check(TABLE, self.cheater, points=60, on_decision=leak_hook(self.leak),
                             bot_env={"CHEAT_TEST_LEAK": self.leak})
        self.assertFalse(rep["passed"])
        self.assertGreater(rep["decision_changes"], 0)
        self.assertEqual(rep["view_mismatches"], 0)  # the bench itself did not leak

    def test_without_the_leak_the_same_bot_is_indistinguishable_from_an_honest_one(self):
        # Same program, but the file never changes with the hidden tiles: nothing to catch.
        Path(self.leak).write_text(json.dumps({"hands": [[0] * 34] * 3}))
        rep = fairplay.check(TABLE, self.cheater, points=30, bot_env={"CHEAT_TEST_LEAK": self.leak})
        self.assertTrue(rep["passed"], rep)

    def test_scoring_refuses_a_cheater(self):
        # score() runs the check without the test hook, so wrap the check to add it.
        real = fairplay.check

        def with_hook(table, spec, **kw):
            return real(table, spec, on_decision=leak_hook(self.leak), **kw)

        with mock.patch.object(fairplay, "check", with_hook):
            meta = bench.bot_meta(self.cheater, name="cheater", track="bots", kind=None, trained_on=None,
                                  description=None, cwd=None, hash_dir=None, hash_override=None)
            with self.assertRaises(bench.Rejected):
                bench.score(TABLE, self.cheater, meta, deals=2, results_dir=Path(tempfile.mkdtemp()),
                            fairplay_points=40, write=False, quiet=True, bot_env={"CHEAT_TEST_LEAK": self.leak})

    def test_a_harness_that_leaks_is_reported_as_a_view_mismatch(self):
        real = fairplay.build_view

        def leaky(state, seat, **kw):
            msg = real(state, seat, **kw)
            msg["secret"] = [list(p.concealed) for p in state.players]  # what a bug in the bench would look like
            return msg

        with mock.patch.object(fairplay, "build_view", leaky):
            rep = fairplay.check(TABLE, "ref:ukeire", points=20)
        self.assertFalse(rep["passed"])
        self.assertGreater(rep["view_mismatches"], 0)


class Nondeterminism(unittest.TestCase):
    def test_a_bot_that_ignores_rng_seed_is_rejected(self):
        script = Path(tempfile.mkdtemp()) / "dicey.py"
        script.write_text(textwrap.dedent('''
            import json, random, sys
            for line in sys.stdin:
                m = json.loads(line)
                if m["type"] == "hello":
                    print(json.dumps({"type": "ready"}), flush=True)
                elif m["type"] == "decide":
                    print(json.dumps({"type": "action", "seq": m["seq"], "id": random.choice(m["legal"])["id"]}), flush=True)
                elif m["type"] == "bye":
                    break
        '''))
        rep = fairplay.check(TABLE, "%s %s" % (PY, script), points=30)
        self.assertFalse(rep["passed"])
        self.assertGreater(rep["decision_changes"], 0)


if __name__ == "__main__":
    unittest.main()
