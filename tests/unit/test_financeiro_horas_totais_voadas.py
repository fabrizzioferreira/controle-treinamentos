from __future__ import annotations

import pytest

from backend.src.controle_treinamentos.application import financeiro_horas_totais_voadas as horas
from backend.src.controle_treinamentos.contracts.financeiro import FINANCE_ORG_SCOPE_DEFAULT
from backend.src.controle_treinamentos.repositories import financeiro_lancamentos_jornada as repo


class _FakeCursor:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executed = []
        self.committed = False

    def execute(self, query, params=()):
        self.executed.append((query, params))
        return _FakeCursor(self.rows)

    def commit(self):
        self.committed = True


def _memory(
    *,
    normal_diu=0,
    normal_not=0,
    especial_diu=0,
    especial_not=0,
    normal_pre=0,
    especial_pre=0,
    normal_pos=0,
    especial_pos=0,
    adicional_noturno="100",
    domingo_feriado_noturno="400",
):
    return {
        "parameters": [
            {
                "tipo": "duracao_hora_noturna_minutos",
                "valor": "52.5",
                "unidade": "minutos",
            },
            {
                "tipo": "adicional_noturno",
                "valor": adicional_noturno,
                "unidade": "valor",
            },
            {
                "tipo": "domingo_feriado_noturno",
                "valor": domingo_feriado_noturno,
                "unidade": "valor",
            },
        ],
        "totals": {
            "normal_minutos_diurnos": normal_diu,
            "normal_minutos_noturnos": normal_not,
            "especial_minutos_diurnos": especial_diu,
            "especial_minutos_noturnos": especial_not,
            "normal_minutos_pre": normal_pre,
            "especial_minutos_pre": especial_pre,
            "normal_minutos_pos": normal_pos,
            "especial_minutos_pos": especial_pos,
            "minutos_pre": normal_pre + especial_pre,
            "minutos_pos": normal_pos + especial_pos,
        },
    }


def _row(**overrides):
    payload = {
        "linha_id": 1,
        "linha_status": "ativo",
        "linha_funcao": "comandante",
        "linha_tripulante_id": 101,
        "missao_operacional_id": 201,
        "org_id": FINANCE_ORG_SCOPE_DEFAULT,
        "competencia": "2026-04",
        "missao_status": "ativa",
        "missao_deleted_at": None,
        "tripulante_nome": "Ada Financeira",
        "calculo_horario_id": 301,
        "calculo_status": "calculado",
        "calculos_vigentes_count": 1,
        "minutos_diurnos": 0,
        "minutos_noturnos_reais": 0,
        "horas_noturnas_convertidas": "0.0000",
        "domingo_feriado": False,
        "valor_adicional_noturno": "0.00",
        "valor_domingo_feriado_diurno": "0.00",
        "valor_domingo_feriado_noturno": "0.00",
        "valor_pre": "0.00",
        "valor_pos": "0.00",
        "calculo_total": "0.00",
        "memoria_calculo": _memory(),
        "parametros_usados": [],
    }
    payload.update(overrides)
    return payload


def _consolidar(monkeypatch, rows, *, funcao="comandante", incluir_zerados=True, ativos=None):
    calls = []

    def _fake_rows(db, **kwargs):
        calls.append(kwargs)
        return rows

    monkeypatch.setattr(horas, "listar_linhas_horas_totais_voadas", _fake_rows)
    monkeypatch.setattr(horas, "listar_tripulantes_ativos_por_funcao", lambda _db, **_kwargs: ativos or [])
    result = horas.consolidar_horas_totais_voadas(
        competencia="2026-04",
        funcao=funcao,
        incluir_zerados=incluir_zerados,
        db=object(),
    )
    return result, calls


def _cell_text(cell) -> str:
    return cell.getPlainText() if hasattr(cell, "getPlainText") else str(cell)


