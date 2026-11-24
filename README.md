# Why Players Quit · Lab

Quit-signal reports for six PC games, built only from public Steam review data.

**Site:** https://hosungkim48.github.io/whyplayersquit-lab/

The idea: next to every review, Steam publishes how long the reviewer had played when they wrote it and how long they have played in total. The gap shows what the reviewer did *after* complaining. Combining that with the reason each negative review gives separates complaints that go with leaving from complaints players voice while they keep playing.

This is a free, public student research project. It is not affiliated with Valve or with any studio or publisher.

## What is in this repository

| Path | What it is |
|---|---|
| `docs/` | The published site (GitHub Pages). `docs/data/*.json` holds every number shown on the pages. |
| `data/public/` | The same numbers as flat CSV tables, plus the cost ledger and row counts per pipeline stage. |
| `src/` | All code. Run order below. |
| `DATA.md` | Files, columns, quirks. |
| `SUMMARY.md` | What was built, why, judgment calls, cost. |

Raw reviews (text and reviewer IDs) are **not** in this repository. They are fetched to a local cache (`data/raw/`, git-ignored) and never published.

## Run order

```
cd src
python3 fetch_reviews.py     # polite, cached, resumable; full English review history per game
python3 fetch_news.py        # official announcements / patch notes
python3 build_dataset.py     # raw pages -> one local table per game
python3 label.py <appid>     # negative reviews -> reason labels (small model; cost recorded per call)
python3 quotes.py            # short paraphrases, screened by code
python3 audit_sample.py      # random samples for accuracy checks (local only)
python3 audit.py             # accuracy results -> docs/data/label_audit.json
python3 analyze.py           # every number -> docs/data/*.json and data/public/*.csv
python3 cost.py              # spend from real token counts -> docs/data/cost.json
python3 build_site.py        # docs/*.html from the JSON
python3 verify.py            # checks: site numbers match data, no raw text or IDs published
```

## Limits (short version)

- Reviews represent only the players who wrote them, in English.
- All patterns are associations. Nothing here shows that a complaint caused a player to leave.
- Reason labels come from a language model and contain errors; see the accuracy check on the site's method page.
