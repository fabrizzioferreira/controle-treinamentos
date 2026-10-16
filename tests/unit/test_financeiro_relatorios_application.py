from __future__ import annotations

from decimal import Decimal

import pytest

from backend.src.controle_treinamentos.application import financeiro_relatorios
from backend.src.controle_treinamentos.application.financeiro_competencias import (
    ParametrosNaoElegiveisFechamentoRealErro,
)
from backend.src.controle_treinamentos.contracts.financeiro import FINANCE_ORG_SCOPE_DEFAULT
from backend.src.controle_treinamentos.core.domain_errors import DomainValidationError


class _FakeDB:
    def __init__(self):
        self.committed = False

    def commit(self):
        self.committed = True


def _period_payload(status: str = "aberta") -> dict:
    snapshot = {
        "snapshot_version": "finance-period-snapshot-v1",
        "generated_at": "2026-04-30T12:00:00",
        "missoes_operacionais": [
            {
                "id": 10,
                "data_missao": "2026-04-10",
                "cavok_numero_voo": "QA-100",
                "aeronave_id": 2,
                "categoria_financeira_aeronave": "a",
                "comandante_tripulante_id": 135,
                "copiloto_tripulante_id": 136,
                "status": "ativa",
            }
        ],
        "calculos_horarios": [
            {
                "id": 21,
                "mission_id": 10,
                "tripulante_id": 135,
                "tripulante": {"nome": "Comandante QA"},
                "funcao": "comandante",
                "jornada_total_minutos": 120,
                "minutos_noturnos_reais": 60,
                "horas_noturnas_convertidas": "1.1429",
                "total": "120.00",
                "status": "calculado",
                "memoria_calculo": {"formula": "60 / 52.5"},
                "parametros_usados": [{"id": 1, "tipo": "duracao_hora_noturna_minutos", "unidade": "minutos", "valor": "52.5"}],
            }
        ],
        "calculos_produtividade": [
            {
                "id": 31,
                "tripulante_id": 135,
                "tripulante": {"nome": "Comandante QA"},
                "funcao": "comandante",
                "categoria_aplicavel": "categoria a",
                "produtividade_calculada": "300.00",
                "garantia_minima": "3000.00",
                "total_devido": "3000.00",
                "status": "calculado",
                "memoria_calculo": {"formula": "max(produtividade, garantia)"},
                "parametros_usados": [{"id": 34, "tipo": "garantia_minima", "unidade": "valor", "valor": "3000.00"}],
            }
        ],
        "parametros_usados": [
            {"id": 1, "tipo": "duracao_hora_noturna_minutos", "unidade": "minutos", "valor": "52.5"},
            {"id": 34, "tipo": "garantia_minima", "funcao": "comandante", "categoria": "categoria a", "unidade": "valor", "valor": "3000.00"},
        ],
        "divergencias": [],
        "totals": {
            "mission_count": 1,
            "hourly_calculation_count": 1,
            "productivity_calculation_count": 1,
            "divergence_count": 0,
            "total_horario": "120.00",
            "total_produtividade": "3000.00",
            "total_geral": "3120.00",
        },
    }
    return {
        "period": {
            "id": 7,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-04",
            "status": status,
            "snapshot": snapshot if status == "fechada" else None,
            "totals": snapshot["totals"],
        },
        "snapshot": snapshot,
        "totals": snapshot["totals"],
        "divergences": [],
    }


def test_gerar_relatorio_competencia_pdf_usa_dados_persistidos_e_registra_audit(monkeypatch):
    db = _FakeDB()
    detail_calls = []
    audit_calls = []
    recalculate_calls = []

    def fake_detail(competencia, **kwargs):
        detail_calls.append((competencia, kwargs))
        return _period_payload(status="aberta")

    monkeypatch.setattr(financeiro_relatorios, "detalhar_competencia_financeira", fake_detail)
    monkeypatch.setattr(
        financeiro_relatorios,
        "recalcular_competencia_financeira",
        lambda *args, **kwargs: recalculate_calls.append((args, kwargs)),
        raising=False,
    )
    monkeypatch.setattr(
        financeiro_relatorios,
        "avaliar_elegibilidade_fechamento_real_snapshot",
        lambda **kwargs: {
            "environment": "hml",
            "release_eligible": False,
            "blocking_parameters": [{"parameter_id": 2}],
        },
    )
    monkeypatch.setattr(financeiro_relatorios, "record_audit_event", lambda *args, **kwargs: audit_calls.append(kwargs))

    result = financeiro_relatorios.gerar_relatorio_financeiro_competencia_pdf(
        "2026-04",
        actor_user_id=501,
        request_id="webreq-pdf",
        correlation_id="corr-pdf",
        db=db,
    )

    assert result["content"].startswith(b"%PDF")
    assert result["mimetype"] == "application/pdf"
    assert result["mode"] == "previa"
    assert result["filename"] == "relatorio-financeiro-2026-04-previa.pdf"
    assert detail_calls == [("2026-04", {"org_id": FINANCE_ORG_SCOPE_DEFAULT, "db": db})]
    assert db.committed is True
    assert audit_calls[0]["acao"] == "finance.export.generated"
    assert audit_calls[0]["entidade"] == "finance_export"
    assert audit_calls[0]["payload_novo"]["metadata"]["format"] == "pdf"
    assert audit_calls[0]["payload_novo"]["metadata"]["record_count"] == 3
    assert audit_calls[0]["payload_novo"]["totals"]["total_geral"] == "3120.00"
    assert result["metadata"]["release_eligibility"]["release_eligible"] is False
    assert result["metadata"]["filters"]["mode"] == "previa"
    assert result["metadata"]["event_name"] == "finance.export.generated"
    assert recalculate_calls == []


