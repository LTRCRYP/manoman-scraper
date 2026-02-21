"""
Keyword-based filter: keep jobs whose title or description/snippet
contains at least one of the configured keywords (case-insensitive).
"""

from typing import Any


def load_keywords(keywords: list[str]) -> list[str]:
    """Normalize keyword list (strip, lower, drop empty)."""
    return [k.strip().lower() for k in keywords if k and k.strip()]


def job_matches_keywords(
    job: dict[str, Any],
    keywords: list[str],
) -> bool:
    """Return True if the job's title or snippet contains any keyword."""
    if not keywords:
        return True
    text_parts = [
        (job.get("title") or ""),
        (job.get("snippet") or ""),
        (job.get("description") or ""),
    ]
    combined = " ".join(text_parts).lower()
    return any(kw in combined for kw in keywords)


def filter_jobs_by_keywords(
    jobs: list[dict[str, Any]],
    keywords: list[str],
) -> list[dict[str, Any]]:
    """Return only jobs that match at least one keyword."""
    norm = load_keywords(keywords)
    return [j for j in jobs if job_matches_keywords(j, norm)]