def test_agrega_comandante_por_competencia(monkeypatch):
    rows = [
        _row(memoria_calculo=_memory(normal_diu=60), calculo_total="0.00"),
        _row(linha_id=2, missao_operacional_id=202, memoria_calculo=_memory(normal_diu=90), calculo_total="0.00"),
    ]

    result, calls = _consolidar(monkeypatch, rows)

    assert calls[0]["competencia"] == "2026-04"
    assert calls[0]["funcao"] == "comandante"
    linha = result["linhas"][0]
    assert linha["tripulante_id"] == 101
    assert linha["funcao"] == "comandante"
    assert linha["dia_normal_diu_minutos"] == 150
    assert linha["dia_normal_diu_hhmm"] == "02:30"
    assert linha["quantidade_lancamentos"] == 2


def test_agrega_copiloto_por_competencia(monkeypatch):
    rows = [
        _row(
            linha_funcao="copiloto",
            linha_tripulante_id=102,
            tripulante_nome="Bia Copiloto",
            memoria_calculo=_memory(normal_diu=120),
        )
    ]

    result, calls = _consolidar(monkeypatch, rows, funcao="copiloto")

    assert calls[0]["funcao"] == "copiloto"
    assert result["linhas"][0]["funcao"] == "copiloto"
    assert result["linhas"][0]["dia_normal_diu_hhmm"] == "02:00"


def test_todos_consolida_comandantes_e_copilotos(monkeypatch):
    rows = [
        _row(linha_funcao="comandante", linha_tripulante_id=101, tripulante_nome="Ada Comandante", memoria_calculo=_memory(normal_diu=60)),
        _row(linha_id=2, linha_funcao="copiloto", linha_tripulante_id=102, tripulante_nome="Bia Copiloto", memoria_calculo=_memory(normal_diu=120)),
    ]

    result, calls = _consolidar(monkeypatch, rows, funcao="todos")

    assert [call["funcao"] for call in calls] == ["comandante", "copiloto"]
    assert result["contexto"]["funcao"] == "todos"
    assert [(linha["tripulante_id"], linha["funcao"]) for linha in result["linhas"]] == [
        (101, "comandante"),
        (102, "copiloto"),
    ]
    assert result["totais"]["tripulantes"] == 2


def test_inclui_tripulante_ativo_sem_lancamento_quando_zerados(monkeypatch):
    result, calls = _consolidar(
        monkeypatch,
        [],
        funcao="copiloto",
        ativos=[
            {
                "tripulante_id": 97,
                "linha_tripulante_id": 97,
                "tripulante_nome": "Wdison Mateus dos Santos",
                "linha_funcao": "copiloto",
            }
        ],
    )

    assert calls[0]["funcao"] == "copiloto"
    linha = result["linhas"][0]
    assert linha["tripulante_id"] == 97
    assert linha["nome_tripulante"] == "Wdison Mateus dos Santos"
    assert linha["funcao"] == "copiloto"
    assert linha["quantidade_lancamentos"] == 0
    assert linha["valor_total_horas"] == "0.00"
    assert linha["dia_normal_diu_hhmm"] == "00:00"


def test_exclui_calculos_obsoletos(monkeypatch):
    result, _calls = _consolidar(monkeypatch, [_row(calculo_status="obsoleto")])

    assert result["linhas"] == []


def test_exclui_missoes_canceladas(monkeypatch):
    result, _calls = _consolidar(monkeypatch, [_row(missao_status="cancelada")])

    assert result["linhas"] == []


def test_exclui_missoes_excluidas(monkeypatch):
    result, _calls = _consolidar(monkeypatch, [_row(missao_deleted_at="2026-04-20T10:00:00")])

    assert result["linhas"] == []


def test_soma_diu_normal(monkeypatch):
    result, _calls = _consolidar(monkeypatch, [_row(memoria_calculo=_memory(normal_diu=75))])

    assert result["linhas"][0]["dia_normal_diu_minutos"] == 75
    assert result["linhas"][0]["dia_normal_diu_hhmm"] == "01:15"


def test_soma_not_normal_reduzido_e_valor(monkeypatch):
    result, _calls = _consolidar(
        monkeypatch,
        [
            _row(
                memoria_calculo=_memory(normal_not=105),
                horas_noturnas_convertidas="2.0000",
                valor_adicional_noturno="180.50",
                calculo_total="180.50",
            )
        ],
    )

    linha = result["linhas"][0]
    assert linha["dia_normal_not_minutos_reduzidos"] == 120
    assert linha["dia_normal_not_hhmm"] == "02:00"
    assert linha["dia_normal_not_valor"] == "180.50"


