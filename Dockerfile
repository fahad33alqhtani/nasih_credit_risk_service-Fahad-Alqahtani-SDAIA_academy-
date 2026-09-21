# ---------- builder ----------
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y \
        --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies change rarely, so they get their own cached layer.
COPY requirements.lock .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir \
       -r requirements.lock

COPY pyproject.toml README.md ./
COPY src/ src/
RUN /opt/venv/bin/pip install --no-cache-dir --no-deps .

# ---------- runtime ----------
FROM python:3.12-slim AS runtime

RUN useradd --create-home --uid 10001 appuser

RUN apt-get update && apt-get install -y \
    --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Only the virtualenv crosses over; build-essential stays behind.
COPY --from=builder /opt/venv /opt/venv

# Separate layer so a retrain doesn't invalidate the source layer.
COPY models/credit_model.joblib models/credit_model.joblib

ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

# /v1/ready rather than /v1/health: only ready confirms the model loaded.
HEALTHCHECK --interval=10s --timeout=3s \
    --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/v1/ready || exit 1

# Exec form so uvicorn is PID 1 and receives SIGTERM directly.
CMD ["uvicorn", "nasih_service.api.app:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000"]
