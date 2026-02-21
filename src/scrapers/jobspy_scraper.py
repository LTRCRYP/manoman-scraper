"""
JobSpy-based scraper for LinkedIn, Indeed, Glassdoor, etc.
Uses https://github.com/speedyapply/JobSpy — install with: pip install python-jobspy
Optional: if not installed, this module logs and returns [].
"""

import logging
from typing import Any

from src.normalize import normalize_job

LOG = logging.getLogger(__name__)

try:
    from jobspy import scrape_jobs
except ImportError:
    scrape_jobs = None  # type: ignore


def _get(row: Any, *keys: str, default: str = "") -> str:
    """Get first present key from a pandas Series / dict (case-insensitive)."""
    for col in keys:
        for k in (col, col.lower(), col.upper()):
            try:
                if hasattr(row, "get") and k in row:
                    v = row.get(k)
                elif hasattr(row, "__getitem__"):
                    v = row[k] if k in row else getattr(row, k, None)
                else:
                    v = getattr(row, k, None)
            except (KeyError, TypeError):
                continue
            if v is not None and str(v).strip():
                return str(v).strip()
    return default


def _row_to_job(row: Any, site: str) -> dict[str, Any] | None:
    """Convert a JobSpy dataframe row to our normalized job dict."""
    title = _get(row, "title", "TITLE")
    company = _get(row, "company", "COMPANY")
    url = _get(row, "job_url", "JOB_URL")
    if not title or not url:
        return None
    city = _get(row, "city", "CITY")
    state = _get(row, "state", "STATE")
    location = ", ".join(filter(None, [city, state])) or None
    desc = _get(row, "description", "DESCRIPTION")
    snippet = (desc[:500] if desc else None) or None
    posted = _get(row, "date_posted", "DATE_POSTED") or None
    source = (_get(row, "site", "SITE") or site or "jobspy").lower()

    return normalize_job(
        title=title,
        company=company or "Unknown",
        url=url,
        source=source,
        location=location,
        posted_date=posted or None,
        snippet=snippet,
    )


def fetch_jobspy_jobs(
    search_terms: list[str],
    *,
    site_name: list[str] | None = None,
    results_wanted: int = 50,
    hours_old: int | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """
    Scrape jobs via JobSpy (LinkedIn, Indeed, etc.) for each search term.
    search_terms: e.g. ["blockchain", "crypto", "web3"]
    site_name: e.g. ["linkedin", "indeed"] (default: ["linkedin", "indeed"])
    results_wanted: per search term, per site (JobSpy caps ~1000 per search).
    hours_old: only jobs posted in the last N hours (optional).
    Returns list of normalized job dicts.
    """
    if scrape_jobs is None:
        LOG.warning("python-jobspy not installed; skip JobSpy scraper. pip install python-jobspy")
        return []

    sites = site_name or ["linkedin", "indeed"]
    out: list[dict[str, Any]] = []
    for term in search_terms:
        try:
            df = scrape_jobs(
                site_name=sites,
                search_term=term,
                results_wanted=results_wanted,
                hours_old=hours_old,
                verbose=0,
                **kwargs,
            )
        except Exception as e:
            LOG.warning("JobSpy search_term=%r: %s", term, e)
            continue
        if df is None or df.empty:
            continue
        n = 0
        for _, row in df.iterrows():
            job = _row_to_job(row, site="")
            if job and job.get("url") and job.get("title"):
                out.append(job)
                n += 1
        LOG.info("JobSpy %r: %d jobs", term, n)
    # Dedupe by url within this batch
    seen_urls: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for j in out:
        u = (j.get("url") or "").strip()
        if u and u not in seen_urls:
            seen_urls.add(u)
            deduped.append(j)
    return deduped
