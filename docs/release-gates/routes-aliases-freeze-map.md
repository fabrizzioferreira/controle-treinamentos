# Routes, Aliases and Deep Links Freeze Map

Data do congelamento: 2026-06-06
Status: BLOQUEADO PARA REORGANIZACAO FISICA
Dependencia direta: `docs/release-gates/contract-freeze-register.md`

Este documento e o mapa oficial de congelamento de rotas SPA, rotas
SSR/backend, aliases, redirects, deep links, PDFs, CSVs, exports e fallbacks
operacionais antes de qualquer move, rename, limpeza, refatoracao,
padronizacao ou reorganizacao fisica do repositorio.

Regra central: rota, alias, redirect, link de menu, link de template, hash
route, backend link, PDF, CSV ou path operacional so pode mudar fora da
reorganizacao fisica, com teste de contrato, telemetria de uso quando aplicavel
e validacao humana explicita. A ausencia de menu nao significa ausencia de
contrato.

## 1. Resumo executivo

A leitura confirmou que a aplicacao possui quatro superficies de rota vivas e
interdependentes:

- SPA hash routes em `frontend/src/app/route-registry.js`,
  `frontend/src/app/router.js`, `frontend/src/app/bootstrap.js` e
  `frontend/src/state/navigation-state.js`.
- Navegacao e links de compatibilidade em `frontend/src/shell/navigation.js`,
  `frontend/src/compat/backend-links.js`, `frontend/src/shell/login.js`,
  `frontend/src/shell/render-shell.js` e `frontend/src/shell/redirects.js`.
- Rotas Flask SSR/backend, APIs e exports em `backend/src/controle_treinamentos`
  sob `blueprints/**`, `api/http/**`, `core/frontend_routes.py`,
  `auth.py` e `contracts/financeiro_http.py`.
- Links hardcoded/documentados em templates, docs e scripts operacionais, em
  especial `backend/src/controle_treinamentos/templates/base.html`,
  `backend/src/controle_treinamentos/templates/dashboard.html`,
  `docs/architecture/FRONTEND_ARCHITECTURE.md`,
  `docs/migration/*.md`, `ops/scripts/**` e `ops/windows/caddy/Caddyfile.example`.

Decisao geral: congelar rotas criticas como contratos vivos. Rotas citadas
apenas em documentos historicos ou artefatos gerados ficam como "validar" ou
"revisar depois", nunca como removiveis por estetica. A baseline P0 registrada
em `docs/release-gates/baseline-p0-execution.md` esta VERMELHA e inclui falhas
em rotas SPA/SSR/frontend; portanto este mapa nao libera reorganizacao.

## 2. Arquivo criado

Arquivo de gate criado: `docs/release-gates/routes-aliases-freeze-map.md`.

Escopo deste arquivo:

- Documentar o estado atual observado.
- Congelar paths, hashes, aliases, redirects e deep links.
- Marcar lacunas sem executar endpoints nem alterar codigo.
- Servir como pre-condicao documental para qualquer discussao posterior de move
  fisico.

Fora do escopo:

- Alterar route registry, router, navigation, backend-links, templates, guards ou
  permissoes.
- Executar endpoints, scripts sensiveis, migrations, cleanup, restore ou jobs.
- Normalizar nomenclaturas ou transformar rotas SSR em SPA.

## 3. Rotas SPA canonicas

Fonte principal: `frontend/src/app/route-registry.js`.

| Path | Tipo | Origem | Renderizador | Permissao | Menu | Consumidores | Risco se mudar | Decisao |
|---|---|---|---|---|---|---|---|---|
| `#/dashboard` | SPA canonica | `staticRouteDefinitions` | `renderDashboardPage` | `dashboard:view` | Sim, primario | `navigation.js`, bootstrap landing, templates SSR, scripts smoke | Quebra primeira tela, landing, bookmarks e redirects `/dashboard` | congelar |
| `#/dashboard-operacional` | SPA canonica | `staticRouteDefinitions` | `renderOperationalDashboardPage` | `dashboard:view` | Sim | `navigation.js`, dashboard operacional, docs arquitetura | Quebra painel operacional e atalhos de bases/treinamentos | congelar |
| `#/dashboard-operacional-tv` | SPA canonica sem menu | `staticRouteDefinitions` | `renderOperationalDashboardTvPage` | `dashboard:view` | Nao | TV/deep link operacional | Quebra exibicao TV ou bookmark direto sem evidencia no menu | congelar |
| `#/tripulantes` | SPA canonica | `staticRouteDefinitions` | `renderTripulantesListPage` | `tripulantes:view` ou `relatorio_individual:view` | Sim | `navigation.js`, templates, financeiro missoes, relatorios | Quebra CRUD, relatorio individual e seletores financeiros | congelar |
| `#/tripulantes/new` | SPA canonica interna | `staticRouteDefinitions` | `renderTripulanteFormPage` | `tripulantes:create` | Nao | Pagina de tripulantes, redirects SSR `/tripulantes/novo` | Quebra criacao via SPA e compat GET legado | congelar |
| `#/tripulantes/<id>` | SPA dinamica | `dynamicRouteDefinitions` | `renderTripulanteFormPage` | `tripulantes:edit` | Nao direto | Dashboard, templates, relatorio individual, deep links | Quebra bookmarks de detalhe, docs e edicao | congelar |
| `#/treinamentos` | SPA canonica | `staticRouteDefinitions` | `renderTreinamentosListPage` | `treinamentos:view` | Sim | `navigation.js`, dashboard, relatorios, templates | Quebra lista, filtros e dashboard | congelar |
| `#/treinamentos/new` | SPA canonica interna | `staticRouteDefinitions` | `renderTreinamentosListPage` | `treinamentos:create` | Nao | SPA treinamentos, redirect SSR `/treinamentos/novo` | Quebra criacao e importacao de programa | congelar |
| `#/treinamentos/<id>` | SPA dinamica | `dynamicRouteDefinitions` | `renderTreinamentoFormPage` | `treinamentos:edit` | Nao direto | Dashboard SSR/SPA, calendario, docs | Quebra deep link de treinamento e edicao | congelar |
| `#/treinamentos/raiz` | SPA canonica | `staticRouteDefinitions` | `renderTrainingRootPage` | `tipos_treinamento:view` | Sim | `navigation.js`, `backend-links.js`, redirects `/tipos-treinamento` e alias `/tipos` | Quebra cadastro raiz, tipos, segmentos, horas de voo e reentrada | congelar |
| `#/relatorios/habilitacoes` | SPA canonica | `staticRouteDefinitions` | `renderRelatorioHabilitacoesPage` | `relatorio_habilitacoes:view` | Sim | `navigation.js`, `/treinamentos/consolidado`, PDF/CSV/export | Quebra filtros, relatorio consolidado e exports | congelar |
| `#/relatorios/individual` | SPA canonica | `staticRouteDefinitions` | `renderRelatorioIndividualPage` | `relatorio_individual:view` | Sim | `navigation.js`, templates de relatorio individual | Quebra seletor oficial de relatorio individual | congelar |
| `#/financeiro/missoes` | SPA canonica financeira | `staticRouteDefinitions` | `renderFinanceiroMissoesPage` | `finance:missions:read` | Nao no menu atual | `pages-financeiro.js`, services financeiros, docs arquitetura | Quebra missoes financeiras e entradas documentadas | congelar |
| `#/financeiro/lancamentos-jornada` | SPA canonica financeira | `staticRouteDefinitions` | `renderFinanceiroLancamentosJornadaPage` | `finance:bonuses:read` | Sim | `navigation.js`, aliases de bonificacoes, services de jornada | Quebra lancamentos, grade, PDFs e pagamentos | congelar |
| `#/financeiro/fechamento-parametros` | SPA canonica financeira | `staticRouteDefinitions` | `renderFinanceiroFechamentoParametrosPage` | `finance:parameters:read` ou `finance:periods:read` | Sim | `navigation.js`, services parametros/feriados/competencias | Quebra fechamento, reabertura, parametros e auditoria financeira | congelar |

