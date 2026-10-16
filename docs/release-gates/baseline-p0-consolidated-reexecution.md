# Baseline P0 Consolidated Reexecution

Data: 2026-06-07  
Janela de execucao: 2026-06-07T15:02:25-03:00 a 2026-06-07T15:18:45-03:00  
Decisao: VERMELHA  
Contexto: reexecucao da baseline P0 consolidada apos remediacoes da Frente 1.6.

## 1. Resumo executivo

A baseline P0 consolidada segura foi reexecutada em ambiente local de teste, sem banco real, sem producao, sem migracoes, sem seeds, sem restore, sem cleanup e sem endpoints destrutivos.

Resultado consolidado seguro:

- 1444 testes passaram.
- 4 testes falharam.
- 0 erros de pytest.
- 0 comandos destrutivos executados.
- 5 arquivos de integracao com dependencia de banco real/schema/bootstrap foram bloqueados por seguranca.
- E2E foi bloqueado por depender de banco E2E mutavel e fluxos destrutivos/operacionais.

A baseline nao pode ser declarada verde nem verde com restricoes, pois ha 4 falhas P0 remanescentes no recorte seguro executado.

## 2. Branch e estado Git

- Branch: `safety-baseline-financeiro-20260602-193550`
- HEAD: `6646873`
- Estado Git: worktree suja antes da reexecucao, com alteracoes existentes da Frente 1.6 e arquivos de documentacao em `docs/release-gates`.
- Regra aplicada: nenhum codigo de produto, teste ou contrato foi alterado durante a execucao da baseline. Esta evidencia documental foi criada apos a execucao.

## 3. Ambiente usado

- Host: Windows / PowerShell
- Workspace: `C:\apps\controle-treinamentos`
- `APP_ENV=testing`
- `DATABASE_URL=postgresql://p0_disabled:***@127.0.0.1:1/p0_disabled`
- `E2E_DATABASE_URL=`
- `PYTHONDONTWRITEBYTECODE=1`
- `--basetemp=C:\Users\FABRIZ~1.ARA\AppData\Local\Temp\ct-p0-consolidated-b05876f0301e4f48b17bb83dbd73863b`

Confirmacao de seguranca:

- `DATABASE_URL` e `E2E_DATABASE_URL` nao apontaram para producao, homologacao ou banco real sensivel durante a execucao.
- `.env` contem `DATABASE_URL=postgresql://***:***@127.0.0.1:5432/ct_local`.
- O app chama `load_dotenv()` no import. `DATABASE_URL` vazio seria sobrescrito pela `.env`; por isso a baseline usou DSN dummy explicito em `127.0.0.1:1`, que nao conecta a banco real.

## 4. Comandos classificados

| ID | Comando/escopo | Classificacao | Decisao |
| --- | --- | --- | --- |
| P0-CONSOLIDATED-SAFE | `tests/unit`, `tests/contract`, `tests/architecture`, `tests/ops` e `tests/integration` exceto arquivos com DB real/bootstrap | seguro / teste isolado | Executado |
| P0-E2E-REAL | `tests/e2e/*` | bloqueado | Nao executado: depende de banco E2E e fluxos mutaveis |
| P0-DB-INTEGRATION-REAL | `tests/integration/test_integration_db.py` | bloqueado | Nao executado: requer banco real/schema |
| P0-FINANCE-SCHEMA-BOOTSTRAP | `tests/integration/test_financeiro_schema_bootstrap.py` | bloqueado | Nao executado: pode criar/validar schema |
| P0-FINANCE-REPOSITORY-INTEGRATION | `tests/integration/test_financeiro_missoes_repository_integration.py` | bloqueado | Nao executado: requer banco real |
| P0-FINANCE-HTTP-INTEGRATION | `tests/integration/test_financeiro_missoes_http.py` | bloqueado | Nao executado: requer banco real/fluxos HTTP de dados |
| P0-FINANCE-APPLICATION-INTEGRATION | `tests/integration/test_financeiro_missoes_application_integration.py` | bloqueado | Nao executado: requer banco real/camada aplicacional |
| OPS-RESTORE | Restore real | destrutivo | Bloqueado |
| OPS-CLEANUP | Cleanup real | destrutivo | Bloqueado |
| OPS-MIGRATIONS | Migracoes | destrutivo/desconhecido | Bloqueado |
| OPS-SEEDS | Seeds | destrutivo | Bloqueado |

