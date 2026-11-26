"""Render the static site (docs/) from docs/data/*.json. No number is typed by hand here:
every figure in the HTML is read from the JSON written by analyze.py, audit.py and cost.py.

Layout is built for studio readers (production, design, engineering, publishing, community):
decisions first, then evidence, then method. Each complaint group carries the team that would own it."""
import html, json, os
from analyze import REASONS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS = os.path.join(ROOT, "docs"); DATA = os.path.join(DOCS, "data")
REPO = "https://github.com/HosungKim48/whyplayersquit-lab"
E = html.escape

OWNER = {"PERF": "Engineering", "STAB": "Engineering & QA", "CONTENT": "Production", "DESIGN": "Game design", "UI": "UX / UI",
         "MONET": "Publishing & pricing", "ONLINE": "Online services", "SUPPORT": "Live ops & community", "STORY": "Narrative",
         "OFFGAME": "Community & comms", "OTHER": "–"}
SHORT = {"PERF": "Performance", "STAB": "Crashes & bugs", "CONTENT": "Content", "DESIGN": "Design", "UI": "Interface", "MONET": "Price",
         "ONLINE": "Online & DRM", "SUPPORT": "Support", "STORY": "Story", "OFFGAME": "Off-game", "OTHER": "No reason"}
VERDICT = {"higher": ("▲", "Leave more often"), "lower": ("▼", "Stay more often"), "similar": ("●", "About average"), "n/a": ("·", "Too few reviews")}


def pct(x, d=0): return "–" if x is None else f"{x * 100:.{d}f}%"
def num(x): return "–" if x is None else f"{x:,}"
def load(name):
    p = os.path.join(DATA, name)
    return json.load(open(p)) if os.path.exists(p) else None


CSS = """
:root{color-scheme:dark;--bg:#090e19;--surface:#131c30;--surface2:#18233b;--line:#27324a;--text:#eef2f8;--text2:#b9c3d3;--muted:#a9b4c6;
--ink:#090e19;--blue:#5a9cec;--orange:#f08152;--grid:#27324a;--heat:90,156,236;--chip:#1d2a45;--focus:#8fbdf5;--display:Sora,Inter,system-ui,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--blue);text-underline-offset:2px}a:focus-visible,summary:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.top{background:var(--ink);color:#fff;position:relative;z-index:2}.top .in{max-width:1220px;margin:0 auto;padding:16px 24px;display:flex;gap:20px;align-items:center;flex-wrap:wrap}
.top .brand{display:flex;gap:10px;align-items:center;font:700 19px var(--display);color:#fff;text-decoration:none}.top .brand svg{width:28px;height:20px}
.top nav{margin-left:auto;display:flex;gap:20px;flex-wrap:wrap;align-items:center}.top nav a{color:#d7deea;text-decoration:none;font-size:14.5px}.top nav a:hover{color:#fff;text-decoration:underline}
.top nav a.cta{border:1.5px solid var(--blue);padding:8px 14px;border-radius:8px;font-weight:600;color:#fff}.top nav a.cta:hover{background:var(--blue);color:#090e19;text-decoration:none}
h1,h2{font-family:var(--display)}
.switch{background:var(--surface);border-bottom:1px solid var(--line)}.switch .in{max-width:1220px;margin:0 auto;padding:8px 24px;display:flex;gap:8px;overflow-x:auto;align-items:center}
.switch span{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;white-space:nowrap;margin-right:4px}
.switch a{white-space:nowrap;font-size:13px;text-decoration:none;color:var(--text2);border:1px solid var(--line);border-radius:999px;padding:3px 12px}
.switch a:hover{border-color:var(--blue);color:var(--text)}.switch a.on{background:var(--blue);color:#090e19;border-color:var(--blue);font-weight:600}
.wrap{max-width:1220px;margin:0 auto;padding:28px 24px 64px}.layout{display:grid;grid-template-columns:200px minmax(0,1fr);gap:36px}
.toc{position:sticky;top:16px;align-self:start;font-size:13px}.toc b{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.toc a{display:block;color:var(--text2);text-decoration:none;padding:5px 10px;border-left:2px solid var(--line)}.toc a:hover{color:var(--text);border-left-color:var(--blue)}
h1{font-size:34px;line-height:1.15;margin:6px 0 8px;letter-spacing:-.01em}h2{font-size:21px;margin:0 0 4px;letter-spacing:-.005em}h3{font-size:15px;margin:0 0 8px}
section{margin-top:44px;scroll-margin-top:16px}.q{color:var(--text2);margin:0 0 14px;max-width:760px}
.kicker{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}.lede{font-size:18px;color:var(--text2);max-width:780px;margin:0 0 6px}
.meta{font-size:13px;color:var(--muted)}.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0 14px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}.kpi .l{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.kpi b{display:block;font-size:30px;line-height:1.2;margin:2px 0;font-variant-numeric:tabular-nums}.kpi .s{font-size:13px;color:var(--text2)}
.calls{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}.call{background:var(--surface);border:1px solid var(--line);border-top:3px solid var(--blue);border-radius:12px;padding:16px 18px}
.call .t{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--blue);font-weight:700}.call h3{font-size:17px;margin:4px 0 6px;line-height:1.3}.call p{margin:0;font-size:14px;color:var(--text2)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:14px}.note{font-size:13px;color:var(--text2)}.small{font-size:12px;color:var(--muted)}
.caveat{border:1px solid var(--line);border-left:3px solid var(--orange);border-radius:8px;padding:9px 14px;margin:14px 0;font-size:13px;color:var(--text2);background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:middle}
th:first-child,td:first-child,td.l,th.l{text-align:left}th{font-weight:600;color:var(--muted);font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;background:var(--surface2);position:sticky;top:0}
tbody tr:hover td{background:var(--surface2)}.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--surface)}.scroll table tr:last-child td{border-bottom:0}
.chip{display:inline-block;font-size:12px;border-radius:999px;padding:2px 10px;background:var(--chip);color:var(--text2);white-space:nowrap}.chip.own{border:1px solid var(--line);background:transparent}
.bar{display:inline-block;height:8px;border-radius:4px;background:var(--blue);vertical-align:middle;margin-right:8px}.bar.o{background:var(--orange)}
.barcell{white-space:nowrap;text-align:left}.barcell span.v{display:inline-block;min-width:38px;text-align:right;margin-right:8px}
svg{display:block;width:100%;height:auto}svg text{font:12px Inter,system-ui,-apple-system,sans-serif;fill:var(--text2)}svg .v{fill:var(--text);font-weight:600}svg .t{fill:var(--muted);font-size:11px}
.legend{font-size:12.5px;color:var(--text2);display:flex;gap:16px;flex-wrap:wrap;margin:2px 0 10px}.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}
.nd{stroke:var(--line);fill:var(--surface2)}.nd.m{stroke:var(--blue);fill:rgba(var(--heat),.12)}.nd.k{stroke:var(--orange);fill:rgba(235,104,52,.13)}.fl{stroke:var(--muted);stroke-width:1.4;fill:none}.fl.k{stroke:var(--orange)}.lanebg{fill:none;stroke:var(--line)}
.sw-b{background:var(--blue)}.sw-o{background:var(--orange)}.sw-g{background:var(--muted)}
details{margin:10px 0}summary{cursor:pointer;font-size:13px;color:var(--text2)}blockquote{margin:6px 0;padding:6px 14px;border-left:3px solid var(--line);color:var(--text2);font-size:14px;background:var(--surface);border-radius:0 8px 8px 0}
.team{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:10px 0}.team h3{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.team ul{margin:6px 0 0;padding-left:20px}.team li{margin:4px 0}
.games{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}.game{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;text-decoration:none;color:var(--text);display:block}
.game:hover{border-color:var(--blue)}.game b{font-size:17px}.game .row{display:flex;gap:18px;margin-top:10px}.game .row div{font-size:12px;color:var(--muted)}
.game .row strong{display:block;font-size:19px;color:var(--text);font-variant-numeric:tabular-nums}
.dl a{display:inline-block;margin:0 8px 8px 0;font-size:13px;border:1px solid var(--line);border-radius:8px;padding:5px 12px;text-decoration:none;background:var(--surface)}
footer{border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);background:var(--surface)}footer div{max-width:1220px;margin:0 auto;padding:18px 24px}
@media (max-width:900px){.layout{grid-template-columns:minmax(0,1fr)}.toc{display:none}h1{font-size:27px}.grid2{grid-template-columns:minmax(0,1fr)}}
@media print{.top nav,.switch,.toc{display:none}.layout{grid-template-columns:1fr}section{break-inside:avoid}}
.hero-bg{position:relative;overflow:hidden}.glow{position:absolute;border-radius:50%;pointer-events:none;animation:drift 14s ease-in-out infinite}
.glow.g1{top:-180px;right:-120px;width:620px;height:620px;background:radial-gradient(circle,rgba(90,156,236,.34),rgba(90,156,236,0) 68%)}
.glow.g2{top:260px;left:-220px;width:560px;height:560px;background:radial-gradient(circle,rgba(240,129,82,.2),rgba(240,129,82,0) 68%);animation-delay:-6s}
.pulseline{position:absolute;top:-56px;left:0;width:100%;height:160px;pointer-events:none;opacity:.5}.pulseline polyline{stroke-dasharray:1400;stroke-dashoffset:1400;animation:trace 3.2s ease-out .2s forwards}
.hero{position:relative;display:flex;flex-wrap:wrap;gap:48px;align-items:center;padding-top:48px;padding-bottom:28px}
.hero .htext{flex:1 1 480px;min-width:0;display:flex;flex-direction:column;gap:18px;align-items:flex-start}
h1.big{font-size:50px;line-height:1.08;letter-spacing:-.02em;margin:0}.hero .lede{margin:0;max-width:560px}
.btn{display:inline-block;text-decoration:none;background:var(--blue);color:#090e19;padding:13px 20px;border-radius:10px;font:600 15.5px Inter,system-ui,sans-serif;border:0;cursor:pointer;box-shadow:0 14px 30px -10px rgba(90,156,236,.7)}
.btn:hover{background:#7db4f5}.btn:focus-visible,.pill:focus-visible{outline:2px solid var(--focus);outline-offset:3px}
.tiltwrap{flex:1 1 400px;min-width:0;perspective:1100px}.stack{position:relative;transform-style:preserve-3d;transition:transform .18s ease-out}
.layer{position:absolute;inset:0;border-radius:22px}.layer.l2{transform:translate3d(26px,26px,-60px);background:#111a2c;border:1px solid #1f2b44}.layer.l1{transform:translate3d(13px,13px,-30px);background:#142037;border:1px solid #263654}
.panel{position:relative;background:linear-gradient(160deg,#1c2a47,#131c30);border:1px solid #34486f;border-radius:22px;padding:26px;display:flex;flex-direction:column;gap:16px;box-shadow:0 40px 70px -30px rgba(0,0,0,.85)}
.kick{font-size:13px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:600}
.pills{display:flex;flex-wrap:wrap;gap:8px}.pill{cursor:pointer;font:600 13px Inter,system-ui,sans-serif;border:1px solid #3a4a6b;background:transparent;color:#d7deea;padding:8px 12px;border-radius:999px;min-height:36px;transition:background .2s,color .2s}
.pill[aria-pressed="true"]{background:var(--blue);border-color:var(--blue);color:#090e19}
.tlegend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:#d7deea}.tlegend span{display:inline-flex;align-items:center;gap:6px}.tlegend svg,.grow svg{width:15px;height:15px;flex:none}
.chartg{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;align-items:end;height:216px;border-bottom:1px solid #2b3b5c}
.chartg .col{display:flex;gap:5px;align-items:flex-end;justify-content:center;transition:opacity .35s ease}.chartg .vb{display:flex;flex-direction:column;align-items:center;gap:5px}
.chartg .vb span{font-size:12.5px;font-weight:600}.chartg .b{width:26px;border-radius:5px 5px 0 0;transform-origin:bottom;animation:growy 1.1s cubic-bezier(.2,.8,.2,1) both}
.chartg .b.p{background:linear-gradient(180deg,#7db4f5,#3b7fd6);box-shadow:0 0 16px rgba(90,156,236,.45)}.chartg .b.n{background:linear-gradient(180deg,#f6a07a,#d9622f);box-shadow:0 0 16px rgba(240,129,82,.4)}
.chartlab{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;font-size:12px;color:var(--muted);text-align:center}.chartlab div{transition:opacity .35s ease}
.dim{opacity:.28}.pnote{font-size:14px;line-height:1.5;color:var(--text2);border-top:1px solid #2b3b5c;padding-top:14px;min-height:3em}
.shead{display:flex;flex-wrap:wrap;gap:12px;align-items:baseline;justify-content:space-between;margin-bottom:16px}.shead h2{font-size:26px;margin:0}
.gcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}
.gcard{text-decoration:none;color:var(--text);background:linear-gradient(165deg,#18233b,#111a2c);border:1px solid var(--line);border-radius:18px;padding:22px;display:flex;flex-direction:column;gap:14px;box-shadow:0 18px 36px -22px rgba(0,0,0,.8)}
.gcard .gh{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.gcard .gn{font:600 18px var(--display)}.gcard .gs{font-size:13px;color:var(--muted)}.gcard .gr{font-size:12.5px;color:var(--muted);white-space:nowrap}
.grow{display:flex;align-items:center;gap:10px;font-size:13.5px;margin-top:7px}.grow b{width:36px}.grow .tr{flex:1;height:10px;background:#0b1120;border-radius:5px}.grow .tr i{display:block;height:10px;border-radius:5px;transform-origin:left;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}
.gfacts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;border-top:1px solid var(--line);padding-top:12px}.gfacts small{display:block;font-size:12px;color:var(--muted)}.gfacts b{font-size:15px}
.gopen{font-size:14px;color:#8fbdf5;font-weight:600}
.lift{transition:transform .25s ease,box-shadow .25s ease,border-color .25s ease}.lift:hover{transform:translateY(-8px);box-shadow:0 28px 50px -18px rgba(0,0,0,.75),0 0 0 1px #3d5a94;border-color:#3d5a94}
.rise{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}
.req{background:linear-gradient(120deg,#1d2d4f,#16223a);border:1px solid #34486f;border-radius:18px;padding:28px;display:flex;flex-wrap:wrap;gap:28px;align-items:flex-start;box-shadow:0 24px 48px -28px rgba(0,0,0,.85)}
.req .rt{flex:1 1 300px;min-width:0}.req h2{font-size:23px;margin:0 0 8px}.req p{margin:0;font-size:15.5px;color:#d7deea}
.req form{flex:2 1 480px;min-width:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}.req .f{display:flex;flex-direction:column;gap:6px;justify-content:flex-end}.req label{font-size:13px;color:#d7deea}
.req input{font:inherit;color:var(--text);background:#0b1120;border:1px solid #3a4a6b;border-radius:8px;padding:11px 12px;min-height:44px;width:100%}.req .fb{grid-column:1/-1;font-size:14px;color:#d7deea}
.more{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px}.mcard{text-decoration:none;color:var(--text);background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:22px;display:flex;flex-direction:column;gap:6px}
.mcard b{font:600 18px var(--display)}.mcard span{font-size:14.5px;color:var(--text2)}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}@keyframes growy{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes rise{from{opacity:.01;transform:translateY(22px)}to{opacity:1;transform:none}}@keyframes trace{to{stroke-dashoffset:0}}@keyframes drift{0%,100%{transform:translate(0,0)}50%{transform:translate(30px,-24px)}}
@media (max-width:900px){h1.big{font-size:34px}.hero{gap:28px;padding-top:28px}.layer{display:none}.chartg .b{width:18px}.chartg .col{gap:3px}.panel{padding:20px}}
@media (prefers-reduced-motion:reduce){.glow,.rise,.chartg .b,.grow .tr i{animation:none}.pulseline polyline{animation:none;stroke-dashoffset:0}.lift,.stack{transition:none}}
"""


