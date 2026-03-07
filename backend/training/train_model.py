from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "training" / "creditcard.csv"
MODEL_PATH = BASE_DIR / "fraud_model.pkl"
COLUMNS_PATH = BASE_DIR / "model_columns.json"
METADATA_PATH = BASE_DIR / "model_metadata.json"

TARGET_COL = "is_fraud"
DROP_COLS = ["transaction_id"]
RANDOM_STATE = 42


def load_and_validate_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")

    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Dataset is empty")

    if TARGET_COL not in df.columns:
        raise KeyError(f"Missing target column '{TARGET_COL}'")

    if df.isnull().sum().sum() > 0:
        print("Warning: Missing values detected. Dropping rows with NaNs.")
        df = df.dropna().reset_index(drop=True)

    if df[TARGET_COL].nunique() < 2:
        raise ValueError("Target must contain at least two classes")

    return df


def build_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    feature_cols = [c for c in df.columns if c not in [TARGET_COL] + DROP_COLS]
    X = pd.get_dummies(df[feature_cols], dtype=float)
    y = df[TARGET_COL].astype(int)

    if X.empty:
        raise ValueError("No feature columns available after preprocessing")

def find_best_threshold(y_true: np.ndarray, proba: np.ndarray) -> float:
    thresholds = np.linspace(0.05, 0.95, 91)
    best_threshold = 0.5
    best_f1 = -1.0

    for threshold in thresholds:
        preds = (proba >= threshold).astype(int)
        score = f1_score(y_true, preds, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_threshold = float(threshold)

    return best_threshold


def evaluate_split(name: str, y_true: np.ndarray, proba: np.ndarray, threshold: float) -> dict:
    preds = (proba >= threshold).astype(int)

    return {
        "split": name,
        "threshold": threshold,
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "pr_auc": float(average_precision_score(y_true, proba)),
        "precision": float(precision_score(y_true, preds, zero_division=0)),
        "recall": float(recall_score(y_true, preds, zero_division=0)),
        "f1": float(f1_score(y_true, preds, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, preds).tolist(),
        "classification_report": classification_report(y_true, preds, output_dict=True, zero_division=0),
    }


def main() -> None:
    start_time = time.time()
    df = load_and_validate_dataset(DATA_PATH)
    X, y = build_feature_matrix(df)

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.2, stratify=y_train_full, random_state=RANDOM_STATE
    )

    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    scale_pos_weight = max(1.0, neg / max(pos, 1))

    model = XGBClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=5,
        min_child_weight=3,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        scale_pos_weight=scale_pos_weight,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    val_proba = model.predict_proba(X_val)[:, 1]
    best_threshold = find_best_threshold(y_val.to_numpy(), val_proba)

    test_proba = model.predict_proba(X_test)[:, 1]
    val_metrics = evaluate_split("validation", y_val.to_numpy(), val_proba, best_threshold)
    test_metrics = evaluate_split("test", y_test.to_numpy(), test_proba, best_threshold)

    joblib.dump(model, MODEL_PATH)
    with COLUMNS_PATH.open("w", encoding="utf-8") as f:
        json.dump(list(X.columns), f, indent=2)

    metadata = {
        "model_type": "xgboost",
        "version": "v2",
        "trained_at_unix": int(time.time()),
        "dataset_rows": int(len(df)),
        "feature_count": int(X.shape[1]),
        "class_balance": {
            "fraud_0": int((y == 0).sum()),
            "fraud_1": int((y == 1).sum()),
        },
        "split_sizes": {
            "train": int(len(X_train)),
            "validation": int(len(X_val)),
            "test": int(len(X_test)),
        },
        "threshold": round(best_threshold, 4),
        "scale_pos_weight": round(scale_pos_weight, 4),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
        "training_time_seconds": round(time.time() - start_time, 2),
    }

    with METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("Training complete.")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Columns saved to: {COLUMNS_PATH}")
    print(f"Metadata saved to: {METADATA_PATH}")
    print("Validation F1:", round(val_metrics["f1"], 4))
    print("Test F1:", round(test_metrics["f1"], 4))
    print("Test ROC-AUC:", round(test_metrics["roc_auc"], 4))
    print("Test PR-AUC:", round(test_metrics["pr_auc"], 4))


if __name__ == "__main__":
    main()
