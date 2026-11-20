"""Command line: ``hkbench score | h2h | fingerprint | fairplay | site | verify-log | tables``."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from hkbench import __version__, bench, fairplay, fingerprint
from hkbench.agents.registry import REFERENCE_BOTS
from hkbench.engine.game import GameState
from hkbench.players import BotCrashed
from hkbench.tables import (PRIVATE_SEEDS_ENV, TablePending, list_tables, load_table, private_seed_path,
                            reference_bot_hash)

DEFAULT_RESULTS = Path(__file__).resolve().parent.parent / "results"
DEFAULT_SITE = Path(__file__).resolve().parent.parent / "site"


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--table", required=True, help="table id, for example hk-hkma-v1")
    p.add_argument("--tables-dir", default=None, help="directory holding the tables (default: ./tables in the repo)")
    p.add_argument("--deals", type=int, default=200, help="number of deals to play (default 200)")
    p.add_argument("--offset", type=int, default=0, help="first deal of the deck to play (default 0)")
    p.add_argument("--private-seeds", default=None,
                   help="path to the private deal deck; or set %s. Without it the public deck is used "
                        "and the run is tagged unverified." % PRIVATE_SEEDS_ENV)
    p.add_argument("--workers", type=int, default=1, help="worker processes (default 1)")
    p.add_argument("--results-dir", default=str(DEFAULT_RESULTS))
    p.add_argument("--skip-fairplay", action="store_true", help="skip the fair-play check (the run is then unverified)")
    p.add_argument("--fairplay-points", type=int, default=fairplay.DEFAULT_POINTS)
    p.add_argument("--timeout", type=float, default=None, help="seconds a bot may take per decision (default: the table's)")
    p.add_argument("--cwd", default=None, help="directory to start the bot in")
    p.add_argument("--no-write", action="store_true", help="print the result without writing files")
    p.add_argument("--training-log", action="store_true",
                   help="also put each won game's melds, concealed tiles, winning tile, flowers and the winner's "
                        "draw count in the log, for training (public deals only; off by default)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="hkbench", description="The Hong Kong Mahjong Bench")
    ap.add_argument("--version", action="version", version="hkbench " + __version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("score", help="score one bot against the frozen field, in duplicate play")
    _common(s)
    s.add_argument("--bot", required=True, help="a command that speaks the protocol, or ref:<name> for an in-repo bot")
    s.add_argument("--name", default=None)
    s.add_argument("--track", default="bots", choices=bench.TRACKS)
    s.add_argument("--kind", default=None, choices=["reference", "external", "hosted"])
    s.add_argument("--trained-on", default=None, help="the rules the bot was trained on (shown on the board)")
    s.add_argument("--description", default=None)
    s.add_argument("--bot-hash", default=None, help="supply the hash yourself (hosted bots, image digests)")
    s.add_argument("--hash-dir", default=None, help="also hash every file under this directory")

    h = sub.add_parser("h2h", help="head to head: two bots, two seats each, every seat pair; Bradley-Terry ranks")
    _common(h)
    h.add_argument("--bot", action="append", required=True, metavar="NAME=COMMAND",
                   help="repeat for each bot; COMMAND may be ref:<name>")
    h.add_argument("--resamples", type=int, default=500, help="bootstrap resamples (default 500)")

    f = sub.add_parser("fingerprint", help="check (or with --write, create) a table's engine fingerprint")
    f.add_argument("--table", required=True)
    f.add_argument("--tables-dir", default=None)
    f.add_argument("--write", action="store_true", help="author a new table: write fingerprint.json")

    fp = sub.add_parser("fairplay", help="run the hidden-tile shuffle check on one bot")
    fp.add_argument("--table", required=True)
    fp.add_argument("--tables-dir", default=None)
    fp.add_argument("--bot", required=True)
    fp.add_argument("--points", type=int, default=fairplay.DEFAULT_POINTS)
    fp.add_argument("--timeout", type=float, default=None)
    fp.add_argument("--cwd", default=None)

    si = sub.add_parser("site", help="build the leaderboard (site/leaderboard.json and index.html) from results/")
    si.add_argument("--results-dir", default=str(DEFAULT_RESULTS))
    si.add_argument("--out", default=str(DEFAULT_SITE))

    v = sub.add_parser("verify-log", help="replay every game in a public-deck log and check its result")
    v.add_argument("log")
    v.add_argument("--tables-dir", default=None)

    t = sub.add_parser("tables", help="list the tables and check the reference field pins")
    t.add_argument("--tables-dir", default=None)
    t.add_argument("--hashes", action="store_true", help="print the current source hash of every reference bot")
    return ap


def _table(args):
    return load_table(args.table, Path(args.tables_dir) if args.tables_dir else None)


def _print_result(result) -> None:
    h = result["headline"]
    lo, hi = h["ci95"] if h["ci95"] else (float("nan"), float("nan"))
    print("%s on %s (%s deck, %s): %+.2f points a hand [%+.2f, %+.2f], %d deals, %d games"
          % (result["bot"]["name"], result["table"]["id"], result["seeds"]["tag"], result["verification"],
             h["points_per_hand"], lo, hi, h["deals"], h["games"]))
    st = result["stats"]
    print("  win %.1f%%  deal-in %.1f%%  average win %.1f points, %.2f faan  limit hands %d"
          % (100 * st["win_rate"]["mean"], 100 * st["deal_in_rate"]["mean"],
             st["average_win_points"] or 0.0, st["average_win_faan"] or 0.0, st["limit_hands"]))


HOSTED_SCRUB = ("--bot", "--cwd", "--hash-dir")


def scrub_hosted(argv: Sequence[str]) -> List[str]:
    """The recorded command for a hosted bot: where its program and files live is not published."""
    out: List[str] = []
    hide_next = False
    for a in argv:
        if hide_next:
            out.append("<hosted>")
            hide_next = False
        elif a in HOSTED_SCRUB:
            out.append(a)
            hide_next = True
        elif any(a.startswith(f + "=") for f in HOSTED_SCRUB):
            out.append(a.split("=", 1)[0] + "=<hosted>")
        else:
            out.append(a)
    return out


def cmd_score(args, argv) -> int:
    table = _table(args)
    priv = private_seed_path(args.private_seeds)
    if args.kind == "hosted":
        argv = scrub_hosted(argv)
    meta = bench.bot_meta(args.bot, name=args.name, track=args.track, kind=args.kind, trained_on=args.trained_on,
                          description=args.description, cwd=args.cwd, hash_dir=args.hash_dir,
                          hash_override=args.bot_hash)
    result = bench.score(table, args.bot, meta, deals=args.deals, offset=args.offset, private_seeds=priv,
                         workers=args.workers, results_dir=Path(args.results_dir), argv=argv,
                         skip_fairplay=args.skip_fairplay, fairplay_points=args.fairplay_points, cwd=args.cwd,
                         decision_timeout_s=args.timeout, write=not args.no_write,
                         training_log=args.training_log)
    _print_result(result)
    if not args.no_write:
        print("wrote %s" % (Path(args.results_dir) / (result["run_id"] + ".json")))
    return 0


def cmd_h2h(args, argv) -> int:
    table = _table(args)
    priv = private_seed_path(args.private_seeds)
    bots = []
    for item in args.bot:
        if "=" not in item:
            raise SystemExit("--bot needs NAME=COMMAND, got %r" % item)
        name, spec = item.split("=", 1)
        meta = bench.bot_meta(spec, name=name, track="bots", kind=None, trained_on=None, description=None,
                              cwd=args.cwd, hash_dir=None, hash_override=None)
        bots.append((name, spec, meta))
    result = bench.h2h(table, bots, deals=args.deals, offset=args.offset, private_seeds=priv, workers=args.workers,
                       results_dir=Path(args.results_dir), argv=argv, skip_fairplay=args.skip_fairplay,
                       fairplay_points=args.fairplay_points, cwd=args.cwd, decision_timeout_s=args.timeout,
                       resamples=args.resamples, write=not args.no_write, training_log=args.training_log)
    print("head to head on %s (%s deck, %s)" % (table.id, result["seeds"]["tag"], result["verification"]))
    for n, r in sorted(result["bradley_terry"].items(), key=lambda kv: -kv[1]["rating"]):
        print("  rank %d  %-20s rating %+7.1f  [%+.1f, %+.1f]" % (r["rank"], n, r["rating"], r["ci95"][0], r["ci95"][1]))
    return 0


def cmd_fingerprint(args) -> int:
    table = _table(args)
    if args.write:
        fp = fingerprint.compute(table.profile)
        table.fingerprint_path.write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("wrote %s: %s" % (table.fingerprint_path, fp["sha256"]))
        return 0
    fp = fingerprint.verify(table)
    print("fingerprint ok for %s: %s (%d deals, %d hands, %d wins)" % (table.id, fp["sha256"][:16], fp["deals"],
                                                                     fp["hands"], fp["wins"]))
    return 0


def cmd_fairplay(args) -> int:
    table = _table(args)
    rep = fairplay.check(table, args.bot, points=args.points, cwd=args.cwd, decision_timeout_s=args.timeout)
    print(json.dumps(rep, indent=2, sort_keys=True))
    return 0 if rep["passed"] else 1


def cmd_site(args) -> int:
    from hkbench import site

    path = site.build(Path(args.results_dir), Path(args.out))
    print("wrote %s" % path)
    return 0


def cmd_verify_log(args) -> int:
    tables_dir = Path(args.tables_dir) if args.tables_dir else None
    bad = 0
    n = 0
    table = None
    with gzip.open(args.log, "rt", encoding="utf-8") as f:
        header = json.loads(f.readline())["header"]
        table = load_table(header["table"], tables_dir)
        profile = table.profile
        for line in f:
            r = json.loads(line)
            if "actions" not in r:
                print("this log has no actions (private deck); nothing to replay")
                return 2
            state = GameState.new_game(profile, seed=r["seed"], dealer=r["dealer"], prevailing_wind=r["prevailing_wind"])
            for actor, action in r["actions"]:
                if state.current_actor() != actor:
                    bad += 1
                    break
                state.apply_action(action)
            else:
                t = state.terminal
                if t is None or list(t.payments) != r["payments"]:
                    bad += 1
            n += 1
    print("%d games replayed, %d mismatches" % (n, bad))
    return 0 if bad == 0 else 1


def cmd_tables(args) -> int:
    if args.hashes:
        for name in sorted(REFERENCE_BOTS):
            print("%-16s %s" % (name, reference_bot_hash(name)))
        return 0
    for t in list_tables(Path(args.tables_dir) if args.tables_dir else None):
        line = "%-14s %-8s %s" % (t.id, t.status, t.rules_track)
        if t.status == "active":
            try:
                t.verify_field()
                line += "  field ok"
            except RuntimeError as exc:
                line += "  FIELD CHANGED: %s" % exc
        else:
            line += "  (%s)" % t.data.get("pending_reason", "")
        print(line)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "score":
            return cmd_score(args, argv)
        if args.cmd == "h2h":
            return cmd_h2h(args, argv)
        if args.cmd == "fingerprint":
            return cmd_fingerprint(args)
        if args.cmd == "fairplay":
            return cmd_fairplay(args)
        if args.cmd == "site":
            return cmd_site(args)
        if args.cmd == "verify-log":
            return cmd_verify_log(args)
        if args.cmd == "tables":
            return cmd_tables(args)
    except (TablePending, bench.Rejected, fingerprint.FingerprintMismatch, BotCrashed, ValueError, RuntimeError) as exc:
        print("hkbench: %s" % exc, file=sys.stderr)
        return 2
    return 0
