# Baseline P0 Execution - Reorganizacao Fisica

Data da execucao: 2026-06-06
Janela: 19:48:06-20:00:50 America/Sao_Paulo
Status: BASELINE VERMELHA
Escopo: execucao nao destrutiva da baseline P0 antes de reorganizacao fisica.

Este relatorio registra evidencia de execucao. Nenhuma falha foi corrigida nesta
rodada. Nenhum endpoint destrutivo foi chamado em ambiente real. Nenhuma
migration, seed, restore, cleanup ou script operacional destrutivo foi executado.

## 1. Resumo executivo

A baseline P0 foi executada por blocos seguros usando pytest local, dublês,
monkeypatch, testes estaticos, Flask test client e arquivos temporarios. As
variaveis `DATABASE_URL` e `E2E_DATABASE_URL` foram removidas dentro dos comandos
de teste para evitar uso acidental de banco real ou homologacao.

Resultado consolidado por comandos executados, com sobreposicao de alguns testes
entre areas:

- 5 blocos de teste executados.
- 1 tentativa invalida de comando registrada, sem teste executado.
- 1300 passagens observadas.
- 28 falhas observadas.
- 8 erros observados.
- 1 bloco teve timeout do wrapper apos o pytest emitir resumo.
- Suites com banco real, e2e, schema bootstrap, restore, cleanup e seeds foram
  bloqueadas, nao aprovadas.

Decisao: `VERMELHA`. A reorganizacao fisica permanece bloqueada.

## 2. Branch e estado Git

- Branch: `safety-baseline-financeiro-20260602-193550`
- HEAD curto: `6646873`
- Estado antes/depois da execucao: worktree sujo.
- Alteracoes de produto/teste ja existentes foram preservadas e nao foram
  revertidas.
- Documentos de gate ja presentes antes desta frente:
  - `docs/release-gates/contract-freeze-register.md`
  - `docs/release-gates/auditability-gate-register.md`

Resumo do `git status --short --untracked-files=all` relevante:

- Arquivos modificados em backend, frontend e tests ja estavam presentes no
  worktree, incluindo financeiro, auth, schema, repositories, frontend e suites
  de contrato.
- Arquivos nao rastreados ja estavam presentes, incluindo dist frontend,
  relatorios PDF e `tests/unit/test_tripulante_operational_periods.py`.
- Novo arquivo desta frente: `docs/release-gates/baseline-p0-execution.md`.

Risco do estado Git: a baseline mede o worktree atual, nao um commit limpo.

## 3. Ambiente usado

- Sistema: Windows / PowerShell.
- CWD: `C:\apps\controle-treinamentos`
- Python: `Python 3.11.9`
- Pytest: `pytest 8.3.5`
- `APP_ENV`: definido como `testing` dentro dos comandos.
- `DATABASE_URL`: removido dentro dos comandos.
- `E2E_DATABASE_URL`: removido dentro dos comandos.
- `PYTHONDONTWRITEBYTECODE`: definido como `1` dentro dos comandos.
- `pytest.ini`: `testpaths` cobre `tests/architecture`, `tests/contract`,
  `tests/e2e`, `tests/integration`, `tests/ops`, `tests/unit`; marcador `e2e`
  indica testes contra homologacao com banco real.
- `--basetemp`: usado nos blocos posteriores em `runtime/pytest-baseline-p0-*`
  para isolar temporarios de pytest.

Arquivos temporarios observados:

- `runtime/pytest-baseline-p0-frontend-routes`
- `runtime/pytest-baseline-p0-ops-db`
- `runtime/pytest-baseline-p0-trip-training-docs`

Esses diretorios estao sob `runtime/`, que e ignorado pelo Git. Eles nao sao
evidencia de aprovacao; a evidencia formal e este documento.

## 4. Testes P0 encontrados

Testes P0 disponiveis foram identificados por leitura de `pytest.ini`,
`pyproject.toml`, `Makefile`, `tests/conftest.py` e inventario `rg --files tests`.

Areas com testes encontrados:

- Auth/session/RBAC/login/logout/falha/capabilities/CSRF/cookies/401/403:
  `tests/unit/test_auth_permissions.py`,
  `tests/unit/test_auth_session_touch_policy.py`,
  `tests/unit/test_login_resilience.py`,
  `tests/unit/test_session_cookie_config.py`,
  `tests/unit/test_security_headers.py`,
  `tests/unit/test_endpoint_permission_coverage.py`,
  `tests/contract/test_api_session_contract.py`,
  `tests/contract/test_auth_semantics_matrix_contract.py`,
  `tests/contract/test_session_lifecycle_contract.py`,
  `tests/contract/test_http_error_contract.py`.
- Financeiro missoes, jornada, recalculo, fechamento/reabertura, parametros,
  feriados, relatorios e PDFs:
  `tests/unit/test_financeiro*.py`,
  `tests/contract/test_financeiro*.py`,
  `tests/architecture/test_financeiro*.py`,
  `tests/architecture/test_responsive_finance_visual_contract.py`.
- Tripulantes, treinamentos, anexos, fotos, documentos e cadastro raiz:
  `tests/unit/test_tripulante*.py`,
  `tests/unit/test_training*.py`,
  `tests/unit/test_media_storage.py`,
  `tests/unit/test_file_access_policy.py`,
  `tests/unit/test_pdf_document_policy.py`,
  `tests/contract/test_api_tripulantes_contract.py`,
  `tests/contract/test_api_tripulante_media_contract.py`,
  `tests/contract/test_api_treinamentos_contract.py`,
  `tests/contract/test_api_training_program_contract.py`,
  `tests/integration/test_tripulante_file_routes_resilience.py`,
  `tests/integration/test_treinamentos_ssr_routes.py`,
  `tests/integration/test_treinamentos_ssr_attachments_exports.py`.
- Rotas SPA, SSR, aliases, redirects e deep links:
  `tests/contract/test_frontend*.py`,
  `tests/contract/test_frontend_compat_redirects.py`,
  `tests/contract/test_backend_ssr_sidebar_shell.py`,
  `tests/architecture/test_ssr*.py`,
  `tests/architecture/test_contract_route_deduplication_governance.py`.
- Banco/schema/repositories/backup/jobs/dead-letter/script guards:
  `tests/unit/test_db*.py`,
  `tests/unit/test_backup_operation_lock.py`,
  `tests/unit/test_restore_validation.py`,
  `tests/unit/test_jobs_queue.py`,
  `tests/unit/test_direct_script_guards.py`,
  `tests/ops/*.py`.
- E2E e banco real:
  `tests/e2e/test_critical_journeys.py`,
  `tests/integration/test_integration_db.py`,
  `tests/integration/test_financeiro_schema_bootstrap.py`,
  `tests/integration/test_financeiro_missoes_*`.

## 5. Testes executados

### P0-AUTH-SEC

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings tests/unit/test_auth_permissions.py tests/unit/test_auth_session_touch_policy.py tests/unit/test_user_loader_request_cache.py tests/unit/test_login_resilience.py tests/unit/test_session_cookie_config.py tests/unit/test_security_headers.py tests/unit/test_http_utils_security.py tests/unit/test_http_request_logging_policy.py tests/unit/test_endpoint_permission_coverage.py tests/unit/test_app_security_config.py tests/unit/test_boot_fallback_security.py tests/contract/test_api_session_contract.py tests/contract/test_auth_semantics_matrix_contract.py tests/contract/test_session_lifecycle_contract.py tests/contract/test_http_error_contract.py tests/contract/test_api_cors_contract.py tests/contract/test_frontend_ux_functional_guards.py tests/contract/test_frontend_service_state_boundaries.py
```

- Inicio: `2026-06-06T19:48:06.4279523-03:00`
- Fim: `2026-06-06T19:49:20.4210518-03:00`
- Duracao: `73.993s`
- Exit code: `1`
- Resultado: `169 passed, 7 failed, 4 errors`
- Arquivos de saida: stdout/stderr capturados neste relatorio; nenhum junit/html
  gerado.

### P0-FINANCE-GLOB-INVALID

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings --basetemp runtime/pytest-baseline-p0-finance tests/unit/test_financeiro*.py tests/contract/test_financeiro*.py tests/architecture/test_financeiro*.py tests/architecture/test_responsive_finance_visual_contract.py
```

- Inicio: `2026-06-06T19:50:01.6418435-03:00`
- Fim: `2026-06-06T19:50:02.6142441-03:00`
- Duracao: `0.972s`
- Exit code: `4`
- Resultado: nenhum teste executado; PowerShell passou o glob literalmente para
  o pytest.
