# Contract Freeze Register - Reorganizacao Fisica

Status: BLOQUEADO PARA REORGANIZACAO FISICA
Data do congelamento: 2026-06-06
Escopo: backend Flask, frontend JavaScript modular, SPA hash-route, SSR/backend compat, aliases, PDF/CSV, contratos HTTP, financeiro, RBAC, jobs, backups, auditoria e scripts operacionais.

Este registro e um gate de release. Antes de qualquer move, rename, limpeza, refatoracao, padronizacao ou alteracao estrutural, os contratos abaixo devem continuar bit a bit compativeis no comportamento observavel. Nenhum contrato esta liberado sem teste de contrato e validacao humana explicita.

## 1. Resumo executivo

A Frente 1.4 classificou o sistema como bloqueado para reorganizacao fisica. Este documento congela as superficies publicas, semi-publicas e operacionais encontradas no codigo atual:

- Endpoints HTTP JSON, binarios, SSR e internos.
- Metodos, paths, path params, query params e request bodies.
- Envelopes JSON, envelopes de erro, status codes, paginacao e headers.
- Sessao, CSRF, capabilities, RBAC e mapa endpoint-permissao.
- Rotas SPA, rotas SSR/backend, aliases e redirects de compatibilidade.
- PDFs, CSVs, exports, politicas de documento e auditoria de download/geracao.
- Schema, migrations corretivas, repositories e formatos financeiros.
- Jobs, scripts canonicos, wrappers compat, variaveis de ambiente e integracoes.
- Logs estruturados, auditoria, request_id, correlation_id, metricas e rastreio de erros.

Regra central: reorganizacao fisica nao pode alterar contrato. Se uma mudanca exigir padronizacao, renomeacao, remocao, ajuste de status code, mudanca de permissao, alteracao de schema, novo path, nova semantica de PDF/CSV ou alteracao de script/job, ela sai do escopo da reorganizacao e precisa de frente propria, versionamento quando aplicavel, teste de contrato e validacao humana.

## 2. Criterios de congelamento

- Nenhum arquivo de produto pode ser alterado para cumprir este gate.
- Nenhum endpoint pode ser executado para "descoberta"; a fonte deste gate e leitura estatica de arquivos reais.
- Paths, metodos, path params, query params, corpos, campos JSON, nomes de campos, envelopes, status codes e headers devem permanecer iguais.
- Erros de API devem manter `success:false`, `message`, `status`, `request_id`, `correlation_id`, `code` opcional e `details` opcional conforme `backend/src/controle_treinamentos/core/http_utils.py`.
- Paginacao deve manter `page`, `per_page`, `total`, `pages`, `has_prev`, `has_next`, `prev_url`, `next_url`.
- Datas devem manter ISO via `isoformat()` e competencias financeiras devem manter `YYYY-MM`.
- Valores monetarios/decimais financeiros devem continuar serializados como string decimal, nao float, onde os contratos financeiros fazem `format(value, "f")`.
- Status de dominio nao podem ser renomeados, traduzidos nem normalizados durante move fisico.
- Auth, session, CSRF, capabilities, RBAC e dependencia de permissoes sao contrato de seguranca.
- Rotas SPA hash, SSR/backend links, aliases e redirects de compatibilidade sao contrato de integracao frontend/backend.
- PDFs/CSVs/exports devem manter paths, parametros, content types, headers, politicas, nomes de arquivo e auditoria.
- Schema, constraints, indices, migrations corretivas e repository boundaries nao podem mudar como efeito colateral.
- Jobs, scripts, wrappers compat e variaveis de ambiente devem manter nomes, argumentos, saidas e exit codes.
- Logs/auditoria/metricas devem manter campos de correlacao e rastreabilidade.

## 3. Classes de evolucao permitida

| Classe | Definicao | Uso neste gate |
|---|---|---|
| nenhuma | Nao alterar durante reorganizacao fisica. | Aliases, redirects, permissao, status code, schema, jobs/scripts canonicos, formatos de PDF/CSV, contratos de erro. |
| somente aditiva | Apenas novos campos opcionais sem remover/renomear campos existentes e sem alterar semantica. | Algumas respostas JSON nao financeiras, somente apos teste de contrato. |
| somente com versionamento | Mudanca breaking exige novo contrato/versionamento ou novo path. | Financeiro, auth/session, schema, exports e integrações externas. |
| somente apos teste de contrato | Mudanca so pode entrar apos teste automatizado provar compatibilidade. | Todos os contratos HTTP, frontend services e rotas SPA/SSR. |
| somente apos validacao humana | Precisa aceite explicito de negocio/operacao/seguranca. | Financeiro sensivel, RBAC, sessoes, PDFs/CSVs, backups, jobs, auditoria e variaveis de ambiente. |

## 4. Fontes reais usadas

| Area | Arquivos reais citados |
|---|---|
| Registro Flask e internos | `backend/src/controle_treinamentos/__init__.py` |
| Auth/RBAC | `backend/src/controle_treinamentos/auth.py`, `backend/src/controle_treinamentos/blueprints/auth/routes.py`, `backend/src/controle_treinamentos/core/auth_contract.py` |
| HTTP utils/erros/CORS/seguranca | `backend/src/controle_treinamentos/core/http_utils.py`, `backend/src/controle_treinamentos/core/errors.py`, `backend/src/controle_treinamentos/core/security.py`, `backend/src/controle_treinamentos/core/cors.py`, `backend/src/controle_treinamentos/core/http_contract.py` |
| API backend | `backend/src/controle_treinamentos/api/http/**/routes*.py` |
| Contratos backend | `backend/src/controle_treinamentos/contracts/*.py` |
| Frontend consumers | `frontend/src/services/*.js`, `frontend/src/features/**/*.js` |
| SPA/compat | `frontend/src/app/route-registry.js`, `frontend/src/shell/navigation.js`, `frontend/src/state/navigation-state.js`, `frontend/src/compat/backend-links.js`, `backend/src/controle_treinamentos/core/frontend_routes.py` |
| SSR/backend | `backend/src/controle_treinamentos/blueprints/**/*.py` |
| Schema/migrations/repos | `backend/src/controle_treinamentos/db/schema.py`, `backend/src/controle_treinamentos/db/migrations.py`, `backend/src/controle_treinamentos/repositories/*.py`, `backend/src/controle_treinamentos/application/*.py` |
| PDF/CSV/file access | `backend/src/controle_treinamentos/core/pdf_document_policy.py`, `backend/src/controle_treinamentos/core/file_access_policy.py`, `backend/src/controle_treinamentos/contracts/relatorios.py` |
| Jobs/scripts/env | `backend/src/controle_treinamentos/infra/jobs.py`, `ops/scripts/**`, `backend/tools/maintenance/**`, `scripts/README.md`, `docs/operations/canonical-commands.md`, `.env.example`, `ops/windows/env/*.example` |
| Integracoes/logs/auditoria | `backend/src/controle_treinamentos/infra/aisweb_client.py`, `backend/src/controle_treinamentos/application/aisweb_*.py`, `backend/src/controle_treinamentos/infra/mailer.py`, `backend/src/controle_treinamentos/infra/backup.py`, `backend/src/controle_treinamentos/audit.py`, `backend/src/controle_treinamentos/core/logging.py`, `backend/src/controle_treinamentos/core/metrics.py` |
| Testes existentes | `tests/contract/*.py`, `tests/integration/*.py`, `tests/unit/*.py`, `tests/architecture/*.py` |

## 5. Contratos HTTP congelados

### CFR-HTTP-AUTH-001 - Auth, session, me e capabilities

- Tipo: HTTP JSON/auth/session.
- Produtor: `backend/src/controle_treinamentos/blueprints/auth/routes.py`, `backend/src/controle_treinamentos/core/auth_contract.py`, `backend/src/controle_treinamentos/core/security.py`.
- Consumidor: `frontend/src/services/session-service.js`, `frontend/src/shell/login.js`, `frontend/src/services/api-client.js`, SPA shell.
- Arquivos envolvidos: produtores acima, `tests/contract/test_api_session_contract.py`, `tests/contract/test_session_lifecycle_contract.py`, `tests/contract/test_auth_semantics_matrix_contract.py`.
- Formato atual: `GET /api/v1/session`, `POST /api/v1/session/login`, `POST /api/v1/session/logout`, `GET /api/v1/me`, `GET /api/v1/capabilities`.
- Campos criticos: `authenticated`, `session`, `csrf_token`, `login_url`, `logout_url`, `user{id,nome,login,email,perfil}`, `capabilities{granted_permissions,groups,landing_url}`.
- Status codes: 200 para estado/login/logout bem sucedido; 400 `csrf_error`; 401 `auth_required`, `auth_invalid_credentials`, `auth_session_expired`, `auth_session_invalid`; 403 `auth_user_inactive`; 503 `auth_backend_unavailable`.
- Formato de erro: envelope Domain/Auth com `success:false`, `status`, `code`, `message`, `request_id`, `correlation_id`, `details` opcional.
- Permissoes: endpoints de self-service publicos; `api_me` e `api_capabilities` autenticados.
- Tabelas envolvidas: `usuarios`; sessao/cookies Flask; metadados de auth em sessao.
- Risco se mudar: logout em massa, quebra de login SPA, perda de CSRF, exposicao indevida de capabilities.
- Teste necessario: contrato de sessao, lifecycle, auth semantics, CORS e frontend login.
- Documentacao necessaria: matriz de auth/session e runbook de sessao.
- Regra de evolucao permitida: somente com versionamento, teste de contrato e validacao humana de seguranca.

