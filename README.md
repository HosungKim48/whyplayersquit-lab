# Player Signals

- **What:** game-by-game reports on what players do after they review a Steam game, recommended or not, built from every public Steam review of that game in every language.
- **The quit signal:** Steam shows each reviewer's playtime when they wrote the review and their playtime now. The gap shows what they did *after* the review: kept playing, or stopped.
- **What a report shows:** who kept playing and who stopped, at every stage of play; which complaints go with players actually leaving; when fans write their reviews; and how the verdict differs by language community. The numbers for each game are in its report.

**Site:** https://hosungkim48.github.io/whyplayersquit-lab/ · **Case study:** [the review score that hid a market](https://hosungkim48.github.io/whyplayersquit-lab/case-study.html)

![Walkthrough of the site](docs/media/walkthrough.gif)

Built with an AI agent (Claude). An independent project, not affiliated with Valve or any studio or publisher.

## What is here

| Path | What it is |
|---|---|
| `docs/` | The published site. `docs/data/*.json` holds every number shown. |
| `data/public/` | The same numbers as CSV tables, plus the cost ledger and row counts per stage. |
| `src/` | All code: fetch → clean → label → analyze → build site → verify. |
| `DATA.md` | Files, columns, quirks. |
| `SUMMARY.md` | What was built, why, cost, judgment calls. |

Raw reviews (text and reviewer IDs) are not in this repository and are never published.

## Run order

```
cd src
python3 fetch_reviews.py english && python3 fetch_reviews.py other
python3 fetch_news.py && python3 fetch_lifetime_summary.py
python3 build_dataset.py
python3 label.py <appid>          # English; run_labeling_other.sh for other languages
python3 sublabel.py               # design sub-reasons, Civilization VII
python3 quotes.py && python3 audit_sample.py && python3 audit.py
python3 analyze.py && python3 after_review.py && python3 fans.py && python3 cost.py && python3 build_site.py
python3 make_media.py && python3 verify.py
```

## The weekly run (product workflow)

```
cd src
./run_weekly.sh            # refresh from Steam, recompute, rebuild every page, verify
./run_weekly.sh --offline  # same, without the Steam refresh
./run_weekly.sh --send     # also post this week's alerts to the webhooks in src/webhooks.json
```

Free: no model calls. Nothing is sent or published unless you ask.

| Script | What it does |
|---|---|
| `refresh.py` | Fetches the newest reviews (re-opens the last two months per game). Needs a computer that can reach Steam. |
| `monitor.py` | Reviews per week, negative share, and flagged weeks → `docs/data/weekly.json` |
| `benchmark.py` | Each game against similar games and all games → `docs/data/benchmark.json` |
| `alerts.py` | Discord / Slack messages for flagged weeks → `docs/data/alerts.json`; sends only with `--send` |
| `export.py` | Static JSON API and CSV files → `docs/api/v1/`, `docs/export/` |
| `build_product.py` | Features, pricing, dashboards, API page. Prices live in `PLANS` at the top. |
| `digest.py` | One ready-to-send HTML email per game → `docs/digest/` |
| `verify_product.py` | Recounts the weekly numbers from the local tables and checks every page and link |

## Adding more games

`src/games.py` lists candidate games that get the free numbers only (behaviour after the review, no model labels). On a computer that can reach Steam:

```
cd src
python3 expand.py --check     # checks each candidate against Steam, fetches nothing
python3 expand.py             # fetches, builds local tables, writes docs/data/*_all.json
```

It is safe to stop and run again; fetched pages are cached.

## Limits

- Reviews represent only the players who wrote them.
- All patterns are associations. Nothing here shows that a complaint caused a player to leave.
- Reason labels come from a language model and were checked by a second model, not by people.
