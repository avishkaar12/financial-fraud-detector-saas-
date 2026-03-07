import pandas as pd
import pytest

from backend.utils.preprocessing import preprocess_for_model
from backend.utils.schema import MODEL_COLUMNS


def test_preprocess_aligns_model_columns():
    txn = {
        "amount": 1200,
        "transaction_hour": 4,
        "foreign_transaction": 1,
        "location_mismatch": 0,
        "device_trust_score": 60,
        "velocity_last_24h": 3,
        "cardholder_age": 40,
        "merchant_category": "Electronics",
    }

    X = preprocess_for_model(txn)
    assert list(X.columns) == MODEL_COLUMNS
    assert X.shape == (1, len(MODEL_COLUMNS))


def test_preprocess_missing_required_column_raises():
    txn = {
        "amount": 1200,
        "transaction_hour": 4,
        "foreign_transaction": 1,
        "location_mismatch": 0,
        "device_trust_score": 60,
        "velocity_last_24h": 3,
        "cardholder_age": 40,
    }

    with pytest.raises(ValueError):
        preprocess_for_model(txn)
