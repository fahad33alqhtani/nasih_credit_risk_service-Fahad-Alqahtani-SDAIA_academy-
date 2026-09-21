"""Application factory: lifespan model loading, trace middleware, error handling."""
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from nasih_service.adapters.redis_audit import RedisAuditStore
from nasih_service.adapters.sklearn_model import SklearnModel
from nasih_service.config import Settings
from nasih_service.logging_setup import configure_logging, set_trace_id
from nasih_service.service.scorer import CreditScorer

logger = logging.getLogger("nasih_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    configure_logging(settings.log_level)
    t0 = time.perf_counter()
    model = SklearnModel.load(settings.model_path)
    # Warm up so the first real request doesn't pay lazy-init cost.
    model.predict_proba({"cash_flow_log": 0.0, "age_months": 0.0})
    audit_store = RedisAuditStore.from_url(settings.redis_url, settings.audit_ttl_seconds)
    logger.info(f"model_loaded version={model.model_version} "
                f"seconds={time.perf_counter() - t0:.3f}")

    app.state.scorer = CreditScorer(model=model, audit_store=audit_store,
                                    reject_threshold=settings.reject_threshold)
    app.state.settings = settings
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Nasih Credit Scoring Service", version="1.0.0", lifespan=lifespan)

    from nasih_service.api.routes import router
    app.include_router(router, prefix="/v1")

    @app.middleware("http")
    async def trace_and_time(request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id", uuid.uuid4().hex[:16])
        request.state.trace_id = trace_id
        set_trace_id(trace_id)
        t0 = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Response-Time-Ms"] = str(round((time.perf_counter() - t0) * 1000, 1))
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        # Log the traceback, return only the trace id to the caller.
        trace_id = getattr(request.state, "trace_id", "unknown")
        logger.exception("unhandled_error")
        return JSONResponse(status_code=500, content={"error": {
            "code": "INTERNAL_ERROR",
            "message": "Unexpected error; contact support with trace_id",
            "trace_id": trace_id}})

    return app


app = create_app()
