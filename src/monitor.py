"""Weekly review monitor: how many reviews each game got per week, how negative they were, and which weeks stand out.

Input : data/work/reviews_<appid>.parquet (local)
Output: docs/data/weekly.json, data/public/weekly_by_game.csv
A week runs Monday to Sunday (UTC). Only complete weeks before the snapshot are counted.
A week is flagged against the BASE weeks before it:
  volume         at least VOL_MIN reviews and at least VOL_X times the usual (median) week
  more_negative  negative share at least SHARE_PTS above the share of the weeks before (both sides need SHARE_MIN reviews)
  more_positive  the same, below
No model calls, no cost. No review text and no IDs are read or written.
"""
import csv, json, os, statistics
import pandas as pd
from games import all_games
from analyze import ROOT

WEEKS, BASE = 52, 8
VOL_X, VOL_MIN, SHARE_PTS, SHARE_MIN = 2.0, 50, 0.15, 30
COLS = ["created", "snapshot", "voted_up"]


def weekly(df):
    snap = pd.to_datetime(int(df.snapshot.max()), unit="s")
    wk = pd.to_datetime(df.created, unit="s").dt.to_period("W-SUN").dt.start_time
    g = pd.DataFrame(dict(week=wk, neg=~df.voted_up)).groupby("week").neg.agg(["size", "sum"])
    last = (snap.to_period("W-SUN").start_time - pd.Timedelta(days=7))          # last complete week
    idx = pd.date_range(end=last, periods=WEEKS + BASE, freq="7D")
    g = g.reindex(idx, fill_value=0)
    n, neg = [int(x) for x in g["size"]], [int(x) for x in g["sum"]]
    rows = []
    for i in range(BASE, len(idx)):
        bn, bneg = n[i - BASE:i], neg[i - BASE:i]; med = statistics.median(bn)
        share = round(neg[i] / n[i], 4) if n[i] else None
        bshare = round(sum(bneg) / sum(bn), 4) if sum(bn) >= SHARE_MIN else None
        flags = []
        if n[i] >= VOL_MIN and n[i] >= VOL_X * max(med, 1): flags.append("volume")
        if n[i] >= SHARE_MIN and bshare is not None:
            if share - bshare >= SHARE_PTS: flags.append("more_negative")
            if share - bshare <= -SHARE_PTS: flags.append("more_positive")
        rows.append(dict(week=idx[i].strftime("%Y-%m-%d"), reviews=n[i], negative=neg[i], negative_share=share,
                         usual_reviews=med, usual_negative_share=bshare, flags=flags))
    l4n, l4neg = sum(n[-4:]), sum(neg[-4:])
    return dict(snapshot=snap.strftime("%Y-%m-%d"), reviews=len(df), negative=int((~df.voted_up).sum()),
                negative_share=round(float((~df.voted_up).mean()), 4),
                last4=dict(reviews=l4n, negative=l4neg, negative_share=round(l4neg / l4n, 4) if l4n >= SHARE_MIN else None),
                latest=rows[-1], alerts=[r for r in rows if r["flags"]], weeks=rows)


if __name__ == "__main__":
    games = []
    for g in all_games():
        df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet"), columns=COLS)
        games.append(dict(slug=g["slug"], name=g["name"], genre=g["genre"], appid=g["appid"], **weekly(df)))
    out = dict(params=dict(weeks=WEEKS, base_weeks=BASE, volume_times=VOL_X, volume_min=VOL_MIN, share_points=SHARE_PTS, share_min=SHARE_MIN), games=games)
    json.dump(out, open(os.path.join(ROOT, "docs", "data", "weekly.json"), "w"), indent=1)
    with open(os.path.join(ROOT, "data", "public", "weekly_by_game.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["game", "week_starting", "reviews", "negative", "negative_share", "usual_reviews", "usual_negative_share", "flags"])
        for g in games:
            for r in g["weeks"]: w.writerow([g["name"], r["week"], r["reviews"], r["negative"], r["negative_share"], r["usual_reviews"], r["usual_negative_share"], " ".join(r["flags"])])
    for g in games:
        print(f"{g['name'][:30]:30} snap {g['snapshot']} latest {g['latest']['week']} n {g['latest']['reviews']:5} neg {g['latest']['negative_share']} | last4 {g['last4']['reviews']:5} | flagged weeks {len(g['alerts'])} {[a['week'] + ':' + '+'.join(a['flags']) for a in g['alerts'][-2:]]}")
