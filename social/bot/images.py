"""Makes the post image (1080×1440 JPEG, the 3:4 portrait Instagram's grid shows) in a headless browser."""

import base64
import html
import mimetypes
import random
import re
from pathlib import Path

from PIL import Image

from . import ROOT, SOCIAL, blp

SIZE = {"width": 1080, "height": 1440}
RATIO = SIZE["width"] / SIZE["height"]


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _render(browser, page_html: str, out: Path, offline: bool = False, size: dict = SIZE,
            check: str | None = None) -> Path:
    context = browser.new_context(viewport=size)
    if offline:  # model-written SVG: nothing may load from the network
        context.route(re.compile(r"^(?!data:).*"), lambda route: route.abort())
    page = context.new_page()
    page.set_content(page_html, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    if check:  # e.g. an SVG without a size draws as an empty box: never post that
        box = page.locator(check).bounding_box()
        if not box or box["width"] < 300 or box["height"] < 200:
            context.close()
            raise RuntimeError(f"{check} rendered too small: {box}")
    page.screenshot(path=out)
    context.close()
    return out


def frame(browser, image: Path, headline: str, out: Path) -> Path:
    template = (SOCIAL / "templates" / "frame.html").read_text()
    page_html = (template.replace("{{headline}}", html.escape(headline))
                 .replace("{{image}}", _data_uri(image))
                 .replace("{{logo}}", _data_uri(ROOT / "public" / "logo.svg")))
    return _render(browser, page_html, out, check=".photo img")


def _safe_svg(svg: str) -> str:
    svg = re.sub(r"<(script|foreignObject)\b.*?</\1\s*>", "", svg, flags=re.S | re.I)
    svg = re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*')", "", svg, flags=re.I)
    return svg


def illustration(browser, svg: str, out: Path) -> Path:
    page_html = ("<!doctype html><style>html,body{margin:0;width:1000px;height:1000px;overflow:hidden;"
                 "background:#fff0f7}svg{display:block;width:1000px;height:1000px}</style>" + _safe_svg(svg))
    return _render(browser, page_html, out, offline=True, size={"width": 1000, "height": 1000})


def make(browser, project: dict, post: dict, workdir: Path, rng: random.Random) -> Path:
    """The raw image for the post's media type (PNG)."""
    media = post["media"]
    raw = workdir / f"{media}.png"
    if media == "illustration":
        art = illustration(browser, post["svg"], workdir / "art.png")
        return frame(browser, art, post["headline"], raw)
    if media == "cover":
        return frame(browser, ROOT / project["cover"], post["headline"], raw)
    if project.get("exporter") == "bizarre-love-polygon":
        lovers = post["lovers"] or blp.random_lovers(rng)
        if media == "card":
            return blp.card(browser, project["url"], lovers, rng, raw)
        shot = blp.screenshot(browser, project["url"], lovers, rng, workdir / "shot.png")
        return frame(browser, shot, post["headline"], raw)
    if media == "screenshot":
        context = browser.new_context(viewport={"width": 390, "height": 760}, device_scale_factor=2)
        page = context.new_page()
        page.goto(project["url"], wait_until="networkidle")
        page.screenshot(path=workdir / "shot.png")
        context.close()
        return frame(browser, workdir / "shot.png", post["headline"], raw)
    raise ValueError(f"{project['id']} can't make {media} images")


def to_jpeg(png: Path, out: Path) -> Path:
    """Saves as a 1080×1440 (3:4) JPEG. Other shapes (the app's 4:5 card, with rounded transparent
    corners) are centred on a gradient of their own top and bottom colours, so the padding blends in."""
    img = Image.open(png).convert("RGBA")
    w, h = img.size
    if abs(w / h - RATIO) > 0.01:
        size = (w, round(w / RATIO)) if w / h > RATIO else (round(h * RATIO), h)
        top, bottom = img.getpixel((w // 2, 2))[:3], img.getpixel((w // 2, h - 3))[:3]
        canvas = Image.new("RGB", size)
        for y in range(size[1]):
            t = y / (size[1] - 1)
            canvas.paste(tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)), (0, y, size[0], y + 1))
        canvas.paste(img, ((size[0] - w) // 2, (size[1] - h) // 2), img)
        img = canvas
    img = img.convert("RGB").resize((SIZE["width"], SIZE["height"]), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=92, optimize=True)
    return out
