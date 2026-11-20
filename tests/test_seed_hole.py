"""The seed hole (1.0.0): a bot could rebuild the private wall from ``rng_seed``. These tests keep it shut.

* ``rng_seed`` and ``game_id`` come from a run key, never from the deal's seed or index.
* Public runs repeat exactly; a private run's streams change with its key.
* A bot's process starts afresh for every game and sees none of the bench's environment.
* The key goes into no result and no log.
* The private deck generator makes independent seeds, and the loader refuses the old start-and-count deck.
"""

import base64
import time
import gzip
import importlib.util
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import textwrap
import unittest
import warnings
from pathlib import Path
from unittest import mock

from helpers import ROOT, hkma_profile, hkma_table
from test_bench import meta

import seed_cheat_bot
from hkbench import bench, fairplay, pool, runkey
from hkbench.players import BYE_GRACE_S, Player, ProcessPlayer, bot_environment, fallback_action, make_player
from hkbench.runner import play_game
from hkbench.seeds import dealer_for_index, wind_for_index
from hkbench.tables import Deal, check_seed, list_tables, load_private_seeds

PY = sys.executable
TABLE = hkma_table()
PROFILE = hkma_profile()
HEX_ID = re.compile(r"^[0-9a-f]{32}$")


class Recorder(Player):
    """Sits at a seat, plays the bench's fallback move, and remembers every message it was sent."""
    name = "recorder"

    def __init__(self):
        self.msgs = []

    def decide(self, msg):
        self.msgs.append(msg)
        return fallback_action(msg), None


def deal_at(index, seed):
    return Deal(index, seed, dealer_for_index(index), wind_for_index(index))


def play_recorded(deal, key, arrangement=0, table_id=TABLE.id):
    rec = Recorder()
    others = [make_player("ref:" + n, table_id, PROFILE) for n in ("ukeire", "faan_aware", "deficiency")]
    seats = [None] * 4
    seats[arrangement] = rec
    for s, o in zip([s for s in range(4) if s != arrangement], others):
        seats[s] = o
    play_game(table_id, PROFILE, deal, seats, arrangement=arrangement, run_key=key)
    return rec.msgs


def stream(msgs):
    return [(m["game_id"], m["seq"], m["rng_seed"]) for m in msgs]


