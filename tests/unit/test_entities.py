"""Unit tests for the feature definition and input validation."""
import math

import pytest

from nasih_service.domain.entities import Business


@pytest.mark.unit
@pytest.mark.parametrize("cash_flow, age, expected_log", [
    (1.0, 0, math.log1p(1.0)),
    (20_000.0, 24, math.log1p(20_000.0)),
    (0.01, 1200, math.log1p(0.01)),
])
def test_to_features_matches_log1p(cash_flow, age, expected_log):
    business = Business(business_id="BIZ-0001", monthly_cash_flow_sar=cash_flow,
                        business_age_months=age)
    features = business.to_features()
    assert features.values["cash_flow_log"] == pytest.approx(expected_log)
    assert features.values["age_months"] == float(age)


@pytest.mark.unit
def test_rejects_non_positive_cash_flow():
    with pytest.raises(ValueError):
        Business(business_id="BIZ-0001", monthly_cash_flow_sar=0.0, business_age_months=1)


@pytest.mark.unit
def test_rejects_negative_age():
    with pytest.raises(ValueError):
        Business(business_id="BIZ-0001", monthly_cash_flow_sar=1000.0, business_age_months=-1)
