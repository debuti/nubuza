"""Decides whether a scheduled run should post, and when.

GitHub cron only fires at fixed UTC times, so the workflow runs hourly and this
module draws each ISO week's posting slots from a seeded RNG: the same week always
gives the same slots, on random days at random minutes inside the posting window.
A run posts the slot that falls within the next hour (sleeping until its minute),
or one that was missed earlier the same day because a run was dropped or late.

Usage: python -m social.bot.schedule   (writes due, at (epoch seconds) and slot to $GITHUB_OUTPUT)
"""

import os
import random
import sys
import time as clock
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from . import load_history

TZ = ZoneInfo(os.environ.get("POST_TZ", "Europe/Madrid"))
POSTS_PER_WEEK = int(os.environ.get("POSTS_PER_WEEK", "2"))
WINDOW_START, WINDOW_END = 9, 17  # local hours, end exclusive
LOOKAHEAD = timedelta(minutes=60)


def week_slots(year: int, week: int) -> list[datetime]:
    rng = random.Random(f"nubuza-social-{year}-W{week:02d}")
    days = sorted(rng.sample(range(1, 8), POSTS_PER_WEEK))
    slots = []
    for weekday in days:
        day = date.fromisocalendar(year, week, weekday)
        at = time(rng.randrange(WINDOW_START, WINDOW_END), rng.randrange(60))
        slots.append(datetime.combine(day, at, TZ))
    return slots


def slot_id(slot: datetime) -> str:
    return slot.strftime("%Y-%m-%dT%H:%M")


def due_slot(now: datetime, posted: set[str]) -> tuple[datetime, float] | None:
    """The slot to post now (or after waiting the returned seconds), if any."""
    year, week, _ = now.isocalendar()
    end_of_window = datetime.combine(now.date(), time(WINDOW_END), TZ)
    for slot in week_slots(year, week):
        if slot_id(slot) in posted or slot.date() != now.date():
            continue
        if slot <= now < end_of_window:
            return slot, 0.0  # missed earlier today: catch up
        if now < slot <= now + LOOKAHEAD:
            return slot, (slot - now).total_seconds()
    return None


def main() -> None:
    now = datetime.now(TZ)
    posted = {h["slot"] for h in load_history()}
    found = due_slot(now, posted)
    year, week, _ = now.isocalendar()
    print(f"now {now:%a %Y-%m-%d %H:%M %Z}; this week's slots:",
          ", ".join(f"{s:%a %H:%M}" + (" ✓" if slot_id(s) in posted else "") for s in week_slots(year, week)))
    out = {"due": "false", "at": "0", "slot": ""}
    if found:
        slot, wait = found
        out = {"due": "true", "at": str(int(clock.time() + wait)), "slot": slot_id(slot)}
        print(f"slot {slot_id(slot)} is due in {int(wait)}s")
    else:
        print("nothing due")
    if path := os.environ.get("GITHUB_OUTPUT"):
        with open(path, "a") as f:
            f.writelines(f"{k}={v}\n" for k, v in out.items())
    else:
        print(out, file=sys.stderr)


if __name__ == "__main__":
    main()
