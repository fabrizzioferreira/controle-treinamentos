# Auth/RBAC P0 Remediation

Data: 2026-06-06
Status: REMEDIADO NO SUBCONJUNTO P0-AUTH-SEC
Branch observada: `safety-baseline-financeiro-20260602-193550`
Escopo: Auth, RBAC, session, CSRF, cookies, capabilities, error envelope, endpoint-permission coverage e guardas frontend incluidos no bloco P0-AUTH-SEC.

Este documento registra investigacao e correcao minima das falhas P0-AUTH-SEC da baseline vermelha da Frente 1.5. Nenhum endpoint destrutivo foi chamado. Nenhuma migration foi executada. Nenhum seed foi executado. Nenhum schema foi alterado. Nenhuma permissao foi relaxada.

## 1. Resumo executivo

A baseline vermelha registrou `169 passed, 7 failed, 4 errors` no bloco P0-AUTH-SEC. A reexecucao inicial reproduziu o mesmo padrao:

- 7 falhas.
- 4 erros.
- 169 testes passando.

Apos a remediacao minima, o bloco P0-AUTH-SEC foi reexecutado com sucesso:

- Resultado final: `180 passed in 71.45s`.
- Falhas remanescentes no bloco P0-AUTH-SEC: nenhuma.
- Erros remanescentes no bloco P0-AUTH-SEC: nenhum.

## 2. Testes falhos identificados

Falhas reproduzidas antes da correcao:

- `tests/unit/test_auth_permissions.py::test_finance_permissions_are_registered_in_catalog`
- `tests/unit/test_auth_permissions.py::test_finance_endpoint_mappings_match_runtime_http_contracts`
- `tests/contract/test_http_error_contract.py::test_api_500_returns_json_contract`
- `tests/contract/test_http_error_contract.py::test_api_error_roundtrips_request_and_correlation_ids`
- `tests/contract/test_http_error_contract.py::test_html_500_returns_stable_error_page_without_redirect`
- `tests/contract/test_http_error_contract.py::test_internal_error_trace_returns_event_for_known_request_id`
- `tests/contract/test_frontend_service_state_boundaries.py::test_frontend_services_and_state_modules_exist_with_explicit_owners`
- Erros de setup em quatro testes de `tests/contract/test_frontend_ux_functional_guards.py`, causados por falha de criacao de diretorio temporario global do pytest no Windows.

## 3. Causa raiz por falha

| Falha | Classificacao | Causa raiz |
| --- | --- | --- |
| Permissao extra `finance:missions:delete` | Teste desatualizado / divergencia de matriz | O runtime, o contrato HTTP financeiro e os eventos de auditoria ja reconheciam delete de missao como permissao explicita. O teste ainda esperava matriz antiga sem delete. |
| Endpoint-permission coverage financeiro | Teste desatualizado / contrato inconsistente | O teste nao comparava `DELETE` e nao normalizava `<int:linha_id>` para `{id}`, embora a matriz canonica financeira ja fizesse isso em outros testes. |
| Contratos 500 API/HTML | Bug real de configuracao de teste | Em `APP_ENV=testing`, Flask propagava excecoes pelo test client e desviava dos handlers de erro, quebrando o contrato de envelope/HTML. |
| Trace interno por request id | Consequencia do bug de erro 500 | Como a excecao escapava, o evento de erro nao era lembrado/persistido pelo handler. |
| Services frontend extras | Teste desatualizado / contrato inconsistente | Novos services financeiros vivos existiam em `frontend/src/services`, mas o teste e a documentacao de owners ainda listavam apenas o primeiro service financeiro. |
| Erros de `tmp_path_factory` | Lacuna de fixture / ambiente | O temp global do Windows estava saturado/bloqueado para criar `pytest-*`; o teste nem chegava a executar o build frontend. |

## 4. Correcoes aplicadas

- `backend/src/controle_treinamentos/__init__.py`
  - Define `PROPAGATE_EXCEPTIONS=False` no app para preservar handlers de erro tambem em `APP_ENV=testing`.
- `tests/unit/test_auth_permissions.py`
  - Inclui `finance:missions:delete` na expectativa do catalogo financeiro.
  - Inclui `DELETE` na comparacao de endpoints financeiros.
  - Normaliza `<int:linha_id>` como `{id}`.
- `tests/contract/test_frontend_service_state_boundaries.py`
  - Inclui os services financeiros vivos na lista esperada.
  - Exige exports minimos desses services.
  - Exige documentacao de ownership para esses services.
- `tests/contract/test_frontend_ux_functional_guards.py`
  - Move o output temporario do build para `runtime/pytest-frontend-ux-functional-guards/<uuid>`, evitando dependencia do temp global do Windows.
- `docs/architecture/FRONTEND_ARCHITECTURE.md`
  - Registra ownership e limites dos services financeiros novos.

## 5. Contratos preservados

