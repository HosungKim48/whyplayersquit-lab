"""Competitor benchmark: where each game sits against similar games and against every game in the set.

Input : docs/data/after_review_all.json, docs/data/fans_all.json, docs/data/weekly.json (all written by code, no text, no IDs)
Output: docs/data/benchmark.json, data/public/benchmark_by_game.csv
For every measure: the game's value, its rank among all games (1 = lowest value), the median of all games,
and the median of its peer group. Peer groups are broad genre families set from the genre label in games.py.
Ranks describe this set of games only. They are not a ranking of all Steam games. No model calls, no cost.
"""
import csv, json, os, statistics
from analyze import ROOT

FAMILIES = [("Shooters", ("shooter",)), ("RPGs", ("rpg",)),
            ("Strategy, builders & management", ("strategy", "builder", "4x", "simulation", "management")),
            ("Action & adventure", ())]   # everything else
MEASURES = [  # key, label, plain meaning
    ("negative_share", "Negative reviews", "share of all reviews that are not recommended"),
    ("critics_stopped", "Critics who stopped", "not-recommended reviewers who logged under 1 more hour"),
    ("fans_stopped", "Fans who stopped", "recommended reviewers who logged under 1 more hour"),
    ("fans_kept_10h", "Fans who played 10+ more hours", "recommended reviewers who logged 10 or more hours after reviewing"),
    ("fan_review_hours", "Hours played when fans review", "median hours played when a recommended review was written"),
]


def family(genre):
    g = genre.lower()
    return next(name for name, keys in FAMILIES if not keys or any(k in g for k in keys))


if __name__ == "__main__":
    D = os.path.join(ROOT, "docs", "data"); L = lambda n: json.load(open(os.path.join(D, n)))
    ar = {g["slug"]: g for g in L("after_review_all.json")["games"]}; fans = {g["slug"]: g for g in L("fans_all.json")["games"]}; wk = L("weekly.json")["games"]
    rows = []
    for w in wk:
        a, f = ar[w["slug"]], fans[w["slug"]]
        rows.append(dict(slug=w["slug"], name=w["name"], genre=w["genre"], family=family(w["genre"]), reviews=w["reviews"],
                         values=dict(negative_share=w["negative_share"], critics_stopped=a["negative"]["walk_rate"], fans_stopped=a["positive"]["walk_rate"],
                                     fans_kept_10h=a["positive"]["kept_10h_rate"], fan_review_hours=f["recommended"]["median"])))
    med = lambda xs: round(statistics.median(xs), 4) if xs else None
    for r in rows:
        peers = [p for p in rows if p["family"] == r["family"] and p["slug"] != r["slug"]]
        r["peers"] = [p["name"] for p in peers]; r["measures"] = []
        for key, label, meaning in MEASURES:
            v = r["values"][key]; allv = sorted(p["values"][key] for p in rows if p["values"][key] is not None)
            pv = [p["values"][key] for p in peers if p["values"][key] is not None]
            r["measures"].append(dict(key=key, label=label, meaning=meaning, value=v, rank=None if v is None else allv.index(v) + 1, of=len(allv),
                                      all_median=med(allv), peer_median=med(pv), all_min=allv[0], all_max=allv[-1]))
    for r in rows: del r["values"]
    out = dict(families=[f[0] for f in FAMILIES], measures=[dict(key=k, label=l, meaning=m) for k, l, m in MEASURES], games=rows)
    json.dump(out, open(os.path.join(D, "benchmark.json"), "w"), indent=1)
    with open(os.path.join(ROOT, "data", "public", "benchmark_by_game.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["game", "peer_group", "measure", "value", "rank_lowest_first", "of_games", "peer_median", "all_games_median"])
        for r in rows:
            for m in r["measures"]: w.writerow([r["name"], r["family"], m["label"], m["value"], m["rank"], m["of"], m["peer_median"], m["all_median"]])
    from collections import Counter
    print(Counter(r["family"] for r in rows))
    for r in rows: print(f"{r['name'][:28]:28} {r['family']:20} " + " ".join(f"{m['value']}(#{m['rank']})" for m in r["measures"]))
