"""The in-repo bots, by name."""

from __future__ import annotations

from typing import Callable, Dict, List

from hkbench.agents.faan_aware import FaanAwareBot
from hkbench.agents.random_bot import RandomBot
from hkbench.agents.shallow_search import ShallowSearchBot
from hkbench.agents.ukeire import DeficiencyBot, UkeireBot

REFERENCE_BOTS: Dict[str, Callable] = {
    "random": RandomBot,
    "deficiency": DeficiencyBot,
    "ukeire": UkeireBot,
    "faan_aware": FaanAwareBot,
    "shallow_search": ShallowSearchBot,
}

#: Source files that make up each bot, relative to the repo root. A bot's pinned hash covers all of them.
BOT_SOURCES: Dict[str, List[str]] = {
    "random": ["hkbench/agents/random_bot.py", "hkbench/seeds.py", "hkbench/view.py"],
    "deficiency": ["hkbench/agents/ukeire.py", "hkbench/agents/shanten.py", "hkbench/engine/win.py",
                   "hkbench/seeds.py", "hkbench/view.py"],
    "ukeire": ["hkbench/agents/ukeire.py", "hkbench/agents/shanten.py", "hkbench/engine/win.py",
               "hkbench/seeds.py", "hkbench/view.py"],
    "faan_aware": ["hkbench/agents/faan_aware.py", "hkbench/agents/shanten.py", "hkbench/engine/win.py",
                   "hkbench/engine/scorer.py", "hkbench/engine/tiles.py", "hkbench/engine/types.py",
                   "hkbench/seeds.py", "hkbench/view.py"],
    "shallow_search": ["hkbench/agents/shallow_search.py", "hkbench/agents/shanten.py", "hkbench/engine/win.py",
                       "hkbench/seeds.py", "hkbench/view.py"],
}
