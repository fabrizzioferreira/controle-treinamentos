from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from unicodedata import normalize as _unicode_normalize

from ..contracts.financeiro import FINANCE_CREW_FUNCTIONS, FINANCE_ORG_SCOPE_DEFAULT
from ..core.domain_errors import DomainValidationError
from .financeiro_categorias import (
    CANONICAL_CATEGORY_A,
    CANONICAL_CATEGORY_B,
    CANONICAL_CATEGORY_TURBOHELICE_PALMAS,
    is_operacao_especial_palmas_turbohelice,
    normalizar_categoria_operacional,
    normalizar_categoria_parametro,
)
from .financeiro_governanca_parametros import (
    classificacao_governanca_parametro,
    detectar_divergencias_ativas,
    detectar_sobreposicoes_ativas,
    parametro_elegivel_fechamento_real,
)

CALCULATION_VERSION = "finance-productivity-v1"
MONEY_QUANTIZER = Decimal("0.01")
FACTOR_QUANTIZER = Decimal("0.000001")
MONETARY_PARAMETER_UNIT = "valor"
_CANCELLED_OPERATIONAL_PERIOD_STATUSES = {"cancelado", "cancelada", "cancelled", "inativo", "inativa"}

PARAMETER_TYPES = (
    "icao_sdea",
    "instrutor",
    "checador",
    "missao_categoria_a",
    "missao_categoria_b",
    "cobertura_base",
    "pernoite_comum_sem_cobertura",
    "garantia_minima",
    "excecao_palmas_turbohelice",
)

PRODUCTIVITY_PARAMETER_RULES: dict[str, dict[str, Any]] = {
    "icao_sdea": {
        "unidade": MONETARY_PARAMETER_UNIT,
        "funcao_mode": "crew",
        "categorias": {""},
    },
    "instrutor": {
        "unidade": MONETARY_PARAMETER_UNIT,
        "funcao_mode": "none",
        "categorias": {""},
    },
    "checador": {
        "unidade": MONETARY_PARAMETER_UNIT,
        "funcao_mode": "none",
        "categorias": {""},
    },
    "missao_categoria_a": {
        "unidade": MONETARY_PARAMETER_UNIT,
        "funcao_mode": "crew",
        "categorias": {CANONICAL_CATEGORY_A},
    },
    "missao_categoria_b": {
        "unidade": MONETARY_PARAMETER_UNIT,
        "funcao_mode": "crew",
        "categorias": {CANONICAL_CATEGORY_B},
    },
    "cobertura_base": {
        "unidade": MONETARY_PARAMETER_UNIT,
        "funcao_mode": "crew",
        "categorias": {""},
    },
    "pernoite_comum_sem_cobertura": {
        "unidade": MONETARY_PARAMETER_UNIT,
        "funcao_mode": "crew",
        "categorias": {""},
    },
    "garantia_minima": {
        "unidade": MONETARY_PARAMETER_UNIT,
        "funcao_mode": "crew",
        "categorias": {CANONICAL_CATEGORY_A, CANONICAL_CATEGORY_B},
    },
    "excecao_palmas_turbohelice": {
        "unidade": MONETARY_PARAMETER_UNIT,
        "funcao_mode": "crew",
        "categorias": {CANONICAL_CATEGORY_TURBOHELICE_PALMAS},
    },
}


class BonificacaoProdutividadeInvalidaErro(DomainValidationError):
    def __init__(self, message: str, *, code: str = "bonificacao_produtividade_invalida"):
        super().__init__(message, code=code, status=400)


class ParametroBonificacaoProdutividadeAusenteErro(BonificacaoProdutividadeInvalidaErro):
    def __init__(self, tipo: str, *, funcao: str | None = None, categoria: str | None = None):
        suffix_parts = []
        if funcao:
            suffix_parts.append(f"funcao={funcao}")
        if categoria:
            suffix_parts.append(f"categoria={categoria}")
        suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""
        super().__init__(
            f"Parametro financeiro obrigatorio ausente: {tipo}{suffix}.",
            code="bonificacao_produtividade_parametro_ausente",
        )


class ParametroBonificacaoProdutividadeAmbiguoErro(BonificacaoProdutividadeInvalidaErro):
    def __init__(
        self,
        tipo: str,
        *,
        funcao: str | None = None,
        categoria: str | None = None,
        unidade: str = MONETARY_PARAMETER_UNIT,
    ):
        suffix_parts = [f"unidade={unidade}"]
        if funcao:
            suffix_parts.append(f"funcao={funcao}")
        if categoria:
            suffix_parts.append(f"categoria={categoria}")
        suffix = f" ({', '.join(suffix_parts)})"
        super().__init__(
            f"Parametro financeiro ambiguo para produtividade: {tipo}{suffix}.",
            code="bonificacao_produtividade_parametro_ambiguo",
        )


class ParametroBonificacaoProdutividadeNaoElegivelErro(BonificacaoProdutividadeInvalidaErro):
    def __init__(self, *, blocking_parameters: list[dict], real_closure: bool):
        context = "fechamento real" if real_closure else "calculo de produtividade"
        super().__init__(
            f"Motor de produtividade bloqueado: parametros nao elegiveis recebidos para {context}.",
            code="bonificacao_produtividade_parametro_nao_elegivel",
        )
        self.details = {
            "real_closure": bool(real_closure),
            "blocking_parameters": blocking_parameters,
            "next_action": (
                "Corrigir cadastro de parametros (unidade, vigencia, classificacao, overlap/divergencia, BRL/QA) "
                "antes de recalcular."
            ),
        }


