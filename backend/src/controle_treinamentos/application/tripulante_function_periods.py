from __future__ import annotations

from datetime import date, datetime

from flask import current_app, has_app_context

from ..core.audit_utils import audit_event, rollback_db
from ..core.domain_errors import DomainConflictError, DomainError, DomainNotFoundError, DomainValidationError
from ..db import get_db
from ..repositories.tripulante_function_periods import (
    cancel_function_period,
    fetch_function_period,
    fetch_function_periods_by_tripulante,
    find_overlapping_function_period,
    insert_function_period,
    tripulante_exists,
)
from ..service_layers.pure_validation import validate_tripulante_categoria
from ..services import parse_date

VALID_FUNCOES = {"comandante", "copiloto"}
STATUS_ATIVO = "ativo"
STATUS_CANCELADO = "cancelado"
OBSERVACAO_MAX_LENGTH = 180


class TripulanteFunctionPeriodValidationError(DomainValidationError):
    code = "tripulante_funcao_vigencia_validation_error"


class TripulanteFunctionPeriodConflictError(DomainConflictError):
    code = "tripulante_funcao_vigencia_conflict"


class TripulanteFunctionPeriodTripulanteNotFoundError(DomainNotFoundError):
    code = "tripulante_not_found"

    def __init__(self, message: str = "Tripulante nao encontrado."):
        super().__init__(message, code=self.code, status=self.status)


class TripulanteFunctionPeriodNotFoundError(DomainNotFoundError):
    code = "tripulante_funcao_vigencia_not_found"

    def __init__(self, message: str = "Vigencia de funcao operacional nao encontrada."):
        super().__init__(message, code=self.code, status=self.status)


def _clean_text(value) -> str:
    return str(value or "").strip()


def _date_iso(value) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _datetime_iso(value) -> str | None:
    if value in (None, ""):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _required_date(payload: dict, key: str, label: str) -> date:
    raw = _clean_text(payload.get(key))
    if not raw:
        raise TripulanteFunctionPeriodValidationError(f"{label} e obrigatoria.")
    parsed = parse_date(raw)
    if parsed is None:
        raise TripulanteFunctionPeriodValidationError(f"{label} deve estar no formato YYYY-MM-DD.")
    return parsed


def _optional_date(payload: dict, key: str, label: str) -> date | None:
    raw = _clean_text(payload.get(key))
    if not raw:
        return None
    parsed = parse_date(raw)
    if parsed is None:
        raise TripulanteFunctionPeriodValidationError(f"{label} deve estar no formato YYYY-MM-DD.")
    return parsed


