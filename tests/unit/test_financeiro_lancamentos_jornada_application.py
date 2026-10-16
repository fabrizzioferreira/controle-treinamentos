from __future__ import annotations

import pytest

from backend.src.controle_treinamentos.application import financeiro_lancamentos_jornada as usecases
from backend.src.controle_treinamentos.contracts.financeiro import FINANCE_ORG_SCOPE_DEFAULT


def _payload(**overrides):
    payload = {
        "competencia": "2026-04",
        "data": "2026-04-10",
        "tripulante_id": 101,
        "funcao": "comandante",
        "aeronave_id": 7,
        "categoria_financeira_aeronave": "A",
        "comandante_tripulante_id": 101,
        "copiloto_tripulante_id": 202,
        "relatorio_voo": "CAVOK-10",
        "contratante": "Cliente",
        "numero_db": "CH-10",
        "trecho": "BSB-GRU",
        "status": "ativa",
    }
    payload.update(overrides)
    return payload


def _line_row(**overrides):
    row = {
        "linha_id": 12,
        "missao_operacional_id": 99,
        "competencia": "2026-04",
        "data_missao": "2026-04-10",
        "data_final": "2026-04-10",
        "linha_tripulante_id": 202,
        "linha_funcao": "comandante",
        "linha_status": "ativo",
        "missao_status": "ativa",
        "tripulante_nome": "Ada",
        "aeronave_id": 7,
        "aeronave_nome": "PT-XYZ",
        "comandante_tripulante_id": 101,
        "copiloto_tripulante_id": 202,
        "cavok_numero_voo": "CAVOK-10",
        "chamado": "CH-10",
        "contratante": "Cliente",
        "trecho": "BSB-GRU",
        "horario_apresentacao": "08:00",
        "horario_abandono": "18:00",
        "pos_exec_min": 30,
        "quantidade_pernoites": 0,
        "cobertura_base": 0,
        "categoria_financeira_aeronave": "A",
        "jornada_total_minutos": 600,
        "minutos_diurnos": 540,
        "minutos_noturnos_reais": 60,
        "horas_noturnas_convertidas": "1.1429",
        "hora_reduzida_minutos": 69,
        "minutos_pre": 600,
        "calculo_horario_id": 44,
        "calculo_status": "calculado",
        "calculo_total": "1000.00",
        "valor_domingo_feriado_diurno": "0.00",
        "valor_domingo_feriado_noturno": "0.00",
        "valor_adicional_noturno": "120.00",
    }
    row.update(overrides)
    return row


def test_mission_payload_from_journey_uses_current_cadastro_when_no_function_history(monkeypatch):
    tripulantes = {
        101: {"id": 101, "ativo": 1, "funcao_operacional": "comandante"},
        202: {"id": 202, "ativo": 1, "funcao_operacional": "comandante"},
    }

    monkeypatch.setattr(
        usecases,
        "fetch_tripulante_basico",
        lambda _db, *, tripulante_id: tripulantes.get(int(tripulante_id)),
    )
    monkeypatch.setattr(
        usecases,
        "fetch_equipamento_basico",
        lambda _db, *, aeronave_id: {"id": int(aeronave_id), "ativo": 1, "categoria_financeira": "A"},
    )

    data = usecases._mission_payload_from_journey(
        _payload(),
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        actor_user_id=55,
        db=object(),
    )

    assert data["comandante_tripulante_id"] == 101
    assert data["copiloto_tripulante_id"] == 202
    assert [item["tripulante_id"] for item in data["participantes"]] == [101, 202]
    assert [item["funcao"] for item in data["participantes"]] == ["comandante", "comandante"]
    assert [item["funcao_missao"] for item in data["participantes"]] == ["comandante", "copiloto"]


def test_mission_payload_from_journey_preserves_current_cadastro_fallback_for_commander(monkeypatch):
    tripulantes = {
        101: {"id": 101, "ativo": 1, "funcao_operacional": "copiloto"},
        202: {"id": 202, "ativo": 1, "funcao_operacional": "copiloto"},
    }

    monkeypatch.setattr(
        usecases,
        "fetch_tripulante_basico",
        lambda _db, *, tripulante_id: tripulantes.get(int(tripulante_id)),
    )
    monkeypatch.setattr(
        usecases,
        "fetch_equipamento_basico",
        lambda _db, *, aeronave_id: {"id": int(aeronave_id), "ativo": 1, "categoria_financeira": "A"},
    )

    data = usecases._mission_payload_from_journey(
        _payload(tripulante_id=101, funcao="copiloto", comandante_tripulante_id=101, copiloto_tripulante_id=202),
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        actor_user_id=55,
        db=object(),
    )

    assert data["comandante_tripulante_id"] == 101
    assert data["copiloto_tripulante_id"] == 202
    assert [item["tripulante_id"] for item in data["participantes"]] == [101, 202]
    assert [item["funcao"] for item in data["participantes"]] == ["copiloto", "copiloto"]
    assert [item["funcao_missao"] for item in data["participantes"]] == ["comandante", "copiloto"]