def page(title, body, ov, depth=0, desc="", current=None):
    up = "../" * depth
    pills = "".join(f'<a class="{"on" if o["slug"] == current else ""}" href="{up}games/{E(o["slug"])}.html">{E(o["name"])}</a>' for o in ov)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700&display=swap" rel="stylesheet"><style>{CSS}</style></head><body>
<div class="top"><div class="in"><a class="brand" href="{up}index.html"><svg viewBox="0 0 28 20" aria-hidden="true"><polyline points="1,14 7,14 10,4 14,18 18,8 21,14 27,14" fill="none" stroke="#5a9cec" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>Player Signals</a>
<nav><a href="{up}index.html#games">Reports</a><a href="{up}quit.html">Why players quit</a><a href="{up}fans.html">When fans review</a><a href="{up}data.html">The numbers</a><a href="{up}case-study.html">Case study</a><a href="{up}method.html">Method &amp; limits</a><a href="{REPO}">Code &amp; data</a><a class="cta" href="{up}index.html#request">Request a report</a></nav></div></div>
<div class="switch"><div class="in"><span>Reports</span>{pills}</div></div>
{body}
<footer><div>A free, public student research project built only from public Steam data, with an AI agent. Not affiliated with Valve or with any studio or publisher named here.
Reviews describe only the players who chose to write one. Nothing on this site shows that one thing caused another. No raw review text or reviewer IDs are published.</div></footer>
</body></html>"""


# ---------- SVG helpers (one axis per chart; hover text via <title>) ----------
def hbar(rows, color="var(--blue)", width=560, label_w=190, fmt=pct, xmax=None, ref=None, ref_label="", whisk=False):
    rows = [r for r in rows if r["value"] is not None]
    if not rows: return "<p class='note'>Not enough reviews to show this chart.</p>"
    bh, gap, top = 18, 9, 22 if ref is not None else 6
    h = top + len(rows) * (bh + gap) + 6; pw = width - label_w - 58
    xmax = xmax or max([r.get("hi") or r["value"] for r in rows] + [ref or 0]) * 1.08 or 1
    s = [f'<svg viewBox="0 0 {width} {h}" role="img">']
    if ref is not None:
        x = label_w + ref / xmax * pw
        s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top-4}" y2="{h-4}" stroke="var(--muted)" stroke-dasharray="3 3"/><text class="t" x="{x:.1f}" y="11" text-anchor="middle">{E(ref_label)} {fmt(ref)}</text>')
    for i, r in enumerate(rows):
        y = top + i * (bh + gap); w = max(r["value"] / xmax * pw, 1)
        s.append(f'<g><title>{E(r["tip"])}</title><text x="{label_w-8}" y="{y+13}" text-anchor="end">{E(r["label"])}</text>'
                 f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bh}" rx="4" fill="{color}"/>')
        end = label_w + w
        if whisk and r.get("lo") is not None:
            x1, x2 = label_w + r["lo"] / xmax * pw, label_w + r["hi"] / xmax * pw; end = x2
            s.append(f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y+bh/2}" y2="{y+bh/2}" stroke="var(--text)" stroke-width="1.5"/>')
        s.append(f'<text class="v" x="{end+6:.1f}" y="{y+13}">{fmt(r["value"])}</text></g>')
    return "".join(s) + "</svg>"


def columns(rows, color="var(--blue)", width=460, height=200, fmt=pct):
    rows = [r for r in rows if r["value"] is not None]
    if not rows: return "<p class='note'>Not enough reviews to show this chart.</p>"
    top, bot = 22, 30; ph = height - top - bot; vmax = max(r["value"] for r in rows) * 1.05 or 1
    slot = width / len(rows); bw = min(slot - 14, 64)
    s = [f'<svg viewBox="0 0 {width} {height}" role="img">', f'<line x1="0" x2="{width}" y1="{top+ph}" y2="{top+ph}" stroke="var(--grid)"/>']
    for i, r in enumerate(rows):
        x = i * slot + (slot - bw) / 2; bh = max(r["value"] / vmax * ph, 1); y = top + ph - bh
        s.append(f'<g><title>{E(r["tip"])}</title><rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{color}"/>'
                 f'<text class="v" x="{x+bw/2:.1f}" y="{y-6:.1f}" text-anchor="middle">{fmt(r["value"])}</text>'
                 f'<text x="{x+bw/2:.1f}" y="{height-10}" text-anchor="middle">{E(r["label"])}</text></g>')
    return "".join(s) + "</svg>"


def priority_map(reasons, avg):
    """x = share of labeled negative reviews, y = walk-away rate. One series; every point is labeled."""
    pts = [r for r in reasons if r["code"] != "OTHER" and r["walk_n"] >= 100 and r["walk_rate"] is not None]
    if len(pts) < 2: return "<p class='note'>Not enough reviews to draw the map.</p>"
    W, H, L, R, T, B = 720, 400, 52, 24, 26, 44; pw, ph = W - L - R, H - T - B
    xmax = max(r["share"] for r in pts) * 1.15
    lo = min([r["walk_rate"] for r in pts] + [avg]); hi = max([r["walk_rate"] for r in pts] + [avg]); pad = max((hi - lo) * .18, .02)
    y0, y1 = max(lo - pad, 0), min(hi + pad, 1)
    X = lambda v: L + v / xmax * pw; Y = lambda v: T + (y1 - v) / (y1 - y0) * ph
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Priority map of complaint groups">']
    ya = Y(avg)
    s.append(f'<rect x="{L}" y="{T}" width="{pw}" height="{ya-T:.1f}" fill="var(--orange)" opacity=".06"/>')
    for i in range(5):
        v = y0 + (y1 - y0) * i / 4; y = Y(v)
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--grid)"/><text class="t" x="{L-8}" y="{y+4:.1f}" text-anchor="end">{pct(v)}</text>')
    for i in range(5):
        v = xmax * i / 4; x = X(v)
        s.append(f'<text class="t" x="{x:.1f}" y="{H-B+16}" text-anchor="middle">{pct(v)}</text>')
    s.append(f'<line x1="{L}" x2="{W-R}" y1="{ya:.1f}" y2="{ya:.1f}" stroke="var(--muted)" stroke-dasharray="4 4"/>'
             f'<text class="t" x="{W-R}" y="{ya-6:.1f}" text-anchor="end">all negative reviewers: {pct(avg)} walked away</text>')
    s.append(f'<text class="t" x="{L+6}" y="{T+14}">▲ these reviewers left more often</text><text class="t" x="{L+6}" y="{H-B-8}">▼ these reviewers stayed more often</text>')
    s.append(f'<text class="t" x="{L+pw/2}" y="{H-6}" text-anchor="middle">Share of labeled negative reviews (how loud the complaint is) →</text>')
    s.append(f'<text class="t" transform="translate(13 {T+ph/2}) rotate(-90)" text-anchor="middle">Walked away after reviewing →</text>')
    # label positions: keep each label level with its point where possible; if labels would collide, spread them and draw a leader line
    items = sorted(pts, key=lambda r: Y(r["walk_rate"]))
    lab_y = []
    for r in items:
        y = Y(r["walk_rate"]) + 4
        if lab_y and y - lab_y[-1] < 15: y = lab_y[-1] + 15
        lab_y.append(y)
    over = lab_y[-1] - (H - B - 4) if lab_y else 0
    if over > 0: lab_y = [y - over for y in lab_y]
    for r, ly in zip(items, lab_y):
        x, y = X(r["share"]), Y(r["walk_rate"])
        right = x < L + pw * .72; moved = abs(ly - 4 - y) > 3
        lx = x + (22 if moved else 11) if right else x - (22 if moved else 11)
        tip = f'{r["reason"]}: {pct(r["share"])} of labeled negative reviews; {pct(r["walk_rate"])} of {r["walk_n"]:,} reviewers walked away (95% interval {pct(r["walk_lo"])}–{pct(r["walk_hi"])})'
        lead = f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{lx + (-3 if right else 3):.1f}" y2="{ly-4:.1f}" stroke="var(--muted)" stroke-width="1"/>' if moved else ""
        s.append(f'<g><title>{E(tip)}</title><line x1="{x:.1f}" x2="{x:.1f}" y1="{Y(r["walk_lo"]):.1f}" y2="{Y(r["walk_hi"]):.1f}" stroke="var(--blue)" stroke-width="1.5" opacity=".45"/>{lead}'
                 f'<circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="transparent"/><circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="var(--blue)" stroke="var(--surface)" stroke-width="2"/>'
                 f'<text class="v" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{"start" if right else "end"}">{E(r["reason"])}</text></g>')
    return "".join(s) + "</svg>"


def timeline(monthly):
    n = len(monthly)
    if n < 2: return ""
    W, L, R = 980, 48, 12; pw = W - L - R; step = pw / n
    h1, h2, gap, top = 110, 130, 36, 18; H = top + h1 + gap + h2 + 34
    vmax = max(m["reviews"] for m in monthly) or 1
    s = [f'<svg viewBox="0 0 {W} {H}" role="img">', f'<text class="t" x="{L}" y="11">Reviews per month (blue) and negative reviews (orange)</text>']
    for i, m in enumerate(monthly):
        x = L + i * step; bw = max(step - 2, 1); b1 = m["reviews"] / vmax * h1; b2 = m["negative"] / vmax * h1
        tip = f'{m["month"]}: {m["reviews"]:,} reviews, {m["negative"]:,} negative ({pct(m["negative_share"])})' + (f' · official patch posts: {len(m["patches"])}' if m["patches"] else "")
        s.append(f'<g><title>{E(tip)}</title><rect x="{x:.1f}" y="{top+h1-b1:.1f}" width="{bw:.1f}" height="{max(b1,1):.1f}" rx="2" fill="var(--blue)"/>'
                 f'<rect x="{x:.1f}" y="{top+h1-b2:.1f}" width="{bw:.1f}" height="{max(b2,1):.1f}" rx="2" fill="var(--orange)"/></g>')
    s.append(f'<text class="t" x="{L-6}" y="{top+8}" text-anchor="end">{vmax:,}</text><text class="t" x="{L-6}" y="{top+h1}" text-anchor="end">0</text>')
    y0 = top + h1 + gap
    s.append(f'<text class="t" x="{L}" y="{y0-9}">Negative share of that month\'s reviews (months with 30+ reviews). Ticks under the axis = months with an official patch or update post.</text>')
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


def pair_columns(rows, width=720, height=250):
    """Two bars per group: recommended (blue) and not recommended (orange). rows: label, a, b, tip."""
    top, bot = 24, 32; ph = height - top - bot; vmax = max(max(r["a"] or 0, r["b"] or 0) for r in rows) * 1.08 or 1
    slot = width / len(rows); bw = min((slot - 28) / 2, 46)
    s = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Share of reviewers who logged under one more hour after reviewing, by hours played at review, recommended against not recommended">', f'<line x1="0" x2="{width}" y1="{top+ph}" y2="{top+ph}" stroke="var(--grid)"/>']
    for i, r in enumerate(rows):
        cx = i * slot + slot / 2
        for v, x, col in [(r["a"], cx - bw - 2, "var(--blue)"), (r["b"], cx + 2, "var(--orange)")]:
            if v is None: continue
            bh = max(v / vmax * ph, 1); y = top + ph - bh
            s.append(f'<g><title>{E(r["tip"])}</title><rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{col}"/><text class="v" x="{x+bw/2:.1f}" y="{y-6:.1f}" text-anchor="middle">{pct(v)}</text></g>')
        s.append(f'<text x="{cx:.1f}" y="{height-10}" text-anchor="middle">{E(r["label"])}</text>')
    return "".join(s) + "</svg>"


def heat(v, n_text=""):
    return "<td>–</td>" if v is None else f'<td style="background:rgba(var(--heat),{min(v*1.6,0.85):.2f})" title="{E(n_text)}">{pct(v)}</td>'


def barcell(v, cls="", scale=120):
    return "<td>–</td>" if v is None else f'<td class="barcell"><span class="v">{pct(v)}</span><span class="bar {cls}" style="width:{max(v*scale,2):.0f}px"></span></td>'


def model_block(m, scope="this game's"):
    if not m or not m.get("ok"): return ""
    named = [r for r in m["rows"] if r["code"] not in ("OTHER", "OFFGAME")]; oth = next((r for r in m["rows"] if r["code"] == "OTHER"), None)
    extra = f" Reviewers whose main complaint was {E(m['reference_reason'].lower())} are the comparison group because they stay most often, so each row reads as how much more often that group walked away than they did."
    if oth and named:
        k = sum(r["odds_ratio"] < oth["odds_ratio"] for r in named)
        extra += f" Reviews with no clear reason sit at {oth['odds_ratio']:.2f}×, higher than {k} of the {len(named)} named complaint types, so the complaint label explains only part of who leaves."
    rows = "".join(f"<tr><td>{E(r['reason'])}</td><td>{num(r['n'])}</td><td><b>{r['odds_ratio']:.2f}×</b></td><td>{r['lo']:.2f}–{r['hi']:.2f}</td><td>{'under 0.001' if r['p'] < 0.001 else f'{r[chr(112)]:.3f}'}</td>"
                   f"<td class='l'><span class='chip'>{'▲ more likely to leave' if r['lo'] > 1 else '▼ less likely to leave' if r['hi'] < 1 else '● no clear difference'}</span></td></tr>" for r in m["rows"])
    return (f"<h3 style='margin-top:22px'>Does it hold after controls?</h3><p class='note'>A logistic regression on {num(m['n'])} of {scope} labeled negative reviews predicts walking away from the main complaint "
            f"while holding constant hours played at review, review language, how long after launch the review was written, and whether it was edited. Each row compares a complaint with <b>{E(m['reference_reason'].lower())}</b>: "
            f"2.00× means twice the odds of having walked away. This narrows the comparison; it still does not show cause.{extra}</p>"
            f"<div class='scroll'><table><thead><tr><th>Main complaint</th><th>Reviews</th><th>Odds of walking away vs. {E(m['reference_reason'].lower())}</th><th>95% interval</th><th>p-value</th><th class='l'>Reading</th></tr></thead><tbody>{rows}</tbody></table></div>")


def sens_line(sv):
    a, b, c = sv
    return (f"\"Walked away\" is set at under 1 more hour. At under {b['hours']} hours the negative-reviewer rate is {pct(b['negative_walk_rate'])} and {b['same_verdict_as_1h']} of {b['complaint_groups']} complaint groups keep the same verdict; "
            f"at under {c['hours']} hours it is {pct(c['negative_walk_rate'])} and {c['same_verdict_as_1h']} of {c['complaint_groups']} keep it (rank correlation with the 1-hour ordering: {b['rank_correlation_with_1h']:.2f} and {c['rank_correlation_with_1h']:.2f}).")


def sub_block(sr):
    if not sr: return ""
    rows = ""
    for r in sr["rows"]:
        sym, vt = VERDICT[r["vs_design_average"]]
        rows += (f"<tr><td>{E(r['sub_reason'])}</td><td>{num(r['n'])}</td>{barcell(r['share'])}<td>{pct(r['share_english'])}</td><td>{pct(r['share_other_languages'])}</td>"
                 f"{barcell(r['walk_rate'], 'o')}<td class='l'><span class='chip'>{sym} {vt}</span></td><td>{r['median_hours_at_review']}</td></tr>")
    return (f"<section id='inside'><h2>Inside \"{E(sr['parent_reason'].lower())}\"</h2><p class='q'>The largest complaint group is too broad to act on. A second pass sorted {num(sr['labeled'])} of these reviews by the design choice they name.</p>"
            f"<div class='scroll'><table><thead><tr><th>Design choice named</th><th>Reviews</th><th class='l'>Share of design complaints</th><th>Among English reviews</th><th>Among other languages</th>"
            f"<th class='l'>Walked away</th><th class='l'>Versus all design complaints ({pct(sr['parent_walk_rate'])})</th><th>Median hours at review</th></tr></thead><tbody>{rows}</tbody></table></div>"
            f"<p class='note'>Same method and caveats as the main labels; this second-level pass was run for this game only and was not separately accuracy-checked.</p></section>")


PLAYBOOK = {
    "PERF": ["Compare session length and next-day return by hardware tier in your own telemetry; reviews cannot see hardware.",
             "Publish a performance target per spec tier and report against it in patch notes, so waiting players know when to return."],
    "STAB": ["Rank crash signatures and save-loss bugs by how many players hit them in their first sessions, not by ticket count.",
             "Check whether players who crashed in session one or two ever started a third session."],
    "CONTENT": ["Find the hour mark where these reviews cluster and look at what players have run out of by then.",
                "State on the store page what is in the game today versus planned, so expectations match the build."],
    "DESIGN": ["Separate 'I dislike this mechanic' from 'this mechanic is unclear': the first is a design call, the second is onboarding.",
               "Test optional rule settings or modes for the most-named mechanic and measure retention of players who switch them on."],
    "UI": ["Run task-based usability checks on the screens named most often; interface complaints are specific and cheap to verify.",
           "Ship interface fixes in small, frequent patches and list them first in the notes."],
    "MONET": ["Compare refund and early-exit rates across editions, regions and price points; price complaints concentrate before much play.",
              "Check whether paid add-ons land while core complaints are still open; the spike list shows review timing around such posts."],
    "ONLINE": ["Track failed logins, disconnects and matchmaking time-outs per player and tie them to next-day return.",
               "If an account or always-online requirement is named, measure how many players drop at that exact step."],
    "SUPPORT": ["Audit promised-versus-shipped items in public posts; these reviewers are usually long-time players reacting to a specific change.",
                "After a patch that triggers a review spike, compare return rates of players active the week before with earlier weeks."],
    "STORY": ["Use quest and dialogue completion telemetry to find where players stop following the main story.",
              "Treat this as input for the next content release more than for patches."],
}


def audit_line(audit, long=False):
    if not audit: return "label accuracy check pending"
    s = f"in a second-model check of {audit['n']} random labels across languages, {pct(audit['main_agree'])} of main reasons were judged correct"
    if long: s = s[0].upper() + s[1:] + f" and {pct(audit['quit_agree'])} of quit-statement tags; expect roughly that error rate in reason shares."
    return s


def game_page(o, audit, ov):
    b = o["behaviour"]; bn, bp = b["negative"], b["positive"]; ovw = o["overview"]; f = o["funnel"]
    reasons = [r for r in o["reasons"] if r["n"] > 0]
    named = [r for r in reasons if r["code"] not in ("OTHER", "OFFGAME")]
    big = [r for r in named if r["walk_n"] >= 100 and r["walk_rate"] is not None]
    his = sorted([r for r in big if r["vs_game_average"] == "higher"], key=lambda r: -r["share"])
    los = sorted([r for r in big if r["vs_game_average"] == "lower"], key=lambda r: -r["share"])
    pt = o["playtime"]; svd = {r["code"]: r for r in o["said_vs_did"]}; early = pt[0]
    langs = o["languages"]; nlang = [l for l in langs if l["code"] != "_small"]

    # ---- three calls (all text built from the data)
    if his:
        gap = lambda r: round(r["walk_rate"] * 100) - round(bn["walk_rate"] * 100)
        top = max(his, key=lambda r: r["walk_rate"]); rest = [r for r in his if r is not top]
        c1h = f"{E(top['reason'])} critics leave most often"
        c1p = f"{pct(top['walk_rate'])} of these reviewers logged under 1 more hour, against {pct(bn['walk_rate'])} for all negative reviewers ({gap(top)} point{'' if gap(top) == 1 else 's'} higher), on {pct(top['share'])} of negative reviews."
        if rest and rest[0]["share"] > top["share"]:
            c1p += f" The largest group above average is {E(rest[0]['reason'].lower())} ({pct(rest[0]['share'])} of reviews), where the gap is {gap(rest[0])} point{'' if gap(rest[0]) == 1 else 's'} ({pct(rest[0]['walk_rate'])})."; rest = rest[1:]
        if rest: c1p += f" Also above average: {', '.join(E(r['reason'].lower()) for r in rest[:2])}."
    else:
        c1h = "No complaint group stands out for leaving"; c1p = f"Every large complaint group sits within its margin of the overall {pct(bn['walk_rate'])} walk-away rate."
    if los: c1p += f" The loudest group that mostly stays: {E(los[0]['reason'].lower())} ({pct(los[0]['share'])} of reviews, {pct(los[0]['walk_rate'])} walked away)."
    c2h = f"{pct(early['neg_walk_rate'])} of under-2-hour critics stop there, inside Steam's refund window" if early["neg_walk_rate"] is not None else "Early hours"
    c2p = f"{pct(early['negative_share_in_bucket'])} of reviews written with under 2 hours played are negative ({num(early['negative'])} reviews), and {pct(early['neg_walk_rate'])} of those reviewers never logged another hour. Steam refunds are available up to 2 hours of play, so some of them stopped to stay eligible, whatever they complained about ({pct(bn['refunded_rate'])} of all negative reviews carry the refund flag). Median playtime at a negative review: {ovw['median_hours_at_negative_review']} h."
    w = svd["WAITING"]
    c3h = f"{pct(w['share'])} of critics said they would come back"
    c3p = f"{num(w['n'])} reviewers wrote that they are waiting for fixes; {pct(w['kept_10h_rate'])} of them went on to play 10+ more hours. Overall, {pct(bn['kept_10h_rate'])} of negative reviewers played 10+ more hours and {pct(bn['active_now_rate'])} played in the two weeks before the snapshot."
    calls = "".join(f'<div class="call"><div class="t">{t}</div><h3>{h}</h3><p>{p}</p></div>' for t, h, p in [("Prioritize", c1h, c1p), ("Protect", c2h, c2p), ("Win back", c3h, c3p)])

    kpis = "".join(f'<div class="kpi"><div class="l">{E(l)}</div><b>{v}</b><div class="s">{E(s)}</div></div>' for l, v, s in [
        ("Reviews analysed", num(ovw["reviews"]), f"{f['languages']} languages · {pct(f['english']/ovw['reviews'])} English"),
        ("Negative", pct(ovw["negative_share"]), f"{num(ovw['negative'])} reviews"),
        ("Walked away", pct(bn["walk_rate"]), "of negative reviewers logged under 1 more hour"),
        ("Kept playing", pct(bn["kept_10h_rate"]), "of negative reviewers played 10+ more hours"),
        ("Refunded", pct(bn["refunded_rate"]), "of negative reviews carry Steam's refund flag")])

    # ---- priority table
    prow = ""
    for r in reasons:
        sym, vt = VERDICT[r["vs_game_average"]]
        prow += (f"<tr><td>{E(r['reason'])}</td><td class='l'><span class='chip own'>{E(OWNER[r['code']])}</span></td><td>{num(r['n'])}</td>{barcell(r['share'])}"
                 f"{barcell(r['walk_rate'], 'o')}<td>{pct(r['walk_rate_adjusted'])}</td><td class='l'><span class='chip'>{sym} {vt}</span></td><td>{r['median_hours_at_review']}</td></tr>")
    ptable = ("<div class='scroll'><table><thead><tr><th>Complaint</th><th class='l'>Likely owner</th><th>Reviews</th><th class='l'>Share of negative</th><th class='l'>Walked away</th>"
              "<th>Adjusted for hours played</th><th class='l'>Versus all critics</th><th>Median hours at review</th></tr></thead><tbody>" + prow + "</tbody></table></div>")

    # ---- when
    c1 = columns([dict(label=p["bucket"], value=p["negative_share_in_bucket"], tip=f'{p["bucket"]}: {p["negative"]:,} of {p["reviews"]:,} reviews negative') for p in pt])
    c2 = columns([dict(label=p["bucket"], value=p["neg_walk_rate"], tip=f'{p["bucket"]}: walk-away rate among {p["neg_walk_n"]:,} negative reviewers') for p in pt], color="var(--orange)")
    hcodes = [r["code"] for r in named[:6]]
    hrows = "".join(f'<tr><td>{E(g["bucket"])} <span class="small">n={g["n"]:,}</span></td>' + "".join(heat(g["shares"][c], f'{REASONS[c]}, {g["bucket"]}') for c in hcodes) + "</tr>" for g in o["reason_by_playtime"])
    htable = f'<div class="scroll"><table><thead><tr><th>Hours played at review</th>{"".join(f"<th>{E(SHORT[c])}</th>" for c in hcodes)}</tr></thead><tbody>{hrows}</tbody></table></div>'
    pt_table = "<div class='scroll'><table><thead><tr><th>Hours at review</th><th>Reviews</th><th>Negative</th><th>Negative share</th><th>Share of all negative</th><th>Negative reviewers who walked away</th></tr></thead><tbody>" + "".join(
        f"<tr><td>{E(p['bucket'])}</td><td>{num(p['reviews'])}</td><td>{num(p['negative'])}</td><td>{pct(p['negative_share_in_bucket'])}</td><td>{pct(p['share_of_all_negative'])}</td><td>{pct(p['neg_walk_rate'])}</td></tr>" for p in pt) + "</tbody></table></div>"

    # ---- markets
    lcodes = o["language_reason_columns"]
    lrow = "".join(f"<tr><td>{E(l['language'])}</td><td>{num(l['reviews'])}</td><td>{pct(l['share_of_reviews'])}</td>{barcell(l['negative_share'])}{barcell(l['neg_walk_rate'], 'o')}"
                   f"<td>{l['median_hours_at_negative_review'] if l['median_hours_at_negative_review'] is not None else '–'}</td><td class='l'>{E(l['top_reason'] or '–')}{' (' + pct(l['top_reason_share']) + ')' if l['top_reason_share'] is not None else ''}</td></tr>" for l in langs)
    ltable = ("<div class='scroll'><table><thead><tr><th>Review language</th><th>Reviews</th><th>Share</th><th class='l'>Negative share</th><th class='l'>Negative reviewers who walked away</th>"
              "<th>Median hours at negative review</th><th class='l'>Top named complaint</th></tr></thead><tbody>" + lrow + "</tbody></table></div>")
    lheat = "".join(f"<tr><td>{E(l['language'])} <span class='small'>n={l['labeled']:,}</span></td>" + "".join(heat(l["reason_shares"].get(c), f"{REASONS[c]}, {l['language']}") for c in lcodes) + "</tr>" for l in langs)
    lheat_t = f'<div class="scroll"><table><thead><tr><th>Review language</th>{"".join(f"<th>{E(SHORT[c])}</th>" for c in lcodes)}</tr></thead><tbody>{lheat}</tbody></table></div>'
    cmp_l = [l for l in nlang if l["reviews"] >= 1000]
    mk = ""
    if len(cmp_l) >= 2:
        a, z = max(cmp_l, key=lambda l: l["negative_share"]), min(cmp_l, key=lambda l: l["negative_share"])
        mk = f"Among languages with 1,000+ reviews, the negative share runs from <b>{pct(z['negative_share'])}</b> ({E(z['language'])}) to <b>{pct(a['negative_share'])}</b> ({E(a['language'])})."
        wl = [l for l in cmp_l if l["neg_walk_rate"] is not None]
        if len(wl) >= 2:
            a2, z2 = max(wl, key=lambda l: l["neg_walk_rate"]), min(wl, key=lambda l: l["neg_walk_rate"])
            mk += f" Walk-away among negative reviewers runs from {pct(z2['neg_walk_rate'])} ({E(z2['language'])}) to {pct(a2['neg_walk_rate'])} ({E(a2['language'])})."

    svd_table = "<div class='scroll'><table><thead><tr><th>What the review said</th><th>Reviews</th><th>Share</th><th class='l'>Logged under 1 more hour</th><th class='l'>Played 10+ more hours</th><th>Played in last 2 weeks</th></tr></thead><tbody>" + "".join(
        f"<tr><td>{E(r['statement'])}</td><td>{num(r['n'])}</td><td>{pct(r['share'])}</td>{barcell(r['walk_rate'], 'o')}{barcell(r['kept_10h_rate'])}<td>{pct(r['active_now_rate'])}</td></tr>" for r in o["said_vs_did"]) + "</tbody></table></div>"

    spikes = ""
    for s in o["spikes"]:
        posts = "".join(f"<li>{E(p['date'])} — {E(p['title'])}</li>" for p in s["official_posts"]) or "<li>No official post found in that window.</li>"
        mix = "".join(f"<span class='chip'>{E(t['reason'])} {pct(t['share'])}</span> " for t in s["top_reasons"]) or "<span class='small'>too few labeled reviews to show a mix</span>"
        spikes += (f"<tr><td>{E(s['week_start'])}</td><td>{num(s['negative'])}</td><td>{s['usual_weekly_negative']:.0f}</td><td>{pct(s['negative_share'])}</td><td class='l'>{mix}</td>"
                   f"<td class='l'><details><summary>{len(s['official_posts'])} official posts nearby</summary><ul class='note'>{posts}</ul></details></td></tr>")
    spikes = ("<div class='scroll'><table><thead><tr><th>Week starting</th><th>Negative reviews</th><th>Usual week before</th><th>Negative share that week</th><th class='l'>Main complaints that week</th><th class='l'>Official posts around it</th></tr></thead><tbody>" + spikes + "</tbody></table></div>"
              ) if spikes else "<p class='note'>No week after the launch period met the spike rule.</p>"

    voices = ""
    for r in named[:5]:
        ps = o["paraphrases"].get(r["code"], [])
        if ps: voices += f"<div><h3>{E(r['reason'])}</h3>" + "".join(f"<blockquote>{E(p)}</blockquote>" for p in ps) + "</div>"

    todo = ""
    for r in named[:5]:
        tips = PLAYBOOK.get(r["code"])
        if not tips: continue
        sym, vt = VERDICT[r["vs_game_average"]]
        todo += (f"<div class='team'><h3><span class='chip own'>{E(OWNER[r['code']])}</span>{E(r['reason'])}<span class='chip'>{pct(r['share'])} of negative reviews</span><span class='chip'>{sym} {vt}</span></h3>"
                 f"<div class='note'>{pct(r['walk_rate'])} of these reviewers walked away; median {r['median_hours_at_review']} hours played at review.</div><ul>" + "".join(f"<li>{E(t)}</li>" for t in tips) + "</ul></div>")

    offgame = next((r for r in o["reasons"] if r["code"] == "OFFGAME"), None)
    off_note = f"<p class='note'><b>Off-game topics.</b> {pct(offgame['share'],1)} of labeled negative reviews ({num(offgame['n'])}) are mainly about politics, social topics, or specific people or companies rather than how the game plays. They are counted and not characterized further; this report takes no position on them.</p>" if offgame else ""

    body = f"""<div class="wrap">
