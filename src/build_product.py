"""Render the product pages from docs/data/*.json: features, pricing, the dashboard for every game, and the API page.

Input : docs/data/weekly.json, benchmark.json, alerts.json, after_review_all.json, fans_all.json, overview.json
Output: docs/features.html, pricing.html, dashboards.html, api.html, docs/dash/<slug>.html
Every number on these pages is read from those JSON files. Prices and plan contents are set in PLANS below.
"""
import json, os
import build_site as bs
from build_site import E, pct, num, page, hbar, pair_columns, thumb, load, DOCS, CONTACT
from analyze import REASONS

PLANS = [  # name, price, per, who, lines, highlighted
    ("Free", "$0", "", "Look around", ["Open demo dashboards", "Method and limits, in full", "One sample digest"], False),
    ("Indie", "$29", "/mo", "1 game", ["Dashboard for your game", "After-the-review and timing charts", "Weekly email digest"], False),
    ("Studio", "$99", "/mo", "Up to 5 games", ["Everything in Indie", "Benchmark against similar games", "Discord and Slack alerts", "CSV export"], True),
    ("Custom", "Quote", "", "Publishers and deep dives", ["Written report with complaint topics", "Markets by review language", "Walkthrough call", "API access"], False),
]

bs.CSS += """
.chipf{display:inline-block;font-size:12px;border-radius:999px;padding:2px 10px;white-space:nowrap;font-weight:600}.chipf.v{background:rgba(240,129,82,.16);color:#f6a07a}.chipf.q{background:var(--chip);color:var(--text2)}.chipf.g{background:rgba(90,156,236,.16);color:#8fbdf5}
.bm{display:grid;grid-template-columns:230px minmax(0,1fr) 190px;gap:16px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line)}.bm:last-child{border-bottom:0}
.bm .bl b{display:block;font-size:14.5px}.bm .bl span{font-size:12.5px;color:var(--muted)}.bm .bv b{font-size:19px;font-variant-numeric:tabular-nums}.bm .bv span{display:block;font-size:12.5px;color:var(--muted)}
.bt{position:relative;height:10px;background:#0b1120;border-radius:5px;margin:0 9px}.bt i{position:absolute;top:-5px;width:3px;height:20px;border-radius:2px;margin-left:-1px}.bt i.pm{background:var(--orange)}.bt i.am{background:var(--muted)}
.bt b{position:absolute;top:-4px;width:18px;height:18px;border-radius:50%;background:var(--blue);margin-left:-9px;box-shadow:0 0 0 3px var(--surface)}
.lg i.dot{border-radius:50%}.lg i.tick{width:3px;height:14px;border-radius:2px;vertical-align:-2px}
@media (max-width:760px){.bm{grid-template-columns:minmax(0,1fr);gap:10px}}
.feat{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:18px}.fcard{background:linear-gradient(165deg,#18233b,#111a2c);border:1px solid var(--line);border-radius:18px;padding:22px;display:flex;flex-direction:column;gap:10px}
.fcard h3{font:600 18px var(--display);margin:0}.fcard p{margin:0;font-size:14.5px;color:var(--text2)}.fcard .ex{border-top:1px solid var(--line);padding-top:10px;font-size:13.5px;color:var(--text2)}.fcard .ex b{color:var(--text)}.fcard a{font-weight:600;font-size:14px;text-decoration:none}
.msg{background:#0b1120;border:1px solid var(--line);border-left:3px solid var(--orange);border-radius:8px;padding:10px 12px;font-size:13.5px}.msg b{display:block;margin-bottom:2px}
.plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px;align-items:stretch}.plan{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:24px;display:flex;flex-direction:column;gap:6px}
.plan.hl{border:2px solid var(--blue);background:linear-gradient(165deg,#1c2a47,#131c30)}.plan .pn{font:600 18px var(--display)}.plan .pp{font:700 38px var(--display);line-height:1.1}.plan .pp small{font:400 15px Inter,system-ui,sans-serif;color:var(--muted)}
.plan .pw{font-size:13.5px;color:var(--muted);margin-bottom:8px}.plan ul{list-style:none;margin:0 0 16px;padding:0;font-size:14.5px;color:var(--text2);flex:1}.plan li{padding:5px 0 5px 22px;position:relative}.plan li:before{content:"✓";position:absolute;left:0;color:var(--blue);font-weight:700}
.plan .btn{text-align:center;box-shadow:none}.plan .btn.ghost{background:transparent;border:1.5px solid var(--blue);color:#fff}.req select{font:inherit;color:var(--text);background:#0b1120;border:1px solid #3a4a6b;border-radius:8px;padding:11px 12px;min-height:44px;width:100%}
.find{font:inherit;color:var(--text);background:#0b1120;border:1px solid #3a4a6b;border-radius:10px;padding:11px 14px;min-height:44px;width:100%;max-width:420px}
.cs{overflow-x:auto}@media (max-width:760px){.cs svg{min-width:600px}}
pre{background:#0b1120;border:1px solid var(--line);border-radius:10px;padding:14px;overflow-x:auto;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;color:var(--text2)}code{font:13px ui-monospace,Menlo,Consolas,monospace;color:#d7deea}
"""

