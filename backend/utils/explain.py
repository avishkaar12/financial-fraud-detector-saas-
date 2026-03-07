from __future__ import annotations

import numpy as np
import shap
import joblib
from pathlib import Path

from .preprocessing import preprocess_for_model

MODEL_PATH = Path(__file__).resolve().parents[1] / "fraud_model.pkl"
model = joblib.load(MODEL_PATH)
explainer = shap.TreeExplainer(model)


def _extract_shap_row(shap_values) -> np.ndarray:
    if isinstance(shap_values, list):
        values = shap_values[-1]
    else:
        values = shap_values

    arr = np.asarray(values)
    if arr.ndim == 1:
        return arr
    if arr.ndim == 2:
        return arr[0]
    if arr.ndim == 3:
        return arr[0, :, -1]
    raise ValueError(f"Unexpected SHAP output shape: {arr.shape}")


def explain_fraud(txn: dict) -> str:
    try:
        X = preprocess_for_model(txn)
        shap_values = explainer.shap_values(X)
        row_values = _extract_shap_row(shap_values)

        top_features = sorted(
            zip(X.columns, row_values),
            key=lambda x: abs(float(x[1])),
            reverse=True,
        )
        return ", ".join(
            f"{feature}: {round(float(value), 4)}" for feature, value in top_features[:3]
        )
    except Exception:
        return "Explanation unavailable"


def generate_reason(txn: dict) -> str:
    amount = float(txn.get("amount", 0))
    hour = int(txn.get("transaction_hour", 0))
    velocity = int(txn.get("velocity_last_24h", 0))

    if amount > 10000 and hour in [0, 1, 2, 3, 4]:
        return "High amount at unusual hour"
    if velocity >= 8:
        return "High transaction velocity in 24h"
    if int(txn.get("foreign_transaction", 0)) == 1 and int(txn.get("location_mismatch", 0)) == 1:
        return "Foreign transaction with location mismatch"
    if amount > 10000:
        return "High amount"
    return "Anomalous pattern detected"


def assess_severity(txn: dict) -> str:
    amount = float(txn.get("amount", 0))
    velocity = int(txn.get("velocity_last_24h", 0))

    if amount > 20000 or velocity >= 10:
        return "high"
    if amount > 10000 or velocity >= 6:
        return "medium"
    return "low"
