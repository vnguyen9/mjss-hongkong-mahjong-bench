#!/usr/bin/env python3
"""Print the faan and payment tables for a table's rules file as Markdown.

RULES.md embeds this output between marker comments, and a test checks that they match, so the
document cannot drift from the rules file.

    python scripts/render_rules.py hk-hkma-v1
    python scripts/render_rules.py hk-house-v1
    python scripts/render_rules.py hk-chicken-v1
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NAMES = {
    "common_hand": "All Sequences",
    "seven_pairs": "Seven Pairs (seven different pairs, concealed)",
    "fully_concealed": "Closed Hand",
    "self_draw": "Self-Drawn",
    "dragon_pong": "Triplet of Dragons (each triplet)",
    "seat_wind": "Triplet of the player's own wind",
    "prevailing_wind": "Triplet of the prevailing wind",
    "mixed_orphans": "All Terminals and Honours (all triplets)",
    "rob_kong": "Robbing a Kong",
    "kong_replacement": "Win on the replacement tile after a kong",
    "last_tile": "Last Tile from the Wall",
    "mixed_one_suit": "Semi-Flush (one suit plus honours)",
    "all_pong": "All Triplets",
    "small_dragons": "Small Dragons",
    "great_dragons": "Big Dragons",
    "pure_one_suit": "Flush (one suit, no honours)",
    "all_honors": "All Honours",
    "small_winds": "Small Winds",
    "great_winds": "Big Winds",
    "four_concealed_pongs": "All Concealed Triplets",
    "all_kongs": "All Quads",
    "pure_orphans": "All Terminals",
    "heavenly_hand": "Bless of Heaven (dealer wins on the first draw)",
    "earthly_hand": "Bless of Earth (win on the dealer's first discard)",
    "thirteen_orphans": "Thirteen Orphans",
    "double_kong": "After Consecutive Kan",
    "nine_gates": "Nine Gates",
    "seat_flower": "Flower matching the player's seat",
    "seat_season": "Season matching the player's seat",
    "no_flowers": "No flowers or seasons",
    "all_flowers": "All four flowers",
    "all_seasons": "All four seasons",
    "seven_flowers": "Seven flowers or seasons (instant win)",
    "eight_flowers": "Eight flowers and seasons (instant win)",
}

ORDER = ["common_hand", "seven_pairs", "fully_concealed", "self_draw", "dragon_pong", "seat_wind", "prevailing_wind",
         "mixed_orphans", "rob_kong", "kong_replacement", "last_tile",
         "mixed_one_suit", "all_pong", "small_dragons", "great_dragons", "pure_one_suit",
         "all_honors", "small_winds", "great_winds", "four_concealed_pongs", "all_kongs", "pure_orphans",
         "heavenly_hand", "earthly_hand", "thirteen_orphans", "double_kong", "nine_gates"]
FLOWER_ORDER = ["seat_flower", "seat_season", "no_flowers", "all_flowers", "all_seasons", "seven_flowers", "eight_flowers"]


def render(table_id: str) -> str:
    d = ROOT / "tables" / table_id
    rules = json.loads((d / "rules.json").read_text(encoding="utf-8"))
    limit = set(rules["exclusions"]["limit_hands"])
    lines = []
    lines.append("Minimum to win: **%d faan**. Cap: **%d faan**." % (rules["win"]["minimum_faan"], rules["win"]["faan_cap"]))
    lines.append("")
    lines.append("| Faan item | Faan |")
    lines.append("|---|---|")
    for key in ORDER:
        if key == "seven_pairs" and not rules["win"].get("seven_pairs"):
            continue
        v = rules["patterns"][key]
        mark = " \\*" if key in limit else ""
        lines.append("| %s%s | %d |" % (NAMES[key], mark, v))
    lines.append("")
    lines.append("\\* Limit hand. Only this item counts, plus Self-Drawn, Last Tile from the Wall, Robbing a Kong and the kong items.")
    lines.append("")
    lines.append("| Flower item | Faan |")
    lines.append("|---|---|")
    for key in FLOWER_ORDER:
        lines.append("| %s | %d |" % (NAMES[key], rules["flowers"][key]))
    lines.append("")
    table = {int(k): v for k, v in rules["payments"]["table"].items()}
    mult = rules["payments"]["self_draw_multiplier"]
    lines.append("| Faan | Discarder pays everything | Self-drawn: each of the three pays | Self-drawn: winner collects |")
    lines.append("|---|---|---|---|")
    for faan in range(rules["win"]["minimum_faan"], rules["win"]["faan_cap"] + 1):
        base = table[faan]
        total = int(base * mult)
        if faan == 0:
            # A win by self-draw always scores Self-Drawn (1 faan), so a 0-faan win is always a discard win.
            lines.append("| 0 (a chicken hand) | %d | not possible | not possible |" % base)
            continue
        lines.append("| %d | %d | %d | %d |" % (faan, base, total // 3, total))
    return "\n".join(lines)


if __name__ == "__main__":
    print(render(sys.argv[1]))