FLAG = {"volume": ("Review spike", "v"), "more_negative": ("More negative than usual", "v"), "more_positive": ("More positive than usual", "g")}
hrs = lambda v: "–" if v is None else f"{v:.0f} h"
def ordinal(n): return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
def chips(flags): return "".join(f'<span class="chipf {FLAG[f][1]}">{FLAG[f][0]}</span> ' for f in flags) or '<span class="chipf q">Nothing unusual</span>'


def week_chart(weeks, width=760, height=270):
    """Bars: reviews per week (flagged weeks in orange). Line underneath: negative share of that week's reviews."""
    L, R, T = 46, 46, 14; bh, gap, lh = 140, 34, 52; pw = width - L - R; slot = pw / len(weeks); bw = max(slot - 4, 3)
    vmax = max(w["reviews"] for w in weeks) or 1
    s = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Reviews per week for the last {len(weeks)} weeks, with the negative share of each week below">',
         f'<text class="t" x="{L - 6}" y="{T + 8}" text-anchor="end">{vmax:,}</text><text class="t" x="{L - 6}" y="{T + bh}" text-anchor="end">0</text><line x1="{L}" x2="{L + pw}" y1="{T + bh}" y2="{T + bh}" stroke="var(--grid)"/>']
    prev = None
    for i, w in enumerate(weeks):
        x = L + i * slot + (slot - bw) / 2; h = max(w["reviews"] / vmax * (bh - 10), 1 if w["reviews"] else 0)
        tip = f'Week of {w["week"]}: {w["reviews"]:,} reviews, {pct(w["negative_share"])} negative' + (" · " + ", ".join(FLAG[f][0].lower() for f in w["flags"]) if w["flags"] else "")
        s.append(f'<rect x="{x:.1f}" y="{T + bh - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" fill="{"var(--orange)" if w["flags"] else "var(--blue)"}"><title>{E(tip)}</title></rect>')
        mon = w["week"][5:7]
        if mon != prev and int(w["week"][8:10]) <= 7: s.append(f'<text class="t" x="{x:.1f}" y="{T + bh + 16}">{["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][int(mon) - 1]}</text>')
        prev = mon
    y0 = T + bh + gap; Y = lambda v: y0 + (1 - v) * lh
    s.append(f'<line x1="{L}" x2="{L + pw}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="var(--grid)"/><line x1="{L}" x2="{L + pw}" y1="{Y(1):.1f}" y2="{Y(1):.1f}" stroke="var(--grid)" stroke-dasharray="2 4"/>'
             f'<text class="t" x="{L - 6}" y="{Y(1) + 4:.1f}" text-anchor="end">100%</text><text class="t" x="{L - 6}" y="{Y(0) + 4:.1f}" text-anchor="end">0%</text>')
    seg = []; last = None
    for i, w in enumerate(weeks + [None]):
        ok = w is not None and w["reviews"] >= 30 and w["negative_share"] is not None
        if ok: seg.append((L + i * slot + slot / 2, Y(w["negative_share"]))); last = (seg[-1], w["negative_share"])
        elif seg:
            s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in seg)}" fill="none" stroke="var(--text)" stroke-width="1.8" stroke-linejoin="round"/>' if len(seg) > 1 else f'<circle cx="{seg[0][0]:.1f}" cy="{seg[0][1]:.1f}" r="2" fill="var(--text)"/>'); seg = []
    if last: s.append(f'<text class="v" x="{min(last[0][0] + 6, width - 40):.1f}" y="{last[0][1] + 4:.1f}">{pct(last[1])}</text>')
    return "".join(s) + "</svg>"


