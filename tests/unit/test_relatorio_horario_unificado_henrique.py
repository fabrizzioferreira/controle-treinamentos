from decimal import Decimal
import pytest

from backend.src.controle_treinamentos.application import financeiro_relatorios as reports
from backend.src.controle_treinamentos.contracts.financeiro import FINANCE_ORG_SCOPE_DEFAULT


def row(identifier, role, amount, **overrides):
    result = {
        "id": identifier, "tripulante_id": 38, "funcao": role,
        "data_missao": f"2026-09-{23 + identifier:02d}", "missao_status": "ativa",
        "tripulante_nome": "Henrique Rodrigues Raggiotto", "status": "calculado",
        "total": amount, "valor_adicional_noturno": amount,
        "minutos_diurnos": 60, "minutos_noturnos": 30, "jornada_total_minutos": 90,
        "horas_noturnas_convertidas": "0.5714", "parametros_usados": [],
        "memoria_calculo": {}, "aeronave_nome": "KING AIR 200-B200" if role == "comandante" else "GULFSTREAM G100",
    }
    result.update(overrides)
    return result


class DB:
    def commit(self):
        pass


def fixtures(monkeypatch, rows):
    calls = []
    def query(db, **kwargs):
        calls.append(kwargs)
        return [item for item in rows if not kwargs.get("funcao") or item["funcao"] == kwargs["funcao"]]
    monkeypatch.setattr(reports, "listar_calculos_horarios", query)
    monkeypatch.setattr(reports, "fetch_tripulante_detail", lambda db, **kwargs: {
        "id": kwargs["tripulante_id"], "nome": "Henrique Rodrigues Raggiotto", "funcao_operacional": "copiloto"
    })
    monkeypatch.setattr(reports, "record_audit_event", lambda *args, **kwargs: None)
    return calls


@pytest.mark.parametrize("selected_role", ["copiloto", "comandante", None])
def test_same_monthly_pdf_includes_both_roles_and_exact_total(monkeypatch, selected_role):
    calls = fixtures(monkeypatch, [row(1, "comandante", "100.25"), row(2, "copiloto", "200.50"),
                                   row(3, "comandante", "900.00", status="obsoleto"),
                                   row(4, "copiloto", "800.00", missao_status="cancelada")])
    built_data = []
    build_pdf = reports._build_individual_pdf
    def capture_pdf(**kwargs):
        built_data.append(kwargs["data"])
        return build_pdf(**kwargs)
    monkeypatch.setattr(reports, "_build_individual_pdf", capture_pdf)
    result = reports.gerar_relatorio_financeiro_individual_pdf(
        tipo="horaria", competencia="2026-09", tripulante_id=38, funcao=selected_role, db=DB()
    )
    assert calls[0]["funcao"] is None
    assert calls[0]["tripulante_id"] == 38
    assert calls[0]["org_id"] == FINANCE_ORG_SCOPE_DEFAULT
    assert result["metadata"]["filters"]["funcao"] is None
    assert result["metadata"]["record_count"] == 2
    assert Decimal(result["metadata"]["total_calculado"]) == Decimal("300.75")
    assert result["content"].startswith(b"%PDF")
    assert built_data[0]["funcao"] == "comandante / copiloto"
    assert {item["aeronave_nome"] for item in built_data[0]["rows"]} == {"KING AIR 200-B200", "GULFSTREAM G100"}


def test_role_subtotals_sum_to_combined_report(monkeypatch):
    fixtures(monkeypatch, [row(1, "comandante", "100.25"), row(2, "copiloto", "200.50")])
    data = reports._hourly_report_data(DB(), competencia="2026-09", tripulante_id=38, funcao=None,
                                      status=None, incluir_obsoletos=False, org_id=FINANCE_ORG_SCOPE_DEFAULT)
    assert [s["funcao"] for s in data["subtotais_funcoes"]] == ["comandante", "copiloto"]
    assert sum(s["total"] for s in data["subtotais_funcoes"]) == data["totals"]["total"]
    assert sum(s["rows"] for s in data["subtotais_funcoes"]) == data["totals"]["rows"]
    story = []
    reports._subtotals_story(story, data, reports._individual_styles())
    assert len(story[1]._cellvalues) == 3


def test_other_crew_keep_requested_role_filter(monkeypatch):
    calls = fixtures(monkeypatch, [row(1, "comandante", "100.25"), row(2, "copiloto", "200.50")])
    result = reports.gerar_relatorio_financeiro_individual_pdf(
        tipo="horaria", competencia="2026-09", tripulante_id=25, funcao="copiloto", db=DB()
    )
    assert calls[0]["funcao"] == "copiloto"
    assert result["metadata"]["record_count"] == 1


def test_productivity_role_not_changed(monkeypatch):
    captured = []
    class StopAfterQuery(Exception):
        pass
    def productivity(*args, **kwargs):
        captured.append(kwargs)
        raise StopAfterQuery()
    monkeypatch.setattr(reports, "_productivity_report_data", productivity)
    with pytest.raises(StopAfterQuery):
        reports.gerar_relatorio_financeiro_individual_pdf(
            tipo="produtividade", competencia="2026-09", tripulante_id=38, funcao="copiloto", db=DB()
        )
    assert captured[0]["funcao"] == "copiloto"


def test_missing_calculation_in_either_role_still_blocks_pdf(monkeypatch):
    fixtures(monkeypatch, [row(1, "comandante", "100.25", id=None, status="recalculo_pendente"), row(2, "copiloto", "200.50")])
    with pytest.raises(reports.DomainValidationError):
        reports.gerar_relatorio_financeiro_individual_pdf(
            tipo="horaria", competencia="2026-09", tripulante_id=38, funcao="copiloto", db=DB()
        )
