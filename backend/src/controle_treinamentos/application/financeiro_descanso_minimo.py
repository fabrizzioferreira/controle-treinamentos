from __future__ import annotations

from datetime import date, datetime, time, timedelta

JORNADA_12H_MINUTES = 720
JORNADA_15H_MINUTES = 900
REPOUSO_MINIMO_ATE_12H_MINUTES = 720
REPOUSO_MINIMO_ATE_15H_MINUTES = 960
REPOUSO_MINIMO_ACIMA_15H_MINUTES = 1440


def _text(value, default: str = "") -> str:
    return str(value or "").strip() or default


def _int(value, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_line_date(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _text(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _parse_line_datetime(value, *, base_date: date) -> tuple[datetime | None, bool]:
    if value in (None, ""):
        return None, False
    if isinstance(value, datetime):
        return value.replace(tzinfo=None), True
    if isinstance(value, time):
        return datetime.combine(base_date, value), False
    if isinstance(value, date):
        return datetime.combine(value, time.min), True
    text = _text(value)
    if not text:
        return None, False
    try:
        if ":" in text and "T" not in text and "-" not in text and "/" not in text:
            parts = text.split(":")
            if len(parts) in {2, 3}:
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) == 3 else 0
                return datetime.combine(base_date, time(hour, minute, second)), False
        return datetime.fromisoformat(text.replace(" ", "T")).replace(tzinfo=None), True
    except ValueError:
        return None, False


def linha_intervalo_descanso(row: dict) -> tuple[datetime, datetime] | None:
    if _text(row.get("missao_status")).lower() in {"cancelada", "cancelado", "excluida", "excluido", "obsoleto"}:
        return None
    linha_status = _text(row.get("linha_status")).lower()
    if linha_status and linha_status not in {"ativo", "ativa"}:
        return None
    data_missao = _parse_line_date(row.get("data_missao") or row.get("data"))
    if data_missao is None:
        return None
    data_final = _parse_line_date(row.get("data_final")) or data_missao
    horario_apresentacao, _start_has_explicit_date = _parse_line_datetime(
        row.get("horario_apresentacao") or row.get("hora_apresentacao"),
        base_date=data_missao,
    )
    horario_abandono, end_has_explicit_date = _parse_line_datetime(
        row.get("horario_abandono") or row.get("hora_abandono"),
        base_date=data_missao,
    )
    if horario_apresentacao is None or horario_abandono is None:
        return None
    if not end_has_explicit_date and data_final > data_missao:
        horario_abandono = datetime.combine(data_final, horario_abandono.time())
    if horario_abandono <= horario_apresentacao:
        horario_abandono += timedelta(days=1)
    return horario_apresentacao, horario_abandono


def _minutes_between(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() // 60)


def repouso_minimo_exigido_minutos(duracao_jornada_minutos: int) -> int:
    if duracao_jornada_minutos <= JORNADA_12H_MINUTES:
        return REPOUSO_MINIMO_ATE_12H_MINUTES
    if duracao_jornada_minutos <= JORNADA_15H_MINUTES:
        return REPOUSO_MINIMO_ATE_15H_MINUTES
    return REPOUSO_MINIMO_ACIMA_15H_MINUTES


def calcular_repouso_regulamentar(inicio_jornada: datetime, fim_jornada: datetime) -> dict:
    duracao_jornada_minutos = max(_minutes_between(inicio_jornada, fim_jornada), 0)
    repouso_exigido_minutos = repouso_minimo_exigido_minutos(duracao_jornada_minutos)
    repouso_minimo_ate = fim_jornada + timedelta(minutes=repouso_exigido_minutos)
    return {
        "inicio_jornada": inicio_jornada.isoformat(timespec="minutes"),
        "fim_jornada": fim_jornada.isoformat(timespec="minutes"),
        "duracao_jornada_min": duracao_jornada_minutos,
        "repouso_exigido_min": repouso_exigido_minutos,
        "repouso_minimo_ate": repouso_minimo_ate.isoformat(timespec="minutes"),
        "descanso_minimo_ate": repouso_minimo_ate.isoformat(timespec="minutes"),
    }


def _linhas_validas_ordenadas(rows: list[dict]) -> list[dict]:
    entries: list[dict] = []
    seen: set[tuple[int, int]] = set()
    for row in rows:
        mission_id = _int(row.get("missao_operacional_id"))
        tripulante_id = _int(row.get("tripulante_id") or row.get("linha_tripulante_id"))
        if not mission_id or not tripulante_id:
            continue
        key = (mission_id, tripulante_id)
        if key in seen:
            continue
        interval = linha_intervalo_descanso(row)
        if interval is None:
            continue
        start, end = interval
        entries.append(
            {
                "mission_id": mission_id,
                "tripulante_id": tripulante_id,
                "start": start,
                "end": end,
            }
        )
        seen.add(key)
    return sorted(
        entries,
        key=lambda item: (item["tripulante_id"], item["start"], item["end"], item["mission_id"]),
    )


def calcular_descanso_minimo_detalhes_por_missao(rows: list[dict]) -> dict[int, dict[int, dict]]:
    contexts: dict[int, dict[int, dict]] = {}
    previous_by_tripulante: dict[int, dict] = {}
    for entry in _linhas_validas_ordenadas(rows):
        tripulante_id = entry["tripulante_id"]
        previous = previous_by_tripulante.get(tripulante_id)
        if previous is not None:
            repouso = calcular_repouso_regulamentar(previous["start"], previous["end"])
            descanso_minimo_ate = previous["end"] + timedelta(minutes=repouso["repouso_exigido_min"])
            if entry["start"] < descanso_minimo_ate:
                repouso_realizado_minutos = max(_minutes_between(previous["end"], entry["start"]), 0)
                contexts.setdefault(entry["mission_id"], {})[tripulante_id] = {
                    **repouso,
                    "jornada_anterior_mission_id": previous["mission_id"],
                    "proxima_mission_id": entry["mission_id"],
                    "tripulante_id": tripulante_id,
                    "proxima_apresentacao": entry["start"].isoformat(timespec="minutes"),
                    "repouso_realizado_min": repouso_realizado_minutos,
                    "deficit_repouso_min": _minutes_between(entry["start"], descanso_minimo_ate),
                }
        previous_by_tripulante[tripulante_id] = entry
    return contexts


def calcular_descanso_minimo_contextos_por_missao(rows: list[dict]) -> dict[int, dict[int, str]]:
    detalhes = calcular_descanso_minimo_detalhes_por_missao(rows)
    return {
        mission_id: {
            tripulante_id: detalhe["descanso_minimo_ate"]
            for tripulante_id, detalhe in tripulantes.items()
        }
        for mission_id, tripulantes in detalhes.items()
    }