<div class="kicker">Quit-signal report · {E(o['genre'])} · released {E(o['release'])}</div>
<h1>{E(o['name'])}</h1>
<p class="lede">Which complaints go with players actually leaving, when they give up, and how it differs by market.</p>
<div class="meta">{num(ovw['reviews'])} public Steam reviews in {f['languages']} languages, {f['first_review']} to {f['last_review']} · playtime snapshot {E(o['snapshot'])} · {num(f['labeled'])} negative reviews labeled by reason</div>
<div class="kpis">{kpis}</div>
<div class="calls">{calls}</div>
<div class="caveat"><b>How far this goes.</b> Reviews come only from players who chose to write one, so every share is a share of <i>reviewers</i>, not of all players. "Walked away" is read from public playtime ({num(bn['walked_away'])} of {num(bn['n'])} negative reviews at least {o['params']['mature_days']} days old). Stopping is not the same as a lost customer: this is a paid game and the median critic had already played {ovw['median_hours_at_negative_review']} hours, so a reviewer who stops late may simply have finished. Read each walk-away rate next to hours played at review. Everything below is an association to check against your own telemetry, not proof of cause.</div>
<div class="layout"><aside class="toc"><b>In this report</b><a href="#priority">1 · Priority map</a>{'<a href="#inside">&nbsp;&nbsp;&nbsp;Inside design complaints</a>' if o.get('sub_reasons') else ''}<a href="#when">2 · When they give up</a><a href="#markets">3 · Markets</a><a href="#said">4 · Said versus did</a><a href="#timeline">5 · Patches &amp; spikes</a><a href="#voices">6 · Player voice</a><a href="#teams">7 · Checks by team</a><a href="#limits">8 · Limits &amp; data</a></aside>
<div>
<section id="priority" style="margin-top:8px"><h2>1 · Priority map</h2>
<p class="q">Which complaints are loud, and which go with leaving? Right = more reviews. Up = the reviewer more often stopped playing afterwards.</p>
<div class="card">{priority_map(reasons, bn['walk_rate'])}
<div class="legend"><span><i class="sw-b"></i>one complaint group (vertical line = 95% interval)</span><span>shaded area = above the average walk-away rate</span></div></div>
<p class="note">Players with few hours leave more often whatever they complain about, so the table also gives each rate re-weighted to the game's overall mix of hours played. "Likely owner" is a suggestion for routing, not a finding.</p>
{ptable}{off_note}{model_block(o.get('model'))}</section>
{sub_block(o.get('sub_reasons'))}