class KeyedSeeds(unittest.TestCase):
    def test_the_old_function_is_gone(self):
        from hkbench import runner
        self.assertFalse(hasattr(runner, "decision_seed"))

    def test_the_deal_seed_is_not_an_input(self):
        # Same index, same key, different deal seeds: the bot is sent the same ids and numbers.
        key = runkey.new_run_key()
        a = stream(play_recorded(deal_at(5, 111), key))
        b = stream(play_recorded(deal_at(5, 222), key))
        by_seq_a, by_seq_b = {x[1]: x for x in a}, {x[1]: x for x in b}
        common = set(by_seq_a) & set(by_seq_b)
        self.assertTrue(common)
        for seq in common:  # the game differs, the numbers and the id do not
            self.assertEqual(by_seq_a[seq], by_seq_b[seq])

    def test_seeds_are_below_two_to_the_31_and_the_ids_are_opaque(self):
        for m in play_recorded(deal_at(3, 99), runkey.new_run_key()):
            self.assertLess(m["rng_seed"], 2 ** 31)
            self.assertRegex(m["game_id"], HEX_ID)

    def test_old_inversion_recovers_the_seed_from_a_1_0_0_game(self):
        # Positive control: the attack is real against the old scheme.
        true_seed = 5_000_000_000 + 37
        obs = [(seq, seed_cheat_bot.old_decision_seed(true_seed, 2, seq)) for seq in (1, 2)]
        self.assertEqual(seed_cheat_bot.invert(obs, range(5_000_000_000, 5_000_000_000 + 64)), true_seed)

    def test_old_inversion_finds_nothing_in_a_keyed_game(self):
        lo, n = 5_000_000_000, 64
        for index in (0, 7, 37):
            msgs = play_recorded(deal_at(index, lo + index), runkey.new_run_key(), arrangement=2)
            obs = [(m["seq"], m["rng_seed"]) for m in msgs[:2]]
            self.assertIsNone(seed_cheat_bot.invert(obs, range(lo, lo + n)), index)
            # nor through the id: it holds no index or arrangement to start from
            self.assertIsNone(re.search(r"/d\d+/a\d+", msgs[0]["game_id"]))

    def test_a_cheating_program_cannot_recover_a_seed(self):
        # The cheat bot, as a separate process, tries the old inversion on every game of a private run.
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp))
        out = tmp / "found.jsonl"
        lo, n = 5_000_000_000, 32
        deck = [lo + i for i in range(n)]
        config = {"table": TABLE.id, "tables_dir": str(TABLE.dir.parent),
                  "players": {"bot": "%s %s" % (PY, ROOT / "tests" / "seed_cheat_bot.py"),
                              "f0": "ref:ukeire", "f1": "ref:faan_aware", "f2": "ref:deficiency"},
                  "run_key": runkey.new_run_key(),
                  "bot_env": {"CHEAT_TEST_OUT": str(out), "CHEAT_TEST_RANGE": "%d,%d" % (lo, n)}}
        deals = [deal_at(i, deck[i]) for i in range(8)]
        pool.run_specs(config, bench.duplicate_specs(deals), workers=1)
        found = [json.loads(line) for line in out.read_text().splitlines()]
        self.assertEqual(len(found), 32)  # it tried, in every game
        self.assertTrue(all(f["recovered"] is None for f in found), found)

    def test_public_runs_repeat_and_private_streams_follow_the_key(self):
        d = deal_at(4, 1_000_004)
        self.assertEqual(stream(play_recorded(d, runkey.PUBLIC_RUN_KEY)), stream(play_recorded(d, runkey.PUBLIC_RUN_KEY)))
        k1, k2 = runkey.new_run_key(), runkey.new_run_key()
        self.assertNotEqual(k1, k2)
        a, b = stream(play_recorded(d, k1)), stream(play_recorded(d, k2))
        self.assertNotEqual({x[0] for x in a}, {x[0] for x in b})
        self.assertNotEqual([x[2] for x in a], [x[2] for x in b])
        self.assertEqual(stream(play_recorded(d, k1)), a)  # one key is still one stream
        self.assertNotEqual([x[2] for x in a], [x[2] for x in stream(play_recorded(d, runkey.PUBLIC_RUN_KEY))])

    def test_a_public_run_scores_the_same_twice_and_a_private_one_follows_its_key(self):
        def rows(res_dir, **kw):
            r = bench.score(TABLE, "ref:random", meta("ref:random"), deals=4, skip_fairplay=True, quiet=True,
                            results_dir=res_dir, **kw)
            with gzip.open(str(res_dir / r["log"]), "rt") as f:
                f.readline()
                return r, [json.loads(line) for line in f]

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp))
        r1, a = rows(tmp / "a")
        r2, b = rows(tmp / "b")
        self.assertEqual(a, b)
        self.assertEqual(r1["headline"], r2["headline"])
        deck = tmp / "deck.json"
        deck.write_text(json.dumps({"seeds": [5_000_000_000 + 7919 * i for i in range(4)]}))
        _, p1 = rows(tmp / "c", private_seeds=str(deck), run_key=b"\x01" * 32)
        _, p2 = rows(tmp / "d", private_seeds=str(deck), run_key=b"\x01" * 32)
        _, p3 = rows(tmp / "e", private_seeds=str(deck), run_key=b"\x02" * 32)
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)  # ref:random draws from rng_seed, so another key plays other games

    def test_game_ids_name_no_deal_arrangement_or_check(self):
        ids = set()
        for index in range(6):
            for arr in range(4):
                gid = runkey.game_id(runkey.PUBLIC_RUN_KEY, TABLE.id, index, arr)
                self.assertRegex(gid, HEX_ID)
                for word in ("fairplay", TABLE.id, "hk", "/d", "/a"):
                    self.assertNotIn(word, gid)
                ids.add(gid)
        self.assertEqual(len(ids), 24)
        self.assertNotIn(runkey.game_id(runkey.PUBLIC_RUN_KEY, TABLE.id, 0, runkey.FAIRPLAY_ARRANGEMENT), ids)

    def test_the_fair_play_check_is_sent_what_a_real_game_sends(self):
        seen = []
        key = runkey.new_run_key()
        rep = fairplay.check(TABLE, "ref:ukeire", points=12, run_key=key,
                             on_decision=lambda s, a, m: seen.append(m))
        self.assertTrue(rep["passed"], rep)
        self.assertTrue(seen)
        for m in seen:
            self.assertRegex(m["game_id"], HEX_ID)
            self.assertLess(m["rng_seed"], 2 ** 31)
        # the same keyed scheme, so the stream moves with the key like a real game's
        other = []
        fairplay.check(TABLE, "ref:ukeire", points=12, run_key=runkey.new_run_key(),
                       on_decision=lambda s, a, m: other.append(m))
        self.assertNotEqual([m["rng_seed"] for m in seen[:5]], [m["rng_seed"] for m in other[:5]])

    def test_every_fair_play_ask_runs_in_a_new_process_after_the_games_so_far(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp))
        out = tmp / "probe.jsonl"
        rep = fairplay.check(TABLE, "%s %s" % (PY, ROOT / "tests" / "env_probe_bot.py"), points=6,
                             bot_env={"PROBE_OUT": str(out)})
        self.assertTrue(rep["passed"], rep)
        rows = [json.loads(line) for line in out.read_text().splitlines()]
        born = {}
        for r in rows:
            born.setdefault(r["born"], []).append(r["seq"])
        self.assertGreaterEqual(len(born), 2 * rep["points"])  # at least one process per re-asked position
        for seqs in born.values():
            self.assertEqual(seqs, sorted(seqs))
            self.assertEqual(len(set(seqs)), len(seqs))  # no process is shown a position twice