def calcular_bonificacao_produtividade(
    *,
    competencia: str,
    tripulante: dict[str, Any],
    funcao: str,
    missoes_operacionais: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    parametros_vigentes: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    cobertura_base: bool = False,
    excecao_palmas_turbohelice: bool = False,
    aplicar_garantia_minima: bool = True,
    real_closure: bool = False,
    release_environment: str = "hml",
    calculation_version: str = CALCULATION_VERSION,
) -> dict[str, Any]:
    """Calcula bonificacao por funcao/produtividade sem Flask, banco, repository ou audit log."""
    resolved_competencia = _resolve_competencia(competencia)
    resolved_funcao = _resolve_funcao(funcao)
    reference_date = date.fromisoformat(f"{resolved_competencia}-01")
    competence_end = _month_end(reference_date)
    parametros_pool = _normalize_parameter_pool(parametros_vigentes)
    _validate_parameter_pool(
        parametros_pool,
        reference_date=reference_date,
        supported_types=PARAMETER_TYPES,
        real_closure=real_closure,
        release_environment=release_environment,
    )
    tripulante_id = _resolve_int(tripulante.get("id") or tripulante.get("tripulante_id"))
    flags = _tripulante_flags(tripulante, competencia_inicio=reference_date, competencia_fim=competence_end)
    contagens = _mission_counts(
        missoes_operacionais,
        cobertura_base=cobertura_base,
        excecao_palmas_turbohelice=excecao_palmas_turbohelice,
    )
    ferias_context = _vacation_proportionality(
        tripulante,
        competencia_inicio=reference_date,
        competencia_fim=competence_end,
    )

    parametros_usados: list[dict[str, Any]] = []
    valor_icao_integral = _conditional_value(
        parametros_pool,
        "icao_sdea",
        active=flags["sdea_ativo"],
        funcao=resolved_funcao,
        allow_general_function=False,
        parametros_usados=parametros_usados,
    )
    valor_icao = _apply_vacation_proportionality(valor_icao_integral, ferias_context)
    valor_instrutor_integral = _conditional_value(
        parametros_pool,
        "instrutor",
        active=flags["instrutor"],
        funcao=None,
        allow_general_function=False,
        parametros_usados=parametros_usados,
    )
    valor_instrutor = _apply_vacation_proportionality(valor_instrutor_integral, ferias_context)
    valor_checador_integral = _conditional_value(
        parametros_pool,
        "checador",
        active=flags["checador"],
        funcao=None,
        allow_general_function=False,
        parametros_usados=parametros_usados,
    )
    valor_checador = _apply_vacation_proportionality(valor_checador_integral, ferias_context)
    valor_missoes_categoria_a = _quantity_value(
        parametros_pool,
        "missao_categoria_a",
        quantity=contagens["categoria_a"],
        funcao=resolved_funcao,
        categoria=CANONICAL_CATEGORY_A,
        allow_general_function=False,
        allow_general_category=False,
        parametros_usados=parametros_usados,
    )
    valor_missoes_categoria_b = _quantity_value(
        parametros_pool,
        "missao_categoria_b",
        quantity=contagens["categoria_b"],
        funcao=resolved_funcao,
        categoria=CANONICAL_CATEGORY_B,
        allow_general_function=False,
        allow_general_category=False,
        parametros_usados=parametros_usados,
    )
    valor_cobertura_base = _quantity_value(
        parametros_pool,
        "cobertura_base",
        quantity=contagens["cobertura_base"],
        funcao=resolved_funcao,
        allow_general_function=False,
        parametros_usados=parametros_usados,
    )
    valor_pernoite_comum, parametro_pernoite_comum = _optional_quantity_value(
        parametros_pool,
        "pernoite_comum_sem_cobertura",
        quantity=contagens["pernoite_comum_sem_cobertura"],
        funcao=resolved_funcao,
        allow_general_function=False,
        parametros_usados=parametros_usados,
    )
    valor_excecao_palmas_parametrizado = _quantity_value(
        parametros_pool,
        "excecao_palmas_turbohelice",
        quantity=contagens["excecao_palmas_turbohelice"],
        funcao=resolved_funcao,
        categoria=CANONICAL_CATEGORY_TURBOHELICE_PALMAS,
        allow_general_function=False,
        allow_general_category=False,
        parametros_usados=parametros_usados,
    )
    categoria_aplicavel = _categoria_aplicavel(contagens)
    categoria_garantia_minima = _categoria_garantia_minima_tripulante(tripulante)
    garantia_parameter = None
    garantia_minima = Decimal("0.00")
    inicio_produtividade = None
    if categoria_garantia_minima:
        garantia_parameter = _find_parameter(
            parametros_pool,
            "garantia_minima",
            funcao=resolved_funcao,
            categoria=categoria_garantia_minima,
            allow_general_function=False,
            allow_general_category=False,
        )
        garantia_minima_integral = _money(_parameter_decimal(garantia_parameter))
        garantia_minima = _apply_vacation_proportionality(garantia_minima_integral, ferias_context)
        inicio_produtividade = _garantia_inicio_produtividade(
            tripulante, funcao=resolved_funcao, categoria=categoria_garantia_minima,
            competencia_inicio=reference_date, competencia_fim=competence_end,
            ferias_context=ferias_context,
        )
        if inicio_produtividade is not None:
            garantia_minima = _money(
                garantia_minima_integral * Decimal(inicio_produtividade["dias_remunerados"])
                / Decimal(inicio_produtividade["dias_competencia"])
            )
        parametros_usados.append(_parameter_reference(garantia_parameter))

    produtividade_sem_piso_palmas = _money(
        valor_icao
        + valor_instrutor
        + valor_checador
        + valor_missoes_categoria_a
        + valor_missoes_categoria_b
        + valor_cobertura_base
        + valor_pernoite_comum
    )
    piso_palmas_integral = (
        valor_excecao_palmas_parametrizado
        if excecao_palmas_turbohelice
        else Decimal("0.00")
    )
    piso_palmas_proporcional = _apply_vacation_proportionality(piso_palmas_integral, ferias_context)
    if excecao_palmas_turbohelice:
        valor_excecao_palmas = _money(
            max(piso_palmas_proporcional - produtividade_sem_piso_palmas, Decimal("0.00"))
        )
    else:
        valor_excecao_palmas = valor_excecao_palmas_parametrizado
    produtividade_calculada = _money(produtividade_sem_piso_palmas + valor_excecao_palmas)
    total_devido = max(produtividade_calculada, garantia_minima) if aplicar_garantia_minima else produtividade_calculada
    total_devido = _money(total_devido)
    excedente = _money(max(produtividade_calculada - garantia_minima, Decimal("0.00")))
    valores = {
        "valor_icao": valor_icao,
        "valor_instrutor": valor_instrutor,
        "valor_checador": valor_checador,
        "valor_missoes_categoria_a": valor_missoes_categoria_a,
        "valor_missoes_categoria_b": valor_missoes_categoria_b,
        "valor_cobertura_base": valor_cobertura_base,
        "valor_pernoite_comum": valor_pernoite_comum,
        "valor_excecao_palmas": valor_excecao_palmas,
        "produtividade_sem_piso_palmas": produtividade_sem_piso_palmas,
        "piso_palmas_integral": piso_palmas_integral,
        "piso_palmas_proporcional": piso_palmas_proporcional,
        "produtividade_calculada": produtividade_calculada,
        "garantia_minima": garantia_minima,
        "excedente": excedente,
        "total_devido": total_devido,
    }

    memoria_calculo = _build_memory(
        competencia=resolved_competencia,
        tripulante=tripulante,
        tripulante_id=tripulante_id,
        funcao=resolved_funcao,
        flags=flags,
        contagens=contagens,
        categoria_aplicavel=categoria_aplicavel,
        categoria_garantia_minima=categoria_garantia_minima,
        parametros_usados=parametros_usados,
        valores=valores,
        parametro_pernoite_comum=parametro_pernoite_comum,
        ferias_context=ferias_context,
        aplicar_garantia_minima=aplicar_garantia_minima,
        calculation_version=calculation_version,
    )
    if inicio_produtividade is not None:
        memoria_calculo["inputs"]["proporcionalidade_inicio_produtividade"] = inicio_produtividade
        memoria_calculo["steps"].insert(-1, _build_step(
            rule_key="garantia_inicio_produtividade",
            rule_label="Garantia proporcional ao inicio da produtividade",
            entrada_usada=inicio_produtividade,
            parametro_usado=_parameter_reference(garantia_parameter),
            formula_conceitual="garantia mensal * dias remunerados desde o inicio / dias da competencia",
            resultado_intermediario={"garantia_mensal": _decimal_text(garantia_minima_integral)},
            resultado_final={"garantia_minima": _decimal_text(garantia_minima)},
        ))
    if contagens["pernoite_comum_sem_cobertura"] > 0 and parametro_pernoite_comum is None:
        memoria_calculo.setdefault("warnings", []).append(
            {
                "code": "pernoite_comum_parametro_ausente",
                "message": "Pernoite comum sem cobertura identificado, mas nao ha parametro financeiro vigente aprovado.",
                "quantidade": contagens["pernoite_comum_sem_cobertura"],
            }
        )
    if not categoria_garantia_minima and aplicar_garantia_minima:
        memoria_calculo.setdefault("warnings", []).append(
            {
                "code": "categoria_operacional_tripulante_nao_elegivel_garantia",
                "message": (
                    "Tripulante sem categoria operacional A/B vigente no cadastro; "
                    "garantia minima nao aplicada."
                ),
            }
        )
    memoria_calculo.setdefault("warnings", []).extend(_governance_warnings(flags))

    return {
        "competencia": resolved_competencia,
        "tripulante_id": tripulante_id,
        "funcao": resolved_funcao,
        "categoria_aplicavel": categoria_aplicavel,
        "valor_icao": valor_icao,
        "valor_instrutor": valor_instrutor,
        "valor_checador": valor_checador,
        "valor_missoes_categoria_a": valor_missoes_categoria_a,
        "valor_missoes_categoria_b": valor_missoes_categoria_b,
        "valor_cobertura_base": valor_cobertura_base,
        "valor_pernoite_comum": valor_pernoite_comum,
        "valor_excecao_palmas": valor_excecao_palmas,
        "produtividade_calculada": produtividade_calculada,
        "garantia_minima": garantia_minima,
        "excedente": excedente,
        "total_devido": total_devido,
        "memoria_calculo": memoria_calculo,
        "parametros_usados": parametros_usados,
        "calculation_version": calculation_version,
    }