Regra de evolucao: nenhuma alteracao de path, permissao, renderizador ou
semantica de hash durante reorganizacao. Novas rotas so podem ser aditivas,
com teste de contrato e validacao humana quando tocarem financeiro, RBAC,
documentos ou operacao.

## 4. Rotas SPA internas

| Path/comportamento | Tipo | Origem | Consumidor | Risco se mudar | Decisao |
|---|---|---|---|---|---|
| `#/login` | SPA interna de auth | `frontend/src/state/navigation-state.js`, `frontend/src/app/bootstrap.js`, `frontend/src/shell/login.js` | Login, api-client, logout SPA | Quebra login, retorno pos-login e sessao expirada | congelar |
| Hash vazio autenticado | redirect interno | `bootstrap.js` | Entrada em `/` ou app vazio | Pode mandar usuario para tela errada | congelar comportamento |
| Rota nao registrada | not found interno | `bootstrap.js` | Qualquer hash desconhecido | Pode mascarar links quebrados ou mudar UX de erro | congelar comportamento |
| Rota sem permissao | forbidden interno | `bootstrap.js`, `frontend/src/app/guards.js` | RBAC frontend | Pode expor tela ou esconder permissao indevida | congelar comportamento |
| Return route | memoria de navegacao | `navigation-state.js`, `login.js` | Login com `next`, sessao expirada | Pode perder deep link do usuario | congelar comportamento |
| Last successful route | memoria de navegacao | `navigation-state.js`, `bootstrap.js` | Landing autenticado | Pode voltar sempre para dashboard indevidamente | congelar comportamento |
| Query de hash | parser SPA | `routeKeyFromHash`, `hashQuery`, paginas SPA | Filtros de `#/treinamentos`, `#/relatorios/habilitacoes`, financeiro | Pode descartar filtros e exports | congelar semantica |

Observacao: `#/login` nao aparece no `route-registry.js`, mas e rota interna
viva por contrato de sessao. Nao deve ser tratada como orfa removivel.

## 5. Aliases

| Alias | Destino atual | Origem | Produtor/adapter | Consumidores | Risco se mudar | Decisao |
|---|---|---|---|---|---|---|
| `#/financeiro/bonificacoes` | `renderFinanceiroLancamentosJornadaPage` | `route-registry.js` | Frontend SPA | Bookmarks financeiros antigos, `navigation.js` active match | Quebra reentrada historica de bonus | congelar |
| `#/financeiro/bonificacoes/horaria` | `renderFinanceiroLancamentosJornadaPage` | `route-registry.js` | Frontend SPA | Bookmarks de bonificacao horaria | Quebra operadores com link antigo | congelar |
| `#/financeiro/bonificacoes/produtividade` | `renderFinanceiroLancamentosJornadaPage` | `route-registry.js` | Frontend SPA | Bookmarks de produtividade | Quebra reentrada de produtividade financeira | congelar |
| `/tipos` | `#/treinamentos/raiz` | `LEGACY_BACKEND_PATH_ALIASES` | `backend-links.js` | Login destination resolver, docs historicos | Alias historico perde canonicalizacao | congelar adapter; validar uso real |
| `/tipos-treinamento` | `#/treinamentos/raiz` quando compat ativo | `FRONTEND_HASH_BY_BACKEND_PATH`, `routes_catalogos.py` | Frontend adapter + Flask redirect | Menu backend link, docs e bookmarks | Pode renderizar SSR legado ou quebrar cadastro raiz | congelar |
| `/dashboard` | `#/dashboard` quando compat ativo | `FRONTEND_HASH_BY_BACKEND_PATH`, `dashboard/routes.py` | Frontend adapter + Flask redirect | Landing SSR, scripts smoke | Quebra entrada pos-login e smoke | congelar |
| `/tripulantes` | `#/tripulantes` | `FRONTEND_HASH_BY_BACKEND_PATH`, `routes.py` | Frontend adapter + Flask redirect | Bookmarks, templates, docs | Quebra lista/compat | congelar |
| `/treinamentos` | `#/treinamentos` | `FRONTEND_HASH_BY_BACKEND_PATH`, `routes_treinamentos.py` | Frontend adapter + Flask redirect | Bookmarks, templates, docs | Quebra lista/compat | congelar |
| `/treinamentos/consolidado` | `#/relatorios/habilitacoes` | `FRONTEND_HASH_BY_BACKEND_PATH`, `routes_treinamentos.py` | Frontend adapter + Flask redirect | Relatorio consolidado, exports | Filtros de relatorio deixam de migrar para SPA | congelar |

