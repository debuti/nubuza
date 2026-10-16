"""Bizarre Love Polygon exports: drives the live app with a fictional demo user.

The app keeps everything encrypted on the device, so the demo data goes in the way a
user's would: as an encrypted backup file restored from Settings. The backup format
mirrors bizarre-love-polygon's src/lib/data/crypto.ts (PBKDF2-SHA256 + AES-256-GCM).
"""

import base64
import json
import os
import random
import tempfile
import time
import uuid
from datetime import date, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PASSPHRASE = "nubuza-demo-passphrase"
ITERATIONS = 100_000  # the app's minimum: quick to restore in CI
AAD = b"bizarre-love-polygon/backup/v1"
PALETTE = ["#ff8fb8", "#ff5fa2", "#ffb38a", "#ffd966", "#7fd8be", "#7ec8ff", "#b79cff", "#e39bff",
           "#ff7f7f", "#e8a0a0"]
THEMES = ["pink", "lilac", "mint", "peach", "sky", "night"]  # share card colours
TYPES = ["crush", "first_date", "kiss", "fling", "situationship", "relationship", "complicated", "other"]

# Used when Claude didn't supply a scenario.
CITIES = [("Paris", 48.8566, 2.3522), ("Lisbon", 38.7223, -9.1393), ("Berlin", 52.52, 13.405),
          ("Tokyo", 35.6762, 139.6503), ("New York", 40.7128, -74.006), ("Rome", 41.9028, 12.4964),
          ("Barcelona", 41.3874, 2.1686), ("Seoul", 37.5665, 126.978), ("Mexico City", 19.4326, -99.1332),
          ("Buenos Aires", -34.6037, -58.3816), ("Sydney", -33.8688, 151.2093), ("Cape Town", -33.9249, 18.4241),
          ("Amsterdam", 52.3676, 4.9041), ("Istanbul", 41.0082, 28.9784), ("Bangkok", 13.7563, 100.5018),
          ("Reykjavik", 64.1466, -21.9426), ("Montreal", 45.5019, -73.5674), ("Madrid", 40.4168, -3.7038)]
NICKNAMES = ["Dimples", "Surfer", "Barista", "Bookworm", "Mr Umbrella", "Glitter", "Sleepy", "Captain",
             "Freckles", "DJ", "Painter", "Cupcake", "Skater", "Poet", "Gamer", "Sunny", "Biscuit", "Pilot"]
EMOJIS = ["💘", "💖", "💕", "💋", "🌹", "🔥", "🦋", "🌈", "⭐", "🍒", "🍓", "🧁", "🐱", "🦊", "🌸", "☕", "🎸", "🏄"]


def random_lovers(rng: random.Random) -> list[dict]:
    lovers = []
    start = date.today() - timedelta(days=rng.randrange(900, 2500))
    for (city, lat, lng), nick in zip(rng.sample(CITIES, rng.randint(3, 6)), rng.sample(NICKNAMES, 6)):
        start += timedelta(days=rng.randrange(30, 300))
        lovers.append({"nickname": nick, "emoji": rng.choice(EMOJIS), "city": city,
                       "lat": lat + rng.uniform(-0.03, 0.03), "lng": lng + rng.uniform(-0.03, 0.03),
                       "from": start.isoformat(), "to": (start + timedelta(days=rng.randrange(1, 120))).isoformat(),
                       "type": rng.choice(TYPES)})
    return lovers


def _clean(lovers: list[dict], rng: random.Random) -> list[dict]:
    """Keeps only lovers the app's schema accepts; falls back to random ones."""
    ok = []
    for lv in lovers[:7]:
        try:
            lv = {**lv, "to": lv.get("to") or None}  # Claude sends "" for "still going"
            date.fromisoformat(lv["from"])
            if lv["to"] is not None:
                date.fromisoformat(lv["to"])
            assert -90 <= lv["lat"] <= 90 and -180 <= lv["lng"] <= 180
            assert 1 <= len(lv["nickname"].strip()) <= 40 and 1 <= len(lv["emoji"]) <= 16
            assert lv["type"] in TYPES
            ok.append(lv)
        except (KeyError, ValueError, AssertionError, TypeError):
            continue
    return ok if len(ok) >= 3 else random_lovers(rng)


def backup(lovers: list[dict], rng: random.Random) -> str:
    now = int(time.time() * 1000)
    data = {
        "version": 1,
        "settings": {"locale": "en", "loverWord": "lovers", "ageConfirmed": True, "tourSeen": True,
                     "theme": rng.choice(THEMES)},
        "lovers": [{
            "id": uuid.uuid4().hex, "nickname": lv["nickname"].strip(), "emoji": lv["emoji"],
            "color": PALETTE[i % len(PALETTE)], "type": lv["type"], "gender": "unspecified",
            "encounters": [{"id": uuid.uuid4().hex, "lat": lv["lat"], "lng": lv["lng"], "from": lv["from"],
                            "to": lv["to"], "place": lv["city"][:80]}],
            "createdAt": now, "updatedAt": now,
        } for i, lv in enumerate(_clean(lovers, rng))],
    }
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS) \
        .derive(PASSPHRASE.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(data).encode(), AAD)
    b64 = lambda b: base64.b64encode(b).decode()
    return json.dumps({"app": "bizarre-love-polygon", "kind": "backup", "v": 1,
                       "kdf": {"name": "PBKDF2-SHA256", "iterations": ITERATIONS, "salt": b64(salt)},
                       "cipher": {"name": "AES-256-GCM", "iv": b64(iv)}, "data": b64(ct)})