### CFR-HTTP-ERR-001 - Envelopes de erro, status e trace headers

- Tipo: HTTP JSON/error/status/headers.
- Produtor: `backend/src/controle_treinamentos/core/http_utils.py`, `backend/src/controle_treinamentos/core/errors.py`, `backend/src/controle_treinamentos/core/security.py`, `backend/src/controle_treinamentos/core/cors.py`.
- Consumidor: `frontend/src/services/api-client.js`, modulos de UI, scripts operacionais que consomem JSON, suporte/monitoramento.
- Arquivos envolvidos: produtores acima, `tests/contract/test_http_error_contract.py`, `tests/contract/test_http_contract_discovery.py`, `tests/contract/test_api_cors_contract.py`.
- Formato atual: erros JSON para `/api/`, `/bases/api/` e endpoints programmaticos; assets binarios retornam corpo vazio em 401/403/404/500 quando aplicavel; HTML navega/redireciona.
- Campos criticos: `success:false`, `message`, `status`, `request_id`, `correlation_id`, `code`, `details`; headers `X-Request-ID`, `X-Correlation-ID`, `X-Release-ID`, `X-Release-Instance-ID`; CORS expõe `X-Request-ID`, `X-Correlation-ID`, `ETag`.
- Status codes: 400, 401, 403, 404, 409, 422, 500, 503 conforme handlers.
- Formato de erro: nao padronizar alem do existente; nao remover `request_id`/`correlation_id`.
- Permissoes: variam por endpoint; preflight CORS permitido apenas para origem permitida e API programatica.
- Tabelas envolvidas: `request_error_events` para persistencia de erros rastreaveis.
- Risco se mudar: frontend perde tratamento de erro, suporte perde rastreio, clientes binarios recebem JSON indevido.
- Teste necessario: `test_http_error_contract.py`, `test_http_contract_discovery.py`, `test_api_cors_contract.py`.
- Documentacao necessaria: catalogo de erro/status por familia.
- Regra de evolucao permitida: nenhuma para reorganizacao fisica; somente versionada apos teste e validacao humana.

### CFR-HTTP-DASH-001 - Dashboard, operacional e AISWEB aliases

- Tipo: HTTP JSON/dashboard/external integration.
- Produtor: `backend/src/controle_treinamentos/api/http/dashboard/routes.py`, `backend/src/controle_treinamentos/contracts/dashboard.py`, `backend/src/controle_treinamentos/application/operational_dashboard.py`, `backend/src/controle_treinamentos/application/aisweb_weather.py`, `backend/src/controle_treinamentos/application/aisweb_notams.py`.
- Consumidor: `frontend/src/services/dashboard-api.js`, dashboard SPA, `frontend/src/features/dashboard/**`.
- Arquivos envolvidos: produtores acima, `tests/contract/test_api_dashboard_contract.py`, `tests/contract/test_api_aisweb_met_contract.py`, `tests/unit/test_operational_dashboard_contracts.py`.
- Formato atual: `GET /api/v1/dashboard/summary`, `/calendar`, `/critical-trainings`, `/base-operations`, `/weather-by-base`, `/notams`, `/operational-alerts`; aliases `GET /api/aisweb/met` e `GET /api/v1/aisweb/met`.
- Campos criticos: `totals`, `summary`, `alerts`, `weeks`, `upcoming`, `items`, `weather`, `icaoCode`, `locationLabel`, `condition`, `rawMetar`, `rawTaf`, `observedAt`, `updatedAt`, `source`, `status`.
- Query/path params: `critical-trainings?limit` default 8 max 20; AISWEB aceita `icaoCode` ou `icao_code`.
- Status codes: 200 sucesso; 400 `aisweb_met_icao_required`/`aisweb_met_invalid_icao`; 401/403 por auth/RBAC; 5xx por erro inesperado.
- Formato de erro: envelope comum.
- Permissoes: `dashboard:view`.
- Tabelas envolvidas: `tripulantes`, `equipamentos`, `tipos_treinamento`, `treinamentos`, `bases`, `pilotos`, `pernoites_operacionais`.
- Risco se mudar: primeira tela SPA quebra, aliases AISWEB perdem compat, telas operacionais exibem clima/alertas incorretos.
- Teste necessario: dashboard API, AISWEB MET, operational dashboard unit, frontend dashboard contracts.
- Documentacao necessaria: contrato de dashboard e upstream AISWEB.
- Regra de evolucao permitida: somente aditiva apos teste; aliases nenhuma mudanca.

### CFR-HTTP-CAD-TRIP-001 - Tripulantes API

- Tipo: HTTP JSON/cadastros.
- Produtor: `backend/src/controle_treinamentos/api/http/cadastros/routes.py`, `backend/src/controle_treinamentos/contracts/tripulantes.py`, `backend/src/controle_treinamentos/application/tripulantes.py`.
- Consumidor: `frontend/src/services/tripulantes-api.js`, paginas SPA de tripulantes, financeiro missoes para opcoes de tripulante.
- Arquivos envolvidos: produtores acima, `tests/contract/test_api_tripulantes_contract.py`.
- Formato atual: `GET /api/v1/tripulantes`, `GET /api/v1/tripulantes/options`, `GET /api/v1/tripulantes/<int:tripulante_id>`, `POST /api/v1/tripulantes`, `PUT /api/v1/tripulantes/<int:tripulante_id>`, `DELETE /api/v1/tripulantes/<int:tripulante_id>`, periodo operacional `GET/POST /api/v1/tripulantes/<id>/periodos-operacionais`, `DELETE /api/v1/tripulantes/<id>/periodos-operacionais/<periodo_id>`.
- Query/path params: `nome`, `status`, `base`, `funcao`, `categoria`, `ativo`, `page`; path `tripulante_id`, `periodo_id`.
- Request bodies: tripulante CRUD; periodo operacional com dados de periodo; nenhuma normalizacao ou rename permitido.
- Campos criticos: `id`, `nome`, `cpf`, `licenca_anac`, `email`, `telefone`, `base`, `base_operacional`, `status`, `status_operacional`, `ativo`, `funcao_operacional`, `categoria_operacional`, flags SDEA/instrutor/checador, `possui_foto`, `photo_url`, `links`, `pagination`.
- Status codes: 200 list/detail/update/delete/periodos; 201 create/periodo create; 404 `tripulante_not_found`; 400/401/403/422 conforme handler.
- Formato de erro: envelope comum.
- Permissoes: view `tripulantes:view` ou `relatorio_individual:view`; create/edit/delete especificos.
- Tabelas envolvidas: `tripulantes`, `bases`, `auditoria_eventos`, `tripulante_periodos_operacionais`.
- Risco se mudar: formularios, filtros, financeiro e relatorios perdem campos de identidade e compat residual.
- Teste necessario: API tripulantes, auth/RBAC e frontend route/service.
- Documentacao necessaria: catalogo de campos de tripulante e periodo operacional.
- Regra de evolucao permitida: somente aditiva apos teste de contrato; permissao/status/path nenhuma mudanca.

### CFR-HTTP-CAD-MEDIA-001 - Fotos, File e anexos de tripulante

- Tipo: HTTP JSON/binario/upload/download.
- Produtor: `backend/src/controle_treinamentos/api/http/cadastros/routes.py`, `backend/src/controle_treinamentos/blueprints/cadastros/routes_file.py`, `backend/src/controle_treinamentos/contracts/tripulante_media.py`, `backend/src/controle_treinamentos/core/file_access_policy.py`.
- Consumidor: SPA tripulantes, SSR File, relatorio individual, browser/download, auditoria.
- Arquivos envolvidos: produtores acima, `tests/contract/test_api_tripulante_media_contract.py`, `tests/integration/test_training_pdf_attachments.py`.
- Formato atual: `GET/POST/DELETE /api/v1/tripulantes/<id>/photo`; `GET/POST /api/v1/tripulantes/<id>/files`; `GET/DELETE /api/v1/tripulantes/<id>/files/<file_id>`; SSR `/tripulantes/<id>/foto`, `/tripulantes/<id>/file`, `/file/upload`, `/file/<arquivo_id>`, `/file/origem/<origem>/<arquivo_id>`, `/file/<arquivo_id>/excluir`, `/file/<arquivo_id>/substituir`.
- Query/path params: `download=1|true|yes|sim` muda `preview` para `download`; path `tripulante_id`, `file_id`, `origem`, `arquivo_id`.
- Request bodies: multipart `arquivo_pdf`/`arquivos_pdf`; JSON `content_base64`/`arquivo_base64`; foto em formato atual.
- Campos criticos: `has_photo`, `photo_url`, `access_policy`, `legacy_blob_policy`, `id`, `tipo_documento`, `nome_original`, `mime_type`, `tamanho_bytes`, `storage_ref`, `arquivo_hash`, `status`, `links{self,preview,download}`, `document_policy`.
- Status codes: 200, 201, 204/200 conforme rota, 401/403 binario vazio, 404 vazio para imagem ou envelope para API JSON.
- Formato de erro: envelope comum para JSON; corpo vazio para binario quando policy manda.
- Permissoes: `tripulantes:view`, `relatorio_individual:view`, `tripulantes:edit`, `tripulantes_file:view/create/delete/replace`.
- Tabelas envolvidas: `tripulantes`, `tripulante_arquivos_pdf`, `treinamento_anexos_pdf`, `auditoria_eventos`.
- Risco se mudar: documentos sensiveis ficam inacessiveis, downloads deixam de auditar, links persistidos quebram.
- Teste necessario: media contract, file access policy, PDF attachment integration, RBAC.
- Documentacao necessaria: politica de File e evidencias PDF.
- Regra de evolucao permitida: nenhuma para paths/headers/permissoes; conteudo somente versionado com validacao humana.

