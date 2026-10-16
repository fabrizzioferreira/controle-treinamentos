# Auditability Gate Register - Reorganizacao Fisica

Data: 2026-06-06
Status geral: BLOQUEADO PARA REORGANIZACAO FISICA
Escopo: auditoria minima para operacoes sensiveis antes de qualquer move, rename, refatoracao, alteracao de contrato ou reorganizacao fisica.

Este documento e um gate de auditoria. Ele nao libera alteracao de codigo, schema,
contrato, permissao, rota, job, script, PDF, CSV ou fluxo operacional. Ele apenas
registra o estado atual observado por leitura estatica dos arquivos e define o
minimo exigido para evolucao segura.

## 1. Resumo executivo

A auditoria persistida atual existe principalmente por `auditoria_eventos` e pelos
helpers `record_audit_event`, `audit_event`, `audit_document_generation` e
`audit_relevant_download`.

O schema atual de `auditoria_eventos` cobre entidade, ID da entidade, acao,
payload anterior, payload novo, usuario executor, timestamp e observacao. Esse
modelo e util para rastreabilidade funcional, mas ainda nao cobre nativamente
campos obrigatorios para compliance operacional completo, como IP, user-agent,
request id, correlation id, origem, resultado, sucesso/falha e checksum de
artefato.

Logs estruturados, metricas, headers de resposta, stdout de scripts e historico
operacional em tabelas auxiliares nao sao considerados auditoria suficiente para
este gate. Eles podem complementar a investigacao, mas nao substituem evento de
auditoria persistido, consultavel e ligado a usuario, entidade, operacao e
resultado.

Conclusao: nenhuma operacao critica deve ser considerada liberada para mudanca
estrutural sem teste de contrato/auditoria e validacao humana. Operacoes
financeiras, RBAC/admin, usuarios, tripulantes, treinamentos, documentos, backups,
jobs, cleanup, migrations e seeds permanecem congeladas para reorganizacao fisica.

## 2. Arquivo criado

- `docs/release-gates/auditability-gate-register.md`

## 3. Criterios de auditoria minima

### 3.1 Campos minimos exigidos

Cada operacao sensivel deve ter auditoria persistida contendo, quando aplicavel:

- Usuario executor: ID do usuario autenticado ou ator tecnico explicitamente
  identificado.
- Timestamp: data/hora persistida no banco.
- Acao: nome estavel, especifico e nao ambiguo da operacao.
- Entidade: tipo de entidade afetada.
- ID do registro: identificador da entidade principal afetada.
- Before: estado anterior ou snapshot minimo antes da alteracao.
- After: estado novo ou snapshot minimo depois da alteracao.
- Motivo: justificativa humana ou tecnica para a operacao sensivel.
- Resultado: sucesso, falha, bloqueio, parcial, dry-run ou cancelamento.
- Origem: endpoint, script, job, rotina ou canal que disparou a operacao.
- IP e user-agent: origem de rede quando a operacao vier de request HTTP.
- Request id e correlation id: rastreabilidade entre HTTP, logs, jobs e auditoria.
- Sucesso/falha: resultado booleano ou enum persistido.
- Artifact/checksum: hash, nome, tamanho e politica do artefato quando houver PDF,
  CSV, backup, arquivo, foto, anexo ou documento gerado/baixado.

### 3.2 Status do gate

- `suficiente`: auditoria persistida contem todos os campos minimos aplicaveis e
  ha teste cobrindo a operacao.
- `parcial`: existe auditoria persistida relevante, mas faltam campos
  estruturais, granularidade, resultado, metadados de request ou teste.
- `insuficiente`: ha apenas log, metrica, stdout, tabela operacional auxiliar ou
  auditoria sem cobertura minima para a operacao.
- `ausente`: nao foi encontrada evidencia de auditoria persistida para a
  operacao.
- `bloqueado`: a operacao e destrutiva, operacionalmente critica ou altera base,
  schema, usuario, permissao, historico, artefato ou dados sensiveis sem
  auditoria minima suficiente.

### 3.3 Regra de evolucao

Mudancas em operacoes sensiveis so sao permitidas quando forem aditivas,
versionadas quando houver contrato externo, cobertas por teste de auditoria e
aprovadas por validacao humana. Nenhum campo existente de auditoria, contrato,
response, permissao, rota, schema, PDF, CSV, job ou script pode ser renomeado ou
removido durante a reorganizacao fisica.

