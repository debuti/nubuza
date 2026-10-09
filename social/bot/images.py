"""Makes the post image (1080×1350 JPEG, Instagram's 4:5 portrait) in a headless browser."""

import base64
import html
import mimetypes
import random
import re
from pathlib import Path

from PIL import Image

from . import ROOT, SOCIAL, blp

SIZE = {"width": 1080, "height": 1350}


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _render(browser, page_html: str, out: Path, offline: bool = False) -> Path:
    context = browser.new_context(viewport=SIZE)
    if offline:  # model-written SVG: nothing may load from the network
        context.route(re.compile(r"^(?!data:).*"), lambda route: route.abort())
    page = context.new_page()
    page.set_content(page_html, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.screenshot(path=out)
    context.close()
    return out


def frame(browser, image: Path, headline: str, out: Path) -> Path:
    template = (SOCIAL / "templates" / "frame.html").read_text()
    page_html = (template.replace("{{headline}}", html.escape(headline))
                 .replace("{{image}}", _data_uri(image))
                 .replace("{{logo}}", _data_uri(ROOT / "public" / "logo.svg")))
    return _render(browser, page_html, out)


def _safe_svg(svg: str) -> str:
    svg = re.sub(r"<(script|foreignObject)\b.*?</\1\s*>", "", svg, flags=re.S | re.I)
    svg = re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*')", "", svg, flags=re.I)
    return svg


def illustration(browser, svg: str, out: Path) -> Path:
    page_html = ("<!doctype html><style>html,body{margin:0;width:1080px;height:1350px;overflow:hidden;"
                 "background:#fff0f7}svg{display:block;width:1080px;height:1350px}</style>" + _safe_svg(svg))
    return _render(browser, page_html, out, offline=True)


def make(browser, project: dict, post: dict, workdir: Path, rng: random.Random) -> Path:
    """The raw image for the post's media type (PNG)."""
    media = post["media"]
    raw = workdir / f"{media}.png"
    if media == "illustration":
        return illustration(browser, post["svg"], raw)
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
    """Instagram only takes JPEG between 4:5 and 1.91:1; taller images are padded to 4:5."""
    img = Image.open(png).convert("RGB")
    w, h = img.size
    if h > w * 1.25:
        canvas = Image.new("RGB", (round(h * 0.8), h), (255, 240, 247))
        canvas.paste(img, ((canvas.width - w) // 2, 0))
        img = canvas
    img.thumbnail((1080, 1350))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=90, optimize=True)
    return out