def test_soma_diu_domingo_feriado(monkeypatch):
    result, _calls = _consolidar(
        monkeypatch,
        [
            _row(
                memoria_calculo=_memory(especial_diu=180),
                valor_domingo_feriado_diurno="270.00",
                calculo_total="270.00",
                domingo_feriado=True,
            )
        ],
    )

    linha = result["linhas"][0]
    assert linha["domingo_feriado_diu_minutos"] == 180
    assert linha["domingo_feriado_diu_hhmm"] == "03:00"
    assert linha["domingo_feriado_diu_valor"] == "270.00"


def test_soma_not_domingo_feriado_reduzido_e_valor(monkeypatch):
    result, _calls = _consolidar(
        monkeypatch,
        [
            _row(
                memoria_calculo=_memory(especial_not=105),
                horas_noturnas_convertidas="2.0000",
                valor_domingo_feriado_noturno="310.00",
                calculo_total="310.00",
                domingo_feriado=True,
            )
        ],
    )

    linha = result["linhas"][0]
    assert linha["domingo_feriado_not_minutos_reduzidos"] == 120
    assert linha["domingo_feriado_not_hhmm"] == "02:00"
    assert linha["domingo_feriado_not_valor"] == "310.00"


def test_total_da_linha_e_soma_dos_componentes_remuneraveis(monkeypatch):
    result, _calls = _consolidar(
        monkeypatch,
        [
            _row(
                memoria_calculo=_memory(normal_not=105, especial_diu=60, especial_not=105),
                valor_adicional_noturno="100.00",
                valor_domingo_feriado_diurno="200.00",
                valor_domingo_feriado_noturno="300.00",
                calculo_total="600.00",
            )
        ],
    )

    linha = result["linhas"][0]
    total_componentes = (
        float(linha["dia_normal_diu_valor"])
        + float(linha["dia_normal_not_valor"])
        + float(linha["domingo_feriado_diu_valor"])
        + float(linha["domingo_feriado_not_valor"])
        + float(linha["componentes_adicionais_valor"])
    )
    assert total_componentes == 600.0
    assert linha["valor_total_horas"] == "600.00"
    assert linha["possui_pendencias"] is False


def test_embute_pre_pos_normal_em_not_e_zera_adicionais(monkeypatch):
    result, _calls = _consolidar(
        monkeypatch,
        [
            _row(
                memoria_calculo=_memory(normal_not=105, normal_pre=21, normal_pos=42),
                valor_adicional_noturno="100.00",
                valor_pre="40.00",
                valor_pos="60.00",
                calculo_total="200.00",
            )
        ],
    )

    linha = result["linhas"][0]
    assert linha["dia_normal_not_minutos_reduzidos"] == 192
    assert linha["dia_normal_not_hhmm"] == "03:12"
    assert linha["dia_normal_not_valor"] == "200.00"
    assert linha["componentes_adicionais_valor"] == "0.00"
    assert linha["valor_total_horas"] == "200.00"
    assert linha["possui_pendencias"] is False

    rows = horas._total_flight_hours_rows(result, horas._pdf_styles())
    header = [_cell_text(cell) for cell in rows[0]]
    values = [_cell_text(cell) for cell in rows[2]]

    assert all("ADICIONAIS" not in text for text in header)
    assert "VALOR TOTAL" in header[9]
    assert values[9] == "R$ 200,00"


def test_embute_pre_pos_domingo_feriado_em_not_e_zera_adicionais(monkeypatch):
    result, _calls = _consolidar(
        monkeypatch,
        [
            _row(
                memoria_calculo=_memory(especial_not=105, especial_pre=105),
                valor_domingo_feriado_noturno="300.00",
                valor_pre="800.00",
                calculo_total="1100.00",
                domingo_feriado=True,
            )
        ],
    )

    linha = result["linhas"][0]
    assert linha["domingo_feriado_not_minutos_reduzidos"] == 240
    assert linha["domingo_feriado_not_hhmm"] == "04:00"
    assert linha["domingo_feriado_not_valor"] == "1100.00"
    assert linha["componentes_adicionais_valor"] == "0.00"
    assert linha["valor_total_horas"] == "1100.00"
    assert linha["possui_pendencias"] is False