### 3.4 Fontes reais lidas

#### Auditoria, schema e helpers

- `backend/src/controle_treinamentos/audit.py`
- `backend/src/controle_treinamentos/core/audit_utils.py`
- `backend/src/controle_treinamentos/db/schema.py`
- `backend/src/controle_treinamentos/core/logging.py`
- `backend/src/controle_treinamentos/core/security.py`
- `backend/src/controle_treinamentos/core/errors.py`
- `backend/src/controle_treinamentos/core/metrics.py`

#### Auth, admin, RBAC e operacoes administrativas

- `backend/src/controle_treinamentos/blueprints/auth/routes.py`
- `backend/src/controle_treinamentos/blueprints/admin/routes.py`
- `backend/src/controle_treinamentos/blueprints/admin/routes_operacional.py`

#### Tripulantes, treinamentos, documentos e relatorios

- `backend/src/controle_treinamentos/application/tripulantes.py`
- `backend/src/controle_treinamentos/application/tripulante_media.py`
- `backend/src/controle_treinamentos/application/treinamentos.py`
- `backend/src/controle_treinamentos/application/training_program.py`
- `backend/src/controle_treinamentos/application/treinamentos_ssr_reports.py`
- `backend/src/controle_treinamentos/blueprints/cadastros/routes_tripulante_views.py`
- `backend/src/controle_treinamentos/core/pdf_document_policy.py`
- `backend/src/controle_treinamentos/core/file_access_policy.py`

#### Financeiro

- `backend/src/controle_treinamentos/financeiro_audit_events.py`
- `backend/src/controle_treinamentos/api/http/financeiro/routes.py`
- `backend/src/controle_treinamentos/application/financeiro_missoes.py`
- `backend/src/controle_treinamentos/application/financeiro_lancamentos_jornada.py`
- `backend/src/controle_treinamentos/application/financeiro_competencias.py`
- `backend/src/controle_treinamentos/application/financeiro_parametros.py`
- `backend/src/controle_treinamentos/application/financeiro_feriados.py`
- `backend/src/controle_treinamentos/application/financeiro_relatorios.py`
- `backend/src/controle_treinamentos/application/financeiro_produtividade_relatorio_geral.py`
- `backend/src/controle_treinamentos/application/financeiro_horas_totais_voadas.py`

#### Jobs, backups, restore, cleanup, migrations e seed

- `backend/src/controle_treinamentos/infra/jobs.py`
- `backend/src/controle_treinamentos/infra/backup.py`
- `ops/scripts/backup/backup_restore_drill.py`
- `backend/tools/maintenance/run_restore_postcheck.py`
- `ops/scripts/backup/run_restore_postcheck.py`
- `backend/tools/maintenance/bootstrap_db_schema.py`
- `backend/tools/maintenance/bootstrap_seed_data.py`
- `backend/src/controle_treinamentos/db/schema_bootstrap.py`
- `backend/src/controle_treinamentos/db/migrations.py`
- `backend/src/controle_treinamentos/db/seeder.py`
- `ops/scripts/database/run_db_consistency.py`
- `backend/tools/manual_unsafe/run_db_repair.py`
- `ops/scripts/database/cleanup_operational_data.py`
- `backend/tools/manual_unsafe/cleanup_operational_data.py`
- `ops/scripts/database/dry_run_tripulante_pdf_cleanup.py`
- `ops/scripts/database/apply_tripulante_pdf_cleanup.py`
- `ops/scripts/admin/sanitize_test_users.py`
- `ops/scripts/admin/ensure_admin_user.py`

## 4. Operacoes financeiras auditadas

As operacoes financeiras possuem o catalogo `FINANCE_AUDIT_EVENT_CATALOG` em
`backend/src/controle_treinamentos/financeiro_audit_events.py`, com expectativa
de metadados como `event_name`, `org_id`, `request_id`, `correlation_id`,
`actor_user_id`, `entity_type`, `entity_id`, `permission` e `source_endpoint`.

Na implementacao atual, os eventos financeiros persistem bons snapshots de
before/after e razao em varios fluxos, mas a cobertura de request id, correlation
id, origem, IP, user-agent, resultado e checksum nao e uniforme. Em
`financeiro_lancamentos_jornada.py`, por exemplo, o helper `_audit` inicializa
`request_id`, `correlation_id` e `source_endpoint` como string vazia por padrao.