Regra de evolucao: aliases tem classificacao "nenhuma" durante reorganizacao.
Remocao exige telemetria humana, teste de contrato e aceite de produto/operacao.

## 6. Rotas SSR/backend

Fontes: `backend/src/controle_treinamentos/blueprints/**`,
`backend/src/controle_treinamentos/api/http/**`,
`backend/src/controle_treinamentos/__init__.py`,
`backend/src/controle_treinamentos/auth.py`.

### Auth, sessao e internos

| Path | Metodo | Produtor | Permissao | Consumidor | Decisao |
|---|---|---|---|---|---|
| `/` | GET | `blueprints/dashboard/routes.py` | publico/landing | Browser, root app | congelar redirect |
| `/login` | GET/POST | `blueprints/auth/routes.py` | publico | Login SSR e compat frontend | congelar |
| `/logout` | GET/POST | `blueprints/auth/routes.py` | publico | Logout SSR e compat | congelar |
| `/api/v1/session` | GET | `blueprints/auth/routes.py` | publico | `session-service.js`, e2e scripts | congelar |
| `/api/v1/session/login` | POST | `blueprints/auth/routes.py` | publico + CSRF | `login.js`, scripts e2e | congelar |
| `/api/v1/session/logout` | POST | `blueprints/auth/routes.py` | publico + CSRF | `render-shell.js`, scripts e2e | congelar |
| `/api/v1/me` | GET | `blueprints/auth/routes.py` | autenticado | e2e, consumers de sessao | congelar |
| `/api/v1/capabilities` | GET | `blueprints/auth/routes.py` | autenticado | RBAC frontend | congelar |
| `/healthz` | GET | `__init__.py` | publico/operacional | smoke/release | congelar |
| `/api/internal/metrics` | GET | `__init__.py` | token interno | smoke/release/monitoramento | congelar |
| `/api/internal/errors/<request_id>` | GET | `__init__.py` | interno/suporte | suporte e auditoria tecnica | congelar |

### Admin, auditoria, backups e operacao

| Path/padrao | Metodo | Produtor | Permissao | Consumidor | Decisao |
|---|---|---|---|---|---|
| `/usuarios` | GET | `blueprints/admin/routes.py` | `usuarios:view` | `navigation.js`, SSR admin | congelar |
| `/usuarios/novo` | GET/POST | `blueprints/admin/routes.py` | `usuarios:manage` | `BACKEND_LINKS.usuariosNew`, SSR admin | congelar |
| `/usuarios/<id>/editar` | GET/POST | `blueprints/admin/routes.py` | `usuarios:manage` | SSR admin | congelar |
| `/auditoria` | GET | `blueprints/admin/routes.py` | `auditoria:view` | `navigation.js`, suporte | congelar |
| `/auditoria/export.pdf` | GET | `blueprints/admin/routes.py` | `auditoria:view` | Browser/download, auditoria | congelar |
| `/notificacoes-email` | GET | `blueprints/admin/routes.py` | `notificacoes:view` | `navigation.js`, topbar, smoke | congelar |
| `/notificacoes-email/novo` | GET/POST | `blueprints/admin/routes.py` | `notificacoes:edit` | SSR admin | congelar |
| `/notificacoes-email/<id>/editar` | GET/POST | `blueprints/admin/routes.py` | `notificacoes:edit` | SSR admin | congelar |
| `/notificacoes-email/disparo-manual` | POST | `blueprints/admin/routes.py` | `notificacoes:edit` | Operacao manual | congelar |
| `/notificacoes-email/teste` | POST | `blueprints/admin/routes.py` | `notificacoes:edit` | Teste manual operacional | congelar |
| `/backups` | GET | `blueprints/admin/routes_operacional.py` | `backups:view` | `navigation.js`, operacao | congelar |
| `/backups/executar` | POST | `blueprints/admin/routes_operacional.py` | `backups:run` | Painel de backups | congelar |
| `/monitoramento` | GET | `blueprints/admin/routes_operacional.py` | `monitoramento:view` | `navigation.js`, operacao | congelar |
| `/jobs/<id>/reativar` | POST | `blueprints/admin/routes_operacional.py` | `usuarios:manage` | Monitoramento/dead-letter | congelar |
| `/jobs/<id>/status` | GET | `blueprints/admin/routes_operacional.py` | `usuarios:manage` | Monitoramento/dead-letter | congelar |
| `/manual/usuario.pdf` | GET | `blueprints/admin/routes_operacional.py` | `monitoramento:view` | `navigation.js`, browser/download | congelar |

### Bases, pernoites e cadastros SSR/fallback

