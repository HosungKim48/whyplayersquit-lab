"""When do players who recommend a game write their review, and where does that sit in their whole playtime?

Input : data/work/reviews_<appid>.parquet (local)
Output: docs/data/fans.json, data/public/fans_review_timing.csv
Only reviews at least MATURE_DAYS old, so total playtime has had time to build up. Total hours = hours at review + hours since.
"Position" = hours at review / total hours: 0% = reviewed at the very start of their time with the game, 100% = never played again.
No review text and no IDs are read or written.
"""
import csv, json, math, os
import numpy as np
import pandas as pd
import sys
from games import GAMES, all_games
from analyze import MATURE_DAYS, MIN_CELL, ROOT

COLS = ["voted_up", "hours_at_review", "hours_after_review", "days_since_review"]
GROUPS = [(0, 10, "Under 10 h"), (10, 50, "10–50 h"), (50, 200, "50–200 h"), (200, 500, "200–500 h"), (500, 1e9, "500 h+")]
EDGES = [0] + [round(0.5 * 2 ** (k / 2), 3) for k in range(23)] + [1e9]   # hours played at review: 0.5 h to 1,024 h, each band 1.41 times the last
POS = [i / 10 for i in range(11)]                                                              # position in whole playtime


def q(x, p): return round(float(np.quantile(x, p)), 1) if len(x) else None


def timing(h):
    """Share of reviews in each hours-at-review bin, and the usual window (middle half)."""
    n = len(h); c = np.histogram(h, EDGES)[0]
    return dict(n=n, p10=q(h, .1), p25=q(h, .25), median=q(h, .5), p75=q(h, .75), p90=q(h, .9),
                curve=[round(float(k) / n, 4) for k in c] if n else [])


def summarize(df):
    m = df[df.days_since_review >= MATURE_DAYS]
    pos, neg = m[m.voted_up], m[~m.voted_up]
    total = pos.hours_at_review + pos.hours_after_review
    position = (pos.hours_at_review / total.where(total > 0)).clip(0, 1)
    groups = []
    for lo, hi, name in GROUPS:
        g = (total >= lo) & (total < hi); p = position[g].dropna(); n = int(g.sum())
        if n < MIN_CELL: groups.append(dict(group=name, n=n)); continue
        c = np.histogram(p, POS)[0]
        groups.append(dict(group=name, n=n, share=round(n / len(pos), 4), median_hours_at_review=q(pos.hours_at_review[g], .5), median_total_hours=q(total[g], .5),
                           position_p25=round(float(p.quantile(.25)), 3), position_median=round(float(p.median()), 3), position_p75=round(float(p.quantile(.75)), 3),
                           reviewed_in_last_tenth=round(float((p >= .9).mean()), 4), curve=[round(float(k) / len(p), 4) for k in c]))
    return dict(recommended=timing(pos.hours_at_review.to_numpy()), not_recommended=timing(neg.hours_at_review.to_numpy()), by_total_hours=groups)


if __name__ == "__main__":
    ALL = "--all" in sys.argv; SFX = "_all" if ALL else ""   # --all: the six studied games plus the expansion games, written to separate files
    frames = []; games = []
    for g in (all_games() if ALL else GAMES):
        df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet"), columns=COLS)
        frames.append(df); games.append(dict(slug=g["slug"], name=g["name"], genre=g["genre"], **summarize(df)))
    out = dict(params=dict(mature_days=MATURE_DAYS, min_cell=MIN_CELL, hour_edges=EDGES[:-1], position_edges=POS, groups=[x[2] for x in GROUPS]), pooled=summarize(pd.concat(frames)), games=games)
    json.dump(out, open(os.path.join(ROOT, "docs", "data", "fans" + SFX + ".json"), "w"), indent=1)
    with open(os.path.join(ROOT, "data", "public", "fans_review_timing" + SFX + ".csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["game", "total_hours_group", "recommended_reviews", "share", "median_hours_at_review", "median_total_hours", "position_p25", "position_median", "position_p75", "reviewed_in_last_tenth"])
        for g in games + [dict(name=f"All {len(games)} games" if ALL else "All six games", **out["pooled"])]:
            for r in g["by_total_hours"]:
                w.writerow([g["name"], r["group"], r["n"]] + [r.get(k) for k in ("share", "median_hours_at_review", "median_total_hours", "position_p25", "position_median", "position_p75", "reviewed_in_last_tenth")])
    for g in games + [dict(name="POOLED", **out["pooled"])]:
        r = g["recommended"]; print(f"{g['name'][:24]:24} rec: p25 {r['p25']} med {r['median']} p75 {r['p75']} | not rec med {g['not_recommended']['median']} | " + " ".join(f"{x['group']}: n{x['n']} at {x.get('median_hours_at_review')}h pos {x.get('position_median')} last10 {x.get('reviewed_in_last_tenth')}" for x in g["by_total_hours"]))