Contratos financeiros permanecem congelados:

- Lancamento financeiro criado, editado, cancelado ou excluido.
- Recalculo financeiro de missao, jornada, produtividade ou competencia.
- Fechamento e reabertura de competencia.
- Alteracao de parametro financeiro.
- Alteracao de feriado financeiro.
- Exportacao financeira em PDF ou relatorio.

Gate financeiro: `parcial` para fluxos com `auditoria_eventos`; `bloqueado` para
qualquer mudanca estrutural sem preenchimento consistente dos metadados minimos,
teste de auditoria e validacao humana.

## 5. Operacoes RBAC/admin auditadas

`backend/src/controle_treinamentos/blueprints/admin/routes.py` registra eventos
persistidos para criacao e edicao de usuarios via `audit_event`.

As operacoes de desativacao, alteracao de role e alteracao de permissoes sao
observadas como `usuario update`, pois compartilham o endpoint de edicao. Esse
registro preserva before/after, mas nao possui acao especifica, motivo dedicado,
diff estruturado de permissoes, IP, user-agent, request id, correlation id ou
resultado persistido.

`backend/src/controle_treinamentos/blueprints/admin/routes_operacional.py`
registra auditoria para enqueue manual de backup e requeue de job, mas a execucao
posterior do backup/job depende de tabelas operacionais e logs complementares.

Gate RBAC/admin: `parcial` para criacao/edicao de usuario por endpoint; `parcial`
para role/permissao/desativacao por auditoria generica de update; `bloqueado`
para criacao/edicao/desativacao de usuarios por scripts operacionais sem evento
persistido minimo.

## 6. Operacoes tripulantes/treinamentos auditadas

`tripulantes.py`, `tripulante_media.py`, `treinamentos.py` e
`training_program.py` possuem auditoria persistida para criacao, edicao,
exclusao/inativacao, alteracao de foto, anexos, arquivos PDF, treinamentos e
cadastros raiz.

A cobertura atual e funcionalmente relevante porque registra entidade, ID,
acao, usuario, before/after e observacao. As lacunas principais sao ausencia de
IP, user-agent, request id, correlation id, origem, resultado, motivo humano
consistente e checksum de artefatos em todos os eventos de upload/remocao.

Gate tripulantes/treinamentos: `parcial`. Mudancas estruturais continuam
bloqueadas ate haver testes de auditoria por operacao e decisao humana sobre os
campos minimos faltantes.

## 7. Operacoes documentos/PDF/CSV auditadas

`audit_document_generation` registra eventos persistidos para geracao de
documentos como PDF/CSV com politica, tipo, dominio, renderer, filename, filtros
e detalhes. `audit_relevant_download` registra downloads relevantes, mas nao
registra previews e nao persiste checksum, IP, user-agent, request id,
correlation id ou resultado.

`pdf_document_policy.py` e `file_access_policy.py` adicionam headers, metricas e
logs estruturados, mas isso nao e suficiente para este gate sem evento persistido
completo.

Gate documentos/PDF/CSV: `parcial` para geracao/download com evento persistido;
`insuficiente` para previews ou acessos sem evento persistido; `bloqueado` para
qualquer alteracao em politica, rota, renderer, nome de arquivo, filtros ou
payload sem teste de auditoria.

## 8. Operacoes backup/jobs/scripts auditadas

Backups via UI/API sao enfileirados em `background_jobs` com `requested_by` e
`origin_request_id`, e possuem evento `background_job enqueue_manual` em
`auditoria_eventos`. A execucao do backup grava historico em `backups_execucoes`
e manifesto com artefatos e `sha256`, mas a tabela de historico nao liga
nativamente actor, request id, correlation id, IP ou user-agent ao resultado
final da execucao.

Requeue de job possui auditoria persistida `requeue_dead_letter`, mas tambem
carece dos metadados minimos de request e resultado operacional completo.

Scripts de restore, migration, repair, cleanup e seed dependem principalmente de
stdout, JSON de evidencia, logs ou alteracoes diretas no banco. Com excecao do
cleanup especifico de PDFs de tripulante, que insere eventos por item removido,
nao ha envelope uniforme de auditoria persistida para execucao de script
operacional.

Gate backup/jobs/scripts: `parcial` para backup enfileirado e requeue; `bloqueado`
para restore, cleanup destrutivo, migration, repair, seed e scripts operacionais
sem auditoria minima persistida.