def test_pdf_fechamento_bloqueia_quando_snapshot_nao_elegivel(monkeypatch):
    db = _FakeDB()
    monkeypatch.setattr(
        financeiro_relatorios,
        "detalhar_competencia_financeira",
        lambda *args, **kwargs: _period_payload(status="fechada"),
    )
    monkeypatch.setattr(
        financeiro_relatorios,
        "avaliar_elegibilidade_fechamento_real_snapshot",
        lambda **kwargs: (_ for _ in ()).throw(
            ParametrosNaoElegiveisFechamentoRealErro(
                competencia="2026-04",
                environment="hml",
                blocking_parameters=[{"parameter_id": 51, "reasons": ["classificacao_nao_elegivel:qa-smoke"]}],
            )
        ),
    )
    audit_calls = []
    monkeypatch.setattr(financeiro_relatorios, "record_audit_event", lambda *args, **kwargs: audit_calls.append(kwargs))

    with pytest.raises(ParametrosNaoElegiveisFechamentoRealErro) as exc:
        financeiro_relatorios.gerar_relatorio_financeiro_competencia_pdf("2026-04", db=db)

    assert exc.value.code == "finance_parameters_not_release_eligible"
    assert audit_calls == []
    assert db.committed is False


def test_gerar_relatorio_competencia_fechada_marca_fechamento(monkeypatch):
    db = _FakeDB()
    release_gate_calls = []
    monkeypatch.setattr(
        financeiro_relatorios,
        "detalhar_competencia_financeira",
        lambda *args, **kwargs: _period_payload(status="fechada"),
    )

    def _fake_release_gate(**kwargs):
        release_gate_calls.append(kwargs)
        return {
            "environment": "hml",
            "release_eligible": True,
            "blocking_parameters": [],
        }

    monkeypatch.setattr(
        financeiro_relatorios,
        "avaliar_elegibilidade_fechamento_real_snapshot",
        _fake_release_gate,
    )
    monkeypatch.setattr(financeiro_relatorios, "record_audit_event", lambda *args, **kwargs: None)

    result = financeiro_relatorios.gerar_relatorio_financeiro_competencia_pdf("2026-04", db=db)

    assert result["content"].startswith(b"%PDF")
    assert result["mode"] == "fechamento"
    assert result["filename"] == "relatorio-financeiro-2026-04-fechamento.pdf"
    assert result["metadata"]["release_eligibility"]["release_eligible"] is True
    assert release_gate_calls[0]["strict"] is True


def test_release_gate_story_includes_operational_fields_and_blocking_parameters():
    story = []
    styles = financeiro_relatorios._styles()
    snapshot = {
        "release_gate": {
            "environment": "hml",
            "release_eligible": False,
            "next_action": "Promover parametros canonicos para release.",
            "blocking_parameters": [
                {
                    "parameter_id": 51,
                    "classification": "qa-smoke",
                    "reasons": ["classificacao_nao_elegivel:qa-smoke"],
                }
            ],
        }
    }

    financeiro_relatorios._release_gate_story(story, snapshot, styles, mode="fechamento")

    assert len(story) == 3
    assert "Release gate" in story[0].text
    summary_table = story[1]
    summary_cells = " ".join(
        getattr(cell, "text", str(cell))
        for row in summary_table._cellvalues
        for cell in row
    )
    assert "Fechamento" in summary_cells
    assert "hml" in summary_cells
    assert "Nao" in summary_cells
    assert "Promover parametros canonicos para release." in summary_cells

    detail_table = story[2]
    detail_cells = " ".join(
        getattr(cell, "text", str(cell))
        for row in detail_table._cellvalues
        for cell in row
    )
    assert "51" in detail_cells
    assert "qa-smoke" in detail_cells
    assert "classificacao_nao_elegivel:qa-smoke" in detail_cells


def test_footer_story_includes_mode_request_correlation_and_versions():
    story = []
    financeiro_relatorios._footer_story(
        story,
        request_id="req-pdf-1",
        correlation_id="corr-pdf-1",
        calculation_version="finance-period-snapshot-v1",
        mode="previa",
    )

    assert len(story) == 2
    footer_text = story[1].text
    assert "mode=previa" in footer_text
    assert "request_id=req-pdf-1" in footer_text
    assert "correlation_id=corr-pdf-1" in footer_text
    assert "calculation_version=finance-period-snapshot-v1" in footer_text
    assert "report_version=finance-period-report-v1" in footer_text


def _tripulante_payload() -> dict:
    return {
        "id": 135,
        "nome": "Comandante QA",
        "cpf": "00000000000",
        "licenca_anac": "ANAC135",
        "funcao_operacional": "comandante",
    }