class FairPlayDeals(unittest.TestCase):
    def test_deals_come_from_a_secret_and_not_from_any_known_range(self):
        ranges = fairplay.public_ranges(TABLE.dir.parent)
        a, b = os.urandom(32), os.urandom(32)
        sa = [fairplay.check_deal_seed(a, i, ranges) for i in range(20)]
        sb = [fairplay.check_deal_seed(b, i, ranges) for i in range(20)]
        self.assertEqual(sa, [fairplay.check_deal_seed(a, i, ranges) for i in range(20)])
        self.assertNotEqual(sa, sb)
        self.assertEqual(len(set(sa)), 20)
        for seed in sa + sb:
            self.assertTrue(0 <= seed < 2 ** 64)
            self.assertFalse(any(lo <= seed < hi for lo, hi in ranges))
            self.assertFalse(8_000_000_000 <= seed < 8_000_000_100)  # the old fixed range
        # a draw that lands in a public range is drawn again
        first = fairplay.check_deal_seed(a, 0, [])
        self.assertNotEqual(fairplay.check_deal_seed(a, 0, [(first, first + 1)]), first)

    def test_two_checks_open_on_different_deals_unless_asked_to_repeat(self):
        def openings(**kw):
            seen = []
            fairplay.check(TABLE, "ref:ukeire", points=3, on_decision=lambda s, a, m: seen.append(m["you"]["hand"]), **kw)
            return seen[:3]

        self.assertNotEqual(openings(), openings())
        self.assertEqual(openings(check_secret=fairplay.DEBUG_CHECK_SECRET),
                         openings(check_secret=fairplay.DEBUG_CHECK_SECRET))


