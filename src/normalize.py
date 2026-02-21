"""
Normalize job records to a common schema for merging and display.
Schema: title, company, url, location, posted_date, source, snippet
"""

from typing import Any


def normalize_job(
    title: str,
    company: str,
    url: str,
    source: str,
    *,
    location: str | None = None,
    posted_date: str | None = None,
    snippet: str | None = None,
) -> dict[str, Any]:
    """Build a normalized job dict. All required fields must be non-empty."""
    return {
        "title": (title or "").strip(),
        "company": (company or "").strip(),
        "url": (url or "").strip(),
        "location": (location or "").strip() or None,
        "posted_date": (posted_date or "").strip() or None,
        "source": (source or "").strip(),
        "snippet": (snippet or "").strip() or None,
    }


def deduplicate_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate by (company, title, url). Keeps first occurrence."""
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, Any]] = []
    for j in jobs:
        key = (
            (j.get("company") or "").strip(),
            (j.get("title") or "").strip(),
            (j.get("url") or "").strip(),
        )
        if not key[0] or not key[1] or not key[2]:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out
