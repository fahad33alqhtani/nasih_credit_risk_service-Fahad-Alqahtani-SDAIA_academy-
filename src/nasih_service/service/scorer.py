"""Use-case layer: score one business."""
from dataclasses import dataclass

from nasih_service.domain.entities import Business
from nasih_service.domain.policies import decide
from nasih_service.service.interfaces import AuditStore, Model


@dataclass
class CreditScorer:
    model: Model
    audit_store: AuditStore
    reject_threshold: float

    def score(self, business: Business) -> dict:
        features = business.to_features()
        raw_prob = self.model.predict_proba(features.values)
        decision = decide(raw_prob, self.reject_threshold)
        result = {
            "business_id": business.business_id,
            "default_probability": raw_prob,
            "decision": decision,
            "model_version": self.model.model_version,
        }
        self.audit_store.record(business.business_id, result)
        return result
