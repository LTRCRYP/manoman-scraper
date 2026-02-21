"""
Greenhouse job board API client.
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
"""

import logging
from typing import Any

import requests

from src.normalize import normalize_job

LOG = logging.getLogger(__name__)
BASE = "https://boards-api.greenhouse.io/v1/boards"


def fetch_greenhouse_jobs(
    companies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Fetch jobs from Greenhouse for each company.
    companies: list of {slug: str, name: str}
    Returns list of normalized job dicts.
    """
    out: list[dict[str, Any]] = []
    for c in companies:
        slug = (c.get("slug") or "").strip()
        name = (c.get("name") or slug or "").strip()
        if not slug:
            continue
        try:
            url = f"{BASE}/{slug}/jobs"
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            LOG.warning("Greenhouse %s (%s): %s", slug, name, e)
            continue
        jobs = data.get("jobs") or []
        for j in jobs:
            loc = j.get("location") or {}
            loc_name = loc.get("name") if isinstance(loc, dict) else None
            normalized = normalize_job(
                title=j.get("title") or "",
                company=name,
                url=j.get("absolute_url") or "",
                source="greenhouse",
                location=loc_name,
                posted_date=j.get("updated_at"),
                snippet=None,
            )
            if normalized["url"] and normalized["title"]:
                out.append(normalized)
    return out
