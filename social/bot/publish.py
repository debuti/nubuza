"""Publishes to X (API v2, OAuth 1.0a user context) and Instagram.

Instagram has two modes (repo variable IG_MODE):
- "kit" (default): opens a GitHub issue with the image and caption, ready to post by hand.
  Nothing touches Instagram, so a new account is never at risk from automation.
- "api": publishes through the Graph API (needs IG_USER_ID and IG_ACCESS_TOKEN).
"""

import base64
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests
from requests_oauthlib import OAuth1Session

from . import redact

X_KEYS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
IG_KEYS = ("IG_USER_ID", "IG_ACCESS_TOKEN")
# graph.instagram.com for "Instagram API with Instagram Login" tokens,
# graph.facebook.com for "with Facebook Login" (Page) tokens.
IG_HOST = os.environ.get("IG_GRAPH_HOST") or "graph.instagram.com"
IG_VERSION = os.environ.get("IG_GRAPH_VERSION") or "v23.0"


def paused(name: str) -> bool:
    """SOCIAL_PAUSE (repo variable) lists platforms not to post to, e.g. "instagram", or "all"."""
    pause = {p.strip().lower() for p in os.environ.get("SOCIAL_PAUSE", "").split(",")}
    return "all" in pause or name in pause


IG_MODE = (os.environ.get("IG_MODE") or "kit").lower()


def configured(keys: tuple[str, ...]) -> bool:
    """Has secrets and isn't paused. Keys tuples are named after their platform below."""
    name = "x" if keys is X_KEYS else "instagram"
    return all(os.environ.get(k) for k in keys) and not paused(name)


def targets(texts: dict, jpeg: Path, image_url: str, post: dict) -> list[tuple[str, callable]]:
    """The platforms this run sends to, each with the call that does it."""
    out = []
    if configured(X_KEYS):
        out.append(("x", lambda: post_x(texts["x"], jpeg, post["alt_text"])))
    if not paused("instagram"):
        if IG_MODE == "api" and configured(IG_KEYS):
            out.append(("instagram", lambda: post_instagram(texts["instagram"], image_url, post["alt_text"])))
        elif IG_MODE == "kit" and shutil.which("gh"):
            out.append(("instagram-kit", lambda: instagram_kit(texts["instagram"], image_url, post)))
    return out


def instagram_kit(caption: str, image_url: str, post: dict) -> str:
    """Opens a GitHub issue with everything needed to post by hand; returns its URL."""
    body = (f"![{post['alt_text']}]({image_url})\n\n"
            f"**1. Guarda la imagen:** [descárgala aquí]({image_url}) (en el móvil, mantén pulsada la imagen).\n\n"
            f"**2. Copia el texto:**\n\n```text\n{caption}\n```\n\n"
            f"**3. Texto alternativo** (Configuración avanzada → Accesibilidad):\n\n```text\n{post['alt_text']}\n```\n\n"
            f"**4. Publícalo en Instagram como @nubuzacom y cierra este issue.**\n")
    result = subprocess.run(["gh", "issue", "create", "--title", f"📸 Post para Instagram: {post['headline']}",
                             "--body-file", "-"], input=body, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(redact(f"gh issue create failed: {result.stderr.strip()}"))
    return result.stdout.strip().splitlines()[-1]


def _check(r: requests.Response) -> dict:
    if not r.ok:
        raise RuntimeError(redact(f"{r.request.method} {r.url.split('?')[0]} → {r.status_code}: {r.text[:500]}"))
    return r.json()


def post_x(text: str, image: Path, alt_text: str) -> str:
    x = OAuth1Session(*(os.environ[k] for k in X_KEYS))
    media = _check(x.post("https://api.x.com/2/media/upload", json={
        "media": base64.b64encode(image.read_bytes()).decode(),
        "media_category": "tweet_image",
    }))["data"]["id"]
    if alt_text:
        try:
            _check(x.post("https://api.x.com/2/media/metadata", json={
                "id": media, "metadata": {"alt_text": {"text": alt_text[:1000]}}}))
        except RuntimeError as e:  # alt text is nice to have, not worth losing the post
            print(f"warning: X alt text not set: {e}")
    tweet = _check(x.post("https://api.x.com/2/tweets", json={"text": text, "media": {"media_ids": [media]}}))
    return f"https://x.com/nubuzacom/status/{tweet['data']['id']}"


def post_instagram(caption: str, image_url: str, alt_text: str) -> str:
    base = f"https://{IG_HOST}/{IG_VERSION}"
    user, token = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
    container = _check(requests.post(f"{base}/{user}/media", data={
        "image_url": image_url, "caption": caption, "alt_text": alt_text, "access_token": token,
    }, timeout=60))["id"]
    for _ in range(30):  # Instagram fetches and processes the image asynchronously
        status = _check(requests.get(f"{base}/{container}", params={
            "fields": "status_code", "access_token": token}, timeout=30)).get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram couldn't process the image: {status}")
        time.sleep(5)
    media = _check(requests.post(f"{base}/{user}/media_publish", data={
        "creation_id": container, "access_token": token}, timeout=60))["id"]
    info = _check(requests.get(f"{base}/{media}", params={"fields": "permalink", "access_token": token}, timeout=30))
    return info.get("permalink", media)
