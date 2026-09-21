"""Unit tests for the decision bands."""
import pytest

from nasih_service.domain.policies import REJECT_THRESHOLD_DEFAULT, REVIEW_BAND, decide


@pytest.mark.unit
@pytest.mark.parametrize("p, expected", [
    (0.699999, "manual_review"),   # just under the reject threshold
    (0.70,     "reject"),          # boundary is inclusive
    (0.449999, "auto_approve"),
    (0.45,     "manual_review"),
    (0.0,      "auto_approve"),
    (1.0,      "reject"),
])
def test_decision_bands(p, expected):
    assert decide(p, reject_threshold=0.70) == expected


@pytest.mark.unit
def test_default_threshold_matches_policy_constant():
    assert decide(REJECT_THRESHOLD_DEFAULT) == "reject"
    assert decide(REJECT_THRESHOLD_DEFAULT - 1e-9) == "manual_review"


@pytest.mark.unit
@pytest.mark.parametrize("threshold", [0.50, 0.70, 0.95])
def test_bands_move_with_the_threshold(threshold):
    assert decide(threshold, reject_threshold=threshold) == "reject"
    assert decide(threshold - REVIEW_BAND, reject_threshold=threshold) == "manual_review"
    assert decide(threshold - REVIEW_BAND - 1e-9, reject_threshold=threshold) == "auto_approve"