def bench_rows(b, total):
    out = []
    for m in b["measures"]:
        if m["value"] is None: continue
        f = hrs if m["key"] == "fan_review_hours" else pct; span = (m["all_max"] - m["all_min"]) or 1; pos = lambda v: f"{(v - m['all_min']) / span * 100:.1f}%"
        out.append(f'<div class="bm"><div class="bl"><b>{E(m["label"])}</b><span>{E(m["meaning"])}</span></div>'
                   f'<div class="bt" role="img" aria-label="{E(m["label"])}: this game {f(m["value"])}, similar games {f(m["peer_median"])}, all games {f(m["all_median"])}"><i class="am" style="left:{pos(m["all_median"])}" title="All {total} games, median: {f(m["all_median"])}"></i>'
                   + (f'<i class="pm" style="left:{pos(m["peer_median"])}" title="Similar games, median: {f(m["peer_median"])}"></i>' if m["peer_median"] is not None else "")
                   + f'<b style="left:{pos(m["value"])}" title="This game: {f(m["value"])}"></b></div>'
                   f'<div class="bv"><b>{f(m["value"])}</b><span>{ordinal(m["rank"])} lowest of {m["of"]} · similar games {f(m["peer_median"])}</span></div></div>')
    return "".join(out)


def timing_chart(f, width=720):
    rows = [("Recommended", f["recommended"], "var(--blue)"), ("Not recommended", f["not_recommended"], "var(--orange)")]
    xmax = max(r[1]["p75"] or 0 for r in rows) * 1.15 or 1; L = 140; pw = width - L - 70; X = lambda v: L + v / xmax * pw
    s = [f'<svg viewBox="0 0 {width} 96" role="img" aria-label="Hours played when the review was written: middle half and median, recommended against not recommended">']
    for i, (lab, t, col) in enumerate(rows):
        if not t["n"] or t["median"] is None: continue
        y = 14 + i * 38
        s.append(f'<text x="{L - 10}" y="{y + 13}" text-anchor="end">{lab}</text><rect x="{L}" y="{y + 4}" width="{pw}" height="10" rx="5" fill="#0b1120"/>'
                 f'<rect x="{X(t["p25"]):.1f}" y="{y + 4}" width="{max(X(t["p75"]) - X(t["p25"]), 2):.1f}" height="10" rx="5" fill="{col}" opacity=".55"><title>Middle half: {t["p25"]} to {t["p75"]} hours</title></rect>'
                 f'<circle cx="{X(t["median"]):.1f}" cy="{y + 9}" r="7" fill="{col}" stroke="var(--surface)" stroke-width="2"><title>Median: {t["median"]} hours</title></circle>'
                 f'<text class="v" x="{X(t["p75"]) + 10:.1f}" y="{y + 13}">{t["median"]:.0f} h</text>')
    return "".join(s) + "</svg>"


