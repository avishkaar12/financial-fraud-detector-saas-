from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_COLUMNS_PATH = BASE_DIR / "model_columns.json"

with MODEL_COLUMNS_PATH.open("r", encoding="utf-8") as f:
    MODEL_COLUMNS: List[str] = json.load(f)

REQUIRED_INPUT_COLUMNS = [
    "amount",
    "transaction_hour",
    "foreign_transaction",
    "location_mismatch",
    "device_trust_score",
    "velocity_last_24h",
    "cardholder_age",
    "merchant_category",
]

NUMERIC_INPUT_COLUMNS = [
    "amount",
    "transaction_hour",
    "foreign_transaction",
    "location_mismatch",
    "device_trust_score",
    "velocity_last_24h",
    "cardholder_age",
]

DEFAULT_INPUT_VALUES: Dict[str, object] = {
    "amount": 0.0,
    "transaction_hour": 12,
    "foreign_transaction": 0,
    "location_mismatch": 0,
    "device_trust_score": 50,
    "velocity_last_24h": 1,
    "cardholder_age": 35,
    "merchant_category": "Unknown",
}

COLUMN_ALIASES = {
    "time": "transaction_hour",
    "hour": "transaction_hour",
    "txn_hour": "transaction_hour",
    "merchant": "merchant_category",
    "category": "merchant_category",
    "merchant_type": "merchant_category",
    "mcc": "merchant_category",
    "foreign": "foreign_transaction",
    "is_foreign": "foreign_transaction",
    "international": "foreign_transaction",
    "is_international": "foreign_transaction",
    "location_diff": "location_mismatch",
    "loc_mismatch": "location_mismatch",
    "geo_mismatch": "location_mismatch",
    "device_score": "device_trust_score",
    "trust_score": "device_trust_score",
    "velocity": "velocity_last_24h",
    "txn_velocity_24h": "velocity_last_24h",
    "transactions_last_24h": "velocity_last_24h",
    "age": "cardholder_age",
    "customer_age": "cardholder_age",
    "txn_id": "transaction_id",
    "id": "transaction_id",
}

_COLUMN_HINTS: Dict[str, List[str]] = {
    "amount": ["amount", "amt", "value", "total"],
    "transaction_hour": ["hour", "time", "timestamp", "datetime", "created_at", "event_time"],
    "merchant_category": ["merchant", "category", "mcc", "merchant_type"],
    "foreign_transaction": ["foreign", "international", "cross_border", "overseas"],
    "location_mismatch": ["location_mismatch", "geo_mismatch", "billing_shipping_mismatch", "address_mismatch"],
    "device_trust_score": ["device_trust_score", "device_score", "trust_score", "device_risk", "risk_score"],
    "velocity_last_24h": ["velocity", "txn_count_24h", "transactions_last_24h", "count_24h"],
    "cardholder_age": ["age", "customer_age", "cardholder_age", "account_holder_age"],
}

_TRUE_VALUES = {"1", "true", "t", "yes", "y", "high", "fraud"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "low", "safe", "legit"}


def normalize_column_name(name: str) -> str:
    base = str(name).strip().lower().replace(" ", "_")
    return COLUMN_ALIASES.get(base, base)


def normalize_transaction_payload(txn: Dict) -> Dict:
    normalized = {}
    for key, value in txn.items():
        norm_key = normalize_column_name(key)
        normalized[norm_key] = value
    return normalized


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {c: normalize_column_name(c) for c in df.columns}
    return df.rename(columns=renamed)


def _find_candidate_column(columns: List[str], target: str) -> str | None:
    if target in columns:
        return target

    for col in columns:
        if normalize_column_name(col) == target:
            return col

    hints = _COLUMN_HINTS.get(target, [])
    for hint in hints:
        for col in columns:
            low = str(col).lower()
            if low == hint or hint in low:
                return col
    return None


def _series_to_binary(series: pd.Series, default: int = 0) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(default).clip(0, 1).round().astype(int)

    normalized = series.astype(str).str.strip().str.lower()
    mapped = normalized.map(lambda v: 1 if v in _TRUE_VALUES else 0 if v in _FALSE_VALUES else default)
    return mapped.astype(int)


def coerce_dataframe_for_detection(df: pd.DataFrame, *, lenient: bool = False) -> Tuple[pd.DataFrame, List[str]]:
    working = normalize_dataframe_columns(df)
    notes: List[str] = []

    if not lenient:
        return working, notes

    columns = list(working.columns)
    for required in REQUIRED_INPUT_COLUMNS:
        if required in working.columns:
            continue
        candidate = _find_candidate_column(columns, required)
        if candidate:
            working[required] = working[candidate]
            notes.append(f"Mapped '{candidate}' -> '{required}'")

    if "transaction_hour" not in working.columns:
        timestamp_col = _find_candidate_column(columns, "transaction_hour")
        if timestamp_col:
            parsed = pd.to_datetime(working[timestamp_col], errors="coerce")
            if parsed.notna().any():
                working["transaction_hour"] = parsed.dt.hour.fillna(DEFAULT_INPUT_VALUES["transaction_hour"])
                notes.append(f"Derived 'transaction_hour' from '{timestamp_col}'")

    for col, default in DEFAULT_INPUT_VALUES.items():
        if col not in working.columns:
            working[col] = default
            notes.append(f"Filled missing '{col}' with default '{default}'")

    working["amount"] = pd.to_numeric(working["amount"], errors="coerce").fillna(DEFAULT_INPUT_VALUES["amount"])
    working["transaction_hour"] = pd.to_numeric(working["transaction_hour"], errors="coerce").fillna(
        DEFAULT_INPUT_VALUES["transaction_hour"]
    ).clip(0, 23).round().astype(int)
    working["foreign_transaction"] = _series_to_binary(working["foreign_transaction"], default=0)
    working["location_mismatch"] = _series_to_binary(working["location_mismatch"], default=0)
    working["device_trust_score"] = pd.to_numeric(working["device_trust_score"], errors="coerce").fillna(
        DEFAULT_INPUT_VALUES["device_trust_score"]
    ).clip(0, 100).round().astype(int)
    working["velocity_last_24h"] = pd.to_numeric(working["velocity_last_24h"], errors="coerce").fillna(
        DEFAULT_INPUT_VALUES["velocity_last_24h"]
    ).clip(0, 1000).round().astype(int)
    working["cardholder_age"] = pd.to_numeric(working["cardholder_age"], errors="coerce").fillna(
        DEFAULT_INPUT_VALUES["cardholder_age"]
    ).clip(0, 120).round().astype(int)
    working["merchant_category"] = (
        working["merchant_category"].fillna(DEFAULT_INPUT_VALUES["merchant_category"]).astype(str).replace({"": "Unknown"})
    )

    return working, notes


def validate_transaction_payload(txn: Dict) -> None:
    missing = [c for c in REQUIRED_INPUT_COLUMNS if c not in txn]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
