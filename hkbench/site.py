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
from hkbench.visuals import banner

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
    html = TEMPLATE.replace("__BANNER__", banner()).replace("__DATA__", json.dumps(data, sort_keys=True).replace("</", "<\\/"))
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    return out_dir / "index.html"


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hong Kong Mahjong Bench</title>
<style>
:root{color-scheme:light;--bg:#f6f8f6;--card:#fff;--ink:#182d25;--mute:#586a62;--line:#dae4de;--accent:#20785b;--soft:#edf5ef;--bar:#a1b3bc;--plot:#1f2933;--rail:#c7d4cd;--warn:#845a12}
:root[data-theme="dark"]{color-scheme:dark;--bg:#0d1612;--card:#14221b;--ink:#edf5ee;--mute:#a5bcb2;--line:#30473a;--accent:#75d9b1;--soft:#1c342c;--bar:#6b8190;--plot:#e6edf3;--rail:#4b6659;--warn:#e6bd73}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#0d1612;--card:#14221b;--ink:#edf5ee;--mute:#a5bcb2;--line:#30473a;--accent:#75d9b1;--soft:#1c342c;--bar:#6b8190;--plot:#e6edf3;--rail:#4b6659;--warn:#e6bd73}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
main{max-width:1160px;margin:auto;padding:24px 32px 60px}a{color:var(--accent);text-underline-offset:4px}nav{display:flex;justify-content:space-between;align-items:center;gap:16px}nav div{display:flex;gap:20px;flex-wrap:wrap}button{font:inherit;cursor:pointer;color:var(--ink)}button:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
#theme{border:1px solid var(--line);border-radius:8px;padding:5px 12px;background:var(--card)}header{text-align:center;margin:24px 0 40px}.banner{max-width:900px;margin:auto}.banner svg{width:100%;height:auto;display:block}.banner svg>rect:first-of-type{fill:var(--soft)}.banner svg>text{fill:var(--ink)}.banner svg>text:last-of-type{fill:var(--mute)}.lede{max-width:660px;margin:20px auto;color:var(--mute);font-size:17px}
.meta{font-size:12px;letter-spacing:.06em;color:var(--mute)}.tracks{display:flex;gap:24px;border-bottom:1px solid var(--line);margin-bottom:28px}.track{border:0;background:none;padding:12px 0;color:var(--mute)}.track[aria-pressed=true]{color:var(--accent);box-shadow:0 2px var(--accent)}.status{font-size:11px;margin-left:8px;background:var(--soft);border-radius:4px;padding:3px 5px}
h2{font-size:26px;letter-spacing:-.6px;line-height:1.3;margin:0 0 10px}.toolbar{display:flex;justify-content:space-between;gap:20px;align-items:center;flex-wrap:wrap;margin:20px 0}.tabs,.decks{display:flex;gap:4px;flex-wrap:wrap}.tabs button,.decks button{border:1px solid transparent;background:transparent;border-radius:6px;padding:8px 14px;color:var(--mute)}.tabs button[aria-pressed=true],.decks button[aria-pressed=true]{background:var(--card);border-color:var(--line);color:var(--accent);font-weight:600}.decks{background:var(--soft);padding:3px;border-radius:9px}.decks button{padding:5px 10px;font-size:13px}
#summary,.explain,footer{color:var(--mute);font-size:13px}#summary{max-width:80ch}.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--card)}table{border-collapse:collapse;width:100%;font-size:14px;white-space:nowrap}caption{text-align:left;padding:16px 20px;font-size:13px;color:var(--mute);border-bottom:1px solid var(--line)}th,td{padding:15px 16px;border-bottom:1px solid var(--line);text-align:right;font-variant-numeric:tabular-nums}th{font-size:12px;color:var(--mute);background:var(--soft);font-weight:500}th button{border:0;background:none;color:inherit;padding:0;font-size:inherit}th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}tr:last-child td{border:0}tr.featured{background:var(--soft)}.name{font-weight:600}.rank{color:var(--mute)}.sub{display:block;color:var(--mute);font-size:11px;font-weight:400}.badge{font-size:11px;border:1px solid var(--line);border-radius:5px;padding:3px 7px;color:var(--warn)}.badge.verified{color:var(--accent)}.metric{min-width:180px}.value{font-weight:650}.interval{display:block;height:20px;margin:7px 0 3px;position:relative;isolation:isolate}.interval:before{content:"";position:absolute;left:0;right:0;top:10px;border-top:1px solid var(--rail);z-index:-1}.mean-bar{position:absolute;top:4px;height:12px;border-radius:3px;background:var(--bar)}.featured .mean-bar{background:var(--accent)}.whisker{position:absolute;top:9px;height:1.5px;background:var(--plot)}.whisker:before,.whisker:after{content:"";position:absolute;top:-4px;width:1.5px;height:10px;background:var(--plot)}.whisker:after{right:0}.zero{position:absolute;top:0;height:20px;border-left:1px solid var(--mute);opacity:.6}.empty{padding:50px 24px;border:1px solid var(--line);border-radius:12px;background:var(--card)}.empty p{color:var(--mute)}footer{border-top:1px solid var(--line);margin-top:32px;padding-top:18px}details{margin-top:28px}summary{cursor:pointer;color:var(--accent)}#headtohead .scroll{margin:16px 0}.explain{margin:12px 0 24px}
@media(max-width:600px){main{padding:16px 16px 40px}nav{font-size:12px}nav div{gap:12px}header{margin:24px 0}.lede{font-size:15px}.tracks{gap:18px;margin-bottom:24px}.track{font-size:13px}.status{margin-left:4px;font-size:10px}h2{font-size:23px}.toolbar{gap:12px}.tabs button{padding:7px 10px;font-size:13px}table{font-size:13px}th,td{padding:12px}.metric{min-width:155px}.banner{margin:0 -5px}.scroll{border-radius:8px}
#board table,#board caption,#board thead,#board tbody{display:block;width:100%;white-space:normal}#board caption{padding:12px}#board thead tr{display:flex;flex-wrap:wrap;background:var(--soft);padding:4px 8px}#board th{border:0;padding:6px;font-size:11px}#board tbody tr{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));padding:14px 12px;gap:12px 8px;border-bottom:1px solid var(--line)}#board td{border:0;padding:0;text-align:left;min-width:0}#board td.rank{grid-column:1;grid-row:1}#board td.name{grid-column:2 / 7;grid-row:1;overflow-wrap:anywhere}#board .name .sub{margin-top:4px}#board td.metric{grid-column:1 / 5;grid-row:2;min-width:0;padding-right:12px}#board td:nth-child(7){grid-column:5 / 7;grid-row:2;text-align:right}#board td:nth-child(4){grid-column:1 / 3}#board td:nth-child(5){grid-column:3 / 5}#board td:nth-child(6){grid-column:5 / 7;text-align:right}#board td:nth-child(4):before,#board td:nth-child(5):before,#board td:nth-child(6):before{display:block;color:var(--mute);font-size:11px}#board td:nth-child(4):before{content:"Win"}#board td:nth-child(5):before{content:"Deal-in"}#board td:nth-child(6):before{content:"Deals"}}
</style>
</head>
<body>
<main>
<nav aria-label="Resources"><div><a href="https://github.com/vnguyen9/mjss-hongkong-mahjong-bench">Repository</a><a href="https://github.com/vnguyen9/mjss-hongkong-mahjong-bench/blob/main/SUBMITTING.md">Submit a bot</a></div><button id="theme" type="button" aria-label="Switch colour theme">Dark mode</button></nav>
<header><div class="banner">__BANNER__</div><p class="lede">A fair way to compare Hong Kong Mahjong players: bots today, LLMs and humans.</p><div class="meta">Version 1.1.0 · Protocol hkbench-1 · MIT licence</div><p class="meta">Made by the team behind <a href="https://mahjongsensei.co">Mahjong Sensei</a>, on the <a href="https://apps.apple.com/us/app/mahjong-sensei/id6792996894">App Store</a></p></header>
<div id="tracks" class="tracks" aria-label="Track"></div>
<h2>Leaderboard</h2>
<p id="summary"></p>
<div class="toolbar"><div id="tables" class="tabs" aria-label="Table"></div><div id="decks" class="decks" aria-label="Deck"></div></div>
<div id="board" aria-live="polite"></div>
<p class="explain">Whiskers show 95% confidence intervals. Bots whose intervals overlap share a rank. Each table has its own points scale, so points cannot be compared across tables. Select a column heading to sort the results.</p>
<details id="headtohead"><summary>View head-to-head results</summary><div id="matches"></div></details>
<footer id="foot"></footer>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
const D=JSON.parse(document.getElementById('data').textContent);
const state={track:'bots',table:'hk-hkma-v1',deck:'private',sort:'points_per_hand',direction:-1};
const host=id=>document.getElementById(id);
function el(tag,attrs={},kids=[]){const e=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>{if(k==='text')e.textContent=v;else e.setAttribute(k,v)});kids.forEach(k=>e.appendChild(k));return e}
const f=x=>x==null?'n/a':(x>=0?'+':'')+x.toFixed(2);
const pct=x=>x==null?'n/a':(100*x).toFixed(1)+'%';
function buttons(id,items,key){host(id).replaceChildren();items.forEach(it=>{const b=el('button',{type:'button','aria-pressed':String(state[key]===it.id),text:it.title,class:key==='track'?'track':''});if(key==='track')b.appendChild(el('span',{class:'status',text:it.id==='bots'?'Live':'Coming'}));b.onclick=()=>{state[key]=it.id;render()};host(id).appendChild(b)})}
function interval(r,lo,hi){const pos=v=>3+94*(v-lo)/(hi-lo||1),zero=pos(0),mean=pos(r.points_per_hand);const bar=el('span',{class:'interval','aria-hidden':'true'});bar.appendChild(el('span',{class:'mean-bar',style:'left:'+Math.min(zero,mean)+'%;width:'+Math.abs(mean-zero)+'%'}));bar.appendChild(el('span',{class:'zero',style:'left:'+zero+'%'}));bar.appendChild(el('span',{class:'whisker',style:'left:'+pos(r.ci95[0])+'%;width:'+(pos(r.ci95[1])-pos(r.ci95[0]))+'%'}));return bar}
function render(){
buttons('tracks',D.tracks,'track');buttons('tables',D.tables.slice().sort((a,b)=>Number(b.headline)-Number(a.headline)).map(t=>({id:t.id,title:t.rules_track})),'table');buttons('decks',[{id:'private',title:'Private deck'},{id:'public',title:'Public deck'}],'deck');
const table=D.tables.find(t=>t.id===state.table);
const descriptions={
'hk-hkma-v1':'HKMA Classical requires 3 faan to win and caps scoring at 10 faan. The discarder pays the whole hand, and flowers do not score.',
'hk-house-v1':'House rules count Seven Pairs as a hand and award points for flowers. Limit hands are graded, with scoring capped at 13 faan.',
'hk-chicken-v1':'Chicken hand uses HKMA Classical with a 0-faan minimum. A hand without a scoring pattern can win, and faan still determine the payout.'
};
host('summary').textContent=descriptions[state.table]||table.summary;
const rows=D.rows.filter(r=>r.table===state.table&&r.track===state.track&&r.seed_tag===state.deck);
rows.sort((a,b)=>{const av=state.sort==='bot'?a.bot.name:a[state.sort],bv=state.sort==='bot'?b.bot.name:b[state.sort];return state.direction*(typeof av==='string'?av.localeCompare(bv):av-bv)});
host('board').replaceChildren();
if(!rows.length){host('board').appendChild(el('div',{class:'empty'},[el('h2',{text:state.track==='bots'?'No results yet':D.tracks.find(t=>t.id===state.track).title+' are coming soon'}),el('p',{text:D.tracks.find(t=>t.id===state.track).note||'There are no runs for this table and deck.'})]))}
else{
const lo=Math.min(0,...rows.map(r=>r.ci95[0])),hi=Math.max(0,...rows.map(r=>r.ci95[1]));
const t=el('table'),head=el('tr'),body=el('tbody');t.appendChild(el('caption',{text:table.rules_track+' · '+state.deck+' deck · '+rows.length+' bots. Select a column heading to sort.'}));
[['Rank','rank'],['Bot','bot'],['Points a hand','points_per_hand'],['Win','win_rate'],['Deal-in','deal_in_rate'],['Deals','deals'],['Status','verification']].forEach(([label,key])=>{const th=el('th',{scope:'col','aria-sort':state.sort===key?(state.direction===1?'ascending':'descending'):'none'}),b=el('button',{text:label+(state.sort===key?(state.direction===1?' ↑':' ↓'):''),type:'button'});b.onclick=()=>{state.direction=state.sort===key?-state.direction:(key==='bot'||key==='verification'?1:-1);state.sort=key;render()};th.appendChild(b);head.appendChild(th)});
rows.forEach(r=>{const tr=el('tr',{class:r.bot.name==='Fu-2.3M-HKMA-1'?'featured':''});tr.appendChild(el('td',{class:'rank',text:r.rank}));tr.appendChild(el('td',{class:'name'},[el('span',{text:r.bot.name}),el('span',{class:'sub',text:'Trained on: '+r.bot.trained_on})]));const metric=el('td',{class:'metric'},[el('span',{class:'value',text:f(r.points_per_hand)}),interval(r,lo,hi),el('span',{class:'sub',text:'['+f(r.ci95[0])+', '+f(r.ci95[1])+']'})]);tr.appendChild(metric);tr.appendChild(el('td',{text:pct(r.win_rate)}));tr.appendChild(el('td',{text:pct(r.deal_in_rate)}));tr.appendChild(el('td',{text:r.deals.toLocaleString('en')}));tr.appendChild(el('td',{},[el('span',{class:'badge '+r.verification,text:r.verification})]));body.appendChild(tr)});
t.appendChild(el('thead',{},[head]));t.appendChild(body);host('board').appendChild(el('div',{class:'scroll',tabindex:'0','aria-label':'Leaderboard results'},[t]));}
const matches=D.head_to_head.filter(h=>h.table===state.table&&h.seed_tag===state.deck);host('headtohead').hidden=state.track!=='bots'||!matches.length;host('matches').replaceChildren();matches.forEach(h=>{const t=el('table'),head=el('tr');['Rank','Bot','Rating','95% interval'].forEach(label=>head.appendChild(el('th',{scope:'col',text:label})));t.appendChild(el('caption',{text:h.deals.toLocaleString('en')+' deals · '+h.seed_tag+' deck · '+h.verification+'. Bradley-Terry ratings use the Elo scale.'}));t.appendChild(el('thead',{},[head]));const body=el('tbody');h.bots.forEach(b=>body.appendChild(el('tr',{},[el('td',{text:b.rank}),el('td',{text:b.name}),el('td',{text:Math.round(b.rating)}),el('td',{text:'['+Math.round(b.ci95[0])+', '+Math.round(b.ci95[1])+']'})])));t.appendChild(body);host('matches').appendChild(el('div',{class:'scroll',tabindex:'0'},[t]))});
host('foot').textContent='Verified rows used private deals after a hidden-tile fair-play check. Unverified rows used public deals. Results updated '+D.generated_utc+'. Built with hkbench '+D.hkbench_version+'.';
}
const theme=host('theme');function setTheme(dark){document.documentElement.dataset.theme=dark?'dark':'light';theme.textContent=dark?'Light mode':'Dark mode';theme.setAttribute('aria-pressed',String(dark))}
setTheme(matchMedia('(prefers-color-scheme:dark)').matches);theme.onclick=()=>setTheme(document.documentElement.dataset.theme!=='dark');
render();
})();
</script>
</body>
</html>
"""