def test_rateia_pre_pos_misto_por_parametros_e_preserva_total_persistido(monkeypatch):
    result, _calls = _consolidar(
        monkeypatch,
        [
            _row(
                memoria_calculo=_memory(normal_pre=105, especial_pre=105),
                valor_pre="1000.00",
                calculo_total="1000.00",
                domingo_feriado=True,
            )
        ],
    )

    linha = result["linhas"][0]
    assert linha["dia_normal_not_minutos_reduzidos"] == 120
    assert linha["dia_normal_not_valor"] == "200.00"
    assert linha["domingo_feriado_not_minutos_reduzidos"] == 120
    assert linha["domingo_feriado_not_valor"] == "800.00"
    assert linha["componentes_adicionais_valor"] == "0.00"
    assert linha["valor_total_horas"] == "1000.00"
    assert linha["possui_pendencias"] is False


def test_memoria_sem_split_mantem_pre_pos_residual_e_marca_pendencia(monkeypatch):
    incomplete_memory = {
        "parameters": [
            {"tipo": "duracao_hora_noturna_minutos", "valor": "52.5", "unidade": "minutos"},
            {"tipo": "adicional_noturno", "valor": "100", "unidade": "valor"},
            {"tipo": "domingo_feriado_noturno", "valor": "400", "unidade": "valor"},
        ],
        "totals": {
            "normal_minutos_diurnos": 0,
            "normal_minutos_noturnos": 0,
            "especial_minutos_diurnos": 0,
            "especial_minutos_noturnos": 0,
            "minutos_pre": 21,
            "minutos_pos": 42,
        },
    }
    result, _calls = _consolidar(
        monkeypatch,
        [
            _row(
                memoria_calculo=incomplete_memory,
                valor_pre="40.00",
                valor_pos="60.00",
                calculo_total="100.00",
            )
        ],
    )

    linha = result["linhas"][0]
    assert linha["dia_normal_not_minutos_reduzidos"] == 0
    assert linha["dia_normal_not_valor"] == "0.00"
    assert linha["componentes_adicionais_valor"] == "100.00"
    assert linha["valor_total_horas"] == "100.00"
    assert linha["possui_pendencias"] is True
    assert linha["pendencias"][0]["code"] == "pre_pos_memoria_sem_split_normal_especial"


def test_nao_usa_preview(monkeypatch):
    result, _calls = _consolidar(monkeypatch, [_row(preview=True, calculo_total="999.00")])

    assert result["linhas"] == []
    assert result["contexto"]["usa_preview"] is False


def test_nao_mistura_funcoes(monkeypatch):
    rows = [
        _row(linha_funcao="comandante", memoria_calculo=_memory(normal_diu=60)),
        _row(linha_id=2, linha_funcao="copiloto", memoria_calculo=_memory(normal_diu=999), calculo_total="999.00"),
    ]

    result, _calls = _consolidar(monkeypatch, rows, funcao="comandante")

    assert len(result["linhas"]) == 1
    assert result["linhas"][0]["funcao"] == "comandante"
    assert result["linhas"][0]["dia_normal_diu_minutos"] == 60


def test_retorna_0000_para_horas_zeradas(monkeypatch):
    result, _calls = _consolidar(monkeypatch, [_row()])

    linha = result["linhas"][0]
    assert linha["dia_normal_diu_hhmm"] == "00:00"
    assert linha["dia_normal_not_hhmm"] == "00:00"
    assert linha["domingo_feriado_diu_hhmm"] == "00:00"
    assert linha["domingo_feriado_not_hhmm"] == "00:00"


def test_retorna_valor_zero_para_campo_sem_pagamento(monkeypatch):
    result, _calls = _consolidar(monkeypatch, [_row(memoria_calculo=_memory(normal_diu=120))])

    linha = result["linhas"][0]
    assert linha["dia_normal_diu_valor"] == "0.00"
    assert linha["componentes_adicionais_valor"] == "0.00"


