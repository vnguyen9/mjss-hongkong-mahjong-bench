"""The leaderboard: ``site/leaderboard.json`` and a static ``site/index.html`` built from ``results/``.

The page needs no server and no network. It carries its own copy of the data so it opens straight
from disk; ``leaderboard.json`` is the same data for another site to pull.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List

from hkbench import __version__, runkey, stats
from hkbench.tables import list_tables

SCHEMA = "hkbench-leaderboard-1"

TRACKS = [
    {"id": "bots", "title": "Bots", "note": None},
    {"id": "llms", "title": "LLMs", "note": "Coming soon: LLMs will play through the same protocol, with cost per hand shown."},
    {"id": "humans", "title": "Humans", "note": "Coming soon: humans will play the same deals at a table in the browser."},
]


def _rows(results_dir: Path) -> List[Dict[str, Any]]:
    out = []
    for path in sorted(results_dir.glob("*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if r.get("schema") != "hkbench-result-1":
            continue
        h, s = r["headline"], r["stats"]
        out.append({
            "run_id": r["run_id"],
            "created_utc": r["created_utc"],
            "track": r["bot"]["track"],
            "table": r["table"]["id"],
            "rules_track": r["table"]["rules_track"],
            "bot": {k: r["bot"][k] for k in ("name", "kind", "trained_on", "sha256", "description")},
            "verification": r["verification"],
            "rng_scheme": runkey.scheme_of(r),
            "isolation": r.get("isolation"),
            "seed_tag": r["seeds"]["tag"],
            "points_per_hand": h["points_per_hand"],
            "se": h["se"],
            "ci95": h["ci95"],
            "deals": h["deals"],
            "games": h["games"],
            "win_rate": s["win_rate"]["mean"],
            "deal_in_rate": s["deal_in_rate"]["mean"],
            "average_win_points": s["average_win_points"],
            "average_win_faan": s["average_win_faan"],
            "limit_hands": s["limit_hands"],
            "log": "results/" + r["log"],
            "result": "results/" + path.name,
            "command": r["command"],
        })
    return out


def _latest(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One row per bot, table and deck: the most recent run."""
    best: Dict[Any, Dict[str, Any]] = {}
    for r in rows:
        key = (r["bot"]["name"], r["bot"]["sha256"], r["table"], r["seed_tag"])
        if key not in best or r["created_utc"] > best[key]["created_utc"]:
            best[key] = r
    return list(best.values())