## 9. Matriz operacao -> auditoria atual -> lacuna -> gate

| ID | Operacao | Modulo | Origem | Endpoint ou script | Tabelas afetadas | Auditoria atual | Lacuna principal | Teste necessario | Gate |
|---|---|---|---|---|---|---|---|---|---|
| AUD-001 | Login | Auth/session | `backend/src/controle_treinamentos/blueprints/auth/routes.py` | `POST /login`, `POST /api/v1/session/login` | `usuarios`, sessao | Log estruturado `auth_outcome`, metricas e sessao | Sem `auditoria_eventos`; resultado, IP/user-agent e request/correlation nao persistidos como auditoria | Teste de login deve validar evento persistido com usuario, origem, resultado e request id | insuficiente |
| AUD-002 | Logout | Auth/session | `backend/src/controle_treinamentos/blueprints/auth/routes.py` | `POST /logout`, `POST /api/v1/session/logout` | sessao | Log estruturado `auth_outcome` e metricas | Sem evento persistido de encerramento de sessao | Teste deve validar auditoria de logout com usuario, origem e resultado | insuficiente |
| AUD-003 | Falha de login | Auth/session | `backend/src/controle_treinamentos/blueprints/auth/routes.py`, `backend/src/controle_treinamentos/core/audit_utils.py` | `POST /login`, `POST /api/v1/session/login` | `usuarios`, sessao, rate limit | Log estruturado, metricas e `register_login_failure` em sessao | Falha nao persistida em auditoria operacional com login mascarado, IP, user-agent, request id e motivo | Teste deve validar evento persistido para credencial invalida, usuario inativo e falha tecnica | insuficiente |
| AUD-004 | Criacao de usuario | Admin/RBAC | `backend/src/controle_treinamentos/blueprints/admin/routes.py` | `/usuarios/novo` | `usuarios`, `auditoria_eventos` | `audit_event` com entidade `usuario`, acao `create`, payload novo | Falta IP, user-agent, request/correlation, resultado e motivo | Teste de contrato de auditoria para criacao de usuario | parcial |
| AUD-005 | Edicao de usuario | Admin/RBAC | `backend/src/controle_treinamentos/blueprints/admin/routes.py` | `/usuarios/<id>/editar` | `usuarios`, `auditoria_eventos` | `audit_event` com entidade `usuario`, acao `update`, before/after | Falta diff estruturado, motivo, request metadata e resultado | Teste deve validar before/after mascarado e metadados minimos | parcial |
| AUD-006 | Desativacao de usuario | Admin/RBAC | `backend/src/controle_treinamentos/blueprints/admin/routes.py` | `/usuarios/<id>/editar` | `usuarios`, `auditoria_eventos` | Auditoria generica `usuario update` | Sem acao especifica `deactivate`, motivo obrigatorio e resultado persistido | Teste deve distinguir desativacao de edicao comum | parcial |
| AUD-007 | Alteracao de role | Admin/RBAC | `backend/src/controle_treinamentos/blueprints/admin/routes.py` | `/usuarios/<id>/editar` | `usuarios.perfil`, `auditoria_eventos` | Auditoria generica `usuario update` | Sem acao especifica `role_change`, sem diff dedicado e request metadata | Teste deve validar role anterior/nova e permissao usada | parcial |
| AUD-008 | Alteracao de permissao | Admin/RBAC | `backend/src/controle_treinamentos/blueprints/admin/routes.py` | `/usuarios/<id>/editar` | `usuarios.permissao_modulos_json`, `auditoria_eventos` | Auditoria generica `usuario update` | Sem acao especifica `permission_change`, diff de permissoes e motivo | Teste deve validar permissoes adicionadas/removidas e ator | parcial |
| AUD-009 | Criacao de tripulante | Tripulantes | `backend/src/controle_treinamentos/application/tripulantes.py` | Endpoints de tripulantes consumidores do service | `tripulantes`, `pilotos`, `auditoria_eventos` | `record_audit_event` via helper com acao `create` | Falta origem HTTP, IP/user-agent, request/correlation e resultado | Teste deve validar payload minimo de criacao | parcial |
| AUD-010 | Edicao de tripulante | Tripulantes | `backend/src/controle_treinamentos/application/tripulantes.py` | Endpoints de tripulantes consumidores do service | `tripulantes`, `pilotos`, `auditoria_eventos` | Acao `update` com before/after | Falta motivo, origem, request metadata e resultado | Teste deve validar before/after e campos sensiveis mascarados | parcial |
| AUD-011 | Exclusao/inativacao de tripulante | Tripulantes | `backend/src/controle_treinamentos/application/tripulantes.py` | Endpoints de exclusao/inativacao | `tripulantes`, `pilotos`, historicos, media, `auditoria_eventos` | Acao `status_change` ou `delete` com before/after | Motivo humano nao uniforme; sem request metadata e resultado | Teste deve cobrir exclusao fisica e inativacao por dependencia | parcial |
| AUD-012 | Upload de foto/anexo | Documentos/tripulantes/treinamentos | `backend/src/controle_treinamentos/application/tripulante_media.py`, `backend/src/controle_treinamentos/application/treinamentos.py` | Endpoints de upload de foto, PDF e anexo | `tripulante_arquivos_pdf`, `treinamento_anexos_pdf`, `tripulantes`, `auditoria_eventos` | Acao `create` ou `update` com nome, MIME e tamanho em varios fluxos | Checksum/artifact nao uniforme; sem IP/user-agent, request/correlation e resultado | Teste deve validar auditoria com hash, tamanho, policy e entidade | parcial |
| AUD-013 | Remocao de foto/anexo | Documentos/tripulantes/treinamentos | `backend/src/controle_treinamentos/application/tripulante_media.py`, `backend/src/controle_treinamentos/application/treinamentos.py` | Endpoints de remocao de foto, PDF e anexo | `tripulante_arquivos_pdf`, `treinamento_anexos_pdf`, `tripulantes`, `auditoria_eventos` | Acao `delete` com before/after ou before | Motivo fixo/nao obrigatorio, checksum e request metadata ausentes | Teste deve validar motivo, before, after e artefato removido | parcial |
| AUD-014 | Criacao de treinamento | Treinamentos | `backend/src/controle_treinamentos/application/treinamentos.py`, `backend/src/controle_treinamentos/application/training_program.py` | Endpoints de treinamento/programa | `treinamentos`, `auditoria_eventos` | Acao `create` com payload novo | Falta origem, request metadata, resultado e motivo quando aplicavel | Teste deve validar auditoria por treinamento criado | parcial |
| AUD-015 | Edicao de treinamento | Treinamentos | `backend/src/controle_treinamentos/application/treinamentos.py`, `backend/src/controle_treinamentos/application/training_program.py` | Endpoints de edicao de treinamento | `treinamentos`, `auditoria_eventos` | Acao `update` com before/after | Falta motivo, request metadata e resultado | Teste deve validar diff e preservacao de campos de dominio | parcial |
| AUD-016 | Exclusao/cancelamento de treinamento | Treinamentos | `backend/src/controle_treinamentos/application/treinamentos.py`, `backend/src/controle_treinamentos/application/training_program.py` | Endpoints de exclusao/cancelamento | `treinamentos`, anexos, notificacoes, `auditoria_eventos` | Acao `delete` com before | Sem motivo obrigatorio, resultado persistido e request metadata | Teste deve cobrir exclusao/cancelamento e anexos vinculados | parcial |
| AUD-017 | Alteracao de cadastro raiz | Cadastros raiz | `backend/src/controle_treinamentos/application/training_program.py` | Endpoints de tipos, segmentos e horas de voo | `tipos_treinamento`, `segmentos_teoricos`, `horas_voo_aeronave`, `auditoria_eventos` | Acao `create`, `update` ou `delete` por entidade | Falta motivo, origem, request metadata e resultado | Teste deve validar entidade raiz antes/depois e ator | parcial |
| AUD-018 | Criacao de lancamento financeiro | Financeiro | `backend/src/controle_treinamentos/application/financeiro_missoes.py`, `backend/src/controle_treinamentos/application/financeiro_lancamentos_jornada.py` | `POST /api/v1/financeiro/...` | Tabelas financeiras de missoes/jornada, `auditoria_eventos` | Eventos financeiros de criacao com before/after e metadados parciais | `request_id`, `correlation_id` e `source_endpoint` ausentes ou vazios em fluxos; sem IP/user-agent/resultado | Teste deve validar catalogo financeiro completo e permissao usada | parcial |
| AUD-019 | Edicao de lancamento financeiro | Financeiro | `backend/src/controle_treinamentos/application/financeiro_missoes.py`, `backend/src/controle_treinamentos/application/financeiro_lancamentos_jornada.py` | `PATCH /api/v1/financeiro/...` | Tabelas financeiras de missoes/jornada, `auditoria_eventos` | Eventos financeiros de update/recalculo com changed fields em alguns fluxos | Metadados de request/origem incompletos; resultado nao uniforme | Teste deve validar before/after, motivo, competencia e moeda | parcial |
| AUD-020 | Cancelamento/exclusao financeira | Financeiro | `backend/src/controle_treinamentos/application/financeiro_missoes.py`, `backend/src/controle_treinamentos/application/financeiro_lancamentos_jornada.py` | Endpoints `cancelar`, `DELETE` financeiro | Tabelas financeiras, `auditoria_eventos` | Eventos financeiros de cancelamento/delete com motivo em alguns fluxos | Sem request/correlation/origem/IP/resultado uniformes | Teste deve validar motivo obrigatorio, before/after e falhas bloqueadas | parcial |
| AUD-021 | Recalculo financeiro | Financeiro | `backend/src/controle_treinamentos/application/financeiro_missoes.py`, `backend/src/controle_treinamentos/application/financeiro_lancamentos_jornada.py`, `backend/src/controle_treinamentos/application/financeiro_competencias.py` | Endpoints `/recalcular` financeiros | Tabelas financeiras de calculo, competencia e jornada, `auditoria_eventos` | Eventos de recalculo/calculate/recalculated em varios services | Origem e resultado incompletos; request/correlation ausentes em varios eventos | Teste deve validar versao de calculo, competencia, totais e resultado | parcial |
| AUD-022 | Fechamento de competencia | Financeiro | `backend/src/controle_treinamentos/application/financeiro_competencias.py` | `POST /api/v1/financeiro/competencias/<id>/fechar` | Competencias financeiras, snapshots financeiros, `auditoria_eventos` | Evento `finance.period.closed` com before/after e release gate | Motivo pode nao ser obrigatorio; sem request/correlation/origem/IP/resultado | Teste deve validar confirmacao, snapshot, competencia e bloqueios | parcial |
| AUD-023 | Reabertura de competencia | Financeiro | `backend/src/controle_treinamentos/application/financeiro_competencias.py` | `POST /api/v1/financeiro/competencias/<id>/reabrir` | Competencias financeiras, `auditoria_eventos` | Evento `finance.period.reopened` com motivo | Sem request/correlation/origem/IP/user-agent/resultado | Teste deve validar motivo, before/after e permissao | parcial |
| AUD-024 | Alteracao de parametro financeiro | Financeiro | `backend/src/controle_treinamentos/application/financeiro_parametros.py` | Endpoints de parametros financeiros | Parametros financeiros, `auditoria_eventos` | Eventos `finance.parameter.created/updated` com reason e changed fields | Sem request/correlation/origem/IP/user-agent/resultado | Teste deve validar valor monetario/decimal, competencia e motivo | parcial |
| AUD-025 | Alteracao de feriado | Financeiro | `backend/src/controle_treinamentos/application/financeiro_feriados.py` | Endpoints de feriados financeiros | Feriados financeiros, `auditoria_eventos` | Eventos financeiros para entidade `finance_holiday` | `reason` fica `None`; faltam request/correlation/origem/IP/resultado | Teste deve validar motivo obrigatorio e data afetada | parcial |
| AUD-026 | Exportacao de relatorio | Relatorios | `backend/src/controle_treinamentos/application/treinamentos_ssr_reports.py`, `backend/src/controle_treinamentos/application/financeiro_relatorios.py` | Endpoints de relatorio/export | Dados consultados, `auditoria_eventos` | `audit_document_generation` e eventos `finance.export.generated` | Checksum, resultado e IP/user-agent ausentes; request metadata desigual | Teste deve validar filtros, linhas, usuario, arquivo e checksum | parcial |
| AUD-027 | Geracao de PDF | Documentos/PDF | `backend/src/controle_treinamentos/core/pdf_document_policy.py`, rotas consumidoras | Endpoints `*.pdf` | Dados consultados, `auditoria_eventos` quando helper e usado | Auditoria de documento em varios PDFs; logs/headers de policy | Logs/headers nao bastam; checksum e resultado nao persistidos | Teste deve validar evento por PDF, policy, filename, filtros e hash | parcial |
| AUD-028 | Geracao de CSV | Documentos/CSV | `backend/src/controle_treinamentos/application/treinamentos_ssr_reports.py` | Export CSV consolidado | Dados consultados, `auditoria_eventos` | `audit_document_generation` com `kind=csv_export` | Sem checksum, IP/user-agent, request/correlation e resultado | Teste deve validar evento por CSV, filtros, linhas e hash | parcial |
| AUD-029 | Download de documento | Documentos/download | `backend/src/controle_treinamentos/core/file_access_policy.py`, rotas de arquivos/anexos | Endpoints de download de arquivo/anexo | Tabelas de arquivos/anexos, `auditoria_eventos` | `audit_relevant_download` somente para action `download` | Preview nao persistido; sem checksum, IP/user-agent, request id e resultado | Teste deve validar download, preview, policy, subject e artefato | parcial |
| AUD-030 | Execucao de backup | Operacional/backup | `backend/src/controle_treinamentos/blueprints/admin/routes_operacional.py`, `backend/src/controle_treinamentos/infra/backup.py` | `/backups/executar`, job de backup | `background_jobs`, `backups_execucoes`, artefatos, `auditoria_eventos` | Enqueue auditado; historico de backup com manifest e `sha256` | Execucao final nao ligada a ator/request em `backups_execucoes`; sem evento de conclusao em `auditoria_eventos` | Teste deve validar enqueue, execucao, manifest, checksum e ator | parcial |
| AUD-031 | Restore | Operacional/restore | `ops/scripts/backup/backup_restore_drill.py`, `backend/tools/maintenance/run_restore_postcheck.py` | Scripts de restore/postcheck | Banco temporario, artefatos de backup | Evidencia JSON/stdout e logs | Sem auditoria persistida padronizada com ator, origem, resultado e checksums vinculados | Teste deve validar trilha persistida de restore dry-run e restore real controlado | bloqueado |
| AUD-032 | Requeue/reactivate job | Operacional/jobs | `backend/src/controle_treinamentos/blueprints/admin/routes_operacional.py`, `backend/src/controle_treinamentos/infra/jobs.py` | `/jobs/<id>/reativar` | `background_jobs`, `auditoria_eventos` | Evento `background_job requeue_dead_letter` com before/after | Sem IP/user-agent, request/correlation e resultado operacional completo | Teste deve validar estado anterior, novo job, ator e request metadata | parcial |
| AUD-033 | Execucao de script operacional | Operacional/scripts | `ops/scripts/**`, `backend/tools/**` | Scripts administrativos e de manutencao | Varia por script | stdout, JSON, logs ou efeitos indiretos | Sem envelope uniforme de auditoria persistida por script | Teste deve validar evento por execucao com args mascarados, ator, host, resultado e artefatos | insuficiente |
| AUD-034 | Cleanup | Operacional/cleanup | `ops/scripts/database/cleanup_operational_data.py`, `ops/scripts/database/apply_tripulante_pdf_cleanup.py`, `ops/scripts/admin/sanitize_test_users.py` | Scripts de cleanup | Multiplas tabelas, arquivos, `auditoria_eventos` | Cleanup de PDF insere eventos por item; outros cleanups usam JSON/stdout e podem alterar/remover auditoria | Cleanup operacional geral pode apagar trilha de auditoria; sem envelope minimo uniforme | Teste deve validar dry-run, confirmacao, evento mestre, eventos por item e bloqueio de producao | bloqueado |
| AUD-035 | Migration | Banco/schema | `backend/src/controle_treinamentos/db/migrations.py`, `backend/src/controle_treinamentos/db/schema_bootstrap.py`, `ops/scripts/database/run_db_consistency.py` | Bootstrap, consistency, repair e migrations | Schema e dados | Logs/stdout/relatorios de consistencia | Sem auditoria persistida de ator, diff, motivo, request/origem e resultado | Teste deve validar evento de migration/repair com checksum de script e plano aplicado | bloqueado |
| AUD-036 | Seed | Banco/seed | `backend/src/controle_treinamentos/db/seeder.py`, `backend/tools/maintenance/bootstrap_seed_data.py`, `ops/scripts/admin/ensure_admin_user.py` | Seed/bootstrap/admin user scripts | `usuarios`, cadastros raiz, parametros e dados base | stdout/JSON; writes diretos via script | Sem auditoria persistida para usuario/defaults criados ou alterados | Teste deve validar ator tecnico, ambiente, before/after, motivo e resultado | bloqueado |