## 5. Comandos executados

### P0-CONSOLIDATED-SAFE

Horario:

- Inicio: `2026-06-07T15:06:14.3954863-03:00`
- Fim: `2026-06-07T15:18:01.5490426-03:00`
- Duracao: `707.154s`

Comando:

```powershell
$env:APP_ENV='testing'
$env:DATABASE_URL='postgresql://p0_disabled:p0_disabled@127.0.0.1:1/p0_disabled'
$env:E2E_DATABASE_URL=''
$env:PYTHONDONTWRITEBYTECODE='1'
$baseTemp = Join-Path ([System.IO.Path]::GetTempPath()) 'ct-p0-consolidated-b05876f0301e4f48b17bb83dbd73863b'
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
python -m pytest @files --basetemp $baseTemp
```

Resultado:

- Arquivos executados: 212
- Arquivos de integracao bloqueados: 5
- Resultado pytest: `4 failed, 1444 passed in 705.85s (0:11:45)`
- Exit code: `1`

## 6. Comandos bloqueados e motivo

- `tests/e2e/*`: bloqueado por depender de banco E2E e fluxos de jornada que podem criar, alterar ou limpar dados.
- `tests/integration/test_integration_db.py`: bloqueado por exigir banco/schema real.
- `tests/integration/test_financeiro_schema_bootstrap.py`: bloqueado por risco de bootstrap/mutacao de schema.
- `tests/integration/test_financeiro_missoes_repository_integration.py`: bloqueado por exigir banco real.
- `tests/integration/test_financeiro_missoes_http.py`: bloqueado por exigir banco real e fluxos HTTP de dados.
- `tests/integration/test_financeiro_missoes_application_integration.py`: bloqueado por exigir banco real/camada aplicacional.
- Restore real, cleanup real, migrations, seeds e scripts operacionais destrutivos: bloqueados por regra de release safety.

## 7. Resultado consolidado

Baseline consolidada segura: VERMELHA.

Motivo:

- A execucao consolidada segura foi realizada.
- O resultado teve 4 falhas P0 remanescentes.
- Testes com banco real/E2E ficaram corretamente bloqueados, nao aprovados.
- Nao ha base para declarar VERDE ou VERDE COM RESTRICOES enquanto falhas bloqueadoras existem no recorte seguro.

## 8. Comparacao com baseline 1.5

Referencia: `docs/release-gates/baseline-p0-execution.md`.

Baseline 1.5:

- Decisao: BASELINE VERMELHA.
- Resultado agregado: 1300 passagens, 28 falhas, 8 erros e 1 timeout.
- Bloqueios relevantes: E2E, banco real/schema, restore, cleanup, seeds e fluxos operacionais.

Baseline atual:

- Decisao: VERMELHA.
- Resultado consolidado seguro: 1444 passagens, 4 falhas, 0 erros.
- Houve melhora objetiva na quantidade de falhas/erros, mas a baseline continua vermelha por falhas P0 remanescentes e bloqueios operacionais necessarios.

Observacao: os numeros nao sao comparaveis 1:1 porque a execucao atual consolidou os arquivos seguros em um unico comando, enquanto a baseline 1.5 foi registrada por blocos e com sobreposicoes.

## 9. Comparacao com subsets 1.6

Referencias:

- `docs/release-gates/auth-rbac-p0-remediation.md`: subset auth/RBAC seguro com `180 passed`.
- `docs/release-gates/financeiro-p0-remediation.md`: subset financeiro seguro com `456 passed`.
- `docs/release-gates/documents-storage-p0-remediation.md`: subset documentos/storage com `111 passed`.
- `docs/release-gates/frontend-routes-p0-remediation.md`: recorte frontend/routes registrou remediacoes da Frente 1.6.
- `docs/release-gates/frontend-boundary-final-resolution.md`: frontend boundary amplo resolvido com `242 passed`.
- `docs/release-gates/db-repositories-backup-lock-p0-remediation.md`: DB/ops seguro com `180 passed`.
- `docs/release-gates/auditability-remediation.md`: auditabilidade ampla com `192 passed`.