### CFR-HTTP-CAD-TRE-001 - Treinamentos API e anexos

- Tipo: HTTP JSON/binario/cadastros.
- Produtor: `backend/src/controle_treinamentos/api/http/cadastros/routes.py`, `backend/src/controle_treinamentos/contracts/treinamentos.py`, `backend/src/controle_treinamentos/application/treinamentos.py`.
- Consumidor: `frontend/src/services/treinamentos-api.js`, SPA treinamentos, relatorios e financeiro indireto.
- Arquivos envolvidos: produtores acima, `tests/contract/test_api_treinamentos_contract.py`.
- Formato atual: `GET/POST /api/v1/treinamentos`, `GET/PUT/DELETE /api/v1/treinamentos/<id>`, `GET/POST /api/v1/treinamentos/<id>/attachments`, `GET/DELETE /api/v1/treinamentos/<id>/attachments/<attachment_id>`.
- Query/path params: `tripulante`, `equipamento`, `tipo`, `status`, `periodo`, `page`; path `id`, `attachment_id`.
- Request bodies: treinamento CRUD; attachment multipart/base64 conforme rotas.
- Campos criticos: `id`, `origem_registro`, campos de completeness, `tripulante_id`, `equipamento_id`, `tipo_treinamento_id`, nomes snapshot, `data_realizacao`, `data_vencimento`, `status_calculado`, `summary`, `pagination`, attachment metadata e policies.
- Status codes: 200, 201, 404, 401/403, 400/422.
- Formato de erro: envelope comum; binario por file access policy.
- Permissoes: `treinamentos:view/create/edit/delete`, `treinamentos_anexos:view/create/delete`.
- Tabelas envolvidas: `treinamentos`, `tripulantes`, `equipamentos`, `tipos_treinamento`, `treinamento_anexos_pdf`, `auditoria_eventos`.
- Risco se mudar: CRUD e relatorios de habilitacoes quebram; anexos de evidencia perdem rastreabilidade.
- Teste necessario: treinamentos contract, PDF attachments, SSR attachments/exports.
- Documentacao necessaria: contrato de treinamento, anexos e completeness.
- Regra de evolucao permitida: somente aditiva apos teste; binario/permission/path nenhuma.

### CFR-HTTP-CAD-ROOT-001 - Treinamento raiz e treinamentos-tripulantes

- Tipo: HTTP JSON/master data/program records.
- Produtor: `backend/src/controle_treinamentos/api/http/cadastros/routes_training_program.py`, `backend/src/controle_treinamentos/contracts/training_program.py`, `backend/src/controle_treinamentos/application/training_program.py`.
- Consumidor: `frontend/src/services/training-program-api.js`, SPA treinamento raiz, formularios de treinamento.
- Arquivos envolvidos: produtores acima, `tests/contract/test_api_training_program_contract.py`, `tests/contract/test_training_root_release_gate.py`, `tests/contract/test_training_root_canonical_reentry.py`.
- Formato atual: `/api/v1/treinamento-raiz/options`, `/tipos`, `/tipos/<id>`, `/segmentos`, `/segmentos/<id>`, `/horas-voo`, `/horas-voo/<id>`; `/api/v1/treinamentos-tripulantes/options`, `/template`, list/detail/update/delete, `/batch`, attachments.
- Query/path params: `tipo_treinamento_id`, `base`, aeronave modelo/reference, ids de tipo/segmento/hora/treinamento/anexo.
- Request bodies: master type/segmento/hora; batch com `segmentos[*]`, evidencias opcionais `arquivo_base64`.
- Campos criticos: `tipos_treinamento`, `modelos_aeronave`, `periodicidade_meses`, `exige_aeronave`, `modelo_segmento`, carga horaria, CTAC, aircraft snapshot, `created_ids`, `template`, `attachments`.
- Status codes: 200, 201, 400 `training_program_missing_type`, 403 `training_program_evidence_upload_forbidden`, 404 `training_program_record_not_found`, 401/422.
- Formato de erro: envelope comum.
- Permissoes: `tipos_treinamento:view/create/edit/delete`, `treinamentos:view/create/edit/delete`, `treinamentos_anexos:create/view/delete`.
- Tabelas envolvidas: `tipos_treinamento`, `segmentos_teoricos`, `horas_voo_aeronave`, `treinamentos`, `treinamento_anexos_pdf`, `auditoria_eventos`.
- Risco se mudar: matriz de treinamento raiz e reentrada canonica quebram; batch pode anexar evidencias sem permissao.
- Teste necessario: API training program, release gate e canonical reentry.
- Documentacao necessaria: contrato master training e batch.
- Regra de evolucao permitida: somente aditiva apos teste; batch/permissao somente validacao humana.

### CFR-HTTP-REL-001 - Relatorios habilitacoes JSON e exports SSR

- Tipo: HTTP JSON/PDF/CSV/report.
- Produtor: `backend/src/controle_treinamentos/api/http/relatorios/routes.py`, `backend/src/controle_treinamentos/contracts/relatorios.py`, `backend/src/controle_treinamentos/blueprints/cadastros/routes_treinamentos.py`, `backend/src/controle_treinamentos/application/relatorios.py`.
- Consumidor: `frontend/src/services/relatorios-api.js`, SPA `#/relatorios/habilitacoes`, SSR report/export.
- Arquivos envolvidos: produtores acima, `tests/contract/test_api_relatorios_contract.py`, `tests/contract/test_pdf_export_contracts.py`, `tests/integration/test_reports_pdf.py`.
- Formato atual: `GET /api/v1/relatorios/habilitacoes`; SSR `/treinamentos/consolidado`, `/treinamentos/consolidado/relatorio`, `/treinamentos/consolidado/export.pdf`, `/treinamentos/consolidado/export.csv`.
- Query/path params: `nome`, `base`, `status`, `tipo`, `ordenacao`; CSV/PDF preservam filtros.
- Campos criticos: `report{summary,filters,options,items}`, CSV colunas `Tripulante`, `Base`, `Funcao/Cargo`, `Habilitacao`, `Data de vencimento`, `Dias restantes`, `Status`; delimiter `;`; BOM UTF-8.
- Status codes: 200; 401/403; erro comum.
- Formato de erro: envelope comum para JSON; HTML/redirect para SSR; PDF/CSV sem normalizacao.
- Permissoes: `relatorio_habilitacoes:view`.
- Tabelas envolvidas: `treinamentos`, `tripulantes`, `equipamentos`, `tipos_treinamento`, `auditoria_eventos`.
- Risco se mudar: CSV usado por operacao/Excel quebra; PDF perde politica; SPA relatorio perde filtros/status.
- Teste necessario: API relatorios, PDF export contracts, integration reports PDF.
- Documentacao necessaria: layout CSV/PDF e status de habilitacao.
- Regra de evolucao permitida: nenhuma para CSV/PDF; JSON somente aditivo apos teste.

### CFR-HTTP-OPS-001 - Operacoes pernoites API read e SSR write atual

- Tipo: HTTP JSON/SSR operacional.
- Produtor: `backend/src/controle_treinamentos/api/http/operacoes/routes.py`, `backend/src/controle_treinamentos/contracts/operacoes.py`, `backend/src/controle_treinamentos/blueprints/operacoes/routes.py`, `backend/src/controle_treinamentos/application/operacoes.py`.
- Consumidor: SSR pernoites, futuros consumidores SPA read-only, arquitetura de cutover.
- Arquivos envolvidos: produtores acima, `tests/contract/test_operacoes_contract.py`, `tests/architecture/test_operacoes_cutover_pernoites.py`.
- Formato atual: API read `GET /api/v1/operacoes/pernoites`, `GET /api/v1/operacoes/pernoites/<int:pernoite_id>`; SSR current write `/pernoites`, `/pernoites/novo`, `/pernoites/<id>/editar`, `/pernoites/<id>/excluir`.
- Query/path params: `tipo`, `tripulante`, `page`, `per_page`; path `pernoite_id`.
- Request bodies: escrita API futura deve permanecer nao registrada ate cutover; SSR usa form atual.
- Campos criticos: `tripulante_id`, `data_pernoite`, `tipo_pernoite`, `quantidade`, `observacoes`, `pagination`.
- Status codes: API 200/404/401/403; SSR conforme form/redirect.
- Formato de erro: envelope comum para API; SSR existente.
- Permissoes: `pernoites:view/create/edit/delete`.
- Tabelas envolvidas: `pernoites_operacionais`, `tripulantes`, `auditoria_eventos`.
- Risco se mudar: cutover pendente perde fronteira; write API pode ser exposta antes da hora.
- Teste necessario: operacoes contract e architecture cutover.
- Documentacao necessaria: registro de current SSR e future API unregistered.
- Regra de evolucao permitida: nenhuma para escrita API ate cutover; read somente aditivo apos teste.

### CFR-HTTP-BASES-001 - Bases API programatica e foto de piloto