def test_mission_payload_from_journey_uses_function_history_for_flight_date(monkeypatch):
    tripulantes = {
        101: {"id": 101, "ativo": 1, "funcao_operacional": "comandante"},
        202: {"id": 202, "ativo": 1, "funcao_operacional": "comandante"},
    }

    def fake_function_period(_db, *, tripulante_id, data_referencia):
        if int(tripulante_id) == 202 and data_referencia == "2026-06-10":
            return {"funcao_operacional": "copiloto"}
        return None

    monkeypatch.setattr(
        usecases,
        "fetch_tripulante_basico",
        lambda _db, *, tripulante_id: tripulantes.get(int(tripulante_id)),
    )
    monkeypatch.setattr(
        usecases,
        "fetch_equipamento_basico",
        lambda _db, *, aeronave_id: {"id": int(aeronave_id), "ativo": 1, "categoria_financeira": "A"},
    )
    monkeypatch.setattr(usecases, "fetch_tripulante_function_period_for_date", fake_function_period)

    data = usecases._mission_payload_from_journey(
        _payload(
            competencia="2026-06",
            data="2026-06-10",
            tripulante_id=202,
            funcao="comandante",
            comandante_tripulante_id=101,
            copiloto_tripulante_id=202,
        ),
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        actor_user_id=55,
        db=object(),
    )

    assert data["comandante_tripulante_id"] == 101
    assert data["copiloto_tripulante_id"] == 202
    assert [item["tripulante_id"] for item in data["participantes"]] == [101, 202]
    assert [item["funcao"] for item in data["participantes"]] == ["comandante", "copiloto"]
    assert [item["funcao_missao"] for item in data["participantes"]] == ["comandante", "copiloto"]


def test_mission_payload_from_journey_accepts_partial_base_coverage(monkeypatch):
    tripulantes = {
        101: {"id": 101, "ativo": 1, "funcao_operacional": "comandante"},
        202: {"id": 202, "ativo": 1, "funcao_operacional": "copiloto"},
    }

    monkeypatch.setattr(
        usecases,
        "fetch_tripulante_basico",
        lambda _db, *, tripulante_id: tripulantes.get(int(tripulante_id)),
    )
    monkeypatch.setattr(
        usecases,
        "fetch_equipamento_basico",
        lambda _db, *, aeronave_id: {"id": int(aeronave_id), "ativo": 1, "categoria_financeira": "A"},
    )

    data = usecases._mission_payload_from_journey(
        _payload(
            quantidade_pernoites=2,
            participantes=[
                {"tripulante_id": 101, "funcao": "comandante", "cobertura_base": False},
                {"tripulante_id": 202, "funcao": "copiloto", "cobertura_base": True},
            ],
        ),
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        actor_user_id=55,
        db=object(),
    )

    assert data["cobertura_base"] is True
    coverages = {item["tripulante_id"]: item["cobertura_base"] for item in data["participantes"]}
    assert coverages == {101: False, 202: True}


def test_category_from_journey_payload_accepts_palmas_turbohelice_human_labels():
    assert (
        usecases._category_from_payload({"categoria_financeira_aeronave": "Palmas turbo-h\u00e9lice"})
        == "turbohelice_palmas"
    )
    assert (
        usecases._category_from_payload(
            {"categoria_financeira_aeronave": "VD"},
            equipamento={"categoria_financeira": "Turbo h\u00e9lice Palmas"},
        )
        == "turbohelice_palmas"
    )
    assert usecases._category_from_payload({"categoria_financeira_aeronave": "Categoria A"}) == "a"


def test_feriados_jornada_por_datas_inclui_corpus_christi_automatico_sem_cadastro(monkeypatch):
    monkeypatch.setattr(usecases, "listar_feriados_por_datas", lambda *args, **kwargs: [])

    feriados = usecases._feriados_jornada_por_datas(
        object(),
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        datas=["2026-06-03", "2026-06-04"],
    )

    assert feriados == {"2026-06-04"}


def test_serialize_line_preserves_full_crew_names():
    line = usecases._serialize_line(
        _line_row(
            comandante_tripulante_nome="Comandante Nome",
            copiloto_tripulante_nome="Segundo Nome",
            terceiro_tripulante_id=303,
            terceiro_tripulante_funcao="copiloto",
            terceiro_tripulante_nome="Terceiro Nome",
        )
    )

    assert line["comandante_tripulante_nome"] == "Comandante Nome"
    assert line["copiloto_tripulante_nome"] == "Segundo Nome"
    assert line["terceiro_tripulante_nome"] == "Terceiro Nome"


