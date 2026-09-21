"""Behavioural tests against the trained model.

The unit and integration suites would stay green even if the model
started returning plausible-looking nonsense. These check that it
behaves the way a credit model is supposed to.
"""
import pathlib

import pytest

pytestmark = [pytest.mark.behavioural, pytest.mark.slow]

GOLDEN = pathlib.Path("tests/behavioural/golden_scores.csv")


def _score(model, business):
    return model.predict_proba(business.to_features().values)


def test_invariance_to_business_id_casing(real_model, sample_business):
    """The business id is an identifier, not a feature."""
    a = _score(real_model, sample_business)
    b = _score(real_model, sample_business.model_copy(
        update={"business_id": sample_business.business_id.lower()}))
    assert a == pytest.approx(b, abs=1e-9)


def test_directional_cash_flow(real_model, sample_business):
    """More monthly cash flow must never raise default risk."""
    low = _score(real_model, sample_business.model_copy(
        update={"monthly_cash_flow_sar": 5_000.0}))
    high = _score(real_model, sample_business.model_copy(
        update={"monthly_cash_flow_sar": 50_000.0}))
    assert high <= low + 1e-6


def test_directional_age(real_model, sample_business):
    """A longer trading history must never raise default risk."""
    young = _score(real_model, sample_business.model_copy(
        update={"business_age_months": 2}))
    old = _score(real_model, sample_business.model_copy(
        update={"business_age_months": 180}))
    assert old <= young + 1e-6


def test_probability_stays_in_range(real_model, sample_business):
    for cash_flow in (1.0, 1_000.0, 500_000.0, 10_000_000.0):
        p = _score(real_model, sample_business.model_copy(
            update={"monthly_cash_flow_sar": cash_flow}))
        assert 0.0 <= p <= 1.0


def test_golden_scores_unchanged():
    """Compares 5,000 reference scores at atol=1e-6.

    A failure means the model changed or training and serving have
    drifted apart. Investigate before regenerating the file.
    """
    import pandas as pd

    from nasih_service.adapters.linear_model import LinearModel
    from nasih_service.domain.entities import Business

    assert GOLDEN.exists(), "run scripts/generate_golden.py first"

    header = GOLDEN.read_text().splitlines()[0]
    assert header.startswith("# model_version=")
    golden_version = header.split("=", 1)[1].strip()

    model = LinearModel.load("models/credit_model.json")
    assert golden_version == model.model_version, (
        f"golden file was recorded against {golden_version}, "
        f"model is {model.model_version}")

    golden = pd.read_csv(GOLDEN, comment="#")
    assert len(golden) == 5000

    current = [
        model.predict_proba(
            Business(business_id=r.business_id,
                    monthly_cash_flow_sar=float(r.monthly_cash_flow_sar),
                    business_age_months=int(r.business_age_months)).to_features().values)
        for r in golden.itertuples()
    ]
    drift = (golden["default_probability"] - pd.Series(current)).abs()
    assert drift.max() <= 1e-6
