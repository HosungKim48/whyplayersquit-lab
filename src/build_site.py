"""Render the static site (docs/) from docs/data/*.json. No number is typed by hand here:
every figure in the HTML is read from the JSON written by analyze.py, audit.py and cost.py."""
import html, json, os
from analyze import REASONS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS = os.path.join(ROOT, "docs"); DATA = os.path.join(DOCS, "data")
REPO = "https://github.com/HosungKim48/whyplayersquit-lab"
E = html.escape


def pct(x, d=0): return "–" if x is None else f"{x * 100:.{d}f}%"
def num(x): return "–" if x is None else f"{x:,}"
def load(name):
    p = os.path.join(DATA, name)
    return json.load(open(p)) if os.path.exists(p) else None


CSS = """
:root{color-scheme:light;--bg:#f7f6f3;--surface:#fcfcfb;--line:#e4e2dc;--text:#0b0b0b;--text2:#52514e;--muted:#8a887f;
--blue:#2a78d6;--blue-soft:#cde2fb;--orange:#eb6834;--grid:#e9e7e1;--heat:42,120,214}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#121211;--surface:#1a1a19;--line:#33332f;--text:#f0efec;--text2:#c3c2b7;--muted:#8f8e85;
--blue:#3987e5;--blue-soft:#184f95;--orange:#d95926;--grid:#2a2a27;--heat:57,135,229}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--blue)}header.site{border-bottom:1px solid var(--line);background:var(--surface)}
header.site div{max-width:980px;margin:0 auto;padding:14px 20px;display:flex;gap:20px;align-items:baseline;flex-wrap:wrap}
header.site .brand{font-weight:700;color:var(--text);text-decoration:none}header.site nav a{margin-right:14px;font-size:14px}
main{max-width:980px;margin:0 auto;padding:28px 20px 60px}h1{font-size:32px;line-height:1.2;margin:8px 0 6px}h2{font-size:22px;margin:44px 0 8px}
h3{font-size:16px;margin:22px 0 6px}.lede{font-size:18px;color:var(--text2);max-width:760px}.kicker{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:16px 0}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px}.tile b{display:block;font-size:28px;line-height:1.15}
.tile span{font-size:13px;color:var(--text2)}.note{font-size:14px;color:var(--text2)}.caveat{border-left:3px solid var(--orange);padding:6px 14px;margin:14px 0;font-size:14px;color:var(--text2);background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}
th:first-child,td:first-child{text-align:left}th{font-weight:600;color:var(--text2);font-size:13px}.scroll{overflow-x:auto}
td.l,th.l{text-align:left}.bottom li{margin:6px 0}.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:14px}
svg{display:block;width:100%;height:auto}svg text{font:12px system-ui,-apple-system,sans-serif;fill:var(--text2)}svg .v{fill:var(--text);font-weight:600}
svg .t{fill:var(--muted);font-size:11px}.legend{font-size:13px;color:var(--text2);display:flex;gap:16px;flex-wrap:wrap;margin:4px 0 8px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}.sw-b{background:var(--blue)}.sw-o{background:var(--orange)}.sw-g{background:var(--muted)}
details{margin:8px 0}summary{cursor:pointer;font-size:14px;color:var(--text2)}blockquote{margin:6px 0;padding:4px 14px;border-left:3px solid var(--line);color:var(--text2);font-size:15px}
.tag{display:inline-block;font-size:12px;border:1px solid var(--line);border-radius:20px;padding:1px 9px;color:var(--text2);margin-left:6px}
footer{border-top:1px solid var(--line);font-size:13px;color:var(--muted)}footer div{max-width:980px;margin:0 auto;padding:18px 20px}
.games{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.games a.card{text-decoration:none;color:var(--text);display:block;margin:0}
.games a.card:hover{border-color:var(--blue)}.games b{font-size:17px}
@media (max-width:520px){.grid2{grid-template-columns:1fr}h1{font-size:26px}}
"""


