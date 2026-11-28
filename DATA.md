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
| `docs/data/after_review.json`, `data/public/after_review_by_hours.csv` | Yes | Behaviour after the review for all reviews, recommended and not recommended, by game and by hours played at review (written by `src/after_review.py`; no text, no IDs). |
| `docs/data/fans.json`, `data/public/fans_review_timing.csv` | Yes | When recommended reviews are written: hours played at review, and the point in the reviewer's whole playtime, by game and by total hours played (written by `src/fans.py`; no text, no IDs). |
| `data/public/*.csv` | Yes | Same numbers as flat tables. |
| `data/public/expansion_check.csv` | Yes | Every expansion candidate from `src/games.py`: Steam's own name, free or paid, lifetime review count, score, and kept / skipped / spare with the reason (written by `src/expand.py`). |
| `data/public/expansion_games.json` | Yes | The 24 kept expansion games: app ID, slug, name, genre, start month, Steam review total and score at the check. |
| `data/public/expansion_fetch.csv` | Yes | Per expansion game: unique reviews fetched, Steam lifetime total, coverage (fetched / total), whether every month finished, any error. |
| `docs/data/after_review_all.json`, `data/public/after_review_by_hours_all.csv` | Yes | Same fields as `after_review.json` and its CSV, for all 30 games (six studied + 24 expansion) and pooled (`after_review.py --all`; no text, no IDs). |
| `docs/data/fans_all.json`, `data/public/fans_review_timing_all.csv` | Yes | Same fields as `fans.json` and its CSV, for all 30 games and pooled (`fans.py --all`; no text, no IDs). |

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

## Row counts, 24 expansion games

Free numbers only: fetched and cleaned, never sent to a model. Snapshot: 2026-11-26 (UTC).

| Game | Steam lifetime summary | API listing | Fetched, unique | English | Other languages | Negative | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Disco Elysium | 119,627 | 116,978 | 116,972 | 57,344 | 59,628 | 8,574 | 97.8% |
| Against the Storm | 33,813 | 33,180 | 33,178 | 19,005 | 14,173 | 1,722 | 98.1% |
| DAVE THE DIVER | 145,577 | 141,839 | 141,832 | 50,707 | 91,125 | 4,735 | 97.4% |
| Lies of P | 59,915 | 57,708 | 57,697 | 27,735 | 29,962 | 4,822 | 96.3% |
| ARMORED CORE VI FIRES OF RUBICON | 67,482 | 66,583 | 66,581 | 40,746 | 25,835 | 5,642 | 98.7% |
| Hi-Fi RUSH | 27,644 | 27,331 | 27,323 | 16,188 | 11,135 | 753 | 98.8% |
| DREDGE | 48,742 | 47,093 | 47,091 | 32,242 | 14,849 | 1,966 | 96.6% |
| Manor Lords | 78,735 | 76,288 | 76,284 | 40,140 | 36,144 | 11,623 | 96.9% |
| Kingdom Come: Deliverance II | 149,428 | 142,715 | 142,708 | 67,012 | 75,696 | 9,088 | 95.5% |
| Cult of the Lamb | 114,482 | 110,797 | 110,784 | 60,226 | 50,558 | 4,628 | 96.8% |
| Persona 3 Reload | 46,357 | 42,731 | 42,728 | 23,075 | 19,653 | 2,125 | 92.2% |
| Frostpunk 2 | 21,324 | 20,875 | 20,873 | 9,660 | 11,213 | 5,360 | 97.9% |
| Dragon Age: The Veilguard | 41,709 | 41,124 | 41,122 | 29,073 | 12,049 | 13,244 | 98.6% |
| Kerbal Space Program 2 | 28,037 | 27,714 | 27,712 | 22,187 | 5,525 | 20,492 | 98.8% |
| Suicide Squad: Kill the Justice League | 12,883 | 12,603 | 12,601 | 7,680 | 4,921 | 4,927 | 97.8% |
| Homeworld 3 | 5,472 | 5,425 | 5,425 | 3,154 | 2,271 | 3,344 | 99.1% |
| S.T.A.L.K.E.R. 2: Heart of Chornobyl | 110,564 | 106,317 | 106,305 | 43,932 | 62,373 | 19,864 | 96.1% |
| Forspoken | 5,421 | 5,386 | 5,386 | 3,192 | 2,194 | 1,901 | 99.4% |
| Avowed | 12,882 | 12,387 | 12,386 | 9,579 | 2,807 | 2,882 | 96.1% |
| Darkest Dungeon II | 24,695 | 23,876 | 23,872 | 11,895 | 11,977 | 5,947 | 96.7% |
| Pacific Drive | 21,973 | 21,117 | 21,116 | 14,025 | 7,091 | 3,519 | 96.1% |
| Sea of Stars | 12,357 | 12,068 | 12,068 | 6,650 | 5,418 | 1,485 | 97.7% |
| Frostpunk | 115,751 | 114,103 | 114,095 | 38,985 | 75,110 | 8,301 | 98.6% |
| Split Fiction | 79,805 | 76,956 | 76,949 | 23,332 | 53,617 | 2,152 | 96.4% |
| **Total** | 1,384,675 | 1,343,194 | 1,343,088 | 657,764 | 685,324 | 149,096 | 97.0% |

Coverage = fetched, unique / Steam lifetime summary. Source: `data/public/expansion_fetch.csv`, `data/raw/<appid>/state.json`.

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

## Fields of `after_review.json`

