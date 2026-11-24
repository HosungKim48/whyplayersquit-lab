"""Combine the analyst's verdicts on the audit samples into a publishable accuracy file (no text, no IDs)."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W = os.path.join(ROOT, "data", "work")
sets, items = [], []
for name, sf, vf in [("English reviews", "audit_sample.json", "audit_verdicts.json"), ("Reviews in other languages", "audit_sample_other.json", "audit_verdicts_other.json"),
                     ("Mixed sample, all languages", "audit_sample_mixed.json", "audit_verdicts_mixed.json")]:
    if not (os.path.exists(os.path.join(W, sf)) and os.path.exists(os.path.join(W, vf))): continue
    sample = json.load(open(os.path.join(W, sf))); verd = json.load(open(os.path.join(W, vf)))  # {"i": [main_ok, quit_ok, better_main_or_null]}
    its = [dict(sample=name, i=s["i"], game=s["game"], language=s.get("language", "english"), model_main=s["main"], model_quit=s["quit"],
                main_ok=bool(verd[str(s["i"])][0]), quit_ok=bool(verd[str(s["i"])][1]), checker_main=verd[str(s["i"])][2]) for s in sample]
    n = len(its); m = sum(x["main_ok"] for x in its); q = sum(x["quit_ok"] for x in its)
    sets.append(dict(name=name, n=n, main_ok=m, quit_ok=q, main_agree=round(m / n, 4), quit_agree=round(q / n, 4))); items += its
n = len(items); m = sum(x["main_ok"] for x in items); q = sum(x["quit_ok"] for x in items)
json.dump(dict(n=n, main_ok=m, quit_ok=q, main_agree=round(m / n, 4), quit_agree=round(q / n, 4), sets=sets,
               checker="Claude Fable 5.2 reading each sampled review (a larger model than the labeler); a second-model check, not a human panel", items=items),
          open(os.path.join(ROOT, "docs", "data", "label_audit.json"), "w"), indent=1)
print(n, m, q, sets)
