"""A Thousand Surnames screenshots: drives the live app with a fictional family.

The app keeps the tree encrypted in the browser, so the demo family goes in the way a user's
would: as a GEDCOM file imported from the start screen. The people are made up (common given
names, real surnames at random); the surname order and the INE stats come from the app itself.
"""

import random
import tempfile
from pathlib import Path

MEN = ["Manuel", "José", "Antonio", "Francisco", "Juan", "Pedro", "Javier", "Luis", "Miguel", "Carlos",
       "Ignacio", "Andrés", "Ramón", "Tomás", "Mikel", "Iñaki", "Jon", "Patxi", "Xabier", "Joseba", "Pablo",
       "Alberto", "Fermín", "Julián", "Vicente", "Agustín"]
WOMEN = ["María", "Carmen", "Josefa", "Isabel", "Dolores", "Pilar", "Teresa", "Ana", "Rosario", "Juana",
         "Lucía", "Elena", "Begoña", "Amaia", "Itziar", "Nerea", "Ainhoa", "Maite", "Mercedes", "Concepción",
         "Rosa", "Encarnación", "Paula", "Marta", "Inés", "Clara"]
COMMON = ["García", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Fernández", "Ruiz", "Díaz", "Moreno",
          "Muñoz", "Romero", "Navarro", "Torres", "Gil", "Serrano", "Molina", "Ortega", "Castro", "Herrera",
          "Vidal", "Prieto", "Medina", "Cano", "Rubio", "Marín", "Iglesias", "Soler", "Delgado", "Pascual",
          "Sanz", "Ramos", "Blanco", "Morales", "Ortiz", "Lozano", "Cabello", "Arévalo", "Toribio", "Calvo"]
BASQUE = ["Etxeberria", "Goikoetxea", "Zubizarreta", "Agirre", "Arrieta", "Urrutia", "Elizondo", "Iturralde",
          "Larrañaga", "Mendizábal", "Garmendia", "Aranburu", "Uriarte", "Olano", "Lizarraga", "Zabala",
          "Arregi", "Ibarra", "Basterretxea", "Etxebarria", "Madariaga", "Ugalde", "Arrizabalaga", "Otxoa"]
RARE = ["Ximénez", "Albornoz", "Zurbano", "Villalobos", "Quintanilla", "Sotomayor", "Cifuentes", "Bustamante",
        "Arteaga", "Valdivieso", "Ponce de León", "Mondragón", "Peñalosa", "Echenique"]


def random_family(rng: random.Random) -> tuple[dict[int, dict], str]:
    """A made-up root person and their ancestors, by Ahnentafel number (1 = root, 2n = father,
    2n + 1 = mother), plus the same family as GEDCOM. Deeper generations have more gaps."""
    depth = rng.choice([4, 5, 5])
    basque = rng.choice([0.0, 0.2, 0.4, 0.6])
    keep = [1, 1, 1, 0.9, 0.75, 0.6]

    def surname() -> str:
        r = rng.random()
        return rng.choice(BASQUE if r < basque else RARE if r < basque + 0.08 else COMMON)

    people = {1: {}}
    for n in range(2, 2 ** (depth + 1)):
        if n // 2 in people and rng.random() < keep[n.bit_length() - 1]:
            people[n] = {}
    # Surnames flow down: your 1st is your father's 1st, your 2nd your mother's 1st.
    for n in sorted(people, reverse=True):
        p = people[n]
        p["s1"] = people[2 * n]["s1"] if 2 * n in people else surname()
        p["s2"] = people[2 * n + 1]["s1"] if 2 * n + 1 in people else surname()
        male = n % 2 == 0 if n > 1 else rng.random() < 0.5
        p["sex"] = "M" if male else "F"
        p["given"] = rng.choice(MEN if male else WOMEN)
        p["year"] = rng.randint(1992, 2004) - sum(rng.randint(24, 34) for _ in range(n.bit_length() - 1))

    lines = ["0 HEAD", "1 SOUR nubuza-demo", "1 GEDC", "2 VERS 5.5.1", "2 FORM LINEAGE-LINKED", "1 CHAR UTF-8"]
    for n, p in people.items():
        lines += [f"0 @I{n}@ INDI", f"1 NAME {p['given']} /{p['s1']} {p['s2']}/", f"2 GIVN {p['given']}",
                  f"2 SURN {p['s1']} {p['s2']}", f"1 SEX {p['sex']}", "1 BIRT", f"2 DATE {p['year']}"]
        if 2 * n in people or 2 * n + 1 in people:
            lines.append(f"1 FAMC @F{n}@")
        if n > 1:
            lines.append(f"1 FAMS @F{n // 2}@")
    for n in people:
        if 2 * n in people or 2 * n + 1 in people:
            lines.append(f"0 @F{n}@ FAM")
            lines += [f"1 HUSB @I{2 * n}@"] if 2 * n in people else []
            lines += [f"1 WIFE @I{2 * n + 1}@"] if 2 * n + 1 in people else []
            lines.append(f"1 CHIL @I{n}@")
    return people, "\n".join(lines + ["0 TRLR"]) + "\n"


