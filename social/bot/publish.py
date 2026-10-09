"""Publishes to X (API v2, OAuth 1.0a user context) and Instagram (Graph API content publishing)."""

import base64
import os
import time
from pathlib import Path

import requests
from requests_oauthlib import OAuth1Session

X_KEYS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
IG_KEYS = ("IG_USER_ID", "IG_ACCESS_TOKEN")
# graph.instagram.com for "Instagram API with Instagram Login" tokens,
# graph.facebook.com for "with Facebook Login" (Page) tokens.
IG_HOST = os.environ.get("IG_GRAPH_HOST") or "graph.instagram.com"
IG_VERSION = os.environ.get("IG_GRAPH_VERSION") or "v23.0"


def configured(keys: tuple[str, ...]) -> bool:
    return all(os.environ.get(k) for k in keys)


def _check(r: requests.Response) -> dict:
    if not r.ok:
        raise RuntimeError(f"{r.request.method} {r.url.split('?')[0]} → {r.status_code}: {r.text[:500]}")
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
