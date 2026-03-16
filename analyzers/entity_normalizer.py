"""Entity normalization utilities."""

import logging
import re
import unicodedata

from analyzers.wine_entities_data import (
    GRAPE_NORMALIZATION,
    REGION_NORMALIZATION,
    WINERY_NORMALIZATION,
)

logger = logging.getLogger(__name__)

# Common prefix/suffix patterns to strip for normalization
_STRIP_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s+|\s+$"),  # leading/trailing whitespace
    re.compile(r"\s{2,}"),  # multiple spaces
    re.compile(r"[''`]"),  # curly quotes to straight
]

# Known entity type aliases for edge case handling
_ENTITY_TYPE_ALIASES: dict[str, str] = {
    "grape": "grape_variety",
    "variety": "grape_variety",
    "varietal": "grape_variety",
    "appellation": "region",
    "area": "region",
    "producer": "winery",
    "estate": "winery",
    "domaine": "winery",
    "chateau": "winery",
}

# Minimum/maximum value lengths for validation
_VALUE_LENGTH_LIMITS: dict[str, tuple[int, int]] = {
    "grape_variety": (2, 100),
    "region": (2, 150),
    "winery": (2, 200),
    "climate_zone": (3, 50),
}


def normalize_unicode(text: str) -> str:
    """Remove accents and normalize unicode characters.

    Args:
        text: Input text

    Returns:
        Normalized text without accents
    """
    # NFD = Canonical Decomposition
    nfd = unicodedata.normalize("NFD", text)
    # Remove combining characters (accents)
    return "".join(char for char in nfd if unicodedata.category(char) != "Mn")


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace: strip and collapse multiple spaces."""
    text = text.strip()
    return re.sub(r"\s{2,}", " ", text)


def _normalize_quotes(text: str) -> str:
    """Normalize curly/smart quotes to straight quotes."""
    return (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )


def resolve_entity_type(entity_type: str) -> str:
    """Resolve entity type aliases to canonical form.

    Args:
        entity_type: Possibly aliased entity type name.

    Returns:
        Canonical entity type name.
    """
    normalized = entity_type.lower().strip()
    return _ENTITY_TYPE_ALIASES.get(normalized, normalized)


def validate_entity_value(entity_type: str, value: str) -> list[str]:
    """Validate an entity value for common issues.

    Args:
        entity_type: Type of entity.
        value: Entity value to validate.

    Returns:
        List of warning messages (empty if valid).
    """
    warnings: list[str] = []
    canonical_type = resolve_entity_type(entity_type)

    if not value or not isinstance(value, str):
        warnings.append(f"Empty or non-string value for entity type '{canonical_type}'")
        return warnings

    cleaned = _normalize_whitespace(value)
    if not cleaned:
        warnings.append(f"Value is only whitespace for entity type '{canonical_type}'")
        return warnings

    # Length validation
    limits = _VALUE_LENGTH_LIMITS.get(canonical_type)
    if limits:
        min_len, max_len = limits
        if len(cleaned) < min_len:
            warnings.append(
                f"Value '{cleaned}' too short for '{canonical_type}' (min {min_len} chars)"
            )
        if len(cleaned) > max_len:
            warnings.append(
                f"Value '{cleaned[:50]}...' too long for '{canonical_type}' (max {max_len} chars)"
            )

    # Check for suspicious patterns
    if re.match(r"^\d+$", cleaned):
        warnings.append(f"Value '{cleaned}' is purely numeric for '{canonical_type}'")
    if re.match(r"^[^a-zA-Z\u00C0-\u024F\uAC00-\uD7AF]+$", cleaned):
        warnings.append(f"Value '{cleaned}' has no alphabetic chars for '{canonical_type}'")

    return warnings


def normalize_entity(entity_type: str, value: str) -> str:
    """Normalize entity value to canonical form.

    Handles edge cases including:
    - Unicode accent variations (e.g., Gewurztraminer vs Gewürztraminer)
    - Whitespace normalization
    - Smart/curly quote normalization
    - Entity type aliasing
    - Case-insensitive matching with accent-stripped fallback

    Args:
        entity_type: Type of entity (grape_variety, region, winery)
        value: Entity value to normalize

    Returns:
        Normalized canonical value
    """
    if not value or not isinstance(value, str):
        return value

    # Pre-process: normalize whitespace and quotes
    cleaned = _normalize_whitespace(value)
    cleaned = _normalize_quotes(cleaned)

    # Resolve entity type aliases
    canonical_type = resolve_entity_type(entity_type)

    # Convert to lowercase for lookup
    value_lower = cleaned.lower()

    # Type-specific normalization with fallback chain
    normalization_map: dict[str, str] | None = None
    if canonical_type == "grape_variety":
        normalization_map = GRAPE_NORMALIZATION
    elif canonical_type == "region":
        normalization_map = REGION_NORMALIZATION
    elif canonical_type == "winery":
        normalization_map = WINERY_NORMALIZATION

    if normalization_map is not None:
        # Direct lookup
        if value_lower in normalization_map:
            return normalization_map[value_lower]

        # Accent-stripped fallback
        value_no_accents = normalize_unicode(value_lower)
        if value_no_accents in normalization_map:
            return normalization_map[value_no_accents]

        # Hyphen/space variation fallback (e.g., "pinot noir" vs "pinot-noir")
        value_hyphen_to_space = value_lower.replace("-", " ")
        if value_hyphen_to_space in normalization_map:
            return normalization_map[value_hyphen_to_space]
        value_space_to_hyphen = value_lower.replace(" ", "-")
        if value_space_to_hyphen in normalization_map:
            return normalization_map[value_space_to_hyphen]

    # If no normalization found, return cleaned value
    return cleaned


def calculate_entity_confidence(
    entity_type: str,
    value: str,
    source: str,
    text: str,
) -> float:
    """Calculate confidence score for an extracted entity.

    Args:
        entity_type: Type of entity
        value: Entity value
        source: Where it was found (title, summary, content)
        text: The text where it was found

    Returns:
        Confidence score (0.0 - 1.0)
    """
    # Base confidence by source
    base_confidence = {
        "title": 1.0,
        "summary": 0.8,
        "content": 0.6,
        "spacy": 0.55,
    }.get(source, 0.5)

    # Boost confidence if entity appears multiple times
    import re

    pattern = r"\b" + re.escape(value.lower()) + r"\b"
    occurrences = len(re.findall(pattern, text.lower()))

    if occurrences > 1:
        base_confidence = min(1.0, base_confidence + (occurrences - 1) * 0.05)

    # Boost confidence for well-known entities (capitalized properly)
    if value[0].isupper() and entity_type in {"winery", "region"}:
        base_confidence = min(1.0, base_confidence + 0.05)

    return round(base_confidence, 2)


def deduplicate_entities(entities: list[dict]) -> list[dict]:
    """Remove duplicate entities, keeping highest confidence.

    Args:
        entities: List of entity dicts with type, value, confidence, source

    Returns:
        Deduplicated list of entities
    """
    # Group by (type, normalized_value)
    entity_map: dict[tuple[str, str], dict] = {}

    for entity in entities:
        entity_type = entity["type"]
        entity_value = entity["value"]

        # Normalize the value
        normalized_value = normalize_entity(entity_type, entity_value)

        key = (entity_type, normalized_value)

        # Keep entity with highest confidence
        if key not in entity_map or entity["confidence"] > entity_map[key]["confidence"]:
            # Update entity value to normalized form
            entity_copy = entity.copy()
            entity_copy["value"] = normalized_value
            entity_map[key] = entity_copy

    return list(entity_map.values())