def dash_page(w, b, a, f, o, ov, total):
    l = w["latest"]
    kp = lambda lab, v, sub: f'<div class="kpi"><div class="l">{lab}</div><b>{v}</b><div class="s">{sub}</div></div>'
    mv = {m["key"]: m for m in b["measures"]}
    kpis = (kp("Reviews", num(w["reviews"]), f"{pct(w['negative_share'])} negative") + kp("Last 4 weeks", num(w["last4"]["reviews"]), f"{pct(w['last4']['negative_share'])} negative")
            + kp("Critics who stopped", pct(a["negative"]["walk_rate"]), f"similar games: {pct(mv['critics_stopped']['peer_median'])}") + kp("Fans who stopped", pct(a["positive"]["walk_rate"]), f"similar games: {pct(mv['fans_stopped']['peer_median'])}"))
    recent = "".join(f"<tr><td>{E(r['week'])}</td><td>{num(r['reviews'])}</td><td>{r['usual_reviews']:,.0f}</td><td>{pct(r['negative_share'])}</td><td>{pct(r['usual_negative_share'])}</td><td class='l'>{chips(r['flags']) if r['flags'] else ''}</td></tr>" for r in reversed(w["weeks"][-8:]))
    after = pair_columns([dict(label=r["bucket"], a=r["positive"].get("walk_rate"), b=r["negative"].get("walk_rate"), tip=f"{r['bucket']}: {r['positive']['n']:,} recommended, {r['negative']['n']:,} not recommended") for r in a["by_hours"]])
    if o:
        top = sorted(((c, s) for c, s in o["reason_shares"].items() if c != "OTHER"), key=lambda t: -t[1])[:6]
        trows = [dict(label=REASONS[c], value=sh, tip=REASONS[c] + ": " + pct(sh, 1) + " of labeled negative reviews; " + pct(o["reason_walk"].get(c)) + " of these reviewers stopped") for c, sh in top]
        topics = ('<div class="card"><div class="cs">' + hbar(trows, color="var(--orange)", width=720, label_w=220) + '</div></div>'
                  + f'<p class="note">Share of labeled negative reviews. Which of these go with leaving is in the <a href="../games/{E(w["slug"])}.html">full report</a>.</p>')
    else:
        topics = '<div class="card"><p style="margin:0">Complaint topics aren\'t labeled for this game yet. That step reads every negative review with a language model, so it runs on request. <a href="../pricing.html">See Custom</a>.</p></div>'
    s = E(w["slug"])
    body = f"""<div class="wrap">
<div class="kicker"><a href="../dashboards.html" style="color:inherit">Dashboards</a> · {E(b["family"])}</div>
<h1>{E(w["name"])}</h1>
<p class="meta">{E(w["genre"])} · public Steam reviews in every language · data as of {E(w["snapshot"])}</p>
<div class="kpis">{kpis}</div>
<section id="week" style="margin-top:28px"><div class="shead"><h2>Reviews, week by week</h2><div>{chips(l["flags"])}</div></div>
<p class="q">Week of {E(l["week"])}: {num(l["reviews"])} new reviews (a usual week: {l["usual_reviews"]:,.0f}). {pct(l["negative_share"])} were negative (usual: {pct(l["usual_negative_share"])}).</p>
<div class="card"><div class="legend"><span><i class="sw-b"></i>Reviews that week</span><span><i class="sw-o"></i>Flagged week</span><span><i style="background:var(--text);height:2px;border-radius:0;vertical-align:4px"></i>Negative share (weeks with 30+ reviews)</span></div><div class="cs">{week_chart(w["weeks"])}</div></div>
<details><summary>Last 8 weeks as a table</summary><div class="scroll"><table><thead><tr><th>Week starting</th><th>Reviews</th><th>Usual week</th><th>Negative</th><th>Usual</th><th class="l">Flag</th></tr></thead><tbody>{recent}</tbody></table></div>
<p class="note">"Usual" is the 8 weeks before. A spike is 50+ reviews and at least double the usual week. A shift is 15+ points away from the usual negative share. Spikes often line up with sales and updates.</p></details></section>
<section id="bench"><h2>Against similar games</h2>
<p class="q">Where this game sits among the {total} games here.</p>
<div class="card"><div class="legend lg"><span><i class="dot sw-b"></i>This game</span><span><i class="tick sw-o"></i>Similar games (median)</span><span><i class="tick sw-g"></i>All {total} games (median)</span></div>{bench_rows(b, total)}</div>
<p class="note">Similar games ({E(b["family"])}): {E(", ".join(b["peers"]))}. Each track runs from the lowest to the highest game. This compares the games on this site, not all of Steam.</p></section>
<section id="after"><h2>After the review</h2>
<p class="q">Who logged under one more hour after reviewing, by hours played at the review.</p>
<div class="card"><div class="tlegend" style="margin-bottom:10px"><span>{thumb(True)}Recommended, stopped</span><span>{thumb(False)}Not recommended, stopped</span></div><div class="cs">{after}</div></div>
<p class="note">Reviews at least 30 days old. Under 2 hours sits inside Steam's refund window.</p></section>
<section id="timing"><h2>When reviews get written</h2>
<p class="q">Hours played at the moment of the review. Dot = median, band = middle half of reviewers.</p>
<div class="card"><div class="cs">{timing_chart(f)}</div></div></section>
<section id="topics"><h2>What critics name</h2>{topics}</section>
<section id="get"><h2>Take it with you</h2>
<div class="dl"><a href="../digest/{s}.html">This week's email digest</a><a href="../export/{s}_weekly.csv">Weekly numbers (CSV)</a><a href="../export/{s}_summary.csv">Summary (CSV)</a><a href="../api/v1/games/{s}.json">Everything (JSON)</a></div>
<div class="caveat">These are reviewers, not all players. A pattern here isn't proof of cause. Stopping late can just mean finishing the game. <a href="../method.html">Method &amp; limits</a></div></section>
</div>"""
    return page(f"{w['name']} dashboard — Player Signals", body, ov, depth=1, desc=f"Weekly Steam review numbers for {w['name']}: review volume, negative share, behaviour after the review, and a benchmark against similar games.")