def page(title, body, depth=0, desc=""):
    up = "../" * depth
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><style>{CSS}</style></head><body>
<header class="site"><div><a class="brand" href="{up}index.html">Why Players Quit · Lab</a>
<nav><a href="{up}index.html">Overview</a><a href="{up}index.html#reports">Game reports</a><a href="{up}method.html">Method &amp; limits</a><a href="{REPO}">Code &amp; data</a></nav></div></header>
<main>{body}</main>
<footer><div>A free, public student research project built only from public Steam data. Not affiliated with Valve or with any studio or publisher named here.
Reviews describe only the players who chose to write one. Nothing on this site shows that one thing caused another. No raw review text or reviewer IDs are published.</div></footer>
</body></html>"""


# ---------- SVG helpers (single axis each; hover text via <title>) ----------
def hbar(rows, color="var(--blue)", width=560, label_w=190, fmt=pct, xmax=None, ref=None, ref_label="", whisk=False):
    """rows: dicts with label, value, tip and optionally lo/hi (confidence interval)."""
    rows = [r for r in rows if r["value"] is not None]
    if not rows: return "<p class='note'>Not enough reviews to show this chart.</p>"
    bh, gap, top = 20, 9, 22 if ref is not None else 6
    h = top + len(rows) * (bh + gap) + 6; pw = width - label_w - 58
    xmax = xmax or max([r.get("hi") or r["value"] for r in rows] + [ref or 0]) * 1.08 or 1
    s = [f'<svg viewBox="0 0 {width} {h}" role="img">']
    if ref is not None:
        x = label_w + ref / xmax * pw
        s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top-4}" y2="{h-4}" stroke="var(--muted)" stroke-dasharray="3 3"/><text class="t" x="{x:.1f}" y="11" text-anchor="middle">{E(ref_label)} {fmt(ref)}</text>')
    for i, r in enumerate(rows):
        y = top + i * (bh + gap); w = max(r["value"] / xmax * pw, 1)
        s.append(f'<g><title>{E(r["tip"])}</title><text x="{label_w-8}" y="{y+14}" text-anchor="end">{E(r["label"])}</text>'
                 f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bh}" rx="4" fill="{color}"/>')
        end = label_w + w
        if whisk and r.get("lo") is not None:
            x1, x2 = label_w + r["lo"] / xmax * pw, label_w + r["hi"] / xmax * pw; end = x2
            s.append(f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y+bh/2}" y2="{y+bh/2}" stroke="var(--text)" stroke-width="1.5"/>')
        s.append(f'<text class="v" x="{end+6:.1f}" y="{y+14}">{fmt(r["value"])}</text></g>')
    return "".join(s) + "</svg>"


def columns(rows, color="var(--blue)", width=460, height=210, fmt=pct):
    rows = [r for r in rows if r["value"] is not None]
    if not rows: return "<p class='note'>Not enough reviews to show this chart.</p>"
    top, bot = 22, 30; ph = height - top - bot; vmax = max(r["value"] for r in rows) * 1.05 or 1
    slot = width / len(rows); bw = min(slot - 14, 64); s = [f'<svg viewBox="0 0 {width} {height}" role="img">',
         f'<line x1="0" x2="{width}" y1="{top+ph}" y2="{top+ph}" stroke="var(--grid)"/>']
    for i, r in enumerate(rows):
        x = i * slot + (slot - bw) / 2; bh = max(r["value"] / vmax * ph, 1); y = top + ph - bh
        s.append(f'<g><title>{E(r["tip"])}</title><rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{color}"/>'
                 f'<text class="v" x="{x+bw/2:.1f}" y="{y-6:.1f}" text-anchor="middle">{fmt(r["value"])}</text>'
                 f'<text x="{x+bw/2:.1f}" y="{height-10}" text-anchor="middle">{E(r["label"])}</text></g>')
    return "".join(s) + "</svg>"


def timeline(monthly, patches, release):
    """Two stacked panels sharing the month axis: review volume (bars) and negative share (line)."""
    n = len(monthly)
    if n < 2: return ""
    W, L, R = 940, 44, 12; pw = W - L - R; step = pw / n
    h1, h2, gap, top = 110, 130, 34, 16; H = top + h1 + gap + h2 + 34
    vmax = max(m["reviews"] for m in monthly) or 1
    s = [f'<svg viewBox="0 0 {W} {H}" role="img">', f'<text class="t" x="{L}" y="11">Reviews per month (blue) and negative reviews (orange)</text>']
    for i, m in enumerate(monthly):
        x = L + i * step; bw = max(step - 2, 1)
        b1 = m["reviews"] / vmax * h1; b2 = m["negative"] / vmax * h1
        tip = f'{m["month"]}: {m["reviews"]:,} reviews, {m["negative"]:,} negative ({pct(m["negative_share"])})' + (f' · official patch posts: {len(m["patches"])}' if m["patches"] else "")
        s.append(f'<g><title>{E(tip)}</title><rect x="{x:.1f}" y="{top+h1-b1:.1f}" width="{bw:.1f}" height="{max(b1,1):.1f}" rx="2" fill="var(--blue)"/>'
                 f'<rect x="{x:.1f}" y="{top+h1-b2:.1f}" width="{bw:.1f}" height="{max(b2,1):.1f}" rx="2" fill="var(--orange)"/></g>')
    s.append(f'<text class="t" x="{L-6}" y="{top+8}" text-anchor="end">{vmax:,}</text><text class="t" x="{L-6}" y="{top+h1}" text-anchor="end">0</text>')
    y0 = top + h1 + gap
    s.append(f'<text class="t" x="{L}" y="{y0-8}">Negative share of that month\'s reviews (months with 30+ reviews). Ticks under the axis = months with an official patch or update post.</text>')
    for g in (0, .25, .5, .75, 1):
        y = y0 + h2 - g * h2
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--grid)"/><text class="t" x="{L-6}" y="{y+4:.1f}" text-anchor="end">{int(g*100)}%</text>')
    pts = [(L + i * step + step / 2, y0 + h2 - m["negative_share"] * h2, m) for i, m in enumerate(monthly) if m["reviews"] >= 30]
    if len(pts) > 1:
        s.append('<polyline fill="none" stroke="var(--orange)" stroke-width="2" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts) + '"/>')
    for x, y, m in pts:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="transparent"><title>{E(m["month"])}: {pct(m["negative_share"])} negative of {m["reviews"]:,} reviews</title></circle><circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="var(--orange)"/>')
    for i, m in enumerate(monthly):
        x = L + i * step + step / 2
        if m["patches"]:
            s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y0+h2+2}" y2="{y0+h2+9}" stroke="var(--text2)" stroke-width="2"><title>{E(m["month"] + ": " + "; ".join(m["patches"][:4]))}</title></line>')
        if m["month"].endswith("-01") or i == 0:
            s.append(f'<text class="t" x="{x:.1f}" y="{H-6}" text-anchor="middle">{E(m["month"])}</text>')
    return "".join(s) + "</svg>"


def heat_table(grid, codes):
    head = "".join(f"<th>{E(REASONS[c])}</th>" for c in codes)
    body = ""
    for g in grid:
        cells = ""
        for c in codes:
            v = g["shares"][c]
            cells += "<td>–</td>" if v is None else f'<td style="background:rgba(var(--heat),{min(v*1.6,0.85):.2f})" title="{E(REASONS[c])}, {E(g["bucket"])}: {pct(v)} of {g["n"]:,} labeled negative reviews">{pct(v)}</td>'
        body += f'<tr><td>{E(g["bucket"])} <span class="note">(n={g["n"]:,})</span></td>{cells}</tr>'
    return f'<div class="scroll"><table><tr><th>Hours played when the review was written</th>{head}</tr>{body}</table></div>'


PLAYBOOK = {
    "PERF": ["Compare session length and return rate by hardware tier in your own telemetry; reviews cannot see hardware.",
             "Publish the performance target per spec tier and report progress against it in patch notes, so waiting players know when to come back."],
    "STAB": ["Rank crash signatures and save-loss bugs by how many players hit them in their first sessions, not by ticket count.",
             "Check whether players who crashed in session one or two ever started a third session."],
    "CONTENT": ["Find the hour mark where these reviews cluster and look at what players have run out of by then.",
                "Say plainly on the store page what is in the game today versus planned, so expectations match the build."],
    "DESIGN": ["Separate 'I don't like this mechanic' from 'this mechanic is unclear': the first is a design choice, the second is onboarding.",
               "Test optional rule settings or modes for the most-named mechanic, and measure retention of players who switch them on."],
    "UI": ["Run task-based usability checks on the screens named most often; UI complaints tend to be specific and cheap to verify.",
           "Ship interface fixes in small, frequent patches and list them at the top of the notes; these reviewers often keep playing."],
    "MONET": ["Compare refund and early-exit rates across editions and price points; price complaints concentrate before much play.",
              "Check whether paid add-ons land while core complaints are still open; review timing around DLC posts is shown in the spike table."],
    "ONLINE": ["Track failed logins, disconnects and matchmaking time-outs per player and tie them to next-day return.",
               "If an account or always-online requirement is named, measure how many players drop at that exact step."],
    "SUPPORT": ["Audit promised-versus-shipped items in public posts; these reviewers are usually long-time players reacting to a specific change.",
                "After a patch that triggers a review spike, compare return rates of players active the week before with earlier weeks."],
    "STORY": ["Use quest and dialogue completion telemetry to find where players stop following the main story.",
              "Treat this as input for the next content release more than for patches."],
}


def game_page(o, audit):
    b = o["behaviour"]; bn, bp = b["negative"], b["positive"]; ov = o["overview"]; f = o["funnel"]
    reasons = [r for r in o["reasons"] if r["n"] > 0]
    named = [r for r in reasons if r["code"] not in ("OTHER", "OFFGAME")]
    big = [r for r in named if r["walk_n"] >= 100 and r["walk_rate"] is not None]
    his = [r for r in big if r["vs_game_average"] == "higher"]; los = [r for r in big if r["vs_game_average"] == "lower"]
    pt = o["playtime"]; svd = {r["code"]: r for r in o["said_vs_did"]}
    early = pt[0]

    bottom = [
        f"<b>{pct(ov['negative_share'])}</b> of the {num(ov['reviews'])} English reviews are negative. The median negative review was written after <b>{ov['median_hours_at_negative_review']} hours</b> of play (positive: {ov['median_hours_at_positive_review']} hours).",
        f"A negative review is not the same as quitting. <b>{pct(bn['walk_rate'])}</b> of negative reviewers logged less than {o['params']['walk_hours']:.0f} more hour after posting; the other {pct(1-bn['walk_rate'])} kept playing, and {pct(bn['kept_10h_rate'])} played 10 or more further hours. Among positive reviewers, {pct(bp['walk_rate'])} stopped that quickly.",
    ]
    if named:
        bottom.append("The most common main complaints are " + ", ".join(f"<b>{E(r['reason'].lower())}</b> ({pct(r['share'])})" for r in named[:3]) + f", out of {num(f['labeled'])} labeled negative reviews.")
    parts = []
    if his: parts.append("clearly more often after complaints about " + ", ".join(f"<b>{E(r['reason'].lower())}</b> ({pct(r['walk_rate'])})" for r in sorted(his, key=lambda r: -r["walk_rate"])[:3]))
    if los: parts.append("clearly less often after complaints about " + ", ".join(f"<b>{E(r['reason'].lower())}</b> ({pct(r['walk_rate'])})" for r in sorted(los, key=lambda r: r["walk_rate"])[:3]))
    if parts: bottom.append(f"Compared with all negative reviewers ({pct(bn['walk_rate'])}), reviewers walked away " + "; and ".join(parts) + ". These are associations, not causes.")
    if early["neg_walk_rate"] is not None:
        bottom.append(f"The first two hours are the sharpest edge: {pct(early['negative_share_in_bucket'])} of reviews written with under 2 hours played are negative, and {pct(early['neg_walk_rate'])} of those reviewers did not come back for another hour.")
    if svd["STOPPED"]["walk_rate"] is not None and svd["WAITING"]["kept_10h_rate"] is not None:
        bottom.append(f"What players say and do differ: of reviewers who wrote that they had quit, {pct(1-svd['STOPPED']['walk_rate'])} still logged another hour or more. Of those who wrote they would wait for fixes, {pct(svd['WAITING']['kept_10h_rate'])} went on to play 10+ more hours.")

    tiles = "".join(f'<div class="tile"><b>{v}</b><span>{E(l)}</span></div>' for v, l in [
        (num(ov["reviews"]), f"English reviews, {f['first_review']} to {f['last_review']}"), (pct(ov["negative_share"]), "negative"),
        (pct(bn["walk_rate"]), "of negative reviewers logged under 1 more hour"), (pct(bn["refunded_rate"]), "of negative reviews are marked refunded"),
        (pct(bn["active_now_rate"]), "of negative reviewers played in the 2 weeks before the snapshot"), (num(f["labeled"]), "negative reviews labeled by reason")])

    # when
    c1 = columns([dict(label=p["bucket"], value=p["negative_share_in_bucket"], tip=f'{p["bucket"]}: {p["negative"]:,} of {p["reviews"]:,} reviews negative') for p in pt])
    c2 = columns([dict(label=p["bucket"], value=p["neg_walk_rate"], tip=f'{p["bucket"]}: walk-away rate among {p["neg_walk_n"]:,} negative reviewers') for p in pt], color="var(--orange)")
    pt_table = "<table><tr><th>Hours at review</th><th>Reviews</th><th>Negative</th><th>Negative share</th><th>Share of all negative</th><th>Negative reviewers who walked away</th></tr>" + "".join(
        f"<tr><td>{E(p['bucket'])}</td><td>{num(p['reviews'])}</td><td>{num(p['negative'])}</td><td>{pct(p['negative_share_in_bucket'])}</td><td>{pct(p['share_of_all_negative'])}</td><td>{pct(p['neg_walk_rate'])}</td></tr>" for p in pt) + "</table>"

    # why
    r1 = hbar([dict(label=r["reason"], value=r["share"], tip=f'{r["reason"]}: main reason in {r["n"]:,} reviews; named as main or second reason in {pct(r["any_mention_share"])}') for r in reasons])
    r2 = hbar([dict(label=r["reason"], value=r["walk_rate"], lo=r["walk_lo"], hi=r["walk_hi"], tip=f'{r["reason"]}: {pct(r["walk_rate"])} of {r["walk_n"]:,} reviewers walked away (95% interval {pct(r["walk_lo"])}–{pct(r["walk_hi"])})') for r in reasons if r["walk_n"] >= 100],
              color="var(--orange)", ref=bn["walk_rate"], ref_label="all negative reviewers", whisk=True)
    r_table = "<table><tr><th>Main reason</th><th>Reviews</th><th>Share</th><th>Main or second reason</th><th>Median hours at review</th><th>Walked away</th><th>95% interval</th><th>Walked away, adjusted for hours played</th><th>Vs. all negative reviewers</th><th>Wrote that they quit</th></tr>" + "".join(
        f"<tr><td>{E(r['reason'])}</td><td>{num(r['n'])}</td><td>{pct(r['share'],1)}</td><td>{pct(r['any_mention_share'],1)}</td><td>{r['median_hours_at_review']}</td><td>{pct(r['walk_rate'])}</td><td>{pct(r['walk_lo'])}–{pct(r['walk_hi'])}</td><td>{pct(r['walk_rate_adjusted'])}</td><td>{E(r['vs_game_average'])}</td><td>{pct(r['says_stopped_rate'])}</td></tr>" for r in reasons) + "</table>"
    heat = heat_table(o["reason_by_playtime"], [r["code"] for r in named[:6]])

    svd_table = "<table><tr><th>What the review said</th><th>Reviews</th><th>Share</th><th>Logged under 1 more hour</th><th>Played 10+ more hours</th><th>Played in last 2 weeks</th></tr>" + "".join(
        f"<tr><td>{E(r['statement'])}</td><td>{num(r['n'])}</td><td>{pct(r['share'])}</td><td>{pct(r['walk_rate'])}</td><td>{pct(r['kept_10h_rate'])}</td><td>{pct(r['active_now_rate'])}</td></tr>" for r in o["said_vs_did"]) + "</table>"

    spikes = ""
    for s in o["spikes"]:
        posts = "".join(f"<li>{E(p['date'])} — {E(p['title'])}</li>" for p in s["official_posts"]) or "<li>No official post found in that window.</li>"
        mix = ", ".join(f"{E(t['reason'].lower())} {pct(t['share'])}" for t in s["top_reasons"]) or "too few labeled reviews to show a mix"
        spikes += f"<div class='card'><b>Week of {E(s['week_start'])}</b>: {num(s['negative'])} negative reviews (usual week before it: {s['usual_weekly_negative']:.0f}); {pct(s['negative_share'])} of that week's {num(s['reviews'])} reviews were negative.<br><span class='note'>Main reasons that week: {mix}.</span><details><summary>Official posts in the days around it</summary><ul class='note'>{posts}</ul></details></div>"
    if not spikes: spikes = "<p class='note'>No week after the launch period met the spike rule (at least 40 negative reviews and at least double the median of the previous 8 weeks).</p>"

    voices = ""
    for r in named[:5]:
        ps = o["paraphrases"].get(r["code"], [])
        if ps: voices += f"<h3>{E(r['reason'])}</h3>" + "".join(f"<blockquote>{E(p)}</blockquote>" for p in ps)

    todo = ""
    for r in named[:4]:
        tips = PLAYBOOK.get(r["code"])
        if not tips: continue
        wr = f"{pct(r['walk_rate'])} of these reviewers walked away ({E(r['vs_game_average'])} vs. all negative reviewers)" if r["walk_rate"] is not None else "walk-away rate not shown (too few reviews)"
        todo += f"<div class='card'><b>{E(r['reason'])}</b><span class='tag'>{pct(r['share'])} of labeled negative reviews</span><div class='note'>{wr}; median {r['median_hours_at_review']} hours played at review.</div><ul>" + "".join(f"<li>{E(t)}</li>" for t in tips) + "</ul></div>"

    offgame = next((r for r in o["reasons"] if r["code"] == "OFFGAME"), None)
    off_note = f"<p class='note'><b>Off-game topics.</b> {pct(offgame['share'],1)} of labeled negative reviews ({num(offgame['n'])}) are mainly about politics, social topics, or specific people or companies rather than how the game plays. They are counted here and not characterized further; this report takes no position on them.</p>" if offgame else ""

    body = f"""
