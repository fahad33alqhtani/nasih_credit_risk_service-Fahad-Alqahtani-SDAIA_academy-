"""Request and response models. This is the public wire contract."""
from pydantic import BaseModel, ConfigDict, Field, field_validator

from nasih_service.domain.entities import Business


class ScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_id: str = Field(min_length=4, max_length=64)
    monthly_cash_flow_sar: float = Field(gt=0, le=50_000_000)
    business_age_months: int = Field(ge=0, le=1200)

    @field_validator("monthly_cash_flow_sar", "business_age_months", mode="before")
    @classmethod
    def _reject_bool(cls, v):
        # Without this, pydantic's lax mode coerces True/False into 1/0.
        # ValueError rather than TypeError: only ValueError and
        # AssertionError are turned into a 422 here, a TypeError would
        # escape as a 500.
        if isinstance(v, bool):
            raise ValueError("boolean is not a valid numeric value")  # noqa: TRY004
        return v

    def to_domain(self) -> Business:
        return Business(**self.model_dump())


class ScoreResponse(BaseModel):
    business_id: str
    default_probability: float = Field(ge=0, le=1)
    decision: str
    model_version: str
    trace_id: str


class DecisionRecord(BaseModel):
    business_id: str
    default_probability: float
    decision: str
    model_version: str


class ErrorBody(BaseModel):
    code: str
    message: str
    trace_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    service: str
