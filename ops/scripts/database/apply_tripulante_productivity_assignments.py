from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import psycopg2
import psycopg2.extras


@dataclass(frozen=True)
class Assignment:
    key: str
    label: str
    match_tokens: tuple[str, ...]
    funcao_operacional: str
    categoria_operacional: str
    data_inicio: date


ASSIGNMENTS = (
    Assignment(
        key="fabrizzio",
        label="Fabrizzio",
        match_tokens=("fabrizzio",),
        funcao_operacional="copiloto",
        categoria_operacional="A",
        data_inicio=date(2026, 8, 27),
    ),
    Assignment(
        key="agnello",
        label="Agnello",
        match_tokens=("agnello",),
        funcao_operacional="comandante",
        categoria_operacional="A",
        data_inicio=date(2026, 8, 29),
    ),
    Assignment(
        key="vitor_avila",
        label="Vitor Avila",
        match_tokens=("vitor", "avila"),
        funcao_operacional="copiloto",
        categoria_operacional="B",
        data_inicio=date(2026, 8, 21),
    ),
)


def _load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _database_url(args: argparse.Namespace) -> str:
    if args.database_url:
        return str(args.database_url).strip()
    env = _load_env_file(Path(args.env_file))
    return (env.get("DATABASE_URL") or os.getenv("DATABASE_URL") or "").strip()


def _normalize_text(value: str | None) -> str:
    raw = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(char for char in raw if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents).strip().lower()


def _fetch_active_tripulantes(cur) -> list[dict]:
    cur.execute(
        """
        SELECT id, nome, funcao_operacional, categoria_operacional, ativo
        FROM tripulantes
        WHERE COALESCE(ativo, 1) = 1
        ORDER BY nome ASC, id ASC
        """
    )
    return [dict(row) for row in cur.fetchall()]


def _fetch_periods(cur, *, tripulante_id: int) -> list[dict]:
    cur.execute(
        """
        SELECT
            id,
            funcao_operacional,
            categoria_operacional,
            data_inicio,
            data_fim,
            status
        FROM tripulante_funcoes_operacionais_vigencias
        WHERE tripulante_id = %s
        ORDER BY data_inicio DESC, id DESC
        """,
        (int(tripulante_id),),
    )
    return [dict(row) for row in cur.fetchall()]


def _iso_date(value) -> str | None:
    if value in (None, ""):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)[:10]


