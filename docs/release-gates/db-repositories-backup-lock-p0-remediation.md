# DB, Repositories and Backup Lock P0 Remediation

Data: 2026-06-06
Status: remediado no subset seguro; banco real permanece nao executado.
Branch observada: `safety-baseline-financeiro-20260602-193550`
Worktree observado: sujo antes e depois da remediacao.

## 1. Resumo executivo

Esta remediacao tratou as falhas P0 de banco, repositories e backup lock
registradas na baseline vermelha da Frente 1.5 sem tocar em banco real, schema,
migrations, seeds, restore, cleanup ou endpoints destrutivos.

As tres falhas nominais do bloco P0-OPS-DB foram classificadas como problemas de
fixture/ambiente de teste:

- `test_backup_operation_lock_blocks_second_execution`: sensivel ao filesystem
  temporario usado pelo `basetemp` da baseline no Windows.
- `test_backup_operation_lock_recovers_stale_lock`: mesma causa de filesystem
  temporario para lock local.
- `test_harden_release_manifest_falls_back_when_workspace_has_no_git_repo`:
  teste usava o `REPO_ROOT` real, que tem `.git`, para validar fallback de
  workspace sem repositorio Git.

Nao houve alteracao em `db/schema.py`, `db/migrations.py`, repositories de
produto, SQL critico, lock de backup de producao, jobs, restore, cleanup ou
scripts operacionais.

## 2. Fontes lidas

- `docs/release-gates/baseline-p0-execution.md`
- `docs/release-gates/data-reader-writer-map.md`
- `docs/release-gates/external-artifacts-inventory.md`
- `backend/src/controle_treinamentos/infra/backup.py`
- `ops/scripts/release/harden_release_manifest.py`
- `tests/unit/test_backup_operation_lock.py`
- `tests/ops/test_release_e2e_homolog_entrypoints.py`

## 3. Testes falhos identificados

| Teste | Falha da baseline | Classificacao | Correcao minima |
| --- | --- | --- | --- |
| `tests/unit/test_backup_operation_lock.py::test_backup_operation_lock_blocks_second_execution` | Terceiro lock retornou payload `None` apos falha de release por `PermissionError [WinError 5]` em `.run_backup.lock`. | Fixture de filesystem / teste sensivel a ambiente Windows. | Usar fixture temporaria gerenciada fora do `basetemp` do workspace. |
| `tests/unit/test_backup_operation_lock.py::test_backup_operation_lock_recovers_stale_lock` | Payload de lock retornou `None`. | Fixture de filesystem / stale lock mal exercitado por permissao local. | Usar fixture temporaria gerenciada fora do `basetemp` do workspace. |
| `tests/ops/test_release_e2e_homolog_entrypoints.py::test_harden_release_manifest_falls_back_when_workspace_has_no_git_repo` | `_git_head(REPO_ROOT)` retornou o HEAD real `66468738ee7248a02e16f5a89162759a3f0473f1`. | Teste sensivel a ambiente. | Criar workspace temporario sem `.git` e validar fallback nele. |

## 4. Causa raiz

O backup lock de produto ja implementava deny-by-default operacional: se existe
lock valido, a segunda aquisicao e bloqueada; se o lock e stale, a remocao so e
aceita quando o arquivo pode ser excluido com sucesso; falha de release e
registrada sem remover a protecao.

A baseline falhou porque o teste exercitava lock local dentro de diretorio
temporario controlado pelo `basetemp` no workspace, onde o Windows retornou
`PermissionError` ao remover `.run_backup.lock`. Alterar o produto para ignorar
essa falha relaxaria a protecao do lock, portanto a correcao correta foi isolar
a fixture de filesystem.

O teste de `_git_head` validava fallback de workspace sem Git usando o proprio
repositorio do projeto. Em uma worktree real, o comportamento correto e retornar
o HEAD, nao o fallback. A fixture agora cria um diretorio temporario sem `.git`.

## 5. Arquivos alterados

- `tests/conftest.py`: adicionada fixture `safe_filesystem_tmp_path` com
  `tempfile.TemporaryDirectory`.
- `tests/unit/test_backup_operation_lock.py`: testes de lock passam a usar
  `safe_filesystem_tmp_path`.
