# API Contract

Base URL (local): `http://127.0.0.1:8000`

## `GET /health`
Returns app readiness.

Response example:
```json
{
  "status": "ok",
  "model": "loaded"
}
```

## `POST /detect`
Upload CSV file and receive per-row fraud predictions.

### Required CSV Columns
- `amount`
- `transaction_hour`
- `foreign_transaction`
- `location_mismatch`
- `device_trust_score`
- `velocity_last_24h`
- `cardholder_age`
- `merchant_category`

### Success Response
```json
{
  "results": [
    {
      "transaction_id": "txn001",
      "predicted_fraud": true,
      "probability": 0.9231,
      "explanation": "amount: 0.4312, velocity_last_24h: 0.2123, foreign_transaction: 0.1021",
      "stored": true,
      "store_error": null
    }
  ]
}
```

### Validation Failure (`422`)
```json
{
  "detail": {
    "error": "Invalid CSV schema",
    "missing_columns": ["transaction_hour"],
    "required_columns": ["amount", "transaction_hour", "..."]
  }
}
```

## `GET /alerts`
Returns latest alerts (optional query params: `severity`, `status`).

## `GET /analytics`
Returns KPI summary and fraud distributions.

## `GET /download`
Returns all transactions data as CSV string payload.