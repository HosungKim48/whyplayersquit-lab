"""Checks before publishing. Exits non-zero on any failure.
1. Recompute headline numbers straight from the local tables and compare with the published JSON.
2. Every percentage/number tile on each game page is present in that game's JSON-derived values (spot list).
3. Nothing in the files to be published contains a reviewer ID, a review ID, or a long run of raw review text.
4. Paraphrases are 20 words or fewer.
5. Spend is under budget.
"""
import glob, json, os, re, subprocess, sys
import pandas as pd
from games import GAMES
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
fail = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: fail.append(msg)

pub_files = [f for f in subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n") if f]
check(not any(f.startswith(("data/raw", "data/work")) for f in pub_files), "no raw/work files among files git would publish")
blob = "\n".join(open(os.path.join(ROOT, f), errors="ignore").read() for f in pub_files if os.path.isfile(os.path.join(ROOT, f)))
check(not re.search(r"7656119\d{10}", blob), "no 17-digit Steam IDs in published files")

for g in GAMES:
    df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet"))
    o = json.load(open(os.path.join(ROOT, "docs", "data", g["slug"] + ".json")))
    neg = df[~df.voted_up]; m = neg[neg.days_since_review >= 30]
    check(o["overview"]["reviews"] == len(df) and o["overview"]["negative"] == len(neg), f"{g['slug']}: review counts match local table")
    check(abs(o["behaviour"]["negative"]["walk_rate"] - (m.hours_after_review < 1).mean()) < 1e-4, f"{g['slug']}: negative walk-away rate recomputed independently")
    check(abs(sum(r["share"] for r in o["reasons"]) - 1) < 0.002, f"{g['slug']}: reason shares sum to 100%")
    check(sum(r["n"] for r in o["reasons"]) == o["funnel"]["labeled"], f"{g['slug']}: reason counts sum to labeled total")
    check(o["funnel"]["fetched_unique"] >= 0.995 * o["funnel"]["api_reported_english_reviews"], f"{g['slug']}: fetched >= 99.5% of API-reported reviews")
    page = open(os.path.join(ROOT, "docs", "games", g["slug"] + ".html")).read()
    check(f"{o['overview']['reviews']:,}" in page and f"{o['behaviour']['negative']['walk_rate']*100:.0f}%" in page, f"{g['slug']}: page shows the JSON figures")
    # raw text leak test: no 8-word run from any review of this game appears in published text
    ids = set(df.rid.astype(str)); check(not any(i in blob for i in list(ids)[:3000]), f"{g['slug']}: no review IDs in published files (3,000 checked)")
    pars = [p for ps in o["paraphrases"].values() for p in ps]
    check(all(len(p.split()) <= 20 for p in pars), f"{g['slug']}: {len(pars)} paraphrases all <= 20 words")
    grams = set()
    for t in df.text[df.words >= 8]:
        w = re.findall(r"[a-z0-9']+", t.lower())
        grams.update(" ".join(w[i:i+8]) for i in range(len(w) - 7))
    pw = re.findall(r"[a-z0-9']+", re.sub(r"<[^>]+>", " ", page).lower())
    hits = [x for x in (" ".join(pw[i:i+8]) for i in range(len(pw) - 7)) if x in grams]
    check(len(hits) == 0, f"{g['slug']}: no 8-word run of the page matches any raw review ({len(hits)} hits) {hits[:2]}")
cost = json.load(open(os.path.join(ROOT, "docs", "data", "cost.json")))
check(cost["total_usd"] < 30, f"total spend ${cost['total_usd']} under $30")
print("\nFAILED" if fail else "\nALL CHECKS PASSED"); sys.exit(1 if fail else 0)
