"""Ports the service layer depends on.

Concrete ML and storage libraries are named in adapters/ and nowhere
else, so swapping either one is a single-file change.
"""
from typing import Protocol


class Model(Protocol):
    """Scores a feature vector for default probability."""

    model_version: str

    def predict_proba(self, features: dict) -> float: ...


class AuditStore(Protocol):
    """Records and retrieves credit decisions."""

    def record(self, business_id: str, decision: dict) -> None: ...

    def get(self, business_id: str) -> dict | None: ...