def test_serialize_line_keeps_pos_exec_and_pos_calculation_separate():
    line = usecases._serialize_line(
        _line_row(
            pos_exec_min=0,
            minutos_pos=139,
        )
    )

    assert line["pos_exec_min"] == 0
    assert line["pos_calculo_min"] == 139


def test_descanso_minimo_contextos_por_missao_detecta_antecipacao_de_descanso():
    rows = [
        _line_row(
            linha_id=27,
            missao_operacional_id=24489,
            competencia="2026-05",
            data_missao="2026-05-27",
            data_final="2026-05-27",
            linha_tripulante_id=18,
            horario_apresentacao="08:00:00",
            horario_abandono="18:00:00",
        ),
        _line_row(
            linha_id=28,
            missao_operacional_id=24503,
            competencia="2026-05",
            data_missao="2026-05-28",
            data_final="2026-05-28",
            linha_tripulante_id=18,
            horario_apresentacao="04:00:00",
            horario_abandono="09:30:00",
        ),
    ]

    contexts = usecases._descanso_minimo_contextos_por_missao(rows)

    assert contexts == {24503: {18: "2026-05-28T06:00"}}


def test_listar_linhas_contexto_descanso_minimo_inclui_ultima_jornada_anterior_da_competencia(monkeypatch):
    current = [
        _line_row(
            linha_id=28,
            missao_operacional_id=24503,
            competencia="2026-06",
            data_missao="2026-06-01",
            data_final="2026-06-01",
            linha_tripulante_id=18,
            horario_apresentacao="06:00:00",
            horario_abandono="10:00:00",
        )
    ]
    previous = _line_row(
        linha_id=27,
        missao_operacional_id=24489,
        competencia="2026-05",
        data_missao="2026-05-31",
        data_final="2026-05-31",
        linha_tripulante_id=18,
        horario_apresentacao="18:00:00",
        horario_abandono="23:00:00",
    )
    previous_calls = []

    def fake_listar_linhas_jornada(_db, **kwargs):
        assert kwargs["competencia"] == "2026-06"
        assert kwargs["org_id"] == FINANCE_ORG_SCOPE_DEFAULT
        return current if kwargs["offset"] == 0 else []

    def fake_fetch_previous(_db, **kwargs):
        previous_calls.append(kwargs)
        return previous

    monkeypatch.setattr(usecases, "listar_linhas_jornada", fake_listar_linhas_jornada)
    monkeypatch.setattr(usecases, "fetch_linha_jornada_anterior_competencia", fake_fetch_previous)

    rows = usecases._listar_linhas_contexto_descanso_minimo(
        object(),
        competencia="2026-06",
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
    )

    assert [row["missao_operacional_id"] for row in rows] == [24489, 24503]
    assert previous_calls == [
        {"competencia": "2026-06", "tripulante_id": 18, "org_id": FINANCE_ORG_SCOPE_DEFAULT}
    ]
    assert usecases._descanso_minimo_contextos_por_missao(rows) == {24503: {18: "2026-06-01T11:00"}}


def test_serialize_line_exposes_position_base_coverage_flags():
    line = usecases._serialize_line(
        _line_row(
            quantidade_pernoites=2,
            cobertura_base=True,
            missao_cobertura_base=True,
            comandante_cobertura_base=False,
            copiloto_cobertura_base=True,
            terceiro_cobertura_base=False,
        )
    )

    assert line["cobertura_base"] is True
    assert line["missao_cobertura_base"] is True
    assert line["comandante_cobertura_base"] is False
    assert line["copiloto_cobertura_base"] is True
    assert line["terceiro_cobertura_base"] is False


def test_linha_jornada_legada_sem_tipo_tripulacao_equivale_a_simples(monkeypatch):
    line = usecases._serialize_line(
        _line_row(
            competencia="2026-05",
            data_missao="2026-05-07",
            data_final="2026-05-08",
            horario_apresentacao="23:00",
            horario_abandono="10:20",
        )
    )
    tripulantes = {
        101: {"id": 101, "ativo": 1, "funcao_operacional": "comandante"},
        202: {"id": 202, "ativo": 1, "funcao_operacional": "copiloto"},
    }

    monkeypatch.setattr(
        usecases,
        "fetch_tripulante_basico",
        lambda _db, *, tripulante_id: tripulantes.get(int(tripulante_id)),
    )
    monkeypatch.setattr(
        usecases,
        "fetch_equipamento_basico",
        lambda _db, *, aeronave_id: {"id": int(aeronave_id), "ativo": 1, "categoria_financeira": "A"},
    )

    payload = usecases._mission_payload_from_journey(
        _payload(
            competencia="2026-05",
            data="2026-05-07",
            data_final="2026-05-08",
            apresentacao="23:00",
            abandono="10:20",
        ),
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        actor_user_id=55,
        db=object(),
    )

    assert line["tipo_tripulacao_jornada"] == "simples"
    assert payload["tipo_tripulacao_jornada"] == "simples"
    assert payload["horario_apresentacao"] == "23:00"
    assert payload["horario_abandono"] == "10:20"