<div class="kicker">Quit-signal report · {E(o['genre'])} · released {E(o['release'])} · data snapshot {E(o['snapshot'])}</div>
<h1>{E(o['name'])}</h1>
<p class="lede">Who left after reviewing, when they gave up, and which complaints go with actually leaving — from every public English Steam review.</p>
<div class="card"><b>Bottom line</b><ul class="bottom">{''.join(f'<li>{x}</li>' for x in bottom)}</ul></div>
<div class="tiles">{tiles}</div>
<div class="caveat">Read this first: reviews come only from players who chose to write one ({num(ov['reviews'])} here), so shares are shares of <i>reviewers</i>, not of all players. "Walked away" is measured from public playtime ({pct(bn['walk_rate'])} = {num(bn['walked_away'])} of {num(bn['n'])} negative reviews at least {o['params']['mature_days']} days old). The patterns below are associations, not proof of cause.</div>

<h2>1. When do reviewers give up?</h2>
<p>Each review records how many hours the reviewer had played. Left: how negative reviews are at each stage. Right: of the negative reviewers at that stage, how many logged under one more hour afterwards.</p>
<div class="grid2"><div class="card"><h3>Negative share of reviews, by hours played at review</h3>{c1}</div><div class="card"><h3>Negative reviewers who walked away, by hours played at review</h3>{c2}</div></div>
<details><summary>Table view</summary><div class="scroll">{pt_table}</div></details>

