from datetime import date

import pytest

from backend.src.controle_treinamentos.core.financeiro_funcoes_voo import resolver_funcao_voo
from backend.src.controle_treinamentos.application import financeiro_lancamentos_jornada as journey
from backend.src.controle_treinamentos.application import financeiro_missoes as missions
from backend.src.controle_treinamentos.application.financeiro_produtividade_funcao import resolver_funcao_produtividade
from backend.src.controle_treinamentos.application.financeiro_bonificacoes import _group_participations
from backend.src.controle_treinamentos.repositories import financeiro_lancamentos_jornada as repository


CREW = {"id": 38, "nome": "Henrique Rodrigues Raggiotto", "funcao_operacional": "copiloto", "ativo": 1}


@pytest.mark.parametrize("aircraft", [
    {"id": 4, "nome": "KING AIR 200-B200", "tipo": "BE20"},
    {"id": 6, "nome": "KING AIR C90A-C90GT", "tipo": "BE9L"},
])
@pytest.mark.parametrize("day,expected", [
    ("2026-09-23", "copiloto"), ("2026-09-24", "comandante"),
    (date(2026, 10, 7), "comandante"), ("2027-01-01", "comandante"),
    (None, "copiloto"), ("invalid", "copiloto"),
])
def test_effective_flight_date_and_models(aircraft, day, expected):
    assert resolver_funcao_voo("copiloto", tripulante=CREW, equipamento=aircraft, data_missao=day) == expected
    assert journey._effective_financial_funcao(CREW, "copiloto", data_missao=day, equipamento=aircraft) == expected
    assert resolver_funcao_produtividade(CREW) == "copiloto"


@pytest.mark.parametrize("aircraft", [
    {"nome": "GULFSTREAM G100", "tipo": "ASTR"},
    {"nome": "WESTWIND 1124", "tipo": "WW24"},
    {"nome": "CESSNA CITATION JET", "tipo": "C525"},
    {"nome": "KING AIRSHIP", "tipo": "OTHER"}, None,
])
def test_other_aircraft_remain_copilot(aircraft):
    assert resolver_funcao_voo("copiloto", tripulante=CREW, equipamento=aircraft, data_missao="2026-09-24") == "copiloto"


@pytest.mark.parametrize("crew", [
    {**CREW, "id": 39}, {**CREW, "nome": "Henrique Silva"}, None,
])
def test_other_crew_unchanged(crew):
    for role in ("comandante", "copiloto"):
        assert resolver_funcao_voo(role, tripulante=crew, equipamento={"tipo": "BE20"}, data_missao="2026-09-24") == role


@pytest.mark.parametrize("crew_seat", ["comandante", "copiloto", "terceiro"])
def test_write_path_uses_flight_role_without_reassigning_seats(monkeypatch, crew_seat):
    crew = {38: CREW, 25: {"id": 25, "nome": "Outro piloto", "ativo": 1, "funcao_operacional": "comandante"}}
    monkeypatch.setattr(journey, "fetch_tripulante_basico", lambda _db, *, tripulante_id: crew[tripulante_id])
    monkeypatch.setattr(journey, "fetch_equipamento_basico", lambda _db, *, aeronave_id: {
        "id": aeronave_id, "nome": "KING AIR 200-B200", "tipo": "BE20", "ativo": 1, "categoria_financeira": "nao_aplicavel"
    })
    payload = {"competencia": "2026-09", "data": "2026-09-24", "tripulante_id": 38,
               "funcao": "copiloto", "aeronave_id": 4, "comandante_tripulante_id": 25,
               "copiloto_tripulante_id": 38, "status": "ativa"}
    if crew_seat == "comandante":
        payload.update(comandante_tripulante_id=38, copiloto_tripulante_id=25, funcao="comandante")
    elif crew_seat == "terceiro":
        payload.update(copiloto_tripulante_id=None, terceiro_tripulante_id=38, terceiro_tripulante_funcao="copiloto")
    result = journey._mission_payload_from_journey(payload, org_id="default", actor_user_id=1, db=object())
    henrique = next(row for row in result["participantes"] if row["tripulante_id"] == 38)
    assert henrique["funcao"] == "comandante"
    assert result["comandante_tripulante_id"] == payload["comandante_tripulante_id"]
    assert result["copiloto_tripulante_id"] == payload["copiloto_tripulante_id"]
    assert CREW["funcao_operacional"] == "copiloto"


def test_productivity_remains_single_copilot_group_for_both_aircraft():
    rows = [{"tripulante_id": 38, "tripulante_nome": CREW["nome"], "funcao": "copiloto",
             "funcao_missao": "comandante", "tripulante_categoria_operacional": "B",
             "aeronave_id": aircraft, "missao_operacional_id": i, "data_missao": "2026-09-24"}
            for i, aircraft in enumerate((4, 6, 8), start=1)]
    groups = _group_participations(rows, org_id="default")
    assert len(groups) == 1
    assert groups[0]["funcao"] == "copiloto"
    assert groups[0]["tripulante"]["categoria_operacional"] == "B"
    assert len(groups[0]["missoes"]) == 3


def test_productivity_join_uses_unchanged_productivity_role():
    query = repository._line_select_sql()
    assert f"AND cp.funcao = {repository._PRODUCTIVITY_CREW_FUNCTION_SQL}" in query
    assert f"AND ch.funcao = {repository._EFFECTIVE_CREW_FUNCTION_SQL}" in query


@pytest.mark.parametrize("day,aircraft_type,expected", [
    ("2026-09-23", "BE20", "copiloto"),
    ("2026-09-24", "BE20", "comandante"),
    ("2026-09-24", "BE9L", "comandante"),
    ("2026-09-24", "ASTR", "copiloto"),
])
def test_direct_mission_preview_agrees_with_flight_rule(monkeypatch, day, aircraft_type, expected):
    monkeypatch.setattr(missions, "fetch_tripulante_basico", lambda _db, **kwargs: CREW)
    monkeypatch.setattr(missions, "fetch_equipamento_basico", lambda _db, **kwargs: {"tipo": aircraft_type})
    payload = {"competencia": "2026-09", "data_missao": day, "aeronave_id": 4,
               "categoria_financeira_aeronave": "nao_aplicavel", "comandante_tripulante_id": 25,
               "copiloto_tripulante_id": 38, "status": "ativa", "trecho": "TEST"}
    result = missions.preview_missao_operacional(payload, db=object())
    assert next(row['funcao'] for row in result['tripulantes_considerados'] if row['tripulante_id']==38) == expected