def test_mission_payload_from_journey_preserves_optional_third_crew(monkeypatch):
    tripulantes = {
        101: {"id": 101, "ativo": 1, "funcao_operacional": "comandante"},
        202: {"id": 202, "ativo": 1, "funcao_operacional": "copiloto"},
        303: {"id": 303, "ativo": 1, "funcao_operacional": "comandante"},
    }

    monkeypatch.setattr(
        usecases,
        "fetch_tripulante_basico",
        lambda _db, *, tripulante_id: tripulantes.get(int(tripulante_id)),
    )
    monkeypatch.setattr(
        usecases,
        "fetch_equipamento_basico",
        lambda _db, *, aeronave_id: {"id": int(aeronave_id), "ativo": 1, "categoria_financeira": "A"},
    )

    data = usecases._mission_payload_from_journey(
        _payload(terceiro_tripulante_id=303, terceiro_tripulante_funcao="comandante"),
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        actor_user_id=55,
        db=object(),
    )

    assert data["terceiro_tripulante_id"] == 303
    assert data["terceiro_tripulante_funcao"] == "comandante"


def test_mission_payload_from_journey_accepts_third_crew_without_second(monkeypatch):
    tripulantes = {
        101: {"id": 101, "ativo": 1, "funcao_operacional": "comandante"},
        303: {"id": 303, "ativo": 1, "funcao_operacional": "copiloto"},
    }

    monkeypatch.setattr(
        usecases,
        "fetch_tripulante_basico",
        lambda _db, *, tripulante_id: tripulantes.get(int(tripulante_id)),
    )
    monkeypatch.setattr(
        usecases,
        "fetch_equipamento_basico",
        lambda _db, *, aeronave_id: {"id": int(aeronave_id), "ativo": 1, "categoria_financeira": "A"},
    )

    data = usecases._mission_payload_from_journey(
        _payload(
            copiloto_tripulante_id="",
            terceiro_tripulante_id=303,
            terceiro_tripulante_funcao="copiloto",
            counterpart_tripulante_id=303,
        ),
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        actor_user_id=55,
        db=object(),
    )

    assert data["comandante_tripulante_id"] == 101
    assert data["copiloto_tripulante_id"] is None
    assert data["terceiro_tripulante_id"] == 303
    assert [item["tripulante_id"] for item in data["participantes"]] == [101, 303]
    assert [item["funcao_missao"] for item in data["participantes"]] == ["comandante", "copiloto"]


def test_criar_linha_jornada_resolves_second_tripulante_by_mission_slot(monkeypatch):
    class FakeDB:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    db = FakeDB()
    captured = {}
    create_call = {}
    data = {
        **_payload(tripulante_id=202, funcao="copiloto"),
        "org_id": FINANCE_ORG_SCOPE_DEFAULT,
        "comandante_tripulante_id": 101,
        "copiloto_tripulante_id": 202,
        "participantes": [
            {"tripulante_id": 101, "funcao": "comandante", "funcao_missao": "comandante", "status": "ativo"},
            {"tripulante_id": 202, "funcao": "copiloto", "funcao_missao": "copiloto", "status": "ativo"},
        ],
    }

    monkeypatch.setattr(usecases, "_mission_payload_from_journey", lambda *args, **kwargs: data)
    monkeypatch.setattr(usecases, "validar_competencia_aberta_para_mutacao", lambda *args, **kwargs: None)

    def fake_criar_missao_operacional(*args, **kwargs):
        create_call.update(kwargs)
        return {"id": 99}

    monkeypatch.setattr(usecases, "criar_missao_operacional", fake_criar_missao_operacional)
    monkeypatch.setattr(usecases, "_recalculate_after_journey_save", lambda *args, **kwargs: {"status": "calculado"})
    monkeypatch.setattr(usecases, "_audit", lambda *args, **kwargs: None)

    def fake_fetch_linha_jornada_por_missao(_db, **kwargs):
        captured.update(kwargs)
        return {
            "linha_id": 12,
            "missao_operacional_id": 99,
            "competencia": "2026-04",
            "data_missao": "2026-04-10",
            "data_final": "2026-04-10",
            "linha_tripulante_id": 202,
            "linha_status": "ativo",
            "missao_status": "ativa",
            "comandante_tripulante_id": 101,
            "copiloto_tripulante_id": 202,
            "linha_funcao": "copiloto",
        }

    monkeypatch.setattr(usecases, "fetch_linha_jornada_por_missao", fake_fetch_linha_jornada_por_missao)

    result = usecases.criar_linha_jornada(
        _payload(tripulante_id=202, funcao="copiloto"),
        actor_user_id=55,
        db=db,
    )

    assert captured["missao_operacional_id"] == 99
    assert captured["tripulante_id"] == 202
    assert create_call["commit"] is False
    assert result["linha"]["tripulante_id"] == 202
    assert result["linha"]["funcao"] == "copiloto"
    assert db.commit_count == 1


