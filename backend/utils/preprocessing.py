from __future__ import annotations

import pandas as pd

from .schema import (
    DEFAULT_INPUT_VALUES,
    MODEL_COLUMNS,
    NUMERIC_INPUT_COLUMNS,
    REQUIRED_INPUT_COLUMNS,
    normalize_transaction_payload,
    validate_transaction_payload,
)


def preprocess_dataframe_for_model(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df[REQUIRED_INPUT_COLUMNS].copy()

    for col in NUMERIC_INPUT_COLUMNS:
        prepared[col] = pd.to_numeric(prepared[col], errors="coerce")
        prepared[col] = prepared[col].fillna(DEFAULT_INPUT_VALUES[col])

    prepared["transaction_hour"] = prepared["transaction_hour"].round().clip(0, 23)
    prepared["foreign_transaction"] = prepared["foreign_transaction"].round().clip(0, 1)
    prepared["location_mismatch"] = prepared["location_mismatch"].round().clip(0, 1)
    prepared["device_trust_score"] = prepared["device_trust_score"].round().clip(0, 100)
    prepared["velocity_last_24h"] = prepared["velocity_last_24h"].round().clip(0, 1000)
    prepared["cardholder_age"] = prepared["cardholder_age"].round().clip(0, 120)

    prepared["merchant_category"] = (
        prepared["merchant_category"]
        .fillna(DEFAULT_INPUT_VALUES["merchant_category"])
        .astype(str)
        .replace({"": DEFAULT_INPUT_VALUES["merchant_category"]})
    )

    df_encoded = pd.get_dummies(prepared, columns=["merchant_category"])

    for col in MODEL_COLUMNS:
        if col not in df_encoded.columns:
            df_encoded[col] = 0

    return df_encoded[MODEL_COLUMNS].astype(float)


def preprocess_for_model(txn: dict) -> pd.DataFrame:
    normalized_txn = normalize_transaction_payload(txn)
    validate_transaction_payload(normalized_txn)
    single_df = pd.DataFrame([normalized_txn])
    return preprocess_dataframe_for_model(single_df)
