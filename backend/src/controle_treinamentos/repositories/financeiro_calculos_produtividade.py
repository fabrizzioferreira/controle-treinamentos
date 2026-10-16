from __future__ import annotations

from calendar import monthrange
from datetime import date
import json
from decimal import Decimal

from ..contracts.financeiro import FINANCE_ORG_SCOPE_DEFAULT


def _effective_crew_function_sql(
    *,
    tripulante_id_sql: str,
    reference_date_sql: str,
    fallback_funcao_sql: str,
) -> str:
    return f"""
COALESCE(
    (
        SELECT tfov.funcao_operacional
        FROM tripulante_funcoes_operacionais_vigencias tfov
        WHERE tfov.tripulante_id = {tripulante_id_sql}
          AND tfov.status = 'ativo'
          AND tfov.data_inicio <= {reference_date_sql}
          AND (tfov.data_fim IS NULL OR tfov.data_fim >= {reference_date_sql})
        ORDER BY tfov.data_inicio DESC, tfov.id DESC
        LIMIT 1
    ),
    {fallback_funcao_sql}
)
"""


def _effective_crew_category_sql(*, tripulante_id_sql: str, reference_date_sql: str) -> str:
    return f"""
COALESCE(
    (
        SELECT NULLIF(TRIM(tfov.categoria_operacional), '')
        FROM tripulante_funcoes_operacionais_vigencias tfov
        WHERE tfov.tripulante_id = {tripulante_id_sql}
          AND tfov.status = 'ativo'
          AND tfov.categoria_operacional IS NOT NULL
          AND tfov.data_inicio <= {reference_date_sql}
          AND (tfov.data_fim IS NULL OR tfov.data_fim >= {reference_date_sql})
        ORDER BY tfov.data_inicio DESC, tfov.id DESC
        LIMIT 1
    ),
    t.categoria_operacional
)
"""

_PRODUCTIVITY_COLUMNS = (
    "org_id",
    "competencia",
    "tripulante_id",
    "funcao",
    "categoria_aplicavel",
    "valor_icao",
    "valor_instrutor",
    "valor_checador",
    "valor_missoes_categoria_a",
    "valor_missoes_categoria_b",
    "valor_cobertura_base",
    "valor_pernoite_comum",
    "valor_excecao_palmas",
    "produtividade_calculada",
    "garantia_minima",
    "total_devido",
    "memoria_calculo",
    "parametros_usados",
    "calculation_version",
    "status",
)


def _resolve_org_id(org_id: str | None) -> str:
    return (org_id or "").strip() or FINANCE_ORG_SCOPE_DEFAULT


def _dict_or_none(row) -> dict | None:
    return dict(row) if row else None


