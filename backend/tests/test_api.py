from io import BytesIO

from fastapi.testclient import TestClient

import backend.main as main


class DummyModel:
    def predict(self, X):
        return [1]

    def predict_proba(self, X):
        return [[0.1, 0.9]]


def test_detect_rejects_old_schema_csv(monkeypatch):
    monkeypatch.setattr(main, "model", DummyModel())
    monkeypatch.setattr(main, "_safe_insert", lambda *_args, **_kwargs: None)

    client = TestClient(main.app)
    csv_bytes = (
        b"transaction_id,amount,location,merchant,time\n"
        b"txn1,12000,New York,Amazon,1\n"
    )

    response = client.post(
        "/detect",
        files={"file": ("bad.csv", BytesIO(csv_bytes), "text/csv")},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["error"] == "Invalid CSV schema"


def test_detect_accepts_model_schema_csv(monkeypatch):
    monkeypatch.setattr(main, "model", DummyModel())
    monkeypatch.setattr(main, "_safe_insert", lambda *_args, **_kwargs: None)

    client = TestClient(main.app)
    csv_bytes = (
        b"transaction_id,amount,transaction_hour,merchant_category,foreign_transaction,location_mismatch,device_trust_score,velocity_last_24h,cardholder_age\n"
        b"txn1,12000,1,Electronics,1,1,42,9,33\n"
    )

    response = client.post(
        "/detect",
        files={"file": ("good.csv", BytesIO(csv_bytes), "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert "results" in body
    assert body["results"][0]["predicted_fraud"] is True