Comparacao:

- Auth/RBAC permaneceu sem falhas no consolidado seguro.
- Frontend boundary amplo permaneceu sem falhas no consolidado seguro.
- DB/ops unitario permaneceu sem falhas no consolidado seguro, mas banco real/restore/cleanup continuam bloqueados por seguranca.
- Financeiro voltou a apresentar uma falha no consolidado seguro em preview HTTP sem recalculate, causada por dependencia de DB nao isolada.
- Documentos/storage voltou a apresentar uma falha de politica em fallback legado de foto.
- Repositories/source-of-truth manteve falha historica ligada a status operacional por snapshot.
- SSR/templates apresentou falha de contrato de acessibilidade no shell base.

## 10. Resultados por area

| Area | Resultado | Evidencia |
| --- | --- | --- |
| Auth/session/RBAC | Liberada no recorte seguro | Sem falhas no consolidado |
| Login/logout/falha | Liberada no recorte seguro | Sem falhas no consolidado |
| Capabilities | Liberada no recorte seguro | Sem falhas no consolidado |
| CSRF/cookies/401/403 | Liberada no recorte seguro | Sem falhas no consolidado |
| Endpoint-permission coverage | Liberada no recorte seguro | Sem falhas no consolidado |
| Financeiro missoes/jornada/recalculo | Bloqueada | Falha em preview HTTP e integracoes DB bloqueadas |
| Fechamento/reabertura/parametros/feriados | Liberada com restricao | Recorte seguro sem falhas especificas, DB real bloqueado |
| Relatorios/PDFs financeiros | Liberada com restricao | Recorte seguro sem falhas especificas, validacao real bloqueada |
| Tripulantes CRUD | Bloqueada | Falha de source-of-truth de status operacional |
| Treinamentos CRUD | Liberada no recorte seguro | Sem falhas no consolidado |
| Anexos/fotos/documentos | Bloqueada | Falha de fallback legado de foto |
| Cadastro raiz | Liberada com restricao | Sem falha especifica, dependencias reais bloqueadas |
| Rotas SPA | Liberada | Frontend boundary amplo sem falhas |
| Rotas SSR/templates | Bloqueada | Falha de contrato de acessibilidade em `base.html` |
| Aliases/redirects/deep links | Liberada | Sem falhas no consolidado |
| PDF/CSV/relatorios | Liberada com restricao | Sem falhas especificas, validacao real bloqueada |
| Banco/schema/repositories | Bloqueada | DB real bloqueado e falha em repository/source-of-truth |
| Backup lock | Liberada no recorte seguro | Sem falhas no consolidado |
| Restore validation unitaria | Liberada com restricao | Unitarios seguros sem falhas, restore real bloqueado |
| Jobs queue/dead-letter | Liberada no recorte seguro | Sem falhas no consolidado |
| Script guards | Liberada no recorte seguro | Sem falhas no consolidado |
| Frontend boundary amplo | Liberada | `242 passed` na evidencia da Frente 1.6 e sem regressao no consolidado |
| Auditabilidade afetada | Liberada com restricao | Sem falhas especificas, operacoes sensiveis reais bloqueadas |
| Regression safety contratos congelados | Bloqueada | 4 falhas P0 no consolidado |

## 11. Falhas remanescentes

1. `tests/contract/test_financeiro_missoes_preview_http.py::test_preview_endpoint_returns_pending_fields_without_recalculate`
   - Esperado: HTTP 200.
   - Obtido: HTTP 500.
   - Evidencia: tentativa de conexao ao DSN dummy `127.0.0.1:1`, recusada por seguranca.
   - Classificacao: falha/bloqueio de isolamento em fluxo financeiro preview HTTP.