Per game and pooled (`games[]`, `pooled`), for reviews at least 30 days old: `positive` / `negative` hold `n`, `walked_away`, `walk_rate` with its 95% interval, `kept_10h_rate`, `median_hours_after`, `active_now_rate`. `by_hours[]` repeats those per hours-at-review bucket with `gap` = negative minus positive walk rate. `baseline_at_critics_hours` is the positive walk rate re-weighted to the negative reviewers' mix of hours buckets; `excess_over_baseline` is the negative walk rate minus that.

Sample row (pooled, 50–200 h): positive n 87,963, walk rate 0.0887; negative walk rate 0.3159.

## Fields of `fans.json`

Per game and pooled, reviews at least 30 days old. `recommended` / `not_recommended`: `n`, quantiles of hours played at review (`p10`, `p25`, `median`, `p75`, `p90`) and `curve`, the share of reviews in each band of `params.hour_edges`. `by_total_hours[]` groups recommended reviewers by total hours played (hours at review + hours since): `n`, `share`, `median_hours_at_review`, `median_total_hours`, `position_p25` / `position_median` / `position_p75` (hours at review divided by total hours), `reviewed_in_last_tenth`, and `curve` (share of the group in each tenth of their playtime).

Sample row (pooled, 500 h+): n 25,321, median hours at review 222.6, position median 0.266.

Quirk: total hours is as of the snapshot, so for players who are still playing the position is an upper bound.

## Quirks

- **Endpoint.** The old `store.steampowered.com/appreviews/<appid>?json=1` address now redirects to the store home page. Steam's documentation points to `api.steampowered.com/IUserReviewsService/GetAppReviews/v1/`, which is what the fetcher uses.
- **Default window.** Without a date range the new endpoint returns only about the last 30 days. A date range with a *future* end date is silently ignored. The fetcher therefore walks one calendar month at a time, ending at the snapshot time.
- **Coverage gap of 1.0%–3.8%.** Steam's lifetime summary count is higher than what the month-by-month listing returns. The listing itself was fetched almost completely (1–6 reviews short per game). The cause of the gap is not documented.
- **Expansion coverage of 92.2%–99.4%.** Same cause as above: for all 24 games the month-by-month listing was fetched almost completely (0–13 reviews short per game) and every game has an empty month before its first review, so the start months are not too late. 11 games fall under 97%; Persona 3 Reload is lowest at 92.2%.
- **Missing playtime at review.** 23 Frostpunk reviews from 2018 have no `pt_review`. `after_review.py` and `fans.py` leave out reviews without it. No other game has any.
- **`steam_purchase` is True on every row**, even with `purchase_type=all`, so Steam-key purchases cannot be separated.
- **Free-to-play games** returned implausibly small totals from this endpoint (for example about 1,000 for a game with a very large player base), so they were left out.
- **`pt_review` and edits.** It is not documented whether editing a review refreshes `pt_review`. Reports show the walk-away rate with and without edited reviews.
- **`hours_after_review` is never negative** in this data.
- **Labels.** `main` / `second` use 11 codes (see `src/label_prompt.txt`); `quit` is STOPPED / WAITING / NONE. Reviews without enough text (`substantive` = False) were not sent to the model. 0.1%–0.7% of sent reviews came back without a valid label line and stay unlabeled.
- **One review was labeled twice** (Monster Hunter Wilds). `analyze.py` keeps one label per review ID.
- **Language is not country.** A review's language is the closest public stand-in for market, and it is imperfect.
- **Language parameter.** The endpoint silently falls back to English unless languages are passed as an array (`languages[0]=...`).

## Product workflow files (added 2026-11-27)

| File | Published? | What it is |
|---|---|---|
| `docs/data/weekly.json`, `data/public/weekly_by_game.csv` | Yes | Per game: 52 complete weeks (Monday to Sunday, UTC) of review counts and negative share, the "usual" week (the 8 weeks before), and flags. Written by `src/monitor.py`. |
| `docs/data/benchmark.json`, `data/public/benchmark_by_game.csv` | Yes | Per game and measure: value, rank among all games (1 = lowest), median of all games, median of the peer group. Written by `src/benchmark.py`. |
| `docs/data/alerts.json` | Yes | Every flagged week of the last year with its ready-made message. `latest` marks the newest complete week. |
| `docs/api/v1/index.json`, `docs/api/v1/games/<slug>.json` | Yes | Everything for one game in one file. `complaints` is `null` for games without model labels. |
| `docs/export/<slug>_weekly.csv`, `<slug>_summary.csv` | Yes | The same numbers as CSV. Summary is long format: section, group, measure, value. |
| `docs/digest/<slug>.html` | Yes | The weekly email, as a web page. |
| `src/webhooks.json` | No (gitignored) | Discord / Slack webhook addresses per game slug. Does not exist until you add it. |
| `data/work/alerts_sent.json` | No | Which (game, week) alerts were already sent, so none is sent twice. |

Quirks:
- **Flags.** `volume`: 50+ reviews and at least 2 times the median of the 8 weeks before. `more_negative` / `more_positive`: negative share 15+ points from the share of the 8 weeks before, with 30+ reviews on both sides. Thresholds are constants at the top of `monitor.py`.
- **Weeks with under 30 reviews** have a `negative_share` but the dashboard does not draw it on the line.
- **Peer groups** are four broad families set by keywords in the genre label (`FAMILIES` in `benchmark.py`). Shooters has only 3 games, so its peer median rests on 2.
- **Ranks cover the games on this site only**, not Steam.
- **After a refresh**, reviews older than about two months keep the playtime seen at an earlier snapshot. A full fetch renews them.
- **Snapshots differ by game** (2026-11-24 for the first six, 2026-11-26 for the rest); every game's latest complete week is the week of 2026-11-16.

Sample row, `weekly_by_game.csv`: `PAYDAY 3,2026-11-16,233,37,0.1588,50.0,0.1924,volume`
