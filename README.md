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

## Social posts (Instagram @nubuza, X @nubuzacom)

`.github/workflows/social.yml` posts about a random nubuza project about twice a week, at a random time between 9:00 and 17:00 (Europe/Madrid).

- **When:** the workflow runs hourly. `social/bot/schedule.py` draws each week's two slots from a seeded RNG and posts when a slot is less than an hour away, or catches up the same day if a run was missed. Posted slots are recorded in `social/history.jsonl`.
- **What:** Claude (`claude-opus-5-5`) writes a kawaii English post (headline, text, hashtags, alt text) from the facts in `social/projects.json`. If Claude is unavailable, the bot picks an unused post from `social/fallback_posts.json` (136 posts).
- **Image** (1080×1350 JPEG), weighted per project in `projects.json`:
  - `card`: the Bizarre Love Polygon share card. The bot opens the live app in headless Chromium, restores an encrypted backup of a fictional demo user and downloads the card. This only works once the app's share feature is deployed; until then the bot uses `screenshot`.
  - `screenshot`: the app on a phone with the demo user's map, framed as a polaroid.
  - `illustration`: an SVG drawn by Claude.
  - `cover`: the project's cover, framed.
  If one type fails, the bot falls back to the next type, ending with `cover`.
- **Publishing:** the image is saved to `public/social/` and deployed with the site, because Instagram fetches images from a public URL. Then the bot posts to X and Instagram, and commits the image and history. A platform without secrets is skipped.

Run **Actions → Social posts → Run workflow** to post by hand. It defaults to a dry run, which saves the image as an artifact and doesn't publish.

Dry run locally: `pip install -r social/requirements.txt && playwright install chromium && python -m social.bot.post --dry-run --no-claude`

### Secrets

| Secret | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | platform.claude.com → API keys |
| `X_API_KEY`, `X_API_SECRET` | developer.x.com → your app → Keys and tokens → API Key and Secret. Set the app's permissions to **Read and write** first. |
| `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` | Same page → Access Token and Secret, generated while logged in as @nubuzacom after enabling write permissions |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | A Meta app with the Instagram API, @nubuza as a professional (Business or Creator) account, permissions `instagram_business_basic` + `instagram_business_content_publish` |

Instagram Login tokens (`graph.instagram.com`, the default) expire after 60 days. Refresh yours before then with `curl "https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=TOKEN"` and save the new token in the secret.
To use a Facebook Login Page token instead, which doesn't expire, set the repository variable `IG_GRAPH_HOST=graph.facebook.com`.
