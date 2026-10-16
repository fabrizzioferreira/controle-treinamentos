# Baseline P0 After Final Remediation

Data: 2026-06-07
Janela de execucao: 2026-06-07T16:10:21-03:00 a 2026-06-07T16:22:21-03:00
Decisao: VERDE COM RESTRICOES

## 1. Resumo executivo

A baseline P0 consolidada segura foi reexecutada apos as quatro remediacoes P0 finais.

Resultado consolidado seguro:

- Passed: 1448
- Failed: 0
- Errors: 0
- Skipped: 0
- Blocked: E2E completo, 5 arquivos de integracao com DB real/schema/bootstrap, restore, cleanup, migrations e seeds
- Exit code: 0
- Duracao: 720.353s

Comparacao com a baseline anterior:

- Antes: 1444 passed, 4 failed, 0 errors
- Depois: 1448 passed, 0 failed, 0 errors

As quatro falhas P0 anteriores foram removidas no recorte seguro. A decisao nao e VERDE pleno porque os escopos DB/E2E reais continuam corretamente bloqueados ate existir ambiente descartavel autorizado.

## 2. Confirmacoes pre-execucao

- Branch: `safety-baseline-financeiro-20260602-193550`
- HEAD: `6646873`
- Git status: worktree suja antes da execucao, com 84 entradas modificadas/nao rastreadas, incluindo remediacoes P0 e evidencias em `docs/release-gates`.
- Regra aplicada: nenhum codigo foi alterado durante a execucao da baseline. Este documento foi criado apos a execucao.

Variaveis observadas antes do comando:

- `APP_ENV=<unset>`
- `FLASK_ENV=<unset>`
- `DATABASE_URL=<unset>`
- `POSTGRES_URL=<unset>`
- `PGHOST=<unset>`
- `PGDATABASE=<unset>`
- `PGUSER=<unset>`
- `PGPASSWORD=<unset>`
- `TEST_DATABASE_URL=<unset>`
- `CI=<unset>`
- `AUDIT_STRICT_MODE=<unset>`
- `AUTH_AUDIT_ENABLED_IN_TESTING=<unset>`

Ambiente seguro aplicado no comando:

- `APP_ENV=testing`
- `DATABASE_URL=postgresql://p0_disabled:***@127.0.0.1:1/p0_disabled`
- `E2E_DATABASE_URL=`
- `PYTHONDONTWRITEBYTECODE=1`
- `--basetemp=C:\Users\Fabrizzio.araujo\AppData\Local\Temp\ct-p0-after-final-ee3ab1c0759d43dea6bc050b99a50394`

## 3. Comando executado

```powershell
$env:APP_ENV='testing'
$env:DATABASE_URL='postgresql://p0_disabled:p0_disabled@127.0.0.1:1/p0_disabled'
$env:E2E_DATABASE_URL=''
$env:PYTHONDONTWRITEBYTECODE='1'
$runId = [guid]::NewGuid().ToString('N')
$baseTemp = Join-Path ([System.IO.Path]::GetTempPath()) "ct-p0-after-final-$runId"
$blockedIntegration = @(
  'tests/integration/test_integration_db.py',
  'tests/integration/test_financeiro_schema_bootstrap.py',
  'tests/integration/test_financeiro_missoes_repository_integration.py',
  'tests/integration/test_financeiro_missoes_http.py',
  'tests/integration/test_financeiro_missoes_application_integration.py'
)
$files = @()
$files += Get-ChildItem -Path tests/unit -Filter '*.py' -File | ForEach-Object { $_.FullName }
$files += Get-ChildItem -Path tests/contract -Filter '*.py' -File | ForEach-Object { $_.FullName }
$files += Get-ChildItem -Path tests/architecture -Filter '*.py' -File | ForEach-Object { $_.FullName }
$files += Get-ChildItem -Path tests/ops -Filter '*.py' -File | ForEach-Object { $_.FullName }
$files += Get-ChildItem -Path tests/integration -Filter '*.py' -File | Where-Object {
  $rel = $_.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
  $blockedIntegration -notcontains $rel
} | ForEach-Object { $_.FullName }
.\.venv\Scripts\python.exe -m pytest @files --basetemp $baseTemp
```

## 4. Resultado da execucao

```text
P0_BASELINE_START=2026-06-07T16:10:21.2483889-03:00
P0_BASELINE_FILES=212
P0_BASELINE_BLOCKED_INTEGRATION=5
collected 1448 items
1448 passed in 718.29s (0:11:58)
P0_BASELINE_END=2026-06-07T16:22:21.6017576-03:00
P0_BASELINE_DURATION_SECONDS=720.353
P0_BASELINE_EXIT_CODE=0
```

## 5. Escopos bloqueados por seguranca

- `tests/e2e/*`: bloqueado por depender de banco E2E mutavel e fluxos operacionais.
- `tests/integration/test_integration_db.py`: bloqueado por exigir banco/schema real.
- `tests/integration/test_financeiro_schema_bootstrap.py`: bloqueado por risco de bootstrap/mutacao de schema.
- `tests/integration/test_financeiro_missoes_repository_integration.py`: bloqueado por exigir banco real.
- `tests/integration/test_financeiro_missoes_http.py`: bloqueado por exigir banco real e fluxos HTTP de dados.
- `tests/integration/test_financeiro_missoes_application_integration.py`: bloqueado por exigir banco real/camada aplicacional.
- Restore real, cleanup real, migrations e seeds: bloqueados.

## 6. Status das quatro falhas P0 anteriores

1. Financeiro preview HTTP
   - Status: RESOLVIDA
   - Evidencia na baseline: `tests/contract/test_financeiro_missoes_preview_http.py` passou.

2. SSR/accessibility
   - Status: RESOLVIDA
   - Evidencia na baseline: `tests/unit/test_accessibility_residual_28_fix.py` passou.

3. Fallback legado de foto
   - Status: RESOLVIDA
   - Evidencia na baseline: `tests/unit/test_legacy_blob_freeze_policy.py` passou.

4. Source-of-truth de status operacional
   - Status: RESOLVIDA
   - Evidencia na baseline: `tests/unit/test_tripulante_operational_status_owner.py` passou.

## 7. Novas falhas

Nenhuma nova falha no recorte P0 consolidado seguro.

## 8. Decisao

Decisao da baseline: VERDE COM RESTRICOES.

Justificativa:

- O recorte P0 consolidado seguro passou integralmente.
- As quatro falhas P0 anteriores foram removidas.
- Nao houve falhas P0 criticas remanescentes no recorte executado.
- DB real, E2E real, restore, cleanup, migrations e seeds continuam bloqueados por regra de seguranca ate existir ambiente descartavel e autorizacao explicita.

Pode seguir para aceite humano: SIM.