def _dismiss(page) -> None:
    """Closes whatever the app pops up on its own: the welcome tour, achievement celebrations…"""
    page.wait_for_timeout(1500)
    for _ in range(6):
        if page.get_by_test_id("tour-skip").is_visible():
            page.get_by_test_id("tour-skip").click()
        elif page.locator("dialog[open]").count():
            page.keyboard.press("Escape")
        else:
            return
        page.wait_for_timeout(500)


def _open_with_demo(browser, url: str, lovers: list[dict], rng: random.Random, viewport: dict):
    context = browser.new_context(viewport=viewport, device_scale_factor=2, locale="en-US",
                                  accept_downloads=True, is_mobile=viewport["width"] < 600, has_touch=True,
                                  reduced_motion="reduce")  # steady buttons and settled pins
    page = context.new_page()
    page.set_default_timeout(60_000)
    page.goto(url)
    page.get_by_test_id("age-yes").click()
    _dismiss(page)
    page.get_by_test_id("open-settings").click()
    settings = page.get_by_test_id("settings")
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "demo.blp"
        f.write_text(backup(lovers, rng))
        settings.locator("input[type=file][accept*=blp]").set_input_files(f)
    settings.get_by_label("Backup passphrase").fill(PASSPHRASE)
    settings.locator("form button[type=submit]").click()
    page.get_by_test_id("confirm-yes").click()
    settings.get_by_role("status").wait_for()
    page.keyboard.press("Escape")
    settings.wait_for(state="hidden")
    _dismiss(page)
    return context, page


def card(browser, url: str, lovers: list[dict], rng: random.Random, out: Path) -> Path:
    """The app's Instagram post card for the demo user (1080×1350; to_jpeg extends it to 3:4)."""
    context, page = _open_with_demo(browser, url, lovers, rng, {"width": 1280, "height": 900})
    try:
        page.get_by_test_id("open-share").click()
        share = page.get_by_test_id("share")
        post = share.get_by_test_id("format-post")
        (post if post.count() else share.get_by_role("button", name="Post")).click()
        share.locator(".preview[aria-busy=false]").wait_for(timeout=90_000)
        page.wait_for_function("() => !document.querySelector('[data-testid=card-preview].dim')")
        with page.expect_download() as dl:
            page.get_by_test_id("card-download").click()
        dl.value.save_as(out)
        return out
    finally:
        context.close()


def screenshot(browser, url: str, lovers: list[dict], rng: random.Random, out: Path) -> Path:
    """A phone screenshot of the demo user's map."""
    context, page = _open_with_demo(browser, url, lovers, rng, {"width": 390, "height": 760})
    try:
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)  # let tiles and pin animations settle
        page.screenshot(path=out)
        return out
    finally:
        context.close()


def phone_shots(browser, url: str, lovers: list[dict], rng: random.Random, outdir: Path) -> dict[str, Path]:
    """Phone screenshots of the demo user's map, stats and the add-a-pin picker."""
    context, page = _open_with_demo(browser, url, lovers, rng, {"width": 390, "height": 760})
    shots = {name: outdir / f"phone-{name}.png" for name in ("map", "stats", "picker")}
    try:
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        page.screenshot(path=shots["map"])
        page.get_by_test_id("add").click(force=True)
        page.get_by_test_id("picker").wait_for()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=shots["picker"])
        page.reload()  # leaves the picker; the demo data stays on the device
        page.get_by_test_id("open-settings").wait_for()
        _dismiss(page)
        page.get_by_test_id("tab-stats").click()
        page.get_by_test_id("stats").wait_for()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=shots["stats"])
        return shots
    finally:
        context.close()


def timelapse(browser, url: str, lovers: list[dict], rng: random.Random, out: Path) -> Path:
    """The app's timelapse video of the demo user's polygon growing (mp4 or webm, as encoded)."""
    context, page = _open_with_demo(browser, url, lovers, rng, {"width": 1280, "height": 900})
    try:
        page.get_by_test_id("open-share").click()
        share = page.get_by_test_id("share")
        share.get_by_test_id("kind-video").click()
        create = page.get_by_test_id("timelapse-create")
        page.wait_for_function("() => !document.querySelector('[data-testid=timelapse-create]')?.disabled",
                               timeout=120_000)
        create.click()
        download = page.get_by_test_id("timelapse-download")
        download.wait_for(timeout=600_000)  # encoding happens in the page, frame by frame
        with page.expect_download(timeout=60_000) as dl:
            download.click()
        path = out.with_suffix(Path(dl.value.suggested_filename).suffix or ".webm")
        dl.value.save_as(path)
        return path
    finally:
        context.close()
