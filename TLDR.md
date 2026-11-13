# nubuza

nubuza.com: the home of the nubuza apps, plus the coordinator of their agents.

- public/: the static gallery site (nubuza.com): a card per app with category filters, the swimming jellyfish mascot, a 404 that suggests a random app, and the umbrella privacy policy and terms (en + es) that cover ads for every app and link to each app's own. Served by Cloudflare, deployed on every push.
- apps-root/: a tiny Worker for the root of apps.nubuza.com: robots.txt listing every app's sitemap, .well-known/assetlinks.json for the Android apps' App Links, redirect to nubuza.com, shared 404. Also deployed on every push.
- social/: a bot that posts about a random app about twice a week on X and Instagram (@nubuzacom), with text written by Claude and a generated image.
- brand/: the nubuza avatar and logo PNGs (square and wide, for consoles such as the AdSense consent message).
