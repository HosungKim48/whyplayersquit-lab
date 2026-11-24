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
MODEL, BATCH, MIN_WORDS, MAX_CHARS, WORKERS = "haiku", 40, 3, 1200, 6
BUDGET_STOP = 26.0  # USD; hard cap for the project is 30
PROMPT_ML = PROMPT.replace("label_prompt.txt", "label_prompt_multilingual.txt")
state = dict(base=0.0, run=0.0, stop=False)
CODES = {"PERF", "STAB", "CONTENT", "DESIGN", "UI", "MONET", "ONLINE", "SUPPORT", "STORY", "OFFGAME", "OTHER"}
QUITS = {"STOPPED", "WAITING", "NONE"}
NEUTRAL_CWD = tempfile.mkdtemp()
lock = threading.Lock()


def spent():
    return sum(json.load(open(f)).get("cost_usd", 0) for f in glob.glob(os.path.join(ROOT, "data", "work", "*", "*", "*.json")) + glob.glob(os.path.join(ROOT, "data", "work", "quotes", "*.json")))


def clean(t):
    return re.sub(r"\s+", " ", re.sub(r"\[/?[a-z0-9*=#:/. ]+\]", " ", t)).strip()[:MAX_CHARS]


def call(user_text, prompt=None):
    p = subprocess.run(["claude", "-p", "--model", MODEL, "--output-format", "json", "--system-prompt-file", prompt or PROMPT, "--tools", "",
                        # without these the CLI loads ~200k tokens of unrelated connector definitions per call
                        "--strict-mcp-config", "--disable-slash-commands", "--effort", "low", "--no-session-persistence",
                        # skip user-level settings: a personal "play a sound when Claude stops" hook was firing on every call
                        "--setting-sources", "project"],
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


def do_batch(g, k, chunk, lang_set="english"):
    suffix = "" if lang_set == "english" else "_other"
    f = os.path.join(OUT, str(g["appid"]) + suffix, f"batch_{k:05d}.json")
    if os.path.exists(f) or state["stop"]: return 0
    body = f"Game: {g['name']}\n\n" + "\n".join(f"{i+1}. {clean(t)}" for i, t in enumerate(chunk.text))
    d, lab, cost, calls = None, {}, 0.0, 0
    for attempt in range(3):
        try:
            d = call(body, PROMPT if lang_set == "english" else PROMPT_ML); calls += 1; cost += d["total_cost_usd"]  # failed attempts still count as spend
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
    with lock:
        json.dump(rec, open(f, "w")); state["run"] += cost
        if state["base"] + state["run"] > BUDGET_STOP: state["stop"] = True   # no new calls start after this
    return cost


def candidates(g, lang_set="english"):
    """Code filter before any paid call: negative reviews with enough text to carry a reason."""
    df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet"))
    if lang_set == "english":
        pool = df[df.language == "english"]; neg = pool[~pool.voted_up]
        keep = neg[neg.words >= MIN_WORDS].sort_values("rid")       # unchanged rule, so cached English batches stay valid
    else:
        pool = df[df.language != "english"]; neg = pool[~pool.voted_up]
        keep = neg[neg.substantive].sort_values("rid")
    return pool, neg, keep


if __name__ == "__main__":
    # usage: label.py <appid> [english|other] [max_batches]
    appid = int(sys.argv[1]); lang_set = sys.argv[2] if len(sys.argv) > 2 else "english"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    g = next(x for x in GAMES if x["appid"] == appid)
    os.makedirs(os.path.join(OUT, str(appid) + ("" if lang_set == "english" else "_other")), exist_ok=True)
    df, neg, keep = candidates(g, lang_set)
    print(f"{g['name']} [{lang_set}]: all {len(df)} -> negative {len(neg)} -> enough text {len(keep)}", flush=True)
    chunks = [(k, keep.iloc[i:i+BATCH]) for k, i in enumerate(range(0, len(keep), BATCH))][:limit]
    state["base"] = spent()
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = [ex.submit(do_batch, g, k, ch, lang_set) for k, ch in chunks]
        for i, fu in enumerate(cf.as_completed(futs), 1):
            fu.result()
            if i % 50 == 0: print(f"  batches {i}/{len(chunks)}  spend this run ${state['run']:.3f}  total ${state['base']+state['run']:.3f}", flush=True)
    if state["stop"]: print("BUDGET STOP")
    print(f"done. spend this run ${state['run']:.4f}; project total ${spent():.4f}")
