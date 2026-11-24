"""One small request per game: Steam's own lifetime review totals (all languages), to compare with what was fetched."""
import os, time, requests, pandas as pd
from games import GAMES
rows = []
for g in GAMES:
    r = requests.get("https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/", params=dict(appid=g["appid"], **{"languages[0]": "all"}, filter="recent", review_type="all", purchase_type="all", num_per_page=1, filter_offtopic_activity=0, cursor="*"), timeout=40)
    q = r.json()["response"]["query_summary"]
    rows.append(dict(appid=g["appid"], game=g["name"], steam_summary_total=q["total_reviews"], steam_summary_negative=q["total_negative"], steam_score_label=q["review_score_desc"], checked_at=int(time.time())))
    time.sleep(1.5)
pd.DataFrame(rows).to_csv(os.path.join(os.path.dirname(__file__), "..", "data", "public", "steam_lifetime_summary.csv"), index=False)
print(pd.DataFrame(rows).to_string())