<h2>2. Why? Main reason given in negative reviews</h2>
<p>{num(f['labeled'])} negative reviews with at least 3 words were sorted by a language model into one main reason each ({audit_line(audit)}).</p>
<div class="grid2"><div class="card"><h3>Share of labeled negative reviews, by main reason</h3>{r1}</div>
<div class="card"><h3>Reviewers who walked away, by main reason (100+ reviews)</h3><div class="legend"><span><i class="sw-o"></i>logged under 1 more hour after the review</span><span>thin line = 95% interval</span></div>{r2}</div></div>
<p class="note">How to read the right-hand chart: a reason far to the right of the dashed line is a complaint whose authors more often stopped playing. A reason to the left is one players grumble about while they keep playing. Neither shows that the complaint <i>caused</i> the behaviour. Players with few hours leave more often whatever they complain about, so the table view also gives each rate re-weighted to the game's overall mix of hours played.</p>
<details><summary>Table view</summary><div class="scroll">{r_table}</div></details>
<h3>Reasons change with time played</h3>
<p class="note">Each row adds up across all reasons to 100% (only the six largest named reasons are shown). Darker = larger share.</p>{heat}
{off_note}

<h2>3. What they said versus what they did</h2>
<p>The same model also tagged whether the reviewer wrote that they had quit, or that they would wait for fixes. Public playtime shows what happened next.</p>
<div class="scroll">{svd_table}</div>

