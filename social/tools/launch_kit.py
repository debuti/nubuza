"""One-off launch kits for the @nubuzacom Instagram, made from the live apps with fictional
demo data and sent to Telegram to publish by hand.

- nubuza (default): welcome post, Bizarre Love Polygon carousel, highlight covers, Reels, X header.
- fivedollars: "Meet 5dollars" post and a how-it-works carousel.
- a-thousand-surnames: "Meet A Thousand Surnames" post and a how-it-works carousel.

    python -m social.tools.launch_kit --out DIR [--project fivedollars|a-thousand-surnames] [--send]

Without --send it only saves the files in DIR, to look at them first.
"""

import argparse
import base64
import json
import os
import random
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

from ..bot import ROOT, blp, fivedollars, images, load_projects, surnames
from ..bot.publish import _check

BLP_URL = "https://bizarre.lovepolygon.com/"
TAGS = "#nubuza #kawaii #cuteapp #webapp #indiedev #pastelaesthetic #privacyfirst #bizarrelovepolygon #lovepolygon #lovemap"

WELCOME = f"""Hi, we're nubuza ☁️🪼

A little cloud of tiny, cute web projects: playful, pastel and private by design 🔒💗

Our first one is Bizarre Love Polygon: pin where you fell for someone and watch your love polygon grow on a pink map 🗺️💕

Follow along for more cute things ✨
.
{TAGS}"""

CAROUSEL = f"""How Bizarre Love Polygon works 💗 (swipe →)

1. Pin where you fell for someone 📍
2. Watch your love polygon grow 🗺️
3. See your love stats ✨
4. Share a cute card, with your spots blurred 📸

No account, no tracking: everything stays encrypted on your device 🔒
💗 bizarre.lovepolygon.com (link in bio)
.
{TAGS} #datinglife #crush"""

REELS = [f"""Watch a love polygon grow, one crush at a time 💗🗺️

Every heart pin is a moment. Connect them and your love life becomes a shape ✨
Make your own timelapse at bizarre.lovepolygon.com (link in bio) 🎬
.
{TAGS} #reels #timelapse""",
         f"""Years of crushes in 30 seconds 😳💞

Bizarre Love Polygon turns your love story into a growing pink polygon. Private, cute and free 🔒✨
🎬 Make yours: bizarre.lovepolygon.com (link in bio)
.
{TAGS} #reels #situationship"""]

STEPS = [("picker", "1. Pin where you fell for someone 📍"), ("map", "2. Watch your love polygon grow 🗺️"),
         ("stats", "3. See your love stats ✨"), ("card", "4. Share your cute card 📸")]

HIGHLIGHTS = [("about", "#cfe6ff", "logo"), ("love-polygon", "#ffd1e6", "polly"),
              ("how-to", "#eadfff", "pin"), ("new", "#c9f2e6", "sparkle")]

