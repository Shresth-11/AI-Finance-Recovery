import pytest

def test_full_reconciliation_flow(client):
    # 1. Load demo dataset
    load_resp = client.post("/api/datasets/load-demo")
    assert load_resp.status_code == 200

    # 2. Trigger reconciliation run
    run_resp = client.post("/api/reconciliation/run")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["summary"]["total_orders"] == 500
    assert run_data["summary"]["total_exceptions"] > 0
    assert run_data["summary"]["unreconciled_amount"] > 0

    # 3. Query reconciliation results
    results_resp = client.get("/api/reconciliation/results?limit=10")
    assert results_resp.status_code == 200
    res_data = results_resp.json()
    assert res_data["total_count"] == run_data["summary"]["total_exceptions"]
    assert len(res_data["exceptions"]) == 10
    
    # Check evidence structure
    first_exc = res_data["exceptions"][0]
    assert first_exc["evidence"]["summary"] is not None
    assert first_exc["evidence"]["details_json"] is not None

    # Filter results by severity
    crit_resp = client.get("/api/reconciliation/results?severity=CRITICAL")
    assert crit_resp.status_code == 200
    crit_data = crit_resp.json()
    assert all(e["severity"] == "CRITICAL" for e in crit_data["exceptions"])

    # 4. Query Dashboard Metrics
    metrics_resp = client.get("/api/dashboard/metrics")
    assert metrics_resp.status_code == 200
    m_data = metrics_resp.json()
    assert m_data["summary"]["total_orders"] == 500
    assert m_data["summary"]["risk_score"] > 0.0
    assert "CRITICAL" in m_data["breakdown"]["by_severity"]

    # 5. Query Dashboard Trends
    trends_resp = client.get("/api/dashboard/trends")
    assert trends_resp.status_code == 200
    t_data = trends_resp.json()
    assert "volume_trend" in t_data
    assert "exception_trend" in t_data
    assert len(t_data["volume_trend"]) > 0