- Tipo: HTTP JSON programatico/binario/SSR.
- Produtor: `backend/src/controle_treinamentos/blueprints/bases/routes.py`, `backend/src/controle_treinamentos/contracts/bases.py`, `backend/src/controle_treinamentos/application/base_operations.py`.
- Consumidor: tela SSR `/bases`, scripts/browser, shell backend links.
- Arquivos envolvidos: produtores acima, `tests/contract/test_bases_api_contract.py`, `backend/src/controle_treinamentos/core/http_contract.py`.
- Formato atual: `/bases`, `/bases/api/dados`, `/bases/pilotos/<pilot_id>/foto`, `/bases/pilotos/adicionar`, `/bases/pilotos/<pilot_id>/status`, `/bases/pilotos/<pilot_id>/mover`, `/bases/pilotos/<pilot_id>/historico`.
- Query/path params: `status`; path `pilot_id`.
- Request bodies: adicionar `nome`, `matricula`, `status`, `base_id`, `tripulante_id`, `observacao`; status `status_novo`, `observacao`; mover `base_nova_id`, `observacao`.
- Campos criticos: `success`, `status`, `code`, `bases`, `pilotos`, `status_options`, `status_filter`, pilot fields e foto.
- Status codes: 200, 201, 400/401/403/404/422.
- Formato de erro: programmatic JSON sempre JSON; foto binaria segue asset behavior.
- Permissoes: view/login; mutacoes `role_required("gestora")`; endpoint map tambem referencia `bases:view`.
- Tabelas envolvidas: `bases`, `pilotos`, `historico_status_piloto`, `tripulantes`, `auditoria_eventos`.
- Risco se mudar: tela SSR de bases e programmatic JSON quebram; status operacional se altera.
- Teste necessario: bases API contract e discovery de programmatic JSON.
- Documentacao necessaria: contrato de bases e status de piloto.
- Regra de evolucao permitida: somente aditiva apos teste; mutacoes/permissoes nenhuma.

### CFR-HTTP-FIN-MIS-001 - Financeiro missoes

- Tipo: HTTP JSON financeiro sensivel.
- Produtor: `backend/src/controle_treinamentos/api/http/financeiro/routes.py`, `backend/src/controle_treinamentos/contracts/financeiro_http.py`, `backend/src/controle_treinamentos/contracts/financeiro.py`, `backend/src/controle_treinamentos/application/financeiro_missoes.py`.
- Consumidor: `frontend/src/services/financeiro-missoes-api.js`, telas `#/financeiro/missoes`, engine financeiro, auditoria.
- Arquivos envolvidos: produtores acima, `tests/integration/test_financeiro_missoes_http.py`, `tests/contract/test_financeiro_missoes_preview_http.py`, `tests/contract/test_financeiro_missoes_recalculo_http.py`.
- Formato atual: `GET/POST /api/v1/financeiro/missoes`, `POST /api/v1/financeiro/missoes/preview`, `GET/PATCH/DELETE /api/v1/financeiro/missoes/<mission_id>`, `POST /api/v1/financeiro/missoes/<mission_id>/recalcular`, `GET /api/v1/financeiro/missoes/<mission_id>/preflight-calculo`, `POST /api/v1/financeiro/missoes/<mission_id>/cancelar`.
- Query/path params: filtros de lista, `competencia`, `page`, `page_size`; path `mission_id`.
- Request bodies: create minimo `competencia`, `data_missao`, `cavok_numero_voo`, `aeronave_id`, `comandante_tripulante_id`, `horario_apresentacao`, `horario_abandono`; patch fields congelados em `_MISSION_PATCH_FIELDS`.
- Campos criticos: envelope financeiro `success,status,code,message,request_id,correlation_id`; `items`, `pagination`, `filters`, `item`, mission fields, participants, links; `competencia YYYY-MM`; dinheiro como string quando presente.
- Status codes: conforme `FINANCE_HTTP_CONTRACTS`: 200/201 sucesso; 400, 401, 403, 404, 409, 422 erros esperados.
- Formato de erro: envelope comum e detalhes financeiros como `finance_invalid_competence`.
- Permissoes: `finance:missions:read/create/update/delete/cancel/recalculate`.
- Tabelas envolvidas: `financeiro_missoes_operacionais`, `financeiro_missao_tripulantes`, `financeiro_competencias`, `financeiro_calculos_horarios`, `financeiro_calculos_produtividade`, `financeiro_divergencias`, `auditoria_eventos`.
- Risco se mudar: calculos financeiros, fechamento de competencia e auditoria podem ficar incorretos.
- Teste necessario: finance missions HTTP, preview, recalculo, repository/application.
- Documentacao necessaria: OpenAPI/contrato financeiro versionado antes de mudar.
- Regra de evolucao permitida: somente com versionamento, teste de contrato e validacao humana financeira.

### CFR-HTTP-FIN-JOR-001 - Lancamentos de jornada e PDF de jornada

- Tipo: HTTP JSON/PDF financeiro sensivel.
- Produtor: `backend/src/controle_treinamentos/api/http/financeiro/routes.py`, `backend/src/controle_treinamentos/contracts/financeiro_http.py`, `backend/src/controle_treinamentos/application/financeiro_lancamentos_jornada.py`, `backend/src/controle_treinamentos/application/financeiro_jornada_query.py`.
- Consumidor: `frontend/src/services/financeiro-lancamentos-jornada-api.js`, rota SPA `#/financeiro/lancamentos-jornada`, aliases de bonificacoes.
- Arquivos envolvidos: produtores acima, `tests/unit/test_financeiro_lancamentos_jornada_application.py`, `tests/architecture/test_financeiro_lancamentos_jornada_backend.py`, `tests/architecture/test_financeiro_lancamentos_jornada_frontend.py`.
- Formato atual: `GET/POST /api/v1/financeiro/lancamentos-jornada`, `POST /api/v1/financeiro/lancamentos-jornada/preview`, `POST /api/v1/financeiro/lancamentos-jornada/recalcular-grade`, `GET /api/v1/financeiro/lancamentos-jornada.pdf`, `PATCH/DELETE /api/v1/financeiro/lancamentos-jornada/<linha_id>`, `POST /api/v1/financeiro/lancamentos-jornada/<linha_id>/recalcular`.
- Query/path params: `competencia`, filtros, `linha_id`; PDF exige query atual.
- Request bodies: lancamento jornada e preview atuais; patch restrito pelo contrato.
- Campos criticos: linhas de jornada, minutos, totais, status de calculo, `calculation_version`, competencia e PDF headers.
- Status codes: 200/201 sucesso; 400/401/403/404/409/422 erros esperados.
- Formato de erro: envelope comum; PDF erro nao pode ser normalizado sem teste do consumidor.
- Permissoes: `finance:bonuses:read`, `finance:bonuses:recalculate`, `finance:exports:create`.
- Tabelas envolvidas: `financeiro_calculos_horarios`, `financeiro_missoes_operacionais`, `financeiro_missao_tripulantes`, `financeiro_parametros`, `financeiro_competencias`, `auditoria_eventos`.
- Risco se mudar: demonstrativos de jornada, PDF e calculos de bonus horario quebram.
- Teste necessario: jornada backend/frontend, PDF response, finance contract.
- Documentacao necessaria: contrato de jornada e PDF.
- Regra de evolucao permitida: somente com versionamento, teste e validacao humana.

### CFR-HTTP-FIN-BON-001 - Bonificacoes, produtividade, extratos e relatorios financeiros

- Tipo: HTTP JSON/PDF financeiro sensivel.
- Produtor: `backend/src/controle_treinamentos/api/http/financeiro/routes.py`, `backend/src/controle_treinamentos/contracts/financeiro_http.py`, `backend/src/controle_treinamentos/application/financeiro_bonificacoes.py`, `backend/src/controle_treinamentos/application/financeiro_relatorios.py`, `backend/src/controle_treinamentos/application/financeiro_produtividade_relatorio_geral.py`.
- Consumidor: `frontend/src/services/financeiro-bonificacoes-api.js`, `frontend/src/services/financeiro-lancamentos-jornada-api.js`, paginas financeiras e usuarios que baixam PDF.
- Arquivos envolvidos: produtores acima, `tests/contract/test_financeiro_bonificacoes_horaria_http.py`, `tests/contract/test_financeiro_bonificacoes_produtividade_http.py`, `tests/contract/test_financeiro_relatorios_individual_http.py`, unitarios de relatorios/produtividade.
- Formato atual: `GET /api/v1/financeiro/bonificacoes/horaria`, `GET /api/v1/financeiro/bonificacoes/horaria/<calculation_id>`, `GET /api/v1/financeiro/bonificacoes/produtividade`, `GET /api/v1/financeiro/produtividade/consolidado`, `GET /api/v1/financeiro/produtividade/relatorio-geral`, `GET /api/v1/financeiro/produtividade/relatorio-geral.pdf`, `GET /api/v1/financeiro/extrato-periodo`, `GET /api/v1/financeiro/extrato-periodo.pdf`, `GET /api/v1/financeiro/bonificacoes/produtividade/<tripulante_id>`, `GET /api/v1/financeiro/relatorios/individual.pdf`.
- Query/path params: `competencia` obrigatoria onde aplicavel; `tipo in {horaria,produtividade}`; `formato=pdf`; `tripulante_id` positivo; `funcao in {comandante,copiloto}`; `status in {calculado,recalculo_pendente,obsoleto}`.
- Request bodies: endpoints read/export sem body.
- Campos criticos: calculos horarios/produtividade, totais monetarios string decimal, `memoria_calculo`, `parametros_usados`, `calculation_version`, PDF headers e footer com request/correlation.
- Status codes: 200 sucesso; 400/401/403/404/422/503 conforme contrato financeiro.
- Formato de erro: envelope comum; PDFs com validação `%PDF` e `%%EOF`.
- Permissoes: `finance:bonuses:read`, `finance:exports:create`.
- Tabelas envolvidas: `financeiro_calculos_horarios`, `financeiro_calculos_produtividade`, `financeiro_missoes_operacionais`, `financeiro_missao_tripulantes`, `financeiro_parametros`, `financeiro_competencias`, `auditoria_eventos`.
- Risco se mudar: pagamento/relatorio financeiro incorreto, arquivo PDF invalido, auditoria incompleta.
- Teste necessario: contract HTTP de bonus/produtividade/individual PDF e unitarios de relatorio.
- Documentacao necessaria: catalogo financeiro de relatorios e memoria de calculo.
- Regra de evolucao permitida: somente com versionamento, teste e validacao humana financeira.

