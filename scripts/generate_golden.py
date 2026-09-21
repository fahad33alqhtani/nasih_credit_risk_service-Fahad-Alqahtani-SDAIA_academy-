#!/usr/bin/env python3
"""Regenerate the behavioural golden file from the current model.

    python scripts/generate_golden.py

Run this only as a deliberate step after a reviewed model change. If
test_golden_scores_unchanged fails, find out why before regenerating.
"""
import pathlib

import pandas as pd

from nasih_service.adapters.linear_model import LinearModel
from nasih_service.domain.entities import Business

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "behavioural" / "golden_scores.csv"


def main() -> None:
    model = LinearModel.load(ROOT / "models" / "credit_model.json")
    df = pd.read_csv(ROOT / "data" / "businesses_sample.csv")

    rows = []
    for _, row in df.iterrows():
        business = Business(business_id=row["business_id"],
                            monthly_cash_flow_sar=float(row["monthly_cash_flow_sar"]),
                            business_age_months=int(row["business_age_months"]))
        rows.append({
            "business_id": business.business_id,
            "monthly_cash_flow_sar": business.monthly_cash_flow_sar,
            "business_age_months": business.business_age_months,
            "default_probability": model.predict_proba(business.to_features().values),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        fh.write(f"# model_version={model.model_version}\n")
        pd.DataFrame(rows).to_csv(fh, index=False)
    print(f"wrote {len(rows)} rows for {model.model_version} -> {OUT}")


if __name__ == "__main__":
    main()
