"""
Discover valid Greenhouse boards and Lever sites from seed lists.
Reads config/seed_greenhouse_slugs.txt and config/seed_lever_sites.txt (one slug/id per line),
pings each API, and appends valid boards to config/greenhouse_slugs.txt and config/lever_sites.txt.
Run from repo root: python -m src.discover_boards
"""

import logging
import time
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
)
LOG = logging.getLogger(__name__)

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards"
LEVER_API = "https://api.lever.co/v0/postings"
REQUEST_DELAY_SEC = 0.5


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_seed(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#")[0].strip().lower()
            if line and line not in out:
                out.append(line)
    return out


def _load_existing(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#")[0].strip().lower()
            if line:
                out.add(line)
    return out


def _append_slugs(path: Path, slugs: list[str], existing: set[str]) -> None:
    added = [s for s in slugs if s not in existing]
    if not added:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for s in added:
            f.write(s + "\n")
    LOG.info("Appended %d slugs to %s", len(added), path.name)


def main() -> None:
    root = _project_root()
    config_dir = root / "config"

    seed_gh = config_dir / "seed_greenhouse_slugs.txt"
    seed_lever = config_dir / "seed_lever_sites.txt"
    out_gh = config_dir / "greenhouse_slugs.txt"
    out_lever = config_dir / "lever_sites.txt"

    existing_gh = _load_existing(out_gh)
    existing_lever = _load_existing(out_lever)

    # Greenhouse discovery
    gh_candidates = _load_seed(seed_gh)
    if not gh_candidates:
        LOG.info("No seed file or empty: %s", seed_gh)
    else:
        valid_gh = []
        for i, slug in enumerate(gh_candidates):
            if slug in existing_gh or slug in valid_gh:
                continue
            time.sleep(REQUEST_DELAY_SEC)
            try:
                r = requests.get(f"{GREENHOUSE_API}/{slug}/jobs", timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("jobs") is not None:
                        valid_gh.append(slug)
                        if len(valid_gh) % 50 == 0:
                            LOG.info("Greenhouse: %d valid so far (checked %d)", len(valid_gh), i + 1)
            except Exception as e:
                LOG.debug("Greenhouse %s: %s", slug, e)
        _append_slugs(out_gh, valid_gh, existing_gh)
        existing_gh |= set(valid_gh)
        LOG.info("Greenhouse: %d new boards discovered (total in file: %d)", len(valid_gh), len(existing_gh))

    # Lever discovery
    lever_candidates = _load_seed(seed_lever)
    if not lever_candidates:
        LOG.info("No seed file or empty: %s", seed_lever)
    else:
        valid_lever = []
        for i, site_id in enumerate(lever_candidates):
            if site_id in existing_lever or site_id in valid_lever:
                continue
            time.sleep(REQUEST_DELAY_SEC)
            try:
                r = requests.get(f"{LEVER_API}/{site_id}", params={"mode": "json"}, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list) and len(data) > 0:
                        valid_lever.append(site_id)
                        if len(valid_lever) % 50 == 0:
                            LOG.info("Lever: %d valid so far (checked %d)", len(valid_lever), i + 1)
            except Exception as e:
                LOG.debug("Lever %s: %s", site_id, e)
        _append_slugs(out_lever, valid_lever, existing_lever)
        existing_lever |= set(valid_lever)
        LOG.info("Lever: %d new sites discovered (total in file: %d)", len(valid_lever), len(existing_lever))


if __name__ == "__main__":
    main()