def _rank(rows: List[Dict[str, Any]]) -> None:
    """Rank within (track, table, deck): rows whose 95% intervals overlap share a rank."""
    groups: Dict[Any, List[Dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault((r["track"], r["table"], r["seed_tag"]), []).append(r)
    for members in groups.values():
        ranks = stats.shared_ranks({m["run_id"]: m for m in members})
        for m in members:
            m["rank"] = ranks[m["run_id"]]
        members.sort(key=lambda m: -m["points_per_hand"])


def _h2h(results_dir: Path) -> List[Dict[str, Any]]:
    out = []
    for path in sorted(results_dir.glob("*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if r.get("schema") != "hkbench-h2h-1":
            continue
        out.append({
            "run_id": r["run_id"], "created_utc": r["created_utc"], "table": r["table"]["id"],
            "rules_track": r["table"]["rules_track"], "verification": r["verification"],
            "seed_tag": r["seeds"]["tag"], "deals": r["seeds"]["deals"],
            "bots": sorted(({"name": n, "rating": v["rating"], "ci95": v["ci95"], "rank": v["rank"]}
                            for n, v in r["bradley_terry"].items()), key=lambda b: b["rank"] * 1e6 - b["rating"]),
            "result": "results/" + path.name,
        })
    return out


def build(results_dir: Path, out_dir: Path) -> Path:
    rows = _latest(_rows(results_dir))
    _rank(rows)
    rows.sort(key=lambda r: (r["table"], r["track"], r["seed_tag"], -r["points_per_hand"]))
    tables = []
    for t in sorted(list_tables(), key=lambda t: (t.data.get("released", ""), t.id)):  # in the order they were released
        tables.append({
            "id": t.id, "title": t.data["title"], "rules_track": t.rules_track, "status": t.status,
            "summary": t.data["summary"], "pending_reason": t.data.get("pending_reason"),
            "field": [m["bot"] for m in t.field],
            "headline": t.id == "hk-hkma-v1",
        })
    timestamps = [r["created_utc"] for r in rows]
    timestamps.extend(r["created_utc"] for r in _h2h(results_dir))
    generated_utc = max(timestamps) if timestamps else "1970-01-01T00:00:00Z"
    data = {
        "schema": SCHEMA,
        "generated_utc": generated_utc,
        "hkbench_version": __version__,
        "tracks": TRACKS,
        "tables": tables,
        "rows": rows,
        "head_to_head": _h2h(results_dir),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "leaderboard.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    html = TEMPLATE.replace("__DATA__", json.dumps(data, sort_keys=True).replace("</", "<\\/"))
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    return out_dir / "index.html"


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hong Kong Mahjong Bench</title>
<style>
:root{--bg:#fbfaf7;--card:#fff;--ink:#1d1d1b;--mute:#6b6a63;--line:#e4e1d8;--accent:#a3261b;--ok:#1f7a3f;--warn:#9a6a00;--chip:#f1eee6}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#161614;--card:#1f1f1c;--ink:#ece9e1;--mute:#a09d93;--line:#333128;--accent:#e0584b;--ok:#58c07a;--warn:#e0b04a;--chip:#2a2924}}
:root[data-theme="dark"]{--bg:#161614;--card:#1f1f1c;--ink:#ece9e1;--mute:#a09d93;--line:#333128;--accent:#e0584b;--ok:#58c07a;--warn:#e0b04a;--chip:#2a2924}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
main{max-width:1040px;margin:0 auto;padding:28px 16px 64px}
h1{font-size:28px;margin:0 0 4px}
p.lede{color:var(--mute);margin:0 0 20px;max-width:62ch}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 12px}
button.tab,button.rules{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:6px 14px;border-radius:999px;cursor:pointer}
button[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.row{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:0 0 12px}
label.chk{color:var(--mute);font-size:14px;display:flex;gap:6px;align-items:center}
.note{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:0 0 14px;color:var(--mute);font-size:14px}
.note b{color:var(--ink)}
.scroll{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;min-width:760px;font-size:14px}
th,td{text-align:right;padding:9px 12px;border-bottom:1px solid var(--line);white-space:nowrap}
th{font-weight:600;color:var(--mute);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
th:nth-child(1),td:nth-child(1),th:nth-child(2),td:nth-child(2){text-align:left}
tr:last-child td{border-bottom:0}
td.rank{color:var(--mute);width:40px}
td .sub{display:block;color:var(--mute);font-size:12px}
.pts{font-variant-numeric:tabular-nums;font-weight:600}
.ci{color:var(--mute);font-variant-numeric:tabular-nums}
.badge{display:inline-block;font-size:11px;padding:1px 8px;border-radius:999px;background:var(--chip);color:var(--mute);margin-left:6px}
.badge.verified{background:transparent;color:var(--ok);border:1px solid var(--ok)}
.badge.unverified{color:var(--warn)}
.empty{padding:28px 14px;color:var(--mute);text-align:center}
h2{font-size:18px;margin:28px 0 8px}
footer{margin-top:28px;color:var(--mute);font-size:13px}
code{background:var(--chip);padding:1px 5px;border-radius:4px;font-size:12px}
</style>
</head>
<body>
<main>
  <h1>Hong Kong Mahjong Bench</h1>
  <p class="lede">Points a hand against a frozen field of reference bots, in duplicate play, with a 95% interval. Every row says which rules it was scored under and whether the deals were private.</p>
  <div class="tabs" id="tracks" role="tablist" aria-label="Track"></div>
  <div class="tabs" id="rules" aria-label="Rules"></div>
  <div class="row"><label class="chk"><input type="checkbox" id="verifiedOnly"> Verified rows only</label></div>
  <div id="note"></div>
  <div id="board"></div>
  <div id="h2h"></div>
  <footer id="foot"></footer>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById("data").textContent);
  var state = {track:"bots", table:"hk-hkma-v1", verifiedOnly:false};
  try { var s = JSON.parse(localStorage.getItem("hkbench") || "{}"); if (s.track) state.track = s.track; if (s.table) state.table = s.table; } catch (e) {}
  function save(){ try { localStorage.setItem("hkbench", JSON.stringify({track:state.track, table:state.table})); } catch (e) {} }
  function el(tag, attrs, kids){ var e = document.createElement(tag); for (var k in (attrs||{})) { if (k === "text") e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]); } (kids||[]).forEach(function(c){ e.appendChild(c); }); return e; }
  function f(x, d){ return x == null ? "n/a" : (x >= 0 && d !== 0 ? "+" : "") + x.toFixed(d == null ? 2 : d); }
  function pct(x){ return x == null ? "n/a" : (100 * x).toFixed(1) + "%"; }
  function buttons(host, items, key){
    host.innerHTML = "";
    items.forEach(function(it){
      var b = el("button", {"class":"tab", "type":"button", "aria-pressed": String(state[key] === it.id), text: it.title});
      b.onclick = function(){ state[key] = it.id; save(); render(); };
      host.appendChild(b);
    });
  }
  function render(){
    buttons(document.getElementById("tracks"), D.tracks, "track");
    buttons(document.getElementById("rules"), D.tables.map(function(t){ return {id:t.id, title:t.rules_track + (t.status === "pending" ? " (pending)" : "")}; }), "table");
    var table = D.tables.filter(function(t){ return t.id === state.table; })[0];
    var track = D.tracks.filter(function(t){ return t.id === state.track; })[0];
    var note = document.getElementById("note"); note.innerHTML = "";
    var board = document.getElementById("board"); board.innerHTML = "";
    var h2h = document.getElementById("h2h"); h2h.innerHTML = "";
    if (table) {
      var n = el("div", {"class":"note"});
      n.appendChild(el("b", {text: table.title + ". "}));
      n.appendChild(document.createTextNode(table.status === "pending" ? "Not scoring yet: " + table.pending_reason + "." : table.summary));
      note.appendChild(n);
    }
    if (table && table.status === "pending") { board.appendChild(el("div", {"class":"empty", text:"This table has no results yet. It opens when the engine supports its scoring."})); render_foot(); return; }
    var rows = D.rows.filter(function(r){ return r.track === state.track && r.table === state.table && (!state.verifiedOnly || r.verification === "verified"); });
    if (!rows.length) {
      board.appendChild(el("div", {"class":"empty", text: track.note || "No rows yet."}));
    } else {
      var head = el("tr"); ["#", "Bot", "Points a hand", "95% interval", "Win", "Deal-in", "Average win", "Games"].forEach(function(h){ head.appendChild(el("th", {text:h})); });
      var body = el("tbody");
      rows.forEach(function(r){
        var tr = el("tr");
        tr.appendChild(el("td", {"class":"rank", text:String(r.rank)}));
        var name = el("td"); name.appendChild(document.createTextNode(r.bot.name));
        name.appendChild(el("span", {"class":"badge " + r.verification, text:r.verification}));
        name.appendChild(el("span", {"class":"sub", text: r.seed_tag + " deals. Trained on: " + r.bot.trained_on}));
        tr.appendChild(name);
        tr.appendChild(el("td", {"class":"pts", text:f(r.points_per_hand)}));
        tr.appendChild(el("td", {"class":"ci", text: r.ci95 ? "[" + f(r.ci95[0]) + ", " + f(r.ci95[1]) + "]" : "n/a"}));
        tr.appendChild(el("td", {text:pct(r.win_rate)}));
        tr.appendChild(el("td", {text:pct(r.deal_in_rate)}));
        tr.appendChild(el("td", {text: r.average_win_points == null ? "n/a" : r.average_win_points.toFixed(1) + " pts, " + r.average_win_faan.toFixed(1) + " faan"}));
        tr.appendChild(el("td", {text:String(r.games)}));
        body.appendChild(tr);
      });
      var t = el("table"); var th = el("thead"); th.appendChild(head); t.appendChild(th); t.appendChild(body);
      var sc = el("div", {"class":"scroll"}); sc.appendChild(t); board.appendChild(sc);
    }
    var hh = D.head_to_head.filter(function(h){ return h.table === state.table; });
    if (state.track === "bots" && hh.length) {
      h2h.appendChild(el("h2", {text:"Head to head"}));
      hh.forEach(function(h){
        var head = el("tr"); ["#", "Bot", "Rating", "95% interval"].forEach(function(x){ head.appendChild(el("th", {text:x})); });
        var body = el("tbody");
        h.bots.forEach(function(b){
          var tr = el("tr"); tr.appendChild(el("td", {"class":"rank", text:String(b.rank)})); tr.appendChild(el("td", {text:b.name}));
          tr.appendChild(el("td", {"class":"pts", text:f(b.rating, 0)})); tr.appendChild(el("td", {"class":"ci", text:"[" + f(b.ci95[0], 0) + ", " + f(b.ci95[1], 0) + "]"}));
          body.appendChild(tr);
        });
        var t = el("table"); var th = el("thead"); th.appendChild(head); t.appendChild(th); t.appendChild(body);
        var sc = el("div", {"class":"scroll"}); sc.appendChild(t);
        h2h.appendChild(el("p", {"class":"ci", text:h.deals + " deals, " + h.seed_tag + " deck, " + h.verification + ". Bradley-Terry rating on the Elo scale."}));
        h2h.appendChild(sc);
      });
    }
    render_foot();
  }
  function render_foot(){
    document.getElementById("foot").innerHTML = "";
    var p = el("p", {text:"A rank is shared when 95% intervals overlap. Points are one quarter of the HKMA rulebook's. Unverified rows were played on the public deals; verified rows were played on private deals after a hidden-tile fair-play check. Built " + D.generated_utc + " by hkbench " + D.hkbench_version + "."});
    document.getElementById("foot").appendChild(p);
  }
  document.getElementById("verifiedOnly").onchange = function(e){ state.verifiedOnly = e.target.checked; render(); };
  render();
})();
</script>
</body>
</html>
"""
