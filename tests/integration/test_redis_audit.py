"""Exercises RedisAuditStore against a real Redis instead of the
in-memory double.

CI supplies a Redis service container. Locally the test skips if
nothing is listening, so a developer without Redis can still run the
full suite.
"""
import os
import uuid

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.slow]

REDIS_URL = os.environ.get("NASIH_TEST_REDIS_URL", "redis://localhost:6379/0")


def _redis_available() -> bool:
    try:
        import redis
        redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1).ping()
        return True
    except Exception:  # noqa: BLE001 - any failure means Redis is not available
        return False


@pytest.mark.skipif(not _redis_available(), reason="no Redis reachable at NASIH_TEST_REDIS_URL")
def test_redis_audit_store_round_trip():
    from nasih_service.adapters.redis_audit import RedisAuditStore

    store = RedisAuditStore.from_url(REDIS_URL, ttl_seconds=30)
    business_id = f"BIZ-REDIS-TEST-{uuid.uuid4().hex[:8]}"

    assert store.get(business_id) is None

    decision = {
        "business_id": business_id,
        "default_probability": 0.42,
        "decision": "manual_review",
        "model_version": "test-1",
    }
    store.record(business_id, decision)
    assert store.get(business_id) == decision
