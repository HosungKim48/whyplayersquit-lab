"""Label negative reviews with a small model (Claude Haiku via the `claude -p` CLI).

Stage 1 (code, free): keep negative reviews with at least MIN_WORDS words.
Stage 2 (paid): batches of BATCH reviews -> one line of codes per review.
Every call's real token counts and cost are written next to its output, and the
run stops before the budget cap is reached. Results are cached, so reruns are free.
"""
import concurrent.futures as cf, glob, json, os, re, subprocess, sys, tempfile, threading
import pandas as pd
from games import GAMES

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "work", "labels")
PROMPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "label_prompt.txt")
MODEL, BATCH, MIN_WORDS, MAX_CHARS, WORKERS = "haiku", 40, 3, 1200, 12
BUDGET_STOP = 22.0  # USD; hard cap for the project is 30
CODES = {"PERF", "STAB", "CONTENT", "DESIGN", "UI", "MONET", "ONLINE", "SUPPORT", "STORY", "OFFGAME", "OTHER"}
QUITS = {"STOPPED", "WAITING", "NONE"}
NEUTRAL_CWD = tempfile.mkdtemp()
lock = threading.Lock()


def spent():
    return sum(json.load(open(f)).get("cost_usd", 0) for f in glob.glob(os.path.join(ROOT, "data", "work", "*", "*", "*.json")) + glob.glob(os.path.join(ROOT, "data", "work", "quotes", "*.json")))


def clean(t):
    return re.sub(r"\s+", " ", re.sub(r"\[/?[a-z0-9*=#:/. ]+\]", " ", t)).strip()[:MAX_CHARS]


def call(user_text):
    p = subprocess.run(["claude", "-p", "--model", MODEL, "--output-format", "json", "--system-prompt-file", PROMPT, "--tools", "",
                        # without these the CLI loads ~200k tokens of unrelated connector definitions per call
                        "--strict-mcp-config", "--disable-slash-commands", "--effort", "low", "--no-session-persistence"],
                       input=user_text, capture_output=True, text=True, timeout=300, cwd=NEUTRAL_CWD,
                       env={**os.environ, "MAX_THINKING_TOKENS": "0"})  # plain classification; no paid reasoning tokens
    d = json.loads(p.stdout)
    if d.get("is_error"): raise RuntimeError(str(d.get("result"))[:200])
    return d


def parse(result, n):
    out = {}
    for line in result.splitlines():
        m = re.match(r"\s*(\d+)\s*\|\s*([A-Z]+)\s*\|\s*([A-Z]+)\s*\|\s*([A-Z]+)", line)
        if m and 1 <= int(m[1]) <= n and m[2] in CODES and m[4] in QUITS:
            out[int(m[1])] = (m[2], m[3] if m[3] in CODES and m[3] != m[2] else "NONE", m[4])
    return out


def do_batch(g, k, chunk):
    f = os.path.join(OUT, str(g["appid"]), f"batch_{k:05d}.json")
    if os.path.exists(f): return 0
    body = f"Game: {g['name']}\n\n" + "\n".join(f"{i+1}. {clean(t)}" for i, t in enumerate(chunk.text))
    d, lab, cost, calls = None, {}, 0.0, 0
    for attempt in range(3):
        try:
            d = call(body); calls += 1; cost += d["total_cost_usd"]  # failed attempts still count as spend
            lab = parse(d["result"], len(chunk))
            if len(lab) >= 0.9 * len(chunk): break
        except Exception as e:
            pass
    if not d: return 0
    u = d["usage"]
    rec = dict(appid=g["appid"], batch=k, n=len(chunk), cost_usd=cost, calls=calls, model=list(d.get("modelUsage", {}))[:1],
               input_tokens=u["input_tokens"], cache_write_tokens=u["cache_creation_input_tokens"],
               cache_read_tokens=u["cache_read_input_tokens"], output_tokens=u["output_tokens"],
               labels=[dict(rid=rid, main=lab[i+1][0], second=lab[i+1][1], quit=lab[i+1][2]) for i, rid in enumerate(chunk.rid) if i+1 in lab])
    with lock: json.dump(rec, open(f, "w"))
    return cost


def candidates(g):
    df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet"))
    neg = df[~df.voted_up]
    keep = neg[neg.words >= MIN_WORDS].sort_values("rid")
    return df, neg, keep


if __name__ == "__main__":
    appid, limit = int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else None
    g = next(x for x in GAMES if x["appid"] == appid)
    os.makedirs(os.path.join(OUT, str(appid)), exist_ok=True)
    df, neg, keep = candidates(g)
    print(f"{g['name']}: all {len(df)} -> negative {len(neg)} -> with >= {MIN_WORDS} words {len(keep)}", flush=True)
    chunks = [(k, keep.iloc[i:i+BATCH]) for k, i in enumerate(range(0, len(keep), BATCH))][:limit]
    base = spent(); run = 0.0
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = []
        for k, ch in chunks:
            futs.append(ex.submit(do_batch, g, k, ch))
            if len(futs) % 40 == 0:  # budget check uses finished + in-flight calls
                run = sum(x.result() for x in futs)
                print(f"  batches {len(futs)}/{len(chunks)}  spend this run ${run:.3f}  total ${base+run:.3f}", flush=True)
                if base + run > BUDGET_STOP: print("BUDGET STOP"); break
        run = sum(x.result() for x in futs)
    print(f"done. spend this run ${run:.4f}; project total ${spent():.4f}")
