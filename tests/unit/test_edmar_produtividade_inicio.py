from decimal import Decimal

import pytest

from backend.src.controle_treinamentos.application.financeiro_bonificacao_produtividade import calcular_bonificacao_produtividade
from backend.src.controle_treinamentos.application import financeiro_produtividade_relatorio_geral as report
from test_financeiro_bonificacao_produtividade_engine import _params, _tripulante, _mission
from test_financeiro_produtividade_relatorio_geral import _consolidar, _row


def calculate(*, month="2026-09", role="comandante", crew=None, missions=(), parameters=None):
    return calcular_bonificacao_produtividade(
        competencia=month, funcao=role,
        tripulante=_tripulante(id=26, nome="Edmar Pinto Fiuza", **(crew or {})),
        missoes_operacionais=missions, parametros_vigentes=parameters or _params(),
    )


def test_first_month_pays_six_days_and_preserves_auditable_formula():
    result = calculate()
    assert result["garantia_minima"] == result["total_devido"] == Decimal("600.00")
    context = result["memoria_calculo"]["inputs"]["proporcionalidade_inicio_produtividade"]
    assert context == {"data_inicio": "2026-09-25", "dias_competencia": 30, "dias_vigencia": 6,
                       "dias_ferias_na_vigencia": 0, "dias_remunerados": 6}
    step = next(s for s in result["memoria_calculo"]["steps"] if s["rule_key"] == "garantia_inicio_produtividade")
    assert step["resultado_final"]["garantia_minima"] == "600.00"
    assert step["resultado_intermediario"]["garantia_mensal"] == "3000.00"


@pytest.mark.parametrize("month", ["2026-10", "2027-09"])
def test_later_months_retain_full_monthly_floor(month):
    result = calculate(month=month)
    assert result["garantia_minima"] == Decimal("3000.00")
    assert "proporcionalidade_inicio_produtividade" not in result["memoria_calculo"]["inputs"]


@pytest.mark.parametrize("start,end,expected", [("2026-09-01","2026-09-24","600.00"),
    ("2026-09-25","2026-09-26","400.00"),("2026-09-01","2026-09-30","0.00")])
def test_vacation_reduces_only_days_overlapping_eligibility(start,end,expected):
    result = calculate(crew={"periodos_operacionais":[{"tipo":"ferias","data_inicio":start,"data_fim":end}]})
    assert result["garantia_minima"] == Decimal(expected)


def test_productivity_above_prorated_floor_is_preserved():
    result = calculate(missions=[_mission(id=i,data_missao="2026-09-25",cavok_numero_voo=str(i)) for i in (10,11,12)])
    assert result["produtividade_calculada"] == result["total_devido"] == Decimal("900.00")
    assert result["garantia_minima"] == Decimal("600.00")


def test_uses_monthly_parameter_without_hardcoded_amount():
    assert calculate(parameters=_params(garantia_minima="4500"))["garantia_minima"] == Decimal("900.00")


@pytest.mark.parametrize("crew,role,expected", [({"id":27,"nome":"Edmar Pinto Fiuza"},"comandante","3000"),
    ({"id":26,"nome":"Outro Tripulante"},"comandante","3000"),
    ({"id":26,"nome":"Edmar Pinto Fiuza","categoria_operacional":"B"},"comandante","6000"),
    ({"id":26,"nome":"Edmar Pinto Fiuza","categoria_operacional":"N/A"},"comandante","0"),
    ({"id":26,"nome":"Edmar Pinto Fiuza"},"copiloto","1500")])
def test_rule_does_not_affect_other_id_identity_category_or_role(crew,role,expected):
    result = calcular_bonificacao_produtividade(competencia="2026-09",funcao=role,tripulante=_tripulante(**crew),missoes_operacionais=[],parametros_vigentes=_params())
    assert result["garantia_minima"] == Decimal(expected)
    assert "proporcionalidade_inicio_produtividade" not in result["memoria_calculo"]["inputs"]


def test_general_report_includes_persisted_effective_category_without_changing_registration(monkeypatch):
    result = calculate()
    row = _row(**result,tripulante_nome="Edmar Pinto Fiuza",tripulante_categoria_operacional="N/A")
    assert report._display_category(row) == "A"
    actual,_ = _consolidar(monkeypatch,[row],categoria="A")
    assert len(actual["items"]) == 1
    assert actual["items"][0]["total_produtividade"] == "600.00"


def test_prior_ineligible_report_remains_excluded():
    assert not report._is_default_report_eligible(_row(tripulante_categoria_operacional="N/A",categoria_aplicavel="nao_aplicavel",valor_excecao_palmas="0",memoria_calculo={"inputs":{"categoria_garantia_minima":None}}))