<section id="when"><h2>2 · When they give up</h2>
<p class="q">How negative are reviews at each stage of play, and how many of those critics never came back?</p>
<div class="grid2"><div class="card"><h3>Negative share of reviews, by hours played at review</h3>{c1}</div><div class="card"><h3>Negative reviewers who walked away, by hours played at review</h3>{c2}</div></div>
<details><summary>Table view</summary>{pt_table}</details>
<h3 style="margin-top:18px">What critics complain about at each stage</h3>
<p class="note">Share of that stage's labeled negative reviews, six largest named complaints. Darker = larger share.</p>{htable}</section>

<section id="markets"><h2>3 · Markets (review language)</h2>
<p class="q">Does the picture change by language community? {mk}</p>
{ltable}
<h3 style="margin-top:18px">What each language community complains about</h3>
<p class="note">Share of that language's labeled negative reviews. Darker = larger share.</p>{lheat_t}
<p class="note">Review language is only a rough stand-in for market: many players write in English wherever they live, and Steam reports no country. Languages with under 300 reviews for this game are grouped.</p></section>

<section id="said"><h2>4 · Said versus did</h2>
<p class="q">How well does "I quit" or "I'll be back when it's fixed" predict what the reviewer did next?</p>{svd_table}</section>

<section id="timeline"><h2>5 · Patches &amp; spikes</h2>
<p class="q">When did negative reviews jump, and what did the studio post around those dates?</p>
<div class="legend"><span><i class="sw-b"></i>all reviews</span><span><i class="sw-o"></i>negative reviews / negative share</span><span><i class="sw-g"></i>month with an official patch or update post</span></div>
<div class="card">{timeline(o['monthly'])}</div>
<h3 style="margin-top:18px">Weeks when negative reviews jumped</h3>
<p class="note">Rule: after the first six weeks, a week with 40+ negative reviews and at least double the median of the previous eight weeks. Sales, free weekends and outside news also move review counts, so a post near a spike is a lead to check, not an explanation.</p>
{spikes}</section>

<section id="voices"><h2>6 · Player voice (paraphrased)</h2>
<p class="q">Short paraphrases that show the kind of complaint in each group. They are not quotes, and no review text is published.</p>
<div class="grid2">{voices or "<p class='note'>No paraphrases available.</p>"}</div></section>

<section id="teams"><h2>7 · Checks by team</h2>
<p class="q">Reviews show where to look. Each lead below can be confirmed or rejected with internal telemetry.</p>{todo}</section>

<section id="limits"><h2>8 · Limits &amp; data</h2>
<ul class="note">
<li>Only people who wrote a review; they are a small and unusual part of the player base.</li>
<li>Playtime after a review is Steam's public figure at the snapshot ({E(o['snapshot'])}). Offline play and other platforms are not counted. Reviews newer than {o['params']['mature_days']} days are left out of walk-away rates.</li>
<li>Editing a review may refresh its "playtime at review" figure. Without edited reviews the walk-away rate of negative reviewers is {pct(b['negative_unedited']['walk_rate'])} (with them: {pct(bn['walk_rate'])}).</li>
<li>Reason labels come from a language model reading up to 1,200 characters per review in its original language. {audit_line(audit, long=True)}</li>
<li>{sens_line(o['sensitivity'])}</li>
<li>Groups that complain about different things also differ in hours played, purchase timing and expectations; the regression in section 1 controls for some of this, not all.</li></ul>
<div class="dl"><a href="../data/{E(o['slug'])}.json">This report's numbers (JSON)</a><a href="{REPO}/tree/main/data/public">All tables (CSV)</a><a href="../method.html">Method &amp; limits</a><a href="{REPO}/blob/main/src/analyze.py">Analysis code</a></div></section>
</div></div></div>"""
    return page(f"{o['name']} — quit signals in Steam reviews", body, ov, depth=1, desc=f"Quit-signal report for {o['name']} from public Steam reviews in all languages.", current=o["slug"])


THUMB = {True: "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
         False: "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"}
def thumb(up):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{THUMB[up]}" fill="none" stroke="{"#5a9cec" if up else "#f08152"}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'

CONTACT = "hosun9k@gmail.com"
OVERVIEW_JS = """<script>
(function(){
var notes=JSON.parse(document.getElementById('pnotes').textContent),pills=[].slice.call(document.querySelectorAll('.pill')),note=document.getElementById('pnote');
function pick(i){pills.forEach(function(p,k){p.setAttribute('aria-pressed',k===i?'true':'false')});
[].forEach.call(document.querySelectorAll('[data-st]'),function(e){var k=+e.getAttribute('data-st');e.classList.toggle('dim',i!==0&&k!==i)});note.textContent=notes[i]}
pills.forEach(function(p,i){p.addEventListener('click',function(){pick(i)})});
var w=document.getElementById('tilt'),st=w&&w.querySelector('.stack');
if(st&&!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)&&matchMedia('(hover: hover)').matches){
w.addEventListener('mousemove',function(e){var r=w.getBoundingClientRect();st.style.transform='rotateX('+((.5-(e.clientY-r.top)/r.height)*10)+'deg) rotateY('+(((e.clientX-r.left)/r.width-.5)*14)+'deg)'});
w.addEventListener('mouseleave',function(){st.style.transform=''})}
var f=document.getElementById('reqform');if(f){f.addEventListener('submit',function(e){e.preventDefault();var d=new FormData(f),v=function(k){return String(d.get(k)||'')};
var body='Name: '+v('name')+'\\nStudio: '+v('studio')+'\\nGame: '+v('game')+'\\nLinkedIn: '+v('linkedin')+'\\nEmail: '+v('email');
document.getElementById('reqfb').hidden=false;
window.location.href='mailto:'+f.getAttribute('data-to')+'?subject='+encodeURIComponent('Player Signals report request: '+v('game'))+'&body='+encodeURIComponent(body)})}
})();
</script>"""


def overview_page_body(ov, games, ar, c1h, lab, fans_line):
    """Overview: one chart of what reviewers did next, then the game cards, then the request form."""
    tot = sum(o["reviews"] for o in ov); nlang = max(o["funnel"]["languages"] for o in games)
    P, N = ar["pooled"]["positive"], ar["pooled"]["negative"]; base = ar["pooled"]["baseline_at_critics_hours"]; rows = ar["pooled"]["by_hours"]
    every = all(r["gap"] is not None and r["gap"] > 0 for g in ar["games"] + [ar["pooled"]] for r in g["by_hours"])
    late = max(((g, r) for g in ar["games"] for r in g["by_hours"][1:] if r["positive"]["walk_rate"] is not None), key=lambda t: t[1]["positive"]["walk_rate"])
    notes = [f"Across all hours, {pct(P['walk_rate'])} of players who recommended a game logged under one more hour after reviewing, against {pct(N['walk_rate'])} of those who did not."
             + (" The gap holds at every stage of play." if every else "") + f" At the critics' hours, recommenders would stop {pct(base)} of the time."]
    for i, r in enumerate(rows):
        t = f"{r['bucket']}: critics stopped {r['negative']['walk_rate'] / r['positive']['walk_rate']:.1f} times as often as recommenders."
        if i == 0: t += " This is inside Steam's refund window, so both groups stop more often here."
        if r["bucket"] == late[1]["bucket"]: t += f" Some recommenders stop here too: in {late[0]['name']} it is {pct(late[1]['positive']['walk_rate'])}, which fits finishing a game more than quitting it."
        notes.append(t)
    H = 3.3
    pills = "".join(f'<button class="pill" type="button" aria-pressed="{"true" if i == 0 else "false"}">{E(l)}</button>' for i, l in enumerate(["All hours"] + [r["bucket"] for r in rows]))
    cols = "".join(f'<div class="col" data-st="{i+1}"><div class="vb"><span style="color:#8fbdf5">{pct(r["positive"]["walk_rate"])}</span><div class="b p" style="height:{r["positive"]["walk_rate"]*100*H:.0f}px"></div></div>'
                   f'<div class="vb"><span style="color:#f6a07a">{pct(r["negative"]["walk_rate"])}</span><div class="b n" style="height:{r["negative"]["walk_rate"]*100*H:.0f}px"></div></div></div>' for i, r in enumerate(rows))
    labs = "".join(f'<div data-st="{i+1}">{E(r["bucket"])}</div>' for i, r in enumerate(rows))
    aria = "Share who logged under one more hour after reviewing, by hours played at review. " + "; ".join(f"{r['bucket']}: recommended {pct(r['positive']['walk_rate'])}, not recommended {pct(r['negative']['walk_rate'])}" for r in rows)
    byslug = {g["slug"]: g for g in ar["games"]}
    cards = "".join(
        f'<a class="gcard lift rise" style="animation-delay:{0.15 + i * 0.09:.2f}s" href="games/{E(o["slug"])}.html"><div class="gh"><div><div class="gn">{E(o["name"])}</div><div class="gs">{E(o["genre"])}</div></div><div class="gr">{num(o["reviews"])} reviews</div></div>'
        f'<div><div class="grow">{thumb(True)}<b style="color:#5a9cec">{pct(byslug[o["slug"]]["positive"]["walk_rate"])}</b><div class="tr"><i style="width:{byslug[o["slug"]]["positive"]["walk_rate"]*200:.0f}%;background:#5a9cec"></i></div></div>'
        f'<div class="grow">{thumb(False)}<b style="color:#f08152">{pct(byslug[o["slug"]]["negative"]["walk_rate"])}</b><div class="tr"><i style="width:{byslug[o["slug"]]["negative"]["walk_rate"]*200:.0f}%;background:#f08152"></i></div></div></div>'
        f'<div class="gfacts"><div><small>Negative reviews</small><b>{pct(o["negative_share"])}</b></div><div><small>Top complaint</small><b>{E(o["top_reason"] or "–")}</b></div></div><div class="gopen">Open report →</div></a>' for i, o in enumerate(ov))
    mh = next((o for o in ov if o["slug"] == "monster-hunter-wilds"), None); cs = "What an English-only read of Steam reviews misses."
    if mh:
        en = next((l for l in mh["languages"] if l["code"] == "english"), None); zh = next((l for l in mh["languages"] if l["code"] == "schinese"), None)
        if en and zh: cs = f"{mh['name']} is {pct(en['negative_share'])} negative in English and {pct(zh['negative_share'])} in Simplified Chinese."
    notes_json = json.dumps(notes).replace("<", "\\u003c")
    legend = lambda a, b: f'<div class="tlegend"><span>{thumb(True)}{a}</span><span>{thumb(False)}{b}</span></div>'
    return f"""<div class="hero-bg"><div class="glow g1" aria-hidden="true"></div><div class="glow g2" aria-hidden="true"></div>
