"""HTTP routes.

/score is a plain def rather than async def on purpose: sklearn
inference is CPU-bound, and FastAPI runs sync routes in a thread pool.
Declaring it async would block the event loop for every other caller.
"""
from fastapi import APIRouter, Depends, HTTPException, Request

from nasih_service.api.schemas import (
    DecisionRecord,
    HealthResponse,
    ScoreRequest,
    ScoreResponse,
)
from nasih_service.service.scorer import CreditScorer

router = APIRouter()


def get_scorer(request: Request) -> CreditScorer:
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise HTTPException(status_code=503, detail="Model not ready",
                             headers={"Retry-After": "5"})
    return scorer


@router.post("/score", response_model=ScoreResponse)
def score(body: ScoreRequest, request: Request,
          scorer: CreditScorer = Depends(get_scorer)):
    result = scorer.score(body.to_domain())
    return ScoreResponse(
        business_id=result["business_id"],
        default_probability=result["default_probability"],
        decision=result["decision"],
        model_version=result["model_version"],
        trace_id=request.state.trace_id,
    )


@router.get("/decisions/{business_id}", response_model=DecisionRecord)
def get_decision(business_id: str, scorer: CreditScorer = Depends(get_scorer)):
    """Read back a decision already made, without re-scoring."""
    record = scorer.audit_store.get(business_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No decision on file for this business_id")
    return DecisionRecord(**record)


@router.get("/health", response_model=HealthResponse)
def health():
    # Liveness only: the process is running. No I/O here.
    return HealthResponse(status="ok", service="nasih-service")


@router.get("/ready")
def ready(request: Request):
    # Readiness: the model is loaded and traffic is safe to accept.
    if getattr(request.app.state, "scorer", None) is None:
        raise HTTPException(status_code=503, detail="warming up")
    return {"status": "ready"}