def test_criar_linha_jornada_invalid_payload_preserves_validation_status(monkeypatch):
    class FakeConn:
        def __init__(self):
            self.rollback_count = 0

        def rollback(self):
            self.rollback_count += 1

    class FakeDB:
        def __init__(self):
            self.conn = FakeConn()

    db = FakeDB()

    with pytest.raises(usecases.DomainValidationError) as exc:
        usecases.criar_linha_jornada(
            {"competencia": "2026-04"},
            actor_user_id=55,
            db=db,
        )

    assert exc.value.status == 400
    assert exc.value.code == "finance_journey_required_fields"
    assert db.conn.rollback_count == 1


def test_atualizar_linha_jornada_defers_mission_commit_until_outer_transaction(monkeypatch):
    class FakeDB:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    db = FakeDB()
    rows = [
        _line_row(linha_id=12, missao_operacional_id=99, linha_tripulante_id=101, linha_funcao="comandante"),
        _line_row(linha_id=12, missao_operacional_id=99, linha_tripulante_id=101, linha_funcao="comandante", trecho="BSB-CGH"),
    ]
    calls = {"mission": None, "audits": []}
    data = {
        **_payload(tripulante_id=101, funcao="comandante", trecho="BSB-CGH"),
        "org_id": FINANCE_ORG_SCOPE_DEFAULT,
        "participantes": [
            {"tripulante_id": 101, "funcao": "comandante", "funcao_missao": "comandante", "status": "ativo"},
            {"tripulante_id": 202, "funcao": "copiloto", "funcao_missao": "copiloto", "status": "ativo"},
        ],
    }

    monkeypatch.setattr(usecases, "fetch_linha_jornada", lambda *_args, **_kwargs: rows.pop(0))
    monkeypatch.setattr(usecases, "validar_competencia_aberta_para_mutacao", lambda *args, **kwargs: None)
    monkeypatch.setattr(usecases, "_mission_payload_from_journey", lambda *args, **kwargs: data)
    monkeypatch.setattr(usecases, "_recalculate_after_journey_save", lambda *args, **kwargs: {"status": "calculado"})
    monkeypatch.setattr(usecases, "_audit", lambda _db, **kwargs: calls["audits"].append(kwargs))

    def fake_update_mission(mission_id, payload, *, actor_user_id, org_id, db, require_times, commit):
        calls["mission"] = {
            "mission_id": mission_id,
            "payload": payload,
            "actor_user_id": actor_user_id,
            "org_id": org_id,
            "db": db,
            "require_times": require_times,
            "commit": commit,
        }
        return {"id": mission_id, "status": "ativa"}

    monkeypatch.setattr(usecases, "atualizar_missao_operacional", fake_update_mission)

    result = usecases.atualizar_linha_jornada(
        12,
        _payload(tripulante_id=101, funcao="comandante", trecho="BSB-CGH"),
        actor_user_id=55,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        db=db,
    )

    assert calls["mission"]["mission_id"] == 99
    assert calls["mission"]["commit"] is False
    assert calls["mission"]["require_times"] is False
    assert calls["mission"]["db"] is db
    assert calls["audits"][0]["event_name"] == "finance.journey_line.updated"
    assert result["linha"]["trecho"] == "BSB-CGH"
    assert db.commit_count == 1