| Path/padrao | Metodo | Produtor | Permissao | Consumidor | Decisao |
|---|---|---|---|---|---|
| `/bases` | GET | `blueprints/bases/routes.py` | `bases:view` | `navigation.js`, dashboard operacional | congelar |
| `/bases/api/dados` | GET | `blueprints/bases/routes.py` | `bases:view` | Dashboard operacional, scripts e2e | congelar |
| `/bases/pilotos/<id>/foto` | GET | `blueprints/bases/routes.py` | `bases:view` | SSR bases | congelar |
| `/bases/pilotos/adicionar` | POST | `blueprints/bases/routes.py` | `bases:view` | SSR bases | congelar |
| `/bases/pilotos/<id>/status` | POST | `blueprints/bases/routes.py` | `bases:view` | SSR bases | congelar |
| `/bases/pilotos/<id>/mover` | POST | `blueprints/bases/routes.py` | `bases:view` | SSR bases | congelar |
| `/bases/pilotos/<id>/historico` | GET | `blueprints/bases/routes.py` | `bases:view` | SSR bases | congelar |
| `/pernoites` | GET | `blueprints/operacoes/routes.py` | `pernoites:view` | Backend link, docs arquitetura | congelar |
| `/pernoites/novo` | GET/POST | `blueprints/operacoes/routes.py` | `pernoites:create` | `BACKEND_LINKS.pernoitesNew`, docs | congelar |
| `/pernoites/<id>/editar` | GET/POST | `blueprints/operacoes/routes.py` | `pernoites:edit` | SSR pernoites | congelar |
| `/pernoites/<id>/excluir` | POST | `blueprints/operacoes/routes.py` | `pernoites:delete` | SSR pernoites | congelar |
| `/equipamentos` | GET | `routes_catalogos.py` | `equipamentos:view` | `navigation.js` | congelar |
| `/equipamentos/novo` | GET/POST | `routes_catalogos.py` | `equipamentos:create` | SSR equipamentos | congelar |
| `/equipamentos/<id>/editar` | GET/POST | `routes_catalogos.py` | `equipamentos:edit` | SSR equipamentos | congelar |
| `/equipamentos/<id>/excluir` | POST | `routes_catalogos.py` | `equipamentos:delete` | SSR equipamentos | congelar |
| `/tipos-treinamento*` | GET/POST | `routes_catalogos.py` | `tipos_treinamento:*` | Compat redirect/fallback SSR | congelar |
| `/tripulantes*` SSR | GET/POST | `routes.py`, `routes_tripulante_views.py`, `routes_file.py` | `tripulantes:*`, `tripulantes_file:*`, relatorio | Fallback/documentos/relatorios | congelar |
| `/treinamentos*` SSR | GET/POST | `routes_treinamentos.py` | `treinamentos:*`, `treinamentos_anexos:*` | Fallback/export/anexos | congelar |

### APIs usadas pelas telas SPA

| Path/padrao | Metodo | Produtor | Consumidor | Decisao |
|---|---|---|---|---|
| `/api/v1/dashboard/*` | GET | `api/http/dashboard/routes.py` | `features/dashboard`, `features/dashboard-operacional` | congelar |
| `/api/aisweb/met` e `/api/v1/aisweb/met` | GET | `api/http/dashboard/routes.py` | Dashboard operacional/AISWEB compat | congelar |
| `/api/v1/tripulantes*` | GET/POST/PUT/DELETE | `api/http/cadastros/routes.py` | `features/tripulantes`, financeiro | congelar |
| `/api/v1/treinamentos*` | GET/POST/PUT/DELETE | `api/http/cadastros/routes.py` | Compat residual/generic treinamentos | congelar |
| `/api/v1/treinamentos-tripulantes*` | GET/POST/PUT/DELETE | `api/http/cadastros/routes_training_program.py` | `features/treinamentos` | congelar |
| `/api/v1/treinamento-raiz*` | GET/POST/PUT/DELETE | `api/http/cadastros/routes_training_program.py` | `features/training-root` | congelar |
| `/api/v1/equipamentos/options` | GET | `api/http/cadastros/routes.py` | Financeiro missoes, treinamentos | congelar |
| `/api/v1/relatorios/habilitacoes` | GET | `api/http/relatorios/routes.py` | `features/relatorios/habilitacoes-page.js` | congelar |
| `/api/v1/operacoes/pernoites*` | GET | `api/http/operacoes/routes.py` | Read model pernoites atual/futuro | congelar |
| `/api/v1/financeiro/*` | GET/POST/PATCH/DELETE | `api/http/financeiro/routes.py`, `contracts/financeiro_http.py` | `services/financeiro-*.js` | congelar |

## 7. Redirects

| Origem | Destino atual | Condicao | Arquivos | Risco se mudar | Decisao |
|---|---|---|---|---|---|
| `/` | frontend app `/` | `frontend_official_enabled()` | `dashboard/routes.py`, `core/frontend_routes.py` | Entrada raiz cai em superficie errada | congelar |
| `/` | `/dashboard` | autenticado sem frontend oficial | `dashboard/routes.py` | SSR fallback quebra | congelar |
| `/` | `/login` | anonimo sem frontend oficial | `dashboard/routes.py` | Login SSR quebra | congelar |
| `/dashboard` | `/#/dashboard` | `frontend_compat_enabled()` | `dashboard/routes.py` | Landing e smoke quebram | congelar |
| `/treinamentos` | `/#/treinamentos` preservando filtros | `frontend_compat_enabled()` | `routes_treinamentos.py` | Filtros de lista se perdem | congelar |
| `/treinamentos/novo` | `/#/treinamentos/new` | GET + compat ativo | `routes_treinamentos.py` | Criacao SPA quebra | congelar |
| `/treinamentos/<id>/editar` | `/#/treinamentos/<id>` | GET + compat ativo | `routes_treinamentos.py` | Edicao SPA quebra | congelar |
| `/treinamentos/consolidado` | `/#/relatorios/habilitacoes` preservando filtros | compat ativo | `routes_treinamentos.py` | Relatorio/export perde recorte | congelar |
| `/tipos-treinamento*` | `/#/treinamentos/raiz` | GET + compat ativo | `routes_catalogos.py`, docs migration 92/96 | Cadastro raiz pode cair no SSR legado | congelar |
| usuario nao autenticado | `/login?next=...` ou `#/login` | auth/RBAC | `auth.py`, `bootstrap.js`, `login.js` | Perda de deep link e retorno | congelar |
| logout SPA | `/#/login` | logout ok | `render-shell.js` | Sessao visual fica inconsistente | congelar |
| auth em `#/login` | return route, last successful ou `#/dashboard` | usuario ja autenticado | `bootstrap.js`, `navigation-state.js` | Usuario volta para tela errada | congelar |

