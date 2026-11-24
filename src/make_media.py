"""Screenshots and a short walkthrough GIF of the built site (docs/media/), taken with a headless browser from the local files."""
import os, sys
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
M = os.path.join(ROOT, "docs", "media"); os.makedirs(M, exist_ok=True)
base = "file://" + os.path.join(ROOT, "docs")
shots = [("index.html", 0), ("index.html", 1500), ("games/monster-hunter-wilds.html", 0), ("games/monster-hunter-wilds.html", 900), ("games/monster-hunter-wilds.html", 3300),
         ("games/civilization-vii.html", 2000), ("case-study.html", 0), ("case-study.html", 800)]
frames = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport=dict(width=1280, height=800), color_scheme="light")
    for i, (path, y) in enumerate(shots):
        pg.goto(f"{base}/{path}"); pg.evaluate(f"window.scrollTo(0,{y})"); pg.wait_for_timeout(250)
        f = os.path.join(M, f"frame_{i}.png"); pg.screenshot(path=f); frames.append(Image.open(f).convert("RGB").resize((960, 600), Image.LANCZOS))
        if i == 0: Image.open(f).convert("RGB").save(os.path.join(M, "overview.png"), optimize=True)
        if i == 3: Image.open(f).convert("RGB").save(os.path.join(M, "report.png"), optimize=True)
        os.remove(f)
    b.close()
pal = [fr.quantize(colors=128, method=Image.MEDIANCUT) for fr in frames]
pal[0].save(os.path.join(M, "walkthrough.gif"), save_all=True, append_images=pal[1:], duration=2200, loop=0, optimize=True)
print({f: os.path.getsize(os.path.join(M, f)) // 1024 for f in os.listdir(M)})
