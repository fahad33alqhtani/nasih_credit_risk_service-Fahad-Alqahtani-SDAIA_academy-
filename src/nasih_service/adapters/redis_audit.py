"""Redis adapter for the decision audit trail.

Decisions are keyed by business_id and expire after a TTL so the store
does not grow without bound.
"""
import json
from typing import Any

import redis


class RedisAuditStore:
    def __init__(self, client: "redis.Redis", ttl_seconds: int = 60 * 60 * 24) -> None:
        self._client = client
        self._ttl = ttl_seconds

    @classmethod
    def from_url(cls, url: str, ttl_seconds: int = 60 * 60 * 24) -> "RedisAuditStore":
        return cls(redis.Redis.from_url(url, decode_responses=True), ttl_seconds)

    def record(self, business_id: str, decision: dict[str, Any]) -> None:
        self._client.set(self._key(business_id), json.dumps(decision), ex=self._ttl)

    def get(self, business_id: str) -> dict[str, Any] | None:
        raw = self._client.get(self._key(business_id))
        return json.loads(raw) if raw is not None else None

    @staticmethod
    def _key(business_id: str) -> str:
        return f"nasih:decision:{business_id}"
