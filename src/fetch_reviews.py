"""Fetch the full English review history for each game from Steam's documented
public endpoint (IUserReviewsService/GetAppReviews) and cache every raw page.

Polite by design: one request at a time, a pause between requests, backoff on
errors, and resume from cache so nothing is ever fetched twice.
Raw pages contain review text and reviewer IDs -> they stay in data/raw (gitignored).
"""
import datetime, gzip, json, os, sys, time
import requests
from games import GAMES

URL = "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/"
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PAUSE = 0.7  # seconds between requests, per stream (4 game streams; responses take ~3s, so about 1 request/second overall)
UA = {"User-Agent": "student-research-script (low rate, cached)"}


def month_windows(release, now):
    """Calendar-month windows [start, end) from the release month to now (UTC)."""
    y, m = int(release[:4]), int(release[5:7]); out = []
    while True:
        start = int(datetime.datetime(y, m, 1, tzinfo=datetime.timezone.utc).timestamp())
        y2, m2 = (y + 1, 1) if m == 12 else (y, m + 1)
        end = int(datetime.datetime(y2, m2, 1, tzinfo=datetime.timezone.utc).timestamp())
        if start >= now: break
        out.append((f"{y}-{m:02d}", start, min(end, now)))
        y, m = y2, m2
    return out


def fetch_game(g):
    """The API only returns a short recent window unless a past date range is given,
    so the full history is walked one calendar month at a time."""
    appid = g["appid"]
    d = os.path.join(RAW, str(appid)); os.makedirs(d, exist_ok=True)
    state_f = os.path.join(d, "state.json")
    state = json.load(open(state_f)) if os.path.exists(state_f) else dict(snapshot=int(time.time()) - 3600, windows={}, n=0)
    for label, start, end in month_windows(g["release"], state["snapshot"]):
        w = state["windows"].setdefault(label, dict(cursor="*", page=0, n=0, done=False))
        while not w["done"]:
            params = dict(appid=appid, languages="english", filter="recent", review_type="all",
                          purchase_type="all", num_per_page=100, filter_offtopic_activity=0,
                          date_range_start=start, date_range_end=end, cursor=w["cursor"])
            for attempt in range(8):
                try:
                    r = requests.get(URL, params=params, headers=UA, timeout=40)
                    if r.status_code == 200:
                        resp = r.json()["response"]; break
                    wait = 30 * (attempt + 1)
                except Exception as e:  # network hiccup
                    wait = 15 * (attempt + 1)
                print(appid, "retry", attempt, "wait", wait, flush=True); time.sleep(wait)
            else:
                print(appid, "giving up for now; rerun to resume", flush=True); return
            revs = resp.get("reviews", [])
            if w["page"] == 0:
                w["total_matching"] = resp.get("total_matching")
                if not os.path.exists(os.path.join(d, "summary.json")):
                    json.dump(dict(fetched_at=int(time.time()), query_summary=resp.get("query_summary")),
                              open(os.path.join(d, "summary.json"), "w"))
            if revs:
                with gzip.open(os.path.join(d, f"{label}_page_{w['page']:05d}.json.gz"), "wt") as f:
                    json.dump(revs, f)
                w["page"] += 1; w["n"] += len(revs); state["n"] += len(revs)
            if not revs or resp.get("cursor") in (None, "", w["cursor"]):
                w["done"] = True
            else:
                w["cursor"] = resp["cursor"]
            json.dump(state, open(state_f, "w"))
            time.sleep(PAUSE)
        print(appid, label, "window done", w["n"], "of", w.get("total_matching"), "| game total", state["n"], flush=True)
    print(appid, "DONE", state["n"], flush=True)


if __name__ == "__main__":
    only = [int(x) for x in sys.argv[1:]]
    for g in GAMES:
        if not only or g["appid"] in only: fetch_game(g)
