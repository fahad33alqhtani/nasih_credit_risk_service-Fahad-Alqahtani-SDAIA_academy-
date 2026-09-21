"""Shared fixtures.

Unit tests need none of these. Integration tests use client_factory,
which builds the real app around a steerable model and an in-memory
audit store. Behavioural tests use real_model, the actual joblib.
"""
import pytest
from fastapi.testclient import TestClient

from nasih_service.api.app import create_app
from nasih_service.api.routes import get_scorer
from nasih_service.domain.entities import Business
from nasih_service.service.scorer import CreditScorer

MODEL_PATH = "models/credit_model.json"


class ConstantModel:
    """Returns a fixed probability, so any decision branch can be driven."""

    def __init__(self, probability, version="test-1"):
        self._p = probability
        self.model_version = version

    def predict_proba(self, features: dict) -> float:
        return self._p


class InMemoryAuditStore:
    """Dict-backed stand-in for RedisAuditStore."""

    def __init__(self):
        self._store: dict[str, dict] = {}

    def record(self, business_id: str, decision: dict) -> None:
        self._store[business_id] = decision

    def get(self, business_id: str) -> dict | None:
        return self._store.get(business_id)


@pytest.fixture
def client_factory():
    # Injects through dependency_overrides, the same seam production
    # wiring goes through.
    def _make(probability=0.10, threshold=0.70):
        app = create_app()
        scorer = CreditScorer(model=ConstantModel(probability),
                              audit_store=InMemoryAuditStore(),
                              reject_threshold=threshold)
        app.dependency_overrides[get_scorer] = lambda: scorer
        return TestClient(app, raise_server_exceptions=False)

    return _make


@pytest.fixture(scope="session")
def real_model():
    # Session-scoped: read the weights file once for the whole run.
    from nasih_service.adapters.linear_model import LinearModel

    return LinearModel.load(MODEL_PATH)


@pytest.fixture
def sample_business():
    return Business(business_id="BIZ-TEST-0001",
                    monthly_cash_flow_sar=20_000.0,
                    business_age_months=24)