def test_atualizar_linha_jornada_recreates_mission_when_crew_identity_changes(monkeypatch):
    class FakeDB:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    db = FakeDB()
    before_row = _line_row(linha_id=12, missao_operacional_id=99, linha_tripulante_id=101, linha_funcao="comandante")
    after_row = _line_row(
        linha_id=77,
        missao_operacional_id=123,
        linha_tripulante_id=303,
        linha_funcao="copiloto",
        terceiro_tripulante_id=303,
        terceiro_tripulante_funcao="copiloto",
    )
    data = {
        **_payload(tripulante_id=303, funcao="copiloto"),
        "org_id": FINANCE_ORG_SCOPE_DEFAULT,
        "comandante_tripulante_id": 101,
        "copiloto_tripulante_id": 202,
        "terceiro_tripulante_id": 303,
        "terceiro_tripulante_funcao": "copiloto",
        "participantes": [
            {"tripulante_id": 101, "funcao": "comandante", "funcao_missao": "comandante", "status": "ativo"},
            {"tripulante_id": 202, "funcao": "copiloto", "funcao_missao": "copiloto", "status": "ativo"},
            {"tripulante_id": 303, "funcao": "copiloto", "funcao_missao": "copiloto", "status": "ativo"},
        ],
    }
    calls = {"cancel": [], "create": [], "recalculate": [], "fetch_new": [], "audits": []}

    monkeypatch.setattr(usecases, "fetch_linha_jornada", lambda *_args, **_kwargs: before_row)
    monkeypatch.setattr(usecases, "validar_competencia_aberta_para_mutacao", lambda *args, **kwargs: None)
    monkeypatch.setattr(usecases, "_mission_payload_from_journey", lambda *args, **kwargs: data)
    monkeypatch.setattr(
        usecases,
        "atualizar_missao_operacional",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("update should not run")),
    )

    def fake_cancel(mission_id, *, actor_user_id, org_id, motivo, db, commit):
        calls["cancel"].append((mission_id, actor_user_id, org_id, motivo, db, commit))
        return {"mission_id": mission_id, "action": "cancelled"}

    def fake_create(payload, *, actor_user_id, org_id, db, require_times, commit):
        calls["create"].append((payload, actor_user_id, org_id, db, require_times, commit))
        return {"id": 123, "status": "ativa"}

    def fake_recalculate(mission_id, *, actor_user_id, org_id, db):
        calls["recalculate"].append((mission_id, actor_user_id, org_id, db))
        return {"status": "calculado"}

    def fake_fetch_new(_db, **kwargs):
        calls["fetch_new"].append(kwargs)
        return after_row

    monkeypatch.setattr(usecases, "cancelar_missao_operacional", fake_cancel)
    monkeypatch.setattr(usecases, "criar_missao_operacional", fake_create)
    monkeypatch.setattr(usecases, "_recalculate_after_journey_save", fake_recalculate)
    monkeypatch.setattr(usecases, "fetch_linha_jornada_por_missao", fake_fetch_new)
    monkeypatch.setattr(usecases, "_audit", lambda _db, **kwargs: calls["audits"].append(kwargs))

    result = usecases.atualizar_linha_jornada(
        12,
        _payload(
            tripulante_id=303,
            funcao="copiloto",
            terceiro_tripulante_id=303,
            terceiro_tripulante_funcao="copiloto",
        ),
        actor_user_id=55,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        db=db,
    )

    assert calls["cancel"] == [
        (
            99,
            55,
            FINANCE_ORG_SCOPE_DEFAULT,
            "recriacao controlada por alteracao de tripulante ou funcao na grade de jornada",
            db,
            False,
        )
    ]
    assert calls["create"][0] == (data, 55, FINANCE_ORG_SCOPE_DEFAULT, db, False, False)
    assert calls["recalculate"] == [(123, 55, FINANCE_ORG_SCOPE_DEFAULT, db)]
    assert calls["fetch_new"] == [
        {"missao_operacional_id": 123, "org_id": FINANCE_ORG_SCOPE_DEFAULT, "tripulante_id": 303}
    ]
    assert calls["audits"][0]["event_name"] == "finance.journey_line.updated"
    assert calls["audits"][0]["reason"] == "recriacao controlada por alteracao de tripulante ou funcao"
    assert calls["audits"][0]["before"]["missao_operacional_id"] == 99
    assert calls["audits"][0]["after"]["recreation"] == {
        "status": "recreated",
        "previous_mission_id": 99,
        "new_mission_id": 123,
        "cancel_action": "cancelled",
    }
    assert result["linha"]["id"] == 77
    assert result["linha"]["missao_operacional_id"] == 123
    assert result["recreation"]["previous_mission_id"] == 99
    assert result["recreation"]["new_mission_id"] == 123
    assert db.commit_count == 1


def test_recalculate_after_journey_save_uses_savepoint_for_unexpected_error(monkeypatch):
    class FakeCursor:
        def close(self):
            pass

    class FakeDB:
        def __init__(self):
            self.statements = []

        def execute(self, statement):
            self.statements.append(statement)
            return FakeCursor()

    db = FakeDB()
    calls = {}

    def boom_recalculate(mission_id, *, actor_user_id, org_id, db, commit):
        calls.update(
            {
                "mission_id": mission_id,
                "actor_user_id": actor_user_id,
                "org_id": org_id,
                "db": db,
                "commit": commit,
            }
        )
        raise RuntimeError("syntax error near token")

    monkeypatch.setattr(usecases, "recalcular_missao_operacional", boom_recalculate)

    result = usecases._recalculate_after_journey_save(
        99,
        actor_user_id=55,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        db=db,
    )

    assert calls["commit"] is False
    assert calls["db"] is db
    assert result["status"] == "pendente"
    assert result["error"]["code"] == "finance_journey_auto_recalculation_failed"
    assert db.statements == [
        "SAVEPOINT finance_journey_recalc",
        "ROLLBACK TO SAVEPOINT finance_journey_recalc",
        "RELEASE SAVEPOINT finance_journey_recalc",
    ]


