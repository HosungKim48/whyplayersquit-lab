"""What reviewers did after writing a review, for ALL reviews (recommended and not recommended).

Input : data/work/reviews_<appid>.parquet (local)
Output: docs/data/after_review.json, data/public/after_review_by_hours.csv
Same definitions as analyze.py: only reviews at least MATURE_DAYS old; "walked away" = under WALK_HOURS more play.
The recommended reviewers are the baseline: they show how often a reviewer stops at a given stage of play
without having complained. No review text and no IDs are read or written.
"""
import csv, json, os
import pandas as pd
import sys
from games import GAMES, all_games
from analyze import BUCKETS, MATURE_DAYS, WALK_HOURS, MIN_CELL, ROOT, wilson

COLS = ["voted_up", "hours_at_review", "hours_after_review", "days_since_review", "pt_2w"]


def cell(m):
    n = len(m)
    if n < MIN_CELL: return dict(n=n, walk_rate=None)
    k = int((m.hours_after_review < WALK_HOURS).sum()); lo, hi = wilson(k, n)
    return dict(n=n, walked_away=k, walk_rate=round(k / n, 4), walk_lo=lo, walk_hi=hi,
                kept_10h_rate=round(float((m.hours_after_review >= 10).mean()), 4),
                median_hours_after=round(float(m.hours_after_review.median()), 1),
                active_now_rate=round(float((m.pt_2w > 0).mean()), 4))


def summarize(df):
    m = df[(df.days_since_review >= MATURE_DAYS) & df.hours_at_review.notna()].copy()   # a few old reviews (Frostpunk, 2018) have no playtime at review
    m["bucket"] = pd.cut(m.hours_at_review, [b[0] for b in BUCKETS] + [1e9], labels=[b[2] for b in BUCKETS], right=False)
    pos, neg = m[m.voted_up], m[~m.voted_up]
    rows = []; expected = 0.0; ok = True
    for _, _, name in BUCKETS:
        p, n = cell(pos[pos.bucket == name]), cell(neg[neg.bucket == name])
        gap = round(n["walk_rate"] - p["walk_rate"], 4) if n["walk_rate"] is not None and p["walk_rate"] is not None else None
        rows.append(dict(bucket=name, positive=p, negative=n, gap=gap))
        if p["walk_rate"] is None: ok = ok and n["n"] == 0
        else: expected += n["n"] / max(len(neg), 1) * p["walk_rate"]
    P, N = cell(pos), cell(neg)
    # baseline: the walk-away rate recommended reviewers would show if they had the critics' mix of hours played
    base = round(expected, 4) if ok else None
    return dict(reviews=len(m), positive=P, negative=N, by_hours=rows, baseline_at_critics_hours=base,
                excess_over_baseline=round(N["walk_rate"] - base, 4) if base is not None and N["walk_rate"] is not None else None)


if __name__ == "__main__":
    ALL = "--all" in sys.argv; SFX = "_all" if ALL else ""   # --all: the six studied games plus the expansion games, written to separate files
    frames = []; games = []
    for g in (all_games() if ALL else GAMES):
        df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet"), columns=COLS)
        frames.append(df); games.append(dict(slug=g["slug"], name=g["name"], genre=g["genre"], **summarize(df)))
    out = dict(params=dict(mature_days=MATURE_DAYS, walk_hours=WALK_HOURS, min_cell=MIN_CELL), pooled=summarize(pd.concat(frames)), games=games)
    json.dump(out, open(os.path.join(ROOT, "docs", "data", "after_review" + SFX + ".json"), "w"), indent=1)
    with open(os.path.join(ROOT, "data", "public", "after_review_by_hours" + SFX + ".csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["game", "hours_at_review", "verdict", "reviews", "walked_away", "walk_rate", "walk_lo", "walk_hi", "kept_10h_rate", "median_hours_after", "active_now_rate"])
        for g in games + [dict(name=f"All {len(games)} games" if ALL else "All six games", **out["pooled"])]:
            for r in g["by_hours"]:
                for v in ("positive", "negative"):
                    c = r[v]; w.writerow([g["name"], r["bucket"], "recommended" if v == "positive" else "not recommended", c["n"]] + [c.get(k) for k in ("walked_away", "walk_rate", "walk_lo", "walk_hi", "kept_10h_rate", "median_hours_after", "active_now_rate")])
    for g in games + [dict(name="POOLED", **out["pooled"])]:
        print(f"{g['name'][:26]:26} pos {g['positive']['walk_rate']} neg {g['negative']['walk_rate']} baseline {g['baseline_at_critics_hours']} excess {g['excess_over_baseline']} | " + " ".join(f"{r['bucket']}: {r['positive']['walk_rate']}/{r['negative']['walk_rate']}" for r in g["by_hours"]))