def test_relatorio_individual_horaria_filtra_vigentes_org_scope_e_audita(monkeypatch):
    db = _FakeDB()
    audit_calls = []
    rows = [
        {
            "id": 21,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-04",
            "missao_operacional_id": 10,
            "tripulante_id": 135,
            "tripulante_nome": "Comandante QA",
            "funcao": "comandante",
            "data_missao": "2026-04-10",
            "cavok_numero_voo": "QA-100",
            "trecho": "SDEA/SBSP",
            "aeronave_nome": "PT-QA",
            "chamado": "DB-1",
            "horario_apresentacao": "2026-04-10T08:00:00",
            "horario_abandono": "2026-04-10T11:00:00",
            "missao_status": "ativa",
            "jornada_total_minutos": 180,
            "minutos_diurnos": 120,
            "minutos_noturnos": 60,
            "horas_noturnas_convertidas": "1.1429",
            "minutos_pre": 15,
            "minutos_pos": 20,
            "domingo_feriado": False,
            "valor_adicional_noturno": "50.00",
            "valor_domingo_feriado_diurno": "0.00",
            "valor_domingo_feriado_noturno": "0.00",
            "valor_pre": "25.00",
            "valor_pos": "25.00",
            "total": "100.00",
            "status": "calculado",
            "parametros_usados": [{"tipo": "adicional_noturno", "valor": "50.00", "unidade": "valor"}],
            "memoria_calculo": {"warnings": []},
        },
        {
            "id": 22,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-04",
            "tripulante_id": 135,
            "funcao": "comandante",
            "data_missao": "2026-04-11",
            "missao_status": "ativa",
            "total": "999.00",
            "status": "obsoleto",
        },
        {
            "id": 23,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-04",
            "tripulante_id": 135,
            "funcao": "comandante",
            "data_missao": "2026-04-12",
            "missao_status": "cancelada",
            "total": "888.00",
            "status": "calculado",
        },
    ]
    calls = []
    monkeypatch.setattr(financeiro_relatorios, "fetch_tripulante_detail", lambda *_args, **_kwargs: _tripulante_payload())
    monkeypatch.setattr(financeiro_relatorios, "listar_calculos_horarios", lambda *args, **kwargs: calls.append(kwargs) or rows)
    monkeypatch.setattr(financeiro_relatorios, "record_audit_event", lambda *args, **kwargs: audit_calls.append(kwargs))

    result = financeiro_relatorios.gerar_relatorio_financeiro_individual_pdf(
        tipo="horaria",
        competencia="2026-04",
        tripulante_id=135,
        funcao="comandante",
        actor_user_id=501,
        request_id="req-ind-hourly",
        correlation_id="corr-ind-hourly",
        db=db,
    )

    assert result["content"].startswith(b"%PDF")
    assert result["filename"] == "relatorio-bonificacao-horaria-2026-04-comandante-qa.pdf"
    assert result["metadata"]["filters"]["tipo"] == "horaria"
    assert result["metadata"]["filters"]["incluir_obsoletos"] is False
    assert result["metadata"]["record_count"] == 1
    assert result["metadata"]["total_calculado"] == "100.00"
    assert calls[0]["org_id"] == FINANCE_ORG_SCOPE_DEFAULT
    assert calls[0]["tripulante_id"] == 135
    assert [call["acao"] for call in audit_calls] == [
        "finance.export.generated",
        "finance.report.individual.generated",
    ]
    assert audit_calls[0]["payload_novo"]["metadata"]["total_calculado"] == "100.00"
    assert audit_calls[1]["payload_novo"]["metadata"]["event_name"] == "finance.report.individual.generated"
    assert db.committed is True