## 10. Operacoes bloqueadas

Permanecem explicitamente bloqueadas para reorganizacao fisica, refatoracao,
rename, move, alteracao de contrato ou mudanca operacional sem gate adicional:

- Login, logout e falha de login, enquanto dependerem de log/metrica/sessao sem
  evento persistido minimo.
- Criacao, edicao, desativacao, role e permissoes de usuario por scripts
  administrativos sem `auditoria_eventos`.
- Restore e postcheck de restore sem trilha persistida vinculada a ator,
  artefatos, checksums e resultado.
- Execucao generica de scripts operacionais sem envelope padrao de auditoria.
- Cleanup operacional destrutivo, especialmente rotinas que podem alterar ou
  remover `auditoria_eventos`.
- Migrations, repair, schema bootstrap e consistencia com reparo manual.
- Seed, bootstrap de dados e criacao/alteracao de admin por script.
- Qualquer alteracao em financeiro, RBAC, tripulantes, treinamentos, documentos,
  PDF, CSV, jobs ou backups antes de teste de auditoria e validacao humana.

## 11. Testes necessarios

Testes minimos exigidos antes de qualquer desbloqueio:

- Teste de contrato da tabela `auditoria_eventos` e dos helpers
  `record_audit_event`, `audit_event`, `audit_document_generation` e
  `audit_relevant_download`.
