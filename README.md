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
