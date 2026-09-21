#!/usr/bin/env python3
"""Generate the synthetic dataset and train the baseline credit model.

    python scripts/generate_baseline_assets.py

Writes data/businesses_sample.csv and models/credit_model.joblib.
Seeded, so repeated runs reproduce the same artefacts.

The model is fit on the same feature columns Business.to_features()
produces, so training and serving share one definition of a feature.
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

RNG = np.random.default_rng(42)
N = 5000

# Data-generating process. Both weights are negative: more cash flow and
# a longer trading history each lower the chance of default. Tuned so the
# scored book lands at roughly 75% approve / 15% review / 10% reject
# instead of collapsing into a single decision band.
BASELINE_LOGIT = -1.5
CASH_FLOW_WEIGHT = -1.0
AGE_WEIGHT = -0.022
NOISE_SD = 0.45


def main() -> None:
    cash_flow = RNG.lognormal(mean=10.0, sigma=1.0, size=N)
    age_months = RNG.integers(low=1, high=240, size=N)
    cash_flow_log = np.log1p(cash_flow)

    linear_risk = (
        BASELINE_LOGIT
        + CASH_FLOW_WEIGHT * (cash_flow_log - cash_flow_log.mean())
        + AGE_WEIGHT * (age_months - age_months.mean())
        + RNG.normal(scale=NOISE_SD, size=N)
    )
    default = RNG.binomial(1, 1 / (1 + np.exp(-linear_risk)))

    pd.DataFrame({
        "business_id": [f"BIZ-{i:06d}" for i in range(1, N + 1)],
        "monthly_cash_flow_sar": np.round(cash_flow, 2),
        "business_age_months": age_months,
    }).to_csv("data/businesses_sample.csv", index=False)

    train_features = pd.DataFrame({
        "cash_flow_log": cash_flow_log,
        "age_months": age_months.astype(float),
    })
    model = LogisticRegression()
    model.fit(train_features, default)

    # Guard against a retrain that inverts the relationship. The
    # behavioural directional tests assert the same property at the
    # service boundary.
    coefs = dict(zip(train_features.columns, model.coef_[0]))
    assert coefs["cash_flow_log"] < 0, "cash flow must reduce default risk"
    assert coefs["age_months"] < 0, "business age must reduce default risk"

    joblib.dump({"pipeline": model, "version": "v1.0.0"}, "models/credit_model.joblib")
    print(f"observed default rate: {default.mean():.1%}")
    print(f"coefficients: {coefs}")
    print(f"wrote data/businesses_sample.csv ({N} rows) and models/credit_model.joblib")


if __name__ == "__main__":
    main()
