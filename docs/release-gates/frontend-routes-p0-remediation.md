# Frontend Routes P0 Remediation

## Resumo executivo

Remediacao do bloco P0-FRONTEND-ROUTES da Frente 1.5 para rotas SPA,
aliases, boundaries frontend, CSS responsivo e estabilidade de navegacao.

A baseline registrava `236 passed, 9 failed, 4 errors`. A reproducao local em
temp do sistema eliminou os errors de cleanup/build e deixou 8 falhas
reproduzidas. Foram corrigidas as falhas diretamente ligadas a rotas,
aliases, CSS, frontend boundaries, dashboard e microcopy funcional.

Resultado final:

- Recorte frontend/routes sem o boundary backend de tamanho:
  `215 passed in 33.49s`
- Recorte amplo com o teste arquitetural backend incluido:
  `216 passed, 1 failed`

A falha remanescente e
`tests/architecture/test_architecture_boundaries.py::test_critical_blueprints_are_split_to_smaller_modules`,
por `backend/src/controle_treinamentos/blueprints/admin/routes.py:810>725`.
Ela exige refatoracao fisica de blueprint backend e permanece bloqueada fora
desta remediacao de rotas/frontend.

## Contexto observado

- Branch: `safety-baseline-financeiro-20260602-193550`
- Working tree: suja antes da remediacao, com alteracoes preexistentes fora
  deste escopo.
- Baseline consultada: `docs/release-gates/baseline-p0-execution.md`
- Freeze map consultado: `docs/release-gates/routes-aliases-freeze-map.md`

## Testes falhos identificados

Falhas reproduzidas no recorte frontend/routes:

- `tests/contract/test_frontend_app_architecture_boundaries.py::test_route_registry_preserves_current_routes_loaders_exports_and_permissions`
- `tests/contract/test_frontend_feature_boundaries.py::test_financeiro_feature_slicing_is_documented`
- `tests/contract/test_frontend_priority_page_visual_foundation.py::test_dashboard_priority_surface_adopts_shared_ui_without_route_or_api_drift`
- `tests/contract/test_frontend_readiness_consolidation.py::test_frontend_first_architecture_wave_has_material_boundaries`
- `tests/contract/test_frontend_responsive_shell_refactor.py::test_shell_css_moves_sidebar_to_drawer_at_mobile_breakpoint`
- `tests/contract/test_frontend_sidebar_responsive_calibration.py::test_sidebar_mobile_uses_temporary_drawer_not_fixed_navigation_column`
- `tests/contract/test_frontend_third_surface_visual_foundation.py::test_tripulante_form_detail_preserves_functional_contracts`
- `tests/architecture/test_responsive_finance_visual_contract.py::test_mobile_sidebar_drawer_open_state_is_visible_and_overlay_is_scoped_to_drawer`
- `tests/architecture/test_architecture_boundaries.py::test_critical_blueprints_are_split_to_smaller_modules`

Errors da baseline em `test_frontend_ux_functional_guards.py` nao foram
reproduzidos ao usar `--basetemp` no temp do sistema; foram classificados como
problema de path temporario/cleanup no workspace gerenciado.

## Causa raiz por falha

1. Route registry:
   - Classificacao: teste desatualizado perante freeze map.
   - Causa: aliases financeiros e `#/financeiro/lancamentos-jornada` estavam
     registrados e congelados, mas o teste ainda os tratava como extras.
   - Correcao: matriz esperada do teste passou a incluir as rotas/aliases
     congelados.

2. Documentacao financeiro:
   - Classificacao: boundary/documentacao incompleta.
   - Causa: `FRONTEND_ARCHITECTURE.md` nao continha a forma ASCII
     `Missoes Operacionais` esperada pelo contrato.
   - Correcao: documentacao passou a registrar `Missoes Operacionais` junto da
     forma acentuada existente.

3. Dashboard action rail:
   - Classificacao: marcador visual/funcional ausente.
   - Causa: `renderDashboardActions` retornava string vazia apesar do CSS e do
     contrato esperarem `dashboard-action-rail`.
   - Correcao: rail aditivo com links ja congelados para vencidos,
     `#/treinamentos/raiz` e `BACKEND_LINKS.equipamentos`.

4. Services/boundaries:
   - Classificacao: modulo extra nao registrado na matriz de readiness.
   - Causa: `financeiro-lancamentos-jornada-api.js` e modulo vivo, mas a suite
     de readiness nao o aceitava.
   - Correcao: teste de readiness atualizado para incluir o service.

5. CSS responsivo shell/sidebar:
   - Classificacao: CSS responsivo divergente entre contratos.
   - Causa: contratos distintos esperavam `translateX` e `translate3d`, alem de
     largura tokenizada e largura legacy.
   - Correcao: CSS manteve linhas legacy e tokenizadas em cascata; valores
     efetivos usam tokens, e os contratos estaticos antigos continuam
     reconhecendo o drawer.

6. Preview local de foto:
   - Classificacao: microcopy funcional divergente.
   - Causa: texto de estado local estava em ASCII e com frase diferente.
   - Correcao: microcopy restaurada para `pre-visualizacao local; ainda nao salva`
     na forma acentuada usada pela tela.

