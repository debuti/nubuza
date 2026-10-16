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
    "screenshot": "",  # each project describes its own screenshots (screenshot_brief)
    "cover": "The image is the project's cover art, framed as a polaroid.",
    "illustration": "You also draw the image: a square kawaii SVG illustration (no text: the headline is "
                    "added around it) that shows the post's idea clearly, as a scene, not a logo. Make it rich "
                    "and full, with no empty areas: a background, a main subject and small details (sparkles, "
                    "clouds, little hearts, map bits). Nubuza style: pastel pinks, lavender, mint, sky blue; "
                    "chunky rounded shapes with dark plum #4a3a6b outlines; blush cheeks and tiny smiles on "
                    "characters.",
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
                                                 "with viewBox=\"0 0 1000 1000\", a filled background, no text, "
                                                 "no scripts, no external references. Empty otherwise."},
        "screen": {"type": "string", "enum": ["report", "alerts", "epic", ""],
                   "description": "Only for 5dollars screenshot posts: the screen that fits the text (report = "
                                  "monthly savings chart, alerts = why a month went off, epic = a trip's "
                                  "expenses). Empty otherwise."},
        "lovers": {"type": "array", "items": LOVER, "description": "Only for card and screenshot posts of "
                                                                   "Bizarre Love Polygon. Empty otherwise."},
    },
    "required": ["headline", "body", "hashtags", "alt_text", "svg", "screen", "lovers"],
    "additionalProperties": False,
}


def backend() -> str | None:
    """Which way to reach Claude: "api" (API key), "agent-sdk" (Claude Code login or OAuth token), or None."""
    choice = os.environ.get("CLAUDE_BACKEND", "auto")
    if choice != "auto":
        return choice
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "api"
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or not os.environ.get("GITHUB_ACTIONS"):
        return "agent-sdk"  # locally, the Agent SDK uses your Claude Code login
    return None


def _ask_api(prompt: str) -> dict:
    import anthropic

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
    return json.loads(next(b.text for b in response.content if b.type == "text"))


def _ask_agent_sdk(prompt: str, schema: dict = SCHEMA) -> dict:
    import anyio
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM,
        model=MODEL,
        tools=[],  # just writing: no file, shell or web tools
        setting_sources=[],  # ignore local Claude Code settings, hooks and CLAUDE.md
        max_turns=3,
        effort="medium",
        output_format={"type": "json_schema", "schema": schema},
    )

    async def run() -> ResultMessage | None:
        result = None
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                result = message
        return result

    result = anyio.run(run)
    if result is None or result.is_error or not isinstance(result.structured_output, dict):
        raise RuntimeError(f"Agent SDK returned no post: {result and (result.errors or result.subtype)}")
    return result.structured_output


def from_claude(project: dict, media: str, recent: list[str], how: str) -> dict:
    wants_lovers = project.get("exporter") == "bizarre-love-polygon" and media in ("card", "screenshot")
    brief = MEDIA_BRIEF[media] or project.get("screenshot_brief", "The image is a screenshot of the app.")
    if media == "illustration" and project.get("art_hint"):
        brief += " " + project["art_hint"]
    if wants_lovers and media == "screenshot":
        brief += " Also invent the demo user's scenario shown on the map (fill `lovers`)."
    prompt = (
        f"Project: {project['name']} ({project['url']})\n"
        f"Pitch: {project['pitch']}\n"
        "Facts:\n" + "\n".join(f"- {f}" for f in project["facts"]) + "\n\n"
        f"Post type: {media}. {brief}\n\n"
        "Recent posts (don't repeat them):\n" + ("\n".join(f"- {r}" for r in recent) or "- none yet")
    )
    data = _ask_api(prompt) if how == "api" else _ask_agent_sdk(prompt)
    if media == "illustration" and not data["svg"].lstrip().startswith("<svg"):
        raise RuntimeError("Claude returned no SVG for an illustration post")
    data.update(source=f"claude-{how}", media=media, id=None)
    return data


def from_bank(project: dict, used: set[str], rng: random.Random) -> dict:
    bank = json.loads((SOCIAL / "fallback_posts.json").read_text())
    mine = [p for p in bank if p["project"] == project["id"]]
    if not mine:  # a new project without bank entries yet
        mine = [{"id": f"{project['id']}-generic", "media": "cover", "headline": f"Meet {project['name']} 💗",
                 "body": f"✨ {project['pitch']} Come say hi! 🥰"}]
    fresh = [p for p in mine if p["id"] not in used] or mine  # start over once all were used
    post = dict(rng.choice(fresh))
    art = SOCIAL / "bank_art" / f"{post['id']}.svg"  # pre-drawn illustration for this exact post
    post.update(source="bank", hashtags=[], alt_text=post.get("alt") or f"{post['headline']}: an image about "
                f"{project['name']}", svg=art.read_text() if art.exists() else "", lovers=[])
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
