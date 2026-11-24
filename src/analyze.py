"""Compute every number shown on the site.

Input : data/work/reviews_<appid>.parquet (local), data/work/labels/<appid>/*.json (local),
        data/raw/news/<appid>.json (official announcements)
Output: docs/data/<slug>.json  (one file per game; the site is rendered only from these)
        docs/data/overview.json, data/public/*.csv (same numbers as flat tables)
No review text and no reviewer or review IDs are written to any output.
"""
import datetime as dt, glob, json, math, os, re
import numpy as np
import pandas as pd
from games import GAMES

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUB = os.path.join(ROOT, "data", "public"); DOCS = os.path.join(ROOT, "docs", "data")
os.makedirs(PUB, exist_ok=True); os.makedirs(DOCS, exist_ok=True)

MATURE_DAYS = 30        # behaviour is only judged for reviews at least this old
WALK_HOURS = 1.0        # "walked away" = less than this much play logged after the review
MIN_CELL = 30           # do not show a rate computed on fewer reviews than this
BUCKETS = [(0, 2, "Under 2 h"), (2, 10, "2–10 h"), (10, 50, "10–50 h"), (50, 200, "50–200 h"), (200, 1e9, "200 h+")]
REASONS = {
    "PERF": "Performance", "STAB": "Crashes & bugs", "CONTENT": "Not enough content", "DESIGN": "Gameplay & design choices",
    "UI": "Interface & controls", "MONET": "Price & monetization", "ONLINE": "Online, accounts & DRM",
    "SUPPORT": "Post-launch support", "STORY": "Story & writing", "OFFGAME": "Off-game topics", "OTHER": "No clear reason",
}
LANG_NAMES = {"english": "English", "schinese": "Chinese (Simplified)", "tchinese": "Chinese (Traditional)", "japanese": "Japanese", "koreana": "Korean",
              "russian": "Russian", "german": "German", "french": "French", "spanish": "Spanish (Spain)", "latam": "Spanish (Latin America)",
              "brazilian": "Portuguese (Brazil)", "portuguese": "Portuguese (Portugal)", "polish": "Polish", "turkish": "Turkish", "italian": "Italian",
              "thai": "Thai", "ukrainian": "Ukrainian", "czech": "Czech", "dutch": "Dutch", "swedish": "Swedish", "hungarian": "Hungarian",
              "danish": "Danish", "finnish": "Finnish", "norwegian": "Norwegian", "romanian": "Romanian", "bulgarian": "Bulgarian", "greek": "Greek",
              "vietnamese": "Vietnamese", "indonesian": "Indonesian", "arabic": "Arabic"}
SUBREASONS = {"AGES": "The Ages system (era splits, resets at transitions)", "CIVSWITCH": "Switching civilizations; leaders not tied to a civilization",
              "LEGACY": "Legacy paths and victory goals feel like a checklist", "SIMPLE": "Oversimplified, less depth",
              "AI": "AI, diplomacy, combat and balance", "CITY": "City, town and settlement management", "PACING": "Game length and pacing",
              "MAPS": "Maps and exploration", "NOTCIV": "\"Doesn't feel like Civilization\" (no mechanic named)", "OTHERD": "Other or unspecified design complaint"}
MIN_LANG = 300          # a language gets its own row in a game's report at this many reviews
PATCH_RE = re.compile(r"\b(patch|hotfix|hot fix|update|title update|ver\.|version|v\d+\.\d+|\d+\.\d+\.\d+|changelog|release notes)\b", re.I)


def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


def rate(mask, base):
    """share of rows in `base` (boolean frame index) where mask is true -> dict with n, k, rate, ci"""
    n = int(base.sum()); k = int((mask & base).sum())
    lo, hi = wilson(k, n)
    return dict(n=n, k=k, rate=round(k / n, 4) if n else None, lo=lo, hi=hi, shown=n >= MIN_CELL)


def behaviour(df):
    m = df[df.days_since_review >= MATURE_DAYS]
    n = len(m)
    if n == 0: return dict(n=0)
    w = int((m.hours_after_review < WALK_HOURS).sum()); lo, hi = wilson(w, n)
    return dict(n=n, walked_away=w, walk_rate=round(w / n, 4), walk_lo=lo, walk_hi=hi,
                kept_10h_rate=round(float((m.hours_after_review >= 10).mean()), 4),
                median_hours_after=round(float(m.hours_after_review.median()), 2),
                refunded_rate=round(float(m.refunded.fillna(False).astype(bool).mean()), 4),
                active_now_rate=round(float((m.pt_2w > 0).mean()), 4), shown=n >= MIN_CELL)


