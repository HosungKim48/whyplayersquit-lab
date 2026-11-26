"""Add more games with the free numbers only: behaviour after the review. No model calls, no cost.

Run this on a computer that can reach Steam (not inside a sandbox):
    python3 expand.py --check     # check the candidate list against Steam; fetch nothing
    python3 expand.py             # check, fetch, build local tables, recompute the all-game files
Safe to stop and run again: every fetched page is cached, so it resumes where it stopped.

Steps and what each writes:
 1. check   -> data/public/expansion_check.csv   (every candidate, Steam's own name and review count, kept or skipped and why)
               data/public/expansion_games.json  (the kept games)
 2. fetch   -> data/raw/<appid>/ and data/raw/<appid>_other/   (local only: review text and reviewer IDs)
 3. build   -> data/work/reviews_<appid>.parquet               (local only)
 4. numbers -> docs/data/after_review_all.json, docs/data/fans_all.json, plus CSVs in data/public  (no text, no IDs)
"""
import concurrent.futures as cf, csv, json, os, re, subprocess, sys, time
import requests
from games import CANDIDATES, EXPANSION_TARGET, EXPANSION_MAX_REVIEWS, EXPANSION_MIN_REVIEWS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUB = os.path.join(ROOT, "data", "public")
UA = {"User-Agent": "student-research-script (low rate, cached)"}
norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())


def get(url, params):
    for attempt in range(5):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=40)
            if r.status_code == 200: return r.json()
        except Exception:
            pass
        time.sleep(10 * (attempt + 1))
    return None


def check(c):
    """One small request for Steam's own review totals, one for the store name and price type."""
    row = dict(appid=c["appid"], expected_name=c["name"], steam_name=None, is_free=None, total_reviews=None, score=None, decision="skip", reason="")
    s = get("https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/", dict(appid=c["appid"], **{"languages[0]": "all"}, filter="recent", review_type="all", purchase_type="all", num_per_page=1, filter_offtopic_activity=0, cursor="*"))
    time.sleep(1.5)
    d = get("https://store.steampowered.com/api/appdetails", dict(appids=c["appid"], l="english", filters="basic"))
    time.sleep(1.5)
    if not s or not d: row["reason"] = "Steam did not answer"; return row
    q = s.get("response", {}).get("query_summary", {}); info = (d.get(str(c["appid"])) or {})
    if not info.get("success"): row["reason"] = "no store page for this app ID"; return row
    row.update(steam_name=info["data"].get("name"), is_free=info["data"].get("is_free"), total_reviews=q.get("total_reviews"), score=q.get("review_score_desc"))
    a, b = norm(c["name"]), norm(row["steam_name"])
    if not a or not b or not (a in b or b in a): row["reason"] = "app ID belongs to a different game"
    elif row["is_free"]: row["reason"] = "free to play (the review endpoint is unreliable for these)"
    elif not row["total_reviews"]: row["reason"] = "Steam returned no review total"
    elif row["total_reviews"] > EXPANSION_MAX_REVIEWS: row["reason"] = f"more than {EXPANSION_MAX_REVIEWS:,} reviews"
    elif row["total_reviews"] < EXPANSION_MIN_REVIEWS: row["reason"] = f"fewer than {EXPANSION_MIN_REVIEWS:,} reviews"
    else: row["decision"] = "ok"
    return row


def run_check():
    rows = []; kept = []
    for c in CANDIDATES:
        r = check(c)
        if r["decision"] == "ok" and len(kept) >= EXPANSION_TARGET: r.update(decision="spare", reason="passed, not needed")
        elif r["decision"] == "ok": r["decision"] = "keep"; kept.append(dict(c, steam_total_reviews=r["total_reviews"], steam_score=r["score"]))
        rows.append(r); print(f"{r['decision']:5} {c['name'][:40]:40} {str(r['total_reviews']):>8} {r['score'] or ''} {r['reason']}", flush=True)
    with open(os.path.join(PUB, "expansion_check.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    json.dump(kept, open(os.path.join(PUB, "expansion_games.json"), "w"), indent=1)
    total = sum(g["steam_total_reviews"] for g in kept)
    print(f"\nKept {len(kept)} of {len(CANDIDATES)} candidates, {total:,} reviews to fetch, about {total / 100 / 3600 * 1.1:.1f} hours at one request a second.")
    return kept


def fetch_and_build(g):
    from fetch_reviews import fetch_game
    from build_dataset import build
    try:
        fetch_game(g, "english"); fetch_game(g, "other")
        r = build(g); got = r["unique_reviews"]; want = g["steam_total_reviews"]
        return dict(name=g["name"], appid=g["appid"], fetched=got, steam_total=want, coverage=round(got / want, 3) if want else None, complete=bool(r["all_windows_done"]))
    except Exception as e:
        return dict(name=g["name"], appid=g["appid"], error=repr(e)[:200])


if __name__ == "__main__":
    kept = run_check()
    if "--check" in sys.argv: sys.exit(0)
    with cf.ThreadPoolExecutor(4) as ex: res = list(ex.map(fetch_and_build, kept))   # four games at a time, as in the first run
    with open(os.path.join(PUB, "expansion_fetch.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "appid", "fetched", "steam_total", "coverage", "complete", "error"]); w.writeheader(); w.writerows(res)
    bad = [r for r in res if r.get("error") or not r.get("complete") or (r.get("coverage") or 0) < 0.97]
    for script in ("after_review.py", "fans.py"): subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), script), "--all"], check=True)
    print("\nFetched", sum(r.get("fetched") or 0 for r in res), "reviews for", len(res) - sum(1 for r in res if r.get("error")), "games.")
    if bad:
        print("Needs a look (run the same command again to resume; coverage under 97% can mean the start month is too late):")
        for r in bad: print("  ", r)
    print("EXPANSION_DONE" if not bad else "EXPANSION_DONE_WITH_WARNINGS")
