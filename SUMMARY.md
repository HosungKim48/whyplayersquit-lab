# SUMMARY

**Site:** https://hosungkim48.github.io/whyplayersquit-lab/
**Repo:** https://github.com/HosungKim48/whyplayersquit-lab
**Data snapshot:** 2026-11-24 (UTC)

## Bottom line

Quit-signal reports for six games, built from 551,228 public Steam reviews in every language (311,106 English, 240,122 in 28 other languages). Steam shows how long each reviewer had played when they wrote the review and how long they have played in total. The gap shows what they did *after* complaining. Depending on the game, only 24%–48% of negative reviewers logged less than one more hour afterwards, so a negative review is more often a warning than a goodbye.

Joining that behaviour with the reason each negative review gives (232,712 reviews labeled by a small model) splits complaints into two kinds:

- **Complaints from players who mostly stay.** Crashes and bugs: these reviewers walked away clearly less often than other negative reviewers in 6 of 6 games.
- **Complaints that go with leaving.** Gameplay and design choices (clearly more often in 5 of 6 games). In a regression that holds playtime, language, review age and game constant, every other complaint type has higher odds of walking away than crash complaints (design: 2.3 times).
- **English is not the whole picture.** Monster Hunter Wilds is 29% negative in English, 78% in Simplified Chinese and 69% in Japanese; across all languages it is 47%.

Total paid model spend: **$14.96** of the $30 cap.

## What I built and why

| Piece | What it does |
|---|---|
| Overview page | Cross-game comparison, and the pooled regression |
| Six game reports | Laid out for a studio: headline numbers, three calls (prioritize / protect / win back), a priority map of complaints, markets by language, said-versus-did, timeline with official posts, paraphrased examples, checks grouped by owning team |
| Case study | One written walk-through (Monster Hunter Wilds): how the English-only reading pointed at the wrong priority |
| Method & limits page | Row counts per stage, definitions, second-model label check, limits, cost |
| Code (`src/`) | Fetch → clean → label → analyze → build site → verify. Every page is rendered from JSON written by code. |

**Why this approach.** Most review analysis stops at "what do people complain about". Studios already know that. The harder question is which complaints cost players. Public playtime gets part of the way: it shows which complainers actually stopped. That is the one thing in public Steam data that is behaviour, not opinion, so every report is built around it.

**Changes since the first version.** (1) All languages instead of English only. (2) Pages redesigned for a studio reader. (3) Portfolio fixes: byline, a label check by a larger model, a case study, a regression with controls, design sub-reasons for one game, a sensitivity check on the walk-away definition, a shorter README with a walkthrough GIF, and a trimmed method page.

## Which games and why

| Game | Reviews | Share not English | Negative | Negative reviewers who walked away | Top complaint |
|---|---:|---:|---:|---:|---|
| Sid Meier's Civilization VII | 44,063 | 34% | 51% | 36% | Gameplay & design choices (33%) |
| Cities: Skylines II | 64,710 | 46% | 44% | 24% | Crashes & bugs (28%) |
| PAYDAY 3 | 50,359 | 36% | 53% | 32% | Online, accounts & DRM (37%) |
| Dragon's Dogma 2 | 77,177 | 42% | 36% | 38% | Performance (29%) |
| Monster Hunter Wilds | 200,364 | 58% | 47% | 24% | Performance (28%) |
| Starfield | 114,555 | 25% | 41% | 48% | Gameplay & design choices (22%) |

