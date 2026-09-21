"""Unit tests for the scoring arithmetic and the weights file."""
import json
import math

import pytest

from nasih_service.adapters.linear_model import LinearModel, _sigmoid


@pytest.mark.unit
@pytest.mark.parametrize("z, expected", [
    (0.0, 0.5),
    (1.0, 0.7310585786300049),
    (-1.0, 0.2689414213699951),
])
def test_sigmoid_known_values(z, expected):
    assert _sigmoid(z) == pytest.approx(expected)


@pytest.mark.unit
@pytest.mark.parametrize("z", [-1e5, -800.0, -710.0, 710.0, 800.0, 1e5])
def test_sigmoid_survives_extreme_inputs(z):
    """The naive 1/(1+exp(-z)) raises OverflowError below about -710."""
    p = _sigmoid(z)
    assert 0.0 <= p <= 1.0


@pytest.mark.unit
def test_sigmoid_is_symmetric():
    for z in (0.3, 2.0, 17.5):
        assert _sigmoid(-z) == pytest.approx(1.0 - _sigmoid(z))


@pytest.mark.unit
def test_predict_proba_matches_hand_computation():
    model = LinearModel(weights={"a": 2.0, "b": -0.5}, intercept=1.0,
                        model_version="test-1")
    expected = 1.0 / (1.0 + math.exp(-(1.0 + 2.0 * 3.0 - 0.5 * 4.0)))
    assert model.predict_proba({"a": 3.0, "b": 4.0}) == pytest.approx(expected)


@pytest.mark.unit
def test_predict_proba_is_a_probability_for_extreme_features():
    model = LinearModel(weights={"a": 1e4}, intercept=0.0, model_version="test-1")
    for value in (-1e6, -1.0, 0.0, 1.0, 1e6):
        assert 0.0 <= model.predict_proba({"a": value}) <= 1.0


@pytest.mark.unit
def test_load_reads_weights_intercept_and_version(tmp_path):
    path = tmp_path / "model.json"
    path.write_text(json.dumps({
        "version": "v9.9.9",
        "intercept": -0.25,
        "weights": {"cash_flow_log": -1.0, "age_months": -0.02},
    }))

    model = LinearModel.load(path)

    assert model.model_version == "v9.9.9"
    expected = _sigmoid(-0.25 + -1.0 * 10.0 + -0.02 * 24.0)
    assert model.predict_proba({"cash_flow_log": 10.0, "age_months": 24.0}) == pytest.approx(expected)


@pytest.mark.unit
def test_an_unknown_feature_is_not_silently_ignored():
    """A renamed feature must fail loudly, not score as if it were absent."""
    model = LinearModel(weights={"a": 1.0}, intercept=0.0, model_version="test-1")
    with pytest.raises(KeyError):
        model.predict_proba({"a": 1.0, "typo_feature": 2.0})