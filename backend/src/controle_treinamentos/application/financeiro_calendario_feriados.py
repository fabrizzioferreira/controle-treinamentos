from __future__ import annotations

from datetime import date, datetime, timedelta

from ..contracts.financeiro import FINANCE_ORG_SCOPE_DEFAULT


def _parse_date(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def data_pascoa_gregoriana(ano: int) -> date:
    year = int(ano)
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def feriados_financeiros_moveis_brasil(ano: int) -> dict[date, str]:
    pascoa = data_pascoa_gregoriana(ano)
    return {
        pascoa - timedelta(days=2): "Paixao de Cristo",
        pascoa + timedelta(days=60): "Corpus Christi",
    }


def nome_feriado_financeiro_automatico(value) -> str | None:
    resolved = _parse_date(value)
    if resolved is None:
        return None
    return feriados_financeiros_moveis_brasil(resolved.year).get(resolved)


def datas_feriados_financeiros_automaticos_no_periodo(data_inicio, data_fim) -> set[date]:
    start = _parse_date(data_inicio)
    end = _parse_date(data_fim)
    if start is None or end is None or end < start:
        return set()

    dates: set[date] = set()
    for year in range(start.year, end.year + 1):
        for holiday in feriados_financeiros_moveis_brasil(year):
            if start <= holiday <= end:
                dates.add(holiday)
    return dates


def feriado_financeiro_automatico_por_data(value, *, org_id: str | None = None) -> dict | None:
    resolved = _parse_date(value)
    if resolved is None:
        return None
    name = nome_feriado_financeiro_automatico(resolved)
    if not name:
        return None
    return {
        "id": None,
        "org_id": (org_id or "").strip() or FINANCE_ORG_SCOPE_DEFAULT,
        "data": resolved.isoformat(),
        "nome": name,
        "tipo": "nacional",
        "localidade": None,
        "status": "ativo",
        "created_by": None,
        "created_at": None,
        "updated_by": None,
        "updated_at": None,
    }
