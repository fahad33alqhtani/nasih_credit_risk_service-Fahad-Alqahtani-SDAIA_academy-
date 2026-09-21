"""Credit policy. The thresholds are a business decision, kept out of the model."""

REJECT_THRESHOLD_DEFAULT = 0.70
REVIEW_BAND = 0.25  # width of the manual-review band below the reject threshold


def decide(default_probability: float, reject_threshold: float = REJECT_THRESHOLD_DEFAULT) -> str:
    if default_probability >= reject_threshold:
        return "reject"
    if default_probability >= reject_threshold - REVIEW_BAND:
        return "manual_review"
    return "auto_approve"
