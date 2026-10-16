from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from flask import g, has_request_context, request

try:
    import psycopg2.extras
    _DictRow = psycopg2.extras.DictRow
except (ImportError, AttributeError):
    _DictRow = type(None)  # type: ignore[misc,assignment]

_REDACTED = "<redacted>"
_MAX_TEXT_LEN = 600
_MAX_USER_AGENT_LEN = 300
_SENSITIVE_FIELD_MARKERS = {
    "senha",
    "password",
    "secret",
    "token",
    "authorization",
    "api_key",
    "access_key",
    "cookie",
    "cpf",
    "documento",
    "telefone",
    "phone",
    "email",
    "foto",
    "arquivo_pdf",
    "arquivo",
    "anexo",
}
_CHECKSUM_KEYS = {
    "artifact_sha256",
    "checksum",
    "content_sha256",
    "document_sha256",
    "file_sha256",
    "manifest_sha256",
    "sha256",
    "storage_sha256",
}


def _is_sensitive_key(key: str) -> bool:
    lowered = (key or "").strip().lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in _SENSITIVE_FIELD_MARKERS)


def _truncate_text(value: str) -> str:
    if len(value) <= _MAX_TEXT_LEN:
        return value
    return f"{value[:_MAX_TEXT_LEN]}...[truncated]"


def _mask_cpf(value: str) -> str:
    digits = "".join(char for char in value if char.isdigit())
    if len(digits) != 11:
        return _REDACTED
    return f"***.{digits[3:6]}.***-**"


def _mask_email(value: str) -> str:
    raw = (value or "").strip()
    if "@" not in raw:
        return _REDACTED
    local_part, domain = raw.split("@", 1)
    if not local_part:
        return f"{_REDACTED}@{domain}"
    return f"{local_part[:1]}***@{domain}"


def _mask_phone(value: str) -> str:
    digits = "".join(char for char in (value or "") if char.isdigit())
    if len(digits) < 4:
        return _REDACTED
    return f"***{digits[-4:]}"


def _mask_sensitive_value(key: str, value: Any):
    lowered = (key or "").lower()
    text = str(value or "")
    if "cpf" in lowered or "documento" in lowered:
        return _mask_cpf(text)
    if "email" in lowered:
        return _mask_email(text)
    if "telefone" in lowered or "phone" in lowered:
        return _mask_phone(text)
    if "foto" in lowered or "arquivo" in lowered or "anexo" in lowered:
        return _REDACTED
    return _REDACTED


def _normalize_value(value: Any, *, parent_key: str | None = None):
    if isinstance(value, _DictRow):
        return {key: _normalize_value(value[key], parent_key=str(key)) for key in value.keys()}
    if isinstance(value, dict):
        result = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            if _is_sensitive_key(key):
                result[key] = _mask_sensitive_value(key, item)
            else:
                result[key] = _normalize_value(item, parent_key=key)
        return result
    if isinstance(value, (list, tuple, set)):
        return [_normalize_value(item, parent_key=parent_key) for item in value]
    if is_dataclass(value):
        return _normalize_value(asdict(value), parent_key=parent_key)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<binary:{len(bytes(value))} bytes>"
    if isinstance(value, str):
        if parent_key and _is_sensitive_key(parent_key):
            return _mask_sensitive_value(parent_key, value)
        return _truncate_text(value)
    return value


def normalize_audit_payload(value: Any):
    if value is None:
        return None
    return _normalize_value(value)


def _request_client_ip() -> str | None:
    if not has_request_context():
        return None
    forwarded_for = (request.headers.get("X-Forwarded-For") or "").split(",", 1)[0].strip()
    if forwarded_for:
        return _truncate_text(forwarded_for)
    real_ip = (request.headers.get("X-Real-IP") or "").strip()
    if real_ip:
        return _truncate_text(real_ip)
    return _truncate_text(request.remote_addr or "") or None


def _request_user_agent() -> str | None:
    if not has_request_context():
        return None
    value = (request.headers.get("User-Agent") or "").strip()
    if not value:
        return None
    if len(value) <= _MAX_USER_AGENT_LEN:
        return value
    return f"{value[:_MAX_USER_AGENT_LEN]}...[truncated]"