- Classificacao: comando invalido, nao conta como aprovacao nem falha de teste.

### P0-FINANCE

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings --basetemp runtime/pytest-baseline-p0-finance <49 arquivos financeiros expandidos>
```

- Inicio: `2026-06-06T19:50:32.1888386-03:00`
- Fim: `2026-06-06T19:52:51.3954863-03:00`
- Duracao: `139.207s`
- Exit code: `1`
- Resultado: `454 passed, 2 failed`
- Arquivos de saida: stdout/stderr capturados neste relatorio; temporarios em
  `runtime/pytest-baseline-p0-finance`.

### P0-TRIP-TRAINING-DOCS

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings --basetemp runtime/pytest-baseline-p0-trip-training-docs <34 arquivos de tripulantes/treinamentos/docs expandidos>
```

- Inicio: `2026-06-06T19:53:18.4545661-03:00`
- Fim: nao impresso pelo wrapper porque o comando atingiu timeout externo.
- Duracao pytest: `307.10s`
- Timeout do wrapper: `308.648s`
- Exit code do wrapper: `124`
- Resultado pytest antes do timeout: `280 passed, 7 failed`
- Arquivos de saida: stdout/stderr capturados neste relatorio; temporarios em
  `runtime/pytest-baseline-p0-trip-training-docs`.

### P0-FRONTEND-ROUTES

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings --basetemp runtime/pytest-baseline-p0-frontend-routes <54 arquivos frontend/rotas expandidos>
```

- Inicio: `2026-06-06T19:59:00.3672655-03:00`
- Fim: `2026-06-06T19:59:36.4908894-03:00`
- Duracao: `36.124s`
- Exit code: `1`
- Resultado: `236 passed, 9 failed, 4 errors`
- Arquivos de saida: stdout/stderr capturados neste relatorio; temporarios em
  `runtime/pytest-baseline-p0-frontend-routes`.

### P0-OPS-DB

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings --basetemp runtime/pytest-baseline-p0-ops-db <32 arquivos ops/db expandidos>
```

- Inicio: `2026-06-06T20:00:00.1437386-03:00`
- Fim: `2026-06-06T20:00:35.9782980-03:00`
- Duracao: `35.835s`
- Exit code: `1`
- Resultado: `161 passed, 3 failed`
- Arquivos de saida: stdout/stderr capturados neste relatorio; temporarios em
  `runtime/pytest-baseline-p0-ops-db`.

## 6. Testes nao executados e motivo

| Area | Arquivo | Motivo | Status |
|---|---|---|---|
| E2E real | `tests/e2e/test_critical_journeys.py` | Exige `E2E_DATABASE_URL`, cria usuarios/entidades, enfileira backup e executa cleanup de entidades. Sem ambiente isolado autorizado. | bloqueado |
| Banco real | `tests/integration/test_integration_db.py` | Exige `DATABASE_URL` apontando para banco de teste real. Nao havia banco isolado declarado. | bloqueado |
| Schema/bootstrap financeiro | `tests/integration/test_financeiro_schema_bootstrap.py` | Executa `execute_schema_bootstrap(db)` em banco real de teste. Regra do gate proibe migration/schema bootstrap nesta execucao. | bloqueado |
| Repository integration financeiro | `tests/integration/test_financeiro_missoes_repository_integration.py` | Exige banco real de teste, schema bootstrap e inserts/updates/cancel/delete em transacao. | bloqueado |
| Application integration financeiro | `tests/integration/test_financeiro_missoes_application_integration.py` | Exige banco real de teste e bootstrap. Sem ambiente isolado autorizado. | bloqueado |
| HTTP integration financeiro | `tests/integration/test_financeiro_missoes_http.py` | Exige banco real de teste, schema bootstrap, login e chamadas CRUD/cancel/delete em test client contra DB. | bloqueado |
| Suite completa | `pytest` sem filtro | Incluiria e2e/banco real e testes bloqueados acima. | bloqueado |
| Restore real | scripts em `ops/scripts/backup/*restore*` | Regra do gate proibe restore. Foram executados apenas testes unitarios/estaticos de validacao. | bloqueado |
| Cleanup real | scripts em `ops/scripts/database/*cleanup*` | Regra do gate proibe cleanup. Foram executados apenas testes de guardas que falham antes de conectar ao DB. | bloqueado |
| Migration/repair/seed real | `backend/tools/maintenance/*`, `ops/scripts/database/run_db_consistency.py`, seeders | Regra do gate proibe migration, repair e seed. Foram executados apenas testes de politica/guardas. | bloqueado |

