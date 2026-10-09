"""Post copy: asked from Claude, or picked from the fallback bank when Claude is unavailable."""

import json
import os
import random
import re

from . import SOCIAL

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")

MEDIA_BRIEF = {
    "card": "The image is the app's own share card of a fictional demo user's love polygon. "
            "Also invent that demo user's scenario: 3 to 7 fictional people (cute nicknames, never real "
            "names) they fell for, each in a real city with its coordinates and dates.",
    "screenshot": "The image is a phone screenshot of the app showing a pink map with heart pins.",
    "cover": "The image is the project's cover art, framed as a polaroid.",
    "illustration": "You also draw the image: a kawaii SVG illustration about the post's idea, in the "
                    "nubuza style (pastel pinks, lavender, mint, sky blue; chunky rounded shapes with "
                    "dark plum #4a3a6b outlines; blush cheeks and tiny smiles on characters).",
}

SYSTEM = """You write social media posts for nubuza, a tiny studio of cute web projects (nubuza.com).
The voice is kawaii: warm, playful, sweet, a little cheeky, with a few emojis. Always write in English.
Posts promote one project and invite people to try it. Be accurate: only claim features listed in the
project facts. Never use real people's names, never mention specific real users, keep it safe for work.
Vary the angle and wording from the recent posts you are shown."""

LOVER = {
    "type": "object",
    "properties": {
        "nickname": {"type": "string"},
        "emoji": {"type": "string"},
        "city": {"type": "string"},
        "lat": {"type": "number"},
        "lng": {"type": "number"},
        "from": {"type": "string", "description": "YYYY-MM-DD"},
        "to": {"type": "string", "description": "YYYY-MM-DD, or empty if still going"},
        "type": {"type": "string", "enum": ["crush", "first_date", "kiss", "fling", "situationship",
                                             "relationship", "complicated", "other"]},
    },
    "required": ["nickname", "emoji", "city", "lat", "lng", "from", "to", "type"],
    "additionalProperties": False,
}

SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "description": "Short title for the image, at most 32 characters."},
        "body": {"type": "string", "description": "The post text: 1-2 sentences, at most 180 characters, "
                                                  "emojis welcome, no hashtags, no links."},
        "hashtags": {"type": "array", "items": {"type": "string"},
                     "description": "6-10 relevant hashtags without the # sign, lowercase, no spaces."},
        "alt_text": {"type": "string", "description": "Image description for screen readers, under 200 characters."},
        "svg": {"type": "string", "description": "Only for illustration posts: a complete standalone <svg> "
                                                 "with viewBox=\"0 0 1080 1350\", no scripts, no external "
                                                 "references, no text other than the headline. Empty otherwise."},
        "lovers": {"type": "array", "items": LOVER, "description": "Only for card and screenshot posts of "
                                                                   "Bizarre Love Polygon. Empty otherwise."},
    },
    "required": ["headline", "body", "hashtags", "alt_text", "svg", "lovers"],
    "additionalProperties": False,
}


def from_claude(project: dict, media: str, recent: list[str]) -> dict:
    import anthropic

    wants_lovers = project.get("exporter") == "bizarre-love-polygon" and media in ("card", "screenshot")
    brief = MEDIA_BRIEF[media]
    if wants_lovers and media == "screenshot":
        brief += " Also invent the demo user's scenario shown on the map (fill `lovers`)."
    prompt = (
        f"Project: {project['name']} ({project['url']})\n"
        f"Pitch: {project['pitch']}\n"
        "Facts:\n" + "\n".join(f"- {f}" for f in project["facts"]) + "\n\n"
        f"Post type: {media}. {brief}\n\n"
        "Recent posts (don't repeat them):\n" + ("\n".join(f"- {r}" for r in recent) or "- none yet")
    )
    client = anthropic.Anthropic()
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        thinking={"type": "adaptive"},
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        response = stream.get_final_message()
    if response.stop_reason != "end_turn":
        raise RuntimeError(f"Claude stopped with {response.stop_reason} (request {response._request_id})")
    data = json.loads(next(b.text for b in response.content if b.type == "text"))
    if media == "illustration" and not data["svg"].lstrip().startswith("<svg"):
        raise RuntimeError("Claude returned no SVG for an illustration post")
    data.update(source="claude", media=media, id=None)
    return data


def from_bank(project: dict, used: set[str], rng: random.Random) -> dict:
    bank = json.loads((SOCIAL / "fallback_posts.json").read_text())
    mine = [p for p in bank if p["project"] == project["id"]]
    if not mine:  # a new project without bank entries yet
        mine = [{"id": f"{project['id']}-generic", "media": "cover", "headline": f"Meet {project['name']} 💗",
                 "body": f"✨ {project['pitch']} Come say hi! 🥰"}]
    fresh = [p for p in mine if p["id"] not in used] or mine  # start over once all were used
    post = dict(rng.choice(fresh))
    post.update(source="bank", hashtags=[], alt_text=f"{post['headline']}: an image about {project['name']}",
                svg="", lovers=[])
    return post


def _x_len(text: str) -> int:
    """Length as X counts it: URLs are 23, most non-Latin characters and emoji count double."""
    text = re.sub(r"https?://\S+", "x" * 23, text)
    narrow = lambda c: ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D or 0x2010 <= ord(c) <= 0x201F \
        or 0x2032 <= ord(c) <= 0x2037
    return sum(1 if narrow(c) else 2 for c in text)


def _tags(post: dict, project: dict, rng: random.Random) -> list[str]:
    pool = project["hashtags"][:]
    rng.shuffle(pool)
    tags = []
    for t in ["nubuza", *post["hashtags"], *pool]:
        t = re.sub(r"[^\w]", "", t.lstrip("#")).lower()
        if t and t not in tags:
            tags.append(t)
    return tags


def compose(post: dict, project: dict, rng: random.Random) -> dict:
    """Builds the X text (280 weighted chars) and the Instagram caption from a post."""
    tags = _tags(post, project, rng)
    body = post["body"].strip()

    x_tags = tags[:4]
    while True:
        x_text = f"{body}\n\n{project['url']}\n" + " ".join(f"#{t}" for t in x_tags)
        if _x_len(x_text) <= 280 or not x_tags:
            break
        x_tags.pop()
    while _x_len(x_text) > 280:  # body itself too long: trim it
        body = body[:-2].rstrip() + "…"
        x_text = f"{body}\n\n{project['url']}"

    caption = (f"{post['body'].strip()}\n\n"
               f"💗 {project['name']}: {project['url'].removeprefix('https://').rstrip('/')} (link in bio)\n"
               f"☁️ more cute things at nubuza.com\n.\n" + " ".join(f"#{t}" for t in tags[:20]))
    return {"x": x_text, "instagram": caption[:2200]}
