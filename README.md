# nubuza.com

A static photo-gallery page for nubuza projects. Plain HTML/CSS and SVG, with no build step and no server code.

```
public/
  index.html        gallery page
  styles.css
  logo.svg          the cloud-jellyfish mascot (also the favicon)
  404.html
  _headers          cache + security headers (Cloudflare reads this)
  projects/         cover images, one per project
wrangler.jsonc      Cloudflare config: static assets only
```

## Preview locally

```sh
python3 -m http.server -d public
```

## Deploy to Cloudflare

`wrangler.jsonc` has no `main` script, so Cloudflare serves the files directly from its edge. No Worker runs, and static asset requests are free and unmetered.

Every push to `main` deploys through `.github/workflows/deploy.yml`, which runs `wrangler deploy` and attaches `nubuza.com` and `www.nubuza.com` as custom domains. The workflow needs two repository secrets:

- `CLOUDFLARE_API_TOKEN`: create it from the "Edit Cloudflare Workers" template, with the nubuza.com zone included.
- `CLOUDFLARE_ACCOUNT_ID`

To deploy by hand instead, run `npx wrangler deploy`.

## Add a project

1. Put a 4:3 cover image in `public/projects/`.
2. In `public/index.html`, copy the `<li class="photo">` block and change the link, image, title and blurb.

## Social posts (Instagram and X: @nubuzacom)

`.github/workflows/social.yml` posts about a random nubuza project about twice a week, at a random time between 9:00 and 17:00 (Europe/Madrid).

- **When:** the workflow runs hourly. `social/bot/schedule.py` draws each week's two slots from a seeded RNG and posts when a slot is less than an hour away, or catches up the same day if a run was missed. Posted slots are recorded in `social/history.jsonl`.
- **What:** Claude (`claude-opus-5-5`) writes a kawaii English post (headline, text, hashtags, alt text) from the facts in `social/projects.json`. If Claude is unavailable, the bot picks an unused post from `social/fallback_posts.json` (136 posts).
- **How it reaches Claude:** through the API when `ANTHROPIC_API_KEY` is set. Otherwise it uses the Claude Agent SDK, which works with `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`) or, locally, with your Claude Code login. Set `CLAUDE_BACKEND=api` or `CLAUDE_BACKEND=agent-sdk` to force one.
- **Image** (1080×1350 JPEG), weighted per project in `projects.json`:
  - `card`: the Bizarre Love Polygon share card. The bot opens the live app in headless Chromium, restores an encrypted backup of a fictional demo user and downloads the card. This only works once the app's share feature is deployed; until then the bot uses `screenshot`.
  - `screenshot`: the app on a phone with the demo user's map, framed as a polaroid.
  - `illustration`: a square SVG drawn by Claude, framed as a polaroid.
  - `cover`: the project's cover, framed.
  If one type fails, the bot falls back to the next type, ending with `cover`.
- **Publishing:** the image is saved to `public/social/` and deployed with the site. Then the bot posts to X and delivers the Instagram post, and commits the image and history. A platform without secrets is skipped.
- **Instagram by hand:** the bot doesn't touch Instagram. It sends you the image, the caption and the alt text, and you publish them from your phone as @nubuzacom. They arrive on Telegram when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set, or otherwise as a GitHub issue (close it once posted). Set the repository variable `IG_MODE` to `telegram`, `kit` (GitHub issue) or `api` (Graph API, needs `IG_USER_ID` and `IG_ACCESS_TOKEN`) to choose.
- **Pausing:** set the repository variable `SOCIAL_PAUSE` to `instagram`, `x` or `all` to stop sending to those platforms.

Run **Actions → Social posts → Run workflow** to post by hand. It defaults to a dry run, which saves the image as an artifact and doesn't publish.

### Posting from your machine

This uses no Actions minutes. To stop the hourly runs too, disable the workflow with `gh workflow disable social.yml`.

```sh
pip install -r social/requirements.txt && playwright install chromium
cp social/.env.example social/.env   # fill in X / Instagram (and optionally Cloudflare)
git pull                             # latest history, so posts don't repeat
python -m social.bot.post --dry-run  # preview: prints the texts, image in public/social/
python -m social.bot.post --commit   # publish, then commit and push the image and history
```

Claude uses your Claude Code login unless `social/.env` sets a key or token. If Node isn't installed, the bot can't run wrangler, so it pushes the image and waits for the Deploy workflow to publish it.

### Secrets

| Secret | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` | platform.claude.com → API keys, or `claude setup-token` for a Claude subscription token |
| `X_API_KEY`, `X_API_SECRET` | developer.x.com → your app → Keys and tokens → API Key and Secret. Set the app's permissions to **Read and write** first. |
| `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` | Same page → Access Token and Secret, generated while logged in as @nubuzacom after enabling write permissions |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | A Meta app with the Instagram API, @nubuzacom as a professional (Business or Creator) account, permissions `instagram_business_basic` + `instagram_business_content_publish` |

| `TELEGRAM_BOT_TOKEN` | Telegram → @BotFather → `/newbot` |
| `TELEGRAM_CHAT_ID` | Send your bot a message, then run `python -m social.tools.telegram_chat_id` with the token in `social/.env` |
| `SECRETS_PAT` | github.com → Settings → Developer settings → Fine-grained tokens. Limit it to **only** `debuti/nubuza`, with Repository permissions → **Secrets: Read and write** and nothing else. |

Instagram Login tokens (`graph.instagram.com`, the default) expire after 60 days. `.github/workflows/instagram-token.yml` refreshes `IG_ACCESS_TOKEN` on the 1st of every month, using `SECRETS_PAT` to save it.

This repository is public, so nothing may leak a secret. The workflows only run on a schedule or by hand, never for pull requests from forks. The refresh never prints tokens. The bot redacts tokens from its error messages and from `social/history.jsonl`.
To use a Facebook Login Page token instead, which doesn't expire, set the repository variable `IG_GRAPH_HOST=graph.facebook.com`.
