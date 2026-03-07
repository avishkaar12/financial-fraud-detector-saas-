# Competition Presentation Script (5 Minutes)

## 1) Problem (30s)
Financial fraud is time-sensitive; manual review is slow and error-prone.

## 2) Solution (45s)
This SaaS predicts fraud from transaction CSV uploads, stores outcomes in PostgreSQL, and generates explainable risk signals.

## 3) Architecture (45s)
- FastAPI backend for prediction APIs
- XGBoost model + SHAP explanations
- Neon PostgreSQL for persistence and analytics retrieval
- Firebase Auth for user sign-in and backend token verification

## 4) Live Demo (2m)
1. Open `/docs` or Postman.
2. Hit `GET /health`.
3. Upload `sample_transactions.csv` to `POST /detect`.
4. Show returned fraud probability + explanation.
5. Hit `GET /alerts` and `GET /analytics`.

## 5) Engineering Quality (45s)
- Strict input schema validation with clear 422 errors
- Robust SHAP fallback to avoid runtime crashes
- Automated tests for preprocessing and API behavior
- Secrets managed via `.env`, no hardcoded keys

## 6) Next Steps (15s)
- Add organization/tenant-level data isolation
- Add billing and usage metering
- Add dashboards for model drift and false-positive tracking