<svg class="pulseline" aria-hidden="true" viewBox="0 0 1280 160" preserveAspectRatio="none"><polyline points="0,90 180,90 230,90 262,30 300,140 338,60 372,90 620,90 660,90 690,48 724,120 752,90 1280,90" fill="none" stroke="#5a9cec" stroke-width="2" stroke-linejoin="round"/></svg>
<div class="wrap hero"><div class="htext rise">
<h1 class="big">A review is not the end of the story. This study measures what players did next.</h1>
<p class="lede">{num(tot)} public Steam reviews of six games, in {nlang} languages. For each one, Steam shows hours played at the review and hours played since.</p>
<a class="btn" href="#games">Find a game like yours</a></div>
<div class="tiltwrap" id="tilt"><div class="stack"><div class="layer l2" aria-hidden="true"></div><div class="layer l1" aria-hidden="true"></div>
<div class="panel"><div class="kick">Stopped within an hour of reviewing</div>
<div class="pills" role="group" aria-label="Hours played at review">{pills}</div>
{legend("Recommended", "Not recommended")}
<div class="chartg" role="img" aria-label="{E(aria)}">{cols}</div>
<div class="chartlab" aria-hidden="true">{labs}</div>
<div class="pnote" id="pnote" aria-live="polite">{E(notes[0])}</div>
<script type="application/json" id="pnotes">{notes_json}</script>
</div></div></div></div></div>
<div class="wrap" style="padding-top:20px">
<section id="games" style="margin-top:0"><div class="shead"><h2>Find a game like yours</h2>{legend("Recommended, stopped", "Not recommended, stopped")}</div>
<div class="gcards">{cards}</div></section>
<section id="request"><div class="req"><div class="rt"><h2>Is your game missing?</h2><p>The same report can be built for any paid Steam game with public reviews. Tell me which game and I will reply by email.</p></div>
<form id="reqform" data-to="{CONTACT}">
<div class="f"><label for="rq-name">Name</label><input id="rq-name" name="name" type="text" autocomplete="name" required></div>
<div class="f"><label for="rq-studio">Studio</label><input id="rq-studio" name="studio" type="text" autocomplete="organization" required></div>
<div class="f"><label for="rq-game">Game</label><input id="rq-game" name="game" type="text" required></div>
<div class="f"><label for="rq-linkedin">LinkedIn profile</label><input id="rq-linkedin" name="linkedin" type="url" placeholder="https://linkedin.com/in/…"></div>
<div class="f"><label for="rq-email">Email address</label><input id="rq-email" name="email" type="email" autocomplete="email" required></div>
<div class="f"><button class="btn" type="submit">Request a report</button></div>
<div class="fb" id="reqfb" role="status" hidden>If your email app did not open, write to {CONTACT}.</div>
</form></div></section>
<section class="more">
<a class="mcard lift" href="quit.html"><b>Why players quit</b><span>{E(c1h)}. Which complaints go with stopping, from {num(lab)} labeled negative reviews.</span></a>
<a class="mcard lift" href="fans.html"><b>When fans review</b><span>{E(fans_line)}</span></a>
<a class="mcard lift" href="data.html"><b>The numbers</b><span>Every table behind this page: by game, by hours played and by review language.</span></a>
<a class="mcard lift" href="case-study.html"><b>Case study: the score that hid a market</b><span>{E(cs)}</span></a>
<a class="mcard lift" href="method.html"><b>Method and limits</b><span>Claude Haiku 5.5 labels, Claude Fable 5.2 audits, code checks every number.</span></a>
</section>
</div>
{OVERVIEW_JS}"""


def index_page(ov, games, audit, cost, models, ar, fans_line):
    tot = sum(o["reviews"] for o in ov); neg = sum(o["negative"] for o in ov); lab = sum(o["labeled"] for o in ov); eng = sum(o["english"] for o in ov)
    nl = len({l["code"] for o in ov for l in o["languages"] if l["code"] != "_small"})
    wmin = min(ov, key=lambda o: o["neg_walk_rate"]); wmax = max(ov, key=lambda o: o["neg_walk_rate"])
    flags = {c: [o["reason_flags"].get(c, "n/a") for o in ov] for c in REASONS if c not in ("OTHER", "OFFGAME")}
    order = sorted(flags, key=lambda c: flags[c].count("lower") - flags[c].count("higher"))
    N = len(ov)
    flagrows = "".join(f"<tr><td>{E(REASONS[c])}</td><td class='l'><span class='chip own'>{E(OWNER[c])}</span></td><td>{flags[c].count('higher')} of {N}</td><td>{flags[c].count('lower')} of {N}</td><td>{N-flags[c].count('higher')-flags[c].count('lower')} of {N}</td></tr>" for c in order)
    stay = [c for c in order if flags[c].count("lower") >= 4]; leave = [c for c in order if flags[c].count("higher") >= 4]
    rng = lambda k, inv=False: (lambda v: f"{pct(min(v))}–{pct(max(v))}")([(1 - o[k]) if inv else o[k] for o in ov if o[k] is not None])
    c1h = ("Players who report crashes are the ones who stay" if "STAB" in stay else "Complaints differ in how often their authors leave")
    c1p = ""
    if stay: c1p += "Reviewers left clearly less often than other critics after complaints about " + ", ".join(f"{E(REASONS[c].lower())} ({flags[c].count('lower')} of {N} games)" for c in reversed(stay)) + ". "
    if leave: c1p += "They left clearly more often after complaints about " + ", ".join(f"{E(REASONS[c].lower())} ({flags[c].count('higher')} of {N} games)" for c in leave) + ". "
    pm = (models or {}).get("pooled") or {}
    if pm.get("ok") and pm.get("reference") == "STAB" and all(r["lo"] > 1 for r in pm["rows"]):
        ors = [r["odds_ratio"] for r in pm["rows"]]
        c1p += f"After controls, every other complaint type has higher odds of walking away than crash complaints ({min(ors):.2f}×–{max(ors):.2f}×)."
    c2h = "Under two hours, critics often stop, but that is also the refund window"
    c2p = f"{rng('under2h_negative_share')} of reviews written with under 2 hours played are negative, and {rng('under2h_neg_walk_rate')} of those reviewers did not log another hour. Steam refunds are available up to 2 hours of play, so part of this is players stopping to stay eligible for a refund, not the complaint itself."
    c3h = "Most critics are still reachable"
    c3p = f"{rng('neg_walk_rate', True)} of negative reviewers kept playing for at least another hour. Of those who wrote they would wait for fixes, {rng('said_waiting_kept_10h_rate')} played 10+ more hours. Of those who wrote they had quit, {rng('said_stopped_walk_rate', True)} still logged another hour or more."
    calls = "".join(f'<div class="call"><div class="t">{t}</div><h3>{h}</h3><p>{p}</p></div>' for t, h, p in [("Prioritize", c1h, c1p), ("Protect", c2h, c2p), ("Win back", c3h, c3p)])

    rows = "".join(f"<tr><td><a href='games/{E(o['slug'])}.html'>{E(o['name'])}</a><div class='small'>{E(o['genre'])}</div></td><td>{num(o['reviews'])}</td><td>{pct(o['english']/o['reviews'])}</td>{barcell(o['negative_share'])}"
                   f"{barcell(o['neg_walk_rate'], 'o')}<td>{pct(o['pos_walk_rate'])}</td><td>{pct(o['kept_10h_rate'])}</td><td>{pct(o['neg_refunded_rate'])}</td><td>{o['neg_median_hours_at_review']}</td><td class='l'>{E(o['top_reason'] or '–')} ({pct(o['top_reason_share'])})</td></tr>" for o in ov)
    codes = [c for c in REASONS if c != "OTHER"]
    head = "".join(f"<th>{E(SHORT[c])}</th>" for c in codes)
    heat1 = "".join(f"<tr><td>{E(o['name'])}</td>" + "".join(heat(o["reason_shares"].get(c)) for c in codes) + "</tr>" for o in ov)
    heat2 = "".join(f"<tr><td>{E(o['name'])} <span class='small'>all: {pct(o['neg_walk_rate'])}</span></td>" + "".join("<td>–</td>" if o["reason_walk"].get(c) is None else f"<td>{VERDICT[o['reason_flags'][c]][0] if o['reason_flags'][c] in ('higher','lower') else ''} {pct(o['reason_walk'][c])}</td>" for c in codes) + "</tr>" for o in ov)
    # markets: languages with 1,000+ reviews in at least 3 games
    lang_tot = {}
    for o in ov:
        for l in o["languages"]:
            if l["code"] != "_small": lang_tot.setdefault(l["code"], dict(name=l["language"], n=0, games=0)); lang_tot[l["code"]]["n"] += l["reviews"]; lang_tot[l["code"]]["games"] += 1
    top_l = sorted(lang_tot, key=lambda c: -lang_tot[c]["n"])[:10]
    def lcell(o, c, key):
        l = next((x for x in o["languages"] if x["code"] == c), None)
        return heat(l[key], f"{l['reviews']:,} reviews") if l and l[key] is not None else "<td>–</td>"
    mhead = "".join(f"<th>{E(o['name'])}</th>" for o in ov)
    m1 = "".join(f"<tr><td>{E(lang_tot[c]['name'])} <span class='small'>{lang_tot[c]['n']:,}</span></td>" + "".join(lcell(o, c, "negative_share") for o in ov) + "</tr>" for c in top_l)
    m2 = "".join(f"<tr><td>{E(lang_tot[c]['name'])}</td>" + "".join(lcell(o, c, "neg_walk_rate") for o in ov) + "</tr>" for c in top_l)
    cards = "".join(f"<a class='game' href='games/{E(o['slug'])}.html'><b>{E(o['name'])}</b><div class='small'>{E(o['genre'])} · released {E(o['release'])}</div>"
                    f"<div class='row'><div><strong>{num(o['reviews'])}</strong>reviews</div><div><strong>{pct(o['negative_share'])}</strong>negative</div><div><strong>{pct(o['neg_walk_rate'])}</strong>of critics walked away</div></div>"
                    f"<div class='note' style='margin-top:10px'>Top complaint: {E((o['top_reason'] or '').lower())} ({pct(o['top_reason_share'])})</div></a>" for o in ov)
    P, N = ar["pooled"]["positive"], ar["pooled"]["negative"]; base = ar["pooled"]["baseline_at_critics_hours"]
    every = all(r["gap"] is not None and r["gap"] > 0 for g in ar["games"] + [ar["pooled"]] for r in g["by_hours"])
    pts = lambda v: "–" if v is None else f"{v * 100:.0f} pts"
    a1h = f"{pct(1 - P['walk_rate'])} of recommenders keep playing"
    a1p = f"{pct(P['kept_10h_rate'])} played 10 or more further hours, and {pct(P['active_now_rate'])} were active in the two weeks before the snapshot. Median play after a positive review: {P['median_hours_after']} hours."
    a2h = f"Critics stop about {N['walk_rate'] / P['walk_rate']:.0f} times as often" + (", at every stage of play" if every else "")
    a2p = (f"{pct(N['walk_rate'])} of critics logged under 1 more hour, against {pct(P['walk_rate'])} of recommenders. Hours played does not explain the gap: recommenders with the critics' mix of hours would stop {pct(base)} of the time. "
           f"Still, {pct(1 - N['walk_rate'])} of critics played on and {pct(N['kept_10h_rate'])} played 10+ more hours.")
    late = max(((g, r) for g in ar["games"] for r in g["by_hours"][1:] if r["positive"]["walk_rate"] is not None), key=lambda t: t[1]["positive"]["walk_rate"])
    late_pool = next(r for r in ar["pooled"]["by_hours"] if r["bucket"] == late[1]["bucket"])
    a3h = f"{num(P['walked_away'])} reviewers recommended a game and stopped there"
    a3p = (f"A small group that a review score never shows. It is largest in {E(late[0]['name'])}: {pct(late[1]['positive']['walk_rate'])} of recommenders who reviewed at {E(late[1]['bucket'].lower())} logged under 1 more hour, "
           f"against {pct(late_pool['positive']['walk_rate'])} at that stage across all six games. That pattern fits finishing a game more than quitting it.")
    acalls = "".join(f'<div class="call"><div class="t">{t}</div><h3>{h}</h3><p>{p}</p></div>' for t, h, p in [("Recommended", a1h, a1p), ("Not recommended", a2h, a2p), ("Recommended, then gone", a3h, a3p)])
    chart = pair_columns([dict(label=r["bucket"], a=r["positive"]["walk_rate"], b=r["negative"]["walk_rate"], tip=f"{r['bucket']}: {r['positive']['n']:,} recommended, {r['negative']['n']:,} not recommended") for r in ar["pooled"]["by_hours"]])
    arow = lambda g, name: (f"<tr><td>{name}</td>{barcell(g['positive']['walk_rate'])}{barcell(g['negative']['walk_rate'], 'o')}<td>{pct(g['baseline_at_critics_hours'])}</td><td><b>{pts(g['excess_over_baseline'])}</b></td>"
                            f"<td>{pct(g['positive']['kept_10h_rate'])}</td><td>{pct(g['negative']['kept_10h_rate'])}</td></tr>")
    arows = "".join(arow(g, f"<a href='games/{E(g['slug'])}.html'>{E(g['name'])}</a><div class='small'>{E(g['genre'])}</div>") for g in ar["games"]) + arow(ar["pooled"], "<b>All six games</b>")
    bhead = "".join(f"<th>{E(r['bucket'])}</th>" for r in ar["pooled"]["by_hours"])
    gone = "".join(f"<tr><td>{E(g['name'])} <span class='small'>{num(g['positive']['walked_away'])} reviewers</span></td>" + "".join(heat(r["positive"]["walk_rate"], f"{r['positive']['n']:,} recommended reviews") for r in g["by_hours"]) + "</tr>" for g in ar["games"])
    body = f"""<div class="wrap">
