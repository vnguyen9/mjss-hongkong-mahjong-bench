"""Rules profiles: a table's rules file, loaded and hashed.

A profile is plain JSON (no third-party parser). Its ``rules_hash`` is the first 16 hex
characters of the SHA-256 of the canonical JSON; ``rules_sha256`` is the full digest. Both
go into every result so a row says exactly which rules it was scored under.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set


@dataclass(frozen=True)
class RulesProfile:
    data: Dict[str, Any]
    path: Path
    rules_hash: str
    rules_sha256: str

    @property
    def profile_id(self) -> str:
        return str(self.data["profile_id"])

    @property
    def minimum_faan(self) -> int:
        return int(self.data["win"]["minimum_faan"])

    @property
    def faan_cap(self) -> int:
        return int(self.data["win"]["faan_cap"])

    @property
    def seven_pairs(self) -> bool:
        """Whether seven different pairs is a legal, scoring win at this table.

        Read with ``.get`` so a rules file without the key (the HKMA table) plays no Seven Pairs.
        """
        return bool(self.data["win"].get("seven_pairs", False))

    @property
    def patterns(self) -> Dict[str, int]:
        return {k: int(v) for k, v in self.data["patterns"].items()}

    @property
    def flower_patterns(self) -> Dict[str, int]:
        return {k: int(v) for k, v in self.data["flowers"].items()}

    @property
    def payment_table(self) -> Dict[int, int]:
        return {int(k): int(v) for k, v in self.data["payments"]["table"].items()}

    @property
    def self_draw_multiplier(self) -> float:
        return float(self.data["payments"]["self_draw_multiplier"])

    @property
    def limit_hands(self) -> Set[str]:
        return set(self.data["exclusions"]["limit_hands"])

    @property
    def implied(self) -> Dict[str, List[str]]:
        return {k: list(v) for k, v in self.data["exclusions"]["implied"].items()}

    def pattern_faan(self, name: str) -> int:
        if name in self.patterns:
            return self.patterns[name]
        if name in self.flower_patterns:
            return self.flower_patterns[name]
        raise KeyError(name)


def _canonical_bytes(data: Dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def profile_from_dict(data: Dict[str, Any], path: Path = Path("<memory>")) -> RulesProfile:
    full = hashlib.sha256(_canonical_bytes(data)).hexdigest()
    return RulesProfile(data=data, path=path, rules_hash=full[:16], rules_sha256=full)


def load_profile(path: "Path | str") -> RulesProfile:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return profile_from_dict(data, p)
