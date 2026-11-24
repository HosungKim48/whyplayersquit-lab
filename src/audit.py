"""Combine the analyst's verdicts on the audit sample into a publishable accuracy file (no text, no IDs)."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sample = json.load(open(os.path.join(ROOT, "data", "work", "audit_sample.json")))
verd = json.load(open(os.path.join(ROOT, "data", "work", "audit_verdicts.json")))  # {"i": [main_ok, quit_ok, better_main_or_null]}
items = []
for s in sample:
    v = verd[str(s["i"])]
    items.append(dict(i=s["i"], game=s["game"], model_main=s["main"], model_quit=s["quit"], main_ok=bool(v[0]), quit_ok=bool(v[1]), checker_main=v[2] if len(v) > 2 else None))
n = len(items); m = sum(x["main_ok"] for x in items); q = sum(x["quit_ok"] for x in items)
json.dump(dict(n=n, main_ok=m, quit_ok=q, main_agree=round(m / n, 4), quit_agree=round(q / n, 4),
               checker="Claude (the AI analyst that built this project) reading each sampled review; not a human panel", items=items),
          open(os.path.join(ROOT, "docs", "data", "label_audit.json"), "w"), indent=1)
print(n, m, q)
