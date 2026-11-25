"""Send a finished reel or post to the nubuza-alerts Telegram bot.

Usage: python3 scripts/send_alert.py "caption" [file ...]
Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from reel/.env, or else the repo-root .env (both gitignored). Never prints them.
.mp4 goes as video, images as documents (full quality), and with no file it sends the caption as text.
"""
import json, sys, urllib.request, uuid
from pathlib import Path

env = {}
here = Path(__file__).resolve().parent.parent
envfile = next(p for p in (here / ".env", here.parent / ".env") if p.exists())
for line in envfile.read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
api = f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}"
chat = env["TELEGRAM_CHAT_ID"]


def call(method, fields, file=None):
    b = uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    if file:
        name, p = file
        body += (f'--{b}\r\nContent-Disposition: form-data; name="{name}"; filename="{p.name}"\r\n'
                 f'Content-Type: application/octet-stream\r\n\r\n').encode() + p.read_bytes() + b"\r\n"
    body += f"--{b}--\r\n".encode()
    req = urllib.request.Request(f"{api}/{method}", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:  # don't echo the URL: it holds the token
        sys.exit(f"{method} failed: HTTP {e.code} {e.read()[:200]!r}")
    if not r.get("ok"):
        sys.exit(f"{method} failed: {r.get('description')}")


caption, files = sys.argv[1], [Path(f) for f in sys.argv[2:]]
if not files:
    call("sendMessage", {"chat_id": chat, "text": caption})
for i, p in enumerate(files):
    cap = caption[:1024] if i == 0 else ""
    if p.suffix.lower() == ".mp4":
        call("sendVideo", {"chat_id": chat, "caption": cap, "supports_streaming": "true"}, ("video", p))
    else:
        call("sendDocument", {"chat_id": chat, "caption": cap}, ("document", p))
if files and len(caption) > 1024:
    call("sendMessage", {"chat_id": chat, "text": caption})
print("sent")
