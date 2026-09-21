# Engineering Decisions

## 1. Feature engineering lives in the domain entity, not in the sklearn pipeline

`Business.to_features()` is the only place raw input (`monthly_cash_flow_sar`,
`business_age_months`) becomes what the model sees (`cash_flow_log`,
`age_months`). `scripts/generate_baseline_assets.py` builds its training frame
from those same column names, and `SklearnModel.predict_proba` wraps a features
dict straight into a `DataFrame` with no further transformation.

The alternative, a `FunctionTransformer` inside the pipeline, would mean the
feature logic exists twice and can drift. Here there is one function, and it is
unit-tested directly in `tests/unit/test_entities.py`.

## 2. The model and the audit store are ports, injected as Protocols

`service/interfaces.py` defines `Model` and `AuditStore` as structural
`Protocol`s. `CreditScorer` depends on two method signatures, not on sklearn or
redis.

That is what lets the fast test gate run with no model loads and no network:
`ConstantModel` and `InMemoryAuditStore` are short test doubles satisfying the
same contract production uses, injected through `app.dependency_overrides`,
which is the same seam the real wiring goes through.

## 3. The audit trail as the extension feature

Redis in `docker-compose.yml` needed an actual job rather than only
demonstrating health gating. An audit trail fits a credit decision: a reviewer
needs to see what was decided without resubmitting the original figures.

It also meant a second adapter and a second port, so the dependency-injection
pattern from decision 2 is exercised twice rather than once.

## 4. Directional behavioural tests assert a sign, not a hand-picked number

`test_directional_cash_flow` and `test_directional_age` do not check that some
business scores below a chosen threshold. They check that raising cash flow, or
raising age, never raises the predicted default probability.

A threshold would be an assumption baked into a test. A sign is a real property:
`generate_baseline_assets.py` asserts both fitted coefficients are negative
before saving the artefact, so a retrain that flips either sign fails the
training script and the behavioural suite independently.

## 5. `NASIH_REDIS_URL` is validated at startup, not on first use

`config.py` runs a `field_validator` on `redis_url` at process start. Without
it, a typo'd environment variable would only surface when the first `/v1/score`
call tried to write an audit record, by which point the container has already
reported itself healthy and started taking traffic.

## 6. Synthetic data tuned so all three decision bands are populated

The first version of the data generator produced a book where 89% of businesses
were rejected and none were auto-approved, because the baseline default rate was
set far too high. The decision logic was correct, but nothing exercised the
approve path on real data and the service looked broken.

The generating process now uses a baseline logit of -1.5, giving a 27.7% default
rate and a scored book of roughly 75% approve, 16% review, 10% reject.