def test_relatorio_individual_horaria_resumo_separa_noturno_reduzido_e_pos(monkeypatch):
    rows = [
        {
            "id": 41,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-04",
            "missao_operacional_id": 10,
            "tripulante_id": 135,
            "tripulante_nome": "Comandante QA",
            "funcao": "copiloto",
            "data_missao": "2026-04-10",
            "missao_status": "ativa",
            "jornada_total_minutos": 180,
            "minutos_diurnos": 110,
            "minutos_noturnos": 70,
            "horas_noturnas_convertidas": "3.3333",
            "minutos_pos": 105,
            "domingo_feriado": False,
            "valor_adicional_noturno": "61.57",
            "valor_domingo_feriado_diurno": "0.00",
            "valor_domingo_feriado_noturno": "0.00",
            "valor_pre": "0.00",
            "valor_pos": "92.36",
            "total": "153.93",
            "status": "calculado",
            "parametros_usados": [{"tipo": "duracao_hora_noturna_minutos", "valor": "52.5000"}],
            "memoria_calculo": {
                "totals": {
                    "normal_minutos_noturnos": 70,
                    "especial_minutos_noturnos": 0,
                },
                "steps": [
                    {
                        "rule_key": "pre_pos_jornada",
                        "resultado_intermediario": {
                            "normal_minutos_pos": 105,
                            "especial_minutos_pos": 0,
                        },
                    }
                ],
                "parameters": [{"tipo": "duracao_hora_noturna_minutos", "valor": "52.5000"}],
            },
        },
        {
            "id": 42,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-04",
            "missao_operacional_id": 11,
            "tripulante_id": 135,
            "tripulante_nome": "Comandante QA",
            "funcao": "copiloto",
            "data_missao": "2026-04-11",
            "missao_status": "ativa",
            "jornada_total_minutos": 225,
            "minutos_diurnos": 120,
            "minutos_noturnos": 105,
            "horas_noturnas_convertidas": "2.0000",
            "domingo_feriado": True,
            "valor_adicional_noturno": "0.00",
            "valor_domingo_feriado_diurno": "92.36",
            "valor_domingo_feriado_noturno": "184.72",
            "valor_pre": "0.00",
            "valor_pos": "0.00",
            "total": "277.08",
            "status": "calculado",
            "parametros_usados": [{"tipo": "duracao_hora_noturna_minutos", "valor": "52.5000"}],
            "memoria_calculo": {
                "totals": {
                    "normal_minutos_noturnos": 0,
                    "especial_minutos_noturnos": 105,
                },
                "parameters": [{"tipo": "duracao_hora_noturna_minutos", "valor": "52.5000"}],
            },
        },
    ]
    monkeypatch.setattr(financeiro_relatorios, "fetch_tripulante_detail", lambda *_args, **_kwargs: _tripulante_payload())
    monkeypatch.setattr(financeiro_relatorios, "listar_calculos_horarios", lambda *args, **kwargs: rows)

    data = financeiro_relatorios._hourly_report_data(
        object(),
        competencia="2026-04",
        tripulante_id=135,
        funcao="copiloto",
        status=None,
        incluir_obsoletos=False,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
    )

    assert data["totals"]["normal_minutos_noturnos"] == 70
    assert data["totals"]["normal_minutos_noturnos_reduzidos"] == 80
    assert data["totals"]["normal_minutos_pos"] == 105
    assert data["totals"]["normal_minutos_pos_reduzidos"] == 120
    assert data["totals"]["normal_minutos_noturnos_remuneraveis_reduzidos"] == 200
    assert data["totals"]["holiday_minutos_noturnos"] == 105
    assert data["totals"]["holiday_minutos_noturnos_reduzidos"] == 120
    assert data["totals"]["holiday_minutos_noturnos_remuneraveis_reduzidos"] == 120

    story = []
    financeiro_relatorios._final_summary_story(story, data, financeiro_relatorios._individual_styles())
    summary_text = " ".join(
        getattr(cell, "text", str(cell))
        for row in story[1]._cellvalues
        for cell in row
    )
    assert "POS" in summary_text
    assert "01:20" in summary_text
    assert "02:00" in summary_text
    assert "03:20" not in summary_text
    assert "01:10" not in summary_text
    assert "01:45" not in summary_text


def test_relatorio_horaria_preserva_memoria_de_corte_simples_para_linha_legada(monkeypatch):
    rows = [
        {
            "id": 51,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-05",
            "missao_operacional_id": 107,
            "tripulante_id": 135,
            "tripulante_nome": "Comandante QA",
            "funcao": "comandante",
            "data_missao": "2026-05-07",
            "missao_status": "ativa",
            "jornada_total_minutos": 680,
            "minutos_diurnos": 160,
            "minutos_noturnos": 520,
            "horas_noturnas_convertidas": "9.9048",
            "minutos_pre": 0,
            "minutos_pos": 110,
            "domingo_feriado": False,
            "valor_adicional_noturno": "990.48",
            "valor_domingo_feriado_diurno": "0.00",
            "valor_domingo_feriado_noturno": "0.00",
            "valor_pre": "0.00",
            "valor_pos": "209.52",
            "total": "1200.00",
            "status": "calculado",
            "parametros_usados": [{"tipo": "duracao_hora_noturna_minutos", "valor": "52.5"}],
            "memoria_calculo": {
                "inputs": {
                    "horario_apresentacao": "2026-05-07T23:00:00",
                    "horario_abandono": "2026-05-08T10:20:00",
                    "limite_jornada": "2026-05-08T08:30:00",
                    "limite_jornada_minutos": 570,
                },
                "steps": [
                    {
                        "rule_key": "pre_pos_jornada",
                        "resultado_intermediario": {
                            "normal_minutos_pre": 0,
                            "normal_minutos_pos": 110,
                            "especial_minutos_pre": 0,
                            "especial_minutos_pos": 0,
                        },
                    }
                ],
                "parameters": [{"tipo": "duracao_hora_noturna_minutos", "valor": "52.5"}],
            },
        }
    ]
    monkeypatch.setattr(financeiro_relatorios, "fetch_tripulante_detail", lambda *_args, **_kwargs: _tripulante_payload())
    monkeypatch.setattr(financeiro_relatorios, "listar_calculos_horarios", lambda *args, **kwargs: rows)

    data = financeiro_relatorios._hourly_report_data(
        object(),
        competencia="2026-05",
        tripulante_id=135,
        funcao="comandante",
        status=None,
        incluir_obsoletos=False,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
    )

    inputs = data["rows"][0]["memoria_calculo"]["inputs"]
    assert inputs.get("tipo_tripulacao_jornada", "simples") == "simples"
    assert inputs["limite_jornada"] == "2026-05-08T08:30:00"
    assert data["totals"]["normal_minutos_pos"] == 110
    assert data["totals"]["normal_minutos_pos_reduzidos"] == 126