class ReplayFollowsTheBot(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp))
        self.out = self.tmp / "probe.jsonl"

    def test_a_bot_that_plays_its_own_moves_never_sees_an_impossible_game(self):
        # Its moves are not the reference bots'. In the check's games and in every replay, the next message
        # must show its own discard on the table.
        rep = fairplay.check(TABLE, "%s %s" % (PY, ROOT / "tests" / "consistency_bot.py"), points=15,
                             bot_env={"PROBE_OUT": str(self.out)})
        seen = self.out.read_text().splitlines() if self.out.exists() else []
        self.assertEqual(seen, [])
        self.assertTrue(rep["passed"], rep)
        self.assertGreaterEqual(rep["asks"], 15 * 3)

    def test_a_bot_that_answers_the_replay_differently_is_not_passed(self):
        rep = fairplay.check(TABLE, "%s %s" % (PY, ROOT / "tests" / "identity_bot.py"), points=15)
        self.assertFalse(rep["passed"])
        self.assertGreater(rep["decision_changes"], 0)


class FreshProcesses(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp))
        self.out = self.tmp / "probe.jsonl"
        self.config = {"table": TABLE.id, "tables_dir": str(TABLE.dir.parent),
                       "players": {"bot": "%s %s" % (PY, ROOT / "tests" / "env_probe_bot.py"),
                                   "f0": "ref:ukeire", "f1": "ref:faan_aware", "f2": "ref:deficiency"},
                       "bot_env": {"PROBE_OUT": str(self.out)}}

    def run_games(self, workers):
        deals = [deal_at(i, 1_000_000 + i) for i in range(3)]
        env = {"HKBENCH_PRIVATE_SEEDS": "/secret/deck.json", "HKBENCH_ANYTHING": "x", "SENTINEL_NOT_ALLOWED": "y"}
        with mock.patch.dict(os.environ, env):
            recs = pool.run_specs(self.config, bench.duplicate_specs(deals), workers=workers)
        rows = [json.loads(line) for line in self.out.read_text().splitlines()]
        return recs, rows

    def check(self, recs, rows):
        self.assertEqual(len(recs), 12)
        by_game = {}
        for r in rows:
            by_game.setdefault(r["game_id"], []).append(r)
        self.assertEqual(len(by_game), 12)
        for r in rows:
            self.assertFalse([k for k in r["env"] if k.upper().startswith("HKBENCH")], r["env"])
            self.assertNotIn("SENTINEL_NOT_ALLOWED", r["env"])
            self.assertEqual(r["values"], [])
            self.assertIn("PROBE_OUT", r["env"])  # what the run explicitly handed over
            self.assertIn("PATH", r["env"])
        # one process per game, never carried to the next
        born = [{r["born"] for r in g} for g in by_game.values()]
        self.assertTrue(all(len(b) == 1 for b in born))
        self.assertEqual(len({next(iter(b)) for b in born}), 12)
        self.assertEqual(len({g[0]["pid"] for g in by_game.values()}), 12)

    def test_each_game_gets_a_new_process_with_none_of_the_benchs_environment(self):
        self.check(*self.run_games(workers=1))

    def test_the_same_holds_across_workers(self):
        self.check(*self.run_games(workers=2))

    def test_two_seats_of_one_bot_get_two_processes(self):
        config = dict(self.config, players={"A": self.config["players"]["bot"], "B": "ref:ukeire"})
        d = deal_at(0, 1_000_000)
        pool.run_specs(config, [{"deal": list(d), "arrangement": 0, "seats": ["A", "B", "A", "B"]}], workers=1)
        rows = [json.loads(line) for line in self.out.read_text().splitlines()]
        self.assertEqual(len({r["born"] for r in rows}), 2)

    def test_the_environment_is_an_allowlist(self):
        src = {"PATH": "/bin", "HOME": "/h", "LANG": "C", "LC_ALL": "C", "TMPDIR": "/t", "SYSTEMROOT": "C:\\W",
               "HKBENCH_PRIVATE_SEEDS": "/x", "AWS_SECRET_ACCESS_KEY": "s", "PYTHONPATH": "/p"}
        self.assertEqual(set(bot_environment(src)), {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT"})
        env = bot_environment(src, scratch="/scratch")
        self.assertEqual({env[k] for k in ("HOME", "TMPDIR", "TEMP", "TMP")}, {"/scratch"})
        self.assertEqual(bot_environment(src, {"MODEL_DIR": "/m"})["MODEL_DIR"], "/m")
        with self.assertRaises(ValueError):
            bot_environment(src, {"HKBENCH_PRIVATE_SEEDS": "/x"})

    def test_a_bot_that_crashes_on_start_still_stops_the_run(self):
        config = dict(self.config, players={"bot": "%s -c 'import sys; sys.exit(3)'" % PY, "f0": "ref:ukeire",
                                            "f1": "ref:ukeire", "f2": "ref:ukeire"})
        from hkbench.players import BotCrashed
        with self.assertRaises(BotCrashed):
            pool.run_specs(config, bench.duplicate_specs([deal_at(0, 1_000_000)]), workers=1)


class Isolation(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp))
        self.out = self.tmp / "probe.jsonl"

    def games(self, players, specs):
        config = {"table": TABLE.id, "tables_dir": str(TABLE.dir.parent), "players": players,
                  "bot_env": {"PROBE_OUT": str(self.out)}}
        pool.run_specs(config, specs, workers=1)
        return [json.loads(line) for line in self.out.read_text().splitlines()]

    def test_a_file_written_in_one_game_is_not_there_in_the_next_or_at_the_other_seat(self):
        d0, d1 = deal_at(0, 1_000_000), deal_at(1, 1_000_001)
        probe = "%s %s" % (PY, ROOT / "tests" / "scratch_probe_bot.py")
        # duplicate scoring: the bot in every seat of one wall, one game after another; head to head: two seats of one bot
        self.games({"bot": probe, "f0": "ref:ukeire", "f1": "ref:ukeire", "f2": "ref:ukeire"},
                   bench.duplicate_specs([d0, d1]))
        rows = self.games({"A": probe, "B": "ref:ukeire"},  # all rows so far: the file is shared
                          [{"deal": list(d0), "arrangement": 0, "seats": ["A", "B", "A", "B"]}])
        self.assertEqual(len(rows), 8 + 2)
        for r in rows:
            self.assertEqual(r["found"], [], r)
            self.assertEqual(len({os.path.realpath(v) for v in r["places"].values()}), 1)  # one directory is cwd, HOME and the temp directory
        dirs = [r["places"]["home"] for r in rows]
        self.assertEqual(len(set(dirs)), len(dirs))
        self.assertFalse([d for d in dirs if os.path.exists(d)])  # and each is gone when its process is

    def test_an_explicit_working_directory_is_kept_but_home_and_temp_are_still_new(self):
        out_dir = self.tmp / "program"
        out_dir.mkdir()
        p = ProcessPlayer("%s %s" % (PY, ROOT / "tests" / "scratch_probe_bot.py"), TABLE.id, cwd=str(out_dir),
                          env={"PROBE_OUT": str(self.out)})
        d = deal_at(0, 1_000_000)
        try:
            play_game(TABLE.id, PROFILE, d, [p] + [make_player("ref:ukeire", TABLE.id, PROFILE) for _ in range(3)],
                      arrangement=0)
        finally:
            p.close()
        row = json.loads(self.out.read_text().splitlines()[0])
        self.assertEqual(os.path.realpath(row["places"]["cwd"]), os.path.realpath(str(out_dir)))
        self.assertNotEqual(row["places"]["home"], row["places"]["cwd"])

    def start_with_descendant(self, exits_on_bye):
        script = self.tmp / "parent.py"
        pidfile = self.tmp / "descendant.pid"
        script.write_text(textwrap.dedent("""
            import json, subprocess, sys, time
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
            open(%r, "w").write(str(child.pid))
            for line in sys.stdin:
                m = json.loads(line)
                if m["type"] == "hello":
                    print(json.dumps({"type": "ready"}), flush=True)
                elif m["type"] == "bye":
                    if %r:
                        break
                    time.sleep(60)
        """ % (str(pidfile), exits_on_bye)))
        player = ProcessPlayer("%s %s" % (PY, script), TABLE.id)
        return player, int(pidfile.read_text())

    @staticmethod
    def alive(pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True

    def test_closing_a_bot_stops_the_descendants_it_left_holding_the_pipes(self):
        for exits in (True, False):
            with self.subTest(exits_on_bye=exits):
                player, descendant = self.start_with_descendant(exits)
                self.assertTrue(self.alive(descendant))
                t0 = time.monotonic()
                player.close()
                took = time.monotonic() - t0
                self.assertLess(took, BYE_GRACE_S + 1.5)
                if exits:
                    self.assertLess(took, 1.0)
                for _ in range(40):
                    if not self.alive(descendant):
                        break
                    time.sleep(0.05)
                self.assertFalse(self.alive(descendant))


class KeyStaysPut(unittest.TestCase):
    def test_the_key_is_in_no_result_and_no_log(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp))
        deck = tmp / "deck.json"
        deck.write_text(json.dumps({"seeds": [5_000_000_000 + 7919 * i for i in range(4)]}))
        key = runkey.new_run_key()
        forms = [key.hex().encode(), key.hex().upper().encode(), base64.b64encode(key), base64.urlsafe_b64encode(key),
                 repr(key).encode(), key]
        r = bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=4, private_seeds=str(deck), results_dir=tmp,
                        fairplay_points=10, quiet=True, run_key=key, argv=["score", "--private-seeds", str(deck)])
        self.assertEqual(r["rng_scheme"], "hmac-sha256-v2")
        self.assertEqual(r["verification"], "verified")
        raw = (tmp / (r["run_id"] + ".json")).read_bytes()
        gz = (tmp / r["log"]).read_bytes()
        text = gzip.decompress(gz)
        self.assertEqual(json.loads(text.splitlines()[0])["header"]["rng_scheme"], "hmac-sha256-v2")
        for form in forms:
            for blob in (raw, gz, text):
                self.assertNotIn(form, blob)
        # and the environment of this process, where a child would look, never held it
        self.assertFalse([k for k, v in os.environ.items() if key.hex() in v])

    def test_a_private_run_draws_its_own_key_and_a_public_one_uses_the_public_key(self):
        keys = []
        real = runkey.new_run_key

        def spy():
            keys.append(real())
            return keys[-1]

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp))
        deck = tmp / "deck.json"
        deck.write_text(json.dumps({"seeds": [5_000_000_000 + 7919 * i for i in range(4)]}))
        with mock.patch.object(runkey, "new_run_key", spy):
            bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=1, private_seeds=str(deck), write=False,
                        skip_fairplay=True, quiet=True, results_dir=tmp)
            bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=1, private_seeds=str(deck), write=False,
                        skip_fairplay=True, quiet=True, results_dir=tmp)
            bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=1, write=False, skip_fairplay=True, quiet=True,
                        results_dir=tmp)
        self.assertEqual(len(keys), 2)  # one per private run, none for the public one
        self.assertNotEqual(keys[0], keys[1])
        self.assertEqual(len(keys[0]), 32)
        self.assertEqual(runkey.PUBLIC_RUN_KEY.hex(),
                         __import__("hashlib").sha256(b"hkbench-public-rng-v2").hexdigest())

    def test_old_results_read_as_the_old_scheme(self):
        self.assertEqual(runkey.scheme_of({"schema": "hkbench-result-1"}), "splitmix-v1")
        self.assertEqual(runkey.scheme_of({"rng_scheme": "hmac-sha256-v2"}), "hmac-sha256-v2")