## 8. Paths PDF/CSV/export

| Path | Tipo | Produtor | Consumidor | Permissao | Campos/headers criticos | Decisao |
|---|---|---|---|---|---|---|
| `/treinamentos/consolidado/export.pdf` | PDF | `routes_treinamentos.py` | `habilitacoes-page.js`, browser | `relatorio_habilitacoes:view` | `HABILITACOES_EXPORT_PDF_POLICY`, `%PDF`, `%%EOF`, `X-Document-*`, `Content-Disposition` | congelar |
| `/treinamentos/consolidado/export.csv` | CSV | `routes_treinamentos.py` | `habilitacoes-page.js`, Excel/operacao | `relatorio_habilitacoes:view` | `text/csv`, BOM UTF-8, delimiter `;`, colunas atuais | congelar |
| `/treinamentos/consolidado/relatorio` | print/HTML | `routes_treinamentos.py` | `habilitacoes-page.js`, browser print | `relatorio_habilitacoes:view` | filtros `nome,base,status,tipo,ordenacao`, `auto_print=1` | congelar |
| `/tripulantes/<id>/relatorio/export.pdf` | PDF | `routes_tripulante_views.py` | SSR relatorio individual | `relatorio_individual:view` | `TRIPULANTE_TREINAMENTOS_EXPORT_PDF_POLICY` | congelar |
| `/auditoria/export.pdf` | PDF | `blueprints/admin/routes.py` | Auditoria/suporte | `auditoria:view` | `AUDITORIA_EXPORT_PDF_POLICY`, filtros `entidade,acao,autor,busca` | congelar |
| `/manual/usuario.pdf` | PDF | `routes_operacional.py` | Menu e suporte | `monitoramento:view` | `USER_GUIDE_PDF_POLICY` | congelar |
| `/api/v1/financeiro/lancamentos-jornada.pdf` | PDF financeiro | `api/http/financeiro/routes.py` | `financeiro-lancamentos-jornada-api.js` | `finance:exports:create` | `competencia`, `funcao`, `tripulante_id`, `status`, PDF valido | congelar |
| `/api/v1/financeiro/horas-totais-voadas.pdf` | PDF financeiro | `api/http/financeiro/routes.py` | `financeiro-lancamentos-jornada-api.js` | `finance:exports:create` | `competencia YYYY-MM`, `funcao` | congelar |
| `/api/v1/financeiro/produtividade/relatorio-geral.pdf` | PDF financeiro | `api/http/financeiro/routes.py` | `financeiro-lancamentos-jornada-api.js` | `finance:exports:create` | `competencia`, `funcao`, `org_id`, `categoria` | congelar |
| `/api/v1/financeiro/extrato-periodo.pdf` | PDF financeiro | `api/http/financeiro/routes.py` | `financeiro-lancamentos-jornada-api.js` | `finance:exports:create` | `data_inicio`, `data_fim`, `tripulante_id`, `funcao`, `tipo` | congelar |
| `/api/v1/financeiro/relatorios/individual.pdf` | PDF financeiro | `api/http/financeiro/routes.py` | `financeiro-bonificacoes-api.js`, jornada API | `finance:exports:create` | `tipo`, `competencia`, `tripulante_id`, `funcao`, `status`, `formato=pdf` | congelar |
| `/api/v1/financeiro/competencias/<competencia>/relatorio.pdf` | PDF financeiro | `api/http/financeiro/routes.py` | `financeiro-parametros-api.js` | `finance:exports:create` | competencia `YYYY-MM`, snapshot fechado | congelar |
| `/api/v1/tripulantes/<id>/files/<file_id>?download=1` | download PDF | `api/http/cadastros/routes.py` | SPA tripulantes, scripts e2e | `tripulantes_file:view` | `download=1`, file policy, auditoria | congelar |
| `/api/v1/treinamentos/<id>/attachments/<attachment_id>?download=1` | download PDF | `api/http/cadastros/routes.py` | SPA treinamentos, scripts e2e | `treinamentos_anexos:view` | `download=1`, file policy, auditoria | congelar |
| `/tripulantes/<id>/file/origem/<origem>/<arquivo_id>?download=1` | download SSR | `routes_file.py` | File tab, scripts e2e | `tripulantes_file:view` | `origem`, `download=1`, policy | congelar |
| `/treinamentos/<id>/anexos/<anexo_id>?download=1` | download SSR | `routes_treinamentos.py` | SSR treinamento | `treinamentos_anexos:view` | `download=1`, policy | congelar |

Regra de evolucao: PDF/CSV/export tem mudanca permitida "nenhuma" para path,
headers, content type, permissao, filtro e formato de arquivo durante
reorganizacao. Mudanca de conteudo exige teste binario/visual e validacao
humana.

## 9. Rotas operacionais/deep links

