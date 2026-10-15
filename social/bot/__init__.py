"""nubuza social bot: posts about nubuza projects to Instagram and X."""

import json
import os
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


def load_projects() -> list[dict]:
    return json.loads((SOCIAL / "projects.json").read_text())


def load_history() -> list[dict]:
    if not HISTORY.exists():
        return []
    return [json.loads(line) for line in HISTORY.read_text().splitlines() if line.strip()]


def append_history(entry: dict) -> None:
    with HISTORY.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
