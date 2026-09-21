# Benchmarks

Recorded from a local run. Environment: _fill in (OS, CPU, Python version)_.
Model version `v1.0.0`.

## Tests

```bash
pytest -m "not slow" --durations=10
pytest -m slow --no-cov
pytest
ruff check src tests scripts && mypy src && lint-imports
```

| Metric | Value |
|---|---|
| Fast gate (`pytest -m "not slow"`) | |
| Slow gate (`pytest -m slow`) | |
| Full suite | |
| Branch coverage, fast gate | |
| Branch coverage, full suite | |
| `ruff check` / `mypy src` / `lint-imports` | |

## Docker

```bash
make build && make image-size
# edit one line in src/nasih_service/api/routes.py, then:
time docker build -t nasih-service:dev .
make up && docker compose ps && make smoke
make startup-time
```

| Metric | Target | Measured |
|---|---|---|
| Multi-stage image size | ≤ 500 MB | |
| Cold build time | | |
| Warm rebuild after a one-line edit | | |
| Time to ready | | |
| `docker compose ps` status | both `(healthy)` | |