def load_labels(appid):
    rows = []
    for sub in (str(appid), str(appid) + "_other"):
        for f in glob.glob(os.path.join(ROOT, "data", "work", "labels", sub, "batch_*.json")):
            rows += json.load(open(f))["labels"]
    return pd.DataFrame(rows).drop_duplicates("rid") if rows else pd.DataFrame(columns=["rid", "main", "second", "quit"])


def announcements(appid):
    items = json.load(open(os.path.join(ROOT, "data", "raw", "news", f"{appid}.json")))["appnews"]["newsitems"]
    out = [dict(date=dt.datetime.fromtimestamp(i["date"], dt.timezone.utc).strftime("%Y-%m-%d"), ts=i["date"], title=i["title"].strip(),
                is_patch=bool(PATCH_RE.search(i["title"])) or "patchnotes" in (i.get("tags") or [])) for i in items]
    return sorted(out, key=lambda x: x["ts"])


POOL = []   # labeled negative reviews of every game, kept for the pooled model


def model_frame(df, L, mature, g):
    """Rows and columns for the walk-away model: labeled negative reviews at least MATURE_DAYS old."""
    d = df[L & mature].copy()
    d["y"] = (d.hours_after_review < WALK_HOURS).astype(int)
    lc = d.language.value_counts()
    d["langg"] = d.language.where(d.language.map(lc) >= MIN_LANG, "other_small")
    days = (d.created - pd.Timestamp(g["release"], tz="UTC").timestamp()) / 86400
    d["age"] = pd.cut(days, [-1e9, 30, 180, 1e9], labels=["first_30_days", "days_31_180", "after_180_days"]).astype(str)
    d["bucket"] = d.bucket.astype(str); d["edited"] = d.edited.astype(int); d["game"] = g["slug"]
    return d[["y", "main", "bucket", "langg", "age", "edited", "game"]]


def walk_model(d, pooled=False):
    """Logistic regression: walked away ~ main complaint + hours band + review language + review timing + edited (+ game).
    Returns odds ratios for each complaint against the reference complaint (crashes & bugs)."""
    import statsmodels.formula.api as smf
    d = d.copy(); n = d.main.value_counts()
    d["main"] = d.main.where(d.main.map(n) >= 100, "RARE")
    ref = "STAB" if n.get("STAB", 0) >= 100 else n.index[0]
    f = f"y ~ C(main, Treatment('{ref}')) + C(bucket) + C(langg) + C(age) + edited" + (" + C(game)" if pooled else "")
    try:
        m = smf.logit(f, d).fit(disp=0, maxiter=200)
    except Exception as e:
        return dict(ok=False, error=str(e)[:120])
    ci = m.conf_int(); rows = []
    for code in n.index:
        key = f"C(main, Treatment('{ref}'))[T.{code}]"
        if key in m.params.index:
            rows.append(dict(code=code, reason=REASONS[code], n=int(n[code]), odds_ratio=round(float(np.exp(m.params[key])), 3),
                             lo=round(float(np.exp(ci.loc[key, 0])), 3), hi=round(float(np.exp(ci.loc[key, 1])), 3), p=float(f"{m.pvalues[key]:.2g}")))
    ctrl = {}
    for key, lab in [("C(bucket)[T.Under 2 h]", "under_2h_vs_10_50h"), ("C(age)[T.first_30_days]", "first_30_days_vs_after_180"), ("edited", "edited_review")]:
        if key in m.params.index: ctrl[lab] = round(float(np.exp(m.params[key])), 3)
    return dict(ok=True, n=int(len(d)), reference=ref, reference_reason=REASONS[ref], pseudo_r2=round(float(m.prsquared), 4),
                formula=f, rows=sorted(rows, key=lambda r: -r["odds_ratio"]), control_odds_ratios=ctrl)


