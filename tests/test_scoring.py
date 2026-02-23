from email_harvester.scoring import compute_quality, parse_confidence, result_is_deliverable


def test_result_is_deliverable() -> None:
    assert result_is_deliverable({"result": "deliverable"}) is True
    assert result_is_deliverable({"status": "unknown"}) is False


def test_parse_confidence_handles_numbers_and_strings() -> None:
    assert parse_confidence({"confidence": 90}) == 90.0
    assert parse_confidence({"score": "0.95"}) == 0.95
    assert parse_confidence({"score": "bad"}) is None


def test_compute_quality_prefers_hunter_and_mx() -> None:
    assert compute_quality(True, {"result": "deliverable"}, 1) == "High"
    assert compute_quality(True, {"confidence": 65}, 1) == "Medium"
    assert compute_quality(True, {}, 4) == "High"
    assert compute_quality(False, {}, 0) == "Low"
