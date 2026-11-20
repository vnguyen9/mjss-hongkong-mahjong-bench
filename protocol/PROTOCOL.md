# Protocol `hkbench-1`

A bot is any program that speaks JSON lines over its standard input and output. The bench starts the program, sends it messages, and reads its answers. One JSON object per line, UTF-8, no blank lines needed. Write answers to stdout and flush after every line. Anything you write to stderr is ignored (the last few lines are shown if your bot crashes).

The machine-readable form is `schema.json` in this folder. `examples/bots/python_bot.py` and `examples/bots/javascript_bot.js` are complete bots.

## The conversation

```
bench -> bot   {"type":"hello", ...}            once, when the program starts
bot   -> bench {"type":"ready", ...}            within 30 seconds
bench -> bot   {"type":"decide", ...}           every time this seat must act
bot   -> bench {"type":"action", ...}           one legal action, within the time limit
bench -> bot   {"type":"game_over", ...}        when a hand ends; no answer
bench -> bot   {"type":"bye"}                   then the bench closes stdin; exit when you see either
```

One program plays many hands. It may be asked to play two seats of the same hand (in a head-to-head match) and different seats in different hands, so keep no state you cannot rebuild from the `decide` message.

### hello and ready

```json
{"type":"hello","protocol":"hkbench-1","table":"hk-hkma-v1","decision_timeout_s":10}
{"type":"ready","protocol":"hkbench-1","name":"my_bot","version":"1.2"}
```

`name` and `version` are optional and are only for display.

### decide

The bench sends **only what that seat could see at a real table**: its own concealed tiles, every discard, every meld and flower on the table, the winds, the dealer, how many tiles are left in the wall, and its own legal actions. It never sends another player's concealed tiles or the order of the wall.

Players are numbered relative to you: `0` you, `1` the player who acts after you, `2` across, `3` the player who acts before you. Only player 1 may claim your discards as a chow.

```json
{"protocol":"hkbench-1","type":"decide","table":"hk-hkma-v1","game_id":"3f9c0a52e1d84b7aa6c5d20817be94f0","seq":7,
 "rng_seed":1396672242,"phase":"turn","prevailing_wind":0,"dealer":2,"wall_remaining":84,
 "you":{"seat_wind":2,"hand":[1,0,0,0,0,0,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,1,0,2,1,0,1,1,0,1,0,1],
        "drawn":31,"draw_kind":"wall","melds":[],"flowers":[3]},
 "others":[{"p":1,"seat_wind":3,"hand_size":13,"melds":[],"flowers":[6]},
           {"p":2,"seat_wind":0,"hand_size":13,"melds":[],"flowers":[]},
           {"p":3,"seat_wind":1,"hand_size":10,"melds":[{"kind":"chow","tiles":[19,20,21],"from":2}],"flowers":[]}],
 "discards":[{"p":2,"tile":11,"claimed":false},{"p":3,"tile":27,"claimed":false},{"p":0,"tile":4,"claimed":false}],
 "offer":null,
 "unseen":[3,4,4,4,3,4,4,3,4,3,4,2,3,4,4,4,4,3,4,2,3,3,4,3,4,2,3,3,3,3,4,3,4,2],
 "legal":[{"id":2,"kind":"discard","tile":0},{"id":11,"kind":"discard","tile":9},{"id":35,"kind":"discard","tile":33}]}
```

(`discards` and `legal` are shortened here.) Fields:

| Field | Meaning |
|---|---|
| `game_id` | A random-looking token that names the hand within this game. It means nothing: it holds no deal number, seat or table, and it is not the same from run to run on a private deck. Do not parse it. |
| `seq` | Counts every decision in the hand across all seats. Echo it back. |
| `rng_seed` | A number below 2^31. **Use it for any randomness.** It is a keyed hash (HMAC-SHA256) of the decision under a key the bench keeps to itself, so it tells you nothing about the deal. On a private deck the key is new every run. |
| `phase` | `turn`: you act on your own hand. `claim`: a tile was discarded (or added to a kong) and you may react. |
| `prevailing_wind`, `dealer` | Winds are 0 East, 1 South, 2 West, 3 North. `dealer` is the dealer's player number relative to you, so `0` means you deal. |
| `wall_remaining` | Tiles left to draw. |
| `you.seat_wind` | Your wind. The dealer is East. |
| `you.hand` | Your concealed tiles as 34 counts, **including the tile you just drew**. |
| `you.drawn` | The tile you just drew, or `null` (after a claim, or on a claim phase). |
| `you.draw_kind` | `wall`, `flower_replacement`, `kong_replacement`, or `null`. |
| `melds` | Shown melds. `kind` is `chow`, `pong`, `exposed_kong`, `concealed_kong` or `added_kong`. `from` is who discarded the claimed tile, `null` for a concealed kong. Concealed kongs are shown to everyone. |
| `flowers` | Flower ids shown by that player (0 to 7). |
| `others[].hand_size` | How many concealed tiles that player holds. |
| `discards` | Every discard so far, oldest first. `claimed` is true if the tile was later taken into a meld. |
| `offer` | On a claim phase: `{"tile", "from", "kind"}`, where `kind` is `discard` or `added_kong` (a player added a fourth tile to a pong; you may rob it by winning). `null` on a turn. |
| `unseen` | For each tile id, how many are not in your hand, not in a meld, and not in a river. It is derived from the other fields and is there for convenience. |
| `legal` | Every action you may take. Never empty. |

