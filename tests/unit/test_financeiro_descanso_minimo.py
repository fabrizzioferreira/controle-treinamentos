from __future__ import annotations

from datetime import datetime

import pytest

from backend.src.controle_treinamentos.application.financeiro_descanso_minimo import (
    calcular_descanso_minimo_contextos_por_missao,
    calcular_descanso_minimo_detalhes_por_missao,
    calcular_repouso_regulamentar,
)


def _row(**overrides):
    row = {
        "missao_operacional_id": 1,
        "linha_tripulante_id": 101,
        "linha_status": "ativo",
        "missao_status": "ativa",
        "data_missao": "2026-05-01",
        "data_final": "2026-05-01",
        "horario_apresentacao": "08:00",
        "horario_abandono": "18:00",
    }
    row.update(overrides)
    return row


@pytest.mark.parametrize(
    ("inicio", "fim", "duracao_min", "repouso_min", "repouso_ate"),
    [
        ("2026-05-01T08:00:00", "2026-05-01T18:00:00", 600, 720, "2026-05-02T06:00"),
        ("2026-05-01T06:00:00", "2026-05-01T18:00:00", 720, 720, "2026-05-02T06:00"),
        ("2026-05-01T06:00:00", "2026-05-01T18:01:00", 721, 960, "2026-05-02T10:01"),
        ("2026-05-01T05:00:00", "2026-05-01T18:30:00", 810, 960, "2026-05-02T10:30"),
        ("2026-05-01T03:00:00", "2026-05-01T18:00:00", 900, 960, "2026-05-02T10:00"),
        ("2026-05-01T03:00:00", "2026-05-01T18:01:00", 901, 1440, "2026-05-02T18:01"),
        ("2026-05-01T02:00:00", "2026-05-01T18:00:00", 960, 1440, "2026-05-02T18:00"),
    ],
)
def test_repouso_regulamentar_variavel_por_duracao_da_jornada_anterior(
    inicio,
    fim,
    duracao_min,
    repouso_min,
    repouso_ate,
):
    result = calcular_repouso_regulamentar(datetime.fromisoformat(inicio), datetime.fromisoformat(fim))

    assert result["duracao_jornada_min"] == duracao_min
    assert result["repouso_exigido_min"] == repouso_min
    assert result["repouso_minimo_ate"] == repouso_ate
    assert result["descanso_minimo_ate"] == repouso_ate


def test_jornada_inferior_a_12h_sem_deficit_quando_apresentacao_respeita_repouso():
    rows = [
        _row(missao_operacional_id=1, horario_apresentacao="08:00", horario_abandono="18:00"),
        _row(
            missao_operacional_id=2,
            data_missao="2026-05-02",
            data_final="2026-05-02",
            horario_apresentacao="06:00",
            horario_abandono="10:00",
        ),
    ]

    assert calcular_descanso_minimo_contextos_por_missao(rows) == {}
    assert calcular_descanso_minimo_detalhes_por_missao(rows) == {}


def test_invasao_de_repouso_de_12h_calcula_deficit_regulatorio_e_contexto_financeiro():
    rows = [
        _row(missao_operacional_id=1, horario_apresentacao="08:00", horario_abandono="18:00"),
        _row(
            missao_operacional_id=2,
            data_missao="2026-05-02",
            data_final="2026-05-02",
            horario_apresentacao="04:00",
            horario_abandono="09:30",
        ),
    ]

    detalhes = calcular_descanso_minimo_detalhes_por_missao(rows)

    assert calcular_descanso_minimo_contextos_por_missao(rows) == {2: {101: "2026-05-02T06:00"}}
    assert detalhes[2][101]["repouso_exigido_min"] == 720
    assert detalhes[2][101]["repouso_realizado_min"] == 600
    assert detalhes[2][101]["deficit_repouso_min"] == 120


@pytest.mark.parametrize(
    ("inicio", "fim", "proxima_apresentacao", "repouso_ate", "deficit"),
    [
        ("06:00", "18:01", "10:00", "2026-05-02T10:01", 1),
        ("05:00", "18:30", "10:00", "2026-05-02T10:30", 30),
        ("03:00", "18:00", "09:00", "2026-05-02T10:00", 60),
        ("03:00", "18:01", "18:00", "2026-05-02T18:01", 1),
        ("02:00", "18:00", "17:00", "2026-05-02T18:00", 60),
    ],
)
def test_boundaries_12h_15h_e_jornada_maior_que_15h_no_contexto(
    inicio,
    fim,
    proxima_apresentacao,
    repouso_ate,
    deficit,
):
    rows = [
        _row(missao_operacional_id=1, horario_apresentacao=inicio, horario_abandono=fim),
        _row(
            missao_operacional_id=2,
            data_missao="2026-05-02",
            data_final="2026-05-02",
            horario_apresentacao=proxima_apresentacao,
            horario_abandono="23:00",
        ),
    ]

    detalhes = calcular_descanso_minimo_detalhes_por_missao(rows)

    assert calcular_descanso_minimo_contextos_por_missao(rows) == {2: {101: repouso_ate}}
    assert detalhes[2][101]["descanso_minimo_ate"] == repouso_ate
    assert detalhes[2][101]["deficit_repouso_min"] == deficit


