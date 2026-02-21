"""
Orchestrator: load config, run all scrapers, merge, dedupe, filter by keywords,
write data/jobs.json and data/last_run.txt.
Run from repo root: python src/run.py
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.filters import filter_jobs_by_keywords, load_keywords
from src.normalize import deduplicate_jobs
from src.scrapers import (
    fetch_crypto_board_jobs,
    fetch_greenhouse_jobs,
    fetch_jobspy_jobs,
    fetch_lever_jobs,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
)
LOG = logging.getLogger(__name__)


def _project_root() -> Path:
    """Repo root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def _load_yaml(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_slugs_from_file(path: Path, key_slug: str, key_name: str) -> list[dict]:
    """Load one slug/id per line from a text file (# = comment). Returns list of dicts."""
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#")[0].strip()
            if not line:
                continue
            out.append({key_slug: line, key_name: line})
    return out


def main() -> None:
    root = _project_root()
    os.chdir(root)

    config_dir = root / "config"
    companies_path = config_dir / "companies.yaml"
    keywords_path = config_dir / "keywords.yaml"
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    companies_cfg = _load_yaml(companies_path)
    if not isinstance(companies_cfg, dict):
        companies_cfg = {}
    keywords_cfg = _load_yaml(keywords_path)
    if isinstance(keywords_cfg, dict) and "keywords" in keywords_cfg:
        keywords_list = list(keywords_cfg["keywords"] or [])
    elif isinstance(keywords_cfg, list):
        keywords_list = list(keywords_cfg)
    else:
        keywords_list = []

    all_jobs: list[dict] = []

    # Greenhouse: YAML lists + optional greenhouse_slugs.txt (one slug per line)
    greenhouse_list: list[dict] = []
    for key in ("greenhouse", "greenhouse_non_crypto"):
        part = companies_cfg.get(key) or []
        if isinstance(part, list):
            greenhouse_list.extend(part)
    extra_gh = _load_slugs_from_file(config_dir / "greenhouse_slugs.txt", "slug", "name")
    if extra_gh:
        greenhouse_list = greenhouse_list + extra_gh
        LOG.info("Greenhouse: %d from YAML + %d from greenhouse_slugs.txt", len(greenhouse_list) - len(extra_gh), len(extra_gh))
    if greenhouse_list:
        jobs = fetch_greenhouse_jobs(greenhouse_list)
        all_jobs.extend(jobs)
        LOG.info("Greenhouse: %d jobs", len(jobs))

    # Lever: YAML list + optional lever_sites.txt (one site id per line)
    lever_list = list(companies_cfg.get("lever") or [])
    if not isinstance(lever_list, list):
        lever_list = []
    extra_lever = _load_slugs_from_file(config_dir / "lever_sites.txt", "id", "name")
    if extra_lever:
        lever_list = lever_list + extra_lever
        LOG.info("Lever: %d from YAML + %d from lever_sites.txt", len(lever_list) - len(extra_lever), len(extra_lever))
    if lever_list:
        jobs = fetch_lever_jobs(lever_list)
        all_jobs.extend(jobs)
        LOG.info("Lever: %d jobs", len(jobs))

    crypto_boards_list = companies_cfg.get("crypto_boards") or []
    if isinstance(crypto_boards_list, list):
        jobs = fetch_crypto_board_jobs(crypto_boards_list)
        all_jobs.extend(jobs)
        LOG.info("Crypto boards: %d jobs", len(jobs))

    # JobSpy: LinkedIn, Indeed, etc. (optional; requires python-jobspy)
    jobspy_cfg = companies_cfg.get("jobspy")
    if isinstance(jobspy_cfg, dict) and jobspy_cfg.get("enabled"):
        terms = jobspy_cfg.get("search_terms") or ["blockchain", "crypto", "web3"]
        sites = jobspy_cfg.get("sites") or ["linkedin", "indeed"]
        wanted = jobspy_cfg.get("results_wanted") or 40
        hours = jobspy_cfg.get("hours_old")
        jobs = fetch_jobspy_jobs(
            search_terms=terms,
            site_name=sites,
            results_wanted=wanted,
            hours_old=hours,
        )
        all_jobs.extend(jobs)
        LOG.info("JobSpy: %d jobs", len(jobs))

    all_jobs = deduplicate_jobs(all_jobs)
    LOG.info("After dedupe: %d jobs", len(all_jobs))

    if keywords_list:
        all_jobs = filter_jobs_by_keywords(all_jobs, keywords_list)
        LOG.info("After keyword filter: %d jobs", len(all_jobs))

    jobs_path = data_dir / "jobs.json"
    with open(jobs_path, "w", encoding="utf-8") as f:
        json.dump(
            {"jobs": all_jobs, "count": len(all_jobs)},
            f,
            indent=2,
            ensure_ascii=False,
        )
    LOG.info("Wrote %s", jobs_path)

    last_run_path = data_dir / "last_run.txt"
    with open(last_run_path, "w", encoding="utf-8") as f:
        f.write(datetime.now(tz=timezone.utc).isoformat())
    LOG.info("Wrote %s", last_run_path)


if __name__ == "__main__":
    main()
