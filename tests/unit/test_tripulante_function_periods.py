from __future__ import annotations

import pytest

from backend.src.controle_treinamentos.application import tripulante_function_periods as periods_app
from backend.src.controle_treinamentos.repositories import tripulante_function_periods as periods_repo


class _FakeConn:
    def __init__(self):
        self.rolled_back = False

    def rollback(self):
        self.rolled_back = True


class _FakeDB:
    def __init__(self):
        self.conn = _FakeConn()
        self.committed = False

    def commit(self):
        self.committed = True


class _FakeCursor:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _CaptureDB:
    def __init__(self, row=None, *, fail=False):
        self.row = row
        self.fail = fail
        self.query = ""
        self.params = ()

    def execute(self, query, params=None):
        if self.fail:
            raise RuntimeError("missing table")
        self.query = query
        self.params = params or ()
        return _FakeCursor(self.row)


def test_create_tripulante_function_period_persists_valid_role_period(monkeypatch):
    db = _FakeDB()
    captured = {}

    monkeypatch.setattr(periods_app, "get_db", lambda: db)
    monkeypatch.setattr(periods_app, "tripulante_exists", lambda _db, *, tripulante_id: tripulante_id == 11)
    monkeypatch.setattr(periods_app, "find_overlapping_function_period", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(periods_app, "audit_event", lambda *_args, **_kwargs: None)

    def fake_insert_function_period(_db, *, data):
        captured.update(data)
        return {
            "id": 41,
            "tripulante_id": data["tripulante_id"],
            "funcao_operacional": data["funcao_operacional"],
            "categoria_operacional": data["categoria_operacional"],
            "data_inicio": data["data_inicio"],
            "data_fim": data["data_fim"],
            "status": "ativo",
            "observacao": data["observacao"],
            "criado_em": None,
            "cancelado_em": None,
        }

    monkeypatch.setattr(periods_app, "insert_function_period", fake_insert_function_period)

    result = periods_app.create_tripulante_function_period(
        tripulante_id=11,
        actor_user_id=21,
        payload={
            "funcao_operacional": "cmt",
            "categoria_operacional": "categoria a",
            "data_inicio": "2026-06-24",
            "observacao": "Promocao a comandante",
        },
    )

    assert result["item"]["id"] == 41
    assert result["item"]["funcao_operacional"] == "comandante"
    assert captured["tripulante_id"] == 11
    assert captured["criado_por"] == 21
    assert captured["categoria_operacional"] == "A"
    assert captured["data_inicio"] == "2026-06-24"
    assert captured["data_fim"] is None
    assert db.committed is True
    assert db.conn.rolled_back is False


def test_insert_function_period_uses_database_default_status_and_non_null_observation():
    db = _CaptureDB(
        {
            "id": 41,
            "tripulante_id": 11,
            "funcao_operacional": "comandante",
            "categoria_operacional": "A",
            "data_inicio": "2026-06-24",
            "data_fim": None,
            "status": "ativo",
            "observacao": "",
        }
    )

    result = periods_repo.insert_function_period(
        db,
        data={
            "tripulante_id": 11,
            "funcao_operacional": "comandante",
            "categoria_operacional": "A",
            "data_inicio": "2026-06-24",
            "data_fim": None,
            "observacao": None,
            "criado_por": 21,
        },
    )

    insert_columns = db.query.split(")", 1)[0]
    assert "status" not in insert_columns
    assert db.params == (11, "comandante", "A", "2026-06-24", None, "", 21)
    assert result["status"] == "ativo"


def test_create_tripulante_function_period_rejects_invalid_date_range(monkeypatch):
    db = _FakeDB()
    monkeypatch.setattr(periods_app, "get_db", lambda: db)
    monkeypatch.setattr(periods_app, "tripulante_exists", lambda *_args, **_kwargs: True)

    with pytest.raises(periods_app.TripulanteFunctionPeriodValidationError) as excinfo:
        periods_app.create_tripulante_function_period(
            tripulante_id=11,
            actor_user_id=21,
            payload={"funcao_operacional": "copiloto", "data_inicio": "2026-06-24", "data_fim": "2026-06-23"},
        )

    assert excinfo.value.code == "tripulante_funcao_vigencia_validation_error"
    assert db.committed is False


def test_create_tripulante_function_period_blocks_active_overlap(monkeypatch):
    db = _FakeDB()
    monkeypatch.setattr(periods_app, "get_db", lambda: db)
    monkeypatch.setattr(periods_app, "tripulante_exists", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        periods_app,
        "find_overlapping_function_period",
        lambda *_args, **_kwargs: {"id": 40, "data_inicio": "2026-06-01", "data_fim": None},
    )

    with pytest.raises(periods_app.TripulanteFunctionPeriodConflictError) as excinfo:
        periods_app.create_tripulante_function_period(
            tripulante_id=11,
            actor_user_id=21,
            payload={"funcao_operacional": "comandante", "data_inicio": "2026-06-24"},
        )

    assert excinfo.value.code == "tripulante_funcao_vigencia_overlap"
    assert db.committed is False


def test_function_period_lifecycle_create_list_and_cancel(monkeypatch):
    db = _FakeDB()
    rows = []
    next_id = {"value": 41}

    monkeypatch.setattr(periods_app, "get_db", lambda: db)
    monkeypatch.setattr(periods_app, "tripulante_exists", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(periods_app, "audit_event", lambda *_args, **_kwargs: None)

    def fake_find_overlap(_db, *, tripulante_id, data_inicio, data_fim):
        requested_end = data_fim or "9999-12-31"
        for row in rows:
            row_end = row["data_fim"] or "9999-12-31"
            if (
                row["tripulante_id"] == tripulante_id
                and row["status"] != "cancelado"
                and row["data_inicio"] <= requested_end
                and row_end >= data_inicio
            ):
                return row
        return None

    def fake_insert(_db, *, data):
        row = {
            "id": next_id["value"],
            "tripulante_id": data["tripulante_id"],
            "funcao_operacional": data["funcao_operacional"],
            "categoria_operacional": data["categoria_operacional"],
            "data_inicio": data["data_inicio"],
            "data_fim": data["data_fim"],
            "status": "ativo",
            "observacao": data["observacao"],
            "criado_em": None,
            "cancelado_em": None,
        }
        rows.append(row)
        next_id["value"] += 1
        return row

    def fake_fetch_many(_db, *, tripulante_id):
        return [row for row in rows if row["tripulante_id"] == tripulante_id]

    def fake_fetch_one(_db, *, tripulante_id, vigencia_id):
        return next((row for row in rows if row["tripulante_id"] == tripulante_id and row["id"] == vigencia_id), None)

    def fake_cancel(_db, *, tripulante_id, vigencia_id, cancelado_por):
        row = fake_fetch_one(_db, tripulante_id=tripulante_id, vigencia_id=vigencia_id)
        if not row or row["status"] == "cancelado":
            return None
        row["status"] = "cancelado"
        row["cancelado_por"] = cancelado_por
        row["cancelado_em"] = "2026-06-01T12:00:00"
        return row

    monkeypatch.setattr(periods_app, "find_overlapping_function_period", fake_find_overlap)
    monkeypatch.setattr(periods_app, "insert_function_period", fake_insert)
    monkeypatch.setattr(periods_app, "fetch_function_periods_by_tripulante", fake_fetch_many)
    monkeypatch.setattr(periods_app, "fetch_function_period", fake_fetch_one)
    monkeypatch.setattr(periods_app, "cancel_function_period", fake_cancel)

    created = periods_app.create_tripulante_function_period(
        tripulante_id=11,
        actor_user_id=21,
        payload={
            "funcao_operacional": "copiloto",
            "categoria_operacional": "b",
            "data_inicio": "2026-06-01",
            "data_fim": "2026-06-23",
        },
    )
    listed = periods_app.list_tripulante_function_periods(tripulante_id=11)
    cancelled = periods_app.cancel_tripulante_function_period(
        tripulante_id=11,
        vigencia_id=created["item"]["id"],
        actor_user_id=21,
    )

    assert listed["items"] == [created["item"]]
    assert created["item"]["categoria_operacional"] == "B"
    assert cancelled["operation"] == "cancelled"
    assert cancelled["item"]["status"] == "cancelado"
    assert periods_app.list_tripulante_function_periods(tripulante_id=11)["items"][0]["status"] == "cancelado"


def test_fetch_function_period_for_date_returns_none_when_table_is_missing():
    db = _CaptureDB(fail=True)

    assert (
        periods_repo.fetch_function_period_for_date(
            db,
            tripulante_id=11,
            data_referencia="2026-06-24",
        )
        is None
    )
