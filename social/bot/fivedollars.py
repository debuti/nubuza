"""5dollars screenshots: drives the live app with a fictional household.

5dollars keeps everything on the user's side (Drive, a folder or the browser), so the demo
household goes in the way a user's data would: as a "5dollars-export" JSON imported into a
new scenario in "This browser". Everything here is made up: no real accounts or amounts.
"""

import json
import random
import tempfile
from datetime import date, timedelta
from pathlib import Path

CATEGORIES = ["Total", "Total>Income", "Total>Income>Salary", "Total>Income>Other", "Total>Expenses",
              "Total>Expenses>Home", "Total>Expenses>Home>Rent", "Total>Expenses>Home>Electricity",
              "Total>Expenses>Home>Internet", "Total>Expenses>Food", "Total>Expenses>Food>Groceries",
              "Total>Expenses>Food>Eating out", "Total>Expenses>Transport", "Total>Expenses>Transport>Fuel",
              "Total>Expenses>Transport>Public transport", "Total>Expenses>Leisure",
              "Total>Expenses>Leisure>Streaming", "Total>Expenses>Leisure>Trips", "Total>Expenses>Shopping",
              "Total>Expenses>Health", "Total>Transfers"]

# description, category, min cents, max cents, times a month (min, max)
MONTHLY = [("SALARY CLOUDWORKS LTD", "Total>Income>Salary", 245000, 245000, (1, 1)),
           ("RENT FLAT 3B", "Total>Expenses>Home>Rent", -95000, -95000, (1, 1)),
           ("ELECTRICITY SPARKCO", "Total>Expenses>Home>Electricity", -8200, -3900, (1, 1)),
           ("FIBER INTERNET", "Total>Expenses>Home>Internet", -3500, -3500, (1, 1)),
           ("STREAMFLIX", "Total>Expenses>Leisure>Streaming", -1299, -1299, (1, 1)),
           ("GREENLEAF SUPERMARKET", "Total>Expenses>Food>Groceries", -11000, -1800, (5, 8)),
           ("CAFE NUBE", "Total>Expenses>Food>Eating out", -2800, -450, (2, 5)),
           ("RAMEN HOUSE", "Total>Expenses>Food>Eating out", -6200, -2400, (0, 2)),
           ("FUEL STATION 24", "Total>Expenses>Transport>Fuel", -7000, -3500, (1, 2)),
           ("METRO CARD TOP-UP", "Total>Expenses>Transport>Public transport", -2000, -2000, (1, 1)),
           ("BOOKSHOP KAWAII", "Total>Expenses>Shopping", -4500, -900, (0, 2)),
           ("PHARMACY", "Total>Expenses>Health", -3200, -600, (0, 1)),
           ("REFUND FROM FRIEND", "Total>Income>Other", 500, 4000, (0, 1))]

TRIP = [("FLIGHT TO LISBON", -18900), ("HOTEL ALFAMA", -32000), ("PASTEIS & COFFEE", -1450),
        ("TRAM 28 TICKETS", -1200), ("SEAFOOD DINNER", -6800)]


def _months(n: int) -> list[date]:
    first = date.today().replace(day=1)
    out = []
    for _ in range(n):
        out.append(first)
        first = (first - timedelta(days=1)).replace(day=1)
    return out[::-1]


