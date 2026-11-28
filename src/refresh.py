"""Weekly refresh: fetch the newest reviews for every game without re-walking the whole history.

Run on a computer that can reach Steam:
    python3 refresh.py            # all games
    python3 refresh.py 632470     # one app ID
What it does, per game and language set: moves the snapshot to now, re-opens the month windows from
(old snapshot - 31 days) onward, and fetches them again with the normal fetcher. That re-reads every review
that was under 31 days old at the last snapshot, so its "played since the review" number is fresh by the time
the review counts as old enough (30 days) to be judged. Then it rebuilds the local table.
Limit: reviews older than that keep the playtime seen at an earlier snapshot. Run a full fetch to renew those.
Cost: no model calls. About 1 request per 100 new reviews, at the same polite rate as the first fetch.
"""
import datetime, json, os, sys, time
from games import all_games
from fetch_reviews import RAW, LANG_SETS, fetch_game
from build_dataset import build


def reopen(g, suffix, now):
    """Mark the recent month windows as not done so fetch_game walks them again. Returns the labels re-opened."""
    f = os.path.join(RAW, str(g["appid"]) + suffix, "state.json")
    if not os.path.exists(f): return None
    st = json.load(open(f)); since = datetime.datetime.fromtimestamp(st["snapshot"] - 31 * 86400, datetime.timezone.utc).strftime("%Y-%m")
    again = [k for k in st["windows"] if k >= since]
    for k in again:
        st["n"] -= st["windows"][k].get("n", 0); st["windows"][k] = dict(cursor="*", page=0, n=0, done=False)
    st["snapshot"] = now; json.dump(st, open(f, "w"))
    return again


if __name__ == "__main__":
    only = [int(x) for x in sys.argv[1:]]; now = int(time.time()) - 3600
    for g in all_games():
        if only and g["appid"] not in only: continue
        for lang_set, (_, suffix) in LANG_SETS.items():
            again = reopen(g, suffix, now)
            if again is None: print(g["name"], lang_set, "has no cache yet; run the full fetch first"); continue
            print(g["name"], lang_set, "re-opening", again, flush=True); fetch_game(g, lang_set)
        r = build(g); print(g["name"], "table rebuilt:", r["unique_reviews"], "reviews", "(complete)" if r["all_windows_done"] else "(INCOMPLETE, run again)", flush=True)
