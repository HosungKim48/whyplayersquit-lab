# DATA.md

Snapshot: 2026-11-24 (UTC). All data is public Steam data.

## Files

| File | Published? | What it is |
|---|---|---|
| `data/raw/<appid>/<YYYY-MM>_page_*.json.gz` | No (local cache) | Raw API pages of English reviews, 100 each, exactly as Steam returned them. Contain review text and reviewer IDs. |
| `data/raw/<appid>_other/...` | No (local cache) | Same, for all other languages. |
| `data/raw/<appid>/state.json` | No | Fetch progress per calendar month (cursor, count, Steam's `total_matching`). |
| `data/raw/news/<appid>.json` | No | Official announcements from Steam's news API (title, date, tags). |
| `data/work/reviews_<appid>.parquet` | No | One row per review, cleaned, with derived columns (below). |
| `data/work/labels/<appid>/batch_*.json`, `labels/<appid>_other/` | No | Model labels per batch of 40 reviews (English / other languages), with real token counts and cost per call. |
| `data/work/sublabels/1295660/` | No | Design sub-reason labels for Civilization VII. |
| `data/work/quotes/<appid>.json` | No | Paraphrases and their cost. |
| `data/work/audit_sample*.json`, `audit_verdicts*.json`, `spotcheck_50.csv` | No | Random samples with text, and the second-model verdicts on them. |
| `docs/data/<slug>.json` | Yes | Every number on that game's report page. |
| `docs/data/overview.json`, `models.json`, `cost.json`, `label_audit.json` | Yes | Cross-game table, regression and sensitivity results, spend, accuracy check (no text, no IDs). |
| `data/public/*.csv` | Yes | Same numbers as flat tables. |

## Row counts by stage

| Game | Steam lifetime summary | API listing | Fetched, unique | English | Other languages | Negative | Negative, enough text | Labeled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sid Meier's Civilization VII | 45,822 | 44,064 | 44,063 | 29,077 | 14,986 | 22,611 | 21,769 | 21,618 |
| Cities: Skylines II | 66,813 | 64,718 | 64,710 | 34,668 | 30,042 | 28,297 | 26,740 | 26,711 |
| PAYDAY 3 | 51,218 | 50,397 | 50,359 | 32,298 | 18,061 | 26,654 | 24,914 | 24,807 |
| Dragon's Dogma 2 | 79,424 | 77,182 | 77,177 | 44,681 | 32,496 | 27,846 | 26,611 | 26,425 |
| Monster Hunter Wilds | 204,706 | 200,393 | 200,364 | 84,926 | 115,438 | 93,999 | 89,401 | 89,279 |
| Starfield | 115,692 | 114,561 | 114,555 | 85,456 | 29,099 | 47,205 | 44,145 | 43,872 |
| **Total** | 563,675 | 551,315 | 551,228 | 311,106 | 240,122 | 246,612 | 233,580 | 232,712 |

Source: `data/public/pipeline_row_counts.csv`.

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
| `language` | Steam language code of the review (`english`, `schinese`, `japanese`, ...) |
| `snapshot` | Unix time that review's page was fetched (English and other languages were fetched in separate runs on the same day) |
| `substantive` | Enough text to carry a reason: 3+ words, or 4+ characters for Chinese, Japanese, Korean and Thai |
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
- **Coverage gap of 1.0%–3.8%.** Steam's lifetime summary count is higher than what the month-by-month listing returns. The listing itself was fetched almost completely (1–6 reviews short per game). The cause of the gap is not documented.
- **`steam_purchase` is True on every row**, even with `purchase_type=all`, so Steam-key purchases cannot be separated.
- **Free-to-play games** returned implausibly small totals from this endpoint (for example about 1,000 for a game with a very large player base), so they were left out.
- **`pt_review` and edits.** It is not documented whether editing a review refreshes `pt_review`. Reports show the walk-away rate with and without edited reviews.
- **`hours_after_review` is never negative** in this data.
- **Labels.** `main` / `second` use 11 codes (see `src/label_prompt.txt`); `quit` is STOPPED / WAITING / NONE. Reviews without enough text (`substantive` = False) were not sent to the model. 0.1%–0.7% of sent reviews came back without a valid label line and stay unlabeled.
- **One review was labeled twice** (Monster Hunter Wilds). `analyze.py` keeps one label per review ID.
- **Language is not country.** A review's language is the closest public stand-in for market, and it is imperfect.
- **Language parameter.** The endpoint silently falls back to English unless languages are passed as an array (`languages[0]=...`).
