# nubuza

nubuza.com: the home of the nubuza apps, plus the coordinator of their agents.

- public/: the static gallery site (nubuza.com): a card per app with category filters, the swimming jellyfish mascot, a 404 that suggests a random app. Served by Cloudflare, deployed on every push.
- apps-root/: a tiny Worker for the root of apps.nubuza.com: robots.txt listing every app's sitemap, redirect to nubuza.com, shared 404.
- social/: a bot that posts about a random app about twice a week on X and Instagram (@nubuzacom), with text written by Claude and a generated image.
- brand/: the nubuza avatar.
