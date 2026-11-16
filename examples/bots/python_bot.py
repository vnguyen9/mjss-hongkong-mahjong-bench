#!/usr/bin/env python3
"""A complete example bot in plain Python. No imports from this repo.

It speaks the JSON-lines protocol in protocol/PROTOCOL.md: read one JSON object per line from
stdin, write one JSON object per line to stdout. It is not a strong player. It declares a win
when it can, claims a pong of a dragon or a wind it is entitled to, and otherwise throws the
tile that looks least useful.

Run it:  python examples/bots/python_bot.py
Score it: python -m hkbench score --table hk-hkma-v1 --bot "python examples/bots/python_bot.py" --deals 50
"""

import json
import sys

DRAGONS = (31, 32, 33)


def neighbours(hand, t):
    """How well tile t connects to the rest of the hand."""
    score = 0
    if t < 27:
        r = t % 9
        for d in (-2, -1, 1, 2):
            if 0 <= r + d <= 8 and hand[t + d] > 0:
                score += 2 if abs(d) == 1 else 1
    return score


def tile_value(hand, t, you, prevailing):
    n = hand[t]
    value = 0
    if n >= 3:
        value += 10
    elif n == 2:
        value += 6
    value += neighbours(hand, t)
    if t in DRAGONS:
        value += 2
    if t == 27 + you["seat_wind"] or t == 27 + prevailing:
        value += 2
    if n == 1 and t >= 27 and t not in DRAGONS and t != 27 + you["seat_wind"] and t != 27 + prevailing:
        value -= 1
    return value


def decide(msg):
    legal = {a["id"]: a for a in msg["legal"]}
    if 1 in legal:                      # win
        return 1
    you = msg["you"]
    if msg["phase"] == "claim":
        tile = msg["offer"]["tile"]
        if 57 in legal and (tile in DRAGONS or tile == 27 + you["seat_wind"] or tile == 27 + msg["prevailing_wind"]):
            return 57                   # pong a value tile
        return 0                        # pass
    hand = you["hand"]
    best, best_value = None, None
    for a in msg["legal"]:
        if a["kind"] != "discard":
            continue
        v = tile_value(hand, a["tile"], you, msg["prevailing_wind"])
        if best_value is None or v < best_value:
            best, best_value = a["id"], v
    return best


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        kind = msg.get("type")
        if kind == "hello":
            print(json.dumps({"type": "ready", "protocol": msg["protocol"], "name": "python_example", "version": "1"}), flush=True)
        elif kind == "decide":
            print(json.dumps({"type": "action", "seq": msg["seq"], "id": decide(msg)}), flush=True)
        elif kind == "bye":
            break
        # game_over needs no answer


if __name__ == "__main__":
    main()