### CFR-HTTP-FIN-GOV-001 - Competencias, parametros, feriados, auditoria e divergencias

- Tipo: HTTP JSON financeiro governanca/observabilidade.
- Produtor: `backend/src/controle_treinamentos/api/http/financeiro/routes.py`, `backend/src/controle_treinamentos/contracts/financeiro_http.py`, `backend/src/controle_treinamentos/application/financeiro_competencias.py`, `financeiro_parametros.py`, `financeiro_feriados.py`, `financeiro_observabilidade.py`, `financeiro_preflight.py`.
- Consumidor: `frontend/src/services/financeiro-parametros-api.js`, tela `#/financeiro/fechamento-parametros`, fechamento financeiro.
- Arquivos envolvidos: produtores acima, `tests/contract/test_financeiro_competencias_http.py`, `test_financeiro_parametros_http.py`, `test_financeiro_feriados_http.py`, `test_financeiro_observabilidade_http.py`, `test_financeiro_preflight_http.py`.
- Formato atual: `GET /api/v1/financeiro/competencias/<competencia>`, `/preflight-calculo`, `/relatorio.pdf`, `POST /recalcular`, `POST /fechar`, `POST /reabrir`; `GET/POST /parametros`, `PATCH /parametros/<parameter_id>`; `GET/POST /feriados`, `PATCH /feriados/<holiday_id>`; `GET /auditoria`; `GET /divergencias`.
- Query/path params: `competencia YYYY-MM`, `parameter_id`, `holiday_id`, filtros de auditoria/divergencia.
- Request bodies: parametro patch fields congelados em `_PARAMETER_PATCH_FIELDS`; feriado patch em `_HOLIDAY_PATCH_FIELDS`.
- Campos criticos: status competencia `aberta`, `em_conferencia`, `fechada`, `reaberta`; parametros com `valor`, `unidade`, `vigencia`; feriados; divergencias `bloqueante|alta|media|informativa`; auditoria.
- Status codes: 200/201 sucesso; 400/401/403/404/409/422.
- Formato de erro: envelope comum; `finance_invalid_competence` com `details{field,value,expected_format}`.
- Permissoes: `finance:periods:read/recalculate/close/reopen`, `finance:parameters:read/create/update`, `finance:audit:read`, `finance:divergences:read`, `finance:exports:create`.
- Tabelas envolvidas: `financeiro_competencias`, `financeiro_parametros`, `financeiro_feriados`, `financeiro_divergencias`, `auditoria_eventos`.
- Risco se mudar: fechamento/reabertura sem controle, parametros monetarios incorretos, perda de auditabilidade.
- Teste necessario: contracts HTTP de competencias/parametros/feriados/observabilidade/preflight.
- Documentacao necessaria: governanca financeira e calendario/parametros.
- Regra de evolucao permitida: nenhuma para permissao/status; demais somente versionado com teste e validacao humana.

### CFR-HTTP-INTERNAL-001 - Health, metricas e trace interno

- Tipo: HTTP interno/operacional.
- Produtor: `backend/src/controle_treinamentos/__init__.py`, `backend/src/controle_treinamentos/core/metrics.py`, `backend/src/controle_treinamentos/core/errors.py`.
- Consumidor: monitoramento, runbooks, suporte e smoke operacional.
- Arquivos envolvidos: produtores acima, `tests/contract/test_http_error_contract.py`.
- Formato atual: `GET /healthz`; `GET /api/internal/metrics` com header `X-Metrics-Token`; `GET /api/internal/errors/<request_id>` com token ou permissao `monitoramento:view`.
- Campos criticos: health `status`, `checks.database`; metrics Prometheus; error trace `success`, `status`, `code=error_event_found`, `event`, `recent`.
- Status codes: health 200/503; metrics 200/403 `metrics_forbidden`/503 `metrics_unconfigured`; errors 200/401/403/404.
- Formato de erro: envelope comum.
- Permissoes: token metrics ou `monitoramento:view` para trace; health publico.
- Tabelas envolvidas: `request_error_events`, `background_jobs`, metricas de runtime; DB probe.
- Risco se mudar: observabilidade e suporte perdem contrato; healthcheck pode derrubar deploy.
- Teste necessario: HTTP error/internal metrics contract e smoke.
- Documentacao necessaria: runbook de metricas e trace.
- Regra de evolucao permitida: nenhuma sem validacao de operacao.

## 6. Contratos de request congelados

| ID | Requests congelados | Formato atual | Evolucao |
|---|---|---|---|
| CFR-REQ-PAG-001 | Listagens com `page`/`per_page`/`page_size` | `page` default 1; cadastros `per_page` 20; financeiro `page_size` default 100 max 100 | nenhuma mudanca de nome/default sem teste |
| CFR-REQ-TRIP-001 | Tripulantes | query `nome,status,base,funcao,categoria,ativo,page`; path int ids; bodies CRUD e periodo operacional atuais | somente aditiva apos teste |
| CFR-REQ-MEDIA-001 | Fotos/files/anexos | multipart `arquivo_pdf`/`arquivos_pdf`, JSON `content_base64`/`arquivo_base64`, `download=1|true|yes|sim` | nenhuma para nomes e semantica |
| CFR-REQ-TRE-001 | Treinamentos | query `tripulante,equipamento,tipo,status,periodo,page`; bodies CRUD e attachment atuais | somente aditiva apos teste |
| CFR-REQ-ROOT-001 | Treinamento raiz/programa | `tipo_treinamento_id`, `base`, refs de aeronave, batch `segmentos[*]` e evidencias | somente apos teste e validacao |
| CFR-REQ-REL-001 | Relatorios | filtros `nome,base,status,tipo,ordenacao` preservados para JSON/PDF/CSV | nenhuma para export |
| CFR-REQ-OPS-001 | Pernoites | API read `tipo,tripulante,page,per_page`; write API futura nao registrada | nenhuma ate cutover |
| CFR-REQ-BASES-001 | Bases | `status`; add/status/move bodies definidos em `contracts/bases.py` | nenhuma para mutacoes |
| CFR-REQ-FIN-COMP-001 | Financeiro competencia | `YYYY-MM` regex `^\d{4}-(0[1-9]|1[0-2])$` | nenhuma |
| CFR-REQ-FIN-MIS-001 | Missoes | create minimo e patch fields `_MISSION_PATCH_FIELDS` | somente versionado |
| CFR-REQ-FIN-GOV-001 | Parametros/feriados | patch fields `_PARAMETER_PATCH_FIELDS` e `_HOLIDAY_PATCH_FIELDS`; Decimal/money como string/decimal aceito pelo dominio | somente versionado |
| CFR-REQ-PDF-001 | PDFs financeiros | `tipo`, `formato=pdf`, `tripulante_id`, `funcao`, `status`, `competencia` atuais | nenhuma sem teste PDF |

## 7. Contratos de response congelados

| ID | Response congelada | Campos criticos | Produtor/consumidor |
|---|---|---|---|
| CFR-RESP-ENV-001 | Envelope JSON generico | `success,status,code,message,request_id,correlation_id` quando produzido; payload especifico por dominio | backend routes -> `api-client.js` |
| CFR-RESP-PAG-001 | Paginacao | `page,per_page,total,pages,has_prev,has_next,prev_url,next_url` | `core/http_utils.py` -> listas SPA |
| CFR-RESP-AUTH-001 | Sessao/capabilities | `authenticated,session,csrf_token,user,capabilities` | auth routes -> session-service/shell |
| CFR-RESP-TRIP-001 | Tripulantes | campos de `contracts/tripulantes.py`, links e compat snapshots | tripulantes API -> SPA/financeiro/relatorios |
| CFR-RESP-MEDIA-001 | Media/file | file/photo state, `links`, `access_policy`, `document_policy` | media routes -> UI/download |
| CFR-RESP-TRE-001 | Treinamentos | summary/detail/collection, `status_calculado`, completeness, attachments | treinamentos API -> SPA/relatorios |
| CFR-RESP-ROOT-001 | Training program | options, tipos, segmentos, horas, records, template, batch | training program API -> SPA |
| CFR-RESP-DASH-001 | Dashboard/AISWEB | summary/calendar/critical/weather/notams/status/source | dashboard routes -> dashboard SPA |
| CFR-RESP-REL-001 | Habilitacoes | `report{summary,filters,options,items}` | relatorios API -> SPA/export |
| CFR-RESP-BASES-001 | Bases | `bases,pilotos,status_options,status_filter` e pilot fields | bases routes -> SSR |
| CFR-RESP-OPS-001 | Pernoites | `pernoites`/`pernoite`, pagination | operacoes API -> current/future UI |
| CFR-RESP-FIN-001 | Financeiro | serializers em `contracts/financeiro.py`; dinheiro decimal string; datas ISO; competencias `YYYY-MM`; enums congelados | finance routes -> frontend finance |
| CFR-RESP-PDF-001 | PDF response | bytes `%PDF` com `%%EOF`, headers `X-Document-*`, `Content-Disposition`, `Cache-Control` | PDF routes -> browser/download |
| CFR-RESP-CSV-001 | CSV response | `text/csv; charset=utf-8`, BOM, delimiter `;`, colunas congeladas | export CSV -> usuarios/Excel |