def _json_default(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def _json_text(value) -> str:
    return json.dumps(value or {}, default=_json_default, ensure_ascii=False)


def _table_columns(db, table_name: str) -> set[str]:
    rows = db.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
        """,
        (table_name,),
    ).fetchall()
    return {str(dict(row).get("column_name") or "").strip() for row in rows}


def _month_bounds(competencia: str) -> tuple[date, date]:
    reference = date.fromisoformat(f"{str(competencia or '').strip()}-01")
    return reference, date(reference.year, reference.month, monthrange(reference.year, reference.month)[1])


def salvar_calculo_produtividade(db, *, data: dict, org_id: str | None = None) -> dict:
    resolved_org_id = _resolve_org_id(org_id or data.get("org_id"))
    payload = {column: data.get(column) for column in _PRODUCTIVITY_COLUMNS}
    payload["org_id"] = resolved_org_id
    payload["memoria_calculo"] = _json_text(data.get("memoria_calculo"))
    payload["parametros_usados"] = _json_text(data.get("parametros_usados"))
    payload["calculation_version"] = data.get("calculation_version") or "finance-productivity-v1"
    payload["status"] = data.get("status") or "calculado"

    row = db.execute(
        """
        INSERT INTO financeiro_calculos_produtividade (
            org_id,
            competencia,
            tripulante_id,
            funcao,
            categoria_aplicavel,
            valor_icao,
            valor_instrutor,
            valor_checador,
            valor_missoes_categoria_a,
            valor_missoes_categoria_b,
            valor_cobertura_base,
            valor_pernoite_comum,
            valor_excecao_palmas,
            produtividade_calculada,
            garantia_minima,
            total_devido,
            memoria_calculo,
            parametros_usados,
            calculation_version,
            status
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s::jsonb,
            %s::jsonb,
            %s,
            COALESCE(%s, 'calculado')
        )
        ON CONFLICT (org_id, competencia, tripulante_id, funcao)
        DO UPDATE SET
            categoria_aplicavel = EXCLUDED.categoria_aplicavel,
            valor_icao = EXCLUDED.valor_icao,
            valor_instrutor = EXCLUDED.valor_instrutor,
            valor_checador = EXCLUDED.valor_checador,
            valor_missoes_categoria_a = EXCLUDED.valor_missoes_categoria_a,
            valor_missoes_categoria_b = EXCLUDED.valor_missoes_categoria_b,
            valor_cobertura_base = EXCLUDED.valor_cobertura_base,
            valor_pernoite_comum = EXCLUDED.valor_pernoite_comum,
            valor_excecao_palmas = EXCLUDED.valor_excecao_palmas,
            produtividade_calculada = EXCLUDED.produtividade_calculada,
            garantia_minima = EXCLUDED.garantia_minima,
            total_devido = EXCLUDED.total_devido,
            memoria_calculo = EXCLUDED.memoria_calculo,
            parametros_usados = EXCLUDED.parametros_usados,
            calculation_version = EXCLUDED.calculation_version,
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
        RETURNING *
        """,
        tuple(payload[column] for column in _PRODUCTIVITY_COLUMNS),
    ).fetchone()
    return dict(row)


def listar_calculos_produtividade(
    db,
    *,
    org_id: str | None = None,
    competencia: str | None = None,
    tripulante_id: int | None = None,
    funcao: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    resolved_org_id = _resolve_org_id(org_id)
    clauses = ["cp.org_id = %s"]
    params: list = [resolved_org_id]
    if competencia:
        clauses.append("cp.competencia = %s")
        params.append(competencia)
    if tripulante_id is not None:
        clauses.append("cp.tripulante_id = %s")
        params.append(int(tripulante_id))
    if funcao:
        clauses.append("cp.funcao = %s")
        params.append(funcao)
    if status:
        clauses.append("cp.status = %s")
        params.append(status)
    params.extend([int(limit), int(offset)])

    rows = db.execute(
        f"""
        SELECT
            cp.*,
            t.nome AS tripulante_nome,
            t.cpf AS tripulante_cpf,
            t.licenca_anac AS tripulante_licenca_anac,
            t.categoria_operacional AS tripulante_categoria_operacional,
            t.elegivel_adicional_excepcional AS tripulante_elegivel_adicional_excepcional,
            t.sdea_ativo AS tripulante_sdea_ativo,
            t.sdea_icao_validade AS tripulante_sdea_icao_validade,
            t.instrutor_ativo AS tripulante_instrutor_ativo,
            t.instrutor_inicio AS tripulante_instrutor_inicio,
            t.instrutor_fim AS tripulante_instrutor_fim,
            t.checador_ativo AS tripulante_checador_ativo,
            t.checador_inicio AS tripulante_checador_inicio,
            t.checador_fim AS tripulante_checador_fim,
            t.checador_carta_designacao AS tripulante_checador_carta_designacao
        FROM financeiro_calculos_produtividade cp
        JOIN tripulantes t
          ON t.id = cp.tripulante_id
        WHERE {" AND ".join(clauses)}
        ORDER BY cp.competencia DESC, t.nome ASC, cp.funcao ASC, cp.id DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    ).fetchall()
    return [dict(row) for row in rows]


def invalidar_calculos_produtividade_vigentes_da_competencia(
    db,
    *,
    competencia: str,
    org_id: str | None = None,
) -> list[dict]:
    resolved_org_id = _resolve_org_id(org_id)
    rows = db.execute(
        """
        WITH candidates AS (
            SELECT id, status AS previous_status
            FROM financeiro_calculos_produtividade
            WHERE org_id = %s
              AND competencia = %s
              AND COALESCE(status, 'calculado') NOT IN ('obsoleto', 'cancelado')
        )
        UPDATE financeiro_calculos_produtividade cp
        SET status = 'obsoleto',
            updated_at = CURRENT_TIMESTAMP
        FROM candidates
        WHERE cp.id = candidates.id
        RETURNING cp.*, candidates.previous_status
        """,
        (resolved_org_id, competencia),
    ).fetchall()
    return [dict(row) for row in rows]


