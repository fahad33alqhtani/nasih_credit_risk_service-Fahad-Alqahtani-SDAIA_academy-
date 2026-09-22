"""End-to-end boot through the real lifespan: joblib load, warm-up,
Redis client construction, route.

Marked slow, unlike the rest of tests/integration/, which injects test
doubles and runs in milliseconds. /health and /ready do no I/O and so
need no Redis; /score writes an audit record on every call, so that
test skips when no Redis is reachable.
"""
import os

import pytest
from fastapi.testclient import TestClient

from nasih_service.api.app import app

pytestmark = [pytest.mark.integration, pytest.mark.slow]

REDIS_URL = os.environ.get("NASIH_TEST_REDIS_URL", "redis://localhost:6379/0")


def _redis_available() -> bool:
    try:
        import redis
        redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1).ping()
        return True
    except Exception:  # noqa: BLE001 - any failure means Redis is not available
        return False


def test_health_through_real_lifespan():
    with TestClient(app) as client:
        response = client.get("/v1/health")
        assert response.status_code == 200


def test_ready_through_real_lifespan():
    with TestClient(app) as client:
        response = client.get("/v1/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}


@pytest.mark.skipif(not _redis_available(), reason="no Redis reachable at NASIH_TEST_REDIS_URL")
def test_score_through_real_lifespan():
    with TestClient(app) as client:
        response = client.post("/v1/predict", json={
            "business_id": "BIZ-TEST-0001",
            "monthly_cash_flow_sar": 20000.0,
            "business_age_months": 24,
        })
        assert response.status_code == 200
        body = response.json()
        assert "default_probability" in body
        assert body["model_version"] == "v1.0.0"
        assert body["decision"] in {"auto_approve", "manual_review", "reject"}

def test_audit_store_is_closed_on_shutdown(monkeypatch, tmp_path):
    """Leaving the lifespan must release the Redis connection pool."""
    import json

    from nasih_service.api import app as app_module

    model_path = tmp_path / "model.json"
    model_path.write_text(json.dumps({
        "version": "v-shutdown-test",
        "intercept": 0.0,
        "weights": {"cash_flow_log": -1.0, "age_months": -0.01},
    }))

    closed = {"value": False}

    class RecordingAuditStore:
        @classmethod
        def from_url(cls, url, ttl_seconds):
            return cls()

        def record(self, business_id, decision):
            pass

        def get(self, business_id):
            return None

        def close(self):
            closed["value"] = True

    monkeypatch.setenv("NASIH_MODEL_PATH", str(model_path))
    monkeypatch.setattr(app_module, "RedisAuditStore", RecordingAuditStore)

    with TestClient(app_module.create_app()) as client:
        assert client.get("/v1/ready").status_code == 200
        assert closed["value"] is False

    assert closed["value"] is True, "lifespan exited without closing the audit store"