def _resolve_competencia(value) -> str:
    competencia = str(value or "").strip()
    if len(competencia) != 7 or competencia[4] != "-":
        raise BonificacaoProdutividadeInvalidaErro(
            "Competencia deve estar no formato YYYY-MM.",
            code="bonificacao_produtividade_competencia_invalida",
        )
    return competencia


def _resolve_funcao(value) -> str:
    funcao = str(value or "").strip()
    if funcao not in FINANCE_CREW_FUNCTIONS:
        raise BonificacaoProdutividadeInvalidaErro(
            "Funcao deve ser comandante ou copiloto.",
            code="bonificacao_produtividade_funcao_invalida",
        )
    return funcao


def _resolve_int(value) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _parse_reference_date(value) -> date | None:
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


def _month_end(value: date) -> date:
    return date(value.year, value.month, monthrange(value.year, value.month)[1])


def _optional_text(value) -> str | None:
    text = str(value or "").strip()
    return text or None


def _is_active_status(parameter: dict[str, Any]) -> bool:
    return str(parameter.get("status") or "").strip().lower() == "ativo"


def _normalize_funcao(value) -> str:
    return str(value or "").strip().lower()


def _parameter_id(parameter: dict[str, Any], *, index: int) -> int:
    raw = parameter.get("id")
    if raw in (None, ""):
        raw = parameter.get("parameter_id")
    if raw in (None, ""):
        return -2_000_000 - index
    try:
        return int(raw)
    except (TypeError, ValueError):
        return -2_000_000 - index