def demo_export(rng: random.Random, months: int = 14) -> dict:
    main, savings = [], []
    month_list = _months(months)
    trip_month = month_list[-4]
    for m in month_list:
        last_day = ((m.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)).day
        share = 1.0  # the current month is still running: only the moves so far
        if m == month_list[-1]:
            share = max(date.today().day - 1, 1) / last_day
            last_day = max(date.today().day - 1, 1)
        rows = []
        for desc, cat, lo, hi, (a, b) in MONTHLY:
            times = rng.randint(a, b)
            if share < 1 and times > 1:
                times = round(times * share)
            for _ in range(times):
                day = 1 if cat.endswith("Salary") else 2 if cat.endswith("Rent") else rng.randint(1, last_day)
                rows.append((min(day, last_day), desc, cat, rng.randint(lo, hi), []))
        if m == trip_month:
            rows += [(min(10 + i, last_day), d, "Total>Expenses>Leisure>Trips", v, ["lisbon"]) for i, (d, v) in enumerate(TRIP)]
        rows.append((min(3, last_day), "TRANSFER TO SAVINGS", "Total>Transfers", -30000, []))
        rows.sort(key=lambda r: r[0])
        for day, desc, cat, amount, tags in rows:
            when = m.replace(day=day).isoformat()
            main.append({"operationDate": when, "valueDate": when, "description": desc, "amount": amount,
                         "category": cat, "tags": tags})
            if desc == "TRANSFER TO SAVINGS":
                savings.append({"operationDate": when, "valueDate": when, "description": "TRANSFER FROM MAIN",
                                "amount": 30000, "category": "Total>Transfers", "tags": []})
    opened = month_list[0].isoformat()
    for account, start in ((main, 412000), (savings, 150000)):  # the ledger chains from 0: open it
        account.insert(0, {"operationDate": opened, "valueDate": opened, "description": "OPENING BALANCE",
                           "amount": start, "category": None, "tags": [], "isVirtual": True})
    matches = []
    for account in (main, savings):
        balance = 0
        for mv in account:
            balance += mv["amount"]
            mv["balance"] = balance
    savings_pos = {mv["operationDate"]: i for i, mv in enumerate(savings)}
    for i, mv in enumerate(main):
        if mv["description"] == "TRANSFER TO SAVINGS":
            matches.append({"from": {"account": 0, "position": i}, "to": {"account": 1, "position": savings_pos[mv["operationDate"]]}})
    trip_start = trip_month.replace(day=10).isoformat()
    return {"format": "5dollars-export", "version": 2, "exportedAt": date.today().isoformat() + "T09:00:00Z",
            "data": {"name": "Home", "categories": [{"path": p} for p in CATEGORIES], "tags": ["lisbon"],
                     "accounts": [{"alias": "Main account", "bankName": "Cloud Bank", "currency": "EUR", "moves": main},
                                  {"alias": "Savings", "bankName": "Cloud Bank", "currency": "EUR", "moves": savings}],
                     "matches": matches,
                     "epics": [{"name": "Lisbon trip ✈️", "description": "Four sunny days in Lisbon",
                                "startDate": trip_start, "endDate": trip_month.replace(day=15).isoformat(),
                                "tags": ["lisbon"]}]}}


def open_demo(browser, url: str, rng: random.Random, viewport: dict):
    """A fresh browser with the demo household imported and opened."""
    context = browser.new_context(viewport=viewport, device_scale_factor=2, locale="en-US",
                                  reduced_motion="reduce", is_mobile=viewport["width"] < 600, has_touch=True)
    context.route("https://pagead2.googlesyndication.com/**", lambda r: r.abort())  # no ads in our posts
    page = context.new_page()
    page.set_default_timeout(60_000)
    page.goto(url)
    page.get_by_role("button", name="Use this browser").click()
    page.get_by_text("No scenarios yet").wait_for()
    page.get_by_label("New scenario name (optional)").fill("Our home")
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "home.json"
        f.write_text(json.dumps(demo_export(rng)))
        page.locator("input[type=file]").first.set_input_files(f)
    page.get_by_role("heading", name="Accounts").wait_for()  # the imported scenario opens by itself
    page.locator(".toast button, [role=status] button").first.click(timeout=5000) if page.locator(
        ".toast button, [role=status] button").count() else None
    return context, page


SCREENS = ("report", "alerts", "epic")


HEIGHTS = {"epic": 640, "accounts": 520, "welcome": 600}  # short pages: no empty space below
WIDTHS = {"moves": 1280}  # the moves table needs room for its category column


def screenshot(browser, url: str, rng: random.Random, out: Path, screen: str | None = None) -> Path:
    """One of the app's screens with the demo household. The bot picks among SCREENS (the monthly
    report, the alerts, the trip epic); the launch kit also uses "welcome", "accounts" and "moves"."""
    screen = screen or rng.choice(SCREENS)
    viewport = {"width": WIDTHS.get(screen, 1000), "height": HEIGHTS.get(screen, 1080)}
    if screen == "welcome":  # the first screen, before any data
        context = browser.new_context(viewport=viewport, device_scale_factor=2, locale="en-US", reduced_motion="reduce")
        context.route("https://pagead2.googlesyndication.com/**", lambda r: r.abort())
        page = context.new_page()
        page.goto(url)
        page.get_by_text("Welcome to 5dollars").wait_for()
        page.get_by_text("Welcome to 5dollars").scroll_into_view_if_needed()
    else:
        context, page = open_demo(browser, url, rng, viewport)
    try:
        if screen == "epic":
            page.get_by_role("link", name="Epics").first.click()
            page.get_by_text("Lisbon trip").first.click()
        elif screen == "moves":
            page.get_by_role("link", name="Main account").first.click()
            page.get_by_role("link", name="Moves").first.click()
            page.get_by_text("moves", exact=False).first.wait_for()
        elif screen not in ("welcome", "accounts"):
            page.get_by_role("link", name=screen.capitalize()).first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=out)
        return out
    finally:
        context.close()
