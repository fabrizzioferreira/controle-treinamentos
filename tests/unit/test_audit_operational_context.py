import json

from flask import Flask, g

from backend.src.controle_treinamentos.audit import record_audit_event
from backend.src.controle_treinamentos.blueprints.auth import routes as auth_routes


class _AuditCursor:
    rowcount = 1


class _AuditDB:
    def __init__(self):
        self.calls = []
        self.committed = False
        self.conn = self
        self.rolled_back = False

    def execute(self, query, params=()):
        self.calls.append((query, params))
        return _AuditCursor()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def _insert_params(db: _AuditDB):
    for query, params in db.calls:
        if "INSERT INTO auditoria_eventos" in " ".join(query.split()):
            return params
    raise AssertionError("audit insert was not recorded")


def test_record_audit_event_adds_request_context_checksum_result_and_masks_sensitive_payload():
    app = Flask(__name__)
    db = _AuditDB()

    with app.test_request_context(
        "/api/v1/financeiro/missoes/10/recalcular",
        method="POST",
        headers={
            "X-Request-ID": "req-audit-1",
            "X-Correlation-ID": "corr-audit-1",
            "User-Agent": "AuditTest/1.0",
            "X-Forwarded-For": "203.0.113.10, 10.0.0.1",
        },
    ):
        g.request_id = "req-audit-1"
        g.correlation_id = "corr-audit-1"
        record_audit_event(
            db,
            entidade="finance_mission",
            entidade_id=10,
            acao="finance.mission.recalculated",
            realizado_por=7,
            payload_novo={
                "email": "operador.auditavel@example.com",
                "senha": "never-store-me",
                "sha256": "abc123",
                "audit_metadata": {
                    "event_name": "finance.mission.recalculated",
                    "request_id": "",
                    "correlation_id": None,
                    "source_endpoint": "",
                },
            },
            observacao="unit-test",
        )

    params = _insert_params(db)
    payload_novo = json.loads(params[4])
    metadata = payload_novo["audit_metadata"]

    assert payload_novo["email"] == "o***@example.com"
    assert payload_novo["senha"] == "<redacted>"
    assert metadata["event_name"] == "finance.mission.recalculated"
    assert metadata["request_id"] == "req-audit-1"
    assert metadata["correlation_id"] == "corr-audit-1"
    assert metadata["source_path"] == "/api/v1/financeiro/missoes/10/recalcular"
    assert metadata["http_method"] == "POST"
    assert metadata["ip_address"] == "203.0.113.10"
    assert metadata["user_agent"] == "AuditTest/1.0"
    assert metadata["result"] == "success"
    assert metadata["success"] is True
    assert metadata["checksum"] == "abc123"


def test_record_audit_event_creates_metadata_payload_when_no_before_or_after_payload_exists():
    db = _AuditDB()

    record_audit_event(
        db,
        entidade="background_job",
        entidade_id=44,
        acao="background_job.requeue_dead_letter",
        realizado_por=9,
        resultado="success",
        origem="ops.jobs",
    )

    params = _insert_params(db)
    assert params[3] is None
    payload_novo = json.loads(params[4])
    assert payload_novo == {
        "audit_metadata": {
            "audit_envelope_version": "audit-context-v1",
            "result": "success",
            "success": True,
            "origin": "ops.jobs",
        }
    }


def test_auth_audit_event_uses_masked_login_hint_and_request_metadata(monkeypatch):
    app = Flask(__name__)
    app.config.update(DATABASE_URL="postgresql://audit-fake", AUDIT_STRICT_MODE=True)
    db = _AuditDB()
    monkeypatch.setattr(auth_routes, "get_db", lambda: db)

    with app.test_request_context(
        "/api/v1/session/login",
        method="POST",
        headers={
            "X-Request-ID": "req-auth-1",
            "X-Correlation-ID": "corr-auth-1",
            "User-Agent": "AuthAudit/1.0",
        },
    ):
        g.request_id = "req-auth-1"
        g.correlation_id = "corr-auth-1"
        recorded = auth_routes._record_auth_audit_event(
            event_name="auth.login.failed",
            user_id=12,
            login_value="operador@example.com",
            status=401,
            result="failure",
            channel="api",
            reason="invalid_credentials",
        )

    assert recorded is True
    assert db.committed is True
    params = _insert_params(db)
    payload_novo = json.loads(params[4])
    metadata = payload_novo["audit_metadata"]

    assert params[0] == "auth_session"
    assert params[1] == 12
    assert params[2] == "auth.login.failed"
    assert params[5] == 12
    assert payload_novo["auth"]["login_hint"] == "o***@example.com"
    assert "operador@example.com" not in json.dumps(payload_novo)
    assert payload_novo["auth"]["reason"] == "invalid_credentials"
    assert metadata["request_id"] == "req-auth-1"
    assert metadata["correlation_id"] == "corr-auth-1"
    assert metadata["origin"] == "auth.api"
    assert metadata["result"] == "failure"
    assert metadata["success"] is False