<h2>4. Timeline and official patches</h2>
<div class="legend"><span><i class="sw-b"></i>all reviews</span><span><i class="sw-o"></i>negative reviews / negative share</span><span><i class="sw-g"></i>month with an official patch or update post</span></div>
<div class="card">{timeline(o['monthly'], o['patch_dates'], o['release'])}</div>
<h3>Weeks when negative reviews jumped</h3>
<p class="note">Rule: after the first six weeks, a week with 40+ negative reviews, at least double the median of the previous eight weeks. Official posts from the surrounding days are listed for context. Sales, free weekends and news also move review counts, so a post near a spike is a lead to check, not an explanation.</p>
{spikes}

<h2>5. In players' words (paraphrased)</h2>
<p class="note">These are short paraphrases written to show the kind of complaint in each group. They are not quotes, and no review text is published.</p>
{voices or "<p class='note'>No paraphrases available.</p>"}

<h2>6. What a studio could do with this</h2>
<p>Reviews point at where to look; a studio's own telemetry can confirm or reject each lead. Suggested checks for this game's largest complaint groups:</p>
{todo}
<div class="card"><b>Three uses of this report</b><ul>
<li><b>Prioritize by behaviour, not volume.</b> Put a complaint group higher when its authors walk away more often than other negative reviewers (section 2, right-hand chart).</li>
<li><b>Protect the riskiest hours.</b> Section 1 shows where negative reviews and walk-aways concentrate; that is the stretch of the game to instrument and playtest first.</li>
<li><b>Talk to the "waiting" group.</b> Section 3 sizes the reviewers who said they would return after fixes and shows how many did; patch notes aimed at their stated reasons are the natural test.</li></ul></div>

