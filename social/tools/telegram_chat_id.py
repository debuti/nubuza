"""Prints the chat id of whoever messaged your Telegram bot, for the TELEGRAM_CHAT_ID secret.

    1. Send any message to your bot from your Telegram account.
    2. TELEGRAM_BOT_TOKEN=... python -m social.tools.telegram_chat_id
       (or put the token in social/.env, which git ignores)
"""

import os

import requests

from ..bot import redact

updates = requests.get(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/getUpdates", timeout=30)
if not updates.ok:
    raise SystemExit(redact(f"Telegram said {updates.status_code}: {updates.text[:300]}"))
chats = {}
for update in updates.json()["result"]:
    chat = (update.get("message") or update.get("edited_message") or {}).get("chat")
    if chat:
        chats[chat["id"]] = chat.get("username") or chat.get("first_name") or chat.get("title")
if not chats:
    raise SystemExit("No messages yet: send your bot a message first, then run this again.")
for chat_id, name in chats.items():
    print(f"{name}: {chat_id}")
