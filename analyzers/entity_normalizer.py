"""Entity normalization utilities."""

import unicodedata

from analyzers.wine_entities_data import (
    GRAPE_NORMALIZATION,
    REGION_NORMALIZATION,
    WINERY_NORMALIZATION,
)


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


def normalize_entity(entity_type: str, value: str) -> str:
    """Normalize entity value to canonical form.

    Args:
        entity_type: Type of entity (grape_variety, region, winery)
        value: Entity value to normalize

    Returns:
        Normalized canonical value
    """
    # Convert to lowercase for lookup
    value_lower = value.lower()

    # Type-specific normalization
    if entity_type == "grape_variety":
        if value_lower in GRAPE_NORMALIZATION:
            return GRAPE_NORMALIZATION[value_lower]
        # If not in map, try without accents
        value_no_accents = normalize_unicode(value_lower)
        if value_no_accents in GRAPE_NORMALIZATION:
            return GRAPE_NORMALIZATION[value_no_accents]

    elif entity_type == "region":
        if value_lower in REGION_NORMALIZATION:
            return REGION_NORMALIZATION[value_lower]
        value_no_accents = normalize_unicode(value_lower)
        if value_no_accents in REGION_NORMALIZATION:
            return REGION_NORMALIZATION[value_no_accents]

    elif entity_type == "winery":
        if value_lower in WINERY_NORMALIZATION:
            return WINERY_NORMALIZATION[value_lower]
        value_no_accents = normalize_unicode(value_lower)
        if value_no_accents in WINERY_NORMALIZATION:
            return WINERY_NORMALIZATION[value_no_accents]

    # If no normalization found, return original value
    return value


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
