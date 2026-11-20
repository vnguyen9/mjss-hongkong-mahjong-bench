"""Scoring a bot: duplicate play against the frozen field, and head-to-head matches."""

from __future__ import annotations

import datetime
import gzip
import hashlib
import json
import os
import platform
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from hkbench import __version__, fairplay, fingerprint, stats
from hkbench.agents.registry import REFERENCE_BOTS
from hkbench.pool import run_specs, stderr_progress
from hkbench.tables import Deal, Table, reference_bot_hash, sha256_file

RESULT_SCHEMA = "hkbench-result-1"
H2H_SCHEMA = "hkbench-h2h-1"
SEAT_PAIRS: Tuple[Tuple[int, int], ...] = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
TRACKS = ("bots", "llms", "humans")


class Rejected(RuntimeError):
    """The bot was not scored: it failed the fair-play check or broke the protocol too often."""


# --- bot identity -----------------------------------------------------------------------------


def bot_hash(spec: str, cwd: Optional[str] = None, hash_dir: Optional[str] = None) -> str:
    """A fingerprint of what is being scored.

    A reference bot: the pinned hash of its source. A command: the command line plus the bytes of
    every argument that is an existing file (so ``python my_bot.py`` hashes ``my_bot.py``), plus
    every file under ``hash_dir`` if given. A hosted bot supplies its own hash instead.
    """
    if spec.startswith("ref:"):
        return reference_bot_hash(spec[4:])
    base = Path(cwd) if cwd else Path.cwd()
    parts = ["command:" + spec]
    paths: List[Path] = []
    for tok in shlex.split(spec):
        p = (base / tok)
        if p.is_file():
            paths.append(p)
    if hash_dir:
        for root, _dirs, files in os.walk(hash_dir):
            for f in files:
                paths.append(Path(root) / f)
    for p in sorted(set(paths)):
        parts.append("%s:%s" % (p.name, sha256_file(p)))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def bot_meta(spec: str, *, name: Optional[str], track: str, kind: Optional[str], trained_on: Optional[str],
             description: Optional[str], cwd: Optional[str], hash_dir: Optional[str],
             hash_override: Optional[str]) -> Dict[str, Any]:
    is_ref = spec.startswith("ref:")
    if track not in TRACKS:
        raise ValueError("track must be one of %s" % ", ".join(TRACKS))
    return {
        "name": name or (spec[4:] if is_ref else Path(shlex.split(spec)[-1]).stem),
        "track": track,
        "kind": kind or ("reference" if is_ref else "external"),
        "sha256": hash_override or bot_hash(spec, cwd, hash_dir),
        "trained_on": trained_on or ("none (scripted)" if is_ref else "unknown"),
        "description": description or "",
    }


# --- shared pieces ----------------------------------------------------------------------------


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z"


def engine_info(table: Table, fp: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "hkbench_version": __version__,
        "python": platform.python_version(),
        "rules_sha256": fp["rules_sha256"],
        "fingerprint_sha256": fp["sha256"],
        "fingerprint_deals": fp["deals"],
    }


def reproduce_command(argv: Sequence[str], private_seeds: Optional[str]) -> str:
    """The command line that made a run, with the private deck and the home directory scrubbed."""
    home = str(Path.home())
    args = []
    for a in argv:
        if private_seeds and a == private_seeds:
            a = "<private deck>"
        else:
            a = a.replace(home, "~")
        args.append(a)
    return " ".join(shlex.quote(a) for a in ["hkbench"] + args)


def _deck(table: Table, deals: int, offset: int, private_seeds: Optional[str]) -> Tuple[str, List[Deal]]:
    if private_seeds:
        return "private", table.private_deals(private_seeds, deals, offset)
    return "public", table.public_deals(deals, offset)


#: What ``--training-log`` adds to the record of a won game (``runner.winning_hand``).
TRAINING_FIELDS = ("melds", "concealed", "winning_tile", "flowers", "winner_draws")


