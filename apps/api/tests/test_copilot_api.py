import pytest

@pytest.fixture(autouse=True)
def setup_reconciliation_data(client):
    # Ensure database tables exist, demo data is loaded, and recon engine is run
    client.post("/api/datasets/load-demo")
    client.post("/api/reconciliation/run")

def test_no_api_key_fallback(client):
    res = client.post("/api/copilot/query", json={"query": "Show the highest-value unresolved issues."})
    assert res.status_code == 200
    data = res.json()
    assert data["fallback_mode"] is True
    assert "Money at risk" in data["answer"] or "top open exceptions" in data["answer"]
    assert len(data["cited_evidence_ids"]) > 0
    assert "Human review is required" in data["disclaimer"]

def test_grounded_source_citation(client):
    res = client.post("/api/copilot/query", json={"query": "Why was EXC_1001 flagged?"})
    assert res.status_code == 200
    data = res.json()
    assert "EXC_1001" in data["cited_evidence_ids"]
    assert "DUPLICATE PAYMENT" in data["answer"] or "EXC_1001" in data["answer"]

def test_insufficient_data_response(client):
    res = client.post("/api/copilot/query", json={"query": "What will the stock price of Apple be tomorrow?"})
    assert res.status_code == 200
    data = res.json()
    assert "I don't have enough data in the current reconciliation run to answer that." in data["answer"]
    assert data["confidence_score"] <= 0.5

def test_safe_failure_behavior(client):
    # Test invalid query length
    res = client.post("/api/copilot/query", json={"query": ""})
    assert res.status_code == 422