| Path/deep link | Origem | Consumidores | Risco | Decisao |
|---|---|---|---|---|
| `/#/dashboard-operacional-tv` | `route-registry.js` | TV/dashboard operacional | Tela TV some sem aparecer no menu | congelar |
| `/#/treinamentos/<id>` | `dynamicRouteDefinitions`, `dashboard/routes.py`, templates | Calendario, dashboard, bookmarks | Detalhe de treinamento fica inacessivel | congelar |
| `/#/tripulantes/<id>` | `dynamicRouteDefinitions`, templates | Dashboard, relatorio individual, bookmarks | Detalhe de tripulante fica inacessivel | congelar |
| `/#/treinamentos?status=vencido` | `templates/dashboard.html`, dashboards SPA | Atalhos por status | Filtros operacionais quebram | congelar semantica |
| `/#/treinamentos?periodo=7` e `periodo=30` | `templates/dashboard.html`, dashboards SPA | Atalhos de vencimento | Filtros operacionais quebram | congelar semantica |
| `/#/dashboard-operacional?painel=meteorologia` | dashboard operacional | Cards/painel meteorologia | Deep link de painel quebra | congelar semantica |
| `/#/dashboard-operacional?painel=notams` | dashboard operacional | Cards/painel NOTAM | Deep link de painel quebra | congelar semantica |
| `/pernoites*` | `backend-links.js`, `operacoes/routes.py`, docs arquitetura | Operacao SSR atual | Cutover pernoites fica inconsistente | congelar |
| `/bases*` | `backend-links.js`, `bases/routes.py`, dashboard operacional | Gestao de bases e mapa | Operacao de bases quebra | congelar |
| `/monitoramento`, `/backups`, `/auditoria` | `navigation.js`, admin routes | Operacao, suporte, auditoria | Perda de suporte operacional | congelar |
| `/jobs/<id>/reativar`, `/jobs/<id>/status` | `routes_operacional.py` | Dead-letter/monitoramento | Requeue/status job quebra | congelar |
| `/?task=backup`, `/backup` | `compat/http_entrypoints/cron.py` | Cron fallback | Backup agendado nao enfileira | congelar |
| `/?task=notificacoes`, `/notificacoes`, `/notifications` | `compat/http_entrypoints/cron.py` | Cron fallback | Notificacoes nao enfileiram | congelar |

## 10. Rotas orfas ou sem menu

Orfa aqui significa "sem item direto no menu atual" ou "sem produtor Flask direto
apesar de existir adapter/documentacao". Nao significa rota removivel.

| Path | Motivo | Arquivos | Risco | Decisao |
|---|---|---|---|---|
| `#/dashboard-operacional-tv` | Sem item em `NAV_GROUPS` | `route-registry.js`, `pages-dashboard-tripulantes.js` | TV/deep link quebra | congelar |
| `#/tripulantes/new` | Sem menu direto | `route-registry.js` | Criacao quebra | congelar |
| `#/tripulantes/<id>` | Dinamica sem menu direto | `route-registry.js`, templates | Bookmarks e edicao quebram | congelar |
| `#/treinamentos/new` | Sem menu direto | `route-registry.js` | Criacao quebra | congelar |
| `#/treinamentos/<id>` | Dinamica sem menu direto | `route-registry.js`, dashboard routes | Calendario e edicao quebram | congelar |
| `#/financeiro/missoes` | Registrada, mas sem item direto em `navigation.js` atual | `route-registry.js`, `pages-financeiro.js` | Missoes financeiras ficam inacessiveis por bookmark | congelar |
| `#/financeiro/bonificacoes*` | Aliases financeiros sem menu direto | `route-registry.js`, `navigation.js` active match | Bookmarks antigos quebram | congelar |
| `/pernoites`, `/pernoites/novo` | Backend links, fora da navegacao principal atual | `backend-links.js`, `operacoes/routes.py`, docs arquitetura | Operacao SSR atual quebra | congelar |
| `/usuarios/novo` | Backend link sem item visivel direto no menu | `backend-links.js`, `admin/routes.py` | Criacao admin quebra | congelar |
| `/tipos` | Alias sem route decorator Flask | `backend-links.js`, docs migration 93 | Resolver de login/reentrada perde alias historico | congelar adapter; validar uso |
| `/tipos-treinamento*` fallback | SSR fallback/redirect, nao tela casual | `routes_catalogos.py`, templates `tipos_*` | Render SSR legado ou quebra compat | congelar |
| `/healthz`, `/api/internal/metrics`, `/api/internal/errors/<id>` | Operacionais sem menu | `__init__.py`, scripts smoke | Observabilidade/release quebra | congelar |

Rotas historicas citadas em docs como `/missoes`, `/produtividade`,
`#/relatorios/produtividade/*`, `/painel-tv` e `/api/v1/tv/*` nao tiveram
produtor vivo confirmado nas rotas atuais lidas. Elas ficam como "validar" ou
"revisar depois" em inventario historico, sem permissao de remocao adicional por
este gate.

## 11. Compat backend/fallbacks

