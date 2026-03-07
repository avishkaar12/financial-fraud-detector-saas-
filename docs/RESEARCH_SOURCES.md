# Research Sources and References

Use this section in your presentation/resume to explain what you researched and implemented.

## Dataset Source
- Primary dataset used by this repo at runtime: `backend/training/creditcard.csv` (project-local file).
- If your local file is based on the public ULB/Kaggle credit-card fraud dataset, cite:
  - Kaggle dataset page: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

## ML and Evaluation References
- XGBoost (scikit-learn estimator usage):
  - https://xgboost.readthedocs.io/en/release_2.1.0/python/sklearn_estimator.html
- XGBoost Python API:
  - https://xgboost.readthedocs.io/en/latest/python/python_api.html
- Scikit-learn precision/recall thresholding:
  - https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_curve.html

## Explainability References
- SHAP TreeExplainer docs:
  - https://shap.readthedocs.io/en/stable/generated/shap.TreeExplainer.html

## Backend and API References
- FastAPI CORS middleware:
  - https://fastapi.tiangolo.com/tutorial/cors/

## PostgreSQL and Auth References
- Psycopg2 usage:
  - https://www.psycopg.org/docs/usage.html
- Firebase Admin token verification:
  - https://firebase.google.com/docs/auth/admin/verify-id-tokens

## What Was Built from This Research
- Dataset-driven fraud detection endpoint (`POST /detect`) for CSV uploads.
- XGBoost model with class-imbalance-aware training and tuned threshold artifact (`model_metadata.json`).
- SHAP-based transaction-level explanation fallback.
- PostgreSQL persistence for transactions, model logs, and alerts.
- Dashboard frontend for upload, alerts, analytics, and demo flow.