## 7. Resultados por area

| Area P0 | Resultado observado | Decisao |
|---|---|---|
| Auth/session/RBAC/login/logout/falha | 169 passed, 7 failed, 4 errors no bloco P0-AUTH-SEC | bloqueada |
| Capabilities/CSRF/cookies/401/403 | Cobertura executada no bloco P0-AUTH-SEC; falhas em contratos de erro e erros em frontend UX | bloqueada |
| Endpoint-permission coverage | Falhas em catalogo/matriz financeira dentro de `test_auth_permissions.py` | bloqueada |
| Financeiro missoes/jornada/recalculo | 454 passed, 2 failed no bloco P0-FINANCE | bloqueada |
| Fechamento/reabertura/parametros/feriados | Executados dentro de P0-FINANCE, sem liberacao macro por falha de matriz financeira | bloqueada |
| Relatorios financeiros/PDFs financeiros | Executados dentro de P0-FINANCE, sem liberacao macro por falha de matriz financeira | bloqueada |
| Tripulantes CRUD | 280 passed, 7 failed no bloco P0-TRIP-TRAINING-DOCS | bloqueada |
| Treinamentos CRUD | Executados dentro de P0-TRIP-TRAINING-DOCS; falhas em anexos/download e timeout do wrapper | bloqueada |
| Anexos/fotos/documentos | Falhas de storage, download audit strict e permissao de filesystem | bloqueada |
| Cadastro raiz | Executado em contratos e integration safe; falha em helper `_decode_photo_data_uri` ausente no supertest | bloqueada |
| Rotas SPA/SSR/aliases/redirects/deep links | 236 passed, 9 failed, 4 errors no bloco P0-FRONTEND-ROUTES | bloqueada |
| PDF/CSV/relatorios nao financeiros | Executados em bloco docs; sem liberacao por falhas em documentos/download | bloqueada |
| Banco/schema/repositories | 161 passed, 3 failed no bloco P0-OPS-DB; integration DB real bloqueada | bloqueada |
| Backup lock | 2 falhas em `test_backup_operation_lock.py` | bloqueada |
| Restore validation | Testes unitarios executados dentro de P0-OPS-DB; restore real bloqueado | restrita |
| Jobs queue/dead-letter | Testes executados dentro de P0-OPS-DB; sem falha nominal observada, mas macro-area ops falhou | restrita |
| Script guards | Testes ops executados; cleanup/restore/migration/seed reais bloqueados | restrita |

## 8. Falhas encontradas

### Auth/session/RBAC e contratos HTTP

- `tests/unit/test_auth_permissions.py::test_finance_permissions_are_registered_in_catalog`
  - Falha: permissao extra `finance:missions:delete` no catalogo runtime.
- `tests/unit/test_auth_permissions.py::test_finance_endpoint_mappings_match_runtime_http_contracts`
  - Falha: divergencia entre endpoints registrados e matriz esperada, incluindo
    rotas de `lancamentos-jornada` e `DELETE /api/v1/financeiro/missoes/{id}`.
- `tests/contract/test_http_error_contract.py`
  - Falhas: testes de 500 API/HTML, request/correlation id e internal trace
    receberam `RuntimeError` propagado em vez de contrato de erro esperado.
- `tests/contract/test_frontend_service_state_boundaries.py::test_frontend_services_and_state_modules_exist_with_explicit_owners`
  - Falha: modulos extras em `frontend/src/services`, incluindo
    `financeiro-bonificacoes-api.js`, `financeiro-parametros-api.js` e
    `financeiro-lancamentos-jornada-api.js`.
- `tests/contract/test_frontend_ux_functional_guards.py`
  - Erro no primeiro bloco: pytest nao conseguiu criar diretorio temporario no
    temp do Windows.

### Financeiro

- `tests/architecture/test_financeiro_baseline_guards.py::test_registered_finance_api_routes_match_future_http_contract_matrix`
  - Falha: matriz futura espera rotas `DELETE` financeiras nao refletidas no
    runtime registrado.