def test_relatorio_individual_horaria_bloqueia_linha_sem_calculo_persistido(monkeypatch):
    db = _FakeDB()
    rows = [
        {
            "id": None,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-04",
            "missao_operacional_id": 10,
            "tripulante_id": 135,
            "tripulante_nome": "Comandante QA",
            "funcao": "comandante",
            "data_missao": "2026-04-10",
            "missao_status": "ativa",
            "total": "0.00",
            "status": "recalculo_pendente",
            "memoria_calculo": {"warnings": [{"code": "calculation_pending"}]},
        }
    ]
    monkeypatch.setattr(financeiro_relatorios, "fetch_tripulante_detail", lambda *_args, **_kwargs: _tripulante_payload())
    monkeypatch.setattr(financeiro_relatorios, "listar_calculos_horarios", lambda *args, **kwargs: rows)
    monkeypatch.setattr(financeiro_relatorios, "record_audit_event", lambda *args, **kwargs: None)

    with pytest.raises(DomainValidationError) as exc:
        financeiro_relatorios.gerar_relatorio_financeiro_individual_pdf(
            tipo="horaria",
            competencia="2026-04",
            tripulante_id=135,
            funcao="comandante",
            actor_user_id=501,
            db=db,
        )

    assert exc.value.code == "finance_hourly_unpersisted_lines"
    assert exc.value.status == 409
    assert db.committed is False


def test_relatorio_individual_produtividade_usa_calculo_persistido_e_missoes_ativas(monkeypatch):
    db = _FakeDB()
    audit_calls = []
    calculations = [
        {
            "id": 31,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-04",
            "tripulante_id": 135,
            "tripulante_nome": "Comandante QA",
            "funcao": "comandante",
            "categoria_aplicavel": "A",
            "valor_icao": "0.00",
            "valor_instrutor": "0.00",
            "valor_checador": "0.00",
            "valor_missoes_categoria_a": "500.00",
            "valor_missoes_categoria_b": "0.00",
            "valor_cobertura_base": "0.00",
            "valor_pernoite_comum": "0.00",
            "valor_excecao_palmas": "0.00",
            "produtividade_calculada": "500.00",
            "garantia_minima": "3000.00",
            "total_devido": "3000.00",
            "status": "calculado",
            "parametros_usados": [{"tipo": "garantia_minima", "valor": "3000.00", "unidade": "valor"}],
            "memoria_calculo": {"inputs": {"contagens_agregadas": {"categoria_a": 1}}},
        }
    ]
    missions = [
        {
            "missao_operacional_id": 10,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-04",
            "tripulante_id": 135,
            "tripulante_nome": "Comandante QA",
            "funcao": "comandante",
            "data_missao": "2026-04-10",
            "cavok_numero_voo": "QA-100",
            "trecho": "SDEA/SBSP",
            "aeronave_nome": "PT-QA",
            "categoria_financeira_aeronave": "A",
            "cobertura_base": False,
            "operacao_especial": "",
            "missao_status": "ativa",
        }
    ]
    monkeypatch.setattr(financeiro_relatorios, "fetch_tripulante_detail", lambda *_args, **_kwargs: _tripulante_payload())
    monkeypatch.setattr(financeiro_relatorios, "listar_calculos_produtividade", lambda *args, **kwargs: calculations)
    monkeypatch.setattr(financeiro_relatorios, "listar_participacoes_produtividade_por_competencia", lambda *args, **kwargs: missions)
    monkeypatch.setattr(financeiro_relatorios, "record_audit_event", lambda *args, **kwargs: audit_calls.append(kwargs))

    result = financeiro_relatorios.gerar_relatorio_financeiro_individual_pdf(
        tipo="produtividade",
        competencia="2026-04",
        tripulante_id=135,
        funcao="comandante",
        actor_user_id=501,
        request_id="req-ind-prod",
        correlation_id="corr-ind-prod",
        db=db,
    )

    assert result["content"].startswith(b"%PDF")
    assert result["filename"] == "relatorio-produtividade-2026-04-comandante-qa.pdf"
    assert result["metadata"]["filters"]["tipo"] == "produtividade"
    assert result["metadata"]["record_count"] == 1
    assert result["metadata"]["total_calculado"] == "3000.00"
    assert [call["acao"] for call in audit_calls] == [
        "finance.export.generated",
        "finance.report.individual.generated",
    ]
    assert audit_calls[0]["payload_novo"]["metadata"]["record_count"] == 1
    assert audit_calls[0]["payload_novo"]["metadata"]["total_calculado"] == "3000.00"
    assert audit_calls[1]["payload_novo"]["metadata"]["event_name"] == "finance.report.individual.generated"
    assert db.committed is True


