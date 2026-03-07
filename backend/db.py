from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import date
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor, execute_values
except ModuleNotFoundError:  # pragma: no cover - handled at runtime if dependency missing
    psycopg2 = None
    sql = None
    RealDictCursor = None
    execute_values = None


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def get_database_url() -> str:
    return (os.getenv("DATABASE_URL") or "").strip()


def get_db_sslmode() -> str:
    return (os.getenv("DB_SSLMODE") or "require").strip()


def get_db_disabled() -> bool:
    return _truthy(os.getenv("DB_DISABLED"))


def _require_driver() -> None:
    if psycopg2 is None or sql is None or RealDictCursor is None or execute_values is None:
        raise RuntimeError("Missing dependency: psycopg2-binary")


def _normalized_database_url(raw_url: str) -> str:
    parts = urlsplit(raw_url)
    query_items = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True) if k.lower() != "channel_binding"]
    normalized_query = urlencode(query_items)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, normalized_query, parts.fragment))


@contextmanager
def _connection():
    _require_driver()

    database_url = get_database_url()
    db_sslmode = get_db_sslmode()

    if get_db_disabled():
        raise RuntimeError("Database disabled by DB_DISABLED")
    if not database_url:
        raise RuntimeError("Missing DATABASE_URL")

    conn = psycopg2.connect(_normalized_database_url(database_url), sslmode=db_sslmode, connect_timeout=10)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


@contextmanager
def _cursor():
    with _connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur


def _insert_row(table: str, payload: Dict[str, Any], *, conflict_target: str | None = None) -> None:
    _require_driver()

    cols = list(payload.keys())
    vals = [payload[col] for col in cols]

    stmt = sql.SQL("INSERT INTO {table} ({cols}) VALUES ({vals})").format(
        table=sql.Identifier(table),
        cols=sql.SQL(", ").join(map(sql.Identifier, cols)),
        vals=sql.SQL(", ").join(sql.Placeholder() for _ in cols),
    )

    if conflict_target:
        stmt = stmt + sql.SQL(" ON CONFLICT ({target}) DO NOTHING").format(
            target=sql.Identifier(conflict_target)
        )

    with _cursor() as cur:
        cur.execute(stmt, vals)


def safe_insert_transaction(payload: Dict[str, Any]) -> str | None:
    try:
        _insert_row("transactions", payload, conflict_target="transaction_id")
        return None
    except Exception as exc:
        return str(exc)


def safe_insert_model_log(payload: Dict[str, Any]) -> str | None:
    try:
        _insert_row("model_logs", payload)
        return None
    except Exception as exc:
        return str(exc)


def safe_insert_alert(payload: Dict[str, Any]) -> str | None:
    try:
        _insert_row("alerts", payload)
        return None
    except Exception as exc:
        return str(exc)


def insert_detection_batch(
    transactions: List[Dict[str, Any]],
    model_logs: List[Dict[str, Any]],
    alerts: List[Dict[str, Any]],
) -> str | None:
    _require_driver()
    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                if transactions:
                    txn_cols = [
                        "transaction_id",
                        "amount",
                        "transaction_hour",
                        "merchant_category",
                        "foreign_transaction",
                        "location_mismatch",
                        "device_trust_score",
                        "velocity_last_24h",
                        "cardholder_age",
                        "is_fraud",
                    ]
                    txn_values = [tuple(row[col] for col in txn_cols) for row in transactions]
                    execute_values(
                        cur,
                        """
                        INSERT INTO transactions (
                          transaction_id, amount, transaction_hour, merchant_category,
                          foreign_transaction, location_mismatch, device_trust_score,
                          velocity_last_24h, cardholder_age, is_fraud
                        ) VALUES %s
                        ON CONFLICT (transaction_id) DO NOTHING
                        """,
                        txn_values,
                    )

                if model_logs:
                    log_cols = ["transaction_id", "predicted_fraud", "probability"]
                    log_values = [tuple(row[col] for col in log_cols) for row in model_logs]
                    execute_values(
                        cur,
                        """
                        INSERT INTO model_logs (transaction_id, predicted_fraud, probability)
                        VALUES %s
                        """,
                        log_values,
                    )

                if alerts:
                    alert_cols = ["transaction_id", "reason", "severity"]
                    alert_values = [tuple(row[col] for col in alert_cols) for row in alerts]
                    execute_values(
                        cur,
                        """
                        INSERT INTO alerts (transaction_id, reason, severity)
                        VALUES %s
                        """,
                        alert_values,
                    )
        return None
    except Exception as exc:
        return str(exc)


def fetch_alerts(*, severity: str | None, status: str | None, limit: int = 50) -> List[Dict[str, Any]]:
    _require_driver()

    where_parts = []
    params: List[Any] = []
    if severity:
        where_parts.append(sql.SQL("severity = %s"))
        params.append(severity)
    if status:
        where_parts.append(sql.SQL("status = %s"))
        params.append(status)

    stmt = sql.SQL("SELECT * FROM alerts")
    if where_parts:
        stmt = stmt + sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_parts)
    stmt = stmt + sql.SQL(" ORDER BY created_at DESC LIMIT %s")
    params.append(int(limit))

    with _cursor() as cur:
        cur.execute(stmt, params)
        return [dict(row) for row in cur.fetchall()]


def fetch_transactions() -> List[Dict[str, Any]]:
    with _cursor() as cur:
        cur.execute("SELECT * FROM transactions ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]


def analytics_totals() -> Tuple[int, int]:
    with _cursor() as cur:
        cur.execute(
            """
            SELECT
              COUNT(*)::int AS total_transactions,
              COALESCE(SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END), 0)::int AS total_fraud
            FROM transactions
            """
        )
        row = cur.fetchone() or {}
        return int(row.get("total_transactions", 0)), int(row.get("total_fraud", 0))


def analytics_fraud_by_day() -> Dict[str, int]:
    with _cursor() as cur:
        cur.execute(
            """
            SELECT
              DATE(created_at) AS txn_date,
              COALESCE(SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END), 0)::int AS fraud_count
            FROM transactions
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
            """
        )
        rows = cur.fetchall()

    out: Dict[str, int] = {}
    for row in rows:
        day = row.get("txn_date")
        day_key = day.isoformat() if isinstance(day, date) else str(day)
        out[day_key] = int(row.get("fraud_count", 0))
    return out


def analytics_fraud_by_merchant_category() -> Dict[str, int]:
    with _cursor() as cur:
        cur.execute(
            """
            SELECT merchant_category, COUNT(*)::int AS fraud_count
            FROM transactions
            WHERE is_fraud = TRUE
            GROUP BY merchant_category
            ORDER BY fraud_count DESC
            """
        )
        rows = cur.fetchall()
    return {
        str(row["merchant_category"]): int(row["fraud_count"])
        for row in rows
        if row.get("merchant_category") is not None
    }


def analytics_fraud_by_severity() -> Dict[str, int]:
    with _cursor() as cur:
        cur.execute(
            """
            SELECT severity, COUNT(*)::int AS severity_count
            FROM alerts
            GROUP BY severity
            ORDER BY severity_count DESC
            """
        )
        rows = cur.fetchall()
    return {
        str(row["severity"]): int(row["severity_count"])
        for row in rows
        if row.get("severity") is not None
    }
