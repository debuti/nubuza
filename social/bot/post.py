"""Makes and publishes one post about a random nubuza project.

    python -m social.bot.post [--slot ID] [--project ID] [--media KIND] [--no-claude] [--dry-run] [--commit]

The image is saved under public/social/ and deployed with the site before posting,
because Instagram fetches images from a public URL. --dry-run stops before deploying;
--commit commits and pushes the image and social/history.jsonl after posting.
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

from . import ROOT, append_history, content, images, load_history, load_projects, publish

SITE = os.environ.get("SITE_URL", "https://nubuza.com")
WRANGLER = "wrangler@4.149.0"
FALLBACK_MEDIA = {"card": ["card", "screenshot", "cover"], "screenshot": ["screenshot", "cover"],
                  "illustration": ["illustration", "cover"], "cover": ["cover"]}


def pick(rng: random.Random, args) -> tuple[dict, str]:
    projects = load_projects()
    project = next(p for p in projects if p["id"] == args.project) if args.project else rng.choice(projects)
    kinds, weights = zip(*project["media"].items())
    return project, args.media or rng.choices(kinds, weights)[0]


def write(project: dict, media: str, history: list[dict], rng: random.Random, use_claude: bool) -> dict:
    how = content.backend() if use_claude else None
    if how:
        recent = [h["text"] for h in history[-12:] if h.get("project") == project["id"]]
        try:
            return content.from_claude(project, media, recent, how)
        except Exception as e:  # any Claude problem: the bank keeps the schedule going
            print(f"Claude unavailable, using the fallback bank: {e!r}")
    used = {h["bank_id"] for h in history if h.get("bank_id")}
    return content.from_bank(project, used, rng)


def deploy_and_wait(url: str, jpeg: Path) -> None:
    if shutil.which("npx"):
        subprocess.run(["npx", "--yes", WRANGLER, "deploy"], cwd=ROOT, check=True)
    else:  # no Node here (e.g. a local run): pushing the image makes the Deploy workflow publish it
        git("add", str(jpeg))
        git("commit", "-m", f"social: image {jpeg.name}")
        git("pull", "--rebase")
        git("push")
    for _ in range(100):
        if requests.head(url, timeout=15).status_code == 200:
            return
        time.sleep(3)
    raise RuntimeError(f"{url} never became reachable")


def git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def commit(message: str, jpeg: Path) -> None:
    git("add", str(jpeg), "social/history.jsonl")
    git("commit", "-m", message)
    git("pull", "--rebase")
    git("push")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", default="")
    ap.add_argument("--project")
    ap.add_argument("--media", choices=["card", "screenshot", "illustration", "cover"])
    ap.add_argument("--no-claude", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and not (publish.configured(publish.X_KEYS) or publish.configured(publish.IG_KEYS)):
        print("No X or Instagram secrets configured yet: nothing to post to.")
        return 0

    rng = random.Random()
    history = load_history()
    project, media = pick(rng, args)
    post = write(project, media, history, rng, not args.no_claude)
    if args.media and post["media"] != args.media and args.media != "illustration":  # bank posts carry their own
        post["media"] = args.media
    print(f"project={project['id']} media={post['media']} source={post['source']}\n"
          f"headline: {post['headline']}\nbody: {post['body']}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    jpeg = ROOT / "public" / "social" / f"{stamp}-{project['id']}.jpg"
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        browser = pw.chromium.launch()
        # If an image type fails (e.g. the app's UI changed), step down: the framed cover always works.
        for media in FALLBACK_MEDIA[post["media"]]:
            try:
                post["media"] = media
                raw = images.make(browser, project, post, Path(tmp), rng)
                break
            except Exception as e:
                print(f"{media} image failed: {e!r}")
        else:
            raise RuntimeError("no image could be made")
        images.to_jpeg(raw, jpeg)
        browser.close()
    texts = content.compose(post, project, rng)
    print(f"image: {jpeg.relative_to(ROOT)}\n--- X ---\n{texts['x']}\n--- Instagram ---\n{texts['instagram']}")

    if args.dry_run:
        return 0

    image_url = f"{SITE}/social/{jpeg.name}"
    deploy_and_wait(image_url, jpeg)
    results, errors = {}, {}
    targets = [("x", publish.X_KEYS, lambda: publish.post_x(texts["x"], jpeg, post["alt_text"])),
               ("instagram", publish.IG_KEYS,
                lambda: publish.post_instagram(texts["instagram"], image_url, post["alt_text"]))]
    for name, keys, send in targets:
        if not publish.configured(keys):
            print(f"{name}: not configured, skipped")
            continue
        try:
            results[name] = send()
            print(f"{name}: {results[name]}")
        except Exception as e:
            errors[name] = repr(e)
            print(f"{name} failed: {e!r}", file=sys.stderr)

    if results:  # anything published: the slot is done (no double posts on retry)
        append_history({"slot": args.slot or f"manual-{stamp}", "at": datetime.now(timezone.utc).isoformat(),
                        "project": project["id"], "media": post["media"], "source": post["source"],
                        "bank_id": post["id"] if post["source"] == "bank" else None,
                        "text": post["body"], "image": f"/social/{jpeg.name}", "posts": results, "errors": errors})
        if args.commit:
            commit(f"social: post {args.slot or 'manual'}", jpeg)
    else:
        jpeg.unlink()
    return 1 if errors or not results else 0


if __name__ == "__main__":
    sys.exit(main())
