"""Draws an illustration for every fallback post that has no image of its own.

    python -m social.tools.draw_bank_art [--redo ID ...]

Uses Claude (API key, OAuth token or your Claude Code login, like the bot) once, so the
bank works without Claude afterwards. Saves social/bank_art/<id>.svg and sets the post's
media to "illustration" and its alt text in social/fallback_posts.json.
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor

from ..bot import SOCIAL, content, load_projects

ART = SOCIAL / "bank_art"
SCHEMA = {
    "type": "object",
    "properties": {
        "svg": {"type": "string", "description": "A complete standalone <svg> with viewBox=\"0 0 1000 1000\", "
                                                "a filled background, no text, no scripts, no external references."},
        "alt": {"type": "string", "description": "Image description for screen readers, under 200 characters."},
    },
    "required": ["svg", "alt"],
    "additionalProperties": False,
}


def draw(post: dict, project: dict) -> tuple[str, dict]:
    prompt = (
        f"Draw the image for this Instagram post about {project['name']} ({project['pitch']}).\n"
        f"Headline (shown above the image, don't repeat it): {post['headline']}\n"
        f"Post text: {post['body']}\n\n"
        "The image must show the post's idea clearly, as a scene, not a logo. Square kawaii SVG illustration in "
        "the nubuza style: pastel pinks, lavender, mint, sky blue; chunky rounded shapes with dark plum #4a3a6b "
        "outlines; blush cheeks and tiny smiles on characters. Rich and full, no empty areas. "
        + project.get("art_hint", "")
    )
    data = content._ask_agent_sdk(prompt, SCHEMA) if content.backend() == "agent-sdk" else None
    if data is None:
        raise SystemExit("Set CLAUDE_BACKEND=agent-sdk or run with your Claude Code login")
    if not data["svg"].lstrip().startswith("<svg"):
        raise RuntimeError("no SVG returned")
    return post["id"], data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", nargs="*", default=[])
    args = ap.parse_args()
    projects = {p["id"]: p for p in load_projects()}
    bank_file = SOCIAL / "fallback_posts.json"
    bank = json.loads(bank_file.read_text())
    todo = [p for p in bank if (p["media"] in ("cover", "illustration") and not (ART / f"{p['id']}.svg").exists())
            or p["id"] in args.redo]
    print(f"drawing {len(todo)} illustrations")
    ART.mkdir(exist_ok=True)
    with ThreadPoolExecutor(4) as pool:
        for future in [pool.submit(draw, p, projects[p["project"]]) for p in todo]:
            try:
                pid, data = future.result()
            except Exception as e:
                print(f"failed: {e!r}")
                continue
            (ART / f"{pid}.svg").write_text(data["svg"])
            post = next(p for p in bank if p["id"] == pid)
            post.update(media="illustration", alt=data["alt"])
            bank_file.write_text(json.dumps(bank, ensure_ascii=False, indent=1))  # save progress as we go
            print(f"drew {pid}: {post['headline']}")


if __name__ == "__main__":
    main()
