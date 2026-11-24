"""Turn cached raw pages into one local table per game (data/work, never published).

Adds the behavioural fields used across the study. Text and reviewer IDs stay local.
"""
import glob, gzip, json, os, sys
import pandas as pd
from games import GAMES

ROOT = os.path.join(os.path.dirname(__file__), "..")


NO_SPACE_LANGS = {"schinese", "tchinese", "japanese", "koreana", "thai"}  # word counts by spaces do not work here


def build(g):
    rows, raw_n, states = {}, 0, {}
    for suffix in ("", "_other"):   # English cache, then all other languages
        d = os.path.join(ROOT, "data", "raw", str(g["appid"]) + suffix)
        if not os.path.exists(os.path.join(d, "state.json")): continue
        state = json.load(open(os.path.join(d, "state.json"))); states[suffix or "english"] = state
        for f in sorted(glob.glob(os.path.join(d, "*_page_*.json.gz"))):
            for r in json.load(gzip.open(f)):
                raw_n += 1
                a = r.get("author", {})
                rows[r["recommendationid"]] = dict(
                    rid=r["recommendationid"], text=r.get("review", "") or "", language=r.get("language", "unknown"),
                    snapshot=state["snapshot"],
                    created=r["timestamp_created"], updated=r.get("timestamp_updated", r["timestamp_created"]),
                    voted_up=bool(r["voted_up"]), votes_up=r.get("votes_up", 0),
                    pt_review=a.get("playtime_at_review"), pt_forever=a.get("playtime_forever"),
                    pt_2w=a.get("playtime_last_two_weeks"), last_played=a.get("last_played"),
                    steam_purchase=r.get("steam_purchase"), free=r.get("received_for_free"),
                    early_access=r.get("written_during_early_access"), refunded=r.get("refunded"),
                    deck=r.get("primarily_steam_deck"))
    df = pd.DataFrame(rows.values())
    df["appid"] = g["appid"]
    df["month"] = pd.to_datetime(df.created, unit="s", utc=True).dt.strftime("%Y-%m")
    df["hours_at_review"] = df.pt_review / 60
    df["hours_after_review"] = (df.pt_forever - df.pt_review) / 60
    df["days_since_review"] = (df.snapshot - df.created) / 86400
    df["days_played_after"] = (df.last_played - df.created) / 86400
    df["words"] = df.text.str.split().str.len()
    chars = df.text.str.replace(r"\s", "", regex=True).str.len()
    # enough text to carry a reason: 3+ words, or 4+ characters in languages written without spaces
    df["substantive"] = (df.words >= 3) | (df.language.isin(NO_SPACE_LANGS) & (chars >= 4))
    df["edited"] = df.updated > df.created + 3600
    df.to_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet"))
    api = {k: sum((w.get("total_matching") or 0) for w in st["windows"].values()) for k, st in states.items()}
    return dict(appid=g["appid"], name=g["name"],
                snapshot_english_utc=pd.to_datetime(states["english"]["snapshot"], unit="s", utc=True).isoformat(),
                snapshot_other_utc=pd.to_datetime(states["_other"]["snapshot"], unit="s", utc=True).isoformat() if "_other" in states else None,
                raw_rows=raw_n, unique_reviews=len(df), english=int((df.language == "english").sum()), other_languages=int((df.language != "english").sum()),
                api_reported_english=api.get("english"), api_reported_other=api.get("_other"),
                all_windows_done=all(w["done"] for st in states.values() for w in st["windows"].values()))


if __name__ == "__main__":
    only = [int(x) for x in sys.argv[1:]]
    out = [build(g) for g in GAMES if (not only or g["appid"] in only) and os.path.exists(os.path.join(ROOT, "data", "raw", str(g["appid"]), "state.json"))]
    print(pd.DataFrame(out).to_string())
    if not only: pd.DataFrame(out).to_csv(os.path.join(ROOT, "data", "public", "fetch_coverage.csv"), index=False)
