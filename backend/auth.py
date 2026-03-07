from __future__ import annotations

import base64
import json
import os
from functools import lru_cache
from typing import Any, Dict

try:
    import firebase_admin
    from firebase_admin import auth, credentials
except ModuleNotFoundError:  # pragma: no cover - handled at runtime if dependency missing
    firebase_admin = None
    auth = None
    credentials = None
from fastapi import HTTPException


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


@lru_cache(maxsize=1)
def auth_required() -> bool:
    return _truthy(os.getenv("AUTH_REQUIRED") or "false")


def _init_firebase() -> None:
    if firebase_admin is None or auth is None or credentials is None:
        raise RuntimeError("Missing dependency: firebase-admin")

    if firebase_admin._apps:
        return

    service_json = (os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or "").strip()
    service_b64 = (os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64") or "").strip()

    if service_json:
        parsed = json.loads(service_json)
        cred = credentials.Certificate(parsed)
    elif service_b64:
        raw = base64.b64decode(service_b64.encode("utf-8")).decode("utf-8")
        parsed = json.loads(raw)
        cred = credentials.Certificate(parsed)
    else:
        cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred)


def verify_id_token(token: str) -> Dict[str, Any]:
    try:
        _init_firebase()
        return dict(auth.verify_id_token(token))
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid auth token: {exc}") from exc