<h1>The numbers</h1>
<p class="lede">Every table behind the overview: what reviewers did after reviewing, by verdict, game, hours played and review language.</p>
<div class="kpis">
<div class="kpi"><div class="l">Reviews analysed</div><b>{num(tot)}</b><div class="s">full history of 6 games, {nl} languages with 300+ reviews in a game</div></div>
<div class="kpi"><div class="l">Recommenders who stopped</div><b>{pct(P['walk_rate'])}</b><div class="s">logged under 1 more hour after a positive review</div></div>
<div class="kpi"><div class="l">Critics who stopped</div><b>{pct(N['walk_rate'])}</b><div class="s">after a negative review ({pct(wmin['neg_walk_rate'])}–{pct(wmax['neg_walk_rate'])} by game)</div></div>
<div class="kpi"><div class="l">Played 10+ more hours</div><b>{pct(P['kept_10h_rate'])} / {pct(N['kept_10h_rate'])}</b><div class="s">recommenders / critics</div></div></div>
<div class="calls">{acalls}</div>
<div class="caveat"><b>How far this goes.</b> Reviews represent only the players who wrote them. All figures are shares of reviewers, and every pattern is an association, not a cause. Stopping is not the same as a lost customer: these are paid games, and a reviewer who stops after 80 hours may simply have finished, while one who stops after 2 never got started. Read each walk-away rate next to hours played at review. See <a href="method.html">Method &amp; limits</a>.</div>

<section id="after"><h2>After the review, by hours played</h2>
<p class="q">How often did a reviewer log under one more hour after reviewing? All six games together, reviews at least {ar['params']['mature_days']} days old.</p>
<div class="card"><div class="legend"><span><i class="sw-b"></i>Recommended</span><span><i class="sw-o"></i>Not recommended</span></div>{chart}</div>
<div class="scroll" style="margin-top:14px"><table><thead><tr><th>Game</th><th class="l">Recommenders who stopped</th><th class="l">Critics who stopped</th><th>Recommenders at the critics' hours</th><th>Gap</th><th>Recommenders who played 10+ more hours</th><th>Critics who played 10+ more hours</th></tr></thead><tbody>{arows}</tbody></table></div>
<p class="note">"Recommenders at the critics' hours" re-weights the recommenders' rates to the critics' mix of hours played, so the gap is not a side effect of critics reviewing earlier or later. It is still an association: a review is often written at the moment a player stops, and that is more common for a negative one. Table by game and stage: <a href="data/after_review.json">data/after_review.json</a>.</p></section>

<section id="gone"><h2>Recommended, then gone</h2>
<p class="q">Share of recommenders who logged under one more hour, by hours played at review. Darker = larger share.</p>
<div class="scroll"><table><thead><tr><th>Game</th>{bhead}</tr></thead><tbody>{gone}</tbody></table></div>
<p class="note">Under 2 hours is inside Steam's refund window, so read that column with care. Later columns show where players who liked a game tend to put it down.</p></section>

<section><h2>Why players quit</h2>
<div class="card"><p style="margin:0">Critics who stop are not spread evenly across complaints. {E(c1h)}. {c1p} <a href="quit.html">See which complaints go with stopping</a>.</p></div></section>

<section><h2>How it works</h2>
<div class="card"><p style="margin:0">Steam publishes, next to every review, how long the reviewer had played when they wrote it and how long they have played in total. The gap shows what the reviewer did <i>after</i> reviewing. For negative reviews, a language model also sorts each one into one main complaint, in its original language, which separates complaints that travel with quitting from complaints players voice while they stay.</p></div></section>

<section><h2>Side by side</h2>
<div class="scroll"><table><thead><tr><th>Game</th><th>Reviews</th><th>English</th><th class="l">Negative</th><th class="l">Critics who walked away</th><th>Positive reviewers who walked away</th><th>Critics who played 10+ more hours</th><th>Negative reviews refunded</th><th>Median hours at negative review</th><th class="l">Top named complaint</th></tr></thead><tbody>{rows}</tbody></table></div></section>

<section id="markets"><h2>Markets (review language)</h2>
<p class="q">The same game can look very different by language community. Ten largest languages across the six games; a cell needs 300+ reviews.</p>
<h3>Negative share of reviews</h3><div class="scroll"><table><thead><tr><th>Review language</th>{mhead}</tr></thead><tbody>{m1}</tbody></table></div>
<h3 style="margin-top:22px">Negative reviewers who walked away</h3><div class="scroll"><table><thead><tr><th>Review language</th>{mhead}</tr></thead><tbody>{m2}</tbody></table></div>
<p class="note">Review language is a rough stand-in for market: many players write in English wherever they live, and Steam reports no country.</p></section>

<section><h2>How a studio could use this</h2>
<div class="grid2">
<div class="team"><h3><span class="chip own">Production</span>Rank fixes by who leaves</h3><div class="note">Each report's priority map shows, per complaint, how often its authors stopped playing compared with other critics.</div></div>
<div class="team"><h3><span class="chip own">Design &amp; UX</span>Find the hours where players are lost</h3><div class="note">Each report shows how negative reviews and walk-aways spread over hours played, and what critics name at each stage.</div></div>
<div class="team"><h3><span class="chip own">Publishing</span>See each market separately</h3><div class="note">Negative share, walk-away rate and top complaint are broken out by review language.</div></div>
<div class="team"><h3><span class="chip own">Live ops &amp; community</span>Size the players who are waiting</h3><div class="note">Each report counts reviewers who said they would return after fixes and how many did, and lists spike weeks next to official posts.</div></div>
</div>
<p class="note">Why these six: premium games with a large body of negative reviews ({pct(min(o['negative_share'] for o in ov))}–{pct(max(o['negative_share'] for o in ov))} negative) and a review history small enough to fetch in full without straining Steam, across different genres. {audit_line(audit)[0].upper() + audit_line(audit)[1:]}. Total paid model spend for the project: ${cost['total_usd']:.2f}. The <a href="{REPO}">code</a> can be re-run on any Steam app ID.</p></section>
</div>"""
    quit_body = f"""<div class="wrap">
<h1>Why players quit</h1>
<p class="lede">Among reviewers who did not recommend a game, which complaints go with stopping, how early they give up, and how often "I quit" turns out to be true. Built from {num(lab)} negative reviews labeled by reason.</p>
<div class="calls">{calls}</div>
<div class="caveat"><b>How far this goes.</b> Reviews represent only the players who wrote them. All figures are shares of reviewers, and every pattern is an association, not a cause. Stopping is not the same as a lost customer: these are paid games, and a reviewer who stops after 80 hours may simply have finished, while one who stops after 2 never got started. Read each walk-away rate next to hours played at review. See <a href="method.html">Method &amp; limits</a>.</div>

<section><h2>Which complaints go with leaving</h2>
<h3>Across games</h3>
<div class="scroll"><table><thead><tr><th>Main complaint</th><th class="l">Likely owner</th><th>Games where these reviewers left clearly more often</th><th>Clearly less often</th><th>No clear difference or too few reviews</th></tr></thead><tbody>{flagrows}</tbody></table></div>
<p class="note">"Clearly" means the complaint group's whole 95% interval is above or below that game's rate for all negative reviewers.</p>
{model_block(models['pooled'], "all six games'") if models else ''}
<p class="note">The pooled model also holds the game constant. Full output: <a href="data/models.json">data/models.json</a>.</p>
<h3 style="margin-top:22px">What negative reviews are about</h3>
<p class="note">Share of each game's labeled negative reviews. The rest of each row is "no clear reason". "Off-game" counts reviews mainly about politics, social topics, or specific people or companies; it is reported as a share only.</p>
<div class="scroll"><table><thead><tr><th>Game</th>{head}</tr></thead><tbody>{heat1}</tbody></table></div>
<h3 style="margin-top:22px">Walk-away rate by main complaint</h3>
<p class="note">▲ / ▼ mark groups clearly above / below the game's own rate. "–" = fewer than 30 reviews.</p>
<div class="scroll"><table><thead><tr><th>Game</th>{head}</tr></thead><tbody>{heat2}</tbody></table></div></section>
</div>"""
    return (page("Player Signals — what players do after they review", overview_page_body(ov, games, ar, c1h, lab, fans_line), ov, desc="What reviewers of Steam games did after reviewing: who kept playing, who stopped, and which complaints go with stopping. Built from public Steam reviews in all languages."),
            page("Why players quit — Player Signals", quit_body, ov, desc="Which complaints go with actually leaving? Complaint analysis of negative Steam reviews in all languages."),
            page("The numbers — Player Signals", body, ov, desc="Tables behind Player Signals: behaviour after the review by game, hours played and review language."))


RAMP = ["#2f6fd0", "#4f8fe0", "#77aaec", "#a3c6f4", "#d3e5fb"]   # one hue, ordered: more total hours = lighter


def line_chart(series, xticks, xmax, ylab, xlab, band=None, marks=None, width=760, height=320, label_ends=True):
    """series: [{name,color,pts:[(x,y)]}] on a shared numeric x (0..xmax) and one y axis. band: (x0,x1,label). marks: per-series x of a marker."""
    L, R, T, B = 48, 96 if label_ends else 20, 22, 46; pw, ph = width - L - R, height - T - B
    ymax = max(y for sr in series for _, y in sr["pts"]) * 1.12 or 1
    X = lambda v: L + v / xmax * pw; Y = lambda v: T + (1 - v / ymax) * ph
    o = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{E(ylab)} by {E(xlab)}">']
    if band: o.append(f'<rect x="{X(band[0]):.1f}" y="{T}" width="{X(band[1]) - X(band[0]):.1f}" height="{ph}" fill="var(--text)" opacity=".07"/><text class="t" x="{(X(band[0]) + X(band[1])) / 2:.1f}" y="{T + 13}" text-anchor="middle">{E(band[2])}</text>')
    step = 0.05 if ymax > 0.16 else 0.02 if ymax > 0.06 else 0.01; v = 0
    while v <= ymax:
        o.append(f'<line x1="{L}" x2="{L + pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--grid)"/><text class="t" x="{L - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{pct(v)}</text>'); v += step
    for xv, lab_ in xticks: o.append(f'<text class="t" x="{X(xv):.1f}" y="{T + ph + 16}" text-anchor="middle">{E(lab_)}</text>')
    o.append(f'<text class="t" x="{L + pw / 2:.1f}" y="{height - 6}" text-anchor="middle">{E(xlab)}</text>')
    ends = []
    for k, sr in enumerate(series):
        d = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in sr["pts"])
        o.append(f'<polyline points="{d}" fill="none" stroke="{sr["color"]}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        for x, y in sr["pts"]: o.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="7" fill="transparent"><title>{E(sr["name"])}: {pct(y, 1)}</title></circle>')
        if marks and marks[k] is not None:
            mx = marks[k]; pts = sr["pts"]; my = next((y0 + (y1 - y0) * (mx - x0) / (x1 - x0) for (x0, y0), (x1, y1) in zip(pts, pts[1:]) if x0 <= mx <= x1), pts[-1][1])
            o.append(f'<circle cx="{X(mx):.1f}" cy="{Y(my):.1f}" r="5" fill="{sr["color"]}" stroke="var(--surface)" stroke-width="2"><title>{E(sr["name"])}: half reviewed by this point</title></circle>')
        ends.append([Y(sr["pts"][-1][1]), sr])
    if label_ends:
        ends.sort(key=lambda e: e[0])
        for i in range(1, len(ends)): ends[i][0] = max(ends[i][0], ends[i - 1][0] + 14)
        for y, sr in ends: o.append(f'<line x1="{L + pw + 4}" x2="{L + pw + 14}" y1="{y:.1f}" y2="{y:.1f}" stroke="{sr["color"]}" stroke-width="2"/><text x="{L + pw + 18}" y="{y + 4:.1f}">{E(sr["name"])}</text>')
    return "".join(o) + "</svg>"


def fans_headline(fans):
    r = fans["pooled"]["recommended"]; return f"Half of all recommendations are written between {r['p25']:.0f} and {r['p75']:.0f} hours of play."


def fans_page(fans, ov):
    """When players who recommend a game write their review, and where that sits in their whole playtime."""
    P = fans["pooled"]; R = P["recommended"]; edges = fans["params"]["hour_edges"]; G = [g for g in P["by_total_hours"] if "curve" in g]
    nb = len(edges)
    def xof(h):   # position of an hours value on the band axis (bands are uneven, so interpolate inside the band)
        for i in range(nb):
            hi = edges[i + 1] if i + 1 < nb else edges[i] * 2
            if h < hi or i == nb - 1: return i + min((h - edges[i]) / (hi - edges[i]), 1)
    hticks = [(i, f"{edges[i]:g} h") for i in range(nb) if edges[i] in (1, 4, 16, 64, 256, 1024)]
    c1 = line_chart([dict(name="Recommended", color="var(--blue)", pts=[(i + .5, y) for i, y in enumerate(R["curve"])])], hticks, nb, "Share of recommended reviews", "Hours played when the review was written (each mark is 4 times the one before)",
                    band=(xof(R["p25"]), xof(R["p75"]), f"middle half: {R['p25']:.0f}–{R['p75']:.0f} h"), marks=[xof(R["median"])], label_ends=False)
    c2 = line_chart([dict(name=g["group"], color=RAMP[i], pts=[(k + .5, y) for k, y in enumerate(g["curve"])]) for i, g in enumerate(G)],
                    [(k, f"{k * 10}%") for k in range(0, 11, 2)], 10, "Share of that group's recommended reviews", "Point in the player's whole playtime when the review was written (0% = start, 100% = never played again)",
                    marks=[g["position_median"] * 10 for g in G])
    lo, hi = G[0], G[-1]
    calls = [("When", f"Half of all recommendations come between {R['p25']:.0f} and {R['p75']:.0f} hours",
              f"The median recommended review is written at {R['median']:.0f} hours of play; one in ten comes before {R['p10']:.0f} hours and one in ten after {R['p90']:.0f}. Critics review at a median of {P['not_recommended']['median']:.0f} hours."),
             ("Where in their playtime", "The more someone ends up playing, the earlier in their time they recommend",
              f"Players who total {lo['group'].lower()} wrote their review {pct(lo['position_median'])} of the way through their playtime. Players who total {hi['group'].lower()} wrote theirs {pct(hi['position_median'])} of the way through, with most of their play still ahead."),
             ("Review and leave", f"{pct(lo['reviewed_in_last_tenth'])} of the lightest players recommend the game as they stop",
              f"They wrote the review in the last tenth of their playtime. Among players who total {hi['group'].lower()} it is {pct(hi['reviewed_in_last_tenth'])}.")]
    callh = "".join(f'<div class="call"><div class="t">{t}</div><h3>{h}</h3><p>{p_}</p></div>' for t, h, p_ in calls)
    grows = "".join(f"<tr><td><a href='games/{E(g['slug'])}.html'>{E(g['name'])}</a><div class='small'>{E(g['genre'])}</div></td><td>{num(g['recommended']['n'])}</td><td>{g['recommended']['p25']}</td><td><b>{g['recommended']['median']}</b></td><td>{g['recommended']['p75']}</td><td>{g['not_recommended']['median']}</td></tr>" for g in fans["games"])
    grows += f"<tr><td><b>All six games</b></td><td>{num(R['n'])}</td><td>{R['p25']}</td><td><b>{R['median']}</b></td><td>{R['p75']}</td><td>{P['not_recommended']['median']}</td></tr>"
    trows = "".join(f"<tr><td>{E(g['group'])}</td><td>{num(g['n'])}</td><td>{pct(g['share'])}</td><td>{g['median_hours_at_review']}</td><td>{g['median_total_hours']}</td>{barcell(g['position_median'])}<td>{pct(g['position_p25'])}–{pct(g['position_p75'])}</td><td>{pct(g['reviewed_in_last_tenth'])}</td></tr>" for g in G)
    names = fans["params"]["groups"]
    prow = lambda g, nm: f"<tr><td>{nm}</td>" + "".join(heat(x.get("position_median"), f"{x['n']:,} recommended reviews") for x in g["by_total_hours"]) + "</tr>"
    prows = "".join(prow(g, E(g["name"])) for g in fans["games"]) + prow(P, "<b>All six games</b>")
    legend = "".join(f'<span><i style="background:{RAMP[i]}"></i>{E(g["group"])}</span>' for i, g in enumerate(G))
    body = f"""<div class="wrap">
