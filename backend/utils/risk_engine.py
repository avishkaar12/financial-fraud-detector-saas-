from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

@dataclass
class RiskSignal:
    name: str
    weight: float
    score: float
    description: str

    @property
    def impact(self) -> float:
        return self.weight * self.score


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def evaluate_risk_signals(txn: Dict) -> List[RiskSignal]:
    amount = _safe_float(txn.get("amount", 0.0))
    hour = _safe_int(txn.get("transaction_hour", 0))
    foreign = _safe_int(txn.get("foreign_transaction", 0))
    mismatch = _safe_int(txn.get("location_mismatch", 0))
    trust_score = _safe_int(txn.get("device_trust_score", 50))
    velocity = _safe_int(txn.get("velocity_last_24h", 0))
    age = _safe_int(txn.get("cardholder_age", 35))

    amount_score = _clamp01(amount / 25000.0)
    velocity_score = _clamp01(velocity / 12.0)
    trust_risk = _clamp01((100.0 - trust_score) / 100.0)
    hour_risk = 1.0 if hour in {0, 1, 2, 3, 4} else (0.6 if hour in {22, 23} else 0.15)
    foreign_mismatch = 1.0 if foreign == 1 and mismatch == 1 else (0.55 if foreign == 1 or mismatch == 1 else 0.05)
    age_risk = 0.65 if age < 21 or age > 75 else 0.15

    return [
        RiskSignal("amount", 0.23, amount_score, f"Transaction amount score={amount_score:.2f}"),
        RiskSignal("velocity", 0.21, velocity_score, f"Velocity in last 24h score={velocity_score:.2f}"),
        RiskSignal("device_risk", 0.2, trust_risk, f"Device trust risk score={trust_risk:.2f}"),
        RiskSignal("hour_pattern", 0.14, hour_risk, f"Hour-based risk score={hour_risk:.2f}"),
        RiskSignal("cross_border_mismatch", 0.17, foreign_mismatch, f"Cross-border mismatch score={foreign_mismatch:.2f}"),
        RiskSignal("age_profile", 0.05, age_risk, f"Age-profile anomaly score={age_risk:.2f}"),
    ]


def rule_risk_score(txn: Dict) -> float:
    signals = evaluate_risk_signals(txn)
    return round(_clamp01(sum(s.impact for s in signals)), 4)


def rule_risk_score_batch(df: pd.DataFrame) -> np.ndarray:
    amount = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    hour = pd.to_numeric(df["transaction_hour"], errors="coerce").fillna(12).to_numpy(dtype=int)
    foreign = pd.to_numeric(df["foreign_transaction"], errors="coerce").fillna(0).to_numpy(dtype=int)
    mismatch = pd.to_numeric(df["location_mismatch"], errors="coerce").fillna(0).to_numpy(dtype=int)
    trust_score = pd.to_numeric(df["device_trust_score"], errors="coerce").fillna(50).to_numpy(dtype=float)
    velocity = pd.to_numeric(df["velocity_last_24h"], errors="coerce").fillna(0).to_numpy(dtype=float)
    age = pd.to_numeric(df["cardholder_age"], errors="coerce").fillna(35).to_numpy(dtype=int)

    amount_score = np.clip(amount / 25000.0, 0.0, 1.0)
    velocity_score = np.clip(velocity / 12.0, 0.0, 1.0)
    trust_risk = np.clip((100.0 - trust_score) / 100.0, 0.0, 1.0)
    hour_risk = np.where(np.isin(hour, [0, 1, 2, 3, 4]), 1.0, np.where(np.isin(hour, [22, 23]), 0.6, 0.15))
    foreign_mismatch = np.where(
        (foreign == 1) & (mismatch == 1),
        1.0,
        np.where((foreign == 1) | (mismatch == 1), 0.55, 0.05),
    )
    age_risk = np.where((age < 21) | (age > 75), 0.65, 0.15)

    score = (
        (0.23 * amount_score)
        + (0.21 * velocity_score)
        + (0.2 * trust_risk)
        + (0.14 * hour_risk)
        + (0.17 * foreign_mismatch)
        + (0.05 * age_risk)
    )
    return np.round(np.clip(score, 0.0, 1.0), 4)


def top_signal_descriptions(txn: Dict, limit: int = 3) -> List[str]:
    signals = evaluate_risk_signals(txn)
    ranked = sorted(signals, key=lambda s: s.impact, reverse=True)
    return [s.description for s in ranked[:limit]]


def risk_band(score: float) -> str:
    if score >= 0.8:
        return "critical"
    if score >= 0.6:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"