FORM_JS = """<script>(function(){var f=document.getElementById('planform');if(!f)return;
document.querySelectorAll('[data-plan]').forEach(function(a){a.addEventListener('click',function(){document.getElementById('pf-plan').value=a.getAttribute('data-plan')})});
f.addEventListener('submit',function(e){e.preventDefault();var d=new FormData(f),v=function(k){return String(d.get(k)||'')};
var body='Plan: '+v('plan')+'\\nName: '+v('name')+'\\nStudio: '+v('studio')+'\\nGame: '+v('game')+'\\nEmail: '+v('email');
document.getElementById('pffb').hidden=false;
window.location.href='mailto:'+f.getAttribute('data-to')+'?subject='+encodeURIComponent('Player Signals '+v('plan')+' plan: '+v('game'))+'&body='+encodeURIComponent(body)})})();</script>"""
FIND_JS = """<script>(function(){var q=document.getElementById('find');if(!q)return;q.addEventListener('input',function(){var t=q.value.toLowerCase();
document.querySelectorAll('[data-name]').forEach(function(c){c.hidden=c.getAttribute('data-name').indexOf(t)<0});
document.querySelectorAll('[data-fam]').forEach(function(s){s.hidden=!s.querySelector('[data-name]:not([hidden])')})})})();</script>"""


def dashboards_page(wk, bm, ar, ov):
    fams = {}
    for w in wk["games"]: fams.setdefault(bm[w["slug"]]["family"], []).append(w)
    def card(w):
        a = ar[w["slug"]]
        return (f'<a class="gcard lift" data-name="{E((w["name"] + " " + w["genre"]).lower())}" href="dash/{E(w["slug"])}.html"><div class="gh"><div><div class="gn">{E(w["name"])}</div><div class="gs">{E(w["genre"])}</div></div><div class="gr">{num(w["reviews"])} reviews</div></div>'
                f'<div><div class="grow">{thumb(True)}<b style="color:#5a9cec">{pct(a["positive"]["walk_rate"])}</b><div class="tr"><i style="width:{min(a["positive"]["walk_rate"] * 110, 100):.0f}%;background:#5a9cec"></i></div></div>'
                f'<div class="grow">{thumb(False)}<b style="color:#f08152">{pct(a["negative"]["walk_rate"])}</b><div class="tr"><i style="width:{min(a["negative"]["walk_rate"] * 110, 100):.0f}%;background:#f08152"></i></div></div></div>'
                f'<div class="gfacts"><div><small>Negative reviews</small><b>{pct(w["negative_share"])}</b></div><div><small>Latest week</small><b>{num(w["latest"]["reviews"])} reviews</b></div></div><div>{chips(w["latest"]["flags"])}</div></a>')
    secs = "".join(f'<section data-fam><div class="shead"><h2>{E(fam)}</h2><span class="meta">{len(ws)} games</span></div><div class="gcards">{"".join(card(w) for w in sorted(ws, key=lambda w: -w["reviews"]))}</div></section>' for fam, ws in sorted(fams.items(), key=lambda t: -len(t[1])))
    n = len(wk["games"]); flagged = sum(1 for w in wk["games"] if w["latest"]["flags"])
    body = f"""<div class="wrap"><h1>Dashboards</h1>
<p class="lede">{n} Steam games, one page each. {flagged} had an unusual week in the latest data.</p>
<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin-top:14px"><input class="find" id="find" type="search" placeholder="Find a game or genre" aria-label="Find a game or genre">
<div class="tlegend"><span>{thumb(True)}Recommended, stopped</span><span>{thumb(False)}Not recommended, stopped</span></div></div>
{secs}
<section><div class="card"><p style="margin:0">These are open demos. Want this for your own game? <a href="pricing.html">See the plans</a> or <a href="index.html#request">request a report</a>.</p></div></section></div>{FIND_JS}"""
    return page("Dashboards — Player Signals", body, ov, desc=f"Weekly Steam review dashboards for {n} games: review volume, negative share, behaviour after the review and a benchmark against similar games.")


