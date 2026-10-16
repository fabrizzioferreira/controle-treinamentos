from __future__ import annotations

import hashlib
import json
import os
import unicodedata

from flask import current_app
from werkzeug.security import generate_password_hash

from ..core.sistema_controle_policy import SISTEMA_CONTROLE_NOTIFICATION_KEYS
from .connection import get_db
from .schema_bootstrap import execute_schema_bootstrap

BASES_SEED = [
    ("BelÃ©m", "PA", -1.4558, -48.4902, True),
    ("Manaus", "AM", -3.1190, -60.0217, True),
    ("Salvador", "BA", -12.9777, -38.5016, True),
    ("GoiÃ¢nia", "GO", -16.6869, -49.2648, True),
    ("Palmas", "TO", -10.2491, -48.3243, True),
    ("SantarÃ©m", "PA", -2.4385, -54.6996, True),
    ("SÃ£o Paulo", "SP", -23.5505, -46.6333, True),
]


_JORNADA_REGULAMENTAR_SIMPLES_DEFAULT = (
    ("00:00", "09:38"), ("00:15", "09:55"), ("00:30", "10:12"), ("00:45", "10:30"),
    ("01:00", "10:47"), ("01:15", "11:04"), ("01:30", "11:21"), ("01:45", "11:38"),
    ("02:00", "11:55"), ("02:15", "12:12"), ("02:30", "12:30"), ("02:45", "12:47"),
    ("03:00", "13:04"), ("03:15", "13:21"), ("03:30", "13:38"), ("03:45", "13:55"),
    ("04:00", "14:12"), ("04:15", "14:30"), ("04:30", "14:47"), ("04:45", "15:04"),
    ("05:00", "15:21"), ("05:15", "15:38"), ("05:30", "15:55"), ("05:45", "16:12"),
    ("06:00", "16:30"), ("06:15", "16:45"), ("06:30", "17:00"), ("06:45", "17:15"),
    ("07:00", "17:30"), ("07:15", "17:43"), ("07:30", "17:56"), ("07:45", "18:09"),
    ("08:00", "18:22"), ("08:15", "18:35"), ("08:30", "18:48"), ("08:45", "19:01"),
    ("09:00", "19:15"), ("09:15", "19:28"), ("09:30", "19:41"), ("09:45", "19:54"),
    ("10:00", "20:07"), ("10:15", "20:20"), ("10:30", "20:33"), ("10:45", "20:46"),
    ("11:00", "21:00"), ("11:15", "21:13"), ("11:30", "21:26"), ("11:45", "21:39"),
    ("12:00", "21:52"), ("12:15", "22:05"), ("12:30", "22:18"), ("12:45", "22:31"),
    ("13:00", "22:45"), ("13:15", "22:58"), ("13:30", "23:11"), ("13:45", "23:24"),
    ("14:00", "23:37"), ("14:15", "23:50"), ("14:30", "00:03"), ("14:45", "00:16"),
    ("15:00", "00:30"), ("15:15", "00:43"), ("15:30", "00:56"), ("15:45", "01:09"),
    ("16:00", "01:22"), ("16:15", "01:35"), ("16:30", "01:48"), ("16:45", "02:01"),
    ("17:00", "02:15"), ("17:15", "02:28"), ("17:30", "02:41"), ("17:45", "02:54"),
    ("18:00", "03:07"), ("18:15", "03:22"), ("18:30", "03:37"), ("18:45", "03:52"),
    ("19:00", "04:07"), ("19:15", "04:22"), ("19:30", "04:37"), ("19:45", "04:52"),
    ("20:00", "05:07"), ("20:15", "05:22"), ("20:30", "05:38"), ("20:45", "05:55"),
    ("21:00", "06:12"), ("21:15", "06:30"), ("21:30", "06:47"), ("21:45", "07:04"),
    ("22:00", "07:21"), ("22:15", "07:38"), ("22:30", "07:55"), ("22:45", "08:12"),
    ("23:00", "08:30"), ("23:15", "08:47"), ("23:30", "09:04"), ("23:45", "09:21"),
)


def _jornada_tabela_regulamentar_default_json() -> str:
    table = dict(_JORNADA_REGULAMENTAR_SIMPLES_DEFAULT)
    return json.dumps(table, ensure_ascii=True, separators=(",", ":"))


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _normalize_base_key(name: str) -> str:
    compact = " ".join((name or "").strip().split())
    return _strip_accents(compact).lower()


def _canonical_base_name(name: str) -> str:
    cleaned_name = " ".join((name or "").strip().split())
    if not cleaned_name:
        return ""
    for seed_name, _uf, _latitude, _longitude, _ativa in BASES_SEED:
        if _normalize_base_key(seed_name) == _normalize_base_key(cleaned_name):
            return seed_name
    return cleaned_name


def _fallback_base_metadata(name: str):
    normalized = _normalize_base_key(name)
    digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
    lat_seed = int(digest[:8], 16)
    lon_seed = int(digest[8:16], 16)
    latitude = -30 + ((lat_seed / 0xFFFFFFFF) * 34)
    longitude = -70 + ((lon_seed / 0xFFFFFFFF) * 36)
    return "--", round(latitude, 4), round(longitude, 4), True