def detalhar_calculo_produtividade_por_tripulante(
    db,
    *,
    tripulante_id: int,
    org_id: str | None = None,
    competencia: str | None = None,
    funcao: str | None = None,
) -> dict | None:
    resolved_org_id = _resolve_org_id(org_id)
    clauses = ["cp.org_id = %s", "cp.tripulante_id = %s"]
    params: list = [resolved_org_id, int(tripulante_id)]
    if competencia:
        clauses.append("cp.competencia = %s")
        params.append(competencia)
    if funcao:
        clauses.append("cp.funcao = %s")
        params.append(funcao)

    row = db.execute(
        f"""
        SELECT
            cp.*,
            t.nome AS tripulante_nome,
            t.cpf AS tripulante_cpf,
            t.licenca_anac AS tripulante_licenca_anac,
            t.categoria_operacional AS tripulante_categoria_operacional,
            t.elegivel_adicional_excepcional AS tripulante_elegivel_adicional_excepcional,
            t.sdea_ativo AS tripulante_sdea_ativo,
            t.sdea_icao_validade AS tripulante_sdea_icao_validade,
            t.instrutor_ativo AS tripulante_instrutor_ativo,
            t.instrutor_inicio AS tripulante_instrutor_inicio,
            t.instrutor_fim AS tripulante_instrutor_fim,
            t.checador_ativo AS tripulante_checador_ativo,
            t.checador_inicio AS tripulante_checador_inicio,
            t.checador_fim AS tripulante_checador_fim,
            t.checador_carta_designacao AS tripulante_checador_carta_designacao
        FROM financeiro_calculos_produtividade cp
        JOIN tripulantes t
          ON t.id = cp.tripulante_id
        WHERE {" AND ".join(clauses)}
        ORDER BY cp.competencia DESC, cp.id DESC
        LIMIT 1
        """,
        tuple(params),
    ).fetchone()
    return _dict_or_none(row)


def listar_participacoes_produtividade_por_competencia(
    db,
    *,
    competencia: str,
    org_id: str | None = None,
) -> list[dict]:
    resolved_org_id = _resolve_org_id(org_id)
    effective_funcao_sql = _effective_crew_function_sql(
        tripulante_id_sql="mt.tripulante_id",
        reference_date_sql="mo.data_missao",
        fallback_funcao_sql="""
        CASE
            WHEN LOWER(TRIM(COALESCE(t.funcao_operacional, ''))) IN ('comandante', 'copiloto')
                THEN LOWER(TRIM(t.funcao_operacional))
            ELSE LOWER(TRIM(mt.funcao))
        END
        """,
    )
    effective_categoria_sql = _effective_crew_category_sql(
        tripulante_id_sql="mt.tripulante_id",
        reference_date_sql="mo.data_missao",
    )
    rows = db.execute(
        f"""
        SELECT
            mo.id AS missao_operacional_id,
            mo.org_id,
            mo.competencia,
            mo.data_missao,
            mo.data_final,
            mo.cavok_numero_voo,
            mo.contratante,
            mo.chamado,
            mo.aeronave_id,
            e.nome AS aeronave_nome,
            mo.categoria_financeira_aeronave,
            mo.trecho,
            mo.houve_pernoite,
            mo.quantidade_pernoites,
            mo.cobertura_base AS missao_cobertura_base,
            mt.cobertura_base AS cobertura_base,
            mo.operacao_especial,
            mo.justificativa,
            mo.status AS missao_status,
            mt.tripulante_id,
            mt.funcao AS funcao_missao,
            {effective_funcao_sql} AS funcao,
            mt.status AS participante_status,
            t.nome AS tripulante_nome,
            t.cpf AS tripulante_cpf,
            t.licenca_anac AS tripulante_licenca_anac,
            t.funcao_operacional AS tripulante_funcao_operacional,
            {effective_categoria_sql} AS tripulante_categoria_operacional,
            t.elegivel_adicional_excepcional AS tripulante_elegivel_adicional_excepcional,
            t.sdea_ativo AS tripulante_sdea_ativo,
            t.sdea_icao_validade AS tripulante_sdea_icao_validade,
            t.instrutor_ativo AS tripulante_instrutor_ativo,
            t.instrutor_inicio AS tripulante_instrutor_inicio,
            t.instrutor_fim AS tripulante_instrutor_fim,
            t.checador_ativo AS tripulante_checador_ativo,
            t.checador_inicio AS tripulante_checador_inicio,
            t.checador_fim AS tripulante_checador_fim,
            t.checador_carta_designacao AS tripulante_checador_carta_designacao
        FROM financeiro_missao_tripulantes mt
        JOIN financeiro_missoes_operacionais mo
          ON mo.id = mt.missao_operacional_id
         AND mo.org_id = mt.org_id
        LEFT JOIN equipamentos e
          ON e.id = mo.aeronave_id
        JOIN tripulantes t
          ON t.id = mt.tripulante_id
        WHERE mt.org_id = %s
          AND mo.competencia = %s
          AND mt.status = 'ativo'
          AND mo.status <> 'cancelada'
          AND mo.deleted_at IS NULL
        ORDER BY t.nome ASC, funcao ASC, mo.data_missao ASC, mo.id ASC
        """,
        (resolved_org_id, competencia),
    ).fetchall()
    return [dict(row) for row in rows]