def test_recalculate_after_journey_save_marks_productivity_domain_error_pending(monkeypatch):
    class FakeCursor:
        def close(self):
            pass

    class FakeDB:
        def __init__(self):
            self.statements = []

        def execute(self, statement):
            self.statements.append(statement)
            return FakeCursor()

    db = FakeDB()
    calls = {"mission": None, "period": None}

    def fake_mission_recalculate(mission_id, *, actor_user_id, org_id, db, commit):
        calls["mission"] = (mission_id, actor_user_id, org_id, db, commit)
        return {"mission_id": mission_id, "competence": "2026-04", "calculation_status": "calculado"}

    def fake_period_recalculate(competencia, *, actor_user_id, org_id, db, commit):
        calls["period"] = (competencia, actor_user_id, org_id, db, commit)
        raise usecases.DomainValidationError(
            "Parametro financeiro ausente.",
            code="finance_parameter_missing",
            status=422,
        )

    monkeypatch.setattr(usecases, "recalcular_missao_operacional", fake_mission_recalculate)
    monkeypatch.setattr(usecases, "recalcular_competencia_financeira", fake_period_recalculate)

    result = usecases._recalculate_after_journey_save(
        99,
        actor_user_id=55,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        db=db,
    )

    assert calls["mission"] == (99, 55, FINANCE_ORG_SCOPE_DEFAULT, db, False)
    assert calls["period"] == ("2026-04", 55, FINANCE_ORG_SCOPE_DEFAULT, db, False)
    assert result["status"] == "calculado"
    assert result["productivity_status"] == "pendente"
    assert result["productivity_error"]["code"] == "finance_parameter_missing"
    assert db.statements == [
        "SAVEPOINT finance_journey_recalc",
        "ROLLBACK TO SAVEPOINT finance_journey_recalc",
        "RELEASE SAVEPOINT finance_journey_recalc",
    ]


def test_criar_linha_jornada_fallbacks_to_created_mission_when_participant_lookup_misses(monkeypatch):
    class FakeDB:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    db = FakeDB()
    calls = []
    data = {
        **_payload(tripulante_id=303, funcao="copiloto"),
        "org_id": FINANCE_ORG_SCOPE_DEFAULT,
        "comandante_tripulante_id": 101,
        "copiloto_tripulante_id": 202,
        "terceiro_tripulante_id": 303,
        "terceiro_tripulante_funcao": "copiloto",
        "participantes": [
            {"tripulante_id": 101, "funcao": "comandante", "funcao_missao": "comandante", "status": "ativo"},
            {"tripulante_id": 202, "funcao": "copiloto", "funcao_missao": "copiloto", "status": "ativo"},
            {"tripulante_id": 303, "funcao": "copiloto", "funcao_missao": "copiloto", "status": "ativo"},
        ],
    }

    monkeypatch.setattr(usecases, "_mission_payload_from_journey", lambda *args, **kwargs: data)
    monkeypatch.setattr(usecases, "validar_competencia_aberta_para_mutacao", lambda *args, **kwargs: None)
    monkeypatch.setattr(usecases, "criar_missao_operacional", lambda *args, **kwargs: {"id": 99})
    monkeypatch.setattr(usecases, "_recalculate_after_journey_save", lambda *args, **kwargs: {"status": "calculado"})
    monkeypatch.setattr(usecases, "_audit", lambda *args, **kwargs: None)

    def fake_fetch_linha_jornada_por_missao(_db, **kwargs):
        calls.append(kwargs)
        if kwargs.get("tripulante_id"):
            return None
        return _line_row(
            linha_id=15,
            missao_operacional_id=99,
            linha_tripulante_id=303,
            linha_funcao="copiloto",
            terceiro_tripulante_id=303,
            terceiro_tripulante_funcao="copiloto",
        )

    monkeypatch.setattr(usecases, "fetch_linha_jornada_por_missao", fake_fetch_linha_jornada_por_missao)

    result = usecases.criar_linha_jornada(
        _payload(tripulante_id=303, funcao="copiloto"),
        actor_user_id=55,
        db=db,
    )

    assert calls == [
        {"missao_operacional_id": 99, "org_id": FINANCE_ORG_SCOPE_DEFAULT, "tripulante_id": 303},
        {"missao_operacional_id": 99, "org_id": FINANCE_ORG_SCOPE_DEFAULT},
    ]
    assert result["linha"]["id"] == 15
    assert result["linha"]["tripulante_id"] == 303
    assert db.commit_count == 1