2. `tests/unit/test_accessibility_residual_28_fix.py::test_shell_has_persistent_live_regions_focus_after_render_and_no_label_generation`
   - Esperado: contrato exato de `<main class="content" id="mainContent" tabindex="-1">`.
   - Obtido: contrato ausente em `backend/src/controle_treinamentos/templates/base.html`.
   - Classificacao: falha de SSR/template/accessibility contract.

3. `tests/unit/test_legacy_blob_freeze_policy.py::test_legacy_photo_fallback_is_centralized_outside_bases_route`
   - Esperado: `backend/src/controle_treinamentos/blueprints/bases/routes.py` sem `_decode_photo_data_uri`.
   - Obtido: helper legado presente no route file.
   - Classificacao: falha de boundary/politica de fallback legado de foto.

4. `tests/unit/test_tripulante_operational_status_owner.py::test_backend_queries_do_not_promote_tripulante_snapshots_as_primary_source`
   - Esperado: repositories nao promoverem snapshots de tripulante como fonte primaria de status.
   - Obtido: offender `backend\src\controle_treinamentos\repositories\financeiro_calculos_horarios.py::status_alias_from_snapshot`.
   - Classificacao: falha de source-of-truth/repository boundary.

## 12. Erros remanescentes

- Erros pytest: 0.
- Logs relevantes: o primeiro teste falho registrou `connection refused` contra o DSN dummy `127.0.0.1:1`. Isto confirma que nenhum banco real foi usado; a falha revela dependencia de DB nao isolada no teste/fluxo de preview.

## 13. Areas liberadas

- Auth/session/RBAC.
- Login/logout/falha.
- Capabilities.
- CSRF/cookies/401/403.
- Endpoint-permission coverage.
- Frontend boundary amplo.
- Rotas SPA.
- Aliases, redirects e deep links.
- Treinamentos CRUD no recorte seguro.
- Backup lock no recorte seguro.
- Jobs queue/dead-letter no recorte seguro.
- Script guards no recorte seguro.

## 14. Areas liberadas com restricao

- Fechamento/reabertura/parametros/feriados: sem falhas especificas no recorte seguro, mas sem validacao em banco real.
- Relatorios financeiros/PDF/CSV: sem falhas especificas no recorte seguro, mas sem validacao real com banco/arquivos sensiveis.
- Cadastro raiz: sem falha especifica no recorte seguro, mas fluxos reais permanecem bloqueados.
- Restore validation: unitarios seguros liberados; restore real bloqueado.
- Auditabilidade afetada: sem falhas especificas no recorte seguro; operacoes reais sensiveis bloqueadas.

## 15. Areas bloqueadas

- Financeiro preview HTTP sem recalculate.
- Financeiro com banco real/schema/bootstrap.
- Tripulantes/status operacional source-of-truth.
- Anexos/fotos/documentos por politica de fallback legado.
- SSR/templates por contrato de acessibilidade.
- Banco/schema/repositories.
- E2E completo.
- Restore real, cleanup real, migrations e seeds.
- Regression safety dos contratos congelados enquanto as 4 falhas P0 permanecerem.

## 16. Evidencia criada

Este documento e a evidencia formal da reexecucao consolidada:

- `docs/release-gates/baseline-p0-consolidated-reexecution.md`

## 17. Decisao da baseline

Decisao: VERMELHA.

Justificativa:

- A baseline P0 consolidada segura foi reexecutada.
- O resultado teve 4 falhas P0.
- Os comandos bloqueados foram corretamente classificados como bloqueados, nao aprovados.
- Subsets verdes da Frente 1.6 nao substituem a baseline consolidada.
- Nao e seguro avancar para reorganizacao fisica ou Frente 2.1 ate remediar as falhas ou formalizar excecoes com escopo, prazo e risco aceito.

## 18. Proximo passo recomendado

1. Corrigir ou formalizar excecao para as 4 falhas P0 remanescentes.
2. Preparar um banco descartavel e explicitamente isolado para E2E/integracao DB, com credenciais e schema temporarios.
3. Reexecutar a baseline P0 consolidada completa incluindo os comandos hoje bloqueados.
4. Reavaliar o release gate somente apos baseline verde ou verde com restricoes formalmente justificadas.
