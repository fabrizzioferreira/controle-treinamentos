# P0 Tripulante Status Source Of Truth Remediation

Data: 2026-06-07

## Falha tratada

`test_backend_queries_do_not_promote_tripulante_snapshots_as_primary_source`

## Causa raiz

`backend/src/controle_treinamentos/repositories/financeiro_calculos_horarios.py` usava o alias curto `c` para a CTE `candidates` no trecho:

```sql
RETURNING ch.*, c.status AS previous_status
```

A policy de source-of-truth trata aliases `c` e `t` como risco para leitura primaria de snapshot de tripulante. O trecho nao lia `tripulantes.status`; ele preservava o status anterior do calculo horario invalidado. Ainda assim, a ambiguidade textual violava a policy que impede promover snapshot como fonte primaria.

## Fonte primaria correta

Para status operacional de tripulante, a fonte primaria correta permanece `pilotos.status`.

Nesta query especifica, `previous_status` nao representa status operacional do tripulante; representa o status anterior do calculo em `financeiro_calculos_horarios.status`. Snapshot historico de tripulante segue permitido apenas como dado auxiliar com alias explicito `status_snapshot_compat`.

## Arquivos alterados

- `backend/src/controle_treinamentos/repositories/financeiro_calculos_horarios.py`
- `docs/release-gates/p0-tripulante-status-source-of-truth-remediation.md`

## Correcao aplicada

O alias da CTE foi tornado explicito:

```sql
FROM candidates candidate
WHERE ch.id = candidate.id
RETURNING ch.*, candidate.status AS previous_status
```

Nao houve alteracao de schema, migration, contrato de relatorio ou regra de calculo financeiro.

## Evidencia

Antes:

```text
.\.venv\Scripts\python.exe -m pytest -q -k test_backend_queries_do_not_promote_tripulante_snapshots_as_primary_source -vv --tb=long
FAILED tests/unit/test_tripulante_operational_status_owner.py::test_backend_queries_do_not_promote_tripulante_snapshots_as_primary_source
backend\src\controle_treinamentos\repositories\financeiro_calculos_horarios.py::status_alias_from_snapshot
```

Teste alvo depois:

```text
.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_tripulante_operational_status_owner.py::test_backend_queries_do_not_promote_tripulante_snapshots_as_primary_source -vv --tb=short
1 passed in 0.89s
```

Subset financeiro/repository:

```text
.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_tripulante_operational_status_owner.py tests\unit\test_financeiro_calculos_horarios_repository.py
17 passed in 1.06s
```

## Resultado

Bloqueador removido: SIM