def test_relatorio_individual_produtividade_preserva_funcao_resolvida_para_agnello(
    monkeypatch,
):
    tripulante_nome = "Rafael Leao Agnello"
    calculation = {
        "id": 31,
        "org_id": FINANCE_ORG_SCOPE_DEFAULT,
        "competencia": "2026-04",
        "tripulante_id": 135,
        "tripulante_nome": tripulante_nome,
        "funcao": "comandante",
        "produtividade_calculada": "500.00",
        "garantia_minima": "3000.00",
        "total_devido": "3000.00",
        "status": "calculado",
        "parametros_usados": [],
        "memoria_calculo": {},
    }
    mission = {
        "missao_operacional_id": 10,
        "org_id": FINANCE_ORG_SCOPE_DEFAULT,
        "competencia": "2026-04",
        "tripulante_id": 135,
        "tripulante_nome": tripulante_nome,
        "funcao": "comandante",
        "missao_status": "ativa",
    }
    calculation_calls = []
    mission_calls = []

    tripulante = _tripulante_payload()
    tripulante["nome"] = tripulante_nome
    monkeypatch.setattr(financeiro_relatorios, "fetch_tripulante_detail", lambda *_args, **_kwargs: tripulante)

    def _calculations(*args, **kwargs):
        calculation_calls.append(kwargs)
        return [calculation] if kwargs.get("funcao") == "comandante" else []

    monkeypatch.setattr(financeiro_relatorios, "listar_calculos_produtividade", _calculations)

    def _missions(*args, **kwargs):
        mission_calls.append(kwargs)
        return [mission]

    monkeypatch.setattr(financeiro_relatorios, "listar_participacoes_produtividade_por_competencia", _missions)

    data = financeiro_relatorios._productivity_report_data(
        object(),
        competencia="2026-04",
        tripulante_id=135,
        funcao="comandante",
        status=None,
        incluir_obsoletos=False,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
    )

    assert calculation_calls[0]["funcao"] == "comandante"
    assert mission_calls[0]["funcao"] is None
    assert data["funcao"] == "comandante"
    assert data["totals"]["missions"] == 1
    assert data["missions"][0]["funcao"] == "comandante"


@pytest.mark.parametrize("tripulante_nome", ["Andre Affonso Abdalla", "Paulo Abdala"])
def test_relatorio_individual_produtividade_mantem_abdalla_como_copiloto(
    monkeypatch,
    tripulante_nome,
):
    calculation = {
        "id": 31,
        "org_id": FINANCE_ORG_SCOPE_DEFAULT,
        "competencia": "2026-04",
        "tripulante_id": 135,
        "tripulante_nome": tripulante_nome,
        "funcao": "copiloto",
        "produtividade_calculada": "500.00",
        "garantia_minima": "3000.00",
        "total_devido": "3000.00",
        "status": "calculado",
        "parametros_usados": [],
        "memoria_calculo": {},
    }
    mission = {
        "missao_operacional_id": 10,
        "org_id": FINANCE_ORG_SCOPE_DEFAULT,
        "competencia": "2026-04",
        "tripulante_id": 135,
        "tripulante_nome": tripulante_nome,
        "funcao": "comandante",
        "missao_status": "ativa",
    }
    calculation_calls = []
    mission_calls = []

    tripulante = _tripulante_payload()
    tripulante["nome"] = tripulante_nome
    monkeypatch.setattr(financeiro_relatorios, "fetch_tripulante_detail", lambda *_args, **_kwargs: tripulante)

    def _calculations(*args, **kwargs):
        calculation_calls.append(kwargs)
        return [calculation] if kwargs.get("funcao") == "copiloto" else []

    monkeypatch.setattr(financeiro_relatorios, "listar_calculos_produtividade", _calculations)

    def _missions(*args, **kwargs):
        mission_calls.append(kwargs)
        return [mission]

    monkeypatch.setattr(financeiro_relatorios, "listar_participacoes_produtividade_por_competencia", _missions)

    data = financeiro_relatorios._productivity_report_data(
        object(),
        competencia="2026-04",
        tripulante_id=135,
        funcao="comandante",
        status=None,
        incluir_obsoletos=False,
        org_id=FINANCE_ORG_SCOPE_DEFAULT,
    )

    assert calculation_calls[0]["funcao"] == "copiloto"
    assert mission_calls[0]["funcao"] is None
    assert data["funcao"] == "copiloto"
    assert data["totals"]["missions"] == 1
    assert data["missions"][0]["funcao"] == "copiloto"


