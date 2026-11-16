"""The protocol: what the bench sends, what bots send back, and what happens when they get it wrong."""

import json
import os
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from helpers import ROOT, check_message, hkma_profile, hkma_table

from hkbench.engine.game import GameState
from hkbench.engine.tile_instance import STANDARD_INSTANCES
from hkbench.players import BotCrashed, ProcessPlayer, fallback_action, make_player
from hkbench.runner import decision_seed, play_game
from hkbench.seeds import Rng
from hkbench.tables import Deal
from hkbench.view import build_view

PY = sys.executable
EXAMPLES = ROOT / "examples" / "bots"


def some_messages(count=60):
    """Real decide messages from games played by random legal moves."""
    profile = hkma_profile()
    rng = Rng(3)
    out = []
    deal = 0
    while len(out) < count:
        state = GameState.new_game(profile, seed=700 + deal, dealer=deal % 4, prevailing_wind=(deal // 4) % 4)
        seq = 0
        while not state.is_terminal() and len(out) < count:
            actor = state.current_actor()
            msg = build_view(state, actor, game_id="t", seq=seq, rng_seed=decision_seed(700 + deal, 0, seq),
                             table_id="hk-hkma-v1")
            out.append((state.clone(), actor, msg))
            state.apply_action(rng.choice(state.legal_actions(actor)))
            seq += 1
        deal += 1
    return out


class Messages(unittest.TestCase):
    def test_every_decide_message_fits_the_schema(self):
        for _state, _actor, msg in some_messages(200):
            self.assertEqual(check_message(msg, "decide"), [], msg)

    def test_messages_are_plain_json(self):
        for _s, _a, msg in some_messages(30):
            self.assertEqual(json.loads(json.dumps(msg)), msg)

    def test_view_shows_only_what_the_seat_can_see(self):
        for state, actor, msg in some_messages(120):
            me = state.players[actor]
            self.assertEqual(msg["you"]["hand"], list(me.concealed))
            self.assertEqual(sum(msg["you"]["hand"]), me.concealed_count())
            # Other seats: only a hand size, never their tiles.
            for o in msg["others"]:
                self.assertEqual(set(o), {"p", "seat_wind", "hand_size", "melds", "flowers"})
            # The message has exactly the documented fields: no wall order, no other hand.
            self.assertEqual(set(msg), {"protocol", "type", "table", "game_id", "seq", "rng_seed", "phase",
                                        "prevailing_wind", "dealer", "wall_remaining", "you", "others",
                                        "discards", "offer", "unseen", "legal"})
            # The tiles a seat cannot see add up: unseen + own hand + table = 4 of each.
            table = [0] * 34
            for o in msg["others"] + [msg["you"]]:
                for m in o["melds"]:
                    for t in (m["tiles"] if m["kind"] == "chow" else [m["tiles"][0]] * (4 if "kong" in m["kind"] else 3)):
                        table[t] += 1
            river = [0] * 34
            for d in msg["discards"]:
                if not d["claimed"]:
                    river[d["tile"]] += 1
            for t in range(34):
                self.assertEqual(msg["unseen"][t] + msg["you"]["hand"][t] + table[t] + river[t], 4, (t, msg["game_id"]))

    def test_claimed_discards_are_marked(self):
        seen_claimed = False
        for _s, _a, msg in some_messages(400):
            seen_claimed = seen_claimed or any(d["claimed"] for d in msg["discards"])
        self.assertTrue(seen_claimed)

    def test_rng_seed_is_per_decision_and_stable(self):
        self.assertEqual(decision_seed(5, 1, 7), decision_seed(5, 1, 7))
        self.assertNotEqual(decision_seed(5, 1, 7), decision_seed(5, 1, 8))
        self.assertLess(decision_seed(2 ** 40, 3, 1999), 2 ** 31)

    def test_fallback_is_always_legal(self):
        for _s, _a, msg in some_messages(200):
            self.assertIn(fallback_action(msg), [a["id"] for a in msg["legal"]])


class ExampleBots(unittest.TestCase):
    """Both example bots, as separate programs, play whole games through the protocol."""

    def play(self, command):
        table = hkma_table()
        profile = table.profile
        bot = make_player(command, table.id, profile)
        try:
            players = [bot, make_player("ref:ukeire", table.id, profile), make_player("ref:faan_aware", table.id, profile),
                       make_player("ref:deficiency", table.id, profile)]
            recs = [play_game(table.id, profile, Deal(i, 1000000 + i, i % 4, 0), players, arrangement=0) for i in range(3)]
        finally:
            bot.close()
        return bot, recs

    def test_python_example(self):
        bot, recs = self.play("%s %s" % (PY, EXAMPLES / "python_bot.py"))
        self.assertEqual(bot.bot_info["name"], "python_example")
        for r in recs:
            self.assertEqual(sum(r["payments"]), 0)
            self.assertEqual(r["faults"][0], {})

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_javascript_example_agrees_with_the_python_one(self):
        _, py = self.play("%s %s" % (PY, EXAMPLES / "python_bot.py"))
        bot, js = self.play("node %s" % (EXAMPLES / "javascript_bot.js"))
        self.assertEqual(bot.bot_info["name"], "javascript_example")
        self.assertEqual([r["payments"] for r in js], [r["payments"] for r in py])
        self.assertEqual([r["decisions"] for r in js], [r["decisions"] for r in py])


BAD_BOT = textwrap.dedent('''
    import json, sys, time
    MODE = sys.argv[1]
    for line in sys.stdin:
        msg = json.loads(line)
        if msg["type"] == "hello":
            print(json.dumps({"type": "ready", "name": "bad"}), flush=True)
        elif msg["type"] == "decide":
            legal = [a["id"] for a in msg["legal"]]
            if MODE == "illegal":
                print(json.dumps({"type": "action", "seq": msg["seq"], "id": 126 if 126 not in legal else 125}), flush=True)
            elif MODE == "garbage":
                print("this is not json", flush=True)
            elif MODE == "wrongtype":
                print(json.dumps({"type": "action", "seq": msg["seq"], "id": "0"}), flush=True)
            elif MODE == "slow":
                time.sleep(2)
                print(json.dumps({"type": "action", "seq": msg["seq"], "id": legal[0]}), flush=True)
            elif MODE == "crash":
                sys.exit(3)
            elif MODE == "stale":
                # Answer the previous decision's seq, then the right one.
                print(json.dumps({"type": "action", "seq": msg["seq"] - 1, "id": 0}), flush=True)
                print(json.dumps({"type": "action", "seq": msg["seq"], "id": legal[0]}), flush=True)
        elif msg["type"] == "bye":
            break
''')


class BadBots(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.script = os.path.join(cls.dir, "bad_bot.py")
        Path(cls.script).write_text(BAD_BOT)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir)

    def player(self, mode, timeout=0.5):
        return ProcessPlayer("%s %s %s" % (PY, self.script, mode), "hk-hkma-v1", decision_timeout_s=timeout,
                             handshake_timeout_s=10)

    def first_message(self):
        return some_messages(1)[0][2]

    def test_illegal_action_is_replaced_by_the_fallback_and_counted(self):
        p = self.player("illegal")
        try:
            msg = self.first_message()
            action, fault = p.decide(msg)
            self.assertEqual(fault, "illegal")
            self.assertEqual(action, fallback_action(msg))
        finally:
            p.close()

    def test_garbage_and_wrong_types_are_malformed(self):
        for mode in ("garbage", "wrongtype"):
            p = self.player(mode)
            try:
                action, fault = p.decide(self.first_message())
                self.assertEqual(fault, "malformed", mode)
            finally:
                p.close()

    def test_a_slow_bot_times_out(self):
        p = self.player("slow", timeout=0.3)
        try:
            msg = self.first_message()
            action, fault = p.decide(msg)
            self.assertEqual(fault, "timeout")
            self.assertEqual(action, fallback_action(msg))
        finally:
            p.close()

    def test_late_answers_to_old_decisions_are_ignored(self):
        p = self.player("stale")
        try:
            msg = dict(self.first_message(), seq=5)
            action, fault = p.decide(msg)
            self.assertIsNone(fault)
            self.assertEqual(action, msg["legal"][0]["id"])
        finally:
            p.close()

    def test_a_crash_stops_the_run(self):
        p = self.player("crash")
        try:
            with self.assertRaises(BotCrashed):
                p.decide(self.first_message())
        finally:
            p.close()

    def test_no_ready_message_is_a_crash(self):
        with self.assertRaises(BotCrashed):
            ProcessPlayer("%s -c pass" % PY, "hk-hkma-v1", handshake_timeout_s=2)

    def test_missing_program_is_a_crash(self):
        with self.assertRaises(BotCrashed):
            ProcessPlayer("/no/such/program", "hk-hkma-v1")


if __name__ == "__main__":
    unittest.main()
