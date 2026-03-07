from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    REPORTLAB_AVAILABLE = True
except Exception:
    colors = None
    A4 = None
    landscape = None
    mm = None
    canvas = None
    Table = None
    TableStyle = None
    REPORTLAB_AVAILABLE = False

from backend import db
from backend.auth import auth_required, verify_id_token
from backend.utils.explain import assess_severity, explain_fraud, generate_reason
from backend.utils.preprocessing import preprocess_dataframe_for_model
from backend.utils.risk_engine import risk_band, rule_risk_score_batch, top_signal_descriptions
from backend.utils.schema import REQUIRED_INPUT_COLUMNS, coerce_dataframe_for_detection

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "fraud_model.pkl"
METADATA_PATH = BASE_DIR / "model_metadata.json"

if not MODEL_PATH.exists():
    raise RuntimeError(f"Missing model artifact: {MODEL_PATH}")

threshold = 0.5
if METADATA_PATH.exists():
    try:
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
        threshold = float(metadata.get("threshold", 0.5))
    except Exception:
        threshold = 0.5

model = joblib.load(MODEL_PATH)

app = FastAPI(title="Financial Fraud Detector API", version="1.0.0")

CASE_OVERRIDES: Dict[str, Dict[str, Any]] = {}
CASE_NOTES: Dict[str, List[Dict[str, Any]]] = {}

MAX_DETECT_ROWS = max(1, int(os.getenv("MAX_DETECT_ROWS", "50000")))
MAX_SHAP_EXPLANATIONS = max(0, int(os.getenv("MAX_SHAP_EXPLANATIONS", "40")))

cors_origins_env = os.getenv("CORS_ORIGINS", "").strip()
CORS_ORIGINS = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

# Allows Vercel preview domains without listing every preview URL.
# Override with env if you want stricter behavior.
CORS_ORIGIN_REGEX = os.getenv(
    "CORS_ORIGIN_REGEX",
    r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$|^vscode-webview://.*$|^null$",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["http://127.0.0.1:5500","http://localhost:5500","http://127.0.0.1:3000","http://localhost:3000"],
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_insert(table: str, payload: Dict[str, Any]) -> str | None:
    if table == "transactions":
        return db.safe_insert_transaction(payload)
    if table == "model_logs":
        return db.safe_insert_model_log(payload)
    if table == "alerts":
        return db.safe_insert_alert(payload)
    return f"Unknown table: {table}"


class CasePatch(BaseModel):
    status: str | None = None
    assignee: str | None = None
    priority: str | None = None
    sla_due_at: str | None = None


class CaseNoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    author: str | None = None


def _require_user(authorization: str | None) -> Dict[str, Any]:
    if not auth_required():
        return {"uid": "local-dev"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization: Bearer <token>")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")

    return verify_id_token(token)


def _case_id_for_alert(alert: Dict[str, Any], idx: int) -> str:
    return str(alert.get("id") or f"{alert.get('transaction_id', 'txn')}-{idx}")


def _build_fraud_pdf(rows: List[Dict[str, Any]]) -> bytes:
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PDF export unavailable: missing dependency 'reportlab'. Install backend requirements.",
        )

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(15 * mm, height - 15 * mm, "Risk Atlas - Fraud Transactions Report")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(15 * mm, height - 22 * mm, f"Total fraud transactions: {len(rows)}")

    if not rows:
        pdf.setFont("Helvetica", 11)
        pdf.drawString(15 * mm, height - 35 * mm, "No fraud transactions available.")
        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    header = ["Transaction ID", "Amount", "Merchant", "Hour", "Severity (if alert)", "Created At"]
    body = [header]

    for row in rows[:500]:
        body.append(
            [
                str(row.get("transaction_id", "")),
                str(row.get("amount", "")),
                str(row.get("merchant_category", "")),
                str(row.get("transaction_hour", "")),
                str(row.get("severity", "n/a")),
                str(row.get("created_at", ""))[:19],
            ]
        )

    table = Table(body, colWidths=[52 * mm, 26 * mm, 42 * mm, 18 * mm, 32 * mm, 50 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b3b66")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c7d1de")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f7fb")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    table_width, table_height = table.wrap(0, 0)
    x = 15 * mm
    y = height - 32 * mm - table_height
    table.drawOn(pdf, x, y)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _validate_dataframe(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_INPUT_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Invalid CSV schema",
                "missing_columns": missing,
                "required_columns": REQUIRED_INPUT_COLUMNS,
            },
        )


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "model": "loaded",
        "threshold": threshold,
        "auth_required": auth_required(),
        "db_configured": bool(db.get_database_url()) and not db.get_db_disabled(),
    }


