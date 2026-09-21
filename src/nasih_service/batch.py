"""Offline batch scoring. Composition root for runs with no HTTP layer.

Audit records are dropped here rather than written to Redis; a batch
run scores the whole file at once and has nothing to look up later.
"""
import time

import pandas as pd

from nasih_service.adapters.sklearn_model import SklearnModel
from nasih_service.config import Settings
from nasih_service.domain.entities import Business
from nasih_service.service.scorer import CreditScorer


class NullAuditStore:
    def record(self, business_id: str, decision: dict) -> None:
        pass

    def get(self, business_id: str):
        return None


def main() -> None:
    settings = Settings()

    t0 = time.perf_counter()
    model = SklearnModel.load(settings.model_path)
    load_duration = time.perf_counter() - t0
    print(f"Loaded model version {model.model_version} in {load_duration:.2f}s")

    scorer = CreditScorer(model=model, audit_store=NullAuditStore(),
                          reject_threshold=settings.reject_threshold)

    df = pd.read_csv("data/businesses_sample.csv")

    t1 = time.perf_counter()
    results = []
    for _, row in df.iterrows():
        business = Business(
            business_id=row["business_id"],
            monthly_cash_flow_sar=float(row["monthly_cash_flow_sar"]),
            business_age_months=int(row["business_age_months"]),
        )
        results.append(scorer.score(business))
    batch_duration = time.perf_counter() - t1

    out_df = pd.DataFrame(results)
    out_df.to_csv("scored.csv", index=False)

    counts = out_df["decision"].value_counts().to_dict()
    print(f"Scored {len(out_df)} businesses in {batch_duration:.2f}s -> scored.csv")
    print(f"Summary: {counts}")


if __name__ == "__main__":
    main()
