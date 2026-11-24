"""Draw fixed-seed random samples of labeled reviews for accuracy checks (local files only; they contain text)."""
import json, os
import pandas as pd
from games import GAMES
from analyze import load_labels, ROOT
import label
frames = []
for g in GAMES:
    df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet")).merge(load_labels(g["appid"]), on="rid")
    df["game"] = g["name"]; frames.append(df)
allf = pd.concat(frames)
a = allf.groupby("game", group_keys=False).sample(10, random_state=7).reset_index(drop=True)   # 60 for the analyst's audit
json.dump([dict(i=i, game=r.game, text=label.clean(r.text)[:900], main=r.main, second=r.second, quit=r.quit) for i, r in a.iterrows()],
          open(os.path.join(ROOT, "data", "work", "audit_sample.json"), "w"), indent=1)
s = allf.drop(a.index, errors="ignore").sample(50, random_state=11)                               # 50 for Hosung's own spot check
s.assign(text=s.text.map(label.clean))[["game", "text", "main", "second", "quit", "hours_at_review", "hours_after_review"]].assign(your_verdict="").to_csv(
    os.path.join(ROOT, "data", "work", "spotcheck_50.csv"), index=False)
print(len(a), len(s))