def load_script():
    spec = importlib.util.spec_from_file_location("make_private_deck", str(ROOT / "scripts" / "make_private_deck.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class PrivateDeckGenerator(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp))
        self.mod = load_script()

    def test_it_writes_independent_seeds_in_a_private_file(self):
        out = self.tmp / "deck.json"
        self.assertEqual(self.mod.main(["--count", "200", "--out", str(out)]), 0)
        self.assertEqual(stat.S_IMODE(out.stat().st_mode), 0o600)
        obj = json.loads(out.read_text())
        self.assertEqual(set(obj), {"seeds"})  # no start, no count
        seeds = obj["seeds"]
        self.assertEqual(len(seeds), 200)
        self.assertEqual(len(set(seeds)), 200)
        self.assertTrue(all(0 <= s < 2 ** 64 for s in seeds))
        self.assertTrue(any(s >= 2 ** 40 for s in seeds))
        self.assertFalse(any(b - a == 1 for a, b in zip(seeds, seeds[1:])))
        for lo, hi in [(t.public_range["start"], t.public_range["start"] + t.public_range["count"]) for t in list_tables()]:
            self.assertFalse(any(lo <= s < hi for s in seeds))
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.assertEqual(load_private_seeds(str(out)), seeds)  # the bench reads it without complaint

    def test_it_will_not_overwrite(self):
        out = self.tmp / "deck.json"
        out.write_text("keep me")
        self.assertEqual(self.mod.main(["--count", "5", "--out", str(out)]), 2)
        self.assertEqual(out.read_text(), "keep me")

    def test_it_refuses_a_seed_inside_any_public_range(self):
        lo = TABLE.public_range["start"]
        draws = iter([lo, lo + 5, 2_000_001, 3_099_999, 4_000_000_000, 4_000_000_001])
        with mock.patch.object(self.mod.secrets, "randbits", lambda _n: next(draws)):
            seeds = self.mod.make_seeds(2, self.mod.public_ranges())
        self.assertEqual(sorted(seeds), [4_000_000_000, 4_000_000_001])

    def test_a_seed_outside_64_bits_is_never_written(self):
        draws = iter([2 ** 64 + 5, -3, 4_000_000_000])
        with mock.patch.object(self.mod.secrets, "randbits", lambda _n: next(draws)):
            self.assertEqual(self.mod.make_seeds(1, self.mod.public_ranges()), [4_000_000_000])

    def test_the_loader_refuses_seeds_that_are_not_64_bit_unsigned(self):
        lo = TABLE.public_range["start"]
        for bad in (lo + 2 ** 64, -1, 2 ** 64, 2 ** 70):
            for form, text in (("seeds", json.dumps({"seeds": [7, bad]})), ("list", json.dumps([7, bad])),
                               ("lines", "7\n%d\n" % bad)):
                path = self.tmp / ("d_%s_%d.txt" % (form, abs(bad) % 1000))
                path.write_text(text)
                with self.subTest(form=form, seed=bad):
                    with self.assertRaises(ValueError):
                        load_private_seeds(str(path))
                    with self.assertRaises(ValueError):
                        TABLE.private_deals(str(path), 1)
        self.assertEqual(check_seed(2 ** 64 - 1), 2 ** 64 - 1)
        for odd in (True, 1.5, None):
            with self.assertRaises(ValueError):
                check_seed(odd)
        # the alias really was a public wall, which is why it matters
        from hkbench.seeds import wall_for_seed
        self.assertEqual(wall_for_seed(lo + 2 ** 64), wall_for_seed(lo))

    def test_the_decks_path_is_hidden_in_every_spelling(self):
        path = str(self.tmp / "secret" / "deck.json")
        for argv in (["score", "--private-seeds", path], ["score", "--private-seeds=" + path],
                     ["score", "--note", "from " + path + " today"]):
            cmd = bench.reproduce_command(argv, path)
            self.assertNotIn(path, cmd)
            self.assertNotIn("deck.json", cmd)
            self.assertIn("<private deck>", cmd)
        rel = os.path.relpath(path)
        self.assertNotIn("deck.json", bench.reproduce_command(["score", "--private-seeds=" + rel], rel))
        self.assertNotIn("deck.json", bench.reproduce_command(["score", "--private-seeds=" + os.path.abspath(rel)], rel))
        self.assertEqual(bench.reproduce_command(["score", "--deals", "5"], None), "hkbench score --deals 5")

    def test_the_deck_runs_a_private_score(self):
        out = self.tmp / "deck.json"
        self.mod.main(["--count", "6", "--out", str(out)])
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            r = bench.score(TABLE, "ref:ukeire", meta("ref:ukeire"), deals=2, private_seeds=str(out), write=False,
                            skip_fairplay=True, quiet=True, results_dir=self.tmp)
        self.assertEqual(r["seeds"]["tag"], "private")


if __name__ == "__main__":
    unittest.main()
