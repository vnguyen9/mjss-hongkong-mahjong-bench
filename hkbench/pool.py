"""Running many games, in this process or in a few worker processes.

A *game spec* says which deal to play and which player sits at each seat::

    {"deal": [index, seed, dealer, prevailing_wind], "arrangement": 2, "seats": ["bot", "f0", "f1", "f2"]}

A *config* says how to build the players the specs name::

    {"table": "hk-hkma-v1", "tables_dir": None, "players": {"bot": "ref:ukeire", "f0": "ref:faan_aware", ...},
     "decision_timeout_s": 10.0, "cwd": None, "record_actions": False}

Every worker builds its own players once and reuses them. Results do not depend on the number
of workers: a game is a pure function of its spec and its players.
"""

from __future__ import annotations

import multiprocessing as mp
import sys
import time
import traceback
from typing import Any, Callable, Dict, List, Optional

from hkbench.players import Player, make_player
from hkbench.runner import play_game
from hkbench.tables import Deal, load_table


class Runtime:
    """The players one process holds."""

    def __init__(self, config: Dict[str, Any]) -> None:
        from pathlib import Path

        self.config = config
        tables_dir = Path(config["tables_dir"]) if config.get("tables_dir") else None
        self.table = load_table(config["table"], tables_dir)
        self.profile = self.table.profile
        self.players: Dict[str, Player] = {}
        try:
            for key, spec in config["players"].items():
                self.players[key] = make_player(
                    spec, self.table.id, self.profile,
                    decision_timeout_s=config.get("decision_timeout_s", self.table.decision_timeout_s),
                    cwd=config.get("cwd"),
                )
        except BaseException:
            self.close()
            raise

    def play(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        index, seed, dealer, wind = spec["deal"]
        seats = spec["seats"]
        rec = play_game(
            self.table.id, self.profile, Deal(index, seed, dealer, wind),
            [self.players[k] for k in seats],
            arrangement=spec["arrangement"],
            seed_key=spec.get("seed_key"),
            record_actions=self.config.get("record_actions", False),
            check_invariants=self.config.get("check_invariants", False),
        )
        rec["seats"] = list(seats)
        return rec

    def close(self) -> None:
        for p in self.players.values():
            try:
                p.close()
            except Exception:
                pass


def _worker_main(config: Dict[str, Any], tasks, results) -> None:
    runtime = None
    try:
        runtime = Runtime(config)
        while True:
            chunk = tasks.get()
            if chunk is None:
                break
            try:
                results.put(("ok", [runtime.play(s) for s in chunk]))
            except BaseException:
                results.put(("err", traceback.format_exc()))
                break
    except BaseException:
        results.put(("err", traceback.format_exc()))
    finally:
        if runtime is not None:
            runtime.close()


def run_specs(
    config: Dict[str, Any],
    specs: List[Dict[str, Any]],
    workers: int = 1,
    progress: Optional[Callable[[int, int], None]] = None,
) -> List[Dict[str, Any]]:
    """Play every spec; return the records in spec order."""
    if workers <= 1 or len(specs) <= 1:
        runtime = Runtime(config)
        try:
            out = []
            for i, s in enumerate(specs):
                out.append(runtime.play(s))
                if progress:
                    progress(i + 1, len(specs))
            return out
        finally:
            runtime.close()

    workers = min(workers, len(specs))
    ctx = mp.get_context("spawn")
    tasks = ctx.Queue()
    results = ctx.Queue()
    size = max(1, min(16, len(specs) // (workers * 6) or 1))
    chunks = [(i, specs[i:i + size]) for i in range(0, len(specs), size)]
    procs = [ctx.Process(target=_worker_main, args=(config, tasks, results)) for _ in range(workers)]
    for p in procs:
        p.start()
    try:
        for _start, chunk in chunks:
            tasks.put(chunk)
        for _ in procs:
            tasks.put(None)
        by_start: Dict[int, List[Dict[str, Any]]] = {}
        done = 0
        order = [start for start, _ in chunks]
        # Results come back in any order; match each to its chunk by the first record's spec.
        lookup = {}
        for start, chunk in chunks:
            lookup[(chunk[0]["deal"][0], chunk[0]["arrangement"], tuple(chunk[0]["seats"]))] = start
        while len(by_start) < len(chunks):
            try:
                kind, payload = results.get(timeout=5.0)
            except Exception:
                if not any(p.is_alive() for p in procs):
                    raise RuntimeError("all workers stopped before finishing")
                continue
            if kind == "err":
                raise RuntimeError("a worker failed:\n" + payload)
            first = payload[0]
            start = lookup[(first["deal"], first["arrangement"], tuple(first["seats"]))]
            by_start[start] = payload
            done += len(payload)
            if progress:
                progress(done, len(specs))
        out = []
        for start in order:
            out.extend(by_start[start])
        return out
    finally:
        for p in procs:
            p.join(timeout=10)
            if p.is_alive():
                p.terminate()


def stderr_progress(label: str) -> Callable[[int, int], None]:
    state = {"t": time.monotonic(), "last": 0}

    def hook(done: int, total: int) -> None:
        now = time.monotonic()
        if done == total or now - state["t"] >= 10:
            state["t"] = now
            print("%s: %d/%d games" % (label, done, total), file=sys.stderr, flush=True)

    return hook
