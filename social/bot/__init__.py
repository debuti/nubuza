"""nubuza social bot: posts about nubuza projects to Instagram and X."""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOCIAL = ROOT / "social"
HISTORY = SOCIAL / "history.jsonl"

# Local runs read secrets from social/.env (KEY=value lines, git-ignored); real env vars win.
if (env := SOCIAL / ".env").exists():
    for line in env.read_text().splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and not key.startswith("#") and value.strip():
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


SECRET_KEYS = ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "CLOUDFLARE_API_TOKEN", "X_API_KEY", "X_API_SECRET",
               "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET", "IG_ACCESS_TOKEN", "TELEGRAM_BOT_TOKEN",
               "TELEGRAM_CHAT_ID")


def redact(text: str) -> str:
    """Hides secrets in anything that may end up in logs or in this (public) repo."""
    text = re.sub(r"(access_token|oauth_\w+|token|key|secret)=[^&\s'\"]+", r"\1=***", text, flags=re.I)
    for key in SECRET_KEYS:
        if len(value := os.environ.get(key, "")) >= 8:
            text = text.replace(value, "***")
    return text


def load_projects() -> list[dict]:
    return json.loads((SOCIAL / "projects.json").read_text())


def load_history() -> list[dict]:
    if not HISTORY.exists():
        return []
    return [json.loads(line) for line in HISTORY.read_text().splitlines() if line.strip()]


def append_history(entry: dict) -> None:
    with HISTORY.open("a") as f:
        f.write(redact(json.dumps(entry, ensure_ascii=False)) + "\n")