def test_relatorio_individual_produtividade_soma_recalculo_pendente_com_total_persistido(monkeypatch):
    db = _FakeDB()
    calculations = [
        {
            "id": 82,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-05",
            "tripulante_id": 135,
            "tripulante_nome": "Comandante QA",
            "funcao": "copiloto",
            "categoria_aplicavel": "categoria b",
            "valor_icao": "150.00",
            "valor_instrutor": "0.00",
            "valor_checador": "0.00",
            "valor_missoes_categoria_a": "0.00",
            "valor_missoes_categoria_b": "2850.00",
            "valor_cobertura_base": "0.00",
            "valor_pernoite_comum": "0.00",
            "valor_excecao_palmas": "0.00",
            "produtividade_calculada": "2850.00",
            "garantia_minima": "3000.00",
            "total_devido": "3000.00",
            "status": "recalculo_pendente",
            "parametros_usados": [{"tipo": "garantia_minima", "valor": "3000.00", "unidade": "valor"}],
            "memoria_calculo": {
                "warnings": [{"code": "pernoite_comum_parametro_ausente"}],
                "inputs": {
                    "contagens_agregadas": {
                        "categoria_b": 9,
                        "pernoite_comum_sem_cobertura": 14,
                    }
                },
            },
        }
    ]
    missions = [
        {
            "missao_operacional_id": 10,
            "org_id": FINANCE_ORG_SCOPE_DEFAULT,
            "competencia": "2026-05",
            "tripulante_id": 135,
            "tripulante_nome": "Comandante QA",
            "funcao": "copiloto",
            "data_missao": "2026-05-10",
            "cavok_numero_voo": "QA-100",
            "trecho": "SDEA/SBSP",
            "aeronave_nome": "PT-QA",
            "categoria_financeira_aeronave": "B",
            "quantidade_pernoites": 3,
            "cobertura_base": False,
            "operacao_especial": "",
            "missao_status": "ativa",
        }
    ]
    monkeypatch.setattr(financeiro_relatorios, "fetch_tripulante_detail", lambda *_args, **_kwargs: _tripulante_payload())
    monkeypatch.setattr(financeiro_relatorios, "listar_calculos_produtividade", lambda *args, **kwargs: calculations)
    monkeypatch.setattr(financeiro_relatorios, "listar_participacoes_produtividade_por_competencia", lambda *args, **kwargs: missions)
    monkeypatch.setattr(financeiro_relatorios, "record_audit_event", lambda *args, **kwargs: None)

    result = financeiro_relatorios.gerar_relatorio_financeiro_individual_pdf(
        tipo="produtividade",
        competencia="2026-05",
        tripulante_id=135,
        funcao="copiloto",
        actor_user_id=501,
        request_id="req-ind-prod-pending",
        correlation_id="corr-ind-prod-pending",
        db=db,
    )

    assert result["content"].startswith(b"%PDF")
    assert result["metadata"]["record_count"] == 1
    assert result["metadata"]["total_calculado"] == "3000.00"


def test_relatorio_produtividade_expoe_pernoite_comum_sem_cobertura_parametrizado():
    calculation = {
        "valor_pernoite_comum": "90.00",
        "memoria_calculo": {
            "inputs": {
                "contagens_agregadas": {
                    "pernoite_comum_sem_cobertura": 2,
                }
            }
        },
    }
    mission = {
        "quantidade_pernoites": 3,
        "cobertura_base": False,
        "categoria_financeira_aeronave": "A",
    }

    rule = financeiro_relatorios._productivity_rule_for_mission(calculation, mission)

    assert rule["key"] == "pernoite_comum_sem_cobertura"
    assert rule["quantity"] == 2
    assert rule["unit_value"] == Decimal("45.00")
    assert rule["total_value"] == Decimal("90.00")


def test_relatorio_produtividade_reconhece_palmas_legada_no_detalhe_da_missao():
    calculation = {
        "valor_excecao_palmas": "5000.00",
        "valor_missoes_categoria_a": "0.00",
        "memoria_calculo": {
            "inputs": {
                "contagens_agregadas": {
                    "excecao_palmas_turbohelice": 1,
                    "categoria_a": 0,
                }
            }
        },
    }
    mission = {
        "categoria_financeira_aeronave": "nao_aplicavel",
        "operacao_especial": "PALMAS",
        "quantidade_pernoites": 0,
        "cobertura_base": False,
    }

    rule = financeiro_relatorios._productivity_rule_for_mission(calculation, mission)

    assert rule["key"] == "excecao_palmas_turbohelice"
    assert rule["unit_value"] == Decimal("5000.00")
    assert rule["total_value"] == Decimal("5000.00")


def test_relatorio_produtividade_nao_repete_valor_do_piso_palmas_por_missao():
    calculation = {
        "valor_excecao_palmas": "5000.00",
        "memoria_calculo": {
            "inputs": {
                "contagens_agregadas": {
                    "excecao_palmas_turbohelice": 1,
                }
            }
        },
    }
    mission = {
        "categoria_financeira_aeronave": "nao_aplicavel",
        "operacao_especial": "PALMAS",
        "quantidade_pernoites": 0,
        "cobertura_base": False,
    }

    rule = financeiro_relatorios._productivity_rule_for_mission(
        calculation,
        mission,
        palmas_floor_consumed=True,
    )

    assert rule["key"] == "excecao_palmas_turbohelice"
    assert rule["quantity"] == 0
    assert rule["total_value"] == Decimal("0.00")


