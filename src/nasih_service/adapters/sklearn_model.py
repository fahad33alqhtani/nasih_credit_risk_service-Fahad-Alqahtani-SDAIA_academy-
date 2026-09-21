"""sklearn/joblib adapter. Nothing else in the service imports either library."""
from pathlib import Path

import joblib
import pandas as pd


class SklearnModel:
    def __init__(self, pipeline, model_version: str) -> None:
        self._pipeline = pipeline
        self.model_version = model_version

    @classmethod
    def load(cls, path: str | Path) -> "SklearnModel":
        # Called from the composition root (batch.py or the FastAPI
        # lifespan), never at import time.
        bundle = joblib.load(path)
        return cls(bundle["pipeline"], bundle["version"])

    def predict_proba(self, features: dict) -> float:
        frame = pd.DataFrame([features])
        return float(self._pipeline.predict_proba(frame)[0, 1])
