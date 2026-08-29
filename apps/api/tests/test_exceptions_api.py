import pytest

def test_exceptions_management_flow(client):
    # 1. Seed demo dataset and execute reconciliation run
    client.post("/api/datasets/load-demo")
    client.post("/api/reconciliation/run")

    # 2. List exceptions with pagination
    resp = client.get("/api/exceptions?page=1&page_size=10&sort_by=priority&sort_order=desc")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["total_count"] > 0
    assert len(data["items"]) == 10
    assert data["items"][0]["priority_score"] >= data["items"][1]["priority_score"]

    # 3. Filter by severity
    crit_resp = client.get("/api/exceptions?severity=CRITICAL")
    assert crit_resp.status_code == 200
    crit_items = crit_resp.json()["items"]
    assert all(item["severity"] == "CRITICAL" for item in crit_items)

    # 4. Search by ID
    target_exc = data["items"][0]
    target_id = str(target_exc["id"])
    target_code = target_exc["exception_code"]

    search_resp = client.get(f"/api/exceptions?search={target_code}")
    assert search_resp.status_code == 200
    assert len(search_resp.json()["items"]) >= 1

    # 5. Get Exception Detail
    detail_resp = client.get(f"/api/exceptions/{target_id}")
    assert detail_resp.status_code == 200
    det = detail_resp.json()
    assert det["id"] == int(target_id)
    assert det["evidence"] is not None
    assert det["evidence"]["summary"] is not None

    # 6. Update Status -> RESOLVED with Audit Log
    patch_payload = {
        "status": "RESOLVED",
        "resolution_code": "CUSTOMER_REFUNDED",
        "note": "Issued full refund via payment gateway console",
        "performed_by": "Finance Officer Jane"
    }
    patch_resp = client.patch(f"/api/exceptions/{target_id}/status", json=patch_payload)
    assert patch_resp.status_code == 200
    patched_det = patch_resp.json()
    assert patched_det["status"] == "RESOLVED"
    assert len(patched_det["audit_history"]) >= 1
    latest_audit = patched_det["audit_history"][0]
    assert latest_audit["action"] == "STATUS_UPDATED_RESOLVED"
    assert latest_audit["performed_by"] == "Finance Officer Jane"
    assert latest_audit["metadata"]["previous_status"] == "OPEN"

    # 7. Test invalid status update rejection
    bad_patch = client.patch(f"/api/exceptions/{target_id}/status", json={"status": "INVALID_STATUS"})
    assert bad_patch.status_code == 422 or bad_patch.status_code == 400

    # 8. Test 404 non-existent exception
    not_found_resp = client.get("/api/exceptions/9999999")
    assert not_found_resp.status_code == 404

    # 9. Test CSV Export
    csv_resp = client.get("/api/reports/exceptions.csv?severity=CRITICAL")
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"] == "text/csv; charset=utf-8"
    csv_text = csv_resp.text
    assert "exception_id,exception_code,exception_type" in csv_text
    assert "CRITICAL" in csv_text