def features_page(wk, bm, ar, fans, alerts, ov):
    n = len(wk["games"]); ex = next(w for w in wk["games"] if w["slug"] == "payday-3"); b = bm[ex["slug"]]; a = ar[ex["slug"]]; f = fans[ex["slug"]]; o = next(x for x in ov if x["slug"] == ex["slug"])
    mv = {m["key"]: m for m in b["measures"]}; al = next((x for x in alerts["alerts"] if x["latest"] and "volume" in x["flags"]), alerts["alerts"][0])
    fc = lambda h, p, exh, link, lab, chip: f'<div class="fcard"><div><span class="chipf {chip[1]}">{chip[0]}</span></div><h3>{h}</h3><p>{p}</p><div class="ex">{exh}</div><a href="{link}">{lab} →</a></div>'
    live, six = (f"Live for {n} games", "g"), ("Live for 6 games · others on request", "q")
    analyze = (fc("Sentiment and topics", "What critics name, sorted into eleven complaint types, in the review's own language.", f"<b>{E(ex['name'])}:</b> top complaint: {E(o['top_reason'])} ({pct(o['top_reason_share'])} of negative reviews).", f"games/{ex['slug']}.html", "See a full report", six)
               + fc("Quit signals", "Who kept playing after reviewing and who stopped, at every stage of play.", f"<b>{E(ex['name'])}:</b> {pct(a['negative']['walk_rate'])} of critics stopped, against {pct(a['positive']['walk_rate'])} of fans.", "quit.html", "Why players quit", live)
               + fc("Review timing", "How many hours in players are when they speak up.", f"<b>{E(ex['name'])}:</b> fans review at a median of {f['recommended']['median']:.0f} hours, critics at {f['not_recommended']['median']:.0f}.", "fans.html", "When fans review", live)
               + fc("Competitor benchmark", "Your numbers next to similar games and the whole set.", f"<b>{E(ex['name'])}:</b> {pct(mv['critics_stopped']['value'])} of critics stopped. Similar games: {pct(mv['critics_stopped']['peer_median'])}.", f"dash/{ex['slug']}.html#bench", "See a benchmark", live))
    deliver = (fc("Web dashboard", "One page per game, rebuilt every week.", f"<b>{E(ex['name'])}:</b> {num(ex['latest']['reviews'])} reviews in the latest week, {pct(ex['latest']['negative_share'])} negative.", f"dash/{ex['slug']}.html", "Open a dashboard", live)
               + fc("Email digest", "The week in one short email: what changed and what didn't.", "A ready-to-send digest is built for every game, every week.", f"digest/{ex['slug']}.html", "Read a sample digest", ("Built weekly · sent on request", "q"))
               + fc("Discord and Slack alerts", "A message in your channel when a week stands out.", f'<div class="msg"><b>{E(al["title"])}</b>{E(al["text"])}</div>', f"dash/{al['slug']}.html#week", "See the week behind it", ("Ready · needs your webhook", "q"))
               + fc("CSV and API export", "Every number as a file your own team can load.", "<code>api/v1/games/&lt;game&gt;.json</code> and two CSV files per game.", "api.html", "API and export", live))
    body = f"""<div class="hero-bg"><div class="glow g1" aria-hidden="true"></div><div class="wrap" style="position:relative;padding-bottom:0">
<h1 class="big" style="max-width:820px">Know what your Steam reviewers did next. Every week.</h1>
<p class="lede" style="margin-top:16px">Player Signals reads every public review of a game and tells your team four things, four ways.</p>
<p style="margin-top:20px"><a class="btn" href="dashboards.html">Open a dashboard</a> &nbsp; <a href="pricing.html" style="font-weight:600">See pricing</a></p></div></div>
<div class="wrap" style="padding-top:8px">
<section><div class="shead"><h2>What gets analyzed</h2></div><div class="feat">{analyze}</div></section>
<section><div class="shead"><h2>How it reaches you</h2></div><div class="feat">{deliver}</div></section>
<section><div class="caveat">What this can't do: reviews describe only the players who wrote one, and nothing here proves that a complaint caused a player to leave. <a href="method.html">Method &amp; limits</a></div></section>
</div>"""
    return page("Features — Player Signals", body, ov, desc="What Player Signals analyzes in Steam reviews and how it reaches a studio: dashboard, email digest, Discord and Slack alerts, CSV and API export.")