def ensure_base_exists(db, base_name: str | None):
    cleaned_name = _canonical_base_name(base_name or "")
    if not cleaned_name:
        return None

    existing_rows = db.execute(
        "SELECT id, nome, uf, latitude, longitude, ativa FROM bases ORDER BY ativa DESC, nome",
    ).fetchall()
    normalized_key = _normalize_base_key(cleaned_name)
    for row in existing_rows:
        if _normalize_base_key(row["nome"]) == normalized_key:
            if row["nome"] != cleaned_name and cleaned_name in {item[0] for item in BASES_SEED}:
                db.execute(
                    """
                    UPDATE tripulantes
                    SET base = %s
                    WHERE LOWER(TRIM(base)) = LOWER(%s)
                    """,
                    (cleaned_name, row["nome"]),
                )
            return row

    known_map = {_normalize_base_key(item[0]): item for item in BASES_SEED}
    known = known_map.get(normalized_key)
    if known:
        _, uf, latitude, longitude, ativa = known
    else:
        uf, latitude, longitude, ativa = _fallback_base_metadata(cleaned_name)
    created = db.execute(
        """
        INSERT INTO bases (nome, uf, latitude, longitude, ativa)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, nome, uf, latitude, longitude, ativa
        """,
        (cleaned_name, uf, latitude, longitude, ativa),
    ).fetchone()
    return created


def sync_tripulante_bases(db):
    rows = db.execute(
        """
        SELECT DISTINCT base
        FROM tripulantes
        WHERE TRIM(COALESCE(base, '')) != ''
        ORDER BY base
        """
    ).fetchall()
    for row in rows:
        canonical_name = _canonical_base_name(row["base"])
        if canonical_name and canonical_name != row["base"]:
            db.execute("UPDATE tripulantes SET base = %s WHERE base = %s", (canonical_name, row["base"]))
        ensure_base_exists(db, canonical_name)


def normalize_tripulante_statuses(db):
    db.execute(
        """
        UPDATE tripulantes
        SET status = CASE
            WHEN LOWER(TRIM(COALESCE(status, ''))) = 'ativo' THEN 'Ativo'
            WHEN LOWER(TRIM(COALESCE(status, ''))) = 'folga' THEN 'Folga'
            WHEN LOWER(TRIM(COALESCE(status, ''))) IN ('ferias', 'fÃ©rias') THEN 'FÃ©rias'
            WHEN LOWER(TRIM(COALESCE(status, ''))) = 'atestado' THEN 'Atestado'
            WHEN LOWER(TRIM(COALESCE(status, ''))) = 'afastado' THEN 'Afastado'
            WHEN LOWER(TRIM(COALESCE(status, ''))) = 'treinamento' THEN 'Treinamento'
            ELSE status
        END
        """
    )
    db.execute(
        """
        UPDATE tripulantes
        SET status = 'Ativo'
        WHERE TRIM(COALESCE(status, '')) = ''
        """
    )


def sync_duplicate_bases(db):
    rows = db.execute(
        """
        SELECT id, nome, uf, latitude, longitude, ativa
        FROM bases
        ORDER BY ativa DESC, nome, id
        """
    ).fetchall()
    grouped = {}
    seed_names = {item[0] for item in BASES_SEED}

    for row in rows:
        key = _normalize_base_key(row["nome"])
        current = grouped.get(key)
        if current is None:
            grouped[key] = row
            continue
        current_is_seed = current["nome"] in seed_names
        row_is_seed = row["nome"] in seed_names
        if row_is_seed and not current_is_seed:
            grouped[key] = row

    for row in rows:
        key = _normalize_base_key(row["nome"])
        canonical = grouped[key]
        if row["id"] == canonical["id"]:
            if not canonical["ativa"]:
                db.execute("UPDATE bases SET ativa = TRUE WHERE id = %s", (canonical["id"],))
            continue
        db.execute("UPDATE pilotos SET base_id = %s WHERE base_id = %s", (canonical["id"], row["id"]))
        db.execute("UPDATE historico_status_piloto SET base_anterior_id = %s WHERE base_anterior_id = %s", (canonical["id"], row["id"]))
        db.execute("UPDATE historico_status_piloto SET base_nova_id = %s WHERE base_nova_id = %s", (canonical["id"], row["id"]))
        db.execute("UPDATE bases SET ativa = FALSE WHERE id = %s", (row["id"],))


