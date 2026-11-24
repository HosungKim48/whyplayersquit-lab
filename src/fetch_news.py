"""Fetch official developer announcements / patch notes (Steam news API) per game. One request each, cached."""
import json, os, time
import requests
from games import GAMES

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "news"); os.makedirs(OUT, exist_ok=True)
for g in GAMES:
    f = os.path.join(OUT, f"{g['appid']}.json")
    if os.path.exists(f): continue
    r = requests.get("https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/",
                     params=dict(appid=g["appid"], count=1000, maxlength=400, feeds="steam_community_announcements"), timeout=40)
    r.raise_for_status(); json.dump(r.json(), open(f, "w")); time.sleep(2)
    items = r.json()["appnews"]["newsitems"]
    print(g["name"], len(items), "announcements")