def _normalize_funcao(value) -> str:
    normalized = _clean_text(value).lower()
    aliases = {
        "cmt": "comandante",
        "comandante": "comandante",
        "cmd": "comandante",
        "cop": "copiloto",
        "copiloto": "copiloto",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in VALID_FUNCOES:
        raise TripulanteFunctionPeriodValidationError("Funcao operacional deve ser comandante ou copiloto.")
    return normalized


def _optional_categoria(value) -> str | None:
    raw = _clean_text(value)
    if not raw:
        return None
    lookup_key = raw.lower().replace("_", " ").replace("-", " ")
    aliases = {
        "a": "A",
        "categoria a": "A",
        "b": "B",
        "categoria b": "B",
        "n/a": "N/A",
        "na": "N/A",
        "nao aplicavel": "N/A",
    }
    normalized = aliases.get(lookup_key, raw.upper())
    try:
        return validate_tripulante_categoria(normalized)
    except ValueError as exc:
        raise TripulanteFunctionPeriodValidationError(str(exc)) from exc


def _parse_payload(payload: dict) -> dict:
    funcao = _normalize_funcao(payload.get("funcao_operacional") or payload.get("funcao"))
    categoria = _optional_categoria(payload.get("categoria_operacional") or payload.get("categoria"))
    data_inicio = _required_date(payload, "data_inicio", "Data de inicio")
    data_fim = _optional_date(payload, "data_fim", "Data de fim")
    if data_fim and data_fim < data_inicio:
        raise TripulanteFunctionPeriodValidationError("Data de fim nao pode ser anterior a data de inicio.")
    observacao = _clean_text(payload.get("observacao")) or None
    if observacao and len(observacao) > OBSERVACAO_MAX_LENGTH:
        raise TripulanteFunctionPeriodValidationError(
            f"Observacao deve ter no maximo {OBSERVACAO_MAX_LENGTH} caracteres."
        )
    return {
        "funcao_operacional": funcao,
        "categoria_operacional": categoria,
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat() if data_fim else None,
        "observacao": observacao,
    }


def serialize_function_period(row: dict) -> dict:
    return {
        "id": int(row["id"]),
        "tripulante_id": int(row["tripulante_id"]),
        "funcao_operacional": _clean_text(row.get("funcao_operacional")),
        "categoria_operacional": _clean_text(row.get("categoria_operacional")) or None,
        "data_inicio": _date_iso(row.get("data_inicio")),
        "data_fim": _date_iso(row.get("data_fim")),
        "status": _clean_text(row.get("status")) or STATUS_ATIVO,
        "observacao": row.get("observacao") or "",
        "criado_em": _datetime_iso(row.get("criado_em")),
        "cancelado_em": _datetime_iso(row.get("cancelado_em")),
    }


def _ensure_tripulante_exists(db, *, tripulante_id: int) -> None:
    if not tripulante_exists(db, tripulante_id=tripulante_id):
        raise TripulanteFunctionPeriodTripulanteNotFoundError()


def list_tripulante_function_periods(*, tripulante_id: int) -> dict:
    db = get_db()
    _ensure_tripulante_exists(db, tripulante_id=tripulante_id)
    rows = fetch_function_periods_by_tripulante(db, tripulante_id=tripulante_id)
    return {"items": [serialize_function_period(row) for row in rows]}


def create_tripulante_function_period(*, tripulante_id: int, payload: dict, actor_user_id: int | None) -> dict:
    db = get_db()
    _ensure_tripulante_exists(db, tripulante_id=tripulante_id)
    data = _parse_payload(payload)
    overlap = find_overlapping_function_period(
        db,
        tripulante_id=tripulante_id,
        data_inicio=data["data_inicio"],
        data_fim=data.get("data_fim"),
    )
    if overlap:
        raise TripulanteFunctionPeriodConflictError(
            "Ja existe vigencia de funcao ativa que se sobrepoe ao intervalo informado.",
            code="tripulante_funcao_vigencia_overlap",
        )

    try:
        created = insert_function_period(
            db,
            data={
                **data,
                "tripulante_id": tripulante_id,
                "criado_por": actor_user_id,
            },
        )
        item = serialize_function_period(created)
        audit_event(db, "tripulante_funcao_operacional_vigencia", item["id"], "create", novo=item)
        db.commit()
    except DomainError:
        rollback_db(db)
        raise
    except Exception as exc:
        rollback_db(db)
        if has_app_context():
            current_app.logger.exception("Falha ao salvar vigencia de funcao operacional do tripulante.")
        raise DomainError(
            "Nao foi possivel salvar a vigencia de funcao operacional.",
            status=500,
            code="tripulante_funcao_vigencia_save_failed",
        ) from exc

    return {"item": item}


def cancel_tripulante_function_period(*, tripulante_id: int, vigencia_id: int, actor_user_id: int | None) -> dict:
    db = get_db()
    _ensure_tripulante_exists(db, tripulante_id=tripulante_id)
    current = fetch_function_period(db, tripulante_id=tripulante_id, vigencia_id=vigencia_id)
    if not current:
        raise TripulanteFunctionPeriodNotFoundError()

    if _clean_text(current.get("status")) == STATUS_CANCELADO:
        return {"item": serialize_function_period(current), "operation": "unchanged"}

    try:
        updated = cancel_function_period(
            db,
            tripulante_id=tripulante_id,
            vigencia_id=vigencia_id,
            cancelado_por=actor_user_id,
        )
        if not updated:
            raise TripulanteFunctionPeriodNotFoundError()
        item = serialize_function_period(updated)
        audit_event(
            db,
            "tripulante_funcao_operacional_vigencia",
            item["id"],
            "cancel",
            anterior=serialize_function_period(current),
            novo=item,
        )
        db.commit()
    except DomainError:
        rollback_db(db)
        raise
    except Exception as exc:
        rollback_db(db)
        if has_app_context():
            current_app.logger.exception("Falha ao cancelar vigencia de funcao operacional do tripulante.")
        raise DomainError(
            "Nao foi possivel cancelar a vigencia de funcao operacional.",
            status=500,
            code="tripulante_funcao_vigencia_cancel_failed",
        ) from exc

    return {"item": item, "operation": "cancelled"}