def pricing_page(wk, ov):
    def plan(name, price, per, who, lines, hl):
        btn = ('<a class="btn ghost" href="dashboards.html">Open the demos</a>' if name == "Free" else f'<a class="btn{"" if hl else " ghost"}" href="#ask" data-plan="{name}">{"Ask for a quote" if name == "Custom" else "Request access"}</a>')
        return f'<div class="plan{" hl" if hl else ""}">{"<div><span class=chipf style=background:var(--blue);color:#090e19>Most teams start here</span></div>" if hl else ""}<div class="pn">{name}</div><div class="pp">{price}<small>{per}</small></div><div class="pw">{who}</div><ul>{"".join(f"<li>{E(x)}</li>" for x in lines)}</ul>{btn}</div>'
    opts = "".join(f"<option>{p[0]}</option>" for p in PLANS if p[0] != "Free")
    body = f"""<div class="wrap"><h1>Pricing</h1>
<p class="lede">Start with the free demos. Pay when you want your own game on it.</p>
<div class="plans" style="margin-top:26px">{"".join(plan(*p) for p in PLANS)}</div>
<div class="caveat">Early access: plans are set up by hand for now, and nothing is charged on this site. Request one and I'll email you back.</div>
<section><h2>Good to know</h2><div class="grid2">
<div class="team"><h3>Which games work?</h3><div class="note">Any paid Steam game with public reviews. Free-to-play games don't work yet: Steam's review data for them is unreliable.</div></div>
<div class="team"><h3>Is a monthly plan worth it for my game?</h3><div class="note">It fits games that still get new reviews every week. For an older, quieter game, a one-time Custom report is the better buy.</div></div>
<div class="team"><h3>Where does the data come from?</h3><div class="note">Only public Steam reviews. No review text or reviewer IDs are published, and nothing needs access to your accounts.</div></div>
<div class="team"><h3>What's in a Custom report?</h3><div class="note">Everything on a dashboard, plus complaint topics from every negative review and a breakdown by review language. <a href="games/monster-hunter-wilds.html">See one</a>.</div></div>
</div></section>
<section id="ask"><div class="req"><div class="rt"><h2>Request a plan</h2><p>Tell me the game and the plan. I'll email you back.</p></div>
<form id="planform" data-to="{CONTACT}">
<div class="f"><label for="pf-plan">Plan</label><select id="pf-plan" name="plan">{opts}</select></div>
<div class="f"><label for="pf-name">Name</label><input id="pf-name" name="name" type="text" autocomplete="name" required></div>
<div class="f"><label for="pf-studio">Studio</label><input id="pf-studio" name="studio" type="text" autocomplete="organization" required></div>
<div class="f"><label for="pf-game">Game</label><input id="pf-game" name="game" type="text" required></div>
<div class="f"><label for="pf-email">Email address</label><input id="pf-email" name="email" type="email" autocomplete="email" required></div>
<div class="f"><button class="btn" type="submit">Request access</button></div>
<div class="fb" id="pffb" role="status" hidden>If your email app did not open, write to {CONTACT}.</div></form></div></section></div>{FORM_JS}"""
    return page("Pricing — Player Signals", body, ov, desc="Player Signals plans: free demo dashboards, Indie and Studio monthly plans, and custom reports.")


