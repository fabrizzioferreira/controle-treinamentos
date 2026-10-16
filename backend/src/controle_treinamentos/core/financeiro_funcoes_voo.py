"""Flight-only role exceptions; productivity continues to use the crew register.

Henrique Rodrigues Raggiotto (38): commander on King Air from 2026-09-24,
inclusive. This does not change mission seat assignments or productivity.
"""
from __future__ import annotations

from datetime import date, datetime


_HENRIQUE_ID = 38
_HENRIQUE_NOME = "henrique rodrigues raggiotto"
_INICIO = date(2026, 9, 24)
_KING_AIR_TIPOS = ("BE20", "BE9L")


def possui_regra_funcao_voo(tripulante_id) -> bool:
    try:
        return int(tripulante_id or 0) == _HENRIQUE_ID
    except (TypeError, ValueError):
        return False


def resolver_funcao_voo(
    funcao_base: str, *, tripulante: dict | None, equipamento: dict | None, data_missao
) -> str:
    crew = tripulante or {}
    aircraft = equipamento or {}
    try:
        crew_id = int(crew.get("id") or 0)
        flight_date = (
            data_missao.date() if isinstance(data_missao, datetime)
            else data_missao if isinstance(data_missao, date)
            else date.fromisoformat(str(data_missao or "")[:10])
        )
    except (TypeError, ValueError):
        return funcao_base
    name = str(crew.get("nome") or "").strip().lower()
    aircraft_name = str(aircraft.get("nome") or "").strip().upper()
    aircraft_type = str(aircraft.get("tipo") or "").strip().upper()
    king_air = (
        aircraft_type in _KING_AIR_TIPOS
        or aircraft_name == "KING AIR"
        or aircraft_name.startswith("KING AIR ")
    )
    if crew_id == _HENRIQUE_ID and name == _HENRIQUE_NOME and flight_date >= _INICIO and king_air:
        return "comandante"
    return funcao_base


def funcao_voo_sql(funcao_base_sql: str) -> str:
    """Trusted SQL expression for the existing mt/t/mo repository aliases."""
    types_sql = ", ".join(f"'{value}'" for value in _KING_AIR_TIPOS)
    return f"""
CASE
    WHEN mt.tripulante_id = {_HENRIQUE_ID}
      AND LOWER(TRIM(t.nome)) = '{_HENRIQUE_NOME}'
      AND mo.data_missao >= DATE '{_INICIO.isoformat()}'
      AND EXISTS (
          SELECT 1 FROM equipamentos funcao_voo_e
          WHERE funcao_voo_e.id = mo.aeronave_id
            AND (
                UPPER(TRIM(funcao_voo_e.tipo)) IN ({types_sql})
                OR UPPER(TRIM(funcao_voo_e.nome)) = 'KING AIR'
                OR LEFT(UPPER(TRIM(funcao_voo_e.nome)), 9) = 'KING AIR '
            )
      )
    THEN 'comandante'
    ELSE ({funcao_base_sql})
END
"""
