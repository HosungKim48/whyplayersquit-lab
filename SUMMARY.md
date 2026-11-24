# SUMMARY

**Site:** https://hosungkim48.github.io/whyplayersquit-lab/
**Repo:** https://github.com/HosungKim48/whyplayersquit-lab
**Data snapshot:** 2026-11-24 (UTC)

## Bottom line

I built quit-signal reports for six games from 311,104 public English Steam reviews. The core idea: Steam shows how long each reviewer had played when they wrote the review and how long they have played in total. The gap tells us what they did *after* complaining. A negative review turns out to be a warning more often than a goodbye: depending on the game, only 26%–51% of negative reviewers logged less than one more hour afterwards.

Joining that behaviour with the reason each negative review gives (114,069 reviews labeled by a small model) splits complaints into two kinds:

- **Complaints from players who mostly stay.** Crashes and bugs: these reviewers walked away clearly less often than other negative reviewers in 6 of 6 games.
- **Complaints that go with leaving.** Gameplay and design choices (clearly more often in 5 of 6 games) and story and writing (4 of 6).

Total paid model spend: **$7.39** of the $30 cap.

## What I built and why

| Piece | What it does |
|---|---|
| Overview page | Cross-game comparison and the patterns that held across games |
| Six game reports | When reviewers give up, why, which complaints go with leaving, said-versus-did, timeline with official patches, paraphrased examples, suggested checks for a studio |
| Method & limits page | Data source, row counts per stage, definitions, accuracy check, limits, cost |
| Code (`src/`) | Fetch → clean → label → analyze → build site → verify. Every page is rendered from JSON written by code. |

**Why this approach.** Most review analysis stops at "what do people complain about". Studios already know that. The harder question is which complaints cost players. Review text alone cannot answer it, but public playtime can get part of the way: it shows which complainers actually stopped. That is the one thing in public Steam data that is behaviour, not opinion, so I made it the centre of every report.

**What "useful to a studio" means here.** A report is useful if it changes what a team looks at next. Each report is built around four decisions: which complaint to prioritize, which hours of the game to protect, how many players are waiting for fixes, and which past patches to re-examine.

## Which games and why

| Game | Genre | English reviews | Negative | Negative reviewers who walked away | Top complaint |
|---|---|---:|---:|---:|---|
| Sid Meier's Civilization VII | 4X strategy | 29,077 | 49% | 38% | Gameplay & design choices (36%) |
| Cities: Skylines II | City builder | 34,666 | 43% | 26% | Crashes & bugs (29%) |
| PAYDAY 3 | Co-op shooter | 32,298 | 54% | 34% | Online, accounts & DRM (36%) |
| Dragon's Dogma 2 | Action RPG | 44,682 | 31% | 41% | Performance (29%) |
| Monster Hunter Wilds | Co-op hunting | 84,926 | 29% | 26% | Performance (44%) |
| Starfield | Single-player RPG | 85,455 | 42% | 51% | Gameplay & design choices (23%) |

Reasons for the choice:

- **Plenty of negative reviews** (13,700+ each), so reason-by-playtime tables are not thin.
- **Different kinds of trouble**: technical launches (Cities II, Wilds, Dragon's Dogma 2), design disputes (Civ VII, Starfield), online-service failure (PAYDAY 3). This lets the reports show contrast.
- **Small enough to fetch in full politely.** I wanted complete review histories, not a "most recent N" sample that would bias the timeline.
- **Paid games only.** The review endpoint returned implausibly small totals for free-to-play games, so I left them out.

Left out on purpose: Helldivers 2 (647,000 English reviews; too many requests to fetch in full), Palworld and Lethal Company (same), free-to-play titles (data problem above).

## What a studio could do with each report

- **Civilization VII.** Design complaints are the largest group (36%) and go with leaving more than average; crash complaints go with staying. The report also flags three post-launch spike weeks that sit next to update and DLC posts. Use: test optional rules for the most-named mechanics before spending more on stability.
- **Cities: Skylines II.** Lowest walk-away rate (26%) even with 43% negative reviews: these are players who stayed and are frustrated. Crashes and performance are over half of complaints. Use: the audience is still there, so fix cadence and communication matter more than win-back.
- **PAYDAY 3.** Online and account complaints are 36% of negative reviews but those reviewers left *less* often than others; content and design reviewers left more. Use: the server story was loud, the content gap was costly.
- **Dragon's Dogma 2.** 76% of reviews under 2 hours are negative and 58% of those reviewers never logged another hour; 8% of negative reviews are refunds. Use: the refund window is where this game lost people; performance on first launch is the thing to instrument.
- **Monster Hunter Wilds.** Performance is 44% of complaints, yet performance reviewers walked away less than average and 65% of "waiting" reviewers played 10+ more hours. Use: a large, still-engaged group is waiting on performance; title-update weeks line up with the biggest spikes.
- **Starfield.** Highest walk-away rate (51%). Design and content complaints dominate (23% each), and design reviewers left clearly more often than other negative reviewers, while crash reviewers left far less often (30%). Use: this looks like a design-and-content retention question more than a stability one; the June 2024 spike week is 48% price complaints.

These are leads to check against internal telemetry, not conclusions.

## Verification I ran

- `src/verify.py` (all checks pass): review counts and walk-away rates recomputed independently from the local tables; reason shares sum to 100%; fetched reviews ≥ 99.5% of what the API listed; no reviewer IDs or review IDs in any published file; no 8-word run on any page matches any raw review; all 60 paraphrases ≤ 20 words; spend under budget.
- **Label accuracy:** I read a random sample of 60 labeled reviews (10 per game). Main reason judged correct in 53 of 60 (88%); quit-statement tag in 57 of 60 (95%). This check was done by me (an AI), not by a human.
- **For your own spot check:** `data/work/spotcheck_50.csv` holds 50 random labeled reviews with text and a blank `your_verdict` column. It is local only and not published.
- Pages opened and checked in a browser, locally and on the live site.

## Cost

| Step | Calls | Cost |
|---|---:|---:|
| Reason labeling, 114,069 reviews (Claude Haiku) | 3,033 | $6.69 |
| Pilot and debugging | 6 | $0.69 |
| Paraphrases | 6 | $0.02 |
| **Total** | | **$7.39** |

Source: `data/public/cost_ledger.csv`, summed from the token counts and list-price cost returned with every call.

Two things to know:

- **$0.64 was wasted in the first pilot.** The command-line tool loaded about 200,000 tokens of unrelated connector definitions into each call. I caught it after 3 calls, fixed the flags, and cost per batch fell from about $0.21 to about $0.002.
- **How the calls were made.** No Anthropic API key was available in the environment, so labeling ran through the Claude Code command line with the Haiku model on your account. The dollar figures are the list-price amounts the tool reports; what you are actually billed depends on your plan. A Groq key was present; I made one test call (132 tokens) and did not use it further because its rate limit (8,000 tokens per minute) was too low.

## What I would do differently with a bigger budget

- **Label positive reviews too.** Many "recommended" reviews contain a reason for stopping ("great for 40 hours, then nothing to do"). That would give a view of quiet churn, not just angry churn.
- **Sub-reasons per game.** "Gameplay & design" is broad. A second pass could name the specific mechanic (for example, a particular progression system) so the report points at a feature, not a category.
- **Human-checked labels.** A few hundred reviews labeled by two people would give a real error rate instead of an AI-on-AI check.
- **More games, including well-received ones**, to see whether the stay/leave split of complaints holds outside troubled launches.
- **Other languages.** Chinese is a large share of Steam reviews and may tell a different story.
- **Repeat snapshots.** Playtime is only known at the snapshot. Monthly snapshots would turn "played since the review" into a real return curve.

## Judgment calls

1. **English reviews only.** Keeps labeling consistent and cheap. Stated on every page.
2. **Full history instead of a sample.** This limited the game list to titles under about 90,000 English reviews.
3. **"Walked away" = under 1 more hour of play after the review, for reviews at least 30 days old.** Simple and easy to explain. A 90-day cut is also computed in each game's JSON (for Civilization VII it gives 37% instead of 38%).
4. **Edited reviews kept in.** It is not documented whether editing refreshes "playtime at review". Each report shows the rate with and without edited reviews; excluding them moves it by 0 to 5 points.
5. **Only negative reviews labeled, and only those with 3+ words.** Shorter ones cannot carry a reason. 6,410 negative reviews were dropped by this filter.
6. **One main reason per review**, plus an optional second. Simpler charts; multi-issue reviews are flattened. Tables also show "main or second".
7. **Eleven fixed reason categories across all games**, so games can be compared. The cost is less game-specific detail.
8. **Labeled everything instead of sampling.** After the cost fix it was cheap enough, and it keeps small cells (late months, long-playtime bands) usable.
9. **"Clearly higher / lower" needs the whole 95% interval above or below the game average.** Many differences are therefore reported as "similar".
10. **Added a playtime-adjusted walk-away rate.** New players leave more whatever they complain about, so the raw comparison alone could mislead.
11. **Off-game reviews** (politics, social topics, specific people or companies) are counted as a share and not characterized, quoted, or paraphrased. Two spike weeks are dominated by them; the reports say so and stop there.
12. **Paraphrases, not quotes.** Written by the model, then screened by code: 20 words or fewer and no 4-word run shared with the source. 75 of 240 candidates were rejected by the screen.
13. **Patch matching is by date only.** Official posts near a spike are listed as context. I did not classify patch contents.
14. **Steam endpoint.** The old review address now redirects. I tried one request to an undocumented store address, stopped, read Steam's documentation, and used the documented replacement for everything.
15. **Request rate.** Four game streams, each waiting 0.7 seconds between requests, about one request per second overall. No errors or rate-limit responses occurred.
16. **Coverage gap.** Steam's lifetime summary count is 0.9%–3.7% higher than what the listing returned. I could not find the cause and report it as a limit.
17. **Did not ask before the paid run.** Your standing rule is to estimate and ask first; this task said to work without asking, so I ran a pilot, estimated about $8, set a hard stop at $22, and proceeded.
18. **Created the GitHub repo** `HosungKim48/whyplayersquit-lab` as public, because it did not exist and GitHub Pages needs it. Nothing else on your account was touched.
19. **Studio suggestions are generic per complaint type** and worded as checks to run, because reviews alone cannot justify telling a studio what to build.
20. **The "what a studio could do" notes in this file** are my reading of the numbers and go beyond what the site states.