PIN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="-14 -40 28 42"><path d="M0 0 C-9 -12 -12 -18 -12 -24
A12 12 0 1 1 12 -24 C12 -18 9 -12 0 0Z" fill="#f0478a" stroke="#d42f72" stroke-width="2"/><path d="M0 -20
C-4 -24 -8 -26 -5 -30 C-3 -32 -1 -31 0 -29 C1 -31 3 -32 5 -30 C8 -26 4 -24 0 -20Z" fill="#fff"/></svg>"""
SPARKLE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M50 4 C55 38 62 45 96 50
C62 55 55 62 50 96 C45 62 38 55 4 50 C38 45 45 38 50 4Z" fill="#ffd966" stroke="#4a3a6b" stroke-width="4"
stroke-linejoin="round"/><circle cx="82" cy="18" r="7" fill="#ff8fbd"/><circle cx="20" cy="84" r="5" fill="#a8e6d9"/></svg>"""


def _uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def _page(browser, html: str, out: Path, size: dict) -> Path:
    context = browser.new_context(viewport=size)
    page = context.new_page()
    page.set_content(html, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.screenshot(path=out)
    context.close()
    return out


FONT = '<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=block" rel="stylesheet">'


def welcome(browser, out: Path, logo: str, cover: str) -> Path:
    html = f"""<!doctype html>{FONT}<style>*{{margin:0;box-sizing:border-box}}
    body{{width:1080px;height:1440px;overflow:hidden;font-family:Fredoka,sans-serif;color:#4a3a6b;
    background:linear-gradient(180deg,#cfe6ff,#fff0f7);display:flex;flex-direction:column;align-items:center;
    padding:90px 70px 70px;text-align:center}}
    .logo{{width:400px;filter:drop-shadow(0 18px 24px rgba(74,58,107,.25))}}
    h1{{font-size:96px;font-weight:600;margin-top:10px}} p{{font-size:44px;margin-top:14px;color:#7a6d96}}
    .photo{{margin-top:70px;background:#fff;padding:18px 18px 26px;border-radius:10px;transform:rotate(-2deg);
    box-shadow:0 20px 50px rgba(74,58,107,.22)}} .photo img{{width:560px;display:block;border-radius:4px}}
    .photo span{{display:block;font-size:30px;font-weight:600;margin-top:12px}}</style>
    <img class="logo" src="{logo}"><h1>Hi, we're nubuza</h1><p>a little cloud of tiny, cute projects</p>
    <div class="photo"><img src="{cover}"><span>first project: Bizarre Love Polygon 💗</span></div>"""
    return _page(browser, html, out, images.SIZE)


def carousel_cover(browser, out: Path, polly: str) -> Path:
    html = f"""<!doctype html>{FONT}<style>*{{margin:0;box-sizing:border-box}}
    body{{width:1080px;height:1440px;overflow:hidden;font-family:Fredoka,sans-serif;color:#4a3a6b;
    background:linear-gradient(180deg,#ffe3f0,#ffd1e6);display:flex;flex-direction:column;align-items:center;
    justify-content:center;text-align:center;padding:80px}}
    img{{width:520px;filter:drop-shadow(0 22px 26px rgba(212,47,114,.3))}}
    h1{{font-size:104px;line-height:1.05;margin-top:40px;font-weight:600}} p{{font-size:46px;margin-top:30px;color:#a0457a}}
    </style><img src="{polly}"><h1>How Bizarre Love Polygon works</h1><p>swipe →</p>"""
    return _page(browser, html, out, images.SIZE)


def x_header(browser, out: Path, logo: str) -> Path:
    """1500×500 X header. The avatar covers the bottom left and phones crop the edges, so the
    content sits in the middle-right."""
    puffs = "".join(f'<i style="width:{w}px;height:{w // 3}px;left:{x}px;top:{y}px"></i>'
                    for w, x, y in [(220, 40, 70), (170, 330, 330), (260, 1210, 380), (190, 1290, 60), (150, 560, 40)])
    html = f"""<!doctype html>{FONT}<style>*{{margin:0;box-sizing:border-box}}
    body{{width:1500px;height:500px;overflow:hidden;font-family:Fredoka,sans-serif;color:#4a3a6b;position:relative;
    background:linear-gradient(100deg,#cfe6ff 0%,#e6dcff 55%,#ffe0ee 100%)}}
    i{{position:absolute;background:rgba(255,255,255,.85);border-radius:999px}}
    i::before,i::after{{content:"";position:absolute;background:inherit;border-radius:50%}}
    i::before{{width:45%;height:140%;left:14%;top:-65%}} i::after{{width:34%;height:105%;left:50%;top:-45%}}
    .c{{position:absolute;left:620px;top:50%;transform:translateY(-50%);display:flex;align-items:center;gap:36px}}
    .c img{{width:230px;filter:drop-shadow(0 14px 18px rgba(74,58,107,.25))}}
    h1{{font-size:110px;font-weight:600;line-height:1}} p{{font-size:38px;margin-top:10px;color:#7a6d96}}
    .s{{position:absolute;font-size:44px;color:#ff8fbd}}</style>{puffs}
    <span class="s" style="left:540px;top:90px">✦</span><span class="s" style="left:1400px;top:250px;color:#b79cff">✦</span>
    <span class="s" style="left:880px;top:410px;color:#7fd8be;font-size:34px">✦</span>
    <div class="c"><img src="{logo}"><div><h1>nubuza</h1><p>tiny, cute web projects</p></div></div>"""
    return _page(browser, html, out, {"width": 1500, "height": 500})


def highlight(browser, out: Path, bg: str, icon: str) -> Path:
    html = f"""<!doctype html><style>*{{margin:0}} body{{width:1080px;height:1920px;overflow:hidden;
    background:radial-gradient(circle at 50% 50%,#fff 0,{bg} 60%);display:flex;align-items:center;justify-content:center}}
    div{{width:620px;height:620px;border-radius:50%;background:#fff;display:flex;align-items:center;
    justify-content:center;box-shadow:0 18px 40px rgba(74,58,107,.18)}} img{{width:400px;max-height:420px}}</style>
    <div><img src="{icon}"></div>"""
    return _page(browser, html, out, {"width": 1080, "height": 1920})


class Telegram:
    def __init__(self):
        self.api = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}"
        self.chat = os.environ["TELEGRAM_CHAT_ID"]

    def call(self, method: str, data: dict | None = None, files: dict | None = None) -> dict:
        return _check(requests.post(f"{self.api}/{method}", data={"chat_id": self.chat, **(data or {})},
                                    files=files, timeout=300))

    def text(self, text: str) -> None:
        self.call("sendMessage", {"text": text})

    def doc(self, path: Path, caption: str = "") -> None:
        self.call("sendDocument", {"caption": caption}, {"document": (path.name, path.read_bytes())})

    def docs(self, paths: list[Path]) -> None:
        media = [{"type": "document", "media": f"attach://f{i}"} for i in range(len(paths))]
        self.call("sendMediaGroup", {"media": json.dumps(media)},
                  {f"f{i}": (p.name, p.read_bytes()) for i, p in enumerate(paths)})

    def video(self, path: Path, caption: str = "") -> None:
        self.call("sendVideo", {"caption": caption, "supports_streaming": "true"},
                  {"video": (path.name, path.read_bytes(), "video/mp4")})


def build(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random()
    project = next(p for p in load_projects() if p["id"] == "bizarre-love-polygon")
    logo = images._data_uri(ROOT / "public" / "logo.svg")
    cover = images._data_uri(ROOT / project["cover"])
    polly = _uri(requests.get(BLP_URL + "favicon.svg", timeout=30).text)
    kit = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        kit["welcome"] = images.to_jpeg(welcome(browser, out / "welcome.png", logo, cover), out / "1-welcome.jpg")

        lovers = blp.random_lovers(rng)
        shots = blp.phone_shots(browser, BLP_URL, lovers, rng, out)
        shots["card"] = blp.card(browser, BLP_URL, lovers, rng, out / "card.png")
        slides = [carousel_cover(browser, out / "slide-0.png", polly)]
        slides += [images.frame(browser, shots[name], title, out / f"slide-{i + 1}.png")
                   for i, (name, title) in enumerate(STEPS)]
        kit["carousel"] = [images.to_jpeg(s, out / f"2-carousel-{i + 1}.jpg") for i, s in enumerate(slides)]

        icons = {"logo": logo, "polly": polly, "pin": _uri(PIN), "sparkle": _uri(SPARKLE)}
        kit["highlights"] = [highlight(browser, out / f"3-highlight-{name}.png", bg, icons[icon])
                             for name, bg, icon in HIGHLIGHTS]

        kit["x_header"] = x_header(browser, out / "5-x-header.png", logo)

        kit["reels"] = []
        for i in range(len(REELS)):
            demo = []
            while len(demo) < 5:  # longer stories make better timelapses
                demo = blp.random_lovers(rng)
            kit["reels"].append(blp.timelapse(browser, BLP_URL, demo, rng, out / f"4-reel-{i + 1}"))
        browser.close()
    return kit


def send(kit: dict) -> None:
    tg = Telegram()
    tg.text("🚀 Kit de lanzamiento de @nubuzacom\n\nPublícalo poco a poco: un post cada día o dos, en este orden. "
            "Fija en tu perfil la bienvenida y el carrusel (… → Fijar en tu perfil).")
    tg.text("1️⃣ POST DE BIENVENIDA. Publícalo el primero y fíjalo.")
    tg.doc(kit["welcome"])
    tg.text(WELCOME)
    tg.text("2️⃣ CARRUSEL «cómo funciona». Al publicar, selecciona varias fotos en este orden (1 → 5) y fíjalo.")
    tg.docs(kit["carousel"])
    tg.text(CAROUSEL)
    for i, (reel, caption) in enumerate(zip(kit["reels"], REELS), 3):
        tg.text(f"{i}️⃣ REEL {i - 2}. Publícalo como Reel (+ → Reel) con este texto. Si Instagram ofrece música, "
                "algo suave y alegre queda genial.")
        tg.video(reel)
        tg.text(caption)
    tg.text("✨ PORTADAS DE HISTORIAS DESTACADAS: Sobre nosotros, Love Polygon, Cómo funciona, Novedades.\n\n"
            "Para cada una: sube una historia (puede ser la propia portada), pulsa «Destacar», ponle nombre "
            "(About, Love Polygon, How to, New) y en «Editar portada» elige esta imagen.")
    tg.docs(kit["highlights"])
    tg.text("🐦 CABECERA DE X (@nubuzacom): Perfil → Editar perfil → toca la imagen de cabecera → elige esta. "
            "Para la foto de perfil de X usa el mismo logo que en Instagram.")
    tg.doc(kit["x_header"])
    tg.text("¡Listo! En los próximos días te llegarán también algunos posts extra del bot 💗")


FD_URL = "https://apps.nubuza.com/fivedollars/"
FD_TAGS = "#nubuza #5dollars #personalfinance #budgeting #budgetapp #savingmoney #familybudget #privacyfirst #cuteapp #webapp"
FD_MEET = f"""Meet 5dollars 💚🪙

Our new little project: a private ledger for your household. Import your bank statements, \
categorise them in seconds and see every month whether you saved or spent more than you earned 📊✨

No account and no server: your ledger is a file that lives in your Google Drive, a folder or your browser 🔒
💚 apps.nubuza.com/fivedollars (link in bio)
.
{FD_TAGS}"""
FD_CAROUSEL = f"""How 5dollars works 💚 (swipe →)

1. Choose where your ledger lives: Drive, a folder or your browser 🔒
2. Import your statements and categorise every move ✨
3. See if you saved each month 📊
4. Know why a month went off 🔔
5. Give trips their own budget ✈️

All the numbers in these screenshots are made up: 5dollars never sees yours 💚
💚 apps.nubuza.com/fivedollars (link in bio)
.
{FD_TAGS} #moneytips"""
FD_STEPS = [("welcome", "1. Your data stays yours 🔒"), ("categories", "2. Categorise every move ✨"),
            ("report", "3. Did you save this month? 📊"), ("alerts", "4. Know why a month went off 🔔"),
            ("epic", "5. Trips get their own budget ✈️")]


def fd_cover(browser, out: Path, art: str, title: str = "How 5dollars works",
             bg: str = "#e8f8ef,#cdeedd", accent: str = "#1f7a52") -> Path:
    html = f"""<!doctype html>{FONT}<style>*{{margin:0;box-sizing:border-box}}
    body{{width:1080px;height:1440px;overflow:hidden;font-family:Fredoka,sans-serif;color:#4a3a6b;
    background:linear-gradient(180deg,{bg});display:flex;flex-direction:column;align-items:center;
    justify-content:center;text-align:center;padding:80px}}
    img{{width:760px;border-radius:28px;box-shadow:0 22px 40px rgba(31,122,82,.25)}}
    h1{{font-size:110px;line-height:1.05;margin-top:60px;font-weight:600}} p{{font-size:46px;margin-top:26px;color:{accent}}}
    </style><img src="{art}"><h1>{title}</h1><p>swipe →</p>"""
    return _page(browser, html, out, images.SIZE)


def build_fivedollars(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random()
    project = next(p for p in load_projects() if p["id"] == "fivedollars")
    cover = ROOT / project["cover"]
    kit = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        kit["meet"] = images.to_jpeg(images.frame(browser, cover, "Meet 5dollars 💚", out / "meet.png"), out / "1-meet.jpg")
        slides = [fd_cover(browser, out / "fd-slide-0.png", images._data_uri(cover))]
        for i, (screen, title) in enumerate(FD_STEPS, 1):
            shot = fivedollars.screenshot(browser, FD_URL, rng, out / f"fd-{screen}.png", screen)
            slides.append(images.frame(browser, shot, title, out / f"fd-slide-{i}.png"))
        kit["carousel"] = [images.to_jpeg(s, out / f"2-carousel-{i + 1}.jpg") for i, s in enumerate(slides)]
        browser.close()
    return kit


def send_fivedollars(kit: dict) -> None:
    tg = Telegram()
    tg.text("🪙 Kit de lanzamiento de 5dollars para @nubuzacom\n\nPublícalo poco a poco (un post cada día o dos), "
            "intercalado con los de Bizarre Love Polygon.")
    tg.text("1️⃣ PRESENTACIÓN «Meet 5dollars». Publícala primero.")
    tg.doc(kit["meet"])
    tg.text(FD_MEET)
    tg.text("2️⃣ CARRUSEL «How 5dollars works». Selecciona las 6 fotos en orden (1 → 6). Puedes fijarlo en lugar "
            "de alguno de Love Polygon (Instagram deja fijar 3).")
    tg.docs(kit["carousel"])
    tg.text(FD_CAROUSEL)


ATS_URL = "https://apps.nubuza.com/a-thousand-surnames/"
ATS_TAGS = ("#nubuza #athousandsurnames #surnames #apellidos #genealogy #familytree #familyhistory #genealogia "
            "#spanishsurnames #cuteapp")
ATS_MEET = f"""Meet A Thousand Surnames 🌳🏷️

Your ID shows two surnames, but your family tree hides many more. Import your tree from Ancestry or \
MyHeritage, or build it by hand, and get every surname you carry, in order, with how rare each one is in Spain ✨

Free, no sign-up, and your tree never leaves your device 🔒
🌳 apps.nubuza.com/a-thousand-surnames (link in bio)
.
{ATS_TAGS}"""
ATS_CAROUSEL = f"""How A Thousand Surnames works 🌳 (swipe →)

1. Import your tree or build it by hand 📂
2. Get every surname you carry, in order 🔤
3. See your family as a fan chart 🌀
4. Stats, trophies and how rare you are 🏆
5. Share your surname card 💌

Everyone in these screenshots is made up: your tree stays encrypted on your device 🔒
🌳 apps.nubuza.com/a-thousand-surnames (link in bio)
.
{ATS_TAGS} #ancestry #myheritage"""
ATS_STEPS = [("start", "1. Import or build your tree 📂"), ("surnames", "2. Every surname, in order 🔤"),
             ("tree", "3. Your family as a fan 🌀"), ("stats", "4. Stats, trophies, rarity 🏆"),
             ("card", "5. A cute card to share 💌")]


def build_surnames(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random()
    project = next(p for p in load_projects() if p["id"] == "a-thousand-surnames")
    cover = ROOT / project["cover"]
    kit = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        kit["meet"] = images.to_jpeg(images.frame(browser, cover, "Meet A Thousand Surnames", out / "meet.png"),
                                     out / "1-meet.jpg")
        slides = [fd_cover(browser, out / "ats-slide-0.png", images._data_uri(cover),
                           "How A Thousand Surnames works", "#e3f6ec,#fde6e1", "#c0392b")]
        for i, (screen, title) in enumerate(ATS_STEPS, 1):
            if screen == "card":
                shot = surnames.card(browser, ATS_URL, rng, out / "ats-card.png", "list")
            else:
                shot = surnames.screenshot(browser, ATS_URL, rng, out / f"ats-{screen}.png", screen)
            slides.append(images.frame(browser, shot, title, out / f"ats-slide-{i}.png"))
        kit["carousel"] = [images.to_jpeg(s, out / f"2-carousel-{i + 1}.jpg") for i, s in enumerate(slides)]
        browser.close()
    return kit


def send_surnames(kit: dict) -> None:
    tg = Telegram()
    tg.text("🌳 Kit de lanzamiento de A Thousand Surnames para @nubuzacom\n\nPublícalo poco a poco (un post cada "
            "día o dos), intercalado con los de los otros proyectos.")
    tg.text("1️⃣ PRESENTACIÓN «Meet A Thousand Surnames». Publícala primero.")
    tg.doc(kit["meet"])
    tg.text(ATS_MEET)
    tg.text("2️⃣ CARRUSEL «How A Thousand Surnames works». Selecciona las 6 fotos en orden (1 → 6). Puedes fijarlo "
            "en lugar de alguno de los otros (Instagram deja fijar 3).")
    tg.docs(kit["carousel"])
    tg.text(ATS_CAROUSEL)


KITS = {"nubuza": (build, send), "fivedollars": (build_fivedollars, send_fivedollars),
        "a-thousand-surnames": (build_surnames, send_surnames)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--project", choices=list(KITS), default="nubuza")
    ap.add_argument("--send", action="store_true")
    args = ap.parse_args()
    make, send_kit = KITS[args.project]
    kit = make(args.out)
    print(json.dumps({k: [str(p) for p in v] if isinstance(v, list) else str(v) for k, v in kit.items()}, indent=1))
    if args.send:
        send_kit(kit)
        print("sent to Telegram")


if __name__ == "__main__":
    main()