7. Blueprint admin:
   - Classificacao: boundary backend fora do escopo seguro desta frente.
   - Causa: `admin/routes.py` tem 810 linhas contra limite 725.
   - Status: bloqueio remanescente documentado; nao foi feita refatoracao fisica
     de blueprint nesta remediacao de rotas/frontend.

## Arquivos alterados

- `frontend/src/features/dashboard/page.js`
- `frontend/src/features/tripulantes/form-page.js`
- `frontend/src/app.css`
- `docs/architecture/FRONTEND_ARCHITECTURE.md`
- `tests/contract/test_frontend_app_architecture_boundaries.py`
- `tests/contract/test_frontend_readiness_consolidation.py`
- `docs/release-gates/frontend-routes-p0-remediation.md`

Arquivos de rota/alias preservados sem alteracao nesta remediacao:

- `frontend/src/app/route-registry.js`
- `frontend/src/app/router.js`
- `frontend/src/app/bootstrap.js`
- `frontend/src/shell/navigation.js`
- `frontend/src/compat/backend-links.js`

## Rotas preservadas

Nenhuma rota foi removida, renomeada ou redirecionada.

Rotas SPA congeladas preservadas:

- `#/dashboard`
- `#/dashboard-operacional`
- `#/dashboard-operacional-tv`
- `#/tripulantes`
- `#/tripulantes/new`
- `#/tripulantes/<id>`
- `#/treinamentos`
- `#/treinamentos/new`
- `#/treinamentos/<id>`
- `#/treinamentos/raiz`
- `#/relatorios/habilitacoes`
- `#/relatorios/individual`
- `#/financeiro/missoes`
- `#/financeiro/lancamentos-jornada`
- `#/financeiro/fechamento-parametros`

## Aliases preservados

Aliases congelados preservados:

- `#/financeiro/bonificacoes`
- `#/financeiro/bonificacoes/horaria`
- `#/financeiro/bonificacoes/produtividade`
- `/tipos`
- `/tipos-treinamento`
- `/dashboard`
- `/tripulantes`
- `/treinamentos`
- `/treinamentos/consolidado`

Nenhum redirect foi alterado.

## Boundaries corrigidas

- Route registry: contrato de teste alinhado ao freeze map.
- Services: matriz de readiness reconhece `financeiro-lancamentos-jornada-api.js`.
- Documentacao: owner financeiro registra Missoes Operacionais e jornada.
- CSS: drawer mobile preserva contratos `translate3d`, `translateX`, largura
  legacy e token `--size-sidebar-mobile-width`.
- Dashboard: `dashboard-action-rail` voltou como container aditivo usando links
  existentes.
- Tripulantes: microcopy funcional de preview local voltou ao contrato esperado.

## Testes reexecutados

Reproducao inicial em temp do sistema:

```text
8 failed, 209 passed
```

Validacao focada das sete falhas frontend corrigidas:

```text
7 passed in 0.58s
```

Validacao focada CSS drawer:

```text
3 passed in 0.15s
```

Recorte frontend/routes sem boundary backend:

```text
215 passed in 33.49s
```

Recorte amplo com boundary backend:

```text
216 passed, 1 failed in 33.55s
```

## Comandos operacionais nao executados

Os comandos abaixo foram deliberadamente NAO EXECUTADOS:

- Remocao de rota - NAO EXECUTADO
- Rename de rota - NAO EXECUTADO
- Alteracao de alias - NAO EXECUTADO
- Alteracao de redirect backend - NAO EXECUTADO
- Alteracao de PDF/CSV/export path - NAO EXECUTADO
- Build/deploy real de producao - NAO EXECUTADO
- Smoke em endpoint real - NAO EXECUTADO
- Migration/seed/schema - NAO EXECUTADO
- Cleanup de artefatos reais - NAO EXECUTADO

## Resultado pos-correcao

Rotas, aliases, frontend boundaries, CSS responsivo e guards do recorte
frontend/routes ficaram verdes no recorte seguro:

```text
215 passed in 33.49s
```

O bloco amplo ainda tem bloqueio remanescente por boundary backend:

```text
tests/architecture/test_architecture_boundaries.py::test_critical_blueprints_are_split_to_smaller_modules
backend/src/controle_treinamentos/blueprints/admin/routes.py:810>725
```

## Riscos remanescentes

- A working tree permanece suja por alteracoes preexistentes.
- O teste de tamanho do blueprint admin exige frente separada de refatoracao
  backend, com preservacao de decorators, endpoints, permissoes e links SSR.
- Esta remediacao nao substitui smoke humano/browser de navegacao.
- Builds reais e artefatos `frontend/dist` nao foram promovidos nem alterados.

## Proximo passo recomendado

Abrir frente separada para split seguro de
`backend/src/controle_treinamentos/blueprints/admin/routes.py`, com teste de
contrato de decorators/permissions antes e depois. Depois disso, reexecutar a
baseline P0 consolidada.