- `tests/ops/test_release_e2e_homolog_entrypoints.py`: teste de fallback Git
  passa a usar workspace temporario sem `.git`.
- `docs/release-gates/db-repositories-backup-lock-p0-remediation.md`: evidencia
  desta remediacao.

Arquivos de produto nao alterados nesta remediacao:

- `backend/src/controle_treinamentos/db/schema.py`
- `backend/src/controle_treinamentos/db/migrations.py`
- `backend/src/controle_treinamentos/infra/backup.py`
- `backend/src/controle_treinamentos/infra/jobs.py`
- `backend/src/controle_treinamentos/repositories/*.py`
- `ops/scripts/backup/*`
- `ops/scripts/database/*`

## 6. Operacoes nao executadas

Todas as operacoes abaixo permanecem `NAO EXECUTADAS`:

- Migration real: `NAO EXECUTADA`.
- Seed real: `NAO EXECUTADO`.
- Restore real: `NAO EXECUTADO`.
- Cleanup real: `NAO EXECUTADO`.
- Backup real: `NAO EXECUTADO`.
- Schema bootstrap real: `NAO EXECUTADO`.
- Repair/migration script real: `NAO EXECUTADO`.
- Endpoint destrutivo: `NAO EXECUTADO`.
- Banco real via `DATABASE_URL`: `NAO EXECUTADO`.
- Banco e2e via `E2E_DATABASE_URL`: `NAO EXECUTADO`.
- Delete fisico novo: `NAO EXECUTADO`.
- Alteracao de SQL critico: `NAO EXECUTADA`.

## 7. Banco real protegido

Os testes foram executados com `APP_ENV=testing`, remocao local de
`DATABASE_URL` e `E2E_DATABASE_URL` dentro do comando de teste, `-p
no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1` e `--basetemp` apontando para
diretorio temporario do sistema.

As suites bloqueadas na baseline continuam bloqueadas e nao foram executadas:

- `tests/e2e/test_critical_journeys.py`
- `tests/integration/test_integration_db.py`
- `tests/integration/test_financeiro_schema_bootstrap.py`
- `tests/integration/test_financeiro_missoes_repository_integration.py`
- `tests/integration/test_financeiro_missoes_application_integration.py`
- `tests/integration/test_financeiro_missoes_http.py`

## 8. Backup lock preservado

O lock de backup foi preservado sem relaxamento:

- A segunda execucao concorrente continua bloqueada enquanto existe lock valido.
- Lock stale so e recuperado quando o arquivo de lock pode ser removido.
- Falha de release continua registrada por log e nao e ignorada silenciosamente.
- Nenhum comportamento em `backend/src/controle_treinamentos/infra/backup.py`
  foi alterado.
- A tabela `backups_execucoes` nao foi escrita.

## 9. Jobs, repositories e schema

O `data-reader-writer-map.md` mantem `backups_execucoes`, `background_jobs` e
`background_job_executions` como tabelas bloqueadas para reorganizacao fisica. A
remediacao nao alterou jobs, dead-letter, cleanup de historico, SQL de
repositories, soft delete, FKs, indices, checks, migrations ou ordem de schema.

## 10. Testes reexecutados

Comando alvo seguro:

```powershell
& {
  $env:APP_ENV='testing'
  Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:E2E_DATABASE_URL -ErrorAction SilentlyContinue
  $env:PYTHONDONTWRITEBYTECODE='1'
  $baseTemp = Join-Path $env:TEMP ('pytest-ops-db-p0-target-' + [guid]::NewGuid().ToString('N'))
  .\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings -p no:cacheprovider --basetemp $baseTemp tests/unit/test_backup_operation_lock.py tests/ops/test_release_e2e_homolog_entrypoints.py
}
```

Resultado: `7 passed in 1.11s`.

Comando P0-OPS-DB seguro:

```powershell
& {
  $env:APP_ENV='testing'
  Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:E2E_DATABASE_URL -ErrorAction SilentlyContinue
  $env:PYTHONDONTWRITEBYTECODE='1'
  $baseTemp = Join-Path $env:TEMP ('pytest-ops-db-p0-safe-' + [guid]::NewGuid().ToString('N'))
  $files = @()
  $files += (Get-ChildItem tests/unit -Filter 'test_db*.py').FullName
  $files += (Resolve-Path tests/unit/test_backup_operation_lock.py).Path
  $files += (Resolve-Path tests/unit/test_restore_validation.py).Path
  $files += (Resolve-Path tests/unit/test_jobs_queue.py).Path
  $files += (Resolve-Path tests/unit/test_direct_script_guards.py).Path
  $files += (Get-ChildItem tests/ops -Filter '*.py').FullName
  .\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings -p no:cacheprovider --basetemp $baseTemp $files
}
```

Resultado: `133 passed in 28.01s`.

Comando P0-OPS-DB seguro ampliado com repositories/schema/boundaries:

```powershell
& {
  $env:APP_ENV='testing'
  Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:E2E_DATABASE_URL -ErrorAction SilentlyContinue
  $env:PYTHONDONTWRITEBYTECODE='1'
  $baseTemp = Join-Path $env:TEMP ('pytest-ops-db-p0-repo-safe-' + [guid]::NewGuid().ToString('N'))
  $files = @()
  $files += (Get-ChildItem tests/unit -Filter 'test_db*.py').FullName
  $files += (Resolve-Path tests/unit/test_backup_operation_lock.py).Path
  $files += (Resolve-Path tests/unit/test_restore_validation.py).Path
  $files += (Resolve-Path tests/unit/test_jobs_queue.py).Path
  $files += (Resolve-Path tests/unit/test_direct_script_guards.py).Path
  $files += (Get-ChildItem tests/ops -Filter '*.py').FullName
  $files += (Resolve-Path tests/unit/test_financeiro_schema.py).Path
  $files += (Resolve-Path tests/unit/test_financeiro_hourly_schema_precision.py).Path
  $files += (Resolve-Path tests/unit/test_financeiro_parametros_repository.py).Path
  $files += (Resolve-Path tests/unit/test_financeiro_missoes_repository.py).Path
  $files += (Resolve-Path tests/unit/test_financeiro_feriados_repository.py).Path
  $files += (Resolve-Path tests/unit/test_financeiro_competencias_repository.py).Path
  $files += (Resolve-Path tests/unit/test_financeiro_calculos_produtividade_repository.py).Path
  $files += (Resolve-Path tests/unit/test_financeiro_calculos_horarios_repository.py).Path
  $files += (Resolve-Path tests/unit/test_equipamentos_schema.py).Path
  $files += (Resolve-Path tests/unit/test_document_repository_policy.py).Path
  $files += (Resolve-Path tests/architecture/test_api_route_repository_boundaries.py).Path
  .\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings -p no:cacheprovider --basetemp $baseTemp $files
}
```

Resultado: `180 passed in 26.68s`.

## 11. Resultado pos-correcao

- Falhas nominais P0-OPS-DB da baseline: corrigidas no subset seguro.
- Backup lock: verde no teste unitario seguro.
- Restore validation unitario: executado no bloco seguro.
- Jobs queue/dead-letter unitario: executado no bloco seguro.
- Script guards e ops entrypoints: executados como testes nao destrutivos.
- Banco real, restore real, cleanup real, migrations e seeds: continuam
  bloqueados e nao executados.

## 12. Riscos remanescentes

- A worktree segue suja; a leitura de baseline nao representa commit limpo.
- Validacao com banco real isolado ainda nao foi executada.
- Schema bootstrap real, repository integration real, restore real e cleanup real
  continuam bloqueados ate haver ambiente isolado autorizado.
- `runtime/`, `ops/artifacts/`, `archive/` e artefatos externos continuam
  bloqueados para limpeza ou reorganizacao em lote.
- Rollback/restore real exige validacao humana e plano operacional aprovado.

## 13. Proximo passo recomendado

Executar nova rodada P0 nao destrutiva consolidada apos as demais remediacoes,
mantendo banco real bloqueado ate existir ambiente isolado explicitamente
autorizado. Somente depois disso preparar uma rodada separada, manualmente
aprovada, para integration DB, schema bootstrap, restore validation real e
cleanup drill controlado.