<h1>When fans review</h1>
<p class="lede">For players who recommended a game: how many hours they had played when they wrote the review, and where that moment sits in all the time they have spent with the game. {num(R['n'])} recommended reviews of six games.</p>
<div class="calls">{callh}</div>
<div class="caveat"><b>How far this goes.</b> A review shows when a player wrote, not when they made up their mind. Total playtime is as of the snapshot, so players who are still playing will end up with their review earlier in their playtime than shown here. Only reviews at least {fans['params']['mature_days']} days old are counted. Reviews represent only the players who wrote them.</div>

<section id="when"><h2>Hours played when fans write the review</h2>
<p class="q">Share of recommended reviews written in each band of hours played, all six games. The shaded area holds the middle half of reviews; the dot marks the median.</p>
<div class="card">{c1}</div>
<div class="scroll" style="margin-top:14px"><table><thead><tr><th>Game</th><th>Recommended reviews</th><th>A quarter written by (hours)</th><th>Median (hours)</th><th>Three quarters written by (hours)</th><th>Not recommended, median (hours)</th></tr></thead><tbody>{grows}</tbody></table></div></section>

<section id="where"><h2>Where the review sits in a player's whole playtime</h2>
<p class="q">Players grouped by the total hours they have played. Each line shows at what point in that playtime the group wrote their review. The dot on each line marks the point by which half of the group had reviewed.</p>
<div class="card"><div class="legend">{legend}</div>{c2}</div>
<div class="scroll" style="margin-top:14px"><table><thead><tr><th>Total hours played</th><th>Recommended reviews</th><th>Share</th><th>Median hours at review</th><th>Median total hours</th><th class="l">Median point in playtime</th><th>Middle half</th><th>Reviewed in the last tenth</th></tr></thead><tbody>{trows}</tbody></table></div>
<h3 style="margin-top:22px">Median point in playtime, by game</h3>
<p class="note">How far through their playtime the median player in each group was when they recommended the game. Darker = later.</p>
<div class="scroll"><table><thead><tr><th>Game</th>{"".join(f"<th>{E(n)}</th>" for n in names)}</tr></thead><tbody>{prows}</tbody></table></div>
<p class="note">Numbers for every game and group: <a href="data/fans.json">data/fans.json</a>.</p></section>
</div>"""
    return page("When fans review — Player Signals", body, ov, desc="When players who recommend a Steam game write their review, in hours played and as a point in their whole playtime.")


def check_loop(games, audit):
    """Lanes diagram: who does each step. Every model step is followed by a check in a different lane. Numbers come from the JSON."""
    enough = sum(o["funnel"]["negative_enough_text"] for o in games); lab = sum(o["funnel"]["labeled"] for o in games)
    X = [140, 246, 352, 458, 564, 670, 776]; BW, BH = 98, 48; LY = {"m": 36, "c": 126, "k": 216}
    steps = [("c", "", "Fetch &amp; filter", f"{num(enough)} reviews"), ("m", "m", "Label", f"{num(lab)} labeled"), ("c", "", "Draw sample", f"{audit['n']}, fixed seeds"),
             ("k", "k", "Audit labels", f"{pct(audit['main_agree'])} correct"), ("c", "", "Analyze", "rates, regression"), ("m", "m", "Paraphrase", "short examples"), ("c", "k", "Screen &amp; verify", "code checks")]
    hops = ["reviews", "all labels", f"{audit['n']} sampled", "verdicts, published", "numbers", "drafts"]
    s = ['<svg viewBox="0 0 900 300" style="min-width:680px" role="img" aria-label="Three lanes: Claude Haiku 5.5, code and Claude Fable 5.2. Each step a model does is followed by a check in a different lane.">',
         '<defs><marker id="lp" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="context-stroke"/></marker></defs>']
    for y, a, b in [(20, "Claude Haiku 5.5", "small model"), (110, "Code", "no model"), (200, "Claude Fable 5.2", "larger model")]:
        s.append(f'<rect class="lanebg" x="10" y="{y}" width="880" height="80" rx="8"/><text class="v" x="22" y="{y + 37}">{a}</text><text class="t" x="22" y="{y + 53}">{b}</text>')
    for i, (lane, cls, t, sub) in enumerate(steps):
        x, y = X[i], LY[lane]
        s.append(f'<rect class="nd {cls}" x="{x}" y="{y}" width="{BW}" height="{BH}" rx="8"/><text class="v" x="{x + BW / 2:.0f}" y="{y + 20}" text-anchor="middle">{t}</text><text class="t" x="{x + BW / 2:.0f}" y="{y + 36}" text-anchor="middle">{sub}</text>')
    for i, lab_ in enumerate(hops):
        (l0, _, _, _), (l1, _, _, _) = steps[i], steps[i + 1]; y0, y1 = LY[l0], LY[l1]; up = y1 < y0
        x0, x1 = X[i] + BW * .75, X[i + 1] + BW * .25
        ya, yb = (y0 - 2, y1 + BH + 3) if up else (y0 + BH + 2, y1 - 3)
        mid = (ya + yb) / 2 + 4
        s.append(f'<line class="fl{" k" if l0 == "k" else ""}" x1="{x0:.0f}" y1="{ya}" x2="{x1:.0f}" y2="{yb}" marker-end="url(#lp)"/>'
                 + (f'<text class="t" x="{(x0 if up else x1 - 34) - 4:.0f}" y="{mid:.0f}" text-anchor="end">{lab_}</text>' if up != ("k" in (l0, l1)) else f'<text class="t" x="{(x1 if not up else x0 + 34) + 4:.0f}" y="{mid:.0f}">{lab_}</text>'))
    return "".join(s) + "</svg>"


def method_page(ov, games, audit, cost):
    funnel = "".join(f"<tr><td>{E(o['name'])}</td><td>{num(o['funnel']['steam_summary_total'])}</td><td>{num(o['funnel']['api_reported_reviews'])}</td><td>{num(o['funnel']['fetched_unique'])}</td><td>{num(o['funnel']['english'])}</td><td>{num(o['funnel']['other_languages'])}</td><td>{num(o['funnel']['negative'])}</td><td>{num(o['funnel']['negative_enough_text'])}</td><td>{num(o['funnel']['labeled'])}</td></tr>" for o in games)
    aud = ""
    if audit:
        sets = "".join(f"<tr><td>{E(s['name'])}</td><td>{s['n']}</td><td>{s['main_ok']} ({pct(s['main_agree'])})</td><td>{s['quit_ok']} ({pct(s['quit_agree'])})</td></tr>" for s in audit["sets"])
        aud = f"""<div class="scroll" style="padding:10px">{check_loop(games, audit)}</div>
