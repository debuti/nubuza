"""nubuza social bot: posts about nubuza projects to Instagram and X."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOCIAL = ROOT / "social"
HISTORY = SOCIAL / "history.jsonl"


def load_projects() -> list[dict]:
    return json.loads((SOCIAL / "projects.json").read_text())


def load_history() -> list[dict]:
    if not HISTORY.exists():
        return []
    return [json.loads(line) for line in HISTORY.read_text().splitlines() if line.strip()]


def append_history(entry: dict) -> None:
    with HISTORY.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