def test_excluir_linha_jornada_cancels_linked_mission_recalculates_period_and_audits(monkeypatch):
    class FakeDB:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    db = FakeDB()
    rows = [
        _line_row(),
        _line_row(missao_status="cancelada", linha_status="cancelado", calculo_status="obsoleto"),
    ]
    calls = {"validated": [], "cancelled": [], "periods": [], "audits": []}

    monkeypatch.setattr(usecases, "fetch_linha_jornada", lambda *_args, **_kwargs: rows.pop(0))
    monkeypatch.setattr(
        usecases,
        "validar_competencia_aberta_para_mutacao",
        lambda _db, *, competencia, org_id: calls["validated"].append((competencia, org_id)),
    )

    def fake_cancel(mission_id, *, actor_user_id, org_id, motivo, db, commit):
        calls["cancelled"].append((mission_id, actor_user_id, org_id, motivo, db, commit))
        return {"mission": {"id": mission_id, "status": "cancelada"}, "action": "cancelled"}

    def fake_period(competencia, *, actor_user_id, org_id, db, commit):
        calls["periods"].append((competencia, actor_user_id, org_id, db, commit))
        return {"status": "recalculated", "competencia": competencia}

    def fake_audit(_db, **kwargs):
        calls["audits"].append(kwargs)

    monkeypatch.setattr(usecases, "cancelar_missao_operacional", fake_cancel)
    monkeypatch.setattr(usecases, "recalcular_competencia_financeira", fake_period)
    monkeypatch.setattr(usecases, "_audit", fake_audit)

    result = usecases.excluir_linha_jornada(
        12,
        {"motivo": "lançamento duplicado"},
        actor_user_id=55,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        db=db,
    )

    assert calls["validated"] == [("2026-04", FINANCE_ORG_SCOPE_DEFAULT)]
    assert calls["cancelled"] == [(99, 55, FINANCE_ORG_SCOPE_DEFAULT, "lançamento duplicado", db, False)]
    assert calls["periods"] == [("2026-04", 55, FINANCE_ORG_SCOPE_DEFAULT, db, False)]
    assert calls["audits"][0]["event_name"] == "finance.journey_line.cancelled"
    assert calls["audits"][0]["reason"] == "lançamento duplicado"
    assert result["linha"]["status"] == "cancelada"
    assert result["linha"]["pode_cancelar"] is False
    assert result["mission_id"] == 99
    assert result["action"] == "cancelled"
    assert result["recalculation"]["period"]["status"] == "recalculated"
    assert db.commit_count == 1


def test_excluir_linha_jornada_keeps_cancel_when_period_recalculation_is_pending(monkeypatch):
    class FakeCursor:
        def close(self):
            pass

    class FakeDB:
        def __init__(self):
            self.commit_count = 0
            self.statements = []

        def execute(self, statement):
            self.statements.append(statement)
            return FakeCursor()

        def commit(self):
            self.commit_count += 1

    db = FakeDB()
    rows = [
        _line_row(),
        _line_row(missao_status="cancelada", linha_status="cancelado", calculo_status="obsoleto"),
    ]
    calls = {"cancelled": [], "audits": []}

    monkeypatch.setattr(usecases, "fetch_linha_jornada", lambda *_args, **_kwargs: rows.pop(0))
    monkeypatch.setattr(usecases, "validar_competencia_aberta_para_mutacao", lambda *_args, **_kwargs: None)

    def fake_cancel(mission_id, *, actor_user_id, org_id, motivo, db, commit):
        calls["cancelled"].append((mission_id, actor_user_id, org_id, motivo, db, commit))
        return {"mission": {"id": mission_id, "status": "cancelada"}, "action": "cancelled"}

    def fake_period(*_args, **_kwargs):
        raise usecases.DomainValidationError(
            "Parametros financeiros pendentes.",
            code="finance_parameters_pending",
            status=409,
        )

    monkeypatch.setattr(usecases, "cancelar_missao_operacional", fake_cancel)
    monkeypatch.setattr(usecases, "recalcular_competencia_financeira", fake_period)
    monkeypatch.setattr(usecases, "_audit", lambda _db, **kwargs: calls["audits"].append(kwargs))

    result = usecases.excluir_linha_jornada(
        12,
        {"motivo": "lancamento duplicado"},
        actor_user_id=55,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
        db=db,
    )

    assert calls["cancelled"] == [(99, 55, FINANCE_ORG_SCOPE_DEFAULT, "lancamento duplicado", db, False)]
    assert result["linha"]["status"] == "cancelada"
    assert result["recalculation"]["period"]["status"] == "pendente"
    assert result["recalculation"]["period"]["error"]["code"] == "finance_parameters_pending"
    assert calls["audits"][0]["event_name"] == "finance.journey_line.cancelled"
    assert any("ROLLBACK TO SAVEPOINT finance_journey_recalc" in statement for statement in db.statements)
    assert db.commit_count == 1


def test_excluir_linha_jornada_requires_reason():
    with pytest.raises(usecases.DomainValidationError) as exc:
        usecases.excluir_linha_jornada(12, {}, actor_user_id=55, db=object())

    assert exc.value.code == "finance_journey_line_delete_reason_required"