- Teste de login, logout e falha de login validando auditoria persistida, nao
  apenas log estruturado.
- Testes RBAC/admin para criacao, edicao, desativacao, role change e permission
  change, com before/after e diff de permissoes.
- Testes financeiros por evento do catalogo, incluindo competencia, valores
  monetarios, motivo, permissao, origem, request id e resultado.
- Testes de tripulantes e treinamentos para create/update/delete/status_change,
  anexos, fotos e cadastros raiz.
- Testes de PDF/CSV/download garantindo policy, filtros, filename, linhas,
  usuario, request/correlation e checksum.
- Testes de backup conectando enqueue, job, historico, manifest, checksums,
  sucesso/falha e ator.
- Testes de jobs para requeue/reactivate com before/after e resultado.
- Testes de scripts operacionais exigindo evento mestre, argumentos mascarados,
  dry-run, confirmacao, resultado, host/origem e artefatos.
- Testes de cleanup garantindo que auditoria nao seja removida sem evento externo
  imutavel e aprovacao humana.
- Testes de migration/repair/seed com checksum do script, plano aplicado,
  before/after ou diff e ator tecnico.

## 12. Lacunas estruturais

- `auditoria_eventos` nao possui campos nativos para IP, user-agent, request id,
  correlation id, origem, resultado, sucesso/falha ou checksum.
