"""Weekly email digest: one short HTML email per game, ready to send. Nothing is sent by this script.

Input : docs/data/weekly.json, benchmark.json, after_review_all.json
Output: docs/digest/<slug>.html  (numbers only; table layout and inline styles so email apps render it)
"""
import html, json, os
from analyze import ROOT

SITE = "https://hosungkim48.github.io/whyplayersquit-lab/"
E = html.escape; p = lambda v: "–" if v is None else f"{v * 100:.0f}%"
KIND = {"volume": "a review spike", "more_negative": "reviews more negative than usual", "more_positive": "reviews more positive than usual"}


def digest(w, b, a):
    l = w["latest"]; mv = {m["key"]: m for m in b["measures"]}
    status = ("This week stood out: " + " and ".join(KIND[f] for f in l["flags"]) + ".") if l["flags"] else "Nothing unusual this week."
    cell = lambda big, small: f'<td width="50%" style="padding:14px 16px;background:#131c30;border:1px solid #27324a;border-radius:10px"><div style="font-size:26px;font-weight:700;color:#eef2f8">{big}</div><div style="font-size:13px;color:#a9b4c6">{small}</div></td>'
    rows = "".join(f'<tr><td style="padding:7px 0;border-bottom:1px solid #27324a;color:#b9c3d3">{E(r["week"])}</td><td align="right" style="padding:7px 0;border-bottom:1px solid #27324a;color:#eef2f8">{r["reviews"]:,}</td>'
                   f'<td align="right" style="padding:7px 0;border-bottom:1px solid #27324a;color:#eef2f8">{p(r["negative_share"])}</td><td align="right" style="padding:7px 0;border-bottom:1px solid #27324a;color:{"#f6a07a" if r["flags"] else "#a9b4c6"}">{E(", ".join(KIND[f] for f in r["flags"])) or "–"}</td></tr>' for r in reversed(w["weeks"][-6:]))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Player Signals weekly: {E(w["name"])}, week of {E(l["week"])}</title></head>
<body style="margin:0;background:#090e19;font-family:Inter,Segoe UI,Helvetica,Arial,sans-serif;color:#eef2f8">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#090e19"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">
<tr><td style="font-size:13px;color:#a9b4c6;padding-bottom:6px">Player Signals · weekly digest · week of {E(l["week"])}</td></tr>
<tr><td style="font-size:26px;font-weight:700;line-height:1.2;padding-bottom:8px">{E(w["name"])}</td></tr>
<tr><td style="font-size:16px;color:#b9c3d3;padding-bottom:18px">{E(status)}</td></tr>
<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="8" style="border-collapse:separate"><tr>
{cell(f"{l['reviews']:,}", f"new reviews · a usual week: {l['usual_reviews']:,.0f}")}{cell(p(l["negative_share"]), f"were negative · usual: {p(l['usual_negative_share'])}")}</tr><tr>
{cell(p(a["negative"]["walk_rate"]), f"of critics stopped playing · similar games: {p(mv['critics_stopped']['peer_median'])}")}{cell(p(a["positive"]["walk_rate"]), f"of fans stopped playing · similar games: {p(mv['fans_stopped']['peer_median'])}")}</tr></table></td></tr>
<tr><td style="padding:22px 8px 6px;font-size:15px;font-weight:700">Last 6 weeks</td></tr>
<tr><td style="padding:0 8px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px">
<tr><td style="padding:6px 0;color:#a9b4c6;font-size:12px">Week starting</td><td align="right" style="color:#a9b4c6;font-size:12px">Reviews</td><td align="right" style="color:#a9b4c6;font-size:12px">Negative</td><td align="right" style="color:#a9b4c6;font-size:12px">Flag</td></tr>{rows}</table></td></tr>
<tr><td style="padding:24px 8px"><a href="{SITE}dash/{E(w["slug"])}.html" style="display:inline-block;background:#5a9cec;color:#090e19;text-decoration:none;font-weight:700;padding:12px 18px;border-radius:10px">Open the dashboard</a></td></tr>
<tr><td style="padding:0 8px 24px;font-size:12px;color:#a9b4c6;line-height:1.5">"Stopped playing" means under one more hour logged after the review, for reviews at least 30 days old. These are reviewers, not all players, and a pattern here isn't proof of cause. Built only from public Steam reviews, as of {E(w["snapshot"])}.</td></tr>
</table></td></tr></table></body></html>"""


if __name__ == "__main__":
    D = os.path.join(ROOT, "docs", "data"); L = lambda n: json.load(open(os.path.join(D, n)))
    wk = L("weekly.json"); bm = {g["slug"]: g for g in L("benchmark.json")["games"]}; ar = {g["slug"]: g for g in L("after_review_all.json")["games"]}
    out = os.path.join(ROOT, "docs", "digest"); os.makedirs(out, exist_ok=True)
    for w in wk["games"]: open(os.path.join(out, w["slug"] + ".html"), "w").write(digest(w, bm[w["slug"]], ar[w["slug"]]))
    print("wrote", len(wk["games"]), "digests")
