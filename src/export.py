"""Export: one JSON file and two CSV files per game, plus an index. Static files, served by the site as a read-only API.

Input : docs/data/weekly.json, benchmark.json, after_review_all.json, fans_all.json, overview.json (numbers only)
Output: docs/api/v1/index.json, docs/api/v1/games/<slug>.json, docs/export/<slug>_weekly.csv, docs/export/<slug>_summary.csv
"""
import csv, json, os
from analyze import ROOT, REASONS

if __name__ == "__main__":
    D = os.path.join(ROOT, "docs", "data"); L = lambda n: json.load(open(os.path.join(D, n)))
    wk = L("weekly.json"); bm = {g["slug"]: g for g in L("benchmark.json")["games"]}
    ar = {g["slug"]: g for g in L("after_review_all.json")["games"]}; fans = {g["slug"]: g for g in L("fans_all.json")["games"]}
    ov = {o["slug"]: o for o in L("overview.json")}
    api = os.path.join(ROOT, "docs", "api", "v1"); ex = os.path.join(ROOT, "docs", "export")
    os.makedirs(os.path.join(api, "games"), exist_ok=True); os.makedirs(ex, exist_ok=True)
    index = []
    for g in wk["games"]:
        s = g["slug"]; a, f, b, o = ar[s], fans[s], bm[s], ov.get(s)
        doc = dict(slug=s, name=g["name"], genre=g["genre"], steam_appid=g["appid"], snapshot=g["snapshot"], reviews=g["reviews"], negative_share=g["negative_share"],
                   after_review=dict(recommended=a["positive"], not_recommended=a["negative"], by_hours_at_review=a["by_hours"]),
                   review_timing=dict(recommended={k: f["recommended"][k] for k in ("n", "p25", "median", "p75")}, not_recommended={k: f["not_recommended"][k] for k in ("n", "p25", "median", "p75")}),
                   benchmark=dict(peer_group=b["family"], peers=b["peers"], measures=b["measures"]),
                   complaints=None if not o else [dict(code=c, label=REASONS[c], share=o["reason_shares"][c], stopped_rate=o["reason_walk"].get(c), against_game_average=o["reason_flags"].get(c)) for c in o["reason_shares"]],
                   weekly=g["weeks"], flagged_weeks=g["alerts"])
        json.dump(doc, open(os.path.join(api, "games", s + ".json"), "w"), indent=1)
        index.append(dict(slug=s, name=g["name"], genre=g["genre"], snapshot=g["snapshot"], reviews=g["reviews"], has_complaints=bool(o), url=f"games/{s}.json"))
        with open(os.path.join(ex, s + "_weekly.csv"), "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["week_starting", "reviews", "negative", "negative_share", "usual_reviews", "usual_negative_share", "flags"])
            for r in g["weeks"]: w.writerow([r["week"], r["reviews"], r["negative"], r["negative_share"], r["usual_reviews"], r["usual_negative_share"], " ".join(r["flags"])])
        with open(os.path.join(ex, s + "_summary.csv"), "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["section", "group", "measure", "value"])
            for m in b["measures"]:
                for k in ("value", "rank", "peer_median", "all_median"): w.writerow(["benchmark", m["label"], k, m[k]])
            for r in a["by_hours"]:
                for v, lab in (("positive", "recommended"), ("negative", "not recommended")):
                    w.writerow(["after_review", f"{r['bucket']} / {lab}", "reviews", r[v]["n"]]); w.writerow(["after_review", f"{r['bucket']} / {lab}", "stopped_rate", r[v].get("walk_rate")])
            for c in doc["complaints"] or []: w.writerow(["complaints", c["label"], "share", c["share"]]); w.writerow(["complaints", c["label"], "stopped_rate", c["stopped_rate"]])
    json.dump(dict(version="v1", note="Read-only static files. Numbers only: no review text, no reviewer or review IDs.", games=index), open(os.path.join(api, "index.json"), "w"), indent=1)
    print("exported", len(index), "games")