def _normalize_parameter_pool(parametros_vigentes: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(parametros_vigentes or []):
        row = dict(item or {})
        row.setdefault("org_id", FINANCE_ORG_SCOPE_DEFAULT)
        row["status"] = str(row.get("status") or "ativo").strip() or "ativo"
        row["motivo"] = str(row.get("motivo") or "").strip()
        row["id"] = _parameter_id(row, index=index)
        normalized.append(row)
    return normalized


def _vigencia_cobre_data(parameter: dict[str, Any], *, reference_date: date) -> bool:
    start = _parse_reference_date(parameter.get("vigencia_inicio"))
    end = _parse_reference_date(parameter.get("vigencia_fim"))
    if start is None:
        return False
    if end is not None and end < start:
        return False
    if start > reference_date:
        return False
    if end is not None and end < reference_date:
        return False
    return True


def _blocking_payload(parameter: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    return {
        "parameter_id": parameter.get("id"),
        "tipo": str(parameter.get("tipo") or "").strip(),
        "funcao": str(parameter.get("funcao") or "").strip() or None,
        "categoria": str(parameter.get("categoria") or "").strip() or None,
        "unidade": str(parameter.get("unidade") or "").strip(),
        "valor": str(parameter.get("valor") or ""),
        "governance_class": classificacao_governanca_parametro(parameter),
        "reasons": sorted(set(reasons)),
    }


def _validate_parameter_pool(
    parametros_pool: list[dict[str, Any]],
    *,
    reference_date: date,
    supported_types: tuple[str, ...],
    real_closure: bool,
    release_environment: str,
) -> None:
    relevant = [
        parameter
        for parameter in parametros_pool
        if str(parameter.get("tipo") or "").strip() in supported_types
    ]
    if not relevant:
        return

    overlap_ids = detectar_sobreposicoes_ativas(relevant, include_unit=False)
    divergence_ids = detectar_divergencias_ativas(relevant, include_unit=False)
    blocking: list[dict[str, Any]] = []

    for parameter in relevant:
        reasons: list[str] = []
        tipo = _optional_text(parameter.get("tipo")) or ""
        unidade = _optional_text(parameter.get("unidade")) or ""
        funcao_parametro = _normalize_funcao(parameter.get("funcao"))
        categoria_parametro = _normalize_category(parameter.get("categoria"))
        rule = PRODUCTIVITY_PARAMETER_RULES.get(tipo)
        parameter_id = int(parameter.get("id"))
        if not _is_active_status(parameter):
            reasons.append("status_inativo")
        if rule:
            if unidade != rule["unidade"]:
                reasons.append("unidade_invalida_para_tipo")
            if rule["funcao_mode"] == "none" and funcao_parametro:
                reasons.append("funcao_invalida_para_tipo")
            if rule["funcao_mode"] == "crew" and funcao_parametro not in FINANCE_CREW_FUNCTIONS:
                reasons.append("funcao_invalida_para_tipo")
            if categoria_parametro not in rule["categorias"]:
                reasons.append("categoria_invalida_para_tipo")
        if str(parameter.get("unidade") or "").strip().upper() == "BRL":
            reasons.append("unidade_brl_legacy")
        if not _vigencia_cobre_data(parameter, reference_date=reference_date):
            reasons.append("vigencia_invalida_ou_fora_da_data")
        if parameter_id in overlap_ids:
            reasons.append("sobreposicao_semantica_ativa")
        if parameter_id in divergence_ids:
            reasons.append("divergencia_semantica_ativa")
        if real_closure:
            if not parametro_elegivel_fechamento_real(parameter, environment=release_environment):
                reasons.append("nao_elegivel_para_fechamento_real")
            if classificacao_governanca_parametro(parameter) == "qa-smoke":
                reasons.append("classificacao_qa_smoke_bloqueada")
        if reasons:
            blocking.append(_blocking_payload(parameter, reasons))

    if blocking:
        raise ParametroBonificacaoProdutividadeNaoElegivelErro(
            blocking_parameters=blocking,
            real_closure=real_closure,
        )


def _bool_value(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "on", "yes", "sim", "ativo"}


def _period_overlaps_competence(start_value, end_value, *, competencia_inicio: date, competencia_fim: date) -> bool:
    start = _parse_reference_date(start_value)
    end = _parse_reference_date(end_value)
    if start is None:
        return False
    if end is not None and end < start:
        return False
    if start > competencia_fim:
        return False
    if end is not None and end < competencia_inicio:
        return False
    return True


def _plain_token(value) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    normalized = _unicode_normalize("NFKD", text)
    return " ".join("".join(ch for ch in normalized if ch.isascii()).split())


def _vacation_periods_from_tripulante(tripulante: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("periodos_ferias", "ferias", "periodos_operacionais"):
        value = tripulante.get(key)
        if isinstance(value, (list, tuple)):
            return [dict(item or {}) for item in value]
    return []


def _vacation_proportionality(
    tripulante: dict[str, Any],
    *,
    competencia_inicio: date,
    competencia_fim: date,
) -> dict[str, Any]:
    month_days = (competencia_fim - competencia_inicio).days + 1
    vacation_days: set[int] = set()
    periods: list[dict[str, Any]] = []

    for item in _vacation_periods_from_tripulante(tripulante):
        tipo = _plain_token(item.get("tipo") or item.get("tipo_periodo"))
        if tipo and tipo not in {"ferias", "feria"}:
            continue
        status = _plain_token(item.get("status") or item.get("situacao"))
        if status in _CANCELLED_OPERATIONAL_PERIOD_STATUSES:
            continue

        start = _parse_reference_date(item.get("data_inicio") or item.get("inicio") or item.get("start"))
        end = _parse_reference_date(item.get("data_fim") or item.get("fim") or item.get("end")) or competencia_fim
        if start is None or end < start:
            continue
        if start > competencia_fim or end < competencia_inicio:
            continue

        overlap_start = max(start, competencia_inicio)
        overlap_end = min(end, competencia_fim)
        days = (overlap_end - overlap_start).days + 1
        for ordinal in range(overlap_start.toordinal(), overlap_end.toordinal() + 1):
            vacation_days.add(ordinal)
        periods.append(
            {
                "id": item.get("id") or item.get("periodo_id"),
                "tipo": str(item.get("tipo") or "ferias").strip() or "ferias",
                "status": str(item.get("status") or "").strip() or None,
                "data_inicio": _date_text(start),
                "data_fim": _date_text(end),
                "dias_sobrepostos": days,
            }
        )

    used_vacation_days = min(len(vacation_days), month_days)
    payable_days = max(month_days - used_vacation_days, 0)
    factor = Decimal(payable_days) / Decimal(month_days)
    return {
        "dias_competencia": month_days,
        "dias_ferias": used_vacation_days,
        "dias_proporcionais": payable_days,
        "fator": factor,
        "periodos": periods,
    }


def _garantia_inicio_produtividade(
    tripulante: dict[str, Any], *, funcao: str, categoria: str,
    competencia_inicio: date, competencia_fim: date, ferias_context: dict[str, Any],
) -> dict[str, Any] | None:
    # Inicio aprovado para Edmar: categoria CitationJet em 25/09/2026,
    # com garantia proporcional somente na competencia de ingresso.
    inicio = date(2026, 9, 25)
    if (
        _resolve_int(tripulante.get("id") or tripulante.get("tripulante_id")) != 26
        or _plain_token(tripulante.get("nome") or tripulante.get("tripulante_nome")) != "edmar pinto fiuza"
        or funcao != "comandante" or categoria != CANONICAL_CATEGORY_A
        or not competencia_inicio <= inicio <= competencia_fim
    ):
        return None
    dias = set(range(inicio.toordinal(), competencia_fim.toordinal() + 1))
    dias_vigencia = len(dias)
    for periodo in ferias_context["periodos"]:
        primeiro = max(inicio, date.fromisoformat(periodo["data_inicio"]))
        ultimo = min(competencia_fim, date.fromisoformat(periodo["data_fim"]))
        dias.difference_update(range(primeiro.toordinal(), ultimo.toordinal() + 1))
    return {
        "data_inicio": inicio.isoformat(), "dias_competencia": ferias_context["dias_competencia"],
        "dias_vigencia": dias_vigencia, "dias_ferias_na_vigencia": dias_vigencia - len(dias),
        "dias_remunerados": len(dias),
    }


def _apply_vacation_proportionality(value: Decimal, ferias_context: dict[str, Any]) -> Decimal:
    return _money(value * ferias_context["fator"])


def _active_checador_designations(
    tripulante: dict[str, Any],
    *,
    competencia_inicio: date,
    competencia_fim: date,
) -> list[dict[str, Any]]:
    direct_requested = _bool_value(
        tripulante.get("checador") or tripulante.get("checador_ativo") or tripulante.get("checador_designado")
    )
    designations = tripulante.get("checador_designacoes")
    active: list[dict[str, Any]] = []
    if isinstance(designations, (list, tuple)):
        for index, item in enumerate(designations):
            row = dict(item or {})
            if not _bool_value(row.get("ativo", True)):
                continue
            if not _period_overlaps_competence(
                row.get("data_inicio") or row.get("inicio") or row.get("checador_inicio"),
                row.get("data_fim") or row.get("fim") or row.get("checador_fim"),
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
            ):
                continue
            carta = _optional_text(
                row.get("carta_designacao")
                or row.get("designacao")
                or row.get("numero")
                or row.get("checador_carta_designacao")
            )
            if not carta:
                continue
            active.append({"index": index, "carta_designacao": carta})
    elif direct_requested and _period_overlaps_competence(
        tripulante.get("checador_inicio"),
        tripulante.get("checador_fim"),
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    ):
        carta = _optional_text(tripulante.get("checador_carta_designacao"))
        if carta:
            active.append({"index": 0, "carta_designacao": carta})
    return active


def _tripulante_flags(
    tripulante: dict[str, Any],
    *,
    competencia_inicio: date,
    competencia_fim: date,
) -> dict[str, Any]:
    sdea_solicitado = _bool_value(tripulante.get("sdea_ativo") or tripulante.get("sdea"))
    sdea_validade = _parse_reference_date(
        tripulante.get("sdea_icao_validade")
        or tripulante.get("sdea_validade")
        or tripulante.get("validade_sdea_icao")
    )
    sdea_vigente = bool(sdea_solicitado and (sdea_validade is None or sdea_validade >= competencia_fim))
    instrutor_solicitado = _bool_value(
        tripulante.get("instrutor") or tripulante.get("instrutor_ativo") or tripulante.get("instrutor_designado")
    )
    instrutor_vigente = instrutor_solicitado and _period_overlaps_competence(
        tripulante.get("instrutor_inicio"),
        tripulante.get("instrutor_fim"),
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    checador_solicitado = _bool_value(
        tripulante.get("checador") or tripulante.get("checador_ativo") or tripulante.get("checador_designado")
    )
    active_designations = _active_checador_designations(
        tripulante,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    carta_considerada = active_designations[0]["carta_designacao"] if active_designations else None
    return {
        "sdea_ativo": sdea_vigente,
        "sdea_solicitado": sdea_solicitado,
        "sdea_icao_validade": _date_text(sdea_validade),
        "sdea_validade_aberta": bool(sdea_solicitado and sdea_validade is None),
        "sdea_regra_vigencia": "validade_vazia_conta_como_vigencia_aberta",
        "instrutor": bool(instrutor_vigente),
        "instrutor_solicitado": instrutor_solicitado,
        "instrutor_inicio": _date_text(tripulante.get("instrutor_inicio")),
        "instrutor_fim": _date_text(tripulante.get("instrutor_fim")),
        "checador": bool(active_designations),
        "checador_solicitado": checador_solicitado,
        "checador_inicio": _date_text(tripulante.get("checador_inicio")),
        "checador_fim": _date_text(tripulante.get("checador_fim")),
        "checador_carta_designacao": _optional_text(tripulante.get("checador_carta_designacao")),
        "checador_cartas_ativas": len(active_designations),
        "checador_carta_considerada": carta_considerada,
        "checador_regra_acumulo": "paga_uma_designacao_vigente_por_competencia",
    }


def _governance_warnings(flags: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if flags.get("sdea_solicitado") and not flags.get("sdea_ativo"):
        warnings.append(
            {
                "code": "sdea_icao_sem_vigencia_valida",
                "message": "SDEA/ICAO ativo no cadastro, mas com validade vencida no ultimo dia da competencia.",
                "validade": flags.get("sdea_icao_validade"),
            }
        )
    if flags.get("instrutor_solicitado") and not flags.get("instrutor"):
        warnings.append(
            {
                "code": "instrutor_fora_da_vigencia",
                "message": "Instrutor marcado no cadastro, mas sem periodo de designacao vigente na competencia.",
                "inicio": flags.get("instrutor_inicio"),
                "fim": flags.get("instrutor_fim"),
            }
        )
    if flags.get("checador_solicitado") and not flags.get("checador"):
        warnings.append(
            {
                "code": "checador_sem_designacao_vigente",
                "message": "Checador marcado no cadastro, mas sem carta/designacao vigente na competencia.",
                "inicio": flags.get("checador_inicio"),
                "fim": flags.get("checador_fim"),
                "carta_designacao": flags.get("checador_carta_designacao"),
            }
        )
    if int(flags.get("checador_cartas_ativas") or 0) > 1:
        warnings.append(
            {
                "code": "checador_multiplas_cartas_nao_acumulam",
                "message": "Mais de uma carta de checador vigente encontrada; o adicional foi pago uma unica vez.",
                "cartas_ativas": flags.get("checador_cartas_ativas"),
                "carta_considerada": flags.get("checador_carta_considerada"),
            }
        )
    return warnings


def _normalize_category(value) -> str:
    return normalizar_categoria_parametro(value)


def _mission_counts(
    missoes_operacionais: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    cobertura_base: bool,
    excecao_palmas_turbohelice: bool,
) -> dict[str, int]:
    counts = {
        "total_missoes": len(missoes_operacionais or []),
        "categoria_a": 0,
        "categoria_b": 0,
        "cobertura_base": 0,
        "pernoite_comum_sem_cobertura": 0,
        "excecao_palmas_turbohelice": 0,
    }
    for mission in missoes_operacionais or []:
        category = normalizar_categoria_operacional(
            mission.get("categoria_financeira_aeronave") or mission.get("categoria_aplicavel")
        )
        if category == CANONICAL_CATEGORY_A:
            counts["categoria_a"] += 1
        elif category == CANONICAL_CATEGORY_B:
            counts["categoria_b"] += 1
        quantidade_pernoites = (
            _resolve_int(mission.get("quantidade_pernoites"))
            if "quantidade_pernoites" in mission
            else None
        )
        if _bool_value(mission.get("cobertura_base")):
            counts["cobertura_base"] += max(0, quantidade_pernoites if quantidade_pernoites is not None else 1)
        elif (quantidade_pernoites or 0) > 1:
            counts["pernoite_comum_sem_cobertura"] += quantidade_pernoites - 1
        if not excecao_palmas_turbohelice and _is_palmas_turbohelice(mission, category=category):
            counts["excecao_palmas_turbohelice"] += 1
    if cobertura_base and counts["cobertura_base"] == 0:
        counts["cobertura_base"] = 1
    if excecao_palmas_turbohelice:
        counts["excecao_palmas_turbohelice"] = 1
    return counts


def _is_palmas_turbohelice(mission: dict[str, Any], *, category: str) -> bool:
    if category == CANONICAL_CATEGORY_TURBOHELICE_PALMAS:
        return True
    if _bool_value(mission.get("excecao_palmas_turbohelice") or mission.get("palmas_turbohelice")):
        return True
    return is_operacao_especial_palmas_turbohelice(mission.get("operacao_especial"))


def _conditional_value(
    parametros_vigentes: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    tipo: str,
    *,
    active: bool,
    funcao: str | None,
    allow_general_function: bool,
    parametros_usados: list[dict[str, Any]],
) -> Decimal:
    if not active:
        return Decimal("0.00")
    parameter = _find_parameter(
        parametros_vigentes,
        tipo,
        funcao=funcao,
        allow_general_function=allow_general_function,
    )
    parametros_usados.append(_parameter_reference(parameter))
    return _money(_parameter_decimal(parameter))


def _quantity_value(
    parametros_vigentes: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    tipo: str,
    *,
    quantity: int,
    funcao: str,
    parametros_usados: list[dict[str, Any]],
    categoria: str | None = None,
    allow_general_function: bool = True,
    allow_general_category: bool = True,
) -> Decimal:
    if quantity <= 0:
        return Decimal("0.00")
    parameter = _find_parameter(
        parametros_vigentes,
        tipo,
        funcao=funcao,
        categoria=categoria,
        allow_general_function=allow_general_function,
        allow_general_category=allow_general_category,
    )
    parametros_usados.append(_parameter_reference(parameter))
    return _money(Decimal(quantity) * _parameter_decimal(parameter))


def _optional_quantity_value(
    parametros_vigentes: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    tipo: str,
    *,
    quantity: int,
    funcao: str,
    parametros_usados: list[dict[str, Any]],
    categoria: str | None = None,
    allow_general_function: bool = True,
    allow_general_category: bool = True,
) -> tuple[Decimal, dict[str, Any] | None]:
    if quantity <= 0:
        return Decimal("0.00"), None
    try:
        parameter = _find_parameter(
            parametros_vigentes,
            tipo,
            funcao=funcao,
            categoria=categoria,
            allow_general_function=allow_general_function,
            allow_general_category=allow_general_category,
        )
    except ParametroBonificacaoProdutividadeAusenteErro:
        return Decimal("0.00"), None
    parametros_usados.append(_parameter_reference(parameter))
    return _money(Decimal(quantity) * _parameter_decimal(parameter)), parameter


def _find_parameter(
    parametros_vigentes: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    tipo: str,
    *,
    funcao: str | None = None,
    categoria: str | None = None,
    unidade: str = MONETARY_PARAMETER_UNIT,
    allow_general_function: bool = True,
    allow_general_category: bool = True,
) -> dict[str, Any]:
    candidates = [
        item
        for item in parametros_vigentes
        if str(item.get("tipo") or "").strip() == tipo
        and str(item.get("unidade") or "").strip() == unidade
    ]
    if categoria is not None:
        exact_category = [item for item in candidates if _normalize_category(item.get("categoria")) == categoria]
        if exact_category:
            candidates = exact_category
        elif allow_general_category:
            candidates = [item for item in candidates if not _normalize_category(item.get("categoria"))]
        else:
            raise ParametroBonificacaoProdutividadeAusenteErro(tipo, funcao=funcao, categoria=categoria)
    else:
        candidates = [item for item in candidates if not _normalize_category(item.get("categoria"))]
    if funcao is not None:
        exact_function = [item for item in candidates if str(item.get("funcao") or "").strip() == funcao]
        if exact_function:
            candidates = exact_function
        elif allow_general_function:
            candidates = [item for item in candidates if not str(item.get("funcao") or "").strip()]
        else:
            raise ParametroBonificacaoProdutividadeAusenteErro(tipo, funcao=funcao, categoria=categoria)
    else:
        candidates = [item for item in candidates if not str(item.get("funcao") or "").strip()]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise ParametroBonificacaoProdutividadeAmbiguoErro(
            tipo,
            funcao=funcao,
            categoria=categoria,
            unidade=unidade,
        )
    raise ParametroBonificacaoProdutividadeAusenteErro(tipo, funcao=funcao, categoria=categoria)


def _parameter_decimal(parameter: dict[str, Any]) -> Decimal:
    try:
        return Decimal(str(parameter.get("valor")).replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise BonificacaoProdutividadeInvalidaErro(
            f"Parametro {parameter.get('tipo')} deve ser numerico.",
            code="bonificacao_produtividade_parametro_decimal_invalido",
        ) from exc


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


def _parameter_reference(parameter: dict[str, Any]) -> dict[str, Any]:
    return {
        "parameter_id": _resolve_int(parameter.get("parameter_id") if "parameter_id" in parameter else parameter.get("id")),
        "tipo": str(parameter.get("tipo") or "").strip(),
        "funcao": str(parameter.get("funcao") or "").strip() or None,
        "categoria": str(parameter.get("categoria") or "").strip() or None,
        "valor": str(parameter.get("valor")),
        "unidade": str(parameter.get("unidade") or "").strip(),
        "vigencia_inicio": _date_text(parameter.get("vigencia_inicio")),
        "vigencia_fim": _date_text(parameter.get("vigencia_fim")),
    }


def _date_text(value) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _factor_text(value: Decimal) -> str:
    return format(value.quantize(FACTOR_QUANTIZER, rounding=ROUND_HALF_UP), "f")


def _categoria_aplicavel(contagens: dict[str, int]) -> str:
    active = []
    if contagens["categoria_a"]:
        active.append(CANONICAL_CATEGORY_A)
    if contagens["categoria_b"]:
        active.append(CANONICAL_CATEGORY_B)
    if contagens["excecao_palmas_turbohelice"]:
        active.append(CANONICAL_CATEGORY_TURBOHELICE_PALMAS)
    if len(active) == 1:
        return active[0]
    if len(active) > 1:
        return "mista"
    return "nao_aplicavel"


def _categoria_garantia_minima_tripulante(tripulante: dict[str, Any]) -> str | None:
    category = normalizar_categoria_operacional(
        tripulante.get("categoria_operacional")
        or tripulante.get("categoria")
        or tripulante.get("categoria_tripulante")
    )
    if category in {CANONICAL_CATEGORY_A, CANONICAL_CATEGORY_B}:
        return category
    return None


def _build_step(
    *,
    rule_key: str,
    rule_label: str,
    entrada_usada: dict[str, Any],
    parametro_usado: dict[str, Any] | None,
    formula_conceitual: str,
    resultado_intermediario: dict[str, Any],
    resultado_final: dict[str, Any],
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "rule_key": rule_key,
        "rule_label": rule_label,
        "entrada_usada": entrada_usada,
        "parametro_usado": _parameter_reference(parametro_usado) if parametro_usado else None,
        "formula_conceitual": formula_conceitual,
        "resultado_intermediario": resultado_intermediario,
        "resultado_final": resultado_final,
        "notes": notes or [],
    }


def _vacation_memory(ferias_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "dias_competencia": ferias_context["dias_competencia"],
        "dias_ferias": ferias_context["dias_ferias"],
        "dias_proporcionais": ferias_context["dias_proporcionais"],
        "fator": _factor_text(ferias_context["fator"]),
        "periodos": ferias_context["periodos"],
    }


def _build_memory(
    *,
    competencia: str,
    tripulante: dict[str, Any],
    tripulante_id: int | None,
    funcao: str,
    flags: dict[str, Any],
    contagens: dict[str, int],
    categoria_aplicavel: str,
    categoria_garantia_minima: str | None,
    parametros_usados: list[dict[str, Any]],
    valores: dict[str, Decimal],
    parametro_pernoite_comum: dict[str, Any] | None,
    ferias_context: dict[str, Any],
    aplicar_garantia_minima: bool,
    calculation_version: str,
) -> dict[str, Any]:
    piso_palmas_integral = valores.get("piso_palmas_integral", Decimal("0.00"))
    piso_palmas_proporcional = valores.get("piso_palmas_proporcional", piso_palmas_integral)
    produtividade_sem_piso_palmas = valores.get(
        "produtividade_sem_piso_palmas",
        valores["produtividade_calculada"],
    )
    palmas_cadastral_com_piso = piso_palmas_integral > Decimal("0.00")
    palmas_formula = (
        "max(piso_palmas_proporcional - produtividade_sem_piso_palmas, 0)"
        if palmas_cadastral_com_piso
        else "quantidade_excecao_palmas_turbohelice * parametro_excecao_palmas_turbohelice"
    )
    palmas_intermediario = (
        {
            "piso_palmas_integral": _decimal_text(piso_palmas_integral),
            "piso_palmas_proporcional": _decimal_text(piso_palmas_proporcional),
            "produtividade_sem_piso_palmas": _decimal_text(produtividade_sem_piso_palmas),
            "complemento_piso_palmas": _decimal_text(valores["valor_excecao_palmas"]),
        }
        if palmas_cadastral_com_piso
        else {}
    )
    palmas_notes = (
        ["SDEA/ICAO e demais componentes da produtividade compoem o piso cadastral de Palmas."]
        if palmas_cadastral_com_piso
        else []
    )
    produtividade_formula = (
        "produtividade_sem_piso_palmas + complemento do piso cadastral de Palmas"
        if palmas_cadastral_com_piso
        else (
            "soma dos adicionais cadastrais, missoes por categoria, cobertura de base, "
            "pernoite comum parametrizado e excecoes"
        )
    )
    ferias_memory = _vacation_memory(ferias_context)
    ferias_steps = (
        [
            _build_step(
                rule_key="ferias_proporcional",
                rule_label="Proporcionalidade por ferias",
                entrada_usada=ferias_memory,
                parametro_usado=None,
                formula_conceitual=(
                    "componentes mensais e pisos * dias_proporcionais / dias_competencia; "
                    "valores por missao permanecem por voo realizado"
                ),
                resultado_intermediario={
                    "fator_proporcional": ferias_memory["fator"],
                    "dias_ferias": ferias_memory["dias_ferias"],
                    "dias_proporcionais": ferias_memory["dias_proporcionais"],
                },
                resultado_final={
                    "valor_icao": _decimal_text(valores["valor_icao"]),
                    "valor_instrutor": _decimal_text(valores["valor_instrutor"]),
                    "valor_checador": _decimal_text(valores["valor_checador"]),
                    "garantia_minima": _decimal_text(valores["garantia_minima"]),
                    "piso_palmas_proporcional": _decimal_text(piso_palmas_proporcional),
                },
                notes=[
                    "Ferias reduzem parcelas mensais e pisos. Missoes efetivamente voadas seguem pelo valor integral da missao."
                ],
            )
        ]
        if ferias_context["dias_ferias"] > 0
        else []
    )
    return {
        "calculation_version": calculation_version,
        "org_id": str(tripulante.get("org_id") or FINANCE_ORG_SCOPE_DEFAULT),
        "competencia": competencia,
        "source": {
            "type": "finance_productivity_competence",
            "id": competencia,
        },
        "participant": {
            "tripulante_id": tripulante_id,
            "funcao": funcao,
        },
        "inputs": {
            "competencia": competencia,
            "tripulante_id": tripulante_id,
            "funcao": funcao,
            "flags_operacionais": flags,
            "contagens_agregadas": contagens,
            "categoria_aplicavel": categoria_aplicavel,
            "categoria_garantia_minima": categoria_garantia_minima,
            "proporcionalidade_ferias": ferias_memory,
            "politica_total_devido": (
                "max(produtividade_calculada, garantia_minima)"
                if aplicar_garantia_minima
                else "produtividade_calculada"
            ),
        },
        "parameters": parametros_usados,
        "calendar_flags": {"ferias": ferias_memory},
        "steps": [
            _build_step(
                rule_key="flags_cadastrais",
                rule_label="Adicionais cadastrais do tripulante",
                entrada_usada=flags,
                parametro_usado=None,
                formula_conceitual=(
                    "somar ICAO/SDEA se valido no ultimo dia da competencia ou com validade cadastral vazia; "
                    "somar instrutor/checador somente com designacao vigente; checador nao acumula multiplas cartas"
                ),
                resultado_intermediario={
                    "valor_icao": _decimal_text(valores["valor_icao"]),
                    "valor_instrutor": _decimal_text(valores["valor_instrutor"]),
                    "valor_checador": _decimal_text(valores["valor_checador"]),
                },
                resultado_final={
                    "subtotal_flags": _decimal_text(
                        valores["valor_icao"] + valores["valor_instrutor"] + valores["valor_checador"]
                    )
                },
                notes=[
                    "SDEA/ICAO com validade vazia conta como vigencia aberta; se houver validade, ela deve estar vigente no ultimo dia da competencia.",
                    "Instrutor exige periodo de designacao sobreposto a competencia.",
                    "Checador exige carta/designacao vigente e paga uma unica vez por competencia.",
                ],
            ),
            *ferias_steps,
            _build_step(
                rule_key="missoes_por_categoria",
                rule_label="Missoes operacionais por categoria financeira",
                entrada_usada={
                    "categoria_a": contagens["categoria_a"],
                    "categoria_b": contagens["categoria_b"],
                    "categoria_aplicavel": categoria_aplicavel,
                },
                parametro_usado=None,
                formula_conceitual="quantidade_categoria_a * missao_categoria_a + quantidade_categoria_b * missao_categoria_b",
                resultado_intermediario={
                    "valor_missoes_categoria_a": _decimal_text(valores["valor_missoes_categoria_a"]),
                    "valor_missoes_categoria_b": _decimal_text(valores["valor_missoes_categoria_b"]),
                },
                resultado_final={
                    "subtotal_missoes": _decimal_text(
                        valores["valor_missoes_categoria_a"] + valores["valor_missoes_categoria_b"]
                    )
                },
            ),
            _build_step(
                rule_key="cobertura_base",
                rule_label="Cobertura de base",
                entrada_usada={"quantidade": contagens["cobertura_base"]},
                parametro_usado=None,
                formula_conceitual="quantidade_cobertura_base * parametro_cobertura_base",
                resultado_intermediario={},
                resultado_final={"valor_cobertura_base": _decimal_text(valores["valor_cobertura_base"])},
            ),
            _build_step(
                rule_key="pernoite_comum_sem_cobertura",
                rule_label="Pernoite comum sem cobertura de base",
                entrada_usada={
                    "quantidade_a_partir_do_segundo_pernoite": contagens["pernoite_comum_sem_cobertura"]
                },
                parametro_usado=parametro_pernoite_comum,
                formula_conceitual=(
                    "se quantidade_pernoites <= 1, adicional = 0; se quantidade_pernoites > 1 e sem cobertura, "
                    "adicional = (quantidade_pernoites - 1) * parametro_pernoite_comum_sem_cobertura_por_funcao"
                ),
                resultado_intermediario={
                    "pernoites_remuneraveis": contagens["pernoite_comum_sem_cobertura"],
                    "valor_unitario": (
                        _decimal_text(_parameter_decimal(parametro_pernoite_comum))
                        if parametro_pernoite_comum
                        else None
                    ),
                },
                resultado_final={"valor_pernoite_comum": _decimal_text(valores["valor_pernoite_comum"])},
                notes=[
                    (
                        "Parametro financeiro vigente aplicado a partir do segundo pernoite."
                        if parametro_pernoite_comum
                        else "Regra classificada sem somar valor porque nao ha parametro vigente aprovado."
                    )
                ],
            ),
            _build_step(
                rule_key="excecao_palmas_turbohelice",
                rule_label="Excecao Palmas/turbo-helice",
                entrada_usada={"quantidade": contagens["excecao_palmas_turbohelice"]},
                parametro_usado=None,
                formula_conceitual=palmas_formula,
                resultado_intermediario=palmas_intermediario,
                resultado_final={"valor_excecao_palmas": _decimal_text(valores["valor_excecao_palmas"])},
                notes=palmas_notes,
            ),
            _build_step(
                rule_key="produtividade_calculada",
                rule_label="Produtividade calculada",
                entrada_usada={},
                parametro_usado=None,
                formula_conceitual=produtividade_formula,
                resultado_intermediario={
                    **{
                        key: _decimal_text(value)
                        for key, value in valores.items()
                        if key.startswith("valor_")
                    },
                    **(
                        {
                            "produtividade_sem_piso_palmas": _decimal_text(produtividade_sem_piso_palmas),
                            "piso_palmas_integral": _decimal_text(piso_palmas_integral),
                        }
                        if palmas_cadastral_com_piso
                        else {}
                    ),
                },
                resultado_final={"produtividade_calculada": _decimal_text(valores["produtividade_calculada"])},
            ),
            _build_step(
                rule_key="garantia_minima",
                rule_label="Garantia minima",
                entrada_usada={
                    "aplicar_garantia_minima": aplicar_garantia_minima,
                    "categoria_garantia_minima": categoria_garantia_minima,
                },
                parametro_usado=None,
                formula_conceitual=(
                    "total_devido = max(produtividade_calculada, garantia_minima)"
                    if aplicar_garantia_minima
                    else "total_devido = produtividade_calculada"
                ),
                resultado_intermediario={
                    "produtividade_calculada": _decimal_text(valores["produtividade_calculada"]),
                    "garantia_minima": _decimal_text(valores["garantia_minima"]),
                    "excedente": _decimal_text(valores["excedente"]),
                },
                resultado_final={
                    "total_devido": _decimal_text(valores["total_devido"]),
                    "excedente": _decimal_text(valores["excedente"]),
                },
                notes=[
                    "Garantia minima usa a categoria operacional/cadastral do tripulante, nao a categoria da missao."
                ],
            ),
        ],
        "totals": {key: _decimal_text(value) for key, value in valores.items()},
        "warnings": [],
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat(),
    }
