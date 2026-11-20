"""The run key: what makes a bot's ``rng_seed`` and ``game_id`` unguessable.

Every decision message carries an ``rng_seed``, and every game a ``game_id``. Both used to be
computed from the deal's seed, so a bot that inverted them could rebuild the wall. Now both are
HMAC-SHA256 outputs under a *run key* that is not an input to anything a bot sees:

* A **private-deck** run draws 32 random bytes from the operating system. The key lives in the
  runner (and its worker processes) only. It is never written to a result or a log, never put in
  the environment, and never sent to a bot.
* A **public-deck** run uses ``PUBLIC_RUN_KEY``, a fixed key printed in this file, so a public run
  repeats exactly and its logs reproduce. A public deck is public anyway.

The key does not take the deal's seed as input: the message is the table, the deal's index, the
arrangement and the decision number, so even a known key says nothing about the wall.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import struct

RNG_SCHEME = "hmac-sha256-v2"
#: What a result file written before 1.1.0 used: SplitMix64 of the deal seed. Read, never written.
LEGACY_RNG_SCHEME = "splitmix-v1"

_TAG = b"hkbench-rng-2"
_GAME_TAG = b"hkbench-game-2"

def scheme_of(result: dict) -> str:
    """The seed scheme a result file was made under; a file from before 1.1.0 names none."""
    return str(result.get("rng_scheme", LEGACY_RNG_SCHEME))


PUBLIC_RUN_KEY = hashlib.sha256(b"hkbench-public-rng-v2").digest()

#: The fair-play check asks about a position on its own deals. Its "arrangement" is out here, where no real game goes.
FAIRPLAY_ARRANGEMENT = 1 << 20


def new_run_key() -> bytes:
    """A fresh private-run key: 32 bytes from the operating system."""
    return os.urandom(32)


def _field(b: bytes) -> bytes:
    """Length-prefixed, so ("ab", "c") and ("a", "bc") are different messages."""
    return struct.pack(">I", len(b)) + b


def _message(tag: bytes, table_id: str, deal_index: int, arrangement: int, seq: int) -> bytes:
    return tag + _field(table_id.encode("utf-8")) + struct.pack(">QIQ", deal_index, arrangement, seq)


def decision_seed(run_key: bytes, table_id: str, deal_index: int, arrangement: int, seq: int) -> int:
    """The ``rng_seed`` of one decision: below 2**31, fixed by the run key and the position alone."""
    digest = hmac.new(run_key, _message(_TAG, table_id, deal_index, arrangement, seq), hashlib.sha256).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFF


def game_id(run_key: bytes, table_id: str, deal_index: int, arrangement: int) -> str:
    """The ``game_id`` of one game: 32 hex digits that name nothing a bot could use."""
    digest = hmac.new(run_key, _message(_GAME_TAG, table_id, deal_index, arrangement, 0), hashlib.sha256).digest()
    return digest[:16].hex()