def listar_periodos_ferias_produtividade(
    db,
    *,
    competencia: str,
    org_id: str | None = None,
) -> dict[int, list[dict]]:
    resolved_org_id = _resolve_org_id(org_id)
    competencia_inicio, competencia_fim = _month_bounds(competencia)
    columns = _table_columns(db, "tripulante_periodos_operacionais")
    required_columns = {"tripulante_id", "tipo", "data_inicio", "data_fim"}
    if not required_columns.issubset(columns):
        return {}

    select_columns = [
        "tpo.id" if "id" in columns else "NULL AS id",
        "tpo.tripulante_id",
        "tpo.tipo",
        "tpo.data_inicio",
        "tpo.data_fim",
        "tpo.status" if "status" in columns else "'confirmado' AS status",
        "tpo.org_id" if "org_id" in columns else "NULL AS org_id",
    ]
    where_clauses = [
        "LOWER(TRIM(COALESCE(tpo.tipo, ''))) IN ('ferias', 'férias')",
        "tpo.data_inicio <= %s",
        "COALESCE(tpo.data_fim, tpo.data_inicio) >= %s",
    ]
    params: list = [competencia_fim, competencia_inicio]
    if "status" in columns:
        where_clauses.append(
            "LOWER(TRIM(COALESCE(tpo.status, 'confirmado'))) NOT IN ('cancelado', 'cancelada', 'cancelled', 'inativo', 'inativa')"
        )
    if "org_id" in columns:
        where_clauses.insert(0, "tpo.org_id = %s")
        params.insert(0, resolved_org_id)
    order_columns = ["tpo.tripulante_id ASC", "tpo.data_inicio ASC"]
    if "id" in columns:
        order_columns.append("tpo.id ASC")

    rows = db.execute(
        f"""
        SELECT {", ".join(select_columns)}
        FROM tripulante_periodos_operacionais tpo
        WHERE {" AND ".join(where_clauses)}
        ORDER BY {", ".join(order_columns)}
        """,
        tuple(params),
    ).fetchall()
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        payload = dict(row)
        tripulante_id = payload.get("tripulante_id")
        if tripulante_id in (None, ""):
            continue
        grouped.setdefault(int(tripulante_id), []).append(payload)
    return grouped


def listar_tripulantes_elegiveis_produtividade(
    db,
    *,
    org_id: str | None = None,
    competencia: str | None = None,
) -> list[dict]:
    _resolve_org_id(org_id)
    params: list = []
    context_sql = ""
    context_join_sql = ""
    reference_date_sql = "CURRENT_DATE"
    if competencia:
        _, competencia_fim = _month_bounds(competencia)
        params.append(competencia_fim)
        context_sql = "WITH produtividade_contexto AS (SELECT %s::date AS data_referencia)"
        context_join_sql = "CROSS JOIN produtividade_contexto pc"
        reference_date_sql = "pc.data_referencia"
    effective_funcao_sql = _effective_crew_function_sql(
        tripulante_id_sql="t.id",
        reference_date_sql=reference_date_sql,
        fallback_funcao_sql="""
        CASE
            WHEN LOWER(TRIM(COALESCE(t.funcao_operacional, ''))) IN ('comandante', 'copiloto')
                THEN LOWER(TRIM(t.funcao_operacional))
            ELSE ''
        END
        """,
    )
    effective_categoria_sql = _effective_crew_category_sql(
        tripulante_id_sql="t.id",
        reference_date_sql=reference_date_sql,
    )
    rows = db.execute(
        f"""
        {context_sql}
        SELECT
            t.id AS tripulante_id,
            t.nome AS tripulante_nome,
            t.cpf AS tripulante_cpf,
            t.licenca_anac AS tripulante_licenca_anac,
            {effective_funcao_sql} AS funcao,
            {effective_categoria_sql} AS tripulante_categoria_operacional,
            t.elegivel_adicional_excepcional AS tripulante_elegivel_adicional_excepcional,
            t.sdea_ativo AS tripulante_sdea_ativo,
            t.sdea_icao_validade AS tripulante_sdea_icao_validade,
            t.instrutor_ativo AS tripulante_instrutor_ativo,
            t.instrutor_inicio AS tripulante_instrutor_inicio,
            t.instrutor_fim AS tripulante_instrutor_fim,
            t.checador_ativo AS tripulante_checador_ativo,
            t.checador_inicio AS tripulante_checador_inicio,
            t.checador_fim AS tripulante_checador_fim,
            t.checador_carta_designacao AS tripulante_checador_carta_designacao
        FROM tripulantes t
        {context_join_sql}
        WHERE COALESCE(t.ativo, 1) = 1
          AND {effective_funcao_sql} IN ('comandante', 'copiloto')
          AND (
              LOWER(REPLACE(REPLACE(TRIM(COALESCE({effective_categoria_sql}, '')), '_', ' '), '-', ' ')) IN (
                  'a',
                  'b',
                  'categoria a',
                  'categoria b'
              )
              OR COALESCE(t.elegivel_adicional_excepcional, 0) <> 0
          )
        ORDER BY t.nome ASC, t.id ASC
        """,
        tuple(params),
    ).fetchall()
    return [dict(row) for row in rows]
