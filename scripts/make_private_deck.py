#!/usr/bin/env python3
"""Make a private deal deck: independent random 64-bit seeds, one JSON file.

    python scripts/make_private_deck.py --count 10000 --out /path/outside/the/repo/deck.json

The seeds come from the operating system's random source (``secrets``), so knowing one says nothing
about another. The file is ``{"seeds": [...]}``, mode 0600. The script will not overwrite a file, and
will not write a seed that falls inside any table's public range (a deck that overlaps it is refused by
the bench anyway). Keep the file out of the repository and out of any place a bot can read.
"""

import argparse
import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hkbench.tables import list_tables  # noqa: E402


def public_ranges(tables_dir=None):
    out = []
    for t in list_tables(tables_dir):
        r = t.public_range
        out.append((r["start"], r["start"] + r["count"]))
    return out


def make_seeds(count: int, ranges) -> list:
    seeds = set()
    while len(seeds) < count:
        s = secrets.randbits(64)
        if any(lo <= s < hi for lo, hi in ranges):
            continue
        seeds.add(s)
    out = sorted(seeds)
    secrets.SystemRandom().shuffle(out)  # no order to read the deck's age or origin from
    return out


def write_deck(path: Path, seeds) -> None:
    """Create ``path`` (never replacing one) with mode 0600 and the seeds in it."""
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"seeds": seeds}, f)
        f.write("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Make a private deal deck of independent random seeds.")
    ap.add_argument("--count", type=int, required=True, help="how many deals")
    ap.add_argument("--out", required=True, help="where to write it (must not exist)")
    ap.add_argument("--tables-dir", default=None, help="tables to keep clear of (default: the repo's)")
    args = ap.parse_args(argv)
    if args.count < 1:
        ap.error("--count must be at least 1")
    out = Path(args.out)
    if out.exists():
        print("make_private_deck: %s exists; not overwriting it" % out, file=sys.stderr)
        return 2
    seeds = make_seeds(args.count, public_ranges(Path(args.tables_dir) if args.tables_dir else None))
    try:
        write_deck(out, seeds)
    except FileExistsError:
        print("make_private_deck: %s exists; not overwriting it" % out, file=sys.stderr)
        return 2
    print("wrote %d seeds to %s (mode 0600). Keep it outside the repository." % (len(seeds), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
