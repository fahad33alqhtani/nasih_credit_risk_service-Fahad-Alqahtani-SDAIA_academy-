# Benchmarks

Recorded from a local run. Environment: Windows 11, Python 3.13.0,
Docker Desktop. Model version `v1.0.0`.

## Tests

```bash
pytest -m "not slow"
pytest -m slow --no-cov
pytest
ruff check src tests scripts && mypy src && lint-imports
```

| Metric                             | Value                                       |
| ---------------------------------- | ------------------------------------------- |
| Fast gate (`pytest -m "not slow"`) | 71 passed, 9 deselected in 5.42s            |
| Slow gate (`pytest -m slow`)       | 7 passed, 2 skipped, 71 deselected in 4.74s |
| Full suite                         | 78 passed, 2 skipped in 5.74s               |
| Branch coverage, fast gate         | 85.42%                                      |
| Branch coverage, full suite        | 96.67%                                      |
| `ruff check`                       | clean                                       |
| `mypy src`                         | no issues, 17 files                         |
| `lint-imports`                     | 1 contract kept, 0 broken                   |

The two skips are the Redis-backed tests, which skip when nothing is
listening on `NASIH_TEST_REDIS_URL`. CI runs them against a service
container.

## Docker

```bash
docker build -t nasih-service:dev .
docker images nasih-service:dev --format "{{.Size}}"
# then edit one line in src/nasih_service/api/routes.py and rebuild
docker compose up -d && docker compose ps
```

| Metric                             | Target           | Measured         |
| ---------------------------------- | ---------------- | ---------------- |
| Multi-stage image size             | ≤ 500 MB         | 277 MB           |
| Cold build (`--no-cache`)          |                  | 63.6 s           |
| Warm rebuild after a one-line edit |                  | 12.5 s           |
| Time to ready                      |                  | 17.4 s           |
| `docker compose ps` status         | both `(healthy)` | both `(healthy)` |

Warm rebuilds skip dependency installation because `requirements.lock`
is copied and installed before the source, so a code edit only
invalidates the last two layers.

Time to ready includes roughly 7.5 s waiting for Redis to report
healthy, which `depends_on: condition: service_healthy` enforces before
the API container starts.

## Effect of moving the training stack out of the runtime image

`DECISIONS.md` #6 replaced the pickled scikit-learn estimator with a
JSON weights file, which removed scikit-learn, scipy, pandas, numpy and
joblib from `requirements.lock`.

|                  | Before  | After  |
| ---------------- | ------- | ------ |
| Image size       | 780 MB  | 277 MB |
| Runtime packages | 56      | 21     |
| Cold build       | ~267 s  | 63.6 s |
| Full test suite  | 264.8 s | 5.7 s  |

The suite got faster for the same reason the image got smaller: the
golden-file test no longer builds 5,000 pandas DataFrames to score
5,000 rows.