def sensitivity(df, L, mature, base_rows):
    """Does the picture change if 'walked away' means under 2 or under 5 more hours instead of under 1?"""
    from scipy.stats import spearmanr
    neg = ~df.voted_up; out = []
    big = [r["code"] for r in base_rows if r["walk_n"] >= 100 and r["code"] != "OTHER"]
    base = {r["code"]: r["vs_game_average"] for r in base_rows}
    ref_rates = None
    for h in (1, 2, 5):
        w = df.hours_after_review < h; avg = float(w[neg & mature].mean()); rates, same = {}, 0
        for c in big:
            msk = L & mature & (df.main == c); k, n = int(w[msk].sum()), int(msk.sum()); lo, hi = wilson(k, n)
            rates[c] = k / n
            flag = "higher" if lo > avg else "lower" if hi < avg else "similar"
            same += flag == base[c]
        if ref_rates is None: ref_rates = rates
        rho = float(spearmanr([ref_rates[c] for c in big], [rates[c] for c in big])[0]) if len(big) > 2 else None
        out.append(dict(hours=h, negative_walk_rate=round(avg, 4), complaint_groups=len(big), same_verdict_as_1h=same,
                        rank_correlation_with_1h=round(rho, 3) if rho is not None else None))
    return out


def analyze(g):
    appid = g["appid"]
    df = pd.read_parquet(os.path.join(ROOT, "data", "work", f"reviews_{appid}.parquet"))
    states = [json.load(open(os.path.join(ROOT, "data", "raw", str(appid) + sfx, "state.json"))) for sfx in ("", "_other") if os.path.exists(os.path.join(ROOT, "data", "raw", str(appid) + sfx, "state.json"))]
    lab = load_labels(appid)
    df = df.merge(lab, on="rid", how="left")
    df["bucket"] = pd.cut(df.hours_at_review, [b[0] for b in BUCKETS] + [1e9], labels=[b[2] for b in BUCKETS], right=False)
    neg, pos = df[~df.voted_up], df[df.voted_up]
    labeled = neg[neg.main.notna()]
    mature = df.days_since_review >= MATURE_DAYS
    walked = df.hours_after_review < WALK_HOURS
    ann = announcements(appid)

    out = dict(appid=appid, slug=g["slug"], name=g["name"], genre=g["genre"], release=g["release"],
               snapshot=dt.datetime.fromtimestamp(max(st["snapshot"] for st in states), dt.timezone.utc).strftime("%Y-%m-%d"),
               snapshot_english=dt.datetime.fromtimestamp(states[0]["snapshot"], dt.timezone.utc).strftime("%Y-%m-%d"),
               params=dict(mature_days=MATURE_DAYS, walk_hours=WALK_HOURS, min_cell=MIN_CELL))

    # --- funnel / coverage
    api_total = sum((w.get("total_matching") or 0) for st in states for w in st["windows"].values())
    life = pd.read_csv(os.path.join(PUB, "steam_lifetime_summary.csv")).set_index("appid").loc[appid]
    out["funnel"] = dict(steam_summary_total=int(life.steam_summary_total), api_reported_reviews=api_total, english=int((df.language == "english").sum()), other_languages=int((df.language != "english").sum()), languages=int(df.language.nunique()), fetched_unique=len(df), negative=len(neg),
                         negative_enough_text=int(neg.substantive.sum()), labeled=len(labeled),
                         first_review=df.month.min(), last_review=df.month.max())
    out["overview"] = dict(reviews=len(df), negative=len(neg), negative_share=round(len(neg) / len(df), 4),
                           median_hours_at_negative_review=round(float(neg.hours_at_review.median()), 1),
                           median_hours_at_positive_review=round(float(pos.hours_at_review.median()), 1))

    # --- behaviour after the review
    out["behaviour"] = dict(negative=behaviour(neg), positive=behaviour(pos),
                            negative_unedited=behaviour(neg[~neg.edited]), negative_90d=None)
    old = neg[neg.days_since_review >= 90]
    out["behaviour"]["negative_90d"] = dict(n=len(old), walk_rate=round(float((old.hours_after_review < WALK_HOURS).mean()), 4) if len(old) else None)

    # --- when: hours played at the time of the review
    rows = []
    for lo, hi, name in BUCKETS:
        b = df.bucket == name
        r = rate(walked, b & ~df.voted_up & mature)
        rows.append(dict(bucket=name, reviews=int(b.sum()), negative=int((b & ~df.voted_up).sum()),
                         negative_share_in_bucket=round(float((~df.voted_up)[b].mean()), 4) if b.sum() else None,
                         share_of_all_negative=round(float((b & ~df.voted_up).sum() / len(neg)), 4),
                         neg_walk_n=r["n"], neg_walk_rate=r["rate"] if r["shown"] else None))
    out["playtime"] = rows

    # --- why: reasons
    base_walk = out["behaviour"]["negative"].get("walk_rate")
    L = df.main.notna() & ~df.voted_up
    out["behaviour"]["negative_labeled"] = behaviour(df[L])
    rows = []
    for code, name in REASONS.items():
        is_main = L & (df.main == code); any_m = L & ((df.main == code) | (df.second == code))
        r = rate(walked, is_main & mature)
        st = rate(df.quit == "STOPPED", is_main)
        flag = "n/a"
        if r["shown"] and base_walk is not None:
            flag = "higher" if r["lo"] > base_walk else "lower" if r["hi"] < base_walk else "similar"
        # same rate re-weighted so every reason has the game's overall mix of hours-at-review (direct standardization)
        adj, ok_adj = 0.0, r["shown"]
        for _, _, bname in BUCKETS:
            wgt = float((L & mature & (df.bucket == bname)).sum() / max((L & mature).sum(), 1))
            cell = is_main & mature & (df.bucket == bname)
            if wgt > 0.02 and cell.sum() < 10: ok_adj = False
            if cell.sum(): adj += wgt * float(walked[cell].mean())
        rows.append(dict(code=code, reason=name, walk_rate_adjusted=round(adj, 4) if ok_adj else None, n=int(is_main.sum()), share=round(float(is_main.sum() / max(L.sum(), 1)), 4),
                         any_mention_share=round(float(any_m.sum() / max(L.sum(), 1)), 4),
                         median_hours_at_review=round(float(df.hours_at_review[is_main].median()), 1) if is_main.sum() else None,
                         walk_n=r["n"], walk_rate=r["rate"] if r["shown"] else None, walk_lo=r["lo"] if r["shown"] else None,
                         walk_hi=r["hi"] if r["shown"] else None, vs_game_average=flag,
                         says_stopped_rate=st["rate"] if st["shown"] else None))
    out["reasons"] = sorted(rows, key=lambda x: -x["n"])

    # --- regression with controls, and sensitivity of the walk-away definition
    mf = model_frame(df, L, mature, g); POOL.append(mf)
    out["model"] = walk_model(mf)
    out["sensitivity"] = sensitivity(df, L, mature, out["reasons"])

    # --- second-level breakdown (only where a sub-reason pass was run)
    sub_files = glob.glob(os.path.join(ROOT, "data", "work", "sublabels", str(appid), "batch_*.json"))
    if sub_files:
        sub = pd.DataFrame([l for f in sub_files for l in json.load(open(f))["labels"]])
        ds = df.merge(sub, on="rid"); dsm = ds[ds.days_since_review >= MATURE_DAYS]
        design_walk = float((dsm.hours_after_review < WALK_HOURS).mean())
        srows = []
        for code, name in SUBREASONS.items():
            a = ds[ds["sub"] == code]; am = dsm[dsm["sub"] == code]; k = int((am.hours_after_review < WALK_HOURS).sum()); lo, hi = wilson(k, len(am))
            en = a[a.language == "english"]; ot = a[a.language != "english"]
            srows.append(dict(code=code, sub_reason=name, n=len(a), share=round(len(a) / len(ds), 4),
                              share_english=round(len(en) / max((ds.language == "english").sum(), 1), 4), share_other_languages=round(len(ot) / max((ds.language != "english").sum(), 1), 4),
                              median_hours_at_review=round(float(a.hours_at_review.median()), 1) if len(a) else None,
                              walk_n=len(am), walk_rate=round(k / len(am), 4) if len(am) >= MIN_CELL else None, walk_lo=lo if len(am) >= MIN_CELL else None, walk_hi=hi if len(am) >= MIN_CELL else None,
                              vs_design_average=("n/a" if len(am) < MIN_CELL else "higher" if lo > design_walk else "lower" if hi < design_walk else "similar")))
        out["sub_reasons"] = dict(parent="DESIGN", parent_reason=REASONS["DESIGN"], labeled=len(ds), eligible=int((L & (df.main == "DESIGN")).sum()),
                                  parent_walk_rate=round(design_walk, 4), rows=sorted(srows, key=lambda r: -r["n"]))

    # --- by review language (a rough stand-in for market; many players review in English wherever they live)
    counts = df.language.value_counts()
    groups = [(l, df.language == l) for l in counts.index if counts[l] >= MIN_LANG]
    small = ~df.language.isin([l for l, _ in groups])
    if small.sum(): groups.append(("_small", small))
    named_codes = [r["code"] for r in out["reasons"] if r["code"] not in ("OTHER",)][:6]
    lrows = []
    for l, msk in groups:
        ln = msk & ~df.voted_up; ll = ln & df.main.notna(); r = rate(walked, ln & mature); nl = int(ll.sum())
        mix = df.main[ll].value_counts()
        mix_named = mix.drop(labels=["OTHER"], errors="ignore")
        lrows.append(dict(code=l, language=LANG_NAMES.get(l, l) if l != "_small" else f"All other languages (under {MIN_LANG} reviews each)",
                          reviews=int(msk.sum()), share_of_reviews=round(float(msk.mean()), 4), negative=int(ln.sum()),
                          negative_share=round(float(ln.sum() / msk.sum()), 4),
                          median_hours_at_negative_review=round(float(df.hours_at_review[ln].median()), 1) if ln.sum() else None,
                          neg_walk_n=r["n"], neg_walk_rate=r["rate"] if r["shown"] else None, labeled=nl,
                          top_reason=REASONS[mix_named.index[0]] if nl >= MIN_CELL and len(mix_named) else None,
                          top_reason_share=round(float(mix_named.iloc[0] / nl), 4) if nl >= MIN_CELL and len(mix_named) else None,
                          reason_shares={c: (round(float(mix.get(c, 0) / nl), 4) if nl >= MIN_CELL else None) for c in REASONS}))
    out["languages"] = lrows; out["language_reason_columns"] = named_codes

    # --- reason x playtime bucket (share of that bucket's labeled negative reviews)
    grid = []
    for lo, hi, name in BUCKETS:
        b = L & (df.bucket == name); n = int(b.sum())
        grid.append(dict(bucket=name, n=n, shares={c: (round(float((b & (df.main == c)).sum() / n), 4) if n >= MIN_CELL else None) for c in REASONS}))
    out["reason_by_playtime"] = grid

    # --- said vs did
    rows = []
    for q, name in [("STOPPED", "Said they quit, refunded or won't return"), ("WAITING", "Said they'd come back if it's fixed"), ("NONE", "Said nothing about stopping")]:
        s = L & (df.quit == q); sm = s & mature
        rows.append(dict(code=q, statement=name, n=int(s.sum()), share=round(float(s.sum() / max(L.sum(), 1)), 4), mature_n=int(sm.sum()),
                         walk_rate=round(float(walked[sm].mean()), 4) if sm.sum() >= MIN_CELL else None,
                         kept_10h_rate=round(float((df.hours_after_review[sm] >= 10).mean()), 4) if sm.sum() >= MIN_CELL else None,
                         active_now_rate=round(float((df.pt_2w[sm] > 0).mean()), 4) if sm.sum() >= MIN_CELL else None))
    out["said_vs_did"] = rows

    # --- timeline by month
    top = [r["code"] for r in out["reasons"] if r["code"] not in ("OTHER",)][:5]
    rows = []
    for mth, d in df.groupby("month"):
        dl = d[d.main.notna() & ~d.voted_up]
        rows.append(dict(month=mth, reviews=len(d), negative=int((~d.voted_up).sum()), negative_share=round(float((~d.voted_up).mean()), 4),
                         labeled=len(dl), reason_counts={c: int((dl.main == c).sum()) for c in REASONS},
                         patches=[a["title"] for a in ann if a["is_patch"] and a["date"][:7] == mth]))
    out["monthly"] = rows; out["top_reasons"] = top

    # --- negative-review spike weeks after the launch period, with official posts from the same days
    rel = pd.Timestamp(g["release"], tz="UTC")
    day = pd.to_datetime(df.created, unit="s", utc=True).dt.floor("D")
    wk = day - pd.to_timedelta(day.dt.weekday, unit="D")  # Monday that starts the review's week (UTC)
    df["week"] = wk
    weekly = df.groupby("week").agg(reviews=("voted_up", "size"), negative=("voted_up", lambda x: int((~x).sum()))).sort_index()
    weekly = weekly.asfreq("7D", fill_value=0)
    spikes = []
    for i in range(len(weekly)):
        w = weekly.index[i]
        if w < rel + pd.Timedelta(days=42) or i < 8: continue
        prior = weekly.negative.iloc[i - 8:i]
        base = float(prior.median())
        cur = int(weekly.negative.iloc[i])
        if cur >= 40 and cur >= 2 * max(base, 1) and cur >= prior.max():
            spikes.append((w, cur, base))
    # keep the first week of each run of consecutive spike weeks, then the largest five
    kept = []
    for w, cur, base in spikes:
        if kept and (w - kept[-1][0]).days <= 14:
            if cur > kept[-1][1]: kept[-1] = (kept[-1][0], cur, kept[-1][2], w)
            continue
        kept.append((w, cur, base, w))
    kept = sorted(kept, key=lambda x: -x[1])[:5]
    rows = []
    for w0, cur, base, wpeak in sorted(kept, key=lambda x: x[0]):
        d = df[df.week == wpeak]; dl = d[d.main.notna() & ~d.voted_up]
        mix = dl.main.value_counts()
        near = [dict(date=a["date"], title=a["title"]) for a in ann
                if (w0 - pd.Timedelta(days=7)).timestamp() <= a["ts"] < (wpeak + pd.Timedelta(days=7)).timestamp()]
        rows.append(dict(week_start=wpeak.strftime("%Y-%m-%d"), negative=cur, usual_weekly_negative=round(base, 1),
                         negative_share=round(float((~d.voted_up).mean()), 4), reviews=len(d),
                         top_reasons=[dict(code=c, reason=REASONS[c], share=round(float(v / len(dl)), 4)) for c, v in mix.head(3).items()] if len(dl) >= MIN_CELL else [],
                         official_posts=near[:6]))
    out["spikes"] = rows
    out["weekly"] = [dict(week=w.strftime("%Y-%m-%d"), reviews=int(r.reviews), negative=int(r.negative)) for w, r in weekly.iterrows()]
    out["patch_dates"] = [dict(date=a["date"], title=a["title"]) for a in ann if a["is_patch"]]

    qf = os.path.join(ROOT, "data", "work", "quotes", f"{appid}.json")
    out["paraphrases"] = json.load(open(qf))["paraphrases"] if os.path.exists(qf) else {}
    json.dump(out, open(os.path.join(DOCS, f"{g['slug']}.json"), "w"), indent=1)
    return out


