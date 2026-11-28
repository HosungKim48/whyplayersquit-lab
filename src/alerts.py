"""Alerts: turn flagged weeks from the monitor into short messages for Discord or Slack.

Input : docs/data/weekly.json
Output: docs/data/alerts.json  (every flagged week of the last year, with its message; numbers only)
Sending is off unless asked for:
    python3 alerts.py                 # write alerts.json, print this week's messages, send nothing
    python3 alerts.py --send          # also post this week's messages to the webhooks in src/webhooks.json
src/webhooks.json is local only (gitignored). Shape: {"<slug>": {"discord": "<webhook url>", "slack": "<webhook url>"}}
Only the latest complete week is ever sent, and each (game, week) is sent once (data/work/alerts_sent.json).
"""
import json, os, sys
from analyze import ROOT

SITE = "https://hosungkim48.github.io/whyplayersquit-lab/"
p = lambda v: "–" if v is None else f"{v * 100:.0f}%"


def message(g, r):
    kind = "Review spike" if "volume" in r["flags"] else "Reviews turned more negative" if "more_negative" in r["flags"] else "Reviews turned more positive"
    text = (f"Week of {r['week']}: {r['reviews']:,} new reviews (a usual week: {r['usual_reviews']:,.0f}). "
            f"{p(r['negative_share'])} were negative (usual: {p(r['usual_negative_share'])}).")
    return dict(title=f"{kind}: {g['name']}", text=text, link=f"{SITE}dash/{g['slug']}.html")


if __name__ == "__main__":
    wk = json.load(open(os.path.join(ROOT, "docs", "data", "weekly.json")))
    out = []
    for g in wk["games"]:
        for r in g["alerts"]: out.append(dict(slug=g["slug"], game=g["name"], week=r["week"], flags=r["flags"], latest=r["week"] == g["latest"]["week"], **message(g, r)))
    out.sort(key=lambda a: a["week"], reverse=True)
    json.dump(dict(params=wk["params"], alerts=out), open(os.path.join(ROOT, "docs", "data", "alerts.json"), "w"), indent=1)
    now = [a for a in out if a["latest"]]
    print(f"{len(out)} flagged weeks in the last year, {len(now)} in the latest week")
    for a in now: print(" ", a["title"], "|", a["text"])
    if "--send" in sys.argv:
        import requests
        hooks_f = os.path.join(os.path.dirname(__file__), "webhooks.json"); sent_f = os.path.join(ROOT, "data", "work", "alerts_sent.json")
        if not os.path.exists(hooks_f): sys.exit("No src/webhooks.json, nothing sent.")
        hooks = json.load(open(hooks_f)); sent = json.load(open(sent_f)) if os.path.exists(sent_f) else []
        for a in now:
            key = f"{a['slug']}|{a['week']}"; h = hooks.get(a["slug"], {})
            if key in sent or not h: continue
            body = f"**{a['title']}**\n{a['text']}\n{a['link']}"
            if h.get("discord"): requests.post(h["discord"], json=dict(content=body), timeout=20).raise_for_status()
            if h.get("slack"): requests.post(h["slack"], json=dict(text=body.replace("**", "*")), timeout=20).raise_for_status()
            sent.append(key); json.dump(sent, open(sent_f, "w")); print("sent", key)