**Reactions are simultaneous.** On a claim phase you are not told what other players choose. Wins beat pongs and kongs, which beat chows. If two players can win on the same tile, the one nearest after the discarder wins.

**Only players who can act are asked.** If you cannot claim a discard, you get no message for it.

### Tiles

| Ids | Tiles |
|---|---|
| 0 to 8 | Characters 1 to 9 |
| 9 to 17 | Bamboo 1 to 9 |
| 18 to 26 | Dots 1 to 9 |
| 27 to 30 | East, South, West, North |
| 31 to 33 | Red, Green, White dragon |

Flowers have their own ids, 0 to 3 (the four flowers) and 4 to 7 (the four seasons). Flower `n` belongs to seat wind `n mod 4`.

### Actions

Each entry in `legal` has an `id` (what you send back), a `kind`, and sometimes `tile` or `tiles`.

| Id | Kind | Notes |
|---|---|---|
| 0 | `pass` | Only on a claim phase. |
| 1 | `win` | Declare a win. Offered only when the hand is complete and reaches the table's minimum faan. |
| 2 to 35 | `discard` | `tile` is the tile id. The id is `2 + tile`. |
| 36 to 56 | `chow` | `tiles` is the run, for example `[22,23,24]`. It includes the offered tile. |
| 57 | `pong` | Claim the offered tile with two of yours. |
| 58 | `kong` | Claim the offered tile with three of yours. |
| 59 to 92 | `concealed_kong` | `tile` is the tile. The id is `59 + tile`. Turn phase only. |
| 93 to 126 | `added_kong` | Add your fourth tile to a shown pong. `tile` is the tile. The id is `93 + tile`. Turn phase only. |

After a claim that is not a win, the claimer is asked for a `turn` with `drawn: null` and normally discards. After a kong the player draws a replacement tile from the back of the wall and is asked again.

### action

```json
{"type":"action","seq":7,"id":13}
```

`seq` must equal the `decide` message's `seq`. `id` must be an integer from `legal`.

### game_over

```json
{"type":"game_over","game_id":"3f9c0a52e1d84b7aa6c5d20817be94f0","cause":"win","winner":1,"discarder":3,"faan":4,"patterns":[["all_pong",3],["dragon_pong",1]],"payment":-16}
```

`cause` is `win` or `exhaustive` (the wall ran out). `winner` and `discarder` are player numbers relative to you, or `null`. `payment` is your points. No answer.

## Time and mistakes

| What | Rule |
|---|---|
| Time | `decision_timeout_s` (10 seconds on both tables) per decision, wall clock. 30 seconds to answer `hello`. |
| Late, malformed or illegal answer | The bench plays a **fallback** for that seat and counts a fault. Fallback: on a claim, pass. On a turn, discard the tile you just drew, or the lowest-numbered legal discard. |
| Too many faults | More than 1 per 1000 decisions and the run is rejected, not scored. |
| A late answer to an old decision | Ignored (the bench matches on `seq`). |
| Crash, closed pipes, or no `ready` | The run stops and is not scored. |

Illegal means: not an integer, not in `legal`, or a `seq` that does not match. Printing anything on stdout that is not one JSON object per line counts as malformed.

## Fair play

A bot must be a **pure function of the `decide` message**. The same message must always get the same answer. If you need randomness, seed it from `rng_seed`. Do not read the clock, files, the network, or your own earlier messages to decide.

Every game gets a **new process**. The bench starts your bot for each seat of each game and stops it when the game ends, so nothing it learns in one game can carry into the next. It starts with only `PATH`, `LANG`, `LC_*` and (on Windows) `SYSTEMROOT` in its environment, plus any variable the run names with `--bot-env`. Nothing of the bench's own (`HKBENCH_*`, the path of the private deck) is passed. `HOME`, `TMPDIR`, `TEMP` and `TMP` all name one new, empty directory that is also its working directory (unless the run gives `--cwd`, the directory your program lives in, which you should treat as read-only). The directory is deleted when the process stops, so a file written in one game is not there in the next or at the bot's other seat. The bot runs in its own process group, and when the game ends the bench kills the whole group, so a background process or a daemon you start does not survive the game. Running natively cannot stop a bot writing elsewhere on disk it has access to, reaching another process of the same user, or starting a process in a new session that survives the kill; a sandbox is the real boundary (`--sandbox CMD`, see `SUBMITTING.md`). In a sandbox the bench leaves `HOME` and the temp directories to the sandbox. One limit remains either way: `game_over` is sent at the end of a scored game and not in the fair-play check, so a bot that could keep state across processes could tell them apart afterwards.

Before a bot is scored, the bench plays it in real games against the field, on deals drawn from a secret made for this check (never a known or public deal), at one seat. At chosen decisions it re-deals every hidden tile (other players' concealed hands and the whole wall) so that the seat's view is unchanged, and asks again in a new process that is first sent that seat's earlier messages of the game, which follow the moves your bot really made, with the pauses the game had between them. Your bot sits at every position against the dealer, as scoring seats it. A bot whose answer to the position changes, or whose answer to an earlier message differs from the one it played, is rejected. The same check runs on your machine:

```
python -m hkbench fairplay --table hk-hkma-v1 --bot "python examples/bots/python_bot.py"
```

The check also confirms that the message the bench builds is byte-identical for every re-deal. The check's messages carry a `game_id` and `rng_seed` made the way a real game's are, in games that look like real ones, so a bot cannot tell the check from a game. `fairplay --debug-fixed-check` repeats the same deals every time, which makes the check recognisable; it is for reproducing a result and is never used when a bot is scored.
