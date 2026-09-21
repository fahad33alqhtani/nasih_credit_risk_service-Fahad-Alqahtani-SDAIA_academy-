"""Logistic-regression inference in plain Python.

The model is fitted with scikit-learn in scripts/generate_baseline_assets.py,
but only its coefficients are shipped: a small JSON file holding the
weights, the intercept and a version string. Scoring is a dot product
and a sigmoid, so serving needs neither scikit-learn, pandas, scipy nor
numpy.
"""
import json
import math
from pathlib import Path


class LinearModel:
    def __init__(self, weights: dict[str, float], intercept: float,
                 model_version: str) -> None:
        self._weights = weights
        self._intercept = intercept
        self.model_version = model_version

    @classmethod
    def load(cls, path: str | Path) -> "LinearModel":
        # Called from the composition root (batch.py or the FastAPI
        # lifespan), never at import time.
        bundle = json.loads(Path(path).read_text())
        return cls(bundle["weights"], bundle["intercept"], bundle["version"])

    def predict_proba(self, features: dict) -> float:
        z = self._intercept + sum(
            self._weights[name] * value for name, value in features.items()
        )
        return _sigmoid(z)


def _sigmoid(z: float) -> float:
    # Branching on the sign keeps math.exp away from its overflow range
    # for extreme inputs; the naive 1/(1+exp(-z)) raises OverflowError
    # once z drops below about -710.
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)