- `tests/architecture/test_financeiro_baseline_guards.py::test_finance_stub_contract_matrix_is_explicit_and_disjoint_from_registered_routes`
  - Falha: divergencia entre matriz stub/future contract e rotas registradas.

### Tripulantes, treinamentos e documentos

- `tests/unit/test_tripulante_operational_status_owner.py::test_backend_queries_do_not_promote_tripulante_snapshots_as_primary_source`
  - Falha: offender `financeiro_calculos_horarios.py::status_alias_from_snapshot`.
- `tests/unit/test_media_storage.py::test_write_tripulante_photo_uses_tripulante_folder`
  - Falha: `PermissionError [WinError 5]` em `os.replace` para foto temporaria.
- `tests/unit/test_media_storage.py::test_write_documents_and_training_attachments_are_grouped_by_tripulante`
  - Falha: `PermissionError [WinError 5]` em `os.replace` para documento.
- `tests/contract/test_api_tripulante_media_contract.py::test_api_tripulante_photo_upload_persists_blob_and_get_returns_binary`
  - Falha: `PermissionError [WinError 5]` ao persistir foto.
- `tests/contract/test_api_tripulante_media_contract.py::test_api_tripulante_file_get_returns_binary`
  - Falha: `audit_relevant_download` em modo estrito tentou inserir
    `auditoria_eventos.realizado_por=31` sem usuario correspondente, causando
    violacao de FK.
- `tests/contract/test_api_treinamentos_contract.py::test_api_treinamento_attachment_get_returns_binary`
  - Falha: `audit_relevant_download` em modo estrito tentou inserir
    `auditoria_eventos.realizado_por=41` sem usuario correspondente, causando
    violacao de FK.
- `tests/integration/test_supertest_regression.py::test_bases_decode_photo_data_uri_accepts_jpg_and_webp`
  - Falha: `backend.src.controle_treinamentos.blueprints.bases.routes` nao tem
    atributo `_decode_photo_data_uri`.

### Rotas SPA/SSR/frontend

- `tests/contract/test_frontend_app_architecture_boundaries.py::test_route_registry_preserves_current_routes_loaders_exports_and_permissions`
  - Falha: route registry contem rotas financeiras extras de bonificacoes e
    lancamentos-jornada.
- `tests/contract/test_frontend_feature_boundaries.py::test_financeiro_feature_slicing_is_documented`
  - Falha: documentacao de arquitetura frontend nao contem a string esperada
    `Missoes Operacionais`.
- `tests/contract/test_frontend_priority_page_visual_foundation.py::test_dashboard_priority_surface_adopts_shared_ui_without_route_or_api_drift`
  - Falha: `dashboard-action-rail` ausente no dashboard.
- `tests/contract/test_frontend_readiness_consolidation.py::test_frontend_first_architecture_wave_has_material_boundaries`
  - Falha: modulo extra `financeiro-lancamentos-jornada-api.js`.
- `tests/contract/test_frontend_responsive_shell_refactor.py::test_shell_css_moves_sidebar_to_drawer_at_mobile_breakpoint`
  - Falha: CSS esperado `transform: translateX(-100%)` ausente.
- `tests/contract/test_frontend_service_state_boundaries.py::test_frontend_services_and_state_modules_exist_with_explicit_owners`
  - Falha: modulos extras em `frontend/src/services`.
- `tests/contract/test_frontend_sidebar_responsive_calibration.py::test_sidebar_mobile_uses_temporary_drawer_not_fixed_navigation_column`
  - Falha: CSS esperado de largura mobile do sidebar ausente.
- `tests/contract/test_frontend_third_surface_visual_foundation.py::test_tripulante_form_detail_preserves_functional_contracts`
  - Falha: texto/contrato funcional esperado de preview local de foto ausente.
- `tests/architecture/test_architecture_boundaries.py::test_critical_blueprints_are_split_to_smaller_modules`
  - Falha: `backend/src/controle_treinamentos/blueprints/admin/routes.py` com
    `810` linhas, acima do limite `725`.
- `tests/contract/test_frontend_ux_functional_guards.py`
  - Erro: build frontend em temp falhou com `PermissionError [WinError 5]` ao
    remover `runtime/pytest-baseline-p0-frontend-routes/frontend-dist0`.

### Banco, backup, jobs e ops

- `tests/unit/test_backup_operation_lock.py::test_backup_operation_lock_blocks_second_execution`
  - Falha: payload esperado do terceiro lock veio `None`; log registra falha ao
    liberar lock por `PermissionError [WinError 5]` em `.run_backup.lock`.
