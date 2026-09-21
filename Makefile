.PHONY: install run-batch serve lint typecheck check-arch test test-fast test-slow \
        build up down image-size smoke startup-time

install:
	pip install -e ".[dev,api]"

run-batch:
	python -m nasih_service.batch

serve:
	fastapi dev src/nasih_service/api/app.py

lint:
	ruff check src tests scripts

typecheck:
	mypy src

check-arch:
	lint-imports

test:
	python -m pytest -v

test-fast:
	python -m pytest -m "not slow"

test-slow:
	python -m pytest -m slow

# ---------- Docker ----------

build:
	docker build -t nasih-service:dev .

up:
	docker compose up -d --build

down:
	docker compose down

image-size:
	docker images nasih-service:dev --format "{{.Size}}"

smoke:
	curl -fsS localhost:8000/v1/health
	curl -fsS localhost:8000/v1/ready
	curl -fsS -X POST localhost:8000/v1/score \
		-H "content-type: application/json" \
		-d '{"business_id":"BIZ-SMOKE-0001","monthly_cash_flow_sar":20000,"business_age_months":24}'

startup-time:
	./scripts/startup_time.sh