| Area | Arquivos | Contrato congelado | Decisao |
|---|---|---|---|
| Backend links | `frontend/src/compat/backend-links.js` | `BACKEND_LINKS`, `BACKEND_LINK_BOUNDARIES`, `FRONTEND_HASH_BY_BACKEND_PATH`, `LEGACY_BACKEND_PATH_ALIASES` | congelar |
| Login destination | `backend-links.js`, `frontend/src/shell/login.js`, `frontend/src/state/navigation-state.js` | `resolveLoginDestination`, `/login` -> `#/login`, backend path conhecido -> hash canonica | congelar |
| Redirect backend->frontend | `backend/src/controle_treinamentos/core/frontend_routes.py` | `FRONTEND_PUBLIC_ORIGIN`, `FRONTEND_LOCAL_ORIGIN`, `FRONTEND_COMPAT_REDIRECTS`, hash deve iniciar com `#/` | congelar |
| Sidebar SSR | `backend/src/controle_treinamentos/templates/base.html` | Links `/#/...` com `hx-boost="false"` | congelar |
| Dashboard SSR | `backend/src/controle_treinamentos/templates/dashboard.html`, `blueprints/dashboard/routes.py` | Cards e calendario para `/#/tripulantes`, `/#/treinamentos`, `/#/treinamentos/<id>`, `/#/tripulantes/<id>` | congelar |
| Relatorio individual SSR | `templates/relatorio_tripulante.html` | Retornos para `/#/relatorios/individual`, `/#/tripulantes/<id>` e PDF export | congelar |
| Cron fallback | `backend/src/controle_treinamentos/compat/http_entrypoints/cron.py` | catch-all GET/POST com `Authorization: Bearer CRON_SECRET`, tasks `backup`, `notificacoes`, `notifications`, vazio | congelar |
| Smoke deploy | `ops/scripts/smoke/post_deploy_smoke.py` | `/healthz`, `/login`, `/dashboard`, `/notificacoes-email`, `/api/internal/metrics` | congelar |
| Uso real/telemetria | `ops/scripts/diagnostics/build_usage_truth_report.py` | Prefixos `/pernoites`, `/bases`, `/usuarios`, `/auditoria`, `/monitoramento`, `/backups`, `/notificacoes-email`, `/manual`, `/missoes` historico | congelar script; validar prefixo historico `/missoes` |
| E2E homolog | `ops/scripts/release/run_e2e_homolog_live.py` | Session APIs, dashboard APIs, bases, tripulantes files/photo, treinamentos attachments, habilitacoes CSV/PDF | congelar |
| Caddy/examples | `ops/windows/caddy/Caddyfile.example` | Path de proxy para `/api/v1/tripulantes/*/files/*` | congelar |

## 12. Matriz path -> origem -> consumidor -> risco -> decisao

| Path/padrao | Origem/produtor | Consumidor | Risco se mudar | Decisao |
|---|---|---|---|---|
| `#/dashboard` | `route-registry.js` | Menu, bootstrap, SSR redirects, smoke | Landing e primeira tela quebram | congelar |
| `#/dashboard-operacional` | `route-registry.js` | Menu, dashboard operacional | Painel operacional quebra | congelar |
| `#/dashboard-operacional-tv` | `route-registry.js` | TV/deep link | Rota sem menu some | congelar |
| `#/tripulantes`, `#/tripulantes/new`, `#/tripulantes/<id>` | `route-registry.js` | Tripulantes SPA, dashboard, relatorios | CRUD e bookmarks quebram | congelar |
| `#/treinamentos`, `#/treinamentos/new`, `#/treinamentos/<id>` | `route-registry.js` | Treinamentos SPA, dashboard, relatorios | Filtros, edicao e calendario quebram | congelar |
| `#/treinamentos/raiz` | `route-registry.js`, `backend-links.js` | Cadastro raiz, aliases `/tipos*` | Tipos/segmentos/horas quebram | congelar |
| `#/relatorios/habilitacoes` | `route-registry.js`, `routes_treinamentos.py` | Relatorio SPA, exports | PDF/CSV perde recorte | congelar |
| `#/relatorios/individual` | `route-registry.js` | Relatorio individual SPA/SSR | Seletor oficial quebra | congelar |
| `#/financeiro/missoes` | `route-registry.js` | Financeiro missoes | Missao financeira inacessivel | congelar |
| `#/financeiro/lancamentos-jornada` | `route-registry.js` | Financeiro jornada | Pagamentos e grade quebram | congelar |
| `#/financeiro/fechamento-parametros` | `route-registry.js` | Parametros, feriados, competencias | Fechamento financeiro quebra | congelar |
| `#/financeiro/bonificacoes*` | `route-registry.js` | Bookmarks antigos, menu active match | Alias financeiro quebra | congelar |
| `#/login` | `navigation-state.js`, `bootstrap.js`, `login.js` | Login/logout/session | Auth quebra | congelar |
| `/`, `/dashboard`, `/login`, `/logout` | `dashboard/routes.py`, `auth/routes.py` | Browser, SSR compat, scripts | Entradas principais quebram | congelar |
| `/api/v1/session*`, `/api/v1/me`, `/api/v1/capabilities` | `auth/routes.py` | `session-service.js`, shell, e2e | Sessao/RBAC quebram | congelar |
| `/usuarios*` | `admin/routes.py` | Admin SSR | RBAC/admin quebra | congelar |
| `/auditoria`, `/auditoria/export.pdf` | `admin/routes.py` | Auditoria/suporte | Evidencia e PDF quebram | congelar |
| `/notificacoes-email*` | `admin/routes.py` | Menu, topbar, smoke | Notificacoes e smoke quebram | congelar |
| `/backups`, `/backups/executar` | `routes_operacional.py` | Operacao backups | Backup manual quebra | congelar |
| `/monitoramento`, `/jobs/<id>/status`, `/jobs/<id>/reativar` | `routes_operacional.py` | Operacao/jobs | Dead-letter e monitoramento quebram | congelar |
| `/manual/usuario.pdf` | `routes_operacional.py` | Menu/suporte | Manual operacional quebra | congelar |
| `/bases*` | `bases/routes.py` | Menu, dashboard operacional, scripts | Gestao de bases quebra | congelar |
| `/pernoites*` | `operacoes/routes.py` | Operacao SSR, docs | Cutover pernoites contaminado | congelar |
| `/equipamentos*` | `routes_catalogos.py` | Menu, financeiro options | Equipamentos e seletores quebram | congelar |
| `/tipos-treinamento*` | `routes_catalogos.py`, `backend-links.js` | Cadastro raiz compat | Reentrada raiz quebra | congelar |
| `/tripulantes*` SSR | `routes.py`, `routes_file.py`, `routes_tripulante_views.py` | Fallback, arquivos, relatorios | Fotos/files/relatorio quebram | congelar |
| `/treinamentos*` SSR | `routes_treinamentos.py` | Fallback, anexos, exports | Anexos e relatorios quebram | congelar |
| `/treinamentos/consolidado/export.pdf` | `routes_treinamentos.py` | Relatorio habilitacoes | PDF operacional quebra | congelar |
| `/treinamentos/consolidado/export.csv` | `routes_treinamentos.py` | Relatorio habilitacoes/Excel | CSV operacional quebra | congelar |
| `/api/v1/dashboard/*` | `api/http/dashboard/routes.py` | Dashboard SPA/TV | Dashboards sem dados | congelar |
| `/api/aisweb/met`, `/api/v1/aisweb/met` | `api/http/dashboard/routes.py` | Meteorologia operacional | AISWEB compat quebra | congelar |
| `/api/v1/tripulantes*` | `api/http/cadastros/routes.py` | Tripulantes SPA, financeiro | CRUD, files e seletores quebram | congelar |
| `/api/v1/treinamentos-tripulantes*` | `routes_training_program.py` | Treinamentos SPA | Programa de treinamentos quebra | congelar |
| `/api/v1/treinamento-raiz*` | `routes_training_program.py` | Cadastro raiz SPA | Tipos/segmentos/horas quebram | congelar |
| `/api/v1/relatorios/habilitacoes` | `api/http/relatorios/routes.py` | Relatorio SPA | Relatorio sem dados | congelar |
| `/api/v1/operacoes/pernoites*` | `api/http/operacoes/routes.py` | Read model pernoites | Futuro cutover perde contrato | congelar |
| `/api/v1/financeiro/missoes*` | `api/http/financeiro/routes.py`, `financeiro_http.py` | Financeiro missoes | Calculo/fechamento/auditoria quebra | congelar |
| `/api/v1/financeiro/lancamentos-jornada*` | `api/http/financeiro/routes.py`, `financeiro_http.py` | Financeiro jornada | Pagamentos e PDF quebram | congelar |
| `/api/v1/financeiro/bonificacoes*`, `/produtividade/*`, `/extrato-periodo*` API financeira | `api/http/financeiro/routes.py`, `financeiro_http.py` | Financeiro bonus/relatorios | Valores financeiros e relatorios quebram | congelar |
| `/api/v1/financeiro/competencias*`, `/parametros*`, `/feriados*`, `/auditoria`, `/divergencias` | `api/http/financeiro/routes.py`, `financeiro_http.py` | Fechamento/parametros/auditoria | Governanca financeira quebra | congelar |
| `/?task=backup`, `/backup`, `/?task=notificacoes`, `/notificacoes`, `/notifications` | `compat/http_entrypoints/cron.py` | Cron/jobs | Jobs agendados nao enfileiram | congelar |
| `/missoes` | Docs/scripts historicos, sem route decorator vivo confirmado | Diagnostico historico | Pode ser legado removido; nao usar como rota viva sem prova | validar |
| `/produtividade*`, `#/relatorios/produtividade*`, `/painel-tv*`, `/api/v1/tv*` | Docs de migracao indicam remocao | Historico/retired docs | Reintroducao pode quebrar governanca | revisar depois |
| Artefatos `frontend/dist/**` e `frontend/ops/artifacts/**` | Build/artefatos gerados | Evidencia historica | Podem refletir builds antigos | revisar depois |