## 8. Contratos de erro/status congelados

| ID | Contrato | Status/codes congelados | Regra |
|---|---|---|---|
| CFR-ERR-AUTH-001 | Auth errors | `auth_required` 401, `auth_session_expired` 401, `auth_session_invalid` 401, `auth_user_inactive` 403, `auth_backend_unavailable` 503, `csrf_error` 400 | nenhuma |
| CFR-ERR-COMMON-001 | Common handlers | `bad_request` 400, `forbidden` 403, `not_found` 404, `conflict` 409, `unprocessable_entity` 422, `internal_error` 500, `service_unavailable` 503 | nenhuma |
| CFR-ERR-FIN-001 | Financeiro | `finance_invalid_competence` e codigos de `FINANCE_HTTP_CONTRACTS`; periodo fechado usa 409 onde definido | somente versionado |
| CFR-ERR-MEDIA-001 | Binarios/assets | auth/forbidden/notfound retornam corpo vazio quando `expects_binary_asset_response()` | nenhuma |
| CFR-ERR-JOBS-001 | Jobs admin | JSON programatico de status/requeue nao deve ser normalizado | nenhuma |
| CFR-ERR-TRACE-001 | Error trace | persistencia em `request_error_events`, listagem recente e headers de trace | nenhuma |

## 9. Contratos de auth/session/capabilities congelados

- Cookies: nomes e paths configuraveis por `SESSION_COOKIE_NAME`, `REMEMBER_COOKIE_NAME`, `SESSION_COOKIE_PATH`, `REMEMBER_COOKIE_PATH`; defaults atuais congelados para compat.
- Session metadata: `state`, `mode`, `remember`, `permanent`, `created_at`, `last_seen_at`, `expires_at`, `backend_verified`, `snapshot{used,age_seconds}`.
- CSRF: `csrf_token` da sessao e header frontend `X-CSRFToken`.
- Frontend: `api-client.js` envia credentials, `Accept: application/json`, `X-Correlation-ID`, `X-Request-ID`, timeout default 45000ms e redireciona 401 para `#/login`.
- Evolucao: somente com teste de contrato de sessao, teste frontend login e validacao humana de seguranca.

## 10. Contratos de RBAC/permissoes congelados

- Produtor: `backend/src/controle_treinamentos/auth.py`.
- Consumidor: `permission_required`, `is_endpoint_permitted`, `frontend/src/app/route-registry.js`, `frontend/src/shell/navigation.js`, SSR templates.
- Catalogo congelado:
  - Dashboard: `dashboard:view`.
  - Operacoes: `operacoes:view`, `pernoites:view/create/edit/delete`, `bases:view`.
  - Relatorios: `relatorios:view`, `relatorio_habilitacoes:view`, `relatorio_individual:view`.
  - Cadastros: `cadastros:view`, `tripulantes:view/create/edit/delete`, `treinamentos:view/create/edit/delete`, `treinamentos_anexos:view/create/delete`, `tripulantes_file:view/create/delete/replace`, `equipamentos:view/create/edit/delete`, `tipos_treinamento:view/create/edit/delete`.
  - Usuarios/admin: `usuarios:view`, `usuarios:manage`, `monitoramento:view`, `backups:view`, `backups:run`, `auditoria:view`, `notificacoes:view`, `notificacoes:edit`.
  - Financeiro: `finance:missions:read/create/update/cancel/delete/recalculate`, `finance:bonuses:read/recalculate`, `finance:parameters:read/create/update`, `finance:periods:read/recalculate/close/reopen`, `finance:audit:read`, `finance:divergences:read`, `finance:exports:create`.
- Role sets financeiros congelados: `admin`, `gestora`, `financeiro`, `operacoes`, `auditor`, `leitura`.
- Dependencias de permissao congeladas: create/edit/delete implicam view conforme `PERMISSION_DEPENDENCIES`; finance exports dependem de leitura de bonus/periodos.
- Regra: nenhuma renomeacao, remocao ou mudanca de permissao durante reorganizacao; qualquer evolucao exige teste RBAC e validacao humana.

## 11. Contratos de rotas/aliases congelados

### SPA hash routes

Produtor: `frontend/src/app/route-registry.js`, `frontend/src/shell/navigation.js`, `frontend/src/state/navigation-state.js`.

Rotas congeladas:

- `#/login`.
- `#/dashboard`, `#/dashboard-operacional`, `#/dashboard-operacional-tv`.
- `#/tripulantes`, `#/tripulantes/new`, `#/tripulantes/<id>`.
- `#/treinamentos`, `#/treinamentos/new`, `#/treinamentos/<id>`, `#/treinamentos/raiz`.
- `#/relatorios/habilitacoes`, `#/relatorios/individual`.
- `#/financeiro/missoes`, `#/financeiro/lancamentos-jornada`, `#/financeiro/fechamento-parametros`.
- Compat financeiro: `#/financeiro/bonificacoes`, `#/financeiro/bonificacoes/horaria`, `#/financeiro/bonificacoes/produtividade`.

Permissoes SPA: congeladas conforme route registry; nao mover modulo sem manter lazy imports e permission gates.

### SSR/backend links, aliases e redirects

Produtor: `frontend/src/compat/backend-links.js`, `backend/src/controle_treinamentos/core/frontend_routes.py`, blueprints SSR.

Backend links congelados:

- `/auditoria`, `/backups`, `/bases`, `/equipamentos`, `/manual/usuario.pdf`, `/monitoramento`, `/notificacoes-email`, `/pernoites`, `/pernoites/novo`, `/tipos-treinamento`, `/treinamentos/consolidado/export.csv`, `/treinamentos/consolidado/export.pdf`, `/treinamentos/consolidado/relatorio`, `/usuarios`, `/usuarios/novo`.

Aliases congelados:

- `/tipos` -> `#/treinamentos/raiz`.
- `/dashboard` -> `#/dashboard`.
- `/tripulantes` -> `#/tripulantes`.
- `/treinamentos` -> `#/treinamentos`.
- `/tipos-treinamento` -> `#/treinamentos/raiz`.
- `/treinamentos/consolidado` -> `#/relatorios/habilitacoes`.

Regra: aliases, redirects e backend links tem evolucao `nenhuma` durante reorganizacao. Remocao exige prova objetiva de consumidor externo ausente e validacao humana.

## 12. Contratos de PDF/CSV/export congelados

| ID | Export | Arquivos | Formato congelado | Permissao | Evolucao |
|---|---|---|---|---|---|
| CFR-PDF-HAB-001 | `/treinamentos/consolidado/export.pdf` | `routes_treinamentos.py`, `pdf_document_policy.py` | `HABILITACOES_EXPORT_PDF_POLICY`, PDF `%PDF`/`%%EOF`, headers `X-Document-*`, auditoria | `relatorio_habilitacoes:view` | nenhuma |
| CFR-CSV-HAB-001 | `/treinamentos/consolidado/export.csv` | `routes_treinamentos.py`, `contracts/relatorios.py` | `text/csv; charset=utf-8`, BOM, delimiter `;`, colunas congeladas | `relatorio_habilitacoes:view` | nenhuma |
| CFR-PDF-TRIP-001 | `/tripulantes/<id>/relatorio/export.pdf` | `routes_tripulante_views.py`, `pdf_document_policy.py` | `TRIPULANTE_TREINAMENTOS_EXPORT_PDF_POLICY` | login/permissao relatorio | nenhuma |
| CFR-PDF-AUD-001 | `/auditoria/export.pdf` | `blueprints/admin/routes.py`, `pdf_document_policy.py` | `AUDITORIA_EXPORT_PDF_POLICY`, filtros `entidade,acao,autor,busca` | `auditoria:view` | nenhuma |
| CFR-PDF-MAN-001 | `/manual/usuario.pdf` | `routes_operacional.py`, `pdf_document_policy.py` | `USER_GUIDE_PDF_POLICY` | `monitoramento:view` | nenhuma |
| CFR-PDF-EVID-001 | treinamento/tripulante files | `file_access_policy.py`, `pdf_document_policy.py` | uploaded PDF evidence, hash/policy/soft delete | file/anexo permissions | nenhuma |
| CFR-PDF-FIN-001 | PDFs financeiros | `api/http/financeiro/routes.py`, relatorios financeiros | attachment, `no-store`, `nosniff`, `X-Document-Policy`, request/correlation em footer | finance export/read | somente versionado |