if __name__ == "__main__":
    res = [analyze(g) for g in GAMES if os.path.exists(os.path.join(ROOT, "data", "work", f"reviews_{g['appid']}.parquet"))]
    ov = []
    for o in res:
        b = o["behaviour"]; top = [r for r in o["reasons"] if r["code"] != "OTHER"][:1]
        ov.append(dict(slug=o["slug"], name=o["name"], genre=o["genre"], release=o["release"], snapshot=o["snapshot"],
                       reviews=o["overview"]["reviews"], negative=o["overview"]["negative"], negative_share=o["overview"]["negative_share"],
                       labeled=o["funnel"]["labeled"], neg_walk_rate=b["negative"].get("walk_rate"), pos_walk_rate=b["positive"].get("walk_rate"),
                       neg_refunded_rate=b["negative"].get("refunded_rate"), neg_active_now_rate=b["negative"].get("active_now_rate"),
                       neg_median_hours_at_review=o["overview"]["median_hours_at_negative_review"],
                       top_reason=top[0]["reason"] if top else None, top_reason_share=top[0]["share"] if top else None,
                       reason_shares={r["code"]: r["share"] for r in o["reasons"]},
                       reason_walk={r["code"]: r["walk_rate"] for r in o["reasons"]},
                       reason_flags={r["code"]: r["vs_game_average"] for r in o["reasons"]},
                       english=o["funnel"]["english"], other_languages=o["funnel"]["other_languages"],
                       languages=[dict(code=l["code"], language=l["language"], reviews=l["reviews"], negative_share=l["negative_share"], neg_walk_rate=l["neg_walk_rate"], top_reason=l["top_reason"]) for l in o["languages"]],
                       kept_10h_rate=b["negative"].get("kept_10h_rate"),
                       under2h_negative_share=o["playtime"][0]["negative_share_in_bucket"], under2h_neg_walk_rate=o["playtime"][0]["neg_walk_rate"],
                       said_stopped_share=o["said_vs_did"][0]["share"], said_stopped_walk_rate=o["said_vs_did"][0]["walk_rate"],
                       said_waiting_share=o["said_vs_did"][1]["share"], said_waiting_kept_10h_rate=o["said_vs_did"][1]["kept_10h_rate"]))
    json.dump(ov, open(os.path.join(DOCS, "overview.json"), "w"), indent=1)
    pooled = walk_model(pd.concat(POOL), pooled=True)
    json.dump(dict(pooled=pooled, per_game={o["slug"]: o["model"] for o in res}, sensitivity={o["slug"]: o["sensitivity"] for o in res}),
              open(os.path.join(DOCS, "models.json"), "w"), indent=1)
    pd.DataFrame([dict(game=o["name"], reference=o["model"].get("reference_reason"), **r) for o in res if o["model"].get("ok") for r in o["model"]["rows"]]
                 + [dict(game="All six games (pooled, game fixed effects)", reference=pooled.get("reference_reason"), **r) for r in pooled.get("rows", [])]).to_csv(os.path.join(PUB, "walk_away_model_odds_ratios.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], **r) for o in res for r in o["sensitivity"]]).to_csv(os.path.join(PUB, "walk_away_sensitivity.csv"), index=False)
    # flat tables
    pd.DataFrame([{k: v for k, v in r.items() if not isinstance(v, (dict, list))} for r in ov]).to_csv(os.path.join(PUB, "games_overview.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], **r) for o in res for r in o["reasons"]]).to_csv(os.path.join(PUB, "reasons_by_game.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], **r) for o in res for r in o["playtime"]]).to_csv(os.path.join(PUB, "playtime_buckets_by_game.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], **r) for o in res for r in o["said_vs_did"]]).to_csv(os.path.join(PUB, "said_vs_did_by_game.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], group=k, **v) for o in res for k, v in o["behaviour"].items()]).to_csv(os.path.join(PUB, "behaviour_after_review.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], month=r["month"], reviews=r["reviews"], negative=r["negative"], negative_share=r["negative_share"], labeled=r["labeled"], **r["reason_counts"]) for o in res for r in o["monthly"]]).to_csv(os.path.join(PUB, "monthly_by_game.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], **{k: v for k, v in l.items() if k != "reason_shares"}, **{"share_" + c: v for c, v in l["reason_shares"].items()}) for o in res for l in o["languages"]]).to_csv(os.path.join(PUB, "languages_by_game.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], parent=o["sub_reasons"]["parent_reason"], **r) for o in res if o.get("sub_reasons") for r in o["sub_reasons"]["rows"]]).to_csv(os.path.join(PUB, "sub_reasons.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], **o["funnel"]) for o in res]).to_csv(os.path.join(PUB, "pipeline_row_counts.csv"), index=False)
    pd.DataFrame([dict(game=o["name"], week_start=s["week_start"], negative=s["negative"], usual_weekly_negative=s["usual_weekly_negative"], negative_share=s["negative_share"],
                       top_reasons="; ".join(f"{t['reason']} {t['share']:.0%}" for t in s["top_reasons"]), official_posts=" | ".join(f"{p['date']} {p['title']}" for p in s["official_posts"])) for o in res for s in o["spikes"]]).to_csv(os.path.join(PUB, "spike_weeks.csv"), index=False)
    for o in res:
        b = o["behaviour"]; print(f"{o['name'][:28]:28} n={o['overview']['reviews']:6} neg={o['overview']['negative_share']:.2f} labeled={o['funnel']['labeled']:6} walk neg={b['negative'].get('walk_rate')} pos={b['positive'].get('walk_rate')} spikes={len(o['spikes'])}")
