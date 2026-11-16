"""Tables: frozen, versioned rule sets with their reference field, deal decks and fingerprint.

A table lives in ``tables/<id>/``:

* ``table.json``       name, rules file, the field of three reference bots (pinned by hash),
                       the public deal range, timeouts, and the engine fingerprint
* ``rules.json``       the rules (faan values, cap, minimum, payments, flowers)
* ``fingerprint.json`` what the engine must reproduce before anything is scored

A table is never edited once released. A change is a new table (``v2``).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, NamedTuple, Optional

from hkbench.agents.registry import BOT_SOURCES
from hkbench.engine.profile import RulesProfile, load_profile
from hkbench.seeds import dealer_for_index, wind_for_index

ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = ROOT / "tables"
PRIVATE_SEEDS_ENV = "HKBENCH_PRIVATE_SEEDS"


class TablePending(RuntimeError):
    """The table is defined but cannot score anything yet."""


class Deal(NamedTuple):
    index: int
    seed: int
    dealer: int
    prevailing_wind: int


def sha256_file(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def hash_sources(paths: Iterable[str], root: Path = ROOT) -> str:
    """One digest over a bot's source files (line endings normalised)."""
    lines = ["%s:%s" % (p, sha256_file(root / p)) for p in sorted(paths)]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def reference_bot_hash(name: str) -> str:
    return hash_sources(BOT_SOURCES[name])


class Table:
    def __init__(self, directory: Path) -> None:
        self.dir = directory
        self.data: Dict[str, Any] = json.loads((directory / "table.json").read_text(encoding="utf-8"))
        self._profile: Optional[RulesProfile] = None

    # --- identity ---
    @property
    def id(self) -> str:
        return str(self.data["id"])

    @property
    def status(self) -> str:
        return str(self.data["status"])

    @property
    def rules_track(self) -> str:
        return str(self.data["rules_track"])

    @property
    def decision_timeout_s(self) -> float:
        return float(self.data["timeouts"]["decision_s"])

    @property
    def fault_limit_per_1000(self) -> float:
        return float(self.data["faults"]["max_per_1000_decisions"])

    def require_active(self) -> None:
        if self.status != "active":
            raise TablePending("table %s is %s: %s" % (self.id, self.status, self.data.get("pending_reason", "")))

    @property
    def profile(self) -> RulesProfile:
        self.require_active()
        if self._profile is None:
            self._profile = load_profile(self.dir / self.data["rules"])
            expected = self.data["rules_sha256"]
            if self._profile.rules_sha256 != expected:
                raise RuntimeError(
                    "table %s: rules.json hash %s does not match table.json %s"
                    % (self.id, self._profile.rules_sha256, expected)
                )
        return self._profile

    # --- the field ---
    @property
    def field(self) -> List[Dict[str, Any]]:
        return list(self.data["field"])

    def verify_field(self) -> None:
        """Refuse to run if a reference bot's source no longer matches its pin."""
        for member in self.field:
            actual = reference_bot_hash(member["bot"])
            if actual != member["sha256"]:
                raise RuntimeError(
                    "table %s: reference bot %s changed (pinned %s, now %s). "
                    "A change to the field is a new table version."
                    % (self.id, member["bot"], member["sha256"][:12], actual[:12])
                )

    # --- deals ---
    @property
    def public_range(self) -> Dict[str, int]:
        return dict(self.data["seeds"]["public"])

    def public_deals(self, count: int, offset: int = 0) -> List[Deal]:
        rng = self.public_range
        if offset + count > rng["count"]:
            raise ValueError("the public deck for %s has %d deals" % (self.id, rng["count"]))
        return [
            Deal(i, rng["start"] + i, dealer_for_index(i), wind_for_index(i))
            for i in range(offset, offset + count)
        ]

    def private_deals(self, path: str, count: int, offset: int = 0) -> List[Deal]:
        seeds = load_private_seeds(path)
        rng = self.public_range
        lo, hi = rng["start"], rng["start"] + rng["count"]
        clash = [s for s in seeds if lo <= s < hi]
        if clash:
            raise ValueError("the private deck overlaps the public range; it would not be private")
        if offset + count > len(seeds):
            raise ValueError("the private deck has %d deals, asked for %d" % (len(seeds), offset + count))
        return [Deal(i, seeds[i], dealer_for_index(i), wind_for_index(i)) for i in range(offset, offset + count)]

    # --- fingerprint ---
    @property
    def fingerprint_path(self) -> Path:
        return self.dir / "fingerprint.json"

    def pinned_fingerprint(self) -> Dict[str, Any]:
        return json.loads(self.fingerprint_path.read_text(encoding="utf-8"))


def load_private_seeds(path: str) -> List[int]:
    """Read a private deck: JSON ``{"seeds": [...]}``, JSON ``{"start": S, "count": C}``, or one integer per line."""
    text = Path(path).read_text(encoding="utf-8").strip()
    if text.startswith("{") or text.startswith("["):
        obj = json.loads(text)
        if isinstance(obj, dict) and "seeds" in obj:
            return [int(s) for s in obj["seeds"]]
        if isinstance(obj, dict) and "start" in obj and "count" in obj:
            return [int(obj["start"]) + i for i in range(int(obj["count"]))]
        if isinstance(obj, list):
            return [int(s) for s in obj]
        raise ValueError("unrecognised private seed file")
    return [int(line) for line in text.splitlines() if line.strip()]


def load_table(table_id: str, tables_dir: Optional[Path] = None) -> Table:
    base = Path(tables_dir) if tables_dir else TABLES_DIR
    d = base / table_id
    if not (d / "table.json").exists():
        available = sorted(p.name for p in base.iterdir() if (p / "table.json").exists()) if base.exists() else []
        raise ValueError("no table %r (have: %s)" % (table_id, ", ".join(available)))
    return Table(d)


def list_tables(tables_dir: Optional[Path] = None) -> List[Table]:
    base = Path(tables_dir) if tables_dir else TABLES_DIR
    return [Table(p) for p in sorted(base.iterdir()) if (p / "table.json").exists()]


def private_seed_path(cli_value: Optional[str]) -> Optional[str]:
    return cli_value or os.environ.get(PRIVATE_SEEDS_ENV) or None