## 13. Contratos de schema/repository congelados

### CFR-SCHEMA-CORE-001 - Schema core

- Tipo: banco/schema/constraints.
- Produtor: `backend/src/controle_treinamentos/db/schema.py`, `backend/src/controle_treinamentos/db/migrations.py`.
- Consumidor: repositories, application services, SSR/API, scripts de consistencia, backups.
- Tabelas congeladas: `usuarios`, `tripulantes`, `equipamentos`, `tipos_treinamento`, `segmentos_teoricos`, `horas_voo_aeronave`, `treinamentos`, `notificacoes_email`, `bases`, `pilotos`, `historico_status_piloto`, `auditoria_eventos`, `sistema_controle`, `notificacoes_treinamento`, `pernoites_operacionais`, `tripulante_periodos_operacionais`, `treinamento_anexos_pdf`, `tripulante_arquivos_pdf`, `backups_execucoes`, `background_jobs`, `background_job_executions`, `request_error_events`.
- Campos/status criticos: `usuarios.perfil` `operador|gestora`; `equipamentos.categoria_financeira` `a|b|turbohelice_palmas|nao_aplicavel`; `pilotos.status` `ativo|folga|ferias|atestado|afastado|treinamento`; `pernoites_operacionais.tipo_pernoite` `cobertura_base|operacional_comum`; PDF statuses `ativo|substituido|removido`; jobs status `queued|running|succeeded|failed|dead_letter|canceled`.
- Repositories envolvidos: `repositories/user_repository.py`, `repositories/catalogos.py`, `repositories/bases.py`, `repositories/tripulante_files.py`, application services.
- Risco se mudar: migrations e serializers quebram; dados historicos e compat residual perdem semantica.
- Teste necessario: schema bootstrap, repository unit/integration, db consistency.
- Documentacao necessaria: ERD/catálogo schema antes de mover.
- Regra de evolucao permitida: nenhuma em reorganizacao; alteracao somente com migration versionada, teste e validacao humana.

### CFR-SCHEMA-FIN-001 - Schema financeiro

- Tipo: banco/schema financeiro sensivel.
- Produtor: `backend/src/controle_treinamentos/db/schema.py`, `contracts/financeiro.py`, repositories/application financeiro.
- Consumidor: endpoints financeiros, relatorios, jobs/scripts, auditoria.
- Tabelas congeladas: `financeiro_missoes_operacionais`, `financeiro_missao_tripulantes`, `financeiro_parametros`, `financeiro_feriados`, `financeiro_competencias`, `financeiro_calculos_horarios`, `financeiro_calculos_produtividade`, `financeiro_divergencias`.
- Campos/status criticos: `competencia YYYY-MM`, `status` missoes `rascunho|ativa|cancelada|recalculo_pendente`; periodos `aberta|em_conferencia|fechada|reaberta`; participantes `comandante|copiloto`; parametros `NUMERIC(14,4)` e status `ativo|inativo|substituido`; money `NUMERIC(14,2)`; severidade `bloqueante|alta|media|informativa`.
- Indices/constraints criticos: unicidade por org/competencia, calculos correntes, feriados por data/tipo/localidade, soft delete e consistencia de tripulacao.
- Risco se mudar: pagamentos incorretos, duplicidade de calculos, fechamento comprometido.
- Teste necessario: `tests/unit/test_financeiro_schema.py`, schema bootstrap, repository/application/http financeiro.
- Documentacao necessaria: contrato financeiro versionado e plano de migracao.
- Regra de evolucao permitida: somente com versionamento, migration explicita, teste e validacao humana financeira.

### CFR-REPO-001 - Boundaries de repositories/application

- Tipo: contrato interno de produtor de dados.
- Produtor: `backend/src/controle_treinamentos/repositories/*.py`, `backend/src/controle_treinamentos/application/*.py`.
- Consumidor: rotas HTTP, jobs, relatorios, scripts.
- Arquivos criticos: `financeiro_missoes.py`, `financeiro_parametros.py`, `financeiro_observabilidade.py`, `tripulante_files.py`, `tripulante_operational_periods.py`, `training_program.py`, `treinamentos.py`, `operacoes.py`.
- Formato atual: rows dict-like usados por serializers; nomes de colunas e aliases SQL sao contrato.
- Risco se mudar: serializer fica sem campo ou muda semantica sem alterar rota.
- Teste necessario: unitarios de repositories e contract HTTP.
- Documentacao necessaria: mapa repository -> serializer -> endpoint.
- Regra de evolucao permitida: somente apos teste de contrato; sem renomeacao observavel.

## 14. Contratos de jobs/scripts congelados

### CFR-JOB-001 - Background jobs

- Tipo: job/operacional/DB.
- Produtor: `backend/src/controle_treinamentos/infra/jobs.py`.
- Consumidor: admin `/backups/executar`, worker, scripts, monitoramento.
- Formato atual: job types `send_daily_notifications`, `run_backup`; status `queued`, `running`, `succeeded`, `dead_letter`; tabelas `background_jobs`, `background_job_executions`.
- Campos criticos: `payload`, `_trace.correlation_id`, `origin_request_id`, `idempotency_key`, `attempts`, `max_attempts`, execution evidence.
- Status/saida: `process_background_jobs` retorna `processed,succeeded,failed,dead_letter`; worker sai 1 se houver dead_letter.
- Permissoes: enqueue de backup manual por `backups:run`; jobs admin `usuarios:manage`.
- Risco se mudar: jobs duplicados, backup/notification fora de idempotencia, monitoramento errado.
- Teste necessario: jobs worker/admin, metrics, backup/notifications.
- Documentacao necessaria: runbook de jobs e fila.
- Regra de evolucao permitida: nenhuma sem validacao operacional.

### CFR-SCRIPT-001 - Scripts canonicos e wrappers compat

- Tipo: CLI/operacional.
- Produtor: `docs/operations/canonical-commands.md`, `ops/README.md`, `scripts/README.md`, `backend/tools/maintenance/**`, `ops/scripts/**`.
- Consumidor: operadores, scheduler Windows, CI, release gates, automacao externa.
- Contratos congelados:
  - Backend local: `backend/tools/runtime/run.py`.
  - App service: `ops/windows/scripts/Invoke-AppService.ps1`.
  - Frontend build: `frontend/scripts/build_frontend.py`.
  - CI minimo: `ops/scripts/release/run_ci_validation_minimal.py`.
  - Smoke: `ops/scripts/smoke/post_deploy_smoke.py`.
  - Release strict: `ops/scripts/release/run_release_strict.py`.
  - Backup: `backend/tools/maintenance/run_backups.py`, wrapper `scripts/backup/run_backups.py`.
  - Restore drill/postcheck: `ops/scripts/backup/backup_restore_drill.py`, `backend/tools/maintenance/run_restore_postcheck.py`.
  - Jobs worker: `backend/tools/maintenance/run_jobs_worker.py`, wrapper `scripts/jobs/run_jobs_worker.py`.
  - Notifications: `backend/tools/maintenance/run_notifications.py`, wrapper `scripts/jobs/run_notifications.py`.
  - Scheduler: `ops/windows/scripts/Install-WindowsScheduledTasks.ps1`.
  - Schema/seed/consistency: `backend/tools/maintenance/bootstrap_db_schema.py`, `bootstrap_seed_data.py`, `run_db_consistency.py`.
  - Manual unsafe repair: `backend/tools/manual_unsafe/run_db_repair.py`.
- Formato atual: wrappers em `scripts/` sao COMPAT, emitem aviso e delegam; `run_db_consistency.py --repair` canonico bloqueia e aponta manual unsafe.
- Risco se mudar: agendadores e runbooks externos quebram silenciosamente.
- Teste necessario: smoke operacional de scripts, release gate, backup/restore drill.
- Documentacao necessaria: lista de comandos canonicos e depreciacoes.
- Regra de evolucao permitida: nenhuma sem prova de consumidor ausente e validacao humana.

### CFR-ENV-001 - Variaveis de ambiente e runtime

- Tipo: configuracao/operacional.
- Produtor: `.env.example`, `ops/windows/env/prod.env.example`, `ops/windows/env/hml.env.example`, `backend/src/controle_treinamentos/__init__.py`, infra modules.
- Consumidor: app, frontend compat, jobs, backup, AISWEB, SMTP/Resend, monitoramento.
- Variaveis criticas congeladas: `APP_ENV`, `SECRET_KEY`, `SECRET_KEY_FINGERPRINT`, `DATABASE_URL`, `ALLOW_LOCAL_DATABASE_IN_SECURE_ENV`, `ALLOW_INSECURE_HTTP_IN_SECURE_ENV`, `SESSION_HOURS`, cookie vars, `TRUST_PROXY_HEADERS`, `FRONTEND_PUBLIC_ORIGIN`, `FRONTEND_LOCAL_ORIGIN`, `FRONTEND_ALLOWED_ORIGINS`, `FRONTEND_COMPAT_REDIRECTS`, `AISWEB_*`, `EMAIL_PROVIDER`, `SMTP_*`, `RESEND_*`, `CRON_SECRET`, `METRICS_TOKEN`, `SENTRY_DSN`, `JOB_*`, backup/runtime paths, `TRAINING_ATTACHMENT_MAX_MB`.
- Risco se mudar: login, redirects, CORS, integracoes e jobs falham por ambiente.
- Teste necessario: runtime env boundaries, CORS, session cookie config, smoke deploy.
- Documentacao necessaria: matriz env por ambiente.
- Regra de evolucao permitida: nenhuma sem release note e validacao operacional.