def test_gera_pendencia_se_ha_lancamento_sem_calculo_persistido(monkeypatch):
    result, _calls = _consolidar(
        monkeypatch,
        [
            _row(
                calculo_horario_id=None,
                calculo_status=None,
                memoria_calculo={},
                calculo_total=None,
            )
        ],
    )

    linha = result["linhas"][0]
    assert linha["valor_total_horas"] == "0.00"
    assert linha["possui_pendencias"] is True
    assert linha["pendencias"][0]["code"] == "calculo_horario_ausente"


def test_repositorio_fonte_filtra_ativos_vigentes_e_deduplica():
    db = _FakeDB(rows=[{"linha_id": 1}])

    rows = repo.listar_linhas_horas_totais_voadas(
        db,
        competencia="2026-04",
        funcao="comandante",
        org_id="org-qa",
    )

    assert rows == [{"linha_id": 1}]
    query, params = db.executed[0]
    assert "ROW_NUMBER() OVER" in query
    assert "ch.status <> 'obsoleto'" in query
    assert "mt.status = 'ativo'" in query
    assert "mo.status <> 'cancelada'" in query
    assert "mo.deleted_at IS NULL" in query
    assert "preview" not in query.lower()
    assert params == ("org-qa", "org-qa", "2026-04", "comandante")


def test_exporta_pdf_horas_totais_voadas_valido_e_auditado(monkeypatch):
    rows = [
        _row(
            memoria_calculo=_memory(normal_diu=60, normal_not=105, especial_diu=30, especial_not=105),
            valor_adicional_noturno="100.00",
            valor_domingo_feriado_diurno="50.00",
            valor_domingo_feriado_noturno="150.00",
            calculo_total="300.00",
        )
    ]
    db = _FakeDB(rows=rows)
    audit_calls = []

    monkeypatch.setattr(horas, "listar_linhas_horas_totais_voadas", lambda _db, **_kwargs: rows)
    monkeypatch.setattr(horas, "listar_tripulantes_ativos_por_funcao", lambda _db, **_kwargs: [])
    monkeypatch.setattr(horas, "record_audit_event", lambda *args, **kwargs: audit_calls.append((args, kwargs)))

    result = horas.exportar_horas_totais_voadas_pdf(
        competencia="2026-04",
        funcao="comandante",
        actor_user_id=77,
        request_id="req-1",
        correlation_id="corr-1",
        db=db,
    )

    assert result["filename"] == "relatorio-horas-totais-voadas-comandantes-2026-04.pdf"
    assert result["mimetype"] == "application/pdf"
    assert result["content"].startswith(b"%PDF")
    assert b"%%EOF" in result["content"][-4096:]
    assert result["metadata"]["record_count"] == 1
    assert result["metadata"]["totais"]["valor_total_horas"] == "300.00"
    assert db.committed is True
    assert audit_calls
    assert audit_calls[0][1]["acao"] == "finance.export.generated"
    assert audit_calls[0][1]["payload_novo"]["metadata"]["source_endpoint"] == "/api/v1/financeiro/horas-totais-voadas.pdf"


def test_exporta_pdf_horas_totais_voadas_bloqueia_pendencia_de_calculo(monkeypatch):
    rows = [
        _row(
            calculo_horario_id=None,
            calculo_status=None,
            memoria_calculo={},
            calculo_total=None,
        )
    ]
    db = _FakeDB(rows=rows)
    audit_calls = []

    monkeypatch.setattr(horas, "listar_linhas_horas_totais_voadas", lambda _db, **_kwargs: rows)
    monkeypatch.setattr(horas, "listar_tripulantes_ativos_por_funcao", lambda _db, **_kwargs: [])
    monkeypatch.setattr(horas, "record_audit_event", lambda *args, **kwargs: audit_calls.append((args, kwargs)))

    with pytest.raises(horas.DomainValidationError) as exc:
        horas.exportar_horas_totais_voadas_pdf(
            competencia="2026-04",
            funcao="comandante",
            actor_user_id=77,
            db=db,
        )

    assert exc.value.status == 409
    assert exc.value.code == "finance_total_flight_hours_pending_calculations"
    assert exc.value.details["pendencias"][0]["code"] == "calculo_horario_ausente"
    assert db.committed is False
    assert audit_calls == []
