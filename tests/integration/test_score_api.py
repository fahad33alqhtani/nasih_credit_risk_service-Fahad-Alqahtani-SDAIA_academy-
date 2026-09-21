"""API contract tests against the real app.

Both the model and the audit store are injected through
dependency_overrides, so these run without a joblib file or a Redis
connection.
"""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from nasih_service.api.app import create_app

MALFORMED = sorted(pathlib.Path("payloads/malformed").glob("*.json"))


def test_malformed_corpus_is_not_empty():
    assert MALFORMED, "payloads/malformed is empty; run pytest from the project root"


@pytest.mark.integration
def test_score_contract(client_factory, sample_business):
    client = client_factory(probability=0.93)  # forces reject
    r = client.post("/v1/score", json=json.loads(sample_business.model_dump_json()))
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "reject"
    assert body["business_id"] == sample_business.business_id
    assert body["model_version"] == "test-1"
    assert 0.0 <= body["default_probability"] <= 1.0
    assert r.headers["X-Trace-Id"]


@pytest.mark.integration
@pytest.mark.parametrize("probability, expected", [
    (0.93, "reject"),
    (0.55, "manual_review"),
    (0.10, "auto_approve"),
])
def test_every_decision_branch_reaches_the_wire(client_factory, sample_business,
                                                probability, expected):
    r = client_factory(probability=probability).post(
        "/v1/score", json=json.loads(sample_business.model_dump_json()))
    assert r.status_code == 200
    assert r.json()["decision"] == expected


@pytest.mark.integration
@pytest.mark.parametrize("payload_file", MALFORMED, ids=lambda p: p.name)
def test_malformed_corpus_rejected(client_factory, payload_file):
    r = client_factory().post("/v1/score",
                              content=payload_file.read_bytes(),
                              headers={"content-type": "application/json"})
    assert 400 <= r.status_code < 500, payload_file.name


@pytest.mark.integration
def test_score_500_hides_stack_trace(client_factory, sample_business, monkeypatch):
    client = client_factory()

    def boom(self, business):
        raise ZeroDivisionError("seeded failure")

    monkeypatch.setattr("nasih_service.service.scorer.CreditScorer.score", boom)
    r = client.post("/v1/score", json=json.loads(sample_business.model_dump_json()))
    assert r.status_code == 500
    assert "ZeroDivisionError" not in r.text
    body = r.json()["error"]
    assert body["code"] == "INTERNAL_ERROR"
    assert body["trace_id"]


@pytest.mark.integration
def test_health_is_up_before_the_model_is(client_factory):
    r = client_factory().get("/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "nasih-service"}


@pytest.mark.integration
def test_ready_is_503_until_the_model_is_loaded():
    client = TestClient(create_app(), raise_server_exceptions=False)
    assert client.get("/v1/ready").status_code == 503


@pytest.mark.integration
def test_score_is_503_until_the_model_is_loaded():
    client = TestClient(create_app(), raise_server_exceptions=False)
    r = client.post("/v1/score", json={
        "business_id": "BIZ-TEST-0001",
        "monthly_cash_flow_sar": 20000.0,
        "business_age_months": 24,
    })
    assert r.status_code == 503
    assert r.headers.get("Retry-After") == "5"


@pytest.mark.integration
def test_trace_id_is_echoed_when_the_caller_supplies_one(client_factory, sample_business):
    r = client_factory().post(
        "/v1/score",
        json=json.loads(sample_business.model_dump_json()),
        headers={"X-Trace-Id": "abc123deadbeef"})
    assert r.status_code == 200
    assert r.headers["X-Trace-Id"] == "abc123deadbeef"
    assert r.json()["trace_id"] == "abc123deadbeef"


@pytest.mark.integration
def test_decision_audit_extension_round_trip(client_factory, sample_business):
    """A scored decision can be read back without resubmitting the input."""
    client = client_factory(probability=0.93)
    post_body = json.loads(sample_business.model_dump_json())
    r1 = client.post("/v1/score", json=post_body)
    assert r1.status_code == 200

    r2 = client.get(f"/v1/decisions/{sample_business.business_id}")
    assert r2.status_code == 200
    record = r2.json()
    assert record["business_id"] == sample_business.business_id
    assert record["decision"] == "reject"


@pytest.mark.integration
def test_decision_audit_404_when_unknown(client_factory):
    client = client_factory()
    r = client.get("/v1/decisions/BIZ-NEVER-SCORED")
    assert r.status_code == 404