## 15. Integracoes externas, logs e auditoria congelados

### CFR-EXT-AISWEB-001 - AISWEB MET/NOTAM

- Produtor: `infra/aisweb_client.py`, `application/aisweb_weather.py`, `application/aisweb_notams.py`.
- Consumidor: dashboard operacional e aliases HTTP.
- Formato externo: base default `http://aisweb.decea.gov.br/api/`, query `apiKey`, `apiPass`, `area`, `icaoCode`; user-agent `BrasilVida-Operacional/1.0`; XML/text; timeout/cache envs.
- Campos internos congelados: weather `available|stale|unavailable|error`; notam `available|empty|stale|unavailable|error`; severidade `critical|warning|attention|info`.
- Regra: somente versionado/testado; alias HTTP nenhuma mudanca.

### CFR-EXT-MAIL-001 - Email SMTP/Resend

- Produtor: `backend/src/controle_treinamentos/infra/mailer.py`.
- Consumidor: job `send_daily_notifications`, admin/notificacoes.
- Formato atual: provider `EMAIL_PROVIDER` default `smtp`; SMTP vars `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_PORT`, `SMTP_USE_SSL`, `SMTP_USE_TLS`, sender; Resend vars `RESEND_API_KEY`, `RESEND_FROM`.
- Tabelas: `notificacoes_email`, `notificacoes_treinamento`, `sistema_controle`.
- Regra: nenhuma renomeacao de env/saida sem validacao operacional.

### CFR-EXT-BACKUP-001 - Backup local/externo

- Produtor: `backend/src/controle_treinamentos/infra/backup.py`, `ops/scripts/backup/run_backups.py`.
- Consumidor: job `run_backup`, admin backups, restore drill.
- Formato atual: artefatos `db_backup_<stamp>.dump|json.gz|sqlite3.gz`, `assets_backup_<stamp>.tar.gz`, `config_backup_<stamp>.tar.gz`, `backup_manifest_<stamp>.json`; historico em `backups_execucoes`; copia externa opcional.
- Regra: nenhuma renomeacao de artefato, manifest ou saida JSON sem validacao de restore.

### CFR-AUDIT-001 - Auditoria, logs e metricas

- Produtor: `backend/src/controle_treinamentos/audit.py`, `core/audit_utils.py`, `core/logging.py`, `core/metrics.py`, `core/errors.py`, `core/security.py`.
- Consumidor: auditoria admin/financeira, suporte, metricas, Sentry, logs.
- Formato atual: `auditoria_eventos(entidade,entidade_id,acao,payload_anterior,payload_novo,realizado_por,observacao)`, mascaramento de campos sensiveis, logs JSON single-line com `timestamp,level,logger,message,module,function,line,request_id,correlation_id`, eventos `http_request`, `error_response`, `background_job_*`, `pdf_document`, `file_access`.
- Risco se mudar: perda de trilha de auditoria e conformidade.
- Teste necessario: audit events, HTTP request logging, metrics, PDF/file policies.
- Regra de evolucao permitida: nenhuma sem validacao humana de auditoria/operacao.

## 16. Matriz contrato -> produtor -> consumidor -> risco -> mudanca permitida

| Contrato | Produtor | Consumidor | Risco se mudar | Mudanca permitida |
|---|---|---|---|---|
| CFR-HTTP-AUTH-001 | auth routes/auth_contract/security | session-service/login/api-client | quebra login, CSRF e capabilities | somente com versionamento + teste + validacao |
| CFR-HTTP-ERR-001 | http_utils/errors/security/cors | api-client, suporte, scripts | handlers frontend e trace quebram | nenhuma |
| CFR-HTTP-DASH-001 | dashboard routes/contracts/AISWEB apps | dashboard SPA | primeira tela e aliases AISWEB quebram | somente aditiva apos teste; aliases nenhuma |
| CFR-HTTP-CAD-TRIP-001 | cadastros routes/tripulantes contract | SPA tripulantes/financeiro/relatorios | formularios e filtros quebram | somente aditiva apos teste |
| CFR-HTTP-CAD-MEDIA-001 | media routes/file policy | SPA/SSR/download/auditoria | documentos/fotos sensiveis inacessiveis | nenhuma |
| CFR-HTTP-CAD-TRE-001 | treinamentos routes/contracts | SPA/relatorios | CRUD/anexos e relatorios quebram | somente aditiva apos teste |
| CFR-HTTP-CAD-ROOT-001 | training_program routes/contracts | SPA raiz/batch | matriz de treinamento e evidencias quebram | teste + validacao |
| CFR-HTTP-REL-001 | relatorios routes/contracts | SPA/export/Excel | CSV/PDF e filtros quebram | export nenhuma; JSON aditiva apos teste |
| CFR-HTTP-OPS-001 | operacoes API/SSR | SSR/futuro SPA | cutover pernoites contaminado | nenhuma ate cutover |
| CFR-HTTP-BASES-001 | bases blueprint/contracts | SSR bases | programmatic JSON e status quebram | mutacao nenhuma; leitura aditiva apos teste |
| CFR-HTTP-FIN-MIS-001 | finance routes/contracts/application | frontend financeiro/engine | calculo e fechamento incorretos | versionamento + teste + validacao |
| CFR-HTTP-FIN-JOR-001 | finance jornada routes/app | lancamentos jornada SPA/PDF | demonstrativo e bonus horario quebram | versionamento + teste + validacao |
| CFR-HTTP-FIN-BON-001 | finance relatorios/bonus apps | SPA/PDF/download | pagamento e PDF incorretos | versionamento + teste + validacao |
| CFR-HTTP-FIN-GOV-001 | finance gov/preflight apps | fechamento parametros SPA | fechamento/parametros/auditoria quebram | nenhuma para status/permissao; demais versionado |
| CFR-ROUTE-SPA-001 | route-registry/navigation | shell SPA | navegacao e RBAC client quebram | nenhuma sem teste frontend |
| CFR-ROUTE-SSR-001 | backend-links/frontend_routes/blueprints | SSR/links externos | bookmarks e redirects quebram | nenhuma |
| CFR-PDFCSV-001 | pdf policy/relatorios/routes | browser/Excel/auditoria | exports invalidos | nenhuma |
| CFR-SCHEMA-CORE-001 | schema/migrations | repos/API/jobs | dados e constraints quebram | versionado + migration + validacao |
| CFR-SCHEMA-FIN-001 | schema/contracts finance | financeiro | risco financeiro direto | versionado + teste + validacao |
| CFR-REPO-001 | repositories/application | routes/jobs/reports | serializers perdem campos | somente apos teste |
| CFR-JOB-001 | infra/jobs | worker/admin/metrics | duplicidade/falha operacional | nenhuma sem validacao |
| CFR-SCRIPT-001 | ops/backend tools/scripts | operadores/scheduler/CI | automacao externa quebra | nenhuma |
| CFR-ENV-001 | env examples/runtime config | app/infra/deploy | ambiente falha em runtime | nenhuma sem release note |
| CFR-EXT-AISWEB-001 | aisweb client/apps | dashboard/AISWEB API | clima/NOTAM indisponivel | versionado/testado |
| CFR-EXT-MAIL-001 | mailer | notifications job | notificacoes falham | nenhuma sem validacao |
| CFR-EXT-BACKUP-001 | backup infra/scripts | jobs/restore | backup/restore falha | nenhuma sem drill |
| CFR-AUDIT-001 | audit/logging/metrics/errors | auditoria/suporte | perda de rastreabilidade | nenhuma |

## 17. Lacunas encontradas

- Nao foi encontrado contrato OpenAPI unico e machine-readable para todos os endpoints; os contratos vivem em rotas, serializers, testes e documentos dispersos.
- Alguns endpoints programaticos de admin/jobs possuem envelope proprio e nao devem ser "corrigidos" por padronizacao durante reorganizacao.
- A existencia de wrappers `scripts/` indica consumidores externos potenciais; nao ha prova objetiva de ausencia de uso externo.
- A escrita API de pernoites esta explicitamente futura/nao registrada; qualquer exposicao antes do cutover e breaking governance.
- PDFs financeiros e exports SSR dependem de validacao visual/binaria; teste textual isolado nao basta.
- O schema financeiro tem riscos de precisao decimal e unicidade; reorganizacao fisica nao deve tocar migrations.
- A arvore de trabalho tinha alteracoes preexistentes fora deste documento; este registro nao as valida nem as libera.
- Nenhum endpoint foi executado por regra deste gate; a verificacao e estatica.

## 18. Proximo passo recomendado

Antes de qualquer move fisico:

1. Transformar este registro em checklist obrigatorio do release gate.
2. Gerar ou consolidar uma especificacao OpenAPI/contract snapshot sem mudar os endpoints.
3. Rodar somente testes de contrato e arquitetura ja existentes para obter baseline.
4. Criar matriz de arquivos permitidos para move com owner e teste minimo por contrato impactado.
5. Exigir validacao humana explicita para financeiro, RBAC, sessao, PDF/CSV, schema, jobs/scripts e auditoria.

Conclusao: a reorganizacao fisica permanece bloqueada ate que cada contrato impactado tenha prova automatizada de compatibilidade e aceite humano quando classificado como sensivel.
