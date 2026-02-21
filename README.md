# Crypto & Web3 Job Scraper + Dashboard

Aggregates crypto/blockchain job listings from **Greenhouse**, **Lever**, and **crypto job boards** (RSS), filters by keywords, and serves a static dashboard. The scraper runs on **GitHub Actions** (daily + manual) and commits updated data to the repo; **GitHub Pages** serves the dashboard.

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

- **`config/companies.yaml`** — Greenhouse board slugs, Lever site ids, and crypto board RSS/API URLs. Add or remove companies here.
- **`config/keywords.yaml`** — Keywords used to filter jobs (title + snippet). Jobs matching any keyword are kept.

## Project layout

- **`src/run.py`** — Orchestrator: loads config, runs scrapers, dedupes, filters, writes `data/jobs.json` and `data/last_run.txt`.
- **`src/scrapers/`** — Greenhouse, Lever, and crypto board (RSS) clients.
- **`data/jobs.json`** — Generated job list (committed so the dashboard can load it).
- **`index.html`**, **`app.js`**, **`styles.css`** — Static dashboard (filters, sort, table).
- **`.github/workflows/scrape-jobs.yml`** — Runs scraper on schedule and on manual dispatch, then commits `data/`.

## Adding companies

Edit `config/companies.yaml`:

- **Greenhouse**: use the board slug from the company’s job URL (e.g. `boards.greenhouse.io/coinbase` → slug `coinbase`).
- **Lever**: use the site name from the URL (e.g. `jobs.lever.co/uniswap` → id `uniswap`).
- **Crypto boards**: add `url` and optional `name` for RSS/API endpoints.

No code changes needed when adding new entries to the config.
