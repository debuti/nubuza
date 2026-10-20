"""calview screenshots: the live app with its settings preloaded.

calview keeps every setting in localStorage, so each scene is just a saved settings object:
no clicking around. The month is one of the next few, so posts show a calendar people can use.
"""

import json
import random
from datetime import date
from pathlib import Path

STORAGE_KEY = "calview.settings.v1"
SCREENS = ("single", "collage", "marks")


def _month(rng: random.Random) -> str:
    today = date.today()
    m = today.month + rng.randint(0, 2)
    return date(today.year + (m - 1) // 12, (m - 1) % 12 + 1, 1).isoformat()


def settings(screen: str, rng: random.Random) -> dict:
    """single = one A4 or A3 sheet; collage = a big calendar split across A4s; marks = the same
    collage with the legend explaining every mark."""
    base = {"lang": "en", "units": "mm", "dateFormat": "ymd", "series": "iso", "weekStart": 1,
            "start": _month(rng), "legend": screen == "marks"}
    if screen == "single":
        return base | {"paper": rng.choice(["A4", "A3"]), "orientation": "portrait", "rows": rng.choice([5, 6]),
                       "collage": False}
    return base | {"paper": rng.choice(["A2", "A1"]), "orientation": "portrait", "rows": rng.choice([9, 13]),
                   "collage": True, "sheetPaper": "A4", "sheetOrientation": "auto"}


def screenshot(browser, url: str, rng: random.Random, out: Path, screen: str | None = None) -> Path:
    """A desktop screenshot of the app: the settings panel on the left, the print preview on the right."""
    screen = screen or rng.choice(SCREENS)
    context = browser.new_context(viewport={"width": 1100, "height": 1250}, device_scale_factor=2, locale="en-US",
                                  reduced_motion="reduce")
    context.route("https://pagead2.googlesyndication.com/**", lambda r: r.abort())  # no ads in our posts
    saved = json.dumps(settings(screen, rng))
    context.add_init_script(f"localStorage.setItem({json.dumps(STORAGE_KEY)}, {json.dumps(saved)})")
    try:
        page = context.new_page()
        page.set_default_timeout(60_000)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=out)
        return out
    finally:
        context.close()
