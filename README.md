# Crypto & Web3 Job Scraper + Dashboard

Aggregates crypto/blockchain job listings from **Greenhouse**, **Lever**, **crypto job boards** (RSS), and **JobSpy** (LinkedIn, Indeed, etc.), filters by keywords, and serves a static dashboard. The scraper runs on **GitHub Actions** (daily + manual) and commits updated data to the repo; **GitHub Pages** serves the dashboard.

## Quick start

1. **Clone or create the repo** and push to GitHub.
2. **Enable GitHub Pages**: Settings → Pages → Source: Deploy from branch → Branch: `main` (or `master`) → root.
3. **Run the scraper**: Actions → "Scrape crypto jobs" → Run workflow (or wait for the daily schedule).
4. **View the dashboard**: `https://<username>.github.io/<repo>/`

## Local run

```bash
cd crypto-jobs
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m src.run
```

Then open `index.html` in a browser (or use a local server so `data/jobs.json` loads: e.g. `python -m http.server 8000` and visit `http://localhost:8000`).

## Config

- **`config/companies.yaml`** — Greenhouse board slugs, Lever site ids, crypto board RSS/API URLs, and optional **JobSpy** (LinkedIn, Indeed) settings. Add or remove sources here.
- **`config/keywords.yaml`** — Keywords used to filter jobs (title + snippet). Jobs matching any keyword are kept.

## Project layout

- **`src/run.py`** — Orchestrator: loads config (YAML + optional slug files), runs scrapers, dedupes, filters, writes `data/jobs.json` and `data/last_run.txt`.
- **`src/discover_boards.py`** — Discovers valid Greenhouse/Lever boards from seed files and appends them to `greenhouse_slugs.txt` / `lever_sites.txt`.
- **`src/scrapers/`** — Greenhouse, Lever, crypto board (RSS), and JobSpy (LinkedIn, Indeed, etc.) clients.
- **`config/seed_greenhouse_slugs.txt`**, **`config/seed_lever_sites.txt`** — Candidate slugs for discovery.
- **`config/greenhouse_slugs.txt`**, **`config/lever_sites.txt`** — Optional; discovered (or manually added) boards; merged with YAML at run time.
- **`data/jobs.json`** — Generated job list (committed so the dashboard can load it).
- **`index.html`**, **`app.js`**, **`styles.css`** — Static dashboard (filters, sort, table).
- **`.github/workflows/scrape-jobs.yml`** — Runs scraper on schedule and on manual dispatch, then commits `data/`.

## Adding companies

Edit `config/companies.yaml`:

- **Greenhouse**: use the board slug from the company’s job URL (e.g. `boards.greenhouse.io/coinbase` → slug `coinbase`).
- **Lever**: use the site name from the URL (e.g. `jobs.lever.co/uniswap` → id `uniswap`).
- **Crypto boards**: add `url` and optional `name` for RSS/API endpoints.

No code changes needed when adding new entries to the config.

## All-encompassing mode (max coverage)

Greenhouse and Lever do **not** expose a public list of all boards/sites. To get as many crypto/blockchain jobs as possible:

1. **Discovery** — Populate optional slug/site lists from seed files:
   ```bash
   python -m src.discover_boards
   ```
   - Reads `config/seed_greenhouse_slugs.txt` and `config/seed_lever_sites.txt` (one slug/id per line).
   - Pings each Greenhouse/Lever API; valid boards are **appended** to `config/greenhouse_slugs.txt` and `config/lever_sites.txt`.
   - The main scraper then uses **YAML + these files** (merged). Run discovery once (or periodically) to grow the list.

2. **Optional slug files** — The scraper automatically merges:
   - **`config/greenhouse_slugs.txt`** — extra Greenhouse board slugs (one per line).
   - **`config/lever_sites.txt`** — extra Lever site ids (one per line).

3. **RSS** — Multiple crypto job board feeds are in `config/companies.yaml` under `crypto_boards`; add any RSS URLs you find for broader coverage.

4. **Keywords** — All jobs are filtered by `config/keywords.yaml`, so only roles matching terms like *blockchain*, *crypto*, *web3*, etc. are kept. Expanding boards/slugs only adds more *crypto-relevant* jobs.

**Suggested workflow:** Run `python -m src.discover_boards` once (takes a while due to rate limiting), then run `python -m src.run` as usual. Add more candidate slugs to the seed files and re-run discovery to grow coverage over time.

### JobSpy (LinkedIn, Indeed)

The scraper can pull jobs from **LinkedIn** and **Indeed** via [JobSpy](https://github.com/speedyapply/JobSpy). Enable it in `config/companies.yaml` under `jobspy` (enabled by default). You can set `sites: [indeed]` to use only Indeed (LinkedIn rate-limits aggressively; JobSpy’s docs recommend proxies for heavy LinkedIn use). Results are merged with other sources and filtered by `keywords.yaml`.