- Auth/session/capabilities permanecem com os contratos congelados.
- 401 continua representando usuario nao autenticado ou sessao invalida/expirada.
- 403 continua representando usuario autenticado sem permissao ou usuario inativo.
- 409 e 422 continuam mapeados para envelopes JSON estaveis nos endpoints programaticos.
- Error envelope preserva `success`, `message`, `status`, `request_id`, `correlation_id`, `code` e `details` quando aplicavel.
- Rotas e paths publicos nao foram alterados.
- Nenhum contrato publico foi relaxado.

## 6. Permissoes preservadas ou ajustadas

Permissoes preservadas:

- `DEFAULT_OPERATOR_PERMISSIONS` continua sem escopo `finance:*`.
- `FINANCE_ROLE_PERMISSION_SETS["operacoes"]` continua limitado a leitura/criacao/edicao operacional e leitura de bonus.
- `FINANCE_ROLE_PERMISSION_SETS["auditor"]` e `["leitura"]` continuam sem permissao de mutacao.
- `ENDPOINT_PERMISSION_MAP` segue deny-by-default para endpoints namespaced nao mapeados.

Permissao ajustada no teste:

- `finance:missions:delete` foi reconhecida como permissao explicita ja existente no runtime e no contrato HTTP. Isso nao concede permissao a operador padrao e nao relaxa RBAC.

## 7. Riscos mitigados

- Excecoes 500 deixam de vazar pelo test client em `testing` e voltam a validar o handler contratual.
- Endpoint-permission coverage passa a cobrir `DELETE` financeiro.
- A rota de jornada com `<int:linha_id>` passa a ser comparada contra o contrato canonico `{id}`.
- Services financeiros novos deixam de aparecer como owners implicitos sem documentacao.
- Guardas frontend deixam de depender do temp global do Windows para gerar dist temporario.

## 8. Testes reexecutados

Reexecucao direcionada das falhas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings tests/unit/test_auth_permissions.py::test_finance_permissions_are_registered_in_catalog tests/unit/test_auth_permissions.py::test_finance_endpoint_mappings_match_runtime_http_contracts tests/contract/test_http_error_contract.py::test_api_500_returns_json_contract tests/contract/test_http_error_contract.py::test_api_error_roundtrips_request_and_correlation_ids tests/contract/test_http_error_contract.py::test_html_500_returns_stable_error_page_without_redirect tests/contract/test_http_error_contract.py::test_internal_error_trace_returns_event_for_known_request_id tests/contract/test_frontend_service_state_boundaries.py::test_frontend_services_and_state_modules_exist_with_explicit_owners tests/contract/test_frontend_ux_functional_guards.py::test_frontend_api_feedback_and_error_guards_are_present
```

Resultado: `8 passed in 3.40s`.

Reexecucao completa P0-AUTH-SEC:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings tests/unit/test_auth_permissions.py tests/unit/test_auth_session_touch_policy.py tests/unit/test_user_loader_request_cache.py tests/unit/test_login_resilience.py tests/unit/test_session_cookie_config.py tests/unit/test_security_headers.py tests/unit/test_http_utils_security.py tests/unit/test_http_request_logging_policy.py tests/unit/test_endpoint_permission_coverage.py tests/unit/test_app_security_config.py tests/unit/test_boot_fallback_security.py tests/contract/test_api_session_contract.py tests/contract/test_auth_semantics_matrix_contract.py tests/contract/test_session_lifecycle_contract.py tests/contract/test_http_error_contract.py tests/contract/test_api_cors_contract.py tests/contract/test_frontend_ux_functional_guards.py tests/contract/test_frontend_service_state_boundaries.py
```

Ambiente da execucao:

- `APP_ENV=testing`
- `DATABASE_URL` removido no processo de teste.
- `E2E_DATABASE_URL` removido no processo de teste.
- `PYTHONDONTWRITEBYTECODE=1`

Resultado final: `180 passed in 71.45s`.

## 9. Resultado pos-correcao

O subconjunto P0-AUTH-SEC passou integralmente.

Nao houve:

- Relaxamento de RBAC.
- Ampliacao de permissao para operador padrao.
- Remocao de teste.
- Alteracao de schema.
- Migration.
- Seed.
- Chamada de endpoint destrutivo.
- Mudanca de contrato publico de auth/session/capabilities.

## 10. Riscos remanescentes

- O working tree geral permanece sujo por alteracoes preexistentes fora desta remediacao.
- A baseline P0 completa da Frente 1.5 ainda permanece vermelha ate os demais blocos serem remediados e reexecutados.
- Suites de e2e, banco real, restore, cleanup, migration e seed continuam fora deste escopo.
- A validacao humana final do release gate ainda precisa ser registrada.

## 11. Proximo passo recomendado

Executar uma rodada de review focada nestas mudancas e seguir para o proximo bloco P0 ainda vermelho. Antes de reabrir o release gate da reorganizacao fisica, reexecutar todos os blocos P0 em ambiente isolado e registrar nova decisao consolidada.
