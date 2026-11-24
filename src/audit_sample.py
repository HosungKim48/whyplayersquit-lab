"""Draw fixed-seed random samples of labeled reviews for accuracy checks (local files only; they contain text).
Sample 1: English (seed 7). Sample 2: all other languages (seed 13). Plus 50 mixed reviews for the author's own check."""
import json, os
import pandas as pd
from games import GAMES
from analyze import load_labels, ROOT
import label
frames = []
for g in GAMES:
    df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet")).merge(load_labels(g["appid"]), on="rid")
    df["game"] = g["name"]; frames.append(df)
allf = pd.concat(frames).sort_values("rid").reset_index(drop=True)
def dump(sample, path):
    json.dump([dict(i=i, game=r.game, language=r.language, text=label.clean(r.text)[:900], main=r.main, second=r.second, quit=r.quit) for i, r in sample.reset_index(drop=True).iterrows()],
              open(os.path.join(ROOT, "data", "work", path), "w"), indent=1, ensure_ascii=False)
en = allf[allf.language == "english"]; ot = allf[allf.language != "english"]
if not os.path.exists(os.path.join(ROOT, "data", "work", "audit_sample.json")):      # the English sample was drawn and judged in round 1; keep it
    dump(en.groupby("game", group_keys=False).sample(10, random_state=7), "audit_sample.json")
dump(ot.groupby("game", group_keys=False).sample(10, random_state=13), "audit_sample_other.json")
s = allf.sample(50, random_state=11)
s.assign(text=s.text.map(label.clean))[["game", "language", "text", "main", "second", "quit", "hours_at_review", "hours_after_review"]].assign(your_verdict="").to_csv(
    os.path.join(ROOT, "data", "work", "spotcheck_50.csv"), index=False)
dump(s, "audit_sample_mixed.json")
print(len(en), len(ot))