def sync_tripulantes_to_pilotos(db):
    db.execute(
        """
        UPDATE pilotos p
        SET
            nome = t.nome
        FROM tripulantes t
        WHERE p.tripulante_id = t.id
        """
    )
    db.execute(
        """
        INSERT INTO pilotos (nome, matricula, tripulante_id, base_id, status)
        SELECT
            t.nome,
            t.licenca_anac,
            t.id,
            b.id,
            CASE LOWER(TRIM(t.status))
                WHEN 'ativo' THEN 'ativo'
                WHEN 'folga' THEN 'folga'
                WHEN 'fÃ©rias' THEN 'ferias'
                WHEN 'ferias' THEN 'ferias'
                WHEN 'atestado' THEN 'atestado'
                WHEN 'afastado' THEN 'afastado'
                WHEN 'treinamento' THEN 'treinamento'
                ELSE 'ativo'
            END
        FROM tripulantes t
        JOIN bases b ON LOWER(TRIM(b.nome)) = LOWER(TRIM(t.base))
        LEFT JOIN pilotos p ON p.tripulante_id = t.id
        LEFT JOIN pilotos pm ON pm.matricula = t.licenca_anac AND pm.tripulante_id IS DISTINCT FROM t.id
        WHERE p.id IS NULL
          AND TRIM(COALESCE(t.licenca_anac, '')) != ''
          AND pm.id IS NULL
        """
    )
    db.execute(
        """
        INSERT INTO pilotos (nome, matricula, tripulante_id, base_id, status)
        SELECT
            t.nome,
            CONCAT('TRIP-', LPAD(t.id::text, 6, '0')),
            t.id,
            b.id,
            CASE LOWER(TRIM(t.status))
                WHEN 'ativo' THEN 'ativo'
                WHEN 'folga' THEN 'folga'
                WHEN 'fÃ©rias' THEN 'ferias'
                WHEN 'ferias' THEN 'ferias'
                WHEN 'atestado' THEN 'atestado'
                WHEN 'afastado' THEN 'afastado'
                WHEN 'treinamento' THEN 'treinamento'
                ELSE 'ativo'
            END
        FROM tripulantes t
        JOIN bases b ON LOWER(TRIM(b.nome)) = LOWER(TRIM(t.base))
        LEFT JOIN pilotos p ON p.tripulante_id = t.id
        LEFT JOIN pilotos pm
            ON pm.matricula = CONCAT('TRIP-', LPAD(t.id::text, 6, '0'))
           AND pm.tripulante_id IS DISTINCT FROM t.id
        WHERE p.id IS NULL
          AND pm.id IS NULL
        """
    )


def fetch_unique_bases(db, include_name: str | None = None):
    selected_canonical = _canonical_base_name(include_name or "")
    rows = db.execute(
        """
        SELECT id, nome, uf, latitude, longitude, ativa
        FROM bases
        ORDER BY ativa DESC, nome
        """
    ).fetchall()
    unique_rows = {}
    for row in rows:
        if not row["ativa"] and _normalize_base_key(row["nome"]) != _normalize_base_key(selected_canonical):
            continue
        key = _normalize_base_key(row["nome"])
        current = unique_rows.get(key)
        if current is None:
            unique_rows[key] = row
            continue
        current_is_seed = any(_normalize_base_key(item[0]) == key and item[0] == current["nome"] for item in BASES_SEED)
        row_is_seed = any(_normalize_base_key(item[0]) == key and item[0] == row["nome"] for item in BASES_SEED)
        if row_is_seed and not current_is_seed:
            unique_rows[key] = row
    return sorted(unique_rows.values(), key=lambda item: item["nome"])

def execute_seed_bootstrap(db=None) -> None:
    db = db or get_db()
    execute_schema_bootstrap(db)

    bootstrap_login = os.getenv("BOOTSTRAP_ADMIN_LOGIN", "").strip()
    bootstrap_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "").strip()
    bootstrap_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@interno.local").strip() or "admin@interno.local"
    user_exists = None
    if bootstrap_login:
        user_exists = db.execute("SELECT id FROM usuarios WHERE login = %s", (bootstrap_login,)).fetchone()
    if bootstrap_login and bootstrap_password and not user_exists:
        db.execute(
            """
            INSERT INTO usuarios (nome, login, email, senha_hash, perfil, ativo)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (login) DO NOTHING
            """,
            (
                "Administradora",
                bootstrap_login,
                bootstrap_email,
                generate_password_hash(bootstrap_password, method="pbkdf2:sha256"),
                "gestora",
                1,
            ),
        )

    for key in SISTEMA_CONTROLE_NOTIFICATION_KEYS:
        if key == "notification_last_error":
            continue
        db.execute(
            "INSERT INTO sistema_controle (chave, valor) VALUES (%s, %s) ON CONFLICT (chave) DO NOTHING",
            (key, ""),
        )

    for nome, uf, latitude, longitude, ativa in BASES_SEED:
        db.execute(
            """
            INSERT INTO bases (nome, uf, latitude, longitude, ativa)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (nome)
            DO UPDATE SET
                uf = EXCLUDED.uf,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                ativa = EXCLUDED.ativa
            """,
            (nome, uf, latitude, longitude, ativa),
        )

    normalize_tripulante_statuses(db)
    sync_tripulante_bases(db)
    sync_duplicate_bases(db)
    sync_tripulantes_to_pilotos(db)

    db.commit()


def execute_script() -> None:
    execute_seed_bootstrap()