## 13. Lacunas de validacao

- A baseline P0 em `docs/release-gates/baseline-p0-execution.md` esta
  `VERMELHA`; rotas SPA/SSR/aliases/deep links permanecem bloqueadas.
- O teste
  `tests/contract/test_frontend_app_architecture_boundaries.py::test_route_registry_preserves_current_routes_loaders_exports_and_permissions`
  falhou porque o route registry contem rotas financeiras extras de
  bonificacoes e lancamentos-jornada. Este documento congela o estado observado,
  mas nao declara o teste resolvido.
- Nao foi executado smoke de browser, endpoint real, PDF real, CSV real, login
  real, backup, cron, job, cleanup, restore, migration ou seed nesta frente.
- Nao ha telemetria de bookmarks externos anexada a este registro. Remocao ou
  rename de alias depende de logs reais e validacao humana.
- `/tipos` existe como alias no adapter frontend, mas nao como route decorator
  Flask vivo. Seu uso externo precisa de telemetria antes de qualquer decisao.
- Docs historicos citam `/missoes` e superficies antigas de produtividade/TV.
  Como as rotas vivas atuais nao foram confirmadas nos decorators lidos, elas
  ficam fora da lista de rotas vivas e dentro de validacao historica.
- Artefatos em `frontend/dist/**` e `frontend/ops/artifacts/**` contem snapshots
  de builds; eles nao devem virar fonte primaria sem comparacao com `frontend/src`.
- PDFs/CSVs financeiros e nao financeiros precisam de validacao binaria/visual
  antes de qualquer mudanca, inclusive em headers e nomes de arquivo.
- Rotas sem menu, especialmente `#/dashboard-operacional-tv`,
  `#/financeiro/missoes` e aliases financeiros, precisam de teste de contrato
  explicito para evitar regressao silenciosa.

## 14. Proximo passo recomendado

Manter a reorganizacao fisica bloqueada. O proximo passo seguro e criar uma
suite de contract/smoke nao destrutiva para este mapa, cobrindo:

- Resolucao de todas as hash routes canonicas, internas e dinamicas.
- Redirects `/dashboard`, `/treinamentos`, `/treinamentos/consolidado`,
  `/tipos-treinamento*` e login/logout.
- Links em `navigation.js`, `backend-links.js` e templates SSR.
- PDFs/CSVs/exports com content type, headers, filtros e permissao.
- Aliases financeiros e alias `/tipos`.
- Rotas operacionais de auditoria, backups, monitoramento, jobs e cron fallback
  em ambiente isolado.

Somente depois de baseline verde, telemetria revisada e validacao humana por
financeiro/RBAC/operacao/documentos, uma frente separada pode avaliar qualquer
evolucao de rota. Ate la, a regra e congelar.