<h2>Limits of this report</h2>
<ul class="note">
<li>Only English reviews. Only people who wrote a review; they are a small and unusual part of the player base.</li>
<li>Playtime after a review is Steam's public figure at the snapshot date ({E(o['snapshot'])}). Offline play and play on other platforms are not counted. Reviews newer than {o['params']['mature_days']} days are excluded from walk-away rates.</li>
<li>If a reviewer edited their review, Steam may have refreshed the "playtime at review" figure. Without edited reviews the walk-away rate of negative reviewers is {pct(b['negative_unedited']['walk_rate'])} (with them: {pct(bn['walk_rate'])}).</li>
<li>Reason labels come from a language model reading up to 1,200 characters per review, one main reason each. {audit_line(audit, long=True)}</li>
<li>Associations only. Players who complain about different things also differ in other ways (hours played, when they bought, what they expected).</li>
</ul>
<p class="note">Every number on this page is in <a href="../data/{E(o['slug'])}.json">data/{E(o['slug'])}.json</a>, produced by <a href="{REPO}/blob/main/src/analyze.py">src/analyze.py</a>. See <a href="../method.html">Method &amp; limits</a>.</p>"""
    return page(f"{o['name']} — quit signals in Steam reviews", body, depth=1, desc=f"Quit-signal report for {o['name']} from public Steam reviews.")


def audit_line(audit, long=False):
    if not audit: return "label accuracy check pending"
    s = f"in a hand check of {audit['n']} random labels, {pct(audit['main_agree'])} of main reasons were judged correct"
    if long: s = s[0].upper() + s[1:] + f" and {pct(audit['quit_agree'])} of quit-statement tags; expect roughly that error rate in reason shares."
    return s


def index_page(ov, audit, cost):
    tot = sum(o["reviews"] for o in ov); neg = sum(o["negative"] for o in ov); lab = sum(o["labeled"] for o in ov)
    wmin = min(ov, key=lambda o: o["neg_walk_rate"]); wmax = max(ov, key=lambda o: o["neg_walk_rate"])
    rows = "".join(f"<tr><td><a href='games/{E(o['slug'])}.html'>{E(o['name'])}</a><div class='note'>{E(o['genre'])}</div></td><td>{num(o['reviews'])}</td><td>{pct(o['negative_share'])}</td><td>{o['neg_median_hours_at_review']}</td>"
                   f"<td>{pct(o['neg_walk_rate'])}</td><td>{pct(o['pos_walk_rate'])}</td><td>{pct(o['neg_refunded_rate'])}</td><td class='l'>{E(o['top_reason'] or '–')} ({pct(o['top_reason_share'])})</td></tr>" for o in ov)
    chart = hbar([dict(label=o["name"], value=o["neg_walk_rate"], tip=f'{o["name"]}: {pct(o["neg_walk_rate"])} of negative reviewers logged under 1 more hour (positive reviewers: {pct(o["pos_walk_rate"])})') for o in sorted(ov, key=lambda o: -o["neg_walk_rate"])],
                 color="var(--orange)", width=640, label_w=230, xmax=1)
    codes = [c for c in REASONS if c != "OTHER"]
    head = "".join(f"<th>{E(REASONS[c])}</th>" for c in codes)
    def cell(v, n=None):
        return "<td>–</td>" if v is None else f'<td style="background:rgba(var(--heat),{min(v*1.6,0.85):.2f})">{pct(v)}</td>'
    heat1 = "".join(f"<tr><td>{E(o['name'])}</td>" + "".join(cell(o["reason_shares"].get(c)) for c in codes) + "</tr>" for o in ov)
    heat2 = "".join(f"<tr><td>{E(o['name'])} <span class='note'>(all: {pct(o['neg_walk_rate'])})</span></td>" + "".join("<td>–</td>" if o["reason_walk"].get(c) is None else f"<td>{pct(o['reason_walk'][c])}</td>" for c in codes) + "</tr>" for o in ov)
    cards = "".join(f"<a class='card' href='games/{E(o['slug'])}.html'><b>{E(o['name'])}</b><div class='note'>{E(o['genre'])} · released {E(o['release'])}</div>"
                    f"<div class='note'>{num(o['reviews'])} reviews · {pct(o['negative_share'])} negative · top complaint: {E((o['top_reason'] or '').lower())}</div></a>" for o in ov)
    flags = {c: [o["reason_flags"].get(c, "n/a") for o in ov] for c in REASONS if c not in ("OTHER", "OFFGAME")}
    order = sorted(flags, key=lambda c: flags[c].count("lower") - flags[c].count("higher"))
    flagrows = "".join(f"<tr><td>{E(REASONS[c])}</td><td>{flags[c].count('higher')}</td><td>{flags[c].count('lower')}</td><td>{len(ov)-flags[c].count('higher')-flags[c].count('lower')}</td></tr>" for c in order)
    stay = [c for c in order if flags[c].count("lower") >= 4]; leave = [c for c in order if flags[c].count("higher") >= 4]
    rng = lambda k, inv=False: (lambda v: f"{pct(min(v))}–{pct(max(v))}")([(1 - o[k]) if inv else o[k] for o in ov if o[k] is not None])
    pats = []
    if stay: pats.append("<b>Complaints voiced by players who mostly stay:</b> " + ", ".join(f"{E(REASONS[c].lower())} (walked away less often than other negative reviewers in {flags[c].count('lower')} of {len(ov)} games)" for c in stay) + ".")
    if leave: pats.append("<b>Complaints that travel with leaving:</b> " + ", ".join(f"{E(REASONS[c].lower())} (more often in {flags[c].count('higher')} of {len(ov)} games)" for c in leave) + ".")
    pats.append(f"<b>The first two hours decide a lot.</b> {rng('under2h_negative_share')} of reviews written with under 2 hours played are negative, and {rng('under2h_neg_walk_rate')} of those reviewers did not log another hour.")
    pats.append(f"<b>Saying is not doing.</b> {rng('said_stopped_share')} of labeled negative reviewers wrote that they had quit; {rng('said_stopped_walk_rate', True)} of them still logged another hour or more. Of those who wrote they would wait for fixes, {rng('said_waiting_kept_10h_rate')} played 10+ more hours.")
    pats.append("These are associations among people who wrote reviews. They do not show that fixing a complaint would have kept anyone.")
    patterns = "".join(f"<li>{x}</li>" for x in pats)
    body = f"""
