from __future__ import annotations

import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlparse


_ERROR_PAGE_TITLE_RE = re.compile(
    r"^(?:"
    r"just a moment\.{0,3}|"
    r"attention required!?|"
    r"access denied|"
    r"403 forbidden|"
    r"404(?: not found)?|"
    r"not found|"
    r"enable javascript and cookies to continue"
    r")(?:\s*\|\s*.*)?$",
    re.IGNORECASE,
)


def is_challenge_or_error_page(title: str | None, body: str | None = None) -> bool:
    """True when a fetched document is a bot wall, Cloudflare interstitial, or error page.

    These responses are not articles. Callers must drop them instead of storing the page.
    """
    title_text = (title or "").strip()
    body_text = body or ""
    if title_text and _ERROR_PAGE_TITLE_RE.match(title_text):
        return True

    blob = f"{title_text}\n{body_text}".lower()
    if "just a moment" in blob and (
        "cloudflare" in blob or "security verification" in blob or "verify you are human" in blob
    ):
        return True
    if "attention required" in blob and ("cloudflare" in blob or "been blocked" in blob):
        return True
    if "cf-browser-verification" in blob or "challenges.cloudflare.com" in blob:
        return True
    # winereview.co.kr returns HTTP 200 with a CUPID/slowAES cookie wall, not a feed.
    if "slowaes.decrypt" in blob and "cupid" in blob:
        return True
    return False


def normalize_title(title: str) -> str:
    if not title:
        return ""

    normalized = title.lower()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"[^\w\s\-]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def validate_url_format(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def is_similar_url(url1: str, url2: str, threshold: float = 0.8) -> bool:
    try:
        parsed1 = urlparse(url1)
        parsed2 = urlparse(url2)

        if parsed1.netloc != parsed2.netloc:
            return False

        path1 = parsed1.path
        path2 = parsed2.path

        if path1 == path2:
            return True

        ratio = SequenceMatcher(None, path1, path2).ratio()
        return ratio >= threshold
    except Exception:
        return False


def detect_duplicate_articles(
    title1: str,
    url1: str,
    title2: str,
    url2: str,
    title_threshold: float = 0.85,
    url_threshold: float = 0.8,
) -> bool:
    norm_title1 = normalize_title(title1)
    norm_title2 = normalize_title(title2)

    title_ratio = SequenceMatcher(None, norm_title1, norm_title2).ratio()
    if title_ratio < title_threshold:
        return False

    return is_similar_url(url1, url2, url_threshold)


def _get_value(article: Any, *keys: str) -> Any:
    if isinstance(article, dict):
        for key in keys:
            if key in article:
                return article[key]
        return None

    for key in keys:
        if hasattr(article, key):
            return getattr(article, key)
    return None


def validate_article(article: Any) -> tuple[bool, list[str]]:
    errors: list[str] = []

    title = _get_value(article, "title")
    link = _get_value(article, "link", "url")
    summary = _get_value(article, "summary", "content")
    source = _get_value(article, "source", "source_id", "source_name")
    category = _get_value(article, "category", "content_type")

    if not title or not isinstance(title, str):
        errors.append("title is missing or not a string")
    elif len(title.strip()) == 0:
        errors.append("title is empty")

    if not link or not isinstance(link, str):
        errors.append("link is missing or not a string")
    elif not validate_url_format(link):
        errors.append(f"link has invalid URL format: {link}")

    if not summary or not isinstance(summary, str):
        errors.append("summary is missing or not a string")
    elif len(summary.strip()) == 0:
        errors.append("summary is empty")

    if not source or not isinstance(source, str):
        errors.append("source is missing or not a string")

    if not category or not isinstance(category, str):
        errors.append("category is missing or not a string")

    title_text = title if isinstance(title, str) else ""
    summary_text = summary if isinstance(summary, str) else ""
    if is_challenge_or_error_page(title_text, summary_text):
        errors.append("content appears to be a challenge or error page")

    return len(errors) == 0, errors


def validate_rating(rating: float | None) -> bool:
    if rating is None:
        return True
    return 0.0 <= rating <= 5.0


def validate_vintage(vintage: int | None) -> bool:
    if vintage is None:
        return True
    return 1900 <= vintage <= datetime.now(tz=UTC).year
