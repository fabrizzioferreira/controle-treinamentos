# P0 Finance Preview HTTP Remediation

Data: 2026-06-07

## Falha tratada

`test_preview_endpoint_returns_pending_fields_without_recalculate`

## Causa raiz

O teste de contrato autenticava um usuario fake, mas nao isolava a auditoria estrita do login. No ambiente local, `_record_auth_audit_event()` tentou gravar em `auditoria_eventos` usando o Postgres real e falhou por FK do usuario fake `902`.

No fluxo de preview, tambem havia dependencia indevida de DB para payload incompleto: `preview_missao_operacional()` chamava `_resolve_db()` antes de verificar os campos obrigatorios. O estado `pendente_dados` nao precisa consultar DB, recalcular ou persistir.

## Arquivos alterados

- `backend/src/controle_treinamentos/application/financeiro_missoes.py`
- `tests/contract/test_financeiro_missoes_preview_http.py`
- `docs/release-gates/p0-finance-preview-http-remediation.md`

## Correcao aplicada

- O helper `_authenticate_client()` do teste passou a usar um DB fake para a auditoria de login, mantendo a validacao de usuario fake sem acessar o DB real.
- `preview_missao_operacional()` agora verifica campos obrigatorios e retorna `pendente_dados` antes de resolver DB.

Nao houve alteracao de calculo financeiro, schema, competencia, contrato publico do endpoint, PDF financeiro, fechamento, reabertura, parametros ou permissoes.

## Evidencia antes

```text
.\.venv\Scripts\python.exe -m pytest -q -k test_preview_endpoint_returns_pending_fields_without_recalculate -vv --tb=long
FAILED tests/contract/test_financeiro_missoes_preview_http.py::test_preview_endpoint_returns_pending_fields_without_recalculate
assert 500 == 200
RuntimeError: Falha ao persistir auditoria de autenticação em modo estrito.
psycopg2.errors.ForeignKeyViolation: Key (realizado_por)=(902) is not present in table "usuarios".
```

## Evidencia depois

Teste alvo:

```text
.\.venv\Scripts\python.exe -m pytest -q tests\contract\test_financeiro_missoes_preview_http.py::test_preview_endpoint_returns_pending_fields_without_recalculate -vv --tb=short
1 passed in 4.05s
```

Subset financeiro relacionado:

```text
.\.venv\Scripts\python.exe -m pytest -q tests\contract\test_financeiro_missoes_preview_http.py
6 passed in 9.40s
```

## Resultado

Bloqueador removido: SIM
