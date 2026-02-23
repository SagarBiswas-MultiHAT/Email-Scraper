"""Email quality scoring rules."""

from __future__ import annotations

from typing import Any


def parse_confidence(hunter_result: dict[str, Any]) -> float | None:
    """Parse confidence/score value from provider payload."""
    for key in ("confidence", "score"):
        value = hunter_result.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def result_is_deliverable(hunter_result: dict[str, Any]) -> bool:
    """Return True for known deliverable-like statuses."""
    truthy = {"deliverable", "deliverable (smtp)", "valid", "ok", "success", "deliverable?"}
    for key in ("result", "status", "status_text", "result_code"):
        value = hunter_result.get(key)
        if value is None:
            continue
        if str(value).strip().lower() in truthy:
            return True
    return False


def compute_quality(mx_ok: bool, hunter_result: dict[str, Any], source_count: int) -> str:
    """Compute High/Medium/Low quality from MX, Hunter, and source confidence."""
    if result_is_deliverable(hunter_result):
        return "High"

    confidence = parse_confidence(hunter_result)
    if confidence is not None:
        normalized = confidence * 100.0 if confidence <= 1.0 else confidence
        if normalized >= 80.0 and (mx_ok or source_count >= 1):
            return "High"
        if 50.0 <= normalized < 80.0 and (mx_ok or source_count >= 1):
            return "Medium"

    if mx_ok and source_count >= 3:
        return "High"
    if mx_ok and source_count >= 1:
        return "Medium"
    return "Low"