def _calm(page) -> None:
    """Hides the trophy celebrations and the "tree imported" toast the app pops after an import."""
    page.add_style_tag(content="[data-testid=celebration], .toasts { display: none !important }")
    page.wait_for_timeout(500)


def open_demo(browser, url: str, rng: random.Random, viewport: dict):
    """A fresh browser with a made-up family imported and opened."""
    context = browser.new_context(viewport=viewport, device_scale_factor=2, locale="en-US", accept_downloads=True,
                                  reduced_motion="reduce", is_mobile=viewport["width"] < 600, has_touch=True)
    context.route("https://pagead2.googlesyndication.com/**", lambda r: r.abort())  # no ads in our posts
    page = context.new_page()
    page.set_default_timeout(60_000)
    page.goto(url.rstrip("/") + "/app/")
    people, gedcom = random_family(rng)
    page.get_by_test_id("start-import").click()
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "family.ged"
        f.write_text(gedcom)
        page.get_by_test_id("gedcom-input").set_input_files(f)
    root = people[1]
    root_name = f"{root['given']} {root['s1']} {root['s2']}"
    go = page.get_by_test_id("import-go")
    go.wait_for()
    if root_name not in go.inner_text():  # the app guesses the youngest person: make sure it's our root
        page.get_by_test_id("root-search").fill(root_name)
        page.get_by_test_id("root-option").filter(has_text=root_name).first.click()
    go.click()
    page.get_by_test_id("tab-surnames").wait_for()
    _calm(page)
    return context, page


SCREENS = ("surnames", "tree", "stats")
CARDS = ("list", "fan")


def screenshot(browser, url: str, rng: random.Random, out: Path, screen: str | None = None) -> Path:
    """A phone screenshot of one tab with the demo family. The bot picks among SCREENS (the
    numbered surname list, the fan-chart tree, the stats); the launch kit also uses "start"."""
    screen = screen or rng.choice(SCREENS)
    viewport = {"width": 430, "height": 900}
    if screen == "start":  # the first screen, before any data
        context = browser.new_context(viewport=viewport, device_scale_factor=2, locale="en-US",
                                      reduced_motion="reduce", is_mobile=True, has_touch=True)
        context.route("https://pagead2.googlesyndication.com/**", lambda r: r.abort())
        page = context.new_page()
        page.goto(url.rstrip("/") + "/app/")
        page.get_by_test_id("start-import").wait_for()
    else:
        context, page = open_demo(browser, url, rng, viewport)
    try:
        if screen != "start":
            page.get_by_test_id(f"tab-{screen}").click()
        page.wait_for_load_state("networkidle")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)
        page.screenshot(path=out)
        return out
    finally:
        context.close()


def card(browser, url: str, rng: random.Random, out: Path, kind: str | None = None) -> Path:
    """The app's own share image for the demo family: "list" is the surname card (1080×1350),
    "fan" the round family "cookie" (1400×1640). to_jpeg extends either to 3:4."""
    kind = kind or rng.choice(CARDS)
    context, page = open_demo(browser, url, rng, {"width": 1000, "height": 900})
    try:
        page.get_by_test_id("tab-share").click()
        page.get_by_test_id(f"share-kind-{kind}").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        with page.expect_download() as dl:
            page.get_by_test_id("download-card").click()
        dl.value.save_as(out)
        return out
    finally:
        context.close()