- `tests/unit/test_backup_operation_lock.py::test_backup_operation_lock_recovers_stale_lock`
  - Falha: payload de lock veio `None`.
- `tests/ops/test_release_e2e_homolog_entrypoints.py::test_harden_release_manifest_falls_back_when_workspace_has_no_git_repo`
  - Falha: `_git_head(REPO_ROOT)` retornou o HEAD real
    `66468738ee7248a02e16f5a89162759a3f0473f1`, mas o teste esperava
    `workspace-without-git`.

## 9. Riscos evidenciados

- Worktree sujo invalida qualquer leitura de baseline como referencia de commit
  limpo.
- Ha drift entre catalogo de permissoes, contratos futuros e rotas financeiras
  registradas.
- Contratos de erro 500 parecem propagar excecao em testes que esperavam envelope
  HTTP estavel.
- Downloads auditados podem falhar em modo estrito quando o usuario autenticado
  do teste nao existe na tabela `usuarios`.
- Operacoes de media/storage apresentam `PermissionError` em escrita atomica no
  Windows durante testes.
- Route registry/frontend contem divergencias de modulo, rotas, CSS e boundaries.
- Build frontend em diretorio temporario falhou por permissao ao remover arvore
  de saida.
- Backup lock apresentou falhas de release/stale lock em filesystem local.
- Suites de e2e/integracao com banco real existem, mas nao foram executadas por
  falta de ambiente isolado autorizado e por conterem bootstrap/CRUD/cleanup.
- Baseline P0 nao pode ser declarada verde nem verde com restricoes, porque ha
  falhas de contrato em areas P0 centrais.

## 10. Areas liberadas

Nenhuma macro-area P0 esta liberada para reorganizacao fisica.

Observacoes positivas, sem liberacao macro:

- Houve grande volume de testes passando em financeiro, auth, frontend, docs e
  ops.
- Testes unitarios/estaticos de restore validation, script guards, jobs queue e
  varias politicas executaram dentro do bloco P0-OPS-DB.
- Essas passagens sao evidencia util, mas nao compensam falhas P0 nem testes
  bloqueados.

## 11. Areas ainda bloqueadas

- Auth/session/RBAC/login/logout/falha.
- Capabilities, CSRF, cookies, 401/403 e erro HTTP.
- Endpoint-permission coverage.
- Financeiro missoes, jornada, recalculo, fechamento/reabertura, parametros,
  feriados, relatorios e PDFs.
- Tripulantes CRUD, treinamentos CRUD, anexos, fotos e documentos.
- Cadastro raiz.
- Rotas SPA, SSR, aliases, redirects e deep links.
- PDF/CSV/relatorios.
- Banco/schema/repositories.
- Backup lock.
- Restore validation real.
- Jobs/dead-letter como macro-area operacional.
- Scripts operacionais, cleanup, migration, repair e seed.

## 12. Arquivo de evidencia criado

- `docs/release-gates/baseline-p0-execution.md`

Arquivos de saida adicionais:

- Nenhum junit/xml/html foi gerado.
- Saidas relevantes de stdout/stderr foram consolidadas neste documento.
- Diretorios temporarios de pytest foram criados em `runtime/pytest-baseline-p0-*`
  e estao ignorados pelo Git.

## 13. Decisao da baseline

Decisao: `VERMELHA`.

Motivos:

- Houve falhas em testes P0 executados.
- Houve erros em testes P0 executados.
- Houve testes P0 bloqueados por falta de ambiente isolado seguro.
- Houve tentativa invalida de comando registrada, sem mascarar o resultado.
- Nao ha base objetiva para declarar area verde sem execucao limpa.

A reorganizacao fisica permanece bloqueada.

## 14. Proximo passo recomendado

Congelar novas reorganizacoes fisicas e abrir uma rodada de triagem P0, sem
misturar correcao com a evidencia inicial:

- Classificar falhas por owner: auth/RBAC, financeiro, frontend rotas, documentos,
  storage, auditoria/download, backup/ops.
- Preparar ambiente isolado para e2e e integracoes com banco real, com DB de
  teste descartavel e autorizacao explicita.
- Reexecutar somente apos correcoes revisadas, mantendo este relatorio como
  baseline vermelha inicial.