<p class="note" style="margin:8px 0 14px">Blue = work by Claude Haiku 5.5. Orange = a check by something other than the author: Claude Fable 5.2 on the labels, code on the paraphrases and the published numbers.</p>
<p>Samples are drawn by code with fixed seeds: 10 per game in English, 10 per game in other languages, plus 50 across everything. For long reviews in the last two samples the checker read the first 420 characters. Overall, main reason judged correct: <b>{pct(audit['main_agree'])}</b> ({audit['main_ok']} of {audit['n']}); quit-statement tag: <b>{pct(audit['quit_agree'])}</b> ({audit['quit_ok']} of {audit['n']}).</p>
<div class="scroll"><table><thead><tr><th>Sample</th><th>Reviews checked</th><th>Main reason correct</th><th>Quit tag correct</th></tr></thead><tbody>{sets}</tbody></table></div>
<p class="note">Per-item verdicts (without text or IDs) are in <a href="data/label_audit.json">data/label_audit.json</a>. The checker reads the non-English reviews directly but is not a native-speaker panel; treat the non-English figure with extra caution. A 50-review sample with text is kept locally for the author's own spot check and is not published.</p>"""
    crow = "".join(f"<tr><td>{E(r['step'])}</td><td>{num(r['calls'])}</td><td>{num(r['input_tokens'])}</td><td>{num(r['output_tokens'])}</td><td>${r['cost_usd']:.2f}</td></tr>" for r in cost["rows"])
    reasons = "".join(f"<tr><td>{E(n)}</td><td class='l'>{E(d)}</td></tr>" for n, d in [
        ("Performance", "low or unstable frame rate, stutter, long loading, hardware demands"), ("Crashes & bugs", "crashes, game-breaking bugs, lost or corrupted saves, will not start"),
        ("Not enough content", "feels unfinished, missing features, repetitive, nothing left to do"), ("Gameplay & design choices", "mechanics, balance, difficulty, pacing, progression, 'boring'"),
        ("Interface & controls", "UI, controls, readability, missing quality-of-life"), ("Price & monetization", "price or value, DLC, microtransactions, editions"),
        ("Online, accounts & DRM", "servers, matchmaking, forced online, third-party accounts, DRM, anti-cheat, cheaters"), ("Post-launch support", "a patch made things worse, slow fixes, broken promises, communication"),
        ("Story & writing", "writing, characters, quests, world building"), ("Off-game topics", "mainly politics, social topics, or specific people or companies rather than how the game plays; reported as a share only, without names and without taking sides"),
        ("No clear reason", "jokes, one-liners, unclear")])
    gap = lambda o: 1 - o['funnel']['fetched_unique'] / o['funnel']['steam_summary_total']
    body = f"""<div class="wrap" style="max-width:980px">
<div class="kicker">Method &amp; limits</div><h1>How the numbers were made</h1>
<p class="lede">Everything is computed by code in the public repository from public Steam data. This page lists each step, each definition, and what the results cannot tell you.</p>
<section><h2>Data</h2>
<ul><li><b>Source:</b> Steam's documented public review endpoint (<code>IUserReviewsService/GetAppReviews</code>), reviews in all languages, full history, walked one calendar month at a time. Official announcements and patch notes come from Steam's public news endpoint (<code>ISteamNews/GetNewsForApp</code>).</li>
<li><b>Politeness:</b> one request at a time per game with a pause between requests (about one request per second overall), back-off on errors, every raw page cached locally so nothing is fetched twice.</li>
<li><b>Privacy:</b> raw review text and reviewer IDs never leave the local cache. The repository and this site contain only aggregated counts and short English paraphrases written by a model and screened by code (20 words or fewer; no 4-word run shared with the source review).</li>
<li><b>Snapshot:</b> English reviews were fetched on {E(min(o['snapshot_english'] for o in games))} and other languages on {E(max(o['snapshot'] for o in games))} (UTC), up to a day apart. Playtime totals are as of each review's fetch.</li></ul></section>
<section><h2>Row counts at each stage</h2>
<div class="scroll"><table><thead><tr><th>Game</th><th>Steam's lifetime total (summary field)</th><th>Listed by the API (sum of months)</th><th>Fetched, unique</th><th>English</th><th>Other languages</th><th>Negative</th><th>Negative with enough text (code filter)</th><th>Labeled by model</th></tr></thead><tbody>{funnel}</tbody></table></div>
<p class="note">Coverage gap: Steam's lifetime summary count is {pct(1 - sum(o['funnel']['fetched_unique'] for o in games) / sum(o['funnel']['steam_summary_total'] for o in games), 1)} higher than the reviews the month-by-month listing returned ({pct(min(gap(o) for o in games), 1)}–{pct(max(gap(o) for o in games), 1)} by game). The listing itself was fetched almost completely. The reason for the gap is not documented by Steam and is not known here; the missing reviews could differ from the fetched ones.</p>
<p class="note">The cheap filter runs in code first: positive reviews are not sent to the model, nor are negative reviews under 3 words (or under 4 characters in Chinese, Japanese, Korean and Thai, which are written without spaces). Reviews the model failed to return a valid line for stay unlabeled.</p></section>
<section><h2>Definitions</h2>
<details><summary>Show all definitions (walk-away, intervals, adjusted rates, regression, markets, spikes)</summary><ul><li><b>Walked away:</b> the reviewer's public total playtime at the snapshot is less than 1 hour above their playtime when they wrote the review. Computed only for reviews at least 30 days old.</li>
<li><b>Played 10+ more hours:</b> same gap, 10 hours or more.</li><li><b>Played in last 2 weeks:</b> Steam's two-week playtime figure is above zero at the snapshot.</li>
<li><b>Refunded:</b> Steam's own flag on the review.</li>
<li><b>95% interval:</b> Wilson interval for a share. Rates on fewer than 30 reviews are not shown.</li>
<li><b>Adjusted for hours played:</b> the walk-away rate a complaint group would have if its reviewers had the same spread of hours-at-review as all labeled negative reviewers of that game (direct standardization over five playtime bands). Not shown when a band is too thin.</li>
<li><b>Leave more often / stay more often / about average:</b> a complaint group is called higher (or lower) only when its whole 95% interval sits above (or below) the game's overall negative-reviewer rate.</li>
<li><b>Market:</b> the language the review is written in, as tagged by Steam. A language gets its own row in a game's report at 300+ reviews.</li>
<li><b>Likely owner:</b> a routing suggestion that maps each complaint type to the kind of team that usually handles it. It is not derived from data.</li>
<li><b>Spike week:</b> after the first six weeks, a week with at least 40 negative reviews, at least double the median of the previous eight weeks, and not below any of them.</li>
<li><b>Regression:</b> logistic regression of walked-away on main complaint (reference: crashes &amp; bugs), hours-at-review band, review language (languages under 300 reviews grouped), review timing (first 30 days, days 31–180, later), edited flag, and game in the pooled model. Complaint groups under 100 reviews are merged. Reported as odds ratios with 95% intervals.</li>
<li><b>Sensitivity:</b> every verdict is recomputed with "walked away" set at under 2 and under 5 further hours; each report's limits section gives the result.</li>
<li><b>Sub-reasons:</b> for Civilization VII only, reviews whose main complaint is gameplay &amp; design were sorted in a second pass into ten design choices.</li></ul></details></section>
<section><h2>Reason labels</h2>
<p>A small language model (Claude Haiku 5.5) read each negative review (first 1,200 characters, in its original language) and returned one main reason, an optional second reason, and whether the reviewer wrote that they had quit or would wait for fixes. Review text was treated as untrusted data.</p>
<details><summary>Show the eleven labels and what each covers</summary><div class="scroll"><table><thead><tr><th>Label</th><th class="l">Covers</th></tr></thead><tbody>{reasons}</tbody></table></div></details>
<h3 style="margin-top:18px">Accuracy check</h3>{aud or "<p class='note'>Pending.</p>"}</section>
<section><h2>Limits</h2>
<ul><li><b>Reviewers are not players.</b> Only a small share of buyers write a review, and they are not a random sample. Nothing here estimates churn for the whole player base.</li>
<li><b>Correlation, not cause.</b> A complaint group with a high walk-away rate was not shown to quit <i>because</i> of that complaint. Groups also differ in hours played, purchase timing and expectations.</li>
<li><b>Language is not country.</b> Many players review in English wherever they live; regional pricing, launch timing and hardware differ by market in ways reviews do not record.</li>
<li><b>Review habits differ by community.</b> Some language communities write shorter or more negative reviews in general, so compare a language with itself across games before comparing languages.</li>
<li><b>Playtime is imperfect.</b> Offline play, other platforms and idle time are not separated. Editing a review may refresh its "playtime at review" value; each report shows the walk-away rate with and without edited reviews.</li>
<li><b>Six games, chosen by hand.</b> All drew heavy criticism; patterns may not hold for well-received or free-to-play games.</li>
<li><b>Model labels contain errors</b> at about the rate shown in the accuracy check, possibly more in smaller languages, and one main reason per review hides multi-issue reviews.</li>
<li><b>Patch matching is by date only.</b> Official posts near a spike are listed for context; sales, free weekends and outside news also move review counts.</li></ul></section>
<section><h2>Cost</h2>
<div class="scroll"><table><thead><tr><th>Step</th><th>Model calls</th><th>Input tokens (incl. cached)</th><th>Output tokens</th><th>Cost</th></tr></thead><tbody>{crow}<tr><td><b>Total</b></td><td></td><td></td><td></td><td><b>${cost['total_usd']:.2f}</b></td></tr></tbody></table></div>
<p class="note">Costs are the list-price figures reported with each call's actual token counts, summed by <a href="{REPO}/blob/main/src/cost.py">src/cost.py</a>. Budget cap for the project: $30.</p></section>
<section><h2>Files</h2>
<div class="dl">{''.join(f'<a href="data/{E(o["slug"])}.json">{E(o["slug"])}.json</a>' for o in games)}<a href="data/overview.json">overview.json</a><a href="{REPO}/tree/main/data/public">CSV tables</a><a href="{REPO}">Repository</a></div></section>
</div>"""
    return page("Method & limits — Player Signals", body, ov, desc="Data, definitions, accuracy check, limits and cost.")


def case_study_page(o, ov):
    """Monster Hunter Wilds: what an English-only read misses. Narrative is fixed text; every figure is read from the game's JSON."""
    L = {l["code"]: l for l in o["languages"]}; en = L["english"]; f = o["funnel"]; ovw = o["overview"]; bn = o["behaviour"]["negative"]
    big = sorted([l for l in o["languages"] if l["code"] not in ("_small",) and l["reviews"] >= 5000], key=lambda l: -l["reviews"])
    worst = max(big, key=lambda l: l["negative_share"])
    non_en = [l for l in big if l["code"] != "english"]
    months = [m for m in o["monthly"] if m["reviews"] >= 1000]; peak = max(months, key=lambda m: m["negative_share"]); launch = max(o["monthly"], key=lambda m: m["reviews"])
    vets = max(big, key=lambda l: l["median_hours_at_negative_review"] or 0)
    lrow = "".join(f"<tr><td>{E(l['language'])}</td><td>{num(l['reviews'])}</td>{barcell(l['negative_share'])}<td>{l['median_hours_at_negative_review']}</td>{barcell(l['neg_walk_rate'], 'o')}"
                   f"<td class='l'>{E(l['top_reason'] or '–')}{' (' + pct(l['top_reason_share']) + ')' if l['top_reason_share'] is not None else ''}</td></tr>" for l in big)
    codes = o["language_reason_columns"]
    hrow = "".join(f"<tr><td>{E(l['language'])} <span class='small'>n={l['labeled']:,}</span></td>" + "".join(heat(l["reason_shares"].get(c)) for c in codes) + "</tr>" for l in big)
    spikes = "".join(f"<li>Week of {E(sp['week_start'])}: {num(sp['negative'])} negative reviews against a usual {sp['usual_weekly_negative']:.0f}. Nearby official posts: {E('; '.join(p_['title'] for p_ in sp['official_posts'][:2]) or 'none found')}.</li>" for sp in o["spikes"][:3])
    body = f"""<div class="wrap" style="max-width:900px">
<div class="kicker">Case study · Monster Hunter Wilds</div>
<h1>The review score that hid a market</h1>
<p class="lede">Read in English, this game has a complaint problem. Read in every language, it has a market problem. Here is how I got from one to the other, and what I would do with it.</p>
<div class="meta">Analysis run with an AI agent · numbers from <a href="data/{E(o['slug'])}.json">the report data</a> · <a href="games/{E(o['slug'])}.html">full report</a></div>

<section><h2>The question</h2>
<p>The first version of this project read English reviews only. On that view the game looked healthy enough: <b>{pct(en['negative_share'])}</b> of {num(en['reviews'])} English reviews were negative, and the dominant complaint was performance. The obvious advice was "keep patching performance".</p>
<p>Then I pulled every language. English turned out to be only <b>{pct(en['share_of_reviews'])}</b> of the reviews. So the question became simple: does the other {pct(1-en['share_of_reviews'])} say the same thing?</p></section>

<section><h2>What the data shows</h2>
<div class="kpis"><div class="kpi"><div class="l">English reviews</div><b>{pct(en['negative_share'])}</b><div class="s">negative</div></div>
<div class="kpi"><div class="l">All languages</div><b>{pct(ovw['negative_share'])}</b><div class="s">negative, {num(ovw['reviews'])} reviews</div></div>
<div class="kpi"><div class="l">{E(worst['language'])}</div><b>{pct(worst['negative_share'])}</b><div class="s">negative, {num(worst['reviews'])} reviews</div></div>
<div class="kpi"><div class="l">Worst month</div><b>{pct(peak['negative_share'])}</b><div class="s">negative in {E(peak['month'])}</div></div></div>
<p>It does not. Languages with 5,000 or more reviews:</p>
<div class="scroll"><table><thead><tr><th>Review language</th><th>Reviews</th><th class="l">Negative share</th><th>Median hours played at negative review</th><th class="l">Critics who walked away</th><th class="l">Top named complaint</th></tr></thead><tbody>{lrow}</tbody></table></div>
<p>Three things stand out to me.</p>
<ul>
<li><b>The gap is large.</b> {E(worst['language'])} reviews are {pct(worst['negative_share'])} negative against {pct(en['negative_share'])} in English. That is not a rounding difference between communities; it is a different verdict.</li>
<li><b>The unhappy players are not people who bounced.</b> The median {E(vets['language'])} critic had played <b>{vets['median_hours_at_negative_review']} hours</b> when they wrote the review (English critics: {en['median_hours_at_negative_review']}). These are invested players.</li>
<li><b>Most of them kept playing.</b> Across all languages only {pct(bn['walk_rate'])} of critics logged under one more hour after reviewing. The anger and the engagement sit in the same people.</li></ul>
<h3 style="margin-top:18px">What each community complains about</h3>
<p class="note">Share of that language's labeled negative reviews.</p>
<div class="scroll"><table><thead><tr><th>Review language</th>{"".join(f"<th>{E(SHORT[c])}</th>" for c in codes)}</tr></thead><tbody>{hrow}</tbody></table></div></section>

<section><h2>When it happened</h2>
<p>The launch month ({E(launch['month'])}) brought {num(launch['reviews'])} reviews at {pct(launch['negative_share'])} negative. The worst stretch came later: <b>{E(peak['month'])}</b> ran at {pct(peak['negative_share'])} negative on {num(peak['reviews'])} reviews. The weeks with the sharpest jumps:</p>
<ul class="note">{spikes}</ul>
<p class="note">Review spikes sit next to official update posts. That is a lead, not a finding: sales and outside news move review counts too.</p></section>

<section><h2>What I would tell the studio</h2>
<div class="team"><h3><span class="chip own">Publishing</span>Stop reading the English score as the score</h3><div class="note">The store shows each visitor reviews in their own language. A team that tracks the English number is tracking the experience of {pct(en['share_of_reviews'])} of reviewers.</div></div>
<div class="team"><h3><span class="chip own">Live ops &amp; community</span>Treat this as a win-back situation, not a lost audience</h3><div class="note">{pct(bn['kept_10h_rate'])} of critics played 10 or more further hours, and {pct(bn['active_now_rate'])} were active in the two weeks before the snapshot. They are reachable, and they are telling you what they want fixed.</div></div>
<div class="team"><h3><span class="chip own">Engineering</span>Check performance by region before assuming one cause</h3><div class="note">The complaint mix differs by language. Hardware, storefront pricing and typical session length differ by region too, and reviews cannot separate them.</div></div></section>

<section><h2>What I would need before believing it</h2>
<ul>
<li><b>Telemetry by region.</b> Review language is a stand-in for market. Actual crash rates, frame times and session lengths by country would confirm or kill this.</li>
<li><b>Review habits by community.</b> Some language communities review more harshly in general. The fair comparison is each language against itself on other games, which the <a href="index.html#markets">markets table</a> starts to show.</li>
<li><b>Human-checked labels in each language.</b> The complaint labels were written by a small AI model and spot-checked by a larger one, not by native speakers.</li>
<li><b>Cause.</b> Nothing here shows that a patch, a price or a performance problem made anyone leave.</li></ul></section>

<section><h2>What I took from it</h2>
<p>The method did not change between the two versions of this project. The sample did. The English-only version was internally consistent, carefully caveated, and pointed at the wrong priority. Since then I check who is missing from the data before I look at what the data says.</p></section>
</div>"""
    return page("Case study: the review score that hid a market — Player Signals", body, ov, desc="Monster Hunter Wilds: what an English-only read of Steam reviews misses.")


if __name__ == "__main__":
    ov = load("overview.json"); audit = load("label_audit.json"); cost = load("cost.json") or dict(total_usd=0, rows=[])
    games = [load(o["slug"] + ".json") for o in ov]
    os.makedirs(os.path.join(DOCS, "games"), exist_ok=True)
    open(os.path.join(DOCS, ".nojekyll"), "w").write("")
    models = load("models.json"); fans = load("fans.json")
    open(os.path.join(DOCS, "fans.html"), "w").write(fans_page(fans, ov))
    idx, quit_html, data_html = index_page(ov, games, audit, cost, models, load("after_review.json"), fans_headline(fans))
    open(os.path.join(DOCS, "index.html"), "w").write(idx); open(os.path.join(DOCS, "quit.html"), "w").write(quit_html); open(os.path.join(DOCS, "data.html"), "w").write(data_html)
    open(os.path.join(DOCS, "method.html"), "w").write(method_page(ov, games, audit, cost))
    for o in games: open(os.path.join(DOCS, "games", o["slug"] + ".html"), "w").write(game_page(o, audit, ov))
    open(os.path.join(DOCS, "case-study.html"), "w").write(case_study_page(next(o for o in games if o["slug"] == "monster-hunter-wilds"), ov))
    print("built", 6 + len(games), "pages")
