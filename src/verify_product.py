"""Checks for the product pages and the weekly workflow outputs. Exits non-zero on any failure.
1. Weekly counts, the latest week and the overall negative share are recomputed from the local tables.
2. Benchmark values match their source files; ranks are consistent.
3. Every game has a dashboard, a digest, an API file and two CSV files, and each dashboard shows its JSON figures.
4. Every local link on every page points at a file that exists.
5. No reviewer IDs or review IDs in the new files.
"""
import glob, json, os, re, sys
import pandas as pd
from games import all_games
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); DOCS = os.path.join(ROOT, "docs")
fail = []
def check(ok, msg):
    if not ok: fail.append(msg); print("FAIL " + msg)
L = lambda n: json.load(open(os.path.join(DOCS, "data", n)))
wk = L("weekly.json"); bm = {g["slug"]: g for g in L("benchmark.json")["games"]}; ar = {g["slug"]: g for g in L("after_review_all.json")["games"]}; fans = {g["slug"]: g for g in L("fans_all.json")["games"]}
games = all_games(); n = 0
check(len(wk["games"]) == len(games) == len(bm), "every game is in weekly.json and benchmark.json")
new_files = glob.glob(os.path.join(DOCS, "dash", "*")) + glob.glob(os.path.join(DOCS, "digest", "*")) + glob.glob(os.path.join(DOCS, "api", "v1", "**", "*.json"), recursive=True) + glob.glob(os.path.join(DOCS, "export", "*")) + [os.path.join(DOCS, f) for f in ("features.html", "pricing.html", "dashboards.html", "api.html", "data/weekly.json", "data/benchmark.json", "data/alerts.json")]
blob = "\n".join(open(f, errors="ignore").read() for f in new_files)
check(not re.search(r"7656119\d{10}", blob), "no 17-digit Steam IDs in the new files")
for g in games:
    s = g["slug"]; w = next(x for x in wk["games"] if x["slug"] == s)
    df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet"), columns=["rid", "created", "voted_up"])
    check(w["reviews"] == len(df) and abs(w["negative_share"] - (~df.voted_up).mean()) < 1e-4, f"{s}: totals match the local table")
    # independent recount of the latest week: plain timestamp arithmetic instead of pandas periods
    t0 = int(pd.Timestamp(w["latest"]["week"]).timestamp()); m = df[(df.created >= t0) & (df.created < t0 + 7 * 86400)]
    check(pd.Timestamp(w["latest"]["week"]).dayofweek == 0 and w["latest"]["reviews"] == len(m) and w["latest"]["negative"] == int((~m.voted_up).sum()), f"{s}: latest week recounted independently")
    t52 = int(pd.Timestamp(w["weeks"][0]["week"]).timestamp()); check(sum(r["reviews"] for r in w["weeks"]) == int(((df.created >= t52) & (df.created < t0 + 7 * 86400)).sum()), f"{s}: 52 weekly counts add up")
    mv = {x["key"]: x for x in bm[s]["measures"]}
    check(mv["critics_stopped"]["value"] == ar[s]["negative"]["walk_rate"] and mv["fans_stopped"]["value"] == ar[s]["positive"]["walk_rate"] and mv["fan_review_hours"]["value"] == fans[s]["recommended"]["median"] and mv["negative_share"]["value"] == w["negative_share"], f"{s}: benchmark values match their sources")
    check(all(1 <= x["rank"] <= x["of"] and x["all_min"] <= x["value"] <= x["all_max"] for x in mv.values()), f"{s}: ranks in range")
    paths = [f"dash/{s}.html", f"digest/{s}.html", f"api/v1/games/{s}.json", f"export/{s}_weekly.csv", f"export/{s}_summary.csv"]
    check(all(os.path.exists(os.path.join(DOCS, p)) for p in paths), f"{s}: dashboard, digest, API file and CSVs exist")
    page = open(os.path.join(DOCS, "dash", s + ".html")).read(); dg = open(os.path.join(DOCS, "digest", s + ".html")).read()
    figs = [f"{w['reviews']:,}", f"{w['latest']['reviews']:,}", f"{ar[s]['negative']['walk_rate'] * 100:.0f}%", f"{ar[s]['positive']['walk_rate'] * 100:.0f}%"]
    check(all(f in page for f in figs) and all(f in dg for f in figs[1:]), f"{s}: dashboard and digest show the JSON figures")
    check(not any(i in blob for i in df.rid.astype(str).head(2000)), f"{s}: no review IDs in the new files (2,000 checked)")
    api = json.load(open(os.path.join(DOCS, "api", "v1", "games", s + ".json"))); check(api["reviews"] == w["reviews"] and len(api["weekly"]) == 52, f"{s}: API file agrees with weekly.json")
    n += 9
# peers: medians recomputed
import statistics
for s, b in bm.items():
    for x in b["measures"]:
        pv = [m["value"] for t, o in bm.items() if o["family"] == b["family"] and t != s for m in o["measures"] if m["key"] == x["key"] and m["value"] is not None]
        check(x["peer_median"] == round(statistics.median(pv), 4), f"{s}: peer median for {x['key']} recomputed"); n += 1
# links
bad = []
for f in glob.glob(os.path.join(DOCS, "**", "*.html"), recursive=True):
    for href in re.findall(r'href="([^"#]+)(?:#[^"]*)?"', open(f).read()):
        if href.startswith(("http", "mailto:")): continue
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), href))): bad.append((os.path.relpath(f, DOCS), href))
check(not bad, f"all local links resolve {bad[:5]}"); n += 3
print(f"\n{n - len(fail)} of {n} product checks passed"); print("FAILED" if fail else "ALL PRODUCT CHECKS PASSED"); sys.exit(1 if fail else 0)
