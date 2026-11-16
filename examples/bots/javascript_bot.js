#!/usr/bin/env node
// A complete example bot in plain JavaScript (Node 14 or newer). No packages.
//
// It speaks the JSON-lines protocol in protocol/PROTOCOL.md: one JSON object per line on stdin,
// one per line on stdout. Not a strong player: it wins when it can, pongs value tiles, and
// otherwise throws the tile that looks least useful.
//
// Score it: python -m hkbench score --table hk-hkma-v1 --bot "node examples/bots/javascript_bot.js" --deals 50

const readline = require("readline");

const DRAGONS = [31, 32, 33];

function neighbours(hand, t) {
  let score = 0;
  if (t < 27) {
    const r = t % 9;
    for (const d of [-2, -1, 1, 2]) {
      if (r + d >= 0 && r + d <= 8 && hand[t + d] > 0) score += Math.abs(d) === 1 ? 2 : 1;
    }
  }
  return score;
}

function tileValue(hand, t, you, prevailing) {
  const n = hand[t];
  let value = 0;
  if (n >= 3) value += 10;
  else if (n === 2) value += 6;
  value += neighbours(hand, t);
  const isDragon = DRAGONS.includes(t);
  if (isDragon) value += 2;
  if (t === 27 + you.seat_wind || t === 27 + prevailing) value += 2;
  if (n === 1 && t >= 27 && !isDragon && t !== 27 + you.seat_wind && t !== 27 + prevailing) value -= 1;
  return value;
}

function decide(msg) {
  const legal = new Map(msg.legal.map((a) => [a.id, a]));
  if (legal.has(1)) return 1; // win
  const you = msg.you;
  if (msg.phase === "claim") {
    const tile = msg.offer.tile;
    if (legal.has(57) && (DRAGONS.includes(tile) || tile === 27 + you.seat_wind || tile === 27 + msg.prevailing_wind)) {
      return 57; // pong a value tile
    }
    return 0; // pass
  }
  let best = null;
  let bestValue = null;
  for (const a of msg.legal) {
    if (a.kind !== "discard") continue;
    const v = tileValue(you.hand, a.tile, you, msg.prevailing_wind);
    if (bestValue === null || v < bestValue) {
      best = a.id;
      bestValue = v;
    }
  }
  return best;
}

const rl = readline.createInterface({ input: process.stdin });
rl.on("line", (line) => {
  line = line.trim();
  if (!line) return;
  const msg = JSON.parse(line);
  if (msg.type === "hello") {
    console.log(JSON.stringify({ type: "ready", protocol: msg.protocol, name: "javascript_example", version: "1" }));
  } else if (msg.type === "decide") {
    console.log(JSON.stringify({ type: "action", seq: msg.seq, id: decide(msg) }));
  } else if (msg.type === "bye") {
    process.exit(0);
  }
  // game_over needs no answer
});
