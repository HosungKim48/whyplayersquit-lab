"""Games in the study. Order = fetch order (smallest first)."""
GAMES = [
    dict(appid=1295660, slug="civilization-vii", name="Sid Meier's Civilization VII", genre="4X strategy", release="2025-02-11"),
    dict(appid=949230, slug="cities-skylines-ii", name="Cities: Skylines II", genre="City builder", release="2023-10-24"),
    dict(appid=1272080, slug="payday-3", name="PAYDAY 3", genre="Co-op shooter (live service)", release="2023-09-21"),
    dict(appid=2054970, slug="dragons-dogma-2", name="Dragon's Dogma 2", genre="Action RPG", release="2024-03-22"),
    dict(appid=2246340, slug="monster-hunter-wilds", name="Monster Hunter Wilds", genre="Action / co-op hunting", release="2025-02-28"),
    dict(appid=1716740, slug="starfield", name="Starfield", genre="Single-player RPG", release="2023-09-06"),
]

# ---- Expansion: games that get the free numbers only (behaviour after the review; no model labels).
# In priority order; src/expand.py checks each one against Steam and keeps the first EXPANSION_TARGET that pass.
# "release" is the month to start walking from, set a little before first availability (early access included).
EXPANSION_TARGET = 24
EXPANSION_MAX_REVIEWS = 150_000   # skip anything bigger: one huge game would dominate the fetch
EXPANSION_MIN_REVIEWS = 5_000
CANDIDATES = [
    # well reviewed
    dict(appid=632470, slug="disco-elysium", name="Disco Elysium", genre="Narrative RPG", release="2019-09-01"),
    dict(appid=1336490, slug="against-the-storm", name="Against the Storm", genre="Roguelite city builder", release="2022-09-01"),
    dict(appid=1868140, slug="dave-the-diver", name="DAVE THE DIVER", genre="Adventure / management", release="2022-09-01"),
    dict(appid=1627720, slug="lies-of-p", name="Lies of P", genre="Soulslike action RPG", release="2023-08-01"),
    dict(appid=1888160, slug="armored-core-vi", name="ARMORED CORE VI FIRES OF RUBICON", genre="Mech action", release="2023-07-01"),
    dict(appid=1817230, slug="hi-fi-rush", name="Hi-Fi RUSH", genre="Rhythm action", release="2022-12-01"),
    dict(appid=1562430, slug="dredge", name="DREDGE", genre="Fishing adventure", release="2023-02-01"),
    dict(appid=1363080, slug="manor-lords", name="Manor Lords", genre="City builder / strategy", release="2024-03-01"),
    dict(appid=1771300, slug="kingdom-come-deliverance-ii", name="Kingdom Come: Deliverance II", genre="Open-world RPG", release="2025-01-01"),
    dict(appid=1313140, slug="cult-of-the-lamb", name="Cult of the Lamb", genre="Roguelite / management", release="2022-07-01"),
    dict(appid=2183900, slug="space-marine-2", name="Warhammer 40,000: Space Marine 2", genre="Third-person shooter", release="2024-08-01"),
    dict(appid=2161700, slug="persona-3-reload", name="Persona 3 Reload", genre="JRPG", release="2024-01-01"),
    # mixed or poorly reviewed
    dict(appid=1601580, slug="frostpunk-2", name="Frostpunk 2", genre="City builder / survival", release="2024-08-01"),
    dict(appid=1845910, slug="dragon-age-the-veilguard", name="Dragon Age: The Veilguard", genre="Action RPG", release="2024-09-01"),
    dict(appid=954850, slug="kerbal-space-program-2", name="Kerbal Space Program 2", genre="Space simulation", release="2023-01-01"),
    dict(appid=1294810, slug="redfall", name="Redfall", genre="Co-op shooter", release="2023-04-01"),
    dict(appid=315210, slug="suicide-squad-kill-the-justice-league", name="Suicide Squad: Kill the Justice League", genre="Co-op shooter (live service)", release="2024-01-01"),
    dict(appid=1840080, slug="homeworld-3", name="Homeworld 3", genre="Real-time strategy", release="2024-04-01"),
    dict(appid=1937780, slug="total-war-pharaoh", name="Total War: PHARAOH", genre="Grand strategy", release="2023-09-01"),
    dict(appid=1643320, slug="stalker-2", name="S.T.A.L.K.E.R. 2: Heart of Chornobyl", genre="Open-world shooter", release="2024-10-01"),
    dict(appid=1680880, slug="forspoken", name="Forspoken", genre="Action RPG", release="2022-12-01"),
    dict(appid=2457220, slug="avowed", name="Avowed", genre="First-person RPG", release="2025-01-01"),
    dict(appid=1940340, slug="darkest-dungeon-ii", name="Darkest Dungeon II", genre="Roguelite RPG", release="2023-04-01"),
    dict(appid=2853730, slug="skull-and-bones", name="Skull and Bones", genre="Naval action (live service)", release="2024-07-01"),
    # spares, used only if one above fails the check
    dict(appid=1458140, slug="pacific-drive", name="Pacific Drive", genre="Driving survival", release="2024-01-01"),
    dict(appid=1244090, slug="sea-of-stars", name="Sea of Stars", genre="Turn-based RPG", release="2023-07-01"),
    dict(appid=323190, slug="frostpunk", name="Frostpunk", genre="City builder / survival", release="2018-03-01"),
    dict(appid=2001120, slug="split-fiction", name="Split Fiction", genre="Co-op adventure", release="2025-02-01"),
    dict(appid=534380, slug="dying-light-2", name="Dying Light 2", genre="Open-world action", release="2022-01-01"),
    dict(appid=646570, slug="slay-the-spire", name="Slay the Spire", genre="Roguelike deckbuilder", release="2017-10-01"),
]


def all_games():
    """The six studied games plus every accepted expansion game that already has a local table."""
    import json, os
    root = os.path.join(os.path.dirname(__file__), "..")
    f = os.path.join(root, "data", "public", "expansion_games.json")
    extra = json.load(open(f)) if os.path.exists(f) else []
    return GAMES + [g for g in extra if os.path.exists(os.path.join(root, "data", "work", f"reviews_{g['appid']}.parquet"))]
