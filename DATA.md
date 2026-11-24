# DATA.md

Snapshot: 2026-11-24 (UTC). All data is public Steam data.

## Files

| File | Published? | What it is |
|---|---|---|
| `data/raw/<appid>/<YYYY-MM>_page_*.json.gz` | No (local cache) | Raw API pages, 100 reviews each, exactly as Steam returned them. Contain review text and reviewer IDs. |
| `data/raw/<appid>/state.json` | No | Fetch progress per calendar month (cursor, count, Steam's `total_matching`). |
| `data/raw/news/<appid>.json` | No | Official announcements from Steam's news API (title, date, tags). |
| `data/work/reviews_<appid>.parquet` | No | One row per review, cleaned, with derived columns (below). |
| `data/work/labels/<appid>/batch_*.json` | No | Model labels per batch of 40 reviews, with real token counts and cost per call. |
| `data/work/quotes/<appid>.json` | No | Paraphrases and their cost. |
| `data/work/audit_sample.json`, `spotcheck_50.csv` | No | Random samples with text for accuracy checks. |
| `docs/data/<slug>.json` | Yes | Every number on that game's report page. |
| `docs/data/overview.json`, `cost.json`, `label_audit.json` | Yes | Cross-game table, spend, accuracy check (no text, no IDs). |
| `data/public/*.csv` | Yes | Same numbers as flat tables. |

## Row counts by stage

| Game | Steam lifetime summary | API listing (sum of months) | Fetched, unique | Negative | Negative, 3+ words | Labeled |
|---|---:|---:|---:|---:|---:|---:|
| Sid Meier's Civilization VII | 30,182 | 29,078 | 29,077 | 14,179 | 13,726 | 13,712 |
| Cities: Skylines II | 35,719 | 34,671 | 34,666 | 14,776 | 14,097 | 14,085 |
| PAYDAY 3 | 32,718 | 32,302 | 32,298 | 17,386 | 16,292 | 16,272 |
| Dragon's Dogma 2 | 45,837 | 44,686 | 44,682 | 13,725 | 13,105 | 13,012 |
| Monster Hunter Wilds | 86,761 | 84,932 | 84,926 | 24,614 | 23,326 | 23,316 |
| Starfield | 86,202 | 85,461 | 85,455 | 36,050 | 33,774 | 33,672 |

Source: `data/public/pipeline_row_counts.csv` and `data/public/steam_lifetime_summary.csv`.

## Columns of `reviews_<appid>.parquet` (local)

| Column | Meaning |
|---|---|
| `rid` | Steam review ID (never published) |
| `text` | Review text (never published) |
| `created`, `updated` | Unix time the review was written / last edited |
| `voted_up` | True = recommended (positive), False = negative |
| `votes_up` | Helpful votes |
| `pt_review` | Minutes played when the review was written |
| `pt_forever` | Minutes played in total at the snapshot |
| `pt_2w` | Minutes played in the two weeks before the snapshot |
| `last_played` | Unix time of the last session |
| `steam_purchase`, `free`, `early_access`, `refunded`, `deck` | Steam flags on the review |
| `month` | Month of the review (UTC) |
| `hours_at_review` | `pt_review / 60` |
| `hours_after_review` | `(pt_forever - pt_review) / 60` — the core behaviour measure |
| `days_since_review` | Age of the review at the snapshot |
| `days_played_after` | Days from review to last session |
| `words` | Word count of the text |
| `edited` | Review was edited more than an hour after posting |

## Three sample rows (Cities: Skylines II; text and IDs removed)

| created | voted_up | pt_review | pt_forever | pt_2w | refunded | month | hours_at_review | hours_after_review | days_since_review | words | edited |
|---:|:--|---:|---:|---:|:--|:--|---:|---:|---:|---:|:--|
| 1724863809 | True | 46498 | 76387 | 0 | False | 2024-08 | 775.0 | 498.2 | 817.5 | 5 | False |
| 1707164769 | True | 718 | 2844 | 0 | False | 2024-02 | 12.0 | 35.4 | 1022.3 | 5 | False |
| 1698249308 | True | 291 | 14086 | 710 | False | 2023-10 | 4.9 | 229.9 | 1125.5 | 47 | False |

## Quirks

- **Endpoint.** The old `store.steampowered.com/appreviews/<appid>?json=1` address now redirects to the store home page. Steam's documentation points to `api.steampowered.com/IUserReviewsService/GetAppReviews/v1/`, which is what the fetcher uses.
- **Default window.** Without a date range the new endpoint returns only about the last 30 days. A date range with a *future* end date is silently ignored. The fetcher therefore walks one calendar month at a time, ending at the snapshot time.
- **Coverage gap of 0.9%–3.7%.** Steam's lifetime summary count is higher than what the month-by-month listing returns. The listing itself was fetched almost completely (1–6 reviews short per game). The cause of the gap is not documented.
- **`steam_purchase` is True on every row**, even with `purchase_type=all`, so Steam-key purchases cannot be separated.
- **Free-to-play games** returned implausibly small totals from this endpoint (for example about 1,000 for a game with a very large player base), so they were left out.
- **`pt_review` and edits.** It is not documented whether editing a review refreshes `pt_review`. Reports show the walk-away rate with and without edited reviews.
- **`hours_after_review` is never negative** in this data.
- **Labels.** `main` / `second` use 11 codes (see `src/label_prompt.txt`); `quit` is STOPPED / WAITING / NONE. Reviews under 3 words were not sent to the model. 0.1%–0.7% of sent reviews came back without a valid label line and stay unlabeled.
