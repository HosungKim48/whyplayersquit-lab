"""Sum real spend from the per-call records (actual token counts and list-price cost reported with each call)."""
import glob, json, os
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W = os.path.join(ROOT, "data", "work")
def tot(files, step):
    rs = [json.load(open(f)) for f in files]
    return dict(step=step, calls=sum(r.get("calls", 1) for r in rs),
                input_tokens=sum(r.get("input_tokens", 0) + r.get("cache_write_tokens", 0) + r.get("cache_read_tokens", 0) for r in rs),
                output_tokens=sum(r.get("output_tokens", 0) for r in rs), cost_usd=round(sum(r.get("cost_usd", 0) for r in rs), 4))
rows = [tot([f for f in glob.glob(f"{W}/labels/[0-9]*/batch_*.json") if "_other" not in f], "Reason labeling, English reviews (Claude Haiku)"),
        tot(glob.glob(f"{W}/labels/[0-9]*_other/batch_*.json"), "Reason labeling, reviews in all other languages (Claude Haiku)"),
        tot(glob.glob(f"{W}/sublabels/*/batch_*.json"), "Design sub-reasons for Civilization VII (Claude Haiku)"),
        tot(glob.glob(f"{W}/labels/pilot_expensive/*.json") + glob.glob(f"{W}/labels/_debug/*.json"), "Pilot and debugging calls (first pilot loaded unneeded tool definitions; fixed)"),
        tot(glob.glob(f"{W}/quotes/[0-9]*.json") + glob.glob(f"{W}/quotes/v1/*.json"), "Paraphrases for report examples, two rounds (Claude Haiku)")]
out = dict(total_usd=round(sum(r["cost_usd"] for r in rows), 2), budget_usd=30, rows=rows)
json.dump(out, open(os.path.join(ROOT, "docs", "data", "cost.json"), "w"), indent=1)
pd.DataFrame(rows).to_csv(os.path.join(ROOT, "data", "public", "cost_ledger.csv"), index=False)
print(out)