@app.post("/detect")
async def detect_fraud(
    file: UploadFile = File(...),
    lenient: bool = Query(default=False),
    authorization: str | None = Header(default=None),
) -> Dict[str, Any]:
    _require_user(authorization)

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only CSV files are supported")

    try:
        df = pd.read_csv(file.file)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Unable to read CSV: {exc}") from exc

    started_at = datetime.now(timezone.utc)
    df, schema_notes = coerce_dataframe_for_detection(df, lenient=lenient)
    _validate_dataframe(df)

    truncated = False
    if len(df) > MAX_DETECT_ROWS:
        df = df.head(MAX_DETECT_ROWS).copy()
        truncated = True

    if "transaction_id" not in df.columns:
        df["transaction_id"] = [str(uuid.uuid4()) for _ in range(len(df))]
    else:
        txn_ids = df["transaction_id"].astype(str).str.strip()
        missing = txn_ids.eq("") | txn_ids.isna()
        if missing.any():
            txn_ids.loc[missing] = [str(uuid.uuid4()) for _ in range(int(missing.sum()))]
        df["transaction_id"] = txn_ids

    results: List[Dict[str, Any]] = []
    pending_transactions: List[Dict[str, Any]] = []
    pending_model_logs: List[Dict[str, Any]] = []
    pending_alerts: List[Dict[str, Any]] = []
    pending_result_indexes: List[int] = []
    shap_budget_left = MAX_SHAP_EXPLANATIONS

    X_batch = preprocess_dataframe_for_model(df)
    model_probs = pd.Series(pd.DataFrame(model.predict_proba(X_batch)).iloc[:, 1]).to_numpy(dtype=float)
    rules_probs = rule_risk_score_batch(df)
    txn_rows = df.to_dict(orient="records")

    for idx, txn in enumerate(txn_rows):
        txn_id = str(txn["transaction_id"])
        model_probability = float(model_probs[idx])
        rules_probability = float(rules_probs[idx])
        probability = round((0.78 * model_probability) + (0.22 * rules_probability), 4)
        prediction = probability >= threshold

        db_record = {
            "transaction_id": txn_id,
            "amount": float(txn["amount"]),
            "transaction_hour": int(txn["transaction_hour"]),
            "merchant_category": str(txn["merchant_category"]),
            "foreign_transaction": int(txn["foreign_transaction"]),
            "location_mismatch": int(txn["location_mismatch"]),
            "device_trust_score": int(txn["device_trust_score"]),
            "velocity_last_24h": int(txn["velocity_last_24h"]),
            "cardholder_age": int(txn["cardholder_age"]),
            "is_fraud": bool(prediction),
        }

        pending_transactions.append(db_record)
        pending_model_logs.append(
            {
                "transaction_id": txn_id,
                "predicted_fraud": bool(prediction),
                "probability": probability,
            }
        )
        if prediction:
            pending_alerts.append(
                {
                    "transaction_id": txn_id,
                    "reason": generate_reason(txn),
                    "severity": assess_severity(txn),
                }
            )

        signals = top_signal_descriptions(txn, limit=3)
        use_shap = prediction or abs(probability - threshold) <= 0.08
        allow_shap = use_shap and shap_budget_left > 0 and len(df) <= 15000
        explanation = explain_fraud(txn) if allow_shap else "; ".join(signals[:2])
        if allow_shap:
            shap_budget_left -= 1

        results.append(
            {
                "transaction_id": txn_id,
                "predicted_fraud": bool(prediction),
                "probability": round(probability, 4),
                "model_probability": round(model_probability, 4),
                "rules_probability": round(rules_probability, 4),
                "threshold": threshold,
                "risk_band": risk_band(probability),
                "signals": signals,
                "explanation": explanation,
                "stored": False,
                "store_error": "Pending batch write",
            }
        )
        pending_result_indexes.append(len(results) - 1)

    batch_error = db.insert_detection_batch(
        transactions=pending_transactions,
        model_logs=pending_model_logs,
        alerts=pending_alerts,
    )

    for idx in pending_result_indexes:
        results[idx]["stored"] = batch_error is None
        results[idx]["store_error"] = batch_error

    duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)

    return {
        "results": results,
        "meta": {
            "rows_processed": len(results),
            "rows_input": len(txn_rows),
            "truncated_to_max_rows": truncated,
            "max_rows": MAX_DETECT_ROWS,
            "lenient": lenient,
            "schema_notes": schema_notes[:12],
            "shap_explanations_used": MAX_SHAP_EXPLANATIONS - shap_budget_left,
            "processing_ms": duration_ms,
        },
    }


@app.get("/alerts")
def get_alerts(
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
) -> List[Dict[str, Any]]:
    _require_user(authorization)
    try:
        return db.fetch_alerts(severity=severity, status=status, limit=50)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Alerts fetch failed: {exc}") from exc


