# Ground Feed — China leadership tracker

A live-ish news river: pulls your RSS sources every 15 minutes, stores new
items as JSON, and shows them on a static page. No server to run or pay for.

## How it works

- `feeds.json` — the list of sources. Edit this to add/remove feeds.
- `fetch_feeds.py` — pulls every feed in `feeds.json` and merges new items
  into `data/items.json` (deduped, newest first, capped at 800 items).
- `index.html` — the page itself. Reads `data/items.json` and `feeds.json`
  directly, no backend needed.
- `.github/workflows/fetch.yml` — a GitHub Action that runs `fetch_feeds.py`
  every 15 minutes and commits the updated `data/items.json` back to the repo.

## One-time setup

1. **Create a new GitHub repo** (public or private — Pages works either way,
   private repos need GitHub Pro/Team/Enterprise for Pages, so public is
   simplest for a solo project).

2. **Push these files to it:**
   ```bash
   cd china-tracker
   git init
   git add .
   git commit -m "Initial tracker"
   git branch -M main
   git remote add origin https://github.com/<you>/<repo-name>.git
   git push -u origin main
   ```

3. **Enable GitHub Pages:**
   Repo → Settings → Pages → "Build and deployment" → Source: "Deploy from a
   branch" → Branch: `main`, folder: `/ (root)`. Save. Your site will be at
   `https://<you>.github.io/<repo-name>/` within a minute or two.

4. **Enable the Action:**
   It runs automatically on the cron schedule once it's pushed, but the
   first run may take up to 15 minutes to fire. To seed data immediately:
   Repo → Actions → "Fetch feeds" → "Run workflow" (this uses the
   `workflow_dispatch` trigger already in the workflow file).

That's it — after the first successful Action run, `data/items.json` has
content and the page will show it.

## Notes / things I couldn't verify from here

- I couldn't test-run `fetch_feeds.py` against the live feeds myself — my
  sandbox's network is locked to package registries only, not arbitrary
  websites. The code is a standard `feedparser` loop and should work
  against all ten RSS URLs, but the *first* real run (via GitHub Actions,
  which has open internet access) is the actual test. If a feed comes back
  empty, check the `[warn]` line in the Action's log output — it'll say
  which source failed.
- **China Daily Global Edition**, **Huanqiu**, and **Caixin China's main
  site** don't have confirmed RSS feeds (see `needs_setup` in `feeds.json`
  for details on each). They're left out of the live feed for now rather
  than guessed at with a broken URL.
- Your four reference links (State Council roster, Asia Society, People's
  Daily PSC page, Propagandascope) show up in a footer panel on the page
  since they're static reference pages, not something that publishes new
  items to poll.

## Adding a source later

Add an entry to `rss_sources` in `feeds.json`:
```json
{ "name": "New Source", "url": "https://example.com/feed", "category": "newsletter" }
```
Categories currently used: `newsletter`, `analysis`, `blog`, `formal`. Using
a new category name is fine — it just won't have a filter chip or dot color
in `index.html` until you add one (both are one line each).

## If you want WeChat or Weibo in here too

Those don't have clean feeds the way the current sources do — see the
earlier conversation for the tradeoffs (Sogou's WeChat search as a
workaround, Weibo needing either scraping-with-friction or a paid data
vendor). Happy to build a second, separate fetcher for either once you
want to take that on — it's a different enough problem that it's worth
keeping out of this repo's straightforward RSS loop.