@pytest.mark.parametrize("missao_status", ["cancelada", "cancelado", "excluida", "excluido", "obsoleto"])
def test_missao_invalida_entre_jornadas_validas_nao_quebra_cadeia_cronologica(missao_status):
    rows = [
        _row(missao_operacional_id=1, horario_apresentacao="08:00", horario_abandono="18:00"),
        _row(
            missao_operacional_id=2,
            data_missao="2026-05-01",
            data_final="2026-05-01",
            horario_apresentacao="20:00",
            horario_abandono="21:00",
            missao_status=missao_status,
        ),
        _row(
            missao_operacional_id=3,
            data_missao="2026-05-02",
            data_final="2026-05-02",
            horario_apresentacao="06:00",
            horario_abandono="10:00",
        ),
    ]

    assert calcular_descanso_minimo_contextos_por_missao(rows) == {}


@pytest.mark.parametrize("linha_status", ["removido", "cancelado", "inativo"])
def test_linha_invalida_entre_jornadas_validas_nao_quebra_cadeia_cronologica(linha_status):
    rows = [
        _row(missao_operacional_id=1, horario_apresentacao="08:00", horario_abandono="18:00"),
        _row(
            missao_operacional_id=2,
            data_missao="2026-05-01",
            data_final="2026-05-01",
            horario_apresentacao="20:00",
            horario_abandono="21:00",
            linha_status=linha_status,
        ),
        _row(
            missao_operacional_id=3,
            data_missao="2026-05-02",
            data_final="2026-05-02",
            horario_apresentacao="06:00",
            horario_abandono="10:00",
        ),
    ]

    assert calcular_descanso_minimo_contextos_por_missao(rows) == {}


def test_dois_tripulantes_permanecem_isolados():
    rows = [
        _row(missao_operacional_id=1, linha_tripulante_id=101, horario_apresentacao="08:00", horario_abandono="18:00"),
        _row(
            missao_operacional_id=2,
            linha_tripulante_id=202,
            data_missao="2026-05-02",
            data_final="2026-05-02",
            horario_apresentacao="04:00",
            horario_abandono="09:00",
        ),
        _row(
            missao_operacional_id=3,
            linha_tripulante_id=101,
            data_missao="2026-05-02",
            data_final="2026-05-02",
            horario_apresentacao="04:00",
            horario_abandono="09:00",
        ),
    ]

    assert calcular_descanso_minimo_contextos_por_missao(rows) == {3: {101: "2026-05-02T06:00"}}


def test_virada_de_dia_calcula_jornada_e_repouso_com_data_final():
    rows = [
        _row(
            missao_operacional_id=1,
            data_missao="2026-05-01",
            data_final="2026-05-02",
            horario_apresentacao="23:00",
            horario_abandono="10:00",
        ),
        _row(
            missao_operacional_id=2,
            data_missao="2026-05-02",
            data_final="2026-05-02",
            horario_apresentacao="21:00",
            horario_abandono="23:00",
        ),
    ]

    detalhes = calcular_descanso_minimo_detalhes_por_missao(rows)

    assert calcular_descanso_minimo_contextos_por_missao(rows) == {2: {101: "2026-05-02T22:00"}}
    assert detalhes[2][101]["duracao_jornada_min"] == 660
    assert detalhes[2][101]["deficit_repouso_min"] == 60


def test_virada_de_mes_e_ano_nao_quebra_calculo_temporal():
    rows = [
        _row(
            missao_operacional_id=1,
            data_missao="2026-12-31",
            data_final="2026-12-31",
            horario_apresentacao="18:00",
            horario_abandono="23:00",
        ),
        _row(
            missao_operacional_id=2,
            data_missao="2027-01-01",
            data_final="2027-01-01",
            horario_apresentacao="06:00",
            horario_abandono="12:00",
        ),
    ]

    detalhes = calcular_descanso_minimo_detalhes_por_missao(rows)

    assert calcular_descanso_minimo_contextos_por_missao(rows) == {2: {101: "2027-01-01T11:00"}}
    assert detalhes[2][101]["deficit_repouso_min"] == 300


def test_virada_de_competencia_sem_violacao_nao_gera_falso_positivo():
    rows = [
        _row(
            missao_operacional_id=1,
            data_missao="2026-05-31",
            data_final="2026-05-31",
            horario_apresentacao="18:00",
            horario_abandono="23:00",
        ),
        _row(
            missao_operacional_id=2,
            data_missao="2026-06-01",
            data_final="2026-06-01",
            horario_apresentacao="11:00",
            horario_abandono="14:00",
        ),
    ]

    assert calcular_descanso_minimo_contextos_por_missao(rows) == {}