- O helper `record_audit_event` nao recebe envelope operacional completo; ele
  persiste apenas entidade, acao, before, after, usuario e observacao.
- `normalize_audit_payload` mascara campos sensiveis corretamente, mas converte
  `Decimal` para float, o que exige cuidado adicional em auditoria financeira.
- Auth/session registra logs e metricas, mas nao eventos persistidos de sucesso,
  logout e falha de login.
- Alteracoes de role, permissao e desativacao de usuario aparecem como update
  generico de usuario.
- Fluxos financeiros possuem catalogo rico, mas preenchimento inconsistente de
  request id, correlation id, source endpoint e resultado.
- Downloads relevantes sao auditados apenas para `download`; previews nao tem a
  mesma trilha persistida.
- Geracao de PDF/CSV nao persiste checksum do artefato como campo obrigatorio.
- `backups_execucoes` guarda historico operacional, mas nao liga nativamente
  execucao a ator, request/correlation e auditoria mestre.
- Scripts operacionais nao compartilham um envelope padrao de auditoria
  persistida.
- Cleanup, migration, repair e seed podem alterar dados criticos sem trilha
  minima uniforme.

## 13. Proximo passo recomendado

Antes de qualquer reorganizacao fisica, criar um plano de remediacao de
auditabilidade sem alterar contratos de produto: definir o envelope minimo de
auditoria, versionar a evolucao do schema de auditoria, escrever testes de
contrato por operacao sensivel e submeter os fluxos bloqueados a validacao humana
de seguranca, produto e operacoes.

Enquanto esses gates nao forem atendidos, a reorganizacao fisica permanece
bloqueada.
