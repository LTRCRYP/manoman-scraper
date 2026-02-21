"""
Lever job postings API client.
GET https://api.lever.co/v0/postings/{site}?mode=json
"""

import logging
from typing import Any

import requests

from src.normalize import normalize_job

LOG = logging.getLogger(__name__)
BASE = "https://api.lever.co/v0/postings"


def _location_from_categories(categories: Any) -> str | None:
    if not categories or not isinstance(categories, dict):
        return None
    loc = categories.get("location")
    if isinstance(loc, str) and loc.strip():
        return loc.strip()
    all_loc = categories.get("allLocations")
    if isinstance(all_loc, list) and all_loc:
        return ", ".join(str(x) for x in all_loc[:3])
    return None


def fetch_lever_jobs(
    companies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Fetch jobs from Lever for each company.
    companies: list of {id: str, name: str}
    Returns list of normalized job dicts.
    """
    out: list[dict[str, Any]] = []
    for c in companies:
        site_id = (c.get("id") or "").strip()
        name = (c.get("name") or site_id or "").strip()
        if not site_id:
            continue
        try:
            url = f"{BASE}/{site_id}"
            r = requests.get(url, params={"mode": "json"}, timeout=15)
            r.raise_for_status()
            jobs = r.json()
        except Exception as e:
            LOG.warning("Lever %s (%s): %s", site_id, name, e)
            continue
        if not isinstance(jobs, list):
            continue
        for j in jobs:
            title = j.get("text") or ""
            url_str = j.get("hostedUrl") or ""
            loc = _location_from_categories(j.get("categories"))
            snippet = (j.get("descriptionPlain") or j.get("openingPlain") or "")[:500]
            normalized = normalize_job(
                title=title,
                company=name,
                url=url_str,
                source="lever",
                location=loc,
                posted_date=None,
                snippet=snippet or None,
            )
            if normalized["url"] and normalized["title"]:
                out.append(normalized)
    return out
