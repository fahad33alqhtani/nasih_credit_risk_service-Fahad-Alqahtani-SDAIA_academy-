"""Domain entities. Stdlib and pydantic only, no I/O and no framework types."""
import math

from pydantic import BaseModel, Field


class Business(BaseModel):
    business_id: str
    monthly_cash_flow_sar: float = Field(gt=0)
    business_age_months: int = Field(ge=0)

    def to_features(self) -> "FeatureVector":
        """Feature definition shared by training and serving.

        The training script builds its frame from these same column
        names, so there is one place the feature logic can go wrong.
        """
        return FeatureVector(values={
            "cash_flow_log": math.log1p(self.monthly_cash_flow_sar),
            "age_months": float(self.business_age_months),
        })


class FeatureVector(BaseModel):
    values: dict[str, float]
