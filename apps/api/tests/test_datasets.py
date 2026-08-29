import io
import pytest

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "LedgerGuard AI" in data["service"]

    # Test /api/health as well
    api_resp = client.get("/api/health")
    assert api_resp.status_code == 200
    assert api_resp.json()["status"] == "healthy"

def test_load_demo_and_summary(client):
    # Initially summary should be empty
    sum_resp = client.get("/api/datasets/summary")
    assert sum_resp.status_code == 200
    assert sum_resp.json()["total_records"] == 0

    # Load demo datasets
    load_resp = client.post("/api/datasets/load-demo")
    assert load_resp.status_code == 200
    load_data = load_resp.json()
    assert load_data["status"] == "success"
    assert load_data["orders_loaded"] == 500
    assert load_data["payments_loaded"] == 540
    assert load_data["settlements_loaded"] == 470
    assert load_data["invoices_loaded"] == 500

    # Summary after load
    sum_resp2 = client.get("/api/datasets/summary")
    assert sum_resp2.status_code == 200
    s_data = sum_resp2.json()
    assert s_data["orders_count"] == 500
    assert s_data["payments_count"] == 540
    assert s_data["settlements_count"] == 470
    assert s_data["invoices_count"] == 500
    assert s_data["total_records"] == 2010

def test_upload_valid_csv(client):
    csv_content = """order_id,merchant_id,customer_id,customer_name,customer_email,customer_phone,order_amount,currency,status,created_at
ord_test_101,mer_01,cust_01,Test User,test@example.com,+919876543210,1500.00,INR,PAID,2026-07-01 10:00:00
ord_test_102,mer_01,cust_02,Sample User,sample@example.com,+919876543211,2500.00,INR,PAID,2026-07-01 11:00:00
"""
    files = {
        "file": ("test_orders.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    data = {"dataset_type": "orders"}
    
    response = client.post("/api/datasets/upload", data=data, files=files)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert res_json["records_processed"] == 2

    # Verify summary count
    sum_resp = client.get("/api/datasets/summary")
    assert sum_resp.json()["orders_count"] == 2

def test_malformed_csv_rejections(client):
    # 1. Non-CSV file extension rejection
    files = {"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")}
    resp1 = client.post("/api/datasets/upload", data={"dataset_type": "orders"}, files=files)
    assert resp1.status_code == 400
    assert "Only CSV files" in resp1.json()["detail"]

    # 2. Missing required headers rejection
    bad_csv = "id,name,amount\n1,john,100\n"
    files2 = {"file": ("bad.csv", io.BytesIO(bad_csv.encode("utf-8")), "text/csv")}
    resp2 = client.post("/api/datasets/upload", data={"dataset_type": "orders"}, files=files2)
    assert resp2.status_code == 400
    assert "Missing required headers" in resp2.json()["detail"]

    # 3. Invalid dataset_type
    valid_csv = "order_id,order_amount,currency,status,created_at\nord_1,100,INR,PAID,2026-01-01 00:00:00\n"
    files3 = {"file": ("valid.csv", io.BytesIO(valid_csv.encode("utf-8")), "text/csv")}
    resp3 = client.post("/api/datasets/upload", data={"dataset_type": "invalid_type"}, files=files3)
    assert resp3.status_code == 400
    assert "Invalid dataset_type" in resp3.json()["detail"]

def test_sensitive_credentials_rejection(client):
    # Rejects CSV containing CVV or password columns
    sensitive_csv = """order_id,order_amount,currency,status,created_at,cvv,card_number
ord_leak_1,500,INR,PAID,2026-07-01 10:00:00,123,4111111111111111
"""
    files = {"file": ("leak.csv", io.BytesIO(sensitive_csv.encode("utf-8")), "text/csv")}
    resp = client.post("/api/datasets/upload", data={"dataset_type": "orders"}, files=files)
    assert resp.status_code == 400
    assert "Security Violation" in resp.json()["detail"]

def test_reset_demo(client):
    # Load data first
    client.post("/api/datasets/load-demo")
    assert client.get("/api/datasets/summary").json()["total_records"] == 2010

    # Reset
    reset_resp = client.post("/api/demo/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "success"

    # Summary after reset
    sum_after = client.get("/api/datasets/summary")
    assert sum_after.json()["total_records"] == 0
    assert sum_after.json()["orders_count"] == 0