- **Plenty of negative reviews** (22,000+ each), so tables by reason, playtime and language are not thin.
- **Different kinds of trouble:** technical launches (Cities II, Wilds, Dragon's Dogma 2), design disputes (Civ VII, Starfield), online-service failure (PAYDAY 3).
- **Small enough to fetch in full politely.** Complete review histories, not a "most recent N" sample.
- **Paid games only.** The review endpoint returned implausibly small totals for free-to-play games.

Left out on purpose: Helldivers 2, Palworld, Lethal Company (too many requests to fetch in full), and free-to-play titles.

## What a studio could do with each report

- **Civilization VII.** Design is the top complaint in every language. The sub-reason pass (7,151 design reviews) shows the Ages system is named most (27%), but those reviewers left *less* often than other design critics (33%); reviewers who say it "doesn't feel like Civilization" without naming a mechanic left most (46%). Use: the Ages critics are engaged and specific, so optional rules could keep them; the "not Civ" group is the harder loss.
- **Cities: Skylines II.** Lowest walk-away rate (24%) with 44% negative: frustrated players who stayed. Crashes and performance are over half of complaints. Use: fix cadence and communication matter more than win-back. Turkish reviews are an outlier (67% negative, mostly off-game topics); the report counts that and does not characterize it.
- **PAYDAY 3.** Online and account complaints are 37% of negative reviews, but those reviewers left *less* often (22%) than content, design and price critics (36%–41%). Use: the server story was loud; the content gap went with leaving.
- **Dragon's Dogma 2.** 78% of reviews written under 2 hours are negative and 56% of those reviewers never logged another hour; 6% of negative reviews are refunds. Simplified Chinese reviews are 55% negative against 31% in English. Use: instrument first-launch performance, and read it by region.
- **Monster Hunter Wilds.** 58% of reviews are not in English, and the verdict differs sharply by language. Critics are invested (median 61 hours at review) and 60% played 10+ more hours. Japanese critics name content first, not performance. Use: a win-back situation with different asks per market.
- **Starfield.** Highest walk-away rate (48%). Design and content dominate; design and story critics left more often, crash critics far less (28%). Use: a design-and-content retention question more than a stability one.

These are leads to check against internal telemetry, not conclusions.

## Verification I ran

- `src/verify.py`: 75 checks, all pass. Review counts and walk-away rates recomputed from the local tables; reason shares sum to 100%; language rows add up to all reviews; at least 97% of eligible reviews labeled; fetched reviews ≥ 99.5% of what the API listed; no reviewer or review IDs in any published file; no 8-word run on any page matches a raw review; all 29 paraphrases ≤ 20 words and in English; spend under budget.
- The check caught one real bug before publishing: one review had been labeled twice, which added a phantom row to Monster Hunter Wilds. Fixed in `analyze.py`.
- **Label check (second model, not human).** Claude Fable 5.2 read three random samples, 170 labeled reviews in all: main reason judged correct in 157 (92%), quit-statement tag in 158 (93%). By sample: English 53/60 and 57/60; other languages 56/60 and 57/60; mixed 48/50 and 44/50. For long reviews in the last two samples the checker read the first 420 characters. The weakest spot is the "waiting" tag, which the labeler sometimes gives to buying advice ("don't buy until patched") instead of a statement about the reviewer's own play.
- **For your own spot check:** `data/work/spotcheck_50.csv` holds the 50 mixed-sample reviews with text and a blank `your_verdict` column. Local only, not published.
- **Sensitivity.** Redefining "walked away" as under 2 or under 5 more hours keeps the ranking of complaints almost unchanged (rank correlation 0.95 or higher in every game).
- Pages opened and checked in a browser, locally and on the live site.

## Cost

| Step | Calls | Cost |
|---|---:|---:|
| Reason labeling, English reviews (Claude Haiku) | 3,033 | $6.69 |
| Reason labeling, all other languages (Claude Haiku) | 3,145 | $7.20 |
| Design sub-reasons, Civilization VII (Claude Haiku) | 179 | $0.35 |
| Pilot and debugging | 6 | $0.69 |
| Paraphrases, two rounds | 12 | $0.03 |
| **Total** | | **$14.96** |

Source: `data/public/cost_ledger.csv`, summed from the token counts and list-price cost returned with every call.

- **$0.64 was wasted in the first pilot** (each call loaded about 200,000 tokens of unrelated connector definitions). Caught after 3 calls and fixed.
- **How the calls were made.** No Anthropic API key was available, so labeling ran through the Claude Code command line with the Haiku model on your account. Dollar figures are the list-price amounts the tool reports; what you are billed depends on your plan.
- **Not in the ledger:** the work of the agent itself (planning, coding, the Fable label check) ran inside the Claude Code sessions and is not a metered API call I can count.

## What I would do differently with a bigger budget

- **Label positive reviews too.** Many "recommended" reviews contain a reason for stopping. That would show quiet churn, not just angry churn.
- **Sub-reasons for every game**, not only Civilization VII.
- **Human-checked labels in each language.** A few hundred reviews judged by native speakers would give a real error rate instead of a model-on-model check.
- **More games, including well-received ones**, to test whether the stay/leave split holds outside troubled launches.
- **Repeat snapshots.** Monthly snapshots would turn "played since the review" into a real return curve.
- **Same-community baselines.** Compare each language against its own reviews of other games, to separate "this market is unhappy" from "this community reviews harshly".

## Judgment calls

1. **All languages, labeled in the original language.** The small model read each review in its own language; nothing was machine-translated first. Paraphrases are written in English.
2. **Language is used as a stand-in for market.** It is not country. Stated on the pages.
3. **Languages under 300 reviews in a game are grouped** into one row, so no rate rests on a handful of reviews.
4. **"Enough text" rule changed for other languages:** 3+ words, or 4+ characters for Chinese, Japanese, Korean and Thai (which do not use spaces). 13,032 negative reviews were dropped by this filter.
5. **Full history instead of a sample.** This limited the game list.
6. **"Walked away" = under 1 more hour after the review, for reviews at least 30 days old.** The 2-hour and 5-hour versions are shown next to it.
7. **Edited reviews kept in**, with the rate shown with and without them, and "edited" used as a control in the regression.
8. **Only negative reviews labeled.** One main reason per review plus an optional second; eleven fixed categories across all games so they can be compared.
9. **"Clearly higher / lower" needs the whole 95% interval above or below the game average.** Many differences are reported as "similar".
10. **Regression reference group is crash complaints**, because they are the clearest "stay" group. Odds ratios describe association only; the page says so.
11. **Sub-reasons done for one game** (Civilization VII, the game where "design" is the broadest bucket), to show the method without spending on all six.
12. **Off-game reviews** (politics, social topics, specific people or companies) are counted as a share and not characterized, quoted or paraphrased. Where they dominate a language or a spike week, the report says so and stops there.
13. **Paraphrases, not quotes.** Written by the model, screened by code: 20 words or fewer, English, no 4-word run shared with the source. 99 candidates were rejected by the screen; 29 are published.
14. **Patch matching is by date only.** Official posts near a spike are listed as context.
15. **Steam endpoint and politeness.** One early request went to an undocumented address; I stopped and used the documented one for everything. About one request per second overall; no rate-limit responses.
16. **Coverage gap.** Steam's lifetime summary is 1.0%–3.8% higher than what the listing returned. Cause unknown; reported as a limit.
17. **Did not ask before the paid runs.** Your standing rule is to estimate and ask first; the task said to work without asking. I piloted, estimated, and set a hard stop at $26.
18. **Label check by Fable 5.2 is described as a second-model check everywhere**, never as human validation, as you asked.
19. **Byline.** The site names "Hosung Kim · USC Marshall School of Business" and says it was built with an AI agent. I added no email, LinkedIn or other link, and no services, pricing or contact-for-hire content.
20. **AI-role note removed.** The site first had a "Who did what" section; you asked for it to be removed. The footer still says the site was built with an AI agent. The case study is written in the first person under your name but was drafted by the agent; edit or drop that page if the voice is not yours.
21. **Your sound hook.** Each labeling call was triggering your "play a sound when Claude stops" hook. Labeling calls now skip user hooks; your settings were not changed.
22. **Two sessions.** This work was finished in a fork of the original session; the original was told not to touch the branch.
23. **Created the GitHub repo** `HosungKim48/whyplayersquit-lab` as public in the first round. Nothing else on your account was touched.
24. **The "what a studio could do" notes in this file** are my reading of the numbers and go beyond what the site states.