@app.get("/cases")
def get_cases(
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
) -> List[Dict[str, Any]]:
    _require_user(authorization)
    try:
        alerts = db.fetch_alerts(severity=severity, status=status, limit=200)
        out: List[Dict[str, Any]] = []
        for idx, alert in enumerate(alerts):
            case_id = _case_id_for_alert(alert, idx)
            override = CASE_OVERRIDES.get(case_id, {})
            notes = CASE_NOTES.get(case_id, [])
            out.append(
                {
                    "case_id": case_id,
                    "transaction_id": alert.get("transaction_id"),
                    "severity": alert.get("severity"),
                    "reason": alert.get("reason"),
                    "status": override.get("status", alert.get("status", "open")),
                    "assignee": override.get("assignee", "unassigned"),
                    "priority": override.get("priority", "normal"),
                    "sla_due_at": override.get("sla_due_at", ""),
                    "notes_count": len(notes),
                    "updated_at": override.get("updated_at", alert.get("created_at")),
                }
            )
        return out
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Cases fetch failed: {exc}") from exc


@app.patch("/cases/{case_id}")
def patch_case(
    case_id: str,
    payload: CasePatch,
    authorization: str | None = Header(default=None),
) -> Dict[str, Any]:
    _require_user(authorization)
    old = CASE_OVERRIDES.get(case_id, {})
    merged = {**old}
    body = payload.model_dump(exclude_none=True)
    for key in ("status", "assignee", "priority", "sla_due_at"):
        if key in body:
            merged[key] = body[key]
    merged["updated_at"] = datetime.now(timezone.utc).isoformat()
    CASE_OVERRIDES[case_id] = merged
    return {"case_id": case_id, "state": merged}


@app.get("/cases/{case_id}/notes")
def get_case_notes(case_id: str, authorization: str | None = Header(default=None)) -> List[Dict[str, Any]]:
    _require_user(authorization)
    return CASE_NOTES.get(case_id, [])


@app.post("/cases/{case_id}/notes")
def add_case_note(
    case_id: str,
    payload: CaseNoteIn,
    authorization: str | None = Header(default=None),
) -> Dict[str, Any]:
    user = _require_user(authorization)
    entry = {
        "id": str(uuid.uuid4()),
        "text": payload.text.strip(),
        "author": payload.author or user.get("uid", "analyst"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    CASE_NOTES[case_id] = [entry, *(CASE_NOTES.get(case_id, []))][:50]
    return {"case_id": case_id, "note": entry, "total_notes": len(CASE_NOTES[case_id])}


@app.get("/analytics")
def get_analytics(authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    _require_user(authorization)

    try:
        total_transactions, total_fraud = db.analytics_totals()
        return {
            "total_transactions": total_transactions,
            "total_fraud": total_fraud,
            "fraud_rate": round((total_fraud / total_transactions) if total_transactions else 0, 4),
            "fraud_by_day": db.analytics_fraud_by_day(),
            "fraud_by_merchant_category": db.analytics_fraud_by_merchant_category(),
            "fraud_by_severity": db.analytics_fraud_by_severity(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analytics fetch failed: {exc}") from exc


@app.get("/governance")
def get_governance(authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    _require_user(authorization)
    try:
        total_transactions, total_fraud = db.analytics_totals()
        fraud_rate = (total_fraud / total_transactions) if total_transactions else 0.0
        by_day = db.analytics_fraud_by_day()
        day_values = list(by_day.values())
        recent = sum(day_values[-3:]) if day_values else 0
        prior = sum(day_values[-6:-3]) if len(day_values) > 3 else 0
        drift_proxy = round(abs(recent - prior) / max(1, prior + recent), 4)
        return {
            "threshold": threshold,
            "total_transactions": total_transactions,
            "total_fraud": total_fraud,
            "fraud_rate": round(fraud_rate, 4),
            "drift_proxy": drift_proxy,
            "stability": "needs_review" if drift_proxy >= 0.35 else "watch" if drift_proxy >= 0.18 else "stable",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Governance fetch failed: {exc}") from exc


@app.get("/download")
def download_data(authorization: str | None = Header(default=None)) -> Dict[str, str]:
    _require_user(authorization)

    try:
        txns = db.fetch_transactions()
        df = pd.DataFrame(txns)
        return {"csv": df.to_csv(index=False)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Download failed: {exc}") from exc


@app.get("/download/fraud-pdf")
def download_fraud_pdf(authorization: str | None = Header(default=None)) -> Response:
    _require_user(authorization)

    try:
        txns = db.fetch_transactions()
        fraud_rows = [row for row in txns if bool(row.get("is_fraud"))]
        pdf_bytes = _build_fraud_pdf(fraud_rows)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="fraud-transactions-report.pdf"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fraud PDF generation failed: {exc}") from exc