def test_relatorio_produtividade_detalha_todos_parametros_aplicados():
    calculation = {
        "funcao": "comandante",
        "valor_icao": "300.00",
        "valor_instrutor": "300.00",
        "valor_checador": "300.00",
        "valor_missoes_categoria_a": "600.00",
        "valor_missoes_categoria_b": "600.00",
        "valor_cobertura_base": "400.00",
        "valor_pernoite_comum": "160.00",
        "valor_excecao_palmas": "5000.00",
        "produtividade_calculada": "7660.00",
        "garantia_minima": "3000.00",
        "excedente": "4660.00",
        "total_devido": "7660.00",
        "parametros_usados": [
            {"tipo": "icao_sdea", "funcao": "comandante", "valor": "300.00"},
            {"tipo": "instrutor", "valor": "300.00"},
            {"tipo": "checador", "valor": "300.00"},
            {"tipo": "missao_categoria_a", "funcao": "comandante", "categoria": "A", "valor": "300.00"},
            {"tipo": "missao_categoria_b", "funcao": "comandante", "categoria": "B", "valor": "600.00"},
            {"tipo": "cobertura_base", "funcao": "comandante", "valor": "200.00"},
            {"tipo": "pernoite_comum_sem_cobertura", "funcao": "comandante", "valor": "80.00"},
            {"tipo": "excecao_palmas_turbohelice", "funcao": "comandante", "categoria": "PALMAS_TURBOHELICE", "valor": "5000.00"},
            {"tipo": "garantia_minima", "funcao": "comandante", "categoria": "A", "valor": "3000.00"},
        ],
        "memoria_calculo": {
            "inputs": {
                "contagens_agregadas": {
                    "categoria_a": 2,
                    "categoria_b": 1,
                    "cobertura_base": 2,
                    "pernoite_comum_sem_cobertura": 2,
                    "excecao_palmas_turbohelice": 1,
                }
            }
        },
    }
    data = {
        "tipo": "produtividade",
        "funcao": "comandante",
        "rows": [calculation],
        "payable_rows": [calculation],
        "parameters": calculation["parametros_usados"],
        "totals": {
            "produtividade_calculada": Decimal("7660.00"),
            "garantia_minima": Decimal("3000.00"),
            "excedente": Decimal("4660.00"),
            "total": Decimal("7660.00"),
        },
    }

    breakdown = financeiro_relatorios._productivity_parameter_breakdown(data)
    by_item = {item["item"]: item for item in breakdown}

    assert by_item["ICAO/SDEA"]["calculo"] == "1 x R$ 300,00"
    assert by_item["Instrutor"]["valor_total"] == Decimal("300.00")
    assert by_item["Checador"]["valor_total"] == Decimal("300.00")
    assert by_item["Missoes Categoria A"]["calculo"] == "2 x R$ 300,00"
    assert by_item["Missoes Categoria B"]["calculo"] == "1 x R$ 600,00"
    assert by_item["Cobertura de base"]["calculo"] == "2 x R$ 200,00"
    assert by_item["Pernoite comum sem cobertura"]["calculo"] == "2 x R$ 80,00"
    assert by_item["Palmas turbo-helice"]["calculo"] == "1 x R$ 5.000,00"
    assert by_item["Garantia minima"]["valor_total"] == Decimal("3000.00")
    assert by_item["Excedente"]["valor_total"] == Decimal("4660.00")
    assert by_item["Total a pagar"]["valor_total"] == Decimal("7660.00")


def test_relatorio_produtividade_detalha_piso_palmas_com_sdea_embutido():
    calculation = {
        "funcao": "copiloto",
        "valor_icao": "150.00",
        "valor_instrutor": "0.00",
        "valor_checador": "0.00",
        "valor_missoes_categoria_a": "0.00",
        "valor_missoes_categoria_b": "0.00",
        "valor_cobertura_base": "0.00",
        "valor_pernoite_comum": "0.00",
        "valor_excecao_palmas": "2350.00",
        "produtividade_calculada": "2500.00",
        "garantia_minima": "0.00",
        "excedente": "2500.00",
        "total_devido": "2500.00",
        "parametros_usados": [
            {"tipo": "icao_sdea", "funcao": "copiloto", "valor": "150.00"},
            {
                "tipo": "excecao_palmas_turbohelice",
                "funcao": "copiloto",
                "categoria": "PALMAS_TURBOHELICE",
                "valor": "2500.00",
            },
        ],
        "memoria_calculo": {
            "inputs": {
                "contagens_agregadas": {
                    "excecao_palmas_turbohelice": 1,
                }
            },
            "totals": {
                "piso_palmas_integral": "2500.00",
                "produtividade_sem_piso_palmas": "150.00",
            },
        },
    }
    data = {
        "tipo": "produtividade",
        "funcao": "copiloto",
        "rows": [calculation],
        "payable_rows": [calculation],
        "parameters": calculation["parametros_usados"],
        "totals": {
            "produtividade_calculada": Decimal("2500.00"),
            "garantia_minima": Decimal("0.00"),
            "excedente": Decimal("2500.00"),
            "total": Decimal("2500.00"),
        },
    }

    breakdown = financeiro_relatorios._productivity_parameter_breakdown(data)
    by_item = {item["item"]: item for item in breakdown}

    assert by_item["ICAO/SDEA"]["valor_total"] == Decimal("150.00")
    assert by_item["Palmas turbo-helice"]["valor_total"] == Decimal("2350.00")
    assert by_item["Palmas turbo-helice"]["calculo"] == "max(R$ 2.500,00 - R$ 150,00, 0)"
    assert by_item["Total a pagar"]["valor_total"] == Decimal("2500.00")
