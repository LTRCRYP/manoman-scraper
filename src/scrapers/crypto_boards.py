"""
Crypto job boards: RSS feeds and simple APIs.
"""

import logging
from typing import Any
from urllib.parse import urlparse

import requests

try:
    import feedparser
except ImportError:
    feedparser = None  # type: ignore

from src.normalize import normalize_job

LOG = logging.getLogger(__name__)


def _parse_rss_feed(
    feed_url: str,
    source_name: str,
) -> list[dict[str, Any]]:
    """Parse an RSS/Atom feed and return normalized jobs."""
    out: list[dict[str, Any]] = []
    if not feedparser:
        LOG.warning("feedparser not installed; skipping RSS %s", feed_url)
        return out
    try:
        resp = requests.get(feed_url, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        LOG.warning("RSS %s (%s): %s", feed_url, source_name, e)
        return out
    for entry in feed.get("entries") or []:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        summary = (entry.get("summary") or entry.get("description") or "")[:500]
        # Try to get company from source tag or author
        company = ""
        src = entry.get("source") or {}
        if isinstance(src, dict) and src.get("title"):
            company = str(src.get("title", "")).strip()
        if not company and entry.get("author"):
            company = str(entry.get("author", "")).strip()
        # Some feeds put company in title like "Company Name - Job Title"
        if not company and " - " in title:
            company = title.split(" - ", 1)[0].strip()
        normalized = normalize_job(
            title=title,
            company=company or source_name,
            url=link,
            source=source_name,
            location=None,
            posted_date=entry.get("published"),
            snippet=summary or None,
        )
        out.append(normalized)
    return out


def fetch_crypto_board_jobs(
    boards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Fetch jobs from crypto job board URLs (RSS or API).
    boards: list of {url: str, name: str (optional)}
    Returns list of normalized job dicts.
    """
    out: list[dict[str, Any]] = []
    for b in boards:
        url = (b.get("url") or "").strip()
        name = (b.get("name") or _name_from_url(url) or "crypto_board").strip()
        if not url:
            continue
        # Treat as RSS if it looks like feed or we get XML
        if "rss" in url.lower() or "feed" in url.lower() or url.endswith(".xml"):
            out.extend(_parse_rss_feed(url, name))
            continue
        # Optional: future API endpoints could be added here
        LOG.debug("Skipping unknown board format: %s", url)
    return out


def _name_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        netloc = (parsed.netloc or "").replace("www.", "")
        if netloc:
            return netloc.split(".")[0]
    except Exception:
        pass
    return ""