def _date_value(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _period_payload(row: dict) -> dict:
    return {
        "id": int(row["id"]),
        "funcao_operacional": row.get("funcao_operacional"),
        "categoria_operacional": row.get("categoria_operacional"),
        "data_inicio": _iso_date(row.get("data_inicio")),
        "data_fim": _iso_date(row.get("data_fim")),
        "status": row.get("status"),
    }


def _period_overlaps_start(row: dict, data_inicio: date) -> bool:
    period_start = _date_value(row.get("data_inicio"))
    period_end = _date_value(row.get("data_fim"))
    return period_start is not None and period_start <= data_inicio and (period_end is None or period_end >= data_inicio)


def _matches_assignment(row: dict, assignment: Assignment) -> bool:
    normalized = _normalize_text(row.get("nome"))
    return all(token in normalized for token in assignment.match_tokens)


def _build_plan(cur, assignments: tuple[Assignment, ...]) -> list[dict]:
    tripulantes = _fetch_active_tripulantes(cur)
    plan = []
    for assignment in assignments:
        matches = [row for row in tripulantes if _matches_assignment(row, assignment)]
        item = {
            "assignment": assignment.key,
            "label": assignment.label,
            "funcao_operacional": assignment.funcao_operacional,
            "categoria_operacional": assignment.categoria_operacional,
            "data_inicio": assignment.data_inicio.isoformat(),
            "matched_tripulantes": [
                {"id": int(row["id"]), "nome": row.get("nome")}
                for row in matches
            ],
        }
        if not matches:
            plan.append({**item, "status": "missing_tripulante"})
            continue
        if len(matches) > 1:
            plan.append({**item, "status": "ambiguous_tripulante"})
            continue

        tripulante = matches[0]
        periods = _fetch_periods(cur, tripulante_id=int(tripulante["id"]))
        exact = [
            row
            for row in periods
            if row.get("status") == "ativo"
            and row.get("funcao_operacional") == assignment.funcao_operacional
            and row.get("categoria_operacional") == assignment.categoria_operacional
            and _iso_date(row.get("data_inicio")) == assignment.data_inicio.isoformat()
            and row.get("data_fim") in (None, "")
        ]
        if exact:
            plan.append(
                {
                    **item,
                    "status": "already_applied",
                    "tripulante_id": int(tripulante["id"]),
                    "existing_period": _period_payload(exact[0]),
                }
            )
            continue

        overlaps = [
            row
            for row in periods
            if row.get("status") == "ativo"
            and _period_overlaps_start(row, assignment.data_inicio)
        ]
        if overlaps:
            plan.append(
                {
                    **item,
                    "status": "blocked_overlap",
                    "tripulante_id": int(tripulante["id"]),
                    "overlapping_periods": [_period_payload(row) for row in overlaps],
                }
            )
            continue

        plan.append({**item, "status": "ready", "tripulante_id": int(tripulante["id"])})
    return plan


def _apply_ready_items(cur, plan: list[dict], *, actor_user_id: int, update_cadastro: bool) -> list[dict]:
    applied = []
    for item in plan:
        if item["status"] != "ready":
            continue
        cur.execute(
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
            VALUES (%s, %s, %s, %s, NULL, %s, %s)
            RETURNING id
            """,
            (
                int(item["tripulante_id"]),
                item["funcao_operacional"],
                item["categoria_operacional"],
                item["data_inicio"],
                f"Ajuste de produtividade por vigencia: {item['label']}",
                int(actor_user_id),
            ),
        )
        period_id = int(cur.fetchone()["id"])
        if update_cadastro:
            cur.execute(
                """
                UPDATE tripulantes
                SET funcao_operacional = %s,
                    categoria_operacional = %s
                WHERE id = %s
                """,
                (
                    item["funcao_operacional"],
                    item["categoria_operacional"],
                    int(item["tripulante_id"]),
                ),
            )
        applied.append({**item, "status": "applied", "period_id": period_id})
    return applied


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aplica vigencias de funcao/categoria para bonus de produtividade de tripulantes."
    )
    parser.add_argument("--env-file", default=".env", help="Arquivo com DATABASE_URL quando --database-url nao for usado.")
    parser.add_argument("--database-url", default="", help="DATABASE_URL explicita. Nao sera impressa.")
    parser.add_argument("--actor-user-id", type=int, default=1, help="Usuario registrado em criado_por.")
    parser.add_argument("--apply", action="store_true", help="Aplica o plano. Sem esta flag, roda em dry-run.")
    parser.add_argument(
        "--skip-cadastro-update",
        action="store_true",
        help="Nao atualiza funcao/categoria cadastral corrente dos tripulantes encontrados.",
    )
    args = parser.parse_args()

    database_url = _database_url(args)
    if not database_url:
        raise SystemExit("DATABASE_URL ausente. Informe --database-url, --env-file ou a variavel DATABASE_URL.")

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT current_database() AS database, current_user AS user")
        meta = dict(cur.fetchone())
        plan = _build_plan(cur, ASSIGNMENTS)
        blockers = [item for item in plan if item["status"] not in {"ready", "already_applied"}]
        applied = []
        if args.apply:
            if blockers:
                conn.rollback()
                print(
                    json.dumps(
                        {
                            "applied": False,
                            "database": meta,
                            "reason": "blocked_plan",
                            "plan": plan,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 2
            applied = _apply_ready_items(
                cur,
                plan,
                actor_user_id=int(args.actor_user_id),
                update_cadastro=not args.skip_cadastro_update,
            )
            conn.commit()
        else:
            conn.rollback()

        print(
            json.dumps(
                {
                    "applied": bool(args.apply),
                    "database": meta,
                    "generated_at": datetime.utcnow().replace(microsecond=0).isoformat(),
                    "plan": plan,
                    "applied_items": applied,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