def api_page(wk, ov):
    ex = wk["games"][0]["slug"]
    rows = "".join(f"<tr><td class='l'><code>{k}</code></td><td class='l'>{v}</td></tr>" for k, v in [
        ("reviews, negative_share, snapshot", "All reviews fetched, the share not recommended, and the date of the data."),
        ("after_review", "Who stopped and who kept playing after reviewing, overall and by hours played at the review."),
        ("review_timing", "Hours played when the review was written: 25th percentile, median, 75th."),
        ("benchmark", "Each measure with the game's value, its rank, and the medians for similar games and all games."),
        ("complaints", "Complaint topics with share and stopped rate. <code>null</code> for games that are not labeled yet."),
        ("weekly, flagged_weeks", "52 weeks of review counts and negative share, and the weeks that stood out.")])
    games = "".join(f"<tr><td class='l'>{E(w['name'])}</td><td class='l'><a href='api/v1/games/{E(w['slug'])}.json'>JSON</a> · <a href='export/{E(w['slug'])}_weekly.csv'>weekly CSV</a> · <a href='export/{E(w['slug'])}_summary.csv'>summary CSV</a></td></tr>" for w in wk["games"])
    body = f"""<div class="wrap"><h1>API and export</h1>
<p class="lede">Every number on a dashboard, as files. Read-only, no key needed for the demo games.</p>
<section style="margin-top:24px"><h2>Two addresses</h2>
<pre>GET api/v1/index.json            the list of games
GET api/v1/games/{E(ex)}.json   everything for one game</pre>
<p class="note">Plain static files, rebuilt with each weekly run. Try the <a href="api/v1/index.json">index</a>.</p></section>
<section><h2>What's in a game file</h2><div class="scroll"><table><thead><tr><th>Field</th><th class="l">What it holds</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Rates are fractions (0.25 = 25%). A rate is <code>null</code> when fewer than 30 reviews stand behind it. No review text and no reviewer or review IDs, anywhere.</p></section>
<section><h2>Files by game</h2><div class="scroll"><table><thead><tr><th>Game</th><th class="l">Files</th></tr></thead><tbody>{games}</tbody></table></div></section></div>"""
    return page("API and export — Player Signals", body, ov, desc="Read-only JSON and CSV files for every Player Signals game.")


if __name__ == "__main__":
    ov = load("overview.json"); wk = load("weekly.json"); alerts = load("alerts.json")
    bm = {g["slug"]: g for g in load("benchmark.json")["games"]}; ar = {g["slug"]: g for g in load("after_review_all.json")["games"]}; fans = {g["slug"]: g for g in load("fans_all.json")["games"]}
    ovs = {o["slug"]: o for o in ov}; total = len(wk["games"])
    os.makedirs(os.path.join(DOCS, "dash"), exist_ok=True)
    W = lambda name, html_: open(os.path.join(DOCS, name), "w").write(html_)
    for w in wk["games"]: W(os.path.join("dash", w["slug"] + ".html"), dash_page(w, bm[w["slug"]], ar[w["slug"]], fans[w["slug"]], ovs.get(w["slug"]), ov, total))
    W("dashboards.html", dashboards_page(wk, bm, ar, ov)); W("features.html", features_page(wk, bm, ar, fans, alerts, ov)); W("pricing.html", pricing_page(wk, ov)); W("api.html", api_page(wk, ov))
    print("built", total + 4, "product pages")