def _infer_audit_result(acao: str, resultado: str | None) -> tuple[str, bool]:
    if resultado:
        normalized = resultado.strip().lower()
    else:
        normalized = ""
    if not normalized:
        action = (acao or "").strip().lower()
        if any(marker in action for marker in ("failed", "failure", "blocked", "denied", "invalid", "error")):
            normalized = "failure"
        else:
            normalized = "success"
    success = normalized not in {"failure", "failed", "blocked", "denied", "error", "invalid"}
    return normalized, success


def _extract_checksum(value: Any) -> str | None:
    if isinstance(value, dict):
        for raw_key, item in value.items():
            key = str(raw_key).strip().lower()
            if key in _CHECKSUM_KEYS and item not in (None, ""):
                return _truncate_text(str(item))
        for item in value.values():
            found = _extract_checksum(item)
            if found:
                return found
    if isinstance(value, (list, tuple, set)):
        for item in value:
            found = _extract_checksum(item)
            if found:
                return found
    return None


def _build_audit_metadata(
    *,
    acao: str,
    resultado: str | None = None,
    origem: str | None = None,
    checksum: str | None = None,
    payload_anterior=None,
    payload_novo=None,
) -> dict[str, Any]:
    result, success = _infer_audit_result(acao, resultado)
    metadata: dict[str, Any] = {
        "audit_envelope_version": "audit-context-v1",
        "result": result,
        "success": success,
    }
    if has_request_context():
        endpoint = (request.endpoint or "").strip()
        path = (request.path or "").strip()
        metadata.update(
            {
                "request_id": getattr(g, "request_id", None) or None,
                "correlation_id": getattr(g, "correlation_id", None) or getattr(g, "request_id", None) or None,
                "source_endpoint": endpoint or None,
                "source_path": path or None,
                "http_method": request.method,
                "ip_address": _request_client_ip(),
                "user_agent": _request_user_agent(),
            }
        )
    resolved_origin = (origem or "").strip() or metadata.get("source_endpoint") or metadata.get("source_path")
    metadata["origin"] = resolved_origin or "backend"
    resolved_checksum = (checksum or "").strip() or _extract_checksum(payload_novo) or _extract_checksum(payload_anterior)
    if resolved_checksum:
        metadata["checksum"] = resolved_checksum
    return {key: value for key, value in metadata.items() if value not in (None, "")}


def _merge_audit_metadata(existing: Any, metadata: dict[str, Any]) -> dict[str, Any]:
    result = dict(existing) if isinstance(existing, dict) else {}
    for key, value in metadata.items():
        if result.get(key) in (None, "", []):
            result[key] = value
    return result


def _payload_with_audit_metadata(payload: Any, metadata: dict[str, Any]):
    if isinstance(payload, dict):
        result = dict(payload)
        result["audit_metadata"] = _merge_audit_metadata(result.get("audit_metadata"), metadata)
        return result
    return {"value": payload, "audit_metadata": dict(metadata)}


def record_audit_event(
    db,
    *,
    entidade: str,
    entidade_id: int,
    acao: str,
    realizado_por: int,
    payload_anterior=None,
    payload_novo=None,
    observacao: str | None = None,
    resultado: str | None = None,
    origem: str | None = None,
    checksum: str | None = None,
):
    normalized_anterior = normalize_audit_payload(payload_anterior)
    normalized_novo = normalize_audit_payload(payload_novo)
    audit_metadata = _build_audit_metadata(
        acao=acao,
        resultado=resultado,
        origem=origem,
        checksum=checksum,
        payload_anterior=normalized_anterior,
        payload_novo=normalized_novo,
    )
    if normalized_anterior is not None:
        normalized_anterior = _payload_with_audit_metadata(normalized_anterior, audit_metadata)
    if normalized_novo is not None:
        normalized_novo = _payload_with_audit_metadata(normalized_novo, audit_metadata)
    if normalized_anterior is None and normalized_novo is None:
        normalized_novo = {"audit_metadata": audit_metadata}

    db.execute(
        """
        INSERT INTO auditoria_eventos
        (entidade, entidade_id, acao, payload_anterior, payload_novo, realizado_por, observacao)
        VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
        """,
        (
            entidade,
            entidade_id,
            acao,
            json.dumps(normalized_anterior) if normalized_anterior is not None else None,
            json.dumps(normalized_novo) if normalized_novo is not None else None,
            realizado_por,
            (observacao or "").strip() or None,
        ),
    )
