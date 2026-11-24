"""Second-level labels for ONE game: which design choice do Civilization VII's "gameplay & design" reviews name?
Same cached, cost-recorded batch pattern as label.py. Output: data/work/sublabels/1295660/batch_*.json"""
import concurrent.futures as cf, json, os, re, sys
import pandas as pd
import label
from analyze import load_labels

APPID = 1295660
CODES = {"AGES", "CIVSWITCH", "LEGACY", "SIMPLE", "AI", "CITY", "PACING", "MAPS", "NOTCIV", "OTHERD"}
OUT = os.path.join(label.ROOT, "data", "work", "sublabels", str(APPID)); os.makedirs(OUT, exist_ok=True)
PROMPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sublabel_prompt.txt")


def do(k, chunk):
    f = os.path.join(OUT, f"batch_{k:05d}.json")
    if os.path.exists(f) or label.state["stop"]: return
    body = "\n".join(f"{i+1}. {label.clean(t)}" for i, t in enumerate(chunk.text))
    d, lab, cost, calls = None, {}, 0.0, 0
    for _ in range(3):
        try:
            d = label.call(body, PROMPT); calls += 1; cost += d["total_cost_usd"]
            lab = {int(m[1]): m[2] for m in re.finditer(r"(?m)^\s*(\d+)\s*\|\s*([A-Z]+)", d["result"]) if m[2] in CODES and 1 <= int(m[1]) <= len(chunk)}
            if len(lab) >= 0.9 * len(chunk): break
        except Exception:
            pass
    if not d: return
    u = d["usage"]
    with label.lock:
        json.dump(dict(appid=APPID, batch=k, n=len(chunk), cost_usd=cost, calls=calls, input_tokens=u["input_tokens"], cache_write_tokens=u["cache_creation_input_tokens"],
                       cache_read_tokens=u["cache_read_input_tokens"], output_tokens=u["output_tokens"],
                       labels=[dict(rid=rid, sub=lab[i+1]) for i, rid in enumerate(chunk.rid) if i+1 in lab]), open(f, "w"))
        label.state["run"] += cost
        if label.state["base"] + label.state["run"] > label.BUDGET_STOP: label.state["stop"] = True


if __name__ == "__main__":
    df = pd.read_parquet(os.path.join(label.ROOT, "data", "work", f"reviews_{APPID}.parquet")).merge(load_labels(APPID), on="rid")
    keep = df[df.main == "DESIGN"].sort_values("rid")
    chunks = [(k, keep.iloc[i:i+label.BATCH]) for k, i in enumerate(range(0, len(keep), label.BATCH))][:int(sys.argv[1]) if len(sys.argv) > 1 else None]
    print("design-complaint reviews", len(keep), "batches", len(chunks), flush=True)
    label.state["base"] = label.spent()
    with cf.ThreadPoolExecutor(6) as ex: list(ex.map(lambda kc: do(*kc), chunks))
    print(f"done. spend this run ${label.state['run']:.4f}; project total ${label.spent():.4f}", "BUDGET STOP" if label.state["stop"] else "")
