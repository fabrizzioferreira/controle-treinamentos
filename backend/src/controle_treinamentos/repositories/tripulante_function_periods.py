from __future__ import annotations


def tripulante_exists(db, *, tripulante_id: int) -> bool:
    return bool(db.execute("SELECT id FROM tripulantes WHERE id = %s", (int(tripulante_id),)).fetchone())


def fetch_function_periods_by_tripulante(db, *, tripulante_id: int) -> list[dict]:
    rows = db.execute(
        """
        SELECT *
        FROM tripulante_funcoes_operacionais_vigencias
        WHERE tripulante_id = %s
        ORDER BY data_inicio DESC, id DESC
        """,
        (int(tripulante_id),),
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_function_period(db, *, tripulante_id: int, vigencia_id: int) -> dict | None:
    row = db.execute(
        """
        SELECT *
        FROM tripulante_funcoes_operacionais_vigencias
        WHERE tripulante_id = %s
          AND id = %s
        """,
        (int(tripulante_id), int(vigencia_id)),
    ).fetchone()
    return dict(row) if row else None


def fetch_function_period_for_date(db, *, tripulante_id: int, data_referencia: str) -> dict | None:
    execute = getattr(db, "execute", None)
    if execute is None:
        return None
    try:
        row = execute(
            """
            SELECT *
            FROM tripulante_funcoes_operacionais_vigencias
            WHERE tripulante_id = %s
              AND status = 'ativo'
              AND data_inicio <= %s::date
              AND (data_fim IS NULL OR data_fim >= %s::date)
            ORDER BY data_inicio DESC, id DESC
            LIMIT 1
            """,
            (int(tripulante_id), data_referencia, data_referencia),
        ).fetchone()
    except Exception:
        return None
    return dict(row) if row else None


def find_overlapping_function_period(
    db,
    *,
    tripulante_id: int,
    data_inicio: str,
    data_fim: str | None,
) -> dict | None:
    row = db.execute(
        """
        SELECT *
        FROM tripulante_funcoes_operacionais_vigencias
        WHERE tripulante_id = %s
          AND status <> 'cancelado'
          AND data_inicio <= COALESCE(%s::date, '9999-12-31'::date)
          AND COALESCE(data_fim, '9999-12-31'::date) >= %s::date
        ORDER BY data_inicio DESC, id DESC
        LIMIT 1
        """,
        (int(tripulante_id), data_fim, data_inicio),
    ).fetchone()
    return dict(row) if row else None


def insert_function_period(db, *, data: dict) -> dict:
    row = db.execute(
        """
        INSERT INTO tripulante_funcoes_operacionais_vigencias (
            tripulante_id,
            funcao_operacional,
            categoria_operacional,
            data_inicio,
            data_fim,
            observacao,
            criado_por
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (
            int(data["tripulante_id"]),
            data["funcao_operacional"],
            data.get("categoria_operacional"),
            data["data_inicio"],
            data.get("data_fim"),
            data.get("observacao") or "",
            data.get("criado_por"),
        ),
    ).fetchone()
    return dict(row)


def cancel_function_period(db, *, tripulante_id: int, vigencia_id: int, cancelado_por: int | None) -> dict | None:
    row = db.execute(
        """
        UPDATE tripulante_funcoes_operacionais_vigencias
        SET status = 'cancelado',
            cancelado_por = %s,
            cancelado_em = CURRENT_TIMESTAMP,
            motivo_status = COALESCE(motivo_status, 'Cancelado via API.')
        WHERE tripulante_id = %s
          AND id = %s
          AND status <> 'cancelado'
        RETURNING *
        """,
        (cancelado_por, int(tripulante_id), int(vigencia_id)),
    ).fetchone()
    return dict(row) if row else None