<div class="kicker">Public Steam review study · snapshot {E(ov[0]['snapshot'])}</div>
<h1>A negative review is a warning, not a goodbye</h1>
<p class="lede">Six big-budget PC games that each drew more than {min(o['negative'] for o in ov) // 1000},000 negative English reviews. For each one, this lab measures who actually stopped playing after reviewing, when they gave up, and which complaints go with leaving — so a studio can tell loud problems from costly ones.</p>
<div class="tiles"><div class="tile"><b>{num(tot)}</b><span>English Steam reviews, full history of 6 games</span></div><div class="tile"><b>{num(neg)}</b><span>negative reviews</span></div>
<div class="tile"><b>{num(lab)}</b><span>negative reviews labeled by reason</span></div><div class="tile"><b>{pct(wmin['neg_walk_rate'])}–{pct(wmax['neg_walk_rate'])}</b><span>of negative reviewers logged under 1 more hour (range across games)</span></div></div>
<div class="card"><b>The idea in one paragraph</b><p>Steam publishes, next to every review, how long the reviewer had played when they wrote it and how long they have played in total. The gap between the two shows what the reviewer did <i>after</i> complaining. Across these six games, between {pct(1-wmax['neg_walk_rate'])} and {pct(1-wmin['neg_walk_rate'])} of negative reviewers kept playing for at least another hour. Combining that behaviour with the reason each review gives separates complaints that travel with quitting from complaints players voice while they stay.</p></div>
<div class="caveat">Reviews represent only the players who wrote them. All figures are shares of reviewers, and every pattern here is an association, not a cause. See <a href="method.html">Method &amp; limits</a>.</div>

<h2>Patterns that held across the six games</h2>
<div class="card"><ul class="bottom">{patterns}</ul>
<div class="scroll"><table><tr><th>Main complaint</th><th>Games where these reviewers walked away clearly <i>more</i> often</th><th>Clearly <i>less</i> often</th><th>No clear difference or too few reviews</th></tr>{flagrows}</table></div>
<p class="note">"Clearly" means the complaint group's whole 95% interval is above or below that game's rate for all negative reviewers. Counts are out of {len(ov)} games.</p></div>

<h2 id="reports">Game reports</h2>
<div class="games">{cards}</div>

<h2>Side by side</h2>
<div class="card"><h3>Negative reviewers who logged under 1 more hour after posting</h3>{chart}</div>
<div class="scroll"><table><tr><th>Game</th><th>English reviews</th><th>Negative</th><th>Median hours at negative review</th><th>Negative reviewers who walked away</th><th>Positive reviewers who walked away</th><th>Negative reviews marked refunded</th><th class="l">Top named complaint</th></tr>{rows}</table></div>
<h3>What negative reviews are about (share of each game's labeled negative reviews)</h3>
<div class="scroll"><table><tr><th>Game</th>{head}</tr>{heat1}</table></div>
<p class="note">The rest of each row is "no clear reason". "Off-game topics" counts reviews mainly about politics, social topics, or specific people or companies; they are reported as a share only.</p>
<h3>Walk-away rate by main complaint</h3>
<div class="scroll"><table><tr><th>Game</th>{head}</tr>{heat2}</table></div>
<p class="note">Share of reviewers citing that main reason who logged under 1 more hour afterwards. "–" means fewer than 30 reviews. Compare each cell with the game's own rate in brackets.</p>

<h2>How studios could use this</h2>
<div class="card"><ul><li><b>Rank fixes by who leaves, not by who is loudest.</b> Each report shows, per complaint, how often its authors stopped playing compared with other negative reviewers.</li>
<li><b>Find the hours where players are lost.</b> Each report shows how negative reviews and walk-aways are spread over hours played.</li>
<li><b>Size the players who are waiting.</b> Each report counts reviewers who said they would return after fixes, and how many did.</li>
<li><b>Line up review spikes with your own release calendar.</b> Each report lists spike weeks next to official patch and update posts.</li>
<li><b>Re-run it on any game.</b> The <a href="{REPO}">code</a> needs only a Steam app ID; raw data is fetched politely and cached.</li></ul></div>
<p class="note">Why these six: all are premium (paid) games with a large body of negative reviews ({pct(min(o['negative_share'] for o in ov))}–{pct(max(o['negative_share'] for o in ov))} negative) and a review history small enough to fetch in full without straining Steam, spread across genres (4X strategy, city builder, co-op shooter, two action RPGs, co-op hunting). {audit_line(audit)[0].upper() + audit_line(audit)[1:]}. Total paid model spend for the whole project: ${cost['total_usd']:.2f}.</p>"""
    return page("Why Players Quit · Lab — quit signals in Steam reviews", body, desc="Which complaints go with actually leaving? Quit-signal reports for six games from public Steam reviews.")


def method_page(ov, games, audit, cost):
    funnel = "".join(f"<tr><td>{E(o['name'])}</td><td>{num(o['funnel']['steam_summary_total'])}</td><td>{num(o['funnel']['api_reported_english_reviews'])}</td><td>{num(o['funnel']['fetched_unique'])}</td><td>{num(o['funnel']['negative'])}</td><td>{num(o['funnel']['negative_3plus_words'])}</td><td>{num(o['funnel']['labeled'])}</td></tr>" for o in games)
    aud = ""
    if audit:
        aud = f"""<p>A random sample of {audit['n']} labeled reviews (drawn by code across all six games, seed fixed) was read and judged by the project's AI analyst (Claude), not by a human panel. Main reason judged correct: <b>{pct(audit['main_agree'])}</b> ({audit['main_ok']} of {audit['n']}). Quit-statement tag judged correct: <b>{pct(audit['quit_agree'])}</b> ({audit['quit_ok']} of {audit['n']}). The per-item verdicts (without text or IDs) are in <a href="data/label_audit.json">data/label_audit.json</a>. A second 50-review sample with text is kept locally for the author's own spot check and is not published.</p>"""
    crow = "".join(f"<tr><td>{E(r['step'])}</td><td>{num(r['calls'])}</td><td>{num(r['input_tokens'])}</td><td>{num(r['output_tokens'])}</td><td>${r['cost_usd']:.2f}</td></tr>" for r in cost["rows"])
    reasons = "".join(f"<tr><td>{E(n)}</td><td class='l'>{E(d)}</td></tr>" for n, d in [
        ("Performance", "low or unstable frame rate, stutter, long loading, hardware demands"), ("Crashes & bugs", "crashes, game-breaking bugs, lost or corrupted saves, will not start"),
        ("Not enough content", "feels unfinished, missing features, repetitive, nothing left to do"), ("Gameplay & design choices", "mechanics, balance, difficulty, pacing, progression, 'boring'"),
        ("Interface & controls", "UI, controls, readability, missing quality-of-life"), ("Price & monetization", "price or value, DLC, microtransactions, editions"),
        ("Online, accounts & DRM", "servers, matchmaking, forced online, third-party accounts, DRM, anti-cheat, cheaters"), ("Post-launch support", "a patch made things worse, slow fixes, broken promises, communication"),
        ("Story & writing", "writing, characters, quests, world building"), ("Off-game topics", "mainly politics, social topics, or specific people or companies rather than how the game plays; reported as a share only, without names and without taking sides"),
        ("No clear reason", "jokes, one-liners, unclear")])
    body = f"""
<div class="kicker">Method &amp; limits</div><h1>How the numbers were made</h1>
<p class="lede">Everything is computed by code in the public repository from public Steam data. This page lists each step, each definition, and what the results cannot tell you.</p>
<h2>Data</h2>
<ul><li><b>Source:</b> Steam's documented public review endpoint (<code>IUserReviewsService/GetAppReviews</code>), English reviews, all purchase types, full history, walked one calendar month at a time. Official announcements and patch notes come from Steam's public news endpoint (<code>ISteamNews/GetNewsForApp</code>).</li>
<li><b>Politeness:</b> one request at a time per game with a pause between requests (about one request per second overall), back-off on errors, every raw page cached locally so nothing is fetched twice.</li>
<li><b>Privacy:</b> raw review text and reviewer IDs never leave the local cache. The repository and this site contain only aggregated counts and short paraphrases written by a model and screened by code (20 words or fewer; no 4-word run shared with the source review).</li>
<li><b>Snapshot:</b> {E(ov[0]['snapshot'])} (UTC). Playtime totals are as of that date.</li></ul>
<h2>Row counts at each stage</h2>
<div class="scroll"><table><tr><th>Game</th><th>Steam's lifetime English total (summary field)</th><th>English reviews reported by the API (sum of months)</th><th>Fetched, unique</th><th>Negative</th><th>Negative with 3+ words (code filter)</th><th>Labeled by model</th></tr>{funnel}</table></div>
<p class="note">Coverage gap: Steam's lifetime summary count is {pct(1 - sum(o['funnel']['fetched_unique'] for o in games) / sum(o['funnel']['steam_summary_total'] for o in games), 1)} higher than the reviews the month-by-month listing returned ({pct(min(1 - o['funnel']['fetched_unique'] / o['funnel']['steam_summary_total'] for o in games), 1)}–{pct(max(1 - o['funnel']['fetched_unique'] / o['funnel']['steam_summary_total'] for o in games), 1)} by game). The listing itself was fetched almost completely. The reason for the gap is not documented by Steam and is not known here; the missing reviews could differ from the fetched ones.</p>
<p class="note">The cheap filter runs in code first: positive reviews and negative reviews under 3 words are not sent to the model. Reviews the model failed to return a valid line for are left unlabeled.</p>
<h2>Definitions</h2>
<ul><li><b>Walked away:</b> the reviewer's public total playtime at the snapshot is less than 1 hour above their playtime when they wrote the review. Computed only for reviews at least 30 days old.</li>
<li><b>Played 10+ more hours:</b> same gap, 10 hours or more.</li><li><b>Played in last 2 weeks:</b> Steam's two-week playtime figure is above zero at the snapshot.</li>
<li><b>Refunded:</b> Steam's own flag on the review.</li>
<li><b>95% interval:</b> Wilson interval for a share. Rates on fewer than 30 reviews are not shown.</li>
<li><b>Adjusted for hours played:</b> the walk-away rate a complaint group would have if its reviewers had the same spread of hours-at-review as all labeled negative reviewers of that game (direct standardization over five playtime bands). Not shown when a band is too thin.</li>
<li><b>"Higher / lower / similar":</b> a reason is called higher (or lower) only when its whole 95% interval sits above (or below) the game's overall negative-reviewer rate.</li>
<li><b>Spike week:</b> after the first six weeks, a week with at least 40 negative reviews, at least double the median of the previous eight weeks, and not below any of them.</li></ul>
<h2>Reason labels</h2>
<p>A small language model (Claude Haiku) read each negative review (first 1,200 characters) and returned one main reason, an optional second reason, and whether the reviewer wrote that they had quit or would wait for fixes. Review text was treated as untrusted data.</p>
<div class="scroll"><table><tr><th>Label</th><th class="l">Covers</th></tr>{reasons}</table></div>
<h3>Accuracy check</h3>{aud or "<p class='note'>Pending.</p>"}
<h2>Limits</h2>
<ul><li><b>Reviewers are not players.</b> Only a small share of buyers write a review, and they are not a random sample. Nothing here estimates churn for the whole player base.</li>
<li><b>Correlation, not cause.</b> A complaint group with a high walk-away rate was not shown to quit <i>because</i> of that complaint. Groups also differ in hours played, purchase timing and expectations.</li>
<li><b>English only.</b> Other language communities may complain about different things.</li>
<li><b>Playtime is imperfect.</b> Offline play, other platforms and idle time are not separated. Editing a review may refresh its "playtime at review" value; each report shows the walk-away rate with and without edited reviews.</li>
<li><b>Six games, chosen by hand.</b> All drew heavy criticism; patterns may not hold for well-received or free-to-play games.</li>
<li><b>Model labels contain errors</b> at about the rate shown in the accuracy check, and one main reason per review hides multi-issue reviews (the tables also show "main or second reason").</li>
<li><b>Patch matching is by date only.</b> Official posts near a spike are listed for context; sales, free weekends and outside news also move review counts.</li></ul>
<h2>Cost</h2>
<div class="scroll"><table><tr><th>Step</th><th>Model calls</th><th>Input tokens (incl. cached)</th><th>Output tokens</th><th>Cost</th></tr>{crow}<tr><td><b>Total</b></td><td></td><td></td><td></td><td><b>${cost['total_usd']:.2f}</b></td></tr></table></div>
<p class="note">Costs are the list-price figures reported with each call's actual token counts, summed by <a href="{REPO}/blob/main/src/cost.py">src/cost.py</a>. Budget cap for the project: $30.</p>
<h2>Files</h2>
<p>Per-game numbers: {' · '.join(f'<a href="data/{E(o["slug"])}.json">{E(o["slug"])}.json</a>' for o in games)}. Cross-game: <a href="data/overview.json">overview.json</a>. Flat CSV tables and all code are in the <a href="{REPO}">repository</a>.</p>"""
    return page("Method & limits — Why Players Quit · Lab", body, desc="Data, definitions, accuracy check, limits and cost.")


if __name__ == "__main__":
    ov = load("overview.json"); audit = load("label_audit.json"); cost = load("cost.json") or dict(total_usd=0, rows=[])
    games = [load(o["slug"] + ".json") for o in ov]
    os.makedirs(os.path.join(DOCS, "games"), exist_ok=True)
    open(os.path.join(DOCS, ".nojekyll"), "w").write("")
    open(os.path.join(DOCS, "index.html"), "w").write(index_page(ov, audit, cost))
    open(os.path.join(DOCS, "method.html"), "w").write(method_page(ov, games, audit, cost))
    for o in games: open(os.path.join(DOCS, "games", o["slug"] + ".html"), "w").write(game_page(o, audit))
    print("built", 2 + len(games), "pages")