def write_log(path: Path, header: Dict[str, Any], records: Sequence[Dict[str, Any]], tag: str) -> None:
    """One gzip JSON-lines file: a header, then one line per game.

    Public-deck logs carry the seed and the full action list, so any game can be replayed with
    ``hkbench verify-log``. Private-deck logs carry only the outcome of each game, by deal index.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(str(path), "wb", mtime=0) as gz:
        gz.write((json.dumps({"header": header}, sort_keys=True) + "\n").encode("utf-8"))
        for r in records:
            row = dict(r)
            if tag == "private":
                row.pop("seed", None)
                row.pop("actions", None)
                for field in TRAINING_FIELDS:  # never on a private deck: a hand names the deal
                    row.pop(field, None)
            gz.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))


def _fault_check(table: Table, decisions: int, faults: Dict[str, int]) -> Dict[str, Any]:
    total = sum(faults.values())
    per_1000 = 1000.0 * total / decisions if decisions else 0.0
    return {"decisions": decisions, "faults": faults, "per_1000_decisions": per_1000,
            "limit_per_1000": table.fault_limit_per_1000, "ok": per_1000 <= table.fault_limit_per_1000}


def check_before_scoring(table: Table, spec: str, *, skip_fairplay: bool, fairplay_points: int,
                         cwd: Optional[str], decision_timeout_s: Optional[float]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """The gate every score or match passes first: field pins, engine fingerprint, fair play."""
    table.require_active()
    table.verify_field()
    fp = fingerprint.verify(table)
    if skip_fairplay:
        return fp, {"status": "skipped"}
    rep = fairplay.check(table, spec, points=fairplay_points, cwd=cwd, decision_timeout_s=decision_timeout_s)
    rep["status"] = "passed" if rep["passed"] else "failed"
    if not rep["passed"]:
        raise Rejected("fair-play check failed for %s: %s" % (spec, json.dumps(rep, sort_keys=True)))
    return fp, rep


# --- duplicate scoring ------------------------------------------------------------------------


def duplicate_specs(deals: Sequence[Deal]) -> List[Dict[str, Any]]:
    """Four games per deal: the bot takes each seat once, the field fills the rest in order."""
    specs = []
    for d in deals:
        for rot in range(4):
            seats = [None] * 4
            seats[rot] = "bot"
            for i in range(3):
                seats[(rot + 1 + i) % 4] = "f%d" % i
            specs.append({"deal": [d.index, d.seed, d.dealer, d.prevailing_wind], "arrangement": rot, "seats": seats})
    return specs


def score(
    table: Table,
    spec: str,
    meta: Dict[str, Any],
    *,
    deals: int,
    offset: int = 0,
    private_seeds: Optional[str] = None,
    workers: int = 1,
    results_dir: Path,
    argv: Sequence[str] = (),
    skip_fairplay: bool = False,
    fairplay_points: int = fairplay.DEFAULT_POINTS,
    cwd: Optional[str] = None,
    decision_timeout_s: Optional[float] = None,
    write: bool = True,
    quiet: bool = False,
    training_log: bool = False,
) -> Dict[str, Any]:
    tag, deck = _deck(table, deals, offset, private_seeds)
    training_log = training_log and tag == "public"  # a private deck's log stays outcome-only
    fp, fair = check_before_scoring(table, spec, skip_fairplay=skip_fairplay, fairplay_points=fairplay_points,
                                    cwd=cwd, decision_timeout_s=decision_timeout_s)
    players = {"bot": spec}
    for i, member in enumerate(table.field):
        players["f%d" % i] = "ref:" + member["bot"]
    config = {"table": table.id, "tables_dir": str(table.dir.parent), "players": players,
              "decision_timeout_s": decision_timeout_s or table.decision_timeout_s, "cwd": cwd,
              "record_actions": True}
    if training_log:
        config["training_log"] = True
    records = run_specs(config, duplicate_specs(deck), workers,
                        None if quiet else stderr_progress("score %s" % meta["name"]))
    cap = table.profile.faan_cap
    summary = stats.duplicate_summary(records, cap)
    faults = _fault_check(table, summary["decisions"], summary["faults"])
    verified = tag == "private" and fair.get("status") == "passed" and faults["ok"]
    if not faults["ok"]:
        raise Rejected("%s made %.2f faults per 1000 decisions (limit %.2f): %s"
                       % (meta["name"], faults["per_1000_decisions"], faults["limit_per_1000"], faults["faults"]))
    created = _now()
    run_id = "%s__%s__%s__%s" % (table.id, _slug(meta["name"]), tag, created.replace(":", "").replace("-", "")[:15])
    result = {
        "schema": RESULT_SCHEMA,
        "run_id": run_id,
        "kind": "duplicate",
        "created_utc": created,
        "table": {
            "id": table.id,
            "rules_track": table.rules_track,
            "rules_sha256": fp["rules_sha256"],
            "field": [{"bot": m["bot"], "sha256": m["sha256"]} for m in table.field],
        },
        "bot": meta,
        "seeds": {"tag": tag, "deals": len(deck), "offset": offset,
                  "public_range": table.public_range if tag == "public" else None},
        "verification": "verified" if verified else "unverified",
        "fairplay": {k: fair[k] for k in ("status", "points", "reshuffles", "asks", "view_mismatches",
                                          "decision_changes", "faults") if k in fair},
        "headline": {
            "metric": "points per hand against the frozen field",
            "points_per_hand": summary["points_per_hand"]["mean"],
            "se": summary["points_per_hand"]["se"],
            "ci95": summary["points_per_hand"]["ci95"],
            "deals": summary["deals"],
            "games": summary["games"],
        },
        "stats": {k: summary[k] for k in ("win_rate", "deal_in_rate", "self_draw_win_rate", "draw_rate",
                                          "limit_hand_rate", "wins", "limit_hands", "average_win_points",
                                          "average_win_faan")},
        "faults": faults,
        "command": reproduce_command(argv, private_seeds),
        "engine": engine_info(table, fp),
        "log": "logs/%s.jsonl.gz" % run_id,
    }
    if training_log:
        result["training_log"] = True
    if write:
        results_dir.mkdir(parents=True, exist_ok=True)
        write_log(results_dir / result["log"], {"run_id": run_id, "table": table.id, "bot": meta,
                                                "seed_tag": tag, "command": result["command"],
                                                "engine": result["engine"]}, records, tag)
        (results_dir / (run_id + ".json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                                      encoding="utf-8")
    return result


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "-" for c in name).strip("-") or "bot"


# --- head to head -----------------------------------------------------------------------------


def h2h_specs(deals: Sequence[Deal]) -> List[Dict[str, Any]]:
    """Six games per deal: every way to seat bot A on two of the four seats and bot B on the other two."""
    specs = []
    for d in deals:
        for arrangement, pair in enumerate(SEAT_PAIRS):
            seats = ["A" if s in pair else "B" for s in range(4)]
            # A pair and its complement are the same game with the teams swapped: same random numbers.
            specs.append({"deal": [d.index, d.seed, d.dealer, d.prevailing_wind], "arrangement": arrangement,
                          "seed_key": min(arrangement, 5 - arrangement), "seats": seats})
    return specs


def _team_points(record: Dict[str, Any], team: str) -> float:
    return float(sum(p for p, k in zip(record["payments"], record["seats"]) if k == team))


def h2h(
    table: Table,
    bots: Sequence[Tuple[str, str, Dict[str, Any]]],
    *,
    deals: int,
    offset: int = 0,
    private_seeds: Optional[str] = None,
    workers: int = 1,
    results_dir: Path,
    argv: Sequence[str] = (),
    skip_fairplay: bool = False,
    fairplay_points: int = fairplay.DEFAULT_POINTS,
    cwd: Optional[str] = None,
    decision_timeout_s: Optional[float] = None,
    resamples: int = 500,
    write: bool = True,
    quiet: bool = False,
    training_log: bool = False,
) -> Dict[str, Any]:
    """Round robin. ``bots`` is a list of (display name, spec, meta)."""
    if len(bots) < 2:
        raise ValueError("a head-to-head needs at least two bots")
    names = [b[0] for b in bots]
    if len(set(names)) != len(names):
        raise ValueError("bot names must be different")
    tag, deck = _deck(table, deals, offset, private_seeds)
    training_log = training_log and tag == "public"  # a private deck's log stays outcome-only
    fps = None
    fair_status = {}
    for name, spec, _meta in bots:
        fps, fair = check_before_scoring(table, spec, skip_fairplay=skip_fairplay, fairplay_points=fairplay_points,
                                         cwd=cwd, decision_timeout_s=decision_timeout_s)
        fair_status[name] = fair.get("status")
    assert fps is not None
    pairs: List[Dict[str, Any]] = []
    pair_deals: Dict[Tuple[str, str], List[Tuple[float, float]]] = {}
    all_records: List[Dict[str, Any]] = []
    decisions = {n: 0 for n in names}
    fault_counts: Dict[str, Dict[str, int]] = {n: {} for n in names}
    for i in range(len(bots)):
        for j in range(i + 1, len(bots)):
            a_name, a_spec, _ = bots[i]
            b_name, b_spec, _ = bots[j]
            config = {"table": table.id, "tables_dir": str(table.dir.parent),
                      "players": {"A": a_spec, "B": b_spec},
                      "decision_timeout_s": decision_timeout_s or table.decision_timeout_s, "cwd": cwd,
                      "record_actions": True}
            if training_log:
                config["training_log"] = True
            recs = run_specs(config, h2h_specs(deck), workers,
                             None if quiet else stderr_progress("%s vs %s" % (a_name, b_name)))
            for r in recs:
                r["pair"] = [a_name, b_name]
                for seat, key in enumerate(r["seats"]):
                    nm = a_name if key == "A" else b_name
                    decisions[nm] += r["decisions"][seat]
                    for k, n in r["faults"][seat].items():
                        fault_counts[nm][k] = fault_counts[nm].get(k, 0) + n
            all_records.extend(recs)
            team = stats.per_deal(recs, lambda r: _team_points(r, "A") / 2.0)
            by_deal: Dict[int, List[float]] = {}
            for r in recs:
                by_deal.setdefault(r["deal"], []).append(stats.team_outcome(_team_points(r, "A")))
            pair_deals[(a_name, b_name)] = [(sum(v), float(len(v))) for _, v in sorted(by_deal.items())]
            outcomes = [stats.team_outcome(_team_points(r, "A")) for r in recs]
            pairs.append({
                "a": a_name, "b": b_name, "games": len(recs), "deals": len(deck),
                "a_points_per_hand_per_seat": stats.mean_ci(team),
                "a_game_wins": sum(1 for o in outcomes if o == 1.0),
                "b_game_wins": sum(1 for o in outcomes if o == 0.0),
                "ties": sum(1 for o in outcomes if o == 0.5),
            })
    bt = stats.bootstrap_bt(names, pair_deals, resamples=resamples)
    ranks = stats.shared_ranks(bt)
    faults_ok = {n: _fault_check(table, decisions[n], fault_counts[n]) for n in names}
    bad = [n for n, f in faults_ok.items() if not f["ok"]]
    if bad:
        raise Rejected("too many faults from: %s" % ", ".join(bad))
    verified = tag == "private" and all(s == "passed" for s in fair_status.values())
    created = _now()
    run_id = "%s__h2h__%s__%s" % (table.id, tag, created.replace(":", "").replace("-", "")[:15])
    result = {
        "schema": H2H_SCHEMA,
        "run_id": run_id,
        "kind": "h2h",
        "created_utc": created,
        "table": {"id": table.id, "rules_track": table.rules_track, "rules_sha256": fps["rules_sha256"]},
        "bots": [dict(b[2], display=b[0]) for b in bots],
        "seeds": {"tag": tag, "deals": len(deck), "offset": offset,
                  "public_range": table.public_range if tag == "public" else None},
        "verification": "verified" if verified else "unverified",
        "fairplay": fair_status,
        "pairs": pairs,
        "bradley_terry": {n: dict(bt[n], rank=ranks[n]) for n in names},
        "rank_rule": "rank = 1 + the number of bots whose 95% interval lies entirely above this bot's; overlapping bots share a rank",
        "faults": faults_ok,
        "command": reproduce_command(argv, private_seeds),
        "engine": engine_info(table, fps),
        "log": "logs/%s.jsonl.gz" % run_id,
    }
    if training_log:
        result["training_log"] = True
    if write:
        results_dir.mkdir(parents=True, exist_ok=True)
        write_log(results_dir / result["log"], {"run_id": run_id, "table": table.id, "seed_tag": tag,
                                                "command": result["command"], "engine": result["engine"]},
                  all_records, tag)
        (results_dir / (run_id + ".json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                                      encoding="utf-8")
    return result
