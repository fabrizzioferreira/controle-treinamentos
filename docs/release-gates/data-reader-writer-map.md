# Data Reader/Writer Map

Status: BLOQUEADO PARA REORGANIZACAO FISICA
Data: 2026-06-06
Escopo: tabelas criticas, leitores, escritores, deleters, rotas, services, repositories, contracts, testes, invariantes e bloqueios.

Este documento e um gate de reorganizacao. Ele nao libera move, rename, limpeza, refatoracao, alteracao estrutural, alteracao de schema, alteracao de query, migration, seed, endpoint destrutivo ou script operacional.

## 1. Resumo executivo

A reorganizacao fisica permanece bloqueada. O contrato vivo de dados esta distribuido entre `backend/src/controle_treinamentos/db/schema.py`, migracoes corretivas em `backend/src/controle_treinamentos/db/migrations.py`, repositories SQL, application services, rotas HTTP/SSR, contracts e testes.

O mapa identifica tabelas criticas, seus leitores e escritores atuais, rotas consumidoras, services, repositories, contracts, testes conhecidos, invariantes e riscos. Nenhuma tabela foi marcada como segura para reorganizacao porque a baseline P0 anterior esta vermelha/bloqueada e porque alguns fluxos ainda dependem de SQL direto em blueprints, infra operacional e application services.

Fontes reais lidas e congeladas como referencia de mapeamento:

- `backend/src/controle_treinamentos/db/schema.py`
- `backend/src/controle_treinamentos/db/migrations.py`
- `backend/src/controle_treinamentos/repositories/*.py`
- `backend/src/controle_treinamentos/application/*.py`
- `backend/src/controle_treinamentos/api/http/**/*.py`
- `backend/src/controle_treinamentos/blueprints/**/*.py`
- `backend/src/controle_treinamentos/contracts/*.py`
- `backend/src/controle_treinamentos/audit.py`
- `backend/src/controle_treinamentos/cache.py`
- `backend/src/controle_treinamentos/core/errors.py`
- `backend/src/controle_treinamentos/core/sistema_controle_policy.py`
- `backend/src/controle_treinamentos/infra/backup.py`
- `backend/src/controle_treinamentos/infra/jobs.py`
- `backend/src/controle_treinamentos/infra/mailer.py`
- `backend/src/controle_treinamentos/monitoring/_monitoring_impl.py`
- `tests/unit`, `tests/integration`, `tests/contract`, `tests/architecture`, `tests/ops`

## 2. Arquivo criado

Arquivo novo:

- `docs/release-gates/data-reader-writer-map.md`

Arquivos de produto alterados:

- Nenhum.

Operacoes nao executadas:

- Migrations nao foram executadas.
- Seeds nao foram executados.
- Scripts operacionais nao foram executados.
- Endpoints nao foram chamados.
- Queries destrutivas nao foram executadas.

## 3. Tabelas criticas mapeadas

| Tabela | Dominio | Finalidade | Constraints e invariantes principais | Status |
| --- | --- | --- | --- | --- |
| `usuarios` | RBAC/sessao/admin | Identidade, login, perfil e permissoes modulares | `login` unico; `perfil` em `operador` ou `gestora`; `permissao_modulos_json` usado por capabilities | Bloqueado |
| `tripulantes` | Tripulantes/documentos/financeiro | Cadastro operacional, foto, flags financeiras e vinculos | `cpf` unico; status/base/ativo; flags `sdea_ativo`, `instrutor_ativo`, `checador_ativo`, `elegivel_adicional_excepcional`; estado de foto | Bloqueado |
| `pilotos` | Bases/operacao | Vinculo operacional com tripulante e base | `matricula` unica; `tripulante_id` unico; status enumerado | Bloqueado |
| `historico_status_piloto` | Bases/auditoria operacional | Historico de status/base de piloto | FK para `pilotos`, `bases`, `usuarios`; trilha temporal | Bloqueado |
| `treinamentos` | Treinamentos | Registros de treinamento individual e programa raiz | FKs para tripulante/equipamento/tipo/segmento; checks de estrutura entre segmento, programa e equipamento | Bloqueado |
| `tipos_treinamento` | Catalogos/treinamentos | Tipos de treinamento e configuracao de periodicidade | `codigo` unico quando existe; `modalidade`; `periodicidade_meses`; `ativo` | Bloqueado |
| `segmentos_teoricos` | Treinamento raiz | Segmentos teoricos por tipo | FK para `tipos_treinamento` com cascade; referencia original unica quando existe | Bloqueado |
| `horas_voo_aeronave` | Treinamento raiz | Horas de voo por aeronave/modelo | FK para `tipos_treinamento` com cascade; referencia original unica quando existe | Bloqueado |
| `auditoria_eventos` | Auditoria/compliance | Eventos persistidos de auditoria | Entidade, entidade_id, acao, before/after/contexto, usuario e timestamp indexados | Bloqueado |
| `request_error_events` | Observabilidade/erros HTTP | Persistencia de erro por request | `request_id` unico; status, code, path, endpoint, metodo, usuario e contexto | Bloqueado |
| `backups_execucoes` | Backup/operacao | Historico persistido de backups | Status `sucesso`/`falha`; artefatos JSON; tamanho/duracao/mensagem | Bloqueado |
| `background_jobs` | Jobs/fila | Fila persistida, deduplicacao e lock de jobs | Status `queued`, `running`, `succeeded`, `failed`, `dead_letter`, `canceled`; `idempotency_key` unico quando existe | Bloqueado |
| `background_job_executions` | Jobs/fila | Historico de tentativas por job | FK cascade para `background_jobs`; status de execucao; duracao e erro | Bloqueado |
| `pernoites_operacionais` | Operacoes/financeiro | Pernoites por tripulante | FK cascade para tripulante; tipo em `cobertura_base` ou `operacional_comum`; quantidade | Bloqueado |
| `financeiro_missoes_operacionais` | Financeiro | Missao operacional e competencia financeira | `competencia` `YYYY-MM`; status financeiro; soft delete; datas/horarios; checks de tripulacao | Bloqueado |
| `financeiro_missao_tripulantes` | Financeiro | Participantes de missao | FK cascade para missao; funcao `comandante`/`copiloto`; status; unicidade por missao/tripulante | Bloqueado |
| `financeiro_calculos_horarios` | Financeiro/calculo | Resultado horario vigente ou obsoleto | Valores nao negativos; status `calculado`, `recalculo_pendente`, `obsoleto`; indice unico para vigente | Bloqueado |
| `financeiro_calculos_produtividade` | Financeiro/calculo | Resultado de produtividade por competencia | `competencia` `YYYY-MM`; valores monetarios; memoria JSON; status vigente | Bloqueado |
| `financeiro_competencias` | Financeiro/fechamento | Estado de fechamento de competencia | Status `aberta`, `em_conferencia`, `fechada`, `reaberta`; unicidade org/competencia | Bloqueado |
| `financeiro_parametros` | Financeiro/governanca | Parametros vigentes de calculo | `valor` numerico 14,4; vigencia; status `ativo`, `inativo`, `substituido` | Bloqueado |
| `financeiro_feriados` | Financeiro/calendario | Feriados usados por calculos | Tipo `nacional`, `estadual`, `municipal`, `operacional`; status; unicidade org/data/tipo/localidade | Bloqueado |
| `financeiro_divergencias` | Financeiro/observabilidade | Divergencias de competencia/calculo | Severidade e status; vinculos com competencia e entidade | Bloqueado |
| `equipamentos` | Catalogos/financeiro/treinamentos | Equipamentos e categoria financeira | Categoria financeira restrita; ativo; usado em treinamento e financeiro | Bloqueado |
| `notificacoes_email` | Admin/notificacoes | Destinatarios ativos de notificacao | `email_destinatario` unico; `ativo` | Bloqueado |
| `sistema_controle` | Controle residual/cache/notificacao | Chave/valor residual controlado | Uso generico proibido por policy; apenas cache legado e compat notificacao | Bloqueado |
| `treinamento_anexos_pdf` | Documentos/treinamentos | PDF anexado a treinamento | FK cascade para treinamento; hash; status `ativo`/`removido`; usuario de upload/remocao | Bloqueado |
| `tripulante_arquivos_pdf` | Documentos/tripulantes | PDF documental de tripulante | FK cascade para tripulante; hash obrigatorio; status `ativo`, `substituido`, `removido`; hash ativo unico | Bloqueado |
| `notificacoes_treinamento` | Notificacoes/treinamentos | Controle de gatilhos enviados | FK cascade para treinamento; gatilho `30`, `60`, `90`, `vencido`; unicidade por treinamento/gatilho | Bloqueado |
| `tripulante_periodos_operacionais` | Tripulantes/financeiro | Periodos operacionais, como ferias | Status `ativo`/`cancelado`; datas validas; cancelamento consistente | Bloqueado |
| `bases` | Bases/operacao | Bases operacionais de pilotos/tripulantes | `nome` unico; uf/coordenadas; ativo | Bloqueado |

## 4. Matriz tabela -> leitores -> escritores

| Tabela | Leitores principais | Escritores principais | Deleters, canceladores ou soft deletes |
| --- | --- | --- | --- |
| `usuarios` | `repositories/user_repository.py:UserRepository.get_by_login`; `blueprints/auth/routes.py`; `blueprints/admin/routes.py`; `audit.py` via FK | `blueprints/admin/routes.py` cria/edita/desativa; `core/audit_utils.py` normaliza permissoes nulas | Desativacao por `UPDATE usuarios SET ativo`; sem delete fisico mapeado no gate |
| `tripulantes` | `repositories/tripulantes.py`; `repositories/queries.py`; `repositories/dashboard_cache.py`; repos financeiros; `application/tripulante_media.py` | `repositories/tripulantes.py:create_tripulante/update_tripulante/update_tripulante_photo_state`; `application/tripulante_media.py`; `application/base_operations.py` sincroniza piloto | `repositories/tripulantes.py:inactivate_tripulante/delete_tripulante`; bloqueado por dependencias financeiras/documentais |
| `pilotos` | `repositories/bases.py`; `repositories/queries.py`; `repositories/dashboard_cache.py` | `repositories/bases.py:insert_pilot/update_pilot_status/update_pilot_base` | `repositories/tripulantes.py:delete_pilotos_by_ids` quando tripulante e removido |
| `historico_status_piloto` | `repositories/bases.py:fetch_pilot_history` | `repositories/bases.py:insert_pilot_history`; `application/base_operations.py` | `repositories/tripulantes.py:delete_historico_status_piloto_by_pilot_ids` |
| `treinamentos` | `repositories/treinamentos.py`; `repositories/training_program.py`; `repositories/queries.py`; `repositories/dashboard_cache.py`; `infra/mailer.py` | `repositories/treinamentos.py:create_treinamento/update_treinamento`; `repositories/training_program.py:create_training_program_record/update_training_program_record` | `repositories/treinamentos.py:delete_treinamento`; `repositories/training_program.py:delete_training_program_record` |
| `tipos_treinamento` | `repositories/catalogos.py`; `repositories/training_program.py`; `repositories/treinamentos.py`; `repositories/queries.py` | `repositories/catalogos.py:create_tipo_treinamento/update_tipo_treinamento`; `repositories/training_program.py:create_training_master_type_cascade/update_training_master_type_cascade` | `repositories/catalogos.py:delete_tipo_treinamento`; `repositories/training_program.py:delete_training_master_type_cascade` |
| `segmentos_teoricos` | `repositories/training_program.py`; `repositories/treinamentos.py` | `repositories/training_program.py:create_training_master_segment/update_training_master_segment` | `repositories/training_program.py:delete_training_master_segment`; FK cascade por tipo |
| `horas_voo_aeronave` | `repositories/training_program.py` | `repositories/training_program.py:create_training_master_hour/update_training_master_hour` | `repositories/training_program.py:delete_training_master_hour`; FK cascade por tipo |
| `auditoria_eventos` | `blueprints/admin/routes.py`; `repositories/financeiro_observabilidade.py` | `audit.py:record_audit_event`; `application/financeiro_governanca_parametros.py`; services com `_audit_event` | Sem delete mapeado; retencao nao deve ser inferida |
| `request_error_events` | `core/errors.py`; `monitoring/_monitoring_impl.py` | `core/errors.py:_persist_error_event_db` com upsert por `request_id` | Sem delete mapeado no gate |
| `backups_execucoes` | `infra/backup.py:list_backup_history`; `monitoring/_monitoring_impl.py`; `blueprints/admin/routes_operacional.py` | `infra/backup.py:_record_backup_history` | Sem delete mapeado no gate; limpeza fisica de artefatos e separada |
| `background_jobs` | `infra/jobs.py`; `monitoring/_monitoring_impl.py`; `blueprints/admin/routes_operacional.py` | `infra/jobs.py:enqueue_background_job/_claim_next_job/_mark_job_as_success/_mark_job_as_failure/requeue_dead_letter_job` | `infra/jobs.py:_cleanup_old_job_history` remove historico antigo |
| `background_job_executions` | `infra/jobs.py`; `monitoring/_monitoring_impl.py` | `infra/jobs.py:_create_execution_log/_finalize_execution_log` | `infra/jobs.py:_cleanup_old_job_history`; FK cascade por job |
| `pernoites_operacionais` | `repositories/operacoes.py`; finance productivity services | `repositories/operacoes.py:insert_pernoite/update_pernoite` | `repositories/operacoes.py:delete_pernoite` |
| `financeiro_missoes_operacionais` | `repositories/financeiro_missoes.py`; `repositories/financeiro_lancamentos_jornada.py`; calculation/report repos | `repositories/financeiro_missoes.py:create_missao_operacional/update_missao_operacional/cancel_missao_operacional/soft_delete_missao_operacional` | Soft delete/cancelamento em `financeiro_missoes.py`; delete fisico nao permitido sem gate |
| `financeiro_missao_tripulantes` | `repositories/financeiro_missoes.py`; `repositories/financeiro_lancamentos_jornada.py`; productivity repos | `repositories/financeiro_missoes.py:insert_missao_tripulante/insert_tripulantes_missao/replace_missao_tripulantes/update_missao_tripulantes_cobertura` | `replace_missao_tripulantes` usa delete fisico; `cancel_missao_tripulantes`/`remover_missao_tripulantes` alteram status |
| `financeiro_calculos_horarios` | `repositories/financeiro_calculos_horarios.py`; jornada/report repos | `repositories/financeiro_calculos_horarios.py:salvar_calculo_horario/salvar_ou_atualizar_calculo_horario_vigente/substituir_calculos_da_missao` | `invalidar_calculos_horarios_vigentes_da_missao` e obsolescencia de duplicados |
| `financeiro_calculos_produtividade` | `repositories/financeiro_calculos_produtividade.py`; reports | `repositories/financeiro_calculos_produtividade.py:salvar_calculo_produtividade` | `invalidar_calculos_produtividade_vigentes_da_competencia` |
| `financeiro_competencias` | `repositories/financeiro_competencias.py`; `repositories/financeiro_missoes.py` | `repositories/financeiro_competencias.py:upsert_competencia_em_conferencia/fechar_competencia_financeira/reabrir_competencia_financeira` | Sem delete mapeado; reabertura muda status |
| `financeiro_parametros` | `repositories/financeiro_parametros.py`; engines de bonificacao; governanca | `repositories/financeiro_parametros.py:criar_parametro_financeiro/atualizar_parametro_financeiro` | Substituicao/inativacao por status; sem delete mapeado |
| `financeiro_feriados` | `repositories/financeiro_feriados.py`; jornada/calculo | `repositories/financeiro_feriados.py:criar_feriado_nacional/atualizar_feriado_nacional` | Inativacao por status; sem delete mapeado |
| `financeiro_divergencias` | `repositories/financeiro_competencias.py`; `repositories/financeiro_observabilidade.py` | Competencia/preflight/calculo registram divergencias | Resolucao/ignoracao por status quando aplicavel; sem delete mapeado |
| `equipamentos` | `repositories/catalogos.py`; `repositories/treinamentos.py`; finance repos | `repositories/catalogos.py:create_equipamento/update_equipamento` | `repositories/catalogos.py:delete_equipamento` condicionado a vinculos |
| `notificacoes_email` | `blueprints/admin/routes.py`; `infra/mailer.py` | `blueprints/admin/routes.py` cria/edita/desativa | Desativacao por `ativo`; sem delete fisico mapeado |
| `sistema_controle` | `cache.py`; `infra/mailer.py`; `monitoring/_monitoring_impl.py`; `blueprints/admin/routes.py` | `cache.py:_set_cache`; `infra/mailer.py:_set_control_value`; `db/seeder.py` apenas fora deste gate | `cache.py:_cleanup_expired/_delete_cache`; uso generico bloqueado por policy |
| `treinamento_anexos_pdf` | `repositories/treinamentos.py`; `repositories/training_program.py`; `repositories/tripulante_files.py` | `repositories/treinamentos.py:create_treinamento_attachment_record`; training program attachment flow | `repositories/treinamentos.py:delete_treinamento_attachment_record/delete_treinamento_attachments`; status removido |
| `tripulante_arquivos_pdf` | `repositories/tripulante_files.py`; `repositories/tripulantes.py` dependencia | `repositories/tripulante_files.py:insert_tripulante_file`; `application/tripulante_media.py` substitui/remove | `application/tripulante_media.py:delete_tripulante_file`; status removido/substituido |
| `notificacoes_treinamento` | `infra/mailer.py`; training queries | Mailer registra gatilhos enviados | `repositories/treinamentos.py:delete_treinamento_notifications`; `repositories/training_program.py:delete_training_program_record_notifications`; FK cascade |
| `tripulante_periodos_operacionais` | `repositories/tripulante_operational_periods.py`; `repositories/tripulantes.py` dependencia; finance engines | `repositories/tripulante_operational_periods.py:insert_operational_period/cancel_operational_period` | Cancelamento por status; sem delete fisico mapeado |
| `bases` | `repositories/bases.py`; `repositories/queries.py`; dashboard | Cadastros/base operations quando aplicavel | Sem delete mapeado no gate |

## 5. Matriz tabela -> rotas/endpoints

| Tabela | Rotas/endpoints consumidores |
| --- | --- |
| `usuarios` | `blueprints/auth/routes.py`: `/login`, `/logout`, `/api/v1/session`, `/api/v1/session/login`, `/api/v1/session/logout`, `/api/v1/me`, `/api/v1/capabilities`; `blueprints/admin/routes.py`: `/usuarios`, `/usuarios/novo`, `/usuarios/<id>/editar` |
| `tripulantes` | `api/http/cadastros/routes.py`: `/api/v1/tripulantes`, `/api/v1/tripulantes/options`, `/api/v1/tripulantes/<id>`, `/api/v1/tripulantes/<id>/photo`, `/api/v1/tripulantes/<id>/files`; `blueprints/cadastros/routes.py`: `/tripulantes`; `routes_tripulante_views.py`: `/tripulantes/<id>/relatorio`, `/export.pdf` |
| `pilotos` | `blueprints/bases/routes.py`: `/bases`, `/bases/api/dados`, `/pilotos/adicionar`, `/pilotos/<id>/status`, `/pilotos/<id>/mover`, `/pilotos/<id>/historico`, `/pilotos/<id>/foto` |
| `historico_status_piloto` | `blueprints/bases/routes.py`: `/pilotos/<id>/historico`, `/pilotos/<id>/status`, `/pilotos/<id>/mover` |
| `treinamentos` | `api/http/cadastros/routes.py`: `/api/v1/treinamentos`, `/api/v1/treinamentos/<id>`, `/attachments`; `api/http/cadastros/routes_training_program.py`: `/api/v1/treinamentos-tripulantes`; `blueprints/cadastros/routes_treinamentos.py`: `/treinamentos`, `/treinamentos/consolidado`, `/export.pdf`, `/export.csv` |
| `tipos_treinamento` | `api/http/cadastros/routes_training_program.py`: `/api/v1/treinamento-raiz/tipos`; `blueprints/cadastros/routes_catalogos.py`: `/tipos-treinamento`; training option endpoints |
| `segmentos_teoricos` | `api/http/cadastros/routes_training_program.py`: `/api/v1/treinamento-raiz/segmentos`, `/api/v1/treinamentos-tripulantes/options` |
| `horas_voo_aeronave` | `api/http/cadastros/routes_training_program.py`: `/api/v1/treinamento-raiz/horas-voo` |
| `auditoria_eventos` | `blueprints/admin/routes.py`: `/auditoria`, `/auditoria/export.pdf`; `api/http/financeiro/routes.py`: `/api/v1/financeiro/auditoria` |
| `request_error_events` | `core/errors.py` captura requests; `blueprints/admin/routes_operacional.py`: `/monitoramento`; `monitoring/_monitoring_impl.py` snapshots de diagnostico |
| `backups_execucoes` | `blueprints/admin/routes_operacional.py`: `/backups`, `/backups/executar`, `/monitoramento`; `infra/backup.py:list_backup_history` |
| `background_jobs` | `blueprints/admin/routes_operacional.py`: `/monitoramento`, `/jobs/<id>/reativar`, `/jobs/<id>/status`, `/backups/executar`; `infra/jobs.py` processamento |
| `background_job_executions` | `infra/jobs.py` processamento; `monitoring/_monitoring_impl.py` snapshots |
| `pernoites_operacionais` | `blueprints/operacoes/routes.py`: `/pernoites`, `/pernoites/novo`, `/pernoites/<id>/editar`, `/pernoites/<id>/excluir`; `api/http/operacoes/routes.py` quando contratos operacionais forem ativados |
| `financeiro_missoes_operacionais` | `api/http/financeiro/routes.py`: `/api/v1/financeiro/missoes`, `/preview`, `/<mission_id>`, `/<id>/recalcular`, `/<id>/preflight-calculo`, `/<id>/cancelar`; jornada/relatorios/competencias |
| `financeiro_missao_tripulantes` | Mesmas rotas de missoes; jornada `/api/v1/financeiro/lancamentos-jornada`; produtividade e relatorios |
| `financeiro_calculos_horarios` | `/api/v1/financeiro/lancamentos-jornada`, `/recalcular-grade`, `/<linha_id>/recalcular`; `/bonificacoes/horaria`; PDFs financeiros |
| `financeiro_calculos_produtividade` | `/api/v1/financeiro/bonificacoes/produtividade`, `/produtividade/consolidado`, `/produtividade/relatorio-geral`, PDFs de produtividade |
| `financeiro_competencias` | `/api/v1/financeiro/competencias/<competencia>`, `/preflight-calculo`, `/relatorio.pdf`, `/recalcular`, `/fechar`, `/reabrir` |
| `financeiro_parametros` | `/api/v1/financeiro/parametros`, `/api/v1/financeiro/parametros/<id>` |
| `financeiro_feriados` | `/api/v1/financeiro/feriados`, `/api/v1/financeiro/feriados/<id>` |
| `financeiro_divergencias` | `/api/v1/financeiro/divergencias`, competencias/preflight/observabilidade |
| `equipamentos` | `api/http/cadastros/routes.py`: `/api/v1/equipamentos/options`; `blueprints/cadastros/routes_catalogos.py`: `/equipamentos`; rotas financeiras de missoes e treinamentos |
| `notificacoes_email` | `blueprints/admin/routes.py`: `/notificacoes-email`, `/novo`, `/<id>/editar`, `/disparo-manual`, `/teste` |
| `sistema_controle` | Sem rota publica generica; consumido por notificacoes admin, cache residual, mailer e monitoramento |
| `treinamento_anexos_pdf` | `api/http/cadastros/routes.py`: `/api/v1/treinamentos/<id>/attachments`; `blueprints/cadastros/routes_treinamentos.py`: `/treinamentos/<id>/anexos/...`; training program attachments |
| `tripulante_arquivos_pdf` | `api/http/cadastros/routes.py`: `/api/v1/tripulantes/<id>/files`; `blueprints/cadastros/routes_file.py`: `/tripulantes/<id>/file`, `/file/upload`, `/file/<arquivo_id>`, `/file/<arquivo_id>/excluir`, `/file/<arquivo_id>/substituir` |
| `notificacoes_treinamento` | Mailer operacional; treinamentos delete/cascade; sem endpoint direto |
| `tripulante_periodos_operacionais` | `api/http/cadastros/routes.py`: `/api/v1/tripulantes/<id>/periodos-operacionais`; finance engines consomem periodos |
| `bases` | `blueprints/bases/routes.py`: `/bases`, `/bases/api/dados`; tripulante/piloto options |

## 6. Matriz tabela -> repositories/services

| Tabela | Repositories e data-access | Services/application | Contracts |
| --- | --- | --- | --- |
| `usuarios` | `repositories/user_repository.py`; SQL direto em `blueprints/admin/routes.py` | `blueprints/auth/routes.py`; admin user forms | Contrato de sessao em rotas/testes: `tests/contract/test_api_session_contract.py`, `test_session_lifecycle_contract.py` |
| `tripulantes` | `repositories/tripulantes.py`; `repositories/queries.py`; `repositories/tripulante_files.py`; repos financeiros | `application/tripulantes.py`; `application/tripulantes_reads.py`; `application/tripulante_media.py` | `contracts/tripulantes.py`; `contracts/tripulante_media.py` |
| `pilotos` | `repositories/bases.py` | `application/base_operations.py` | `contracts/bases.py` |
| `historico_status_piloto` | `repositories/bases.py` | `application/base_operations.py` | `contracts/bases.py` |
| `treinamentos` | `repositories/treinamentos.py`; `repositories/training_program.py`; `repositories/queries.py` | `application/treinamentos.py`; `application/training_program.py`; SSR reads/reports | `contracts/treinamentos.py`; `contracts/training_program.py`; `contracts/relatorios.py` |
| `tipos_treinamento` | `repositories/catalogos.py`; `repositories/training_program.py` | `application/catalogos_ssr.py`; `application/training_program.py` | `contracts/equipamentos.py` indiretamente para catalogos; `contracts/training_program.py`; `contracts/treinamentos.py` |
| `segmentos_teoricos` | `repositories/training_program.py` | `application/training_program.py`; `application/training_program_reads.py` | `contracts/training_program.py` |
| `horas_voo_aeronave` | `repositories/training_program.py` | `application/training_program.py`; `application/training_program_reads.py` | `contracts/training_program.py` |
| `auditoria_eventos` | `audit.py`; `repositories/financeiro_observabilidade.py`; SQL direto em admin | Services de dominio chamam auditoria; `application/financeiro_governanca_parametros.py` tem inserts diretos | `contracts/financeiro.py` para eventos financeiros; audit gate |
| `request_error_events` | `core/errors.py`; `monitoring/_monitoring_impl.py` | Error handlers Flask | `tests/contract/test_http_error_contract.py` |
| `backups_execucoes` | `infra/backup.py`; `monitoring/_monitoring_impl.py` | `blueprints/admin/routes_operacional.py`; job de backup | Backup gate/testes ops |
| `background_jobs` | `infra/jobs.py`; `monitoring/_monitoring_impl.py` | Rotas admin operacionais; handlers de notification/backup | Jobs queue tests |
| `background_job_executions` | `infra/jobs.py`; `monitoring/_monitoring_impl.py` | Worker/processador | Jobs queue tests |
| `pernoites_operacionais` | `repositories/operacoes.py` | `application/operacoes.py`; finance productivity | `contracts/operacoes.py` |
| `financeiro_missoes_operacionais` | `repositories/financeiro_missoes.py`; `financeiro_lancamentos_jornada.py`; calcs/repos de relatorio | `application/financeiro_missoes.py`; `financeiro_lancamentos_jornada.py`; preflight/relatorios | `contracts/financeiro.py`; `contracts/financeiro_http.py` |
| `financeiro_missao_tripulantes` | `repositories/financeiro_missoes.py`; productivity/jornada repos | Mesmos services de missoes, jornada e produtividade | `contracts/financeiro.py`; `contracts/financeiro_http.py` |
| `financeiro_calculos_horarios` | `repositories/financeiro_calculos_horarios.py`; jornada/report repos | `application/financeiro_lancamentos_jornada.py`; engines horarios | `contracts/financeiro.py`; `contracts/financeiro_http.py` |
| `financeiro_calculos_produtividade` | `repositories/financeiro_calculos_produtividade.py` | `application/financeiro_bonificacoes.py`; `financeiro_produtividade_relatorio_geral.py` | `contracts/financeiro.py`; `contracts/financeiro_http.py` |
| `financeiro_competencias` | `repositories/financeiro_competencias.py`; `repositories/financeiro_missoes.py` | `application/financeiro_competencias.py`; preflight/calculos | `contracts/financeiro.py`; `contracts/financeiro_http.py` |
| `financeiro_parametros` | `repositories/financeiro_parametros.py` | `application/financeiro_parametros.py`; `application/financeiro_governanca_parametros.py`; engines | `contracts/financeiro.py`; `contracts/financeiro_http.py` |
| `financeiro_feriados` | `repositories/financeiro_feriados.py`; jornada query | `application/financeiro_feriados.py`; engines | `contracts/financeiro.py`; `contracts/financeiro_http.py` |
| `financeiro_divergencias` | `repositories/financeiro_competencias.py`; `repositories/financeiro_observabilidade.py` | Competencias/preflight/observabilidade | `contracts/financeiro.py`; `contracts/financeiro_http.py` |
| `equipamentos` | `repositories/catalogos.py`; training/finance repos | `application/catalogos_ssr.py`; training/finance services | `contracts/equipamentos.py`; `contracts/treinamentos.py`; `contracts/financeiro.py` |
| `notificacoes_email` | SQL direto em `blueprints/admin/routes.py`; `infra/mailer.py` | Admin notificacoes e disparos | Sem contract dedicado encontrado; testes de mailer cobrem parcialmente |
| `sistema_controle` | `cache.py`; `infra/mailer.py`; `core/sistema_controle_policy.py`; monitoring | Cache residual e notificacao compat | Policy tests em `tests/unit/test_sistema_controle_policy.py` |
| `treinamento_anexos_pdf` | `repositories/treinamentos.py`; `repositories/training_program.py`; `repositories/tripulante_files.py` | `application/treinamentos.py`; training program attachments | `contracts/treinamentos.py`; `contracts/tripulante_media.py`; PDF export contracts |
| `tripulante_arquivos_pdf` | `repositories/tripulante_files.py`; dependency checks em `repositories/tripulantes.py` | `application/tripulante_media.py` | `contracts/tripulante_media.py`; file access policy |
| `notificacoes_treinamento` | `infra/mailer.py`; training delete repos | Mailer/notificacao de treinamentos | Mailer tests e relatorios |
| `tripulante_periodos_operacionais` | `repositories/tripulante_operational_periods.py` | `application/tripulante_operational_periods.py`; finance engines | `contracts/tripulantes.py` indiretamente |
| `bases` | `repositories/bases.py`; `repositories/queries.py` | `application/base_operations.py` | `contracts/bases.py` |

## 7. Tabelas financeiras

As tabelas financeiras sao as de maior risco de reorganizacao porque misturam contrato HTTP, calculo monetario, competencia, soft delete, auditoria, relatorios PDF e queries de jornada.

| Tabela | Produtor principal | Consumidores | Invariantes financeiros | Risco se mover/refatorar |
| --- | --- | --- | --- | --- |
| `financeiro_missoes_operacionais` | `db/schema.py`; `repositories/financeiro_missoes.py` | Rotas de missoes, jornada, competencias, relatorios e preflight | `competencia` `YYYY-MM`; status; soft delete; datas/horarios; tripulacao minima/distinta | Alto: pode duplicar/cancelar missoes, quebrar fechamento ou recalculo |
| `financeiro_missao_tripulantes` | `repositories/financeiro_missoes.py` | Jornada, produtividade, calculos e relatorios | Funcao `comandante`/`copiloto`; cobertura; status; unicidade por missao/tripulante | Alto: altera rateio, produtividade e elegibilidade |
| `financeiro_calculos_horarios` | `repositories/financeiro_calculos_horarios.py` | Jornada, bonificacao horaria, PDFs | Money/minutos nao negativos; status vigente; memoria de calculo | Alto: risco monetario direto e duplicidade de calculo vigente |
| `financeiro_calculos_produtividade` | `repositories/financeiro_calculos_produtividade.py` | Produtividade consolidada/geral/individual | Competencia, valores monetarios, memoria, status | Alto: risco monetario e divergencia de fechamento |
| `financeiro_competencias` | `repositories/financeiro_competencias.py` | Fechar/reabrir/recalcular/preflight | Status de fechamento e snapshot | Critico: pode liberar edicao indevida de competencia fechada |
| `financeiro_parametros` | `repositories/financeiro_parametros.py` | Engines horarios/produtividade, governanca | Vigencia sem sobreposicao, valor numeric 14,4, status | Critico: altera regra monetaria retroativa |
| `financeiro_feriados` | `repositories/financeiro_feriados.py` | Jornada, engines, relatorios | Data/tipo/localidade unico; status | Alto: altera calculo de horario especial |
| `financeiro_divergencias` | `repositories/financeiro_competencias.py`; `repositories/financeiro_observabilidade.py` | Preflight, observabilidade, fechamento | Severidade/status e entidade relacionada | Alto: pode ocultar bloqueios de fechamento |
| `pernoites_operacionais` | `repositories/operacoes.py` | Operacoes e produtividade | Tipo e quantidade | Alto: afeta adicional/pernoite |
| `equipamentos` | `repositories/catalogos.py` | Financeiro e treinamentos | Categoria financeira restrita | Alto: altera categoria de calculo |

Regra de evolucao permitida: nenhuma mudanca estrutural sem teste de contrato, teste repository, teste financeiro de regressao e validacao humana. Mudanca de campo, status, precisao, join, soft delete, ordem de filtro ou competencia exige versionamento ou gate especifico.

## 8. Tabelas de RBAC/sessao

| Tabela | Contrato congelado | Consumidores | Lacuna/gate |
| --- | --- | --- | --- |
| `usuarios` | Login, senha_hash, perfil, ativo, permissoes JSON | Auth routes, admin users, decorators de permissao, capabilities | Bloqueado ate session/RBAC/capabilities e endpoint-permission coverage passarem no gate |
| `auditoria_eventos` | `realizado_por` referencia usuario; before/after/contexto | Admin audit, financeiro audit, services sensiveis | Bloqueado porque logger generico nao basta para compliance |
| `request_error_events` | user_id, request_id, path, endpoint, metodo, status | Error handlers, monitoramento | Bloqueado ate erros 401/403/500 terem persistencia e diagnostico cobertos |

Arquivos principais:

- `backend/src/controle_treinamentos/blueprints/auth/routes.py`
- `backend/src/controle_treinamentos/repositories/user_repository.py`
- `backend/src/controle_treinamentos/blueprints/admin/routes.py`
- `backend/src/controle_treinamentos/core/audit_utils.py`
- `backend/src/controle_treinamentos/audit.py`
- `backend/src/controle_treinamentos/core/errors.py`

## 9. Tabelas de tripulantes/treinamentos

| Tabela | Papel | Risco principal | Gate |
| --- | --- | --- | --- |
| `tripulantes` | Cadastro base, foto, flags financeiras e vinculo piloto | Quebra de CPF unico, foto, status operacional ou elegibilidade financeira | Bloqueado |
| `pilotos` | Matricula/status/base | Dessincronizacao entre piloto e tripulante | Bloqueado |
| `historico_status_piloto` | Historico operacional | Perda de trilha de mudanca de base/status | Bloqueado |
| `treinamentos` | Registro individual e programa | Quebra de vencimentos, anexos, relatorios e notificacoes | Bloqueado |
| `tipos_treinamento` | Catalogo e periodicidade | Quebra de reentrada canonica e periodicidade | Bloqueado |
| `segmentos_teoricos` | Programa raiz teorico | Quebra de estrutura programa/segmento/equipamento | Bloqueado |
| `horas_voo_aeronave` | Programa raiz voo | Quebra de semantica de aeronave/modelo | Bloqueado |
| `treinamento_anexos_pdf` | Anexos PDF de treinamento | Perda de hash, status ou arquivo | Bloqueado |
| `tripulante_arquivos_pdf` | Documentos PDF de tripulante | Perda de controle ativo/substituido/removido | Bloqueado |
| `notificacoes_treinamento` | Gatilhos enviados | Reenvio indevido ou perda de historico de notificacao | Bloqueado |
| `tripulante_periodos_operacionais` | Periodos como ferias | Impacto em produtividade e disponibilidade | Bloqueado |

## 10. Tabelas de auditoria

| Tabela | Auditoria atual | Risco de reorganizacao | Mudanca permitida |
| --- | --- | --- | --- |
| `auditoria_eventos` | Persistencia via `audit.py:record_audit_event`, admin audit e financeiro observabilidade | Perder `before`, `after`, usuario, entidade ou contexto em operacao sensivel | Somente apos teste de contrato e validacao humana |
| `request_error_events` | Persistencia em `core/errors.py` com upsert por `request_id` | Quebrar diagnostico de request, monitoramento e correlacao | Somente apos teste de contrato HTTP/error |
| `financeiro_divergencias` | Divergencias de preflight/fechamento | Ocultar bloqueio financeiro | Somente apos teste financeiro e validacao humana |
| `historico_status_piloto` | Historico especifico de piloto/base | Perder trilha operacional | Somente apos teste de auditoria operacional |

## 11. Tabelas de backup/jobs

| Tabela | Produtor | Consumidor | Invariantes | Status |
| --- | --- | --- | --- | --- |
| `backups_execucoes` | `infra/backup.py:_record_backup_history` | `/backups`, `/monitoramento`, `list_backup_history` | Status sucesso/falha, artefatos, duracao, tamanho | Bloqueado |
| `background_jobs` | `infra/jobs.py:enqueue_background_job` e processador | `/jobs/<id>/reativar`, `/jobs/<id>/status`, monitoramento, backup job, notificacoes | Status de fila, idempotency_key, lock, attempts, requested_by | Bloqueado |
| `background_job_executions` | `infra/jobs.py:_create_execution_log/_finalize_execution_log` | Worker, monitoramento | FK cascade, attempt, status, erro, duracao | Bloqueado |
| `sistema_controle` | `cache.py`, `infra/mailer.py` | Cache residual, notificacao compat, monitoramento | Policy de chaves permitidas; uso generico proibido | Bloqueado |

Observacao: `infra/jobs.py:_cleanup_old_job_history` contem deletes operacionais de historico. Nao executar nem reorganizar sem ambiente isolado, teste de retencao e validacao humana.

## 12. Invariantes criticos

- `db/schema.py` e contrato vivo. Qualquer move/refactor que altere ordem de boot, import, tabela, indice, check ou FK fica bloqueado.
- `db/migrations.py` contem migracoes corretivas sensiveis para permissao de usuario, jobs, tripulantes financeiros, missoes, anexos PDF, soft delete, duplicidade de calculos e treinamento raiz.
- Competencia financeira deve permanecer no formato `YYYY-MM`.
- Valores monetarios e precisao financeira devem manter semantica `NUMERIC`, serializacao e memoria de calculo.
- Status financeiros congelados: missoes, participantes, competencias, parametros, feriados, calculos e divergencias.
- `financeiro_calculos_horarios` nao pode ter mais de um calculo vigente para mesma missao/tripulante/funcao.
- `financeiro_missoes_operacionais` usa soft delete e cancelamento. Delete fisico nao pode ser introduzido.
- `financeiro_missao_tripulantes.replace_missao_tripulantes` possui delete fisico de participantes e precisa de teste especifico antes de qualquer reorganizacao.
- `treinamentos` nao pode aceitar campos de programa sem `segmento_teorico_id`; treinamento de programa nao pode ter equipamento.
- `segmentos_teoricos` e `horas_voo_aeronave` dependem de cascade por tipo de treinamento.
- `tripulante_arquivos_pdf` exige hash e unicidade de hash ativo por tripulante.
- `treinamento_anexos_pdf` e `notificacoes_treinamento` dependem de cascade por treinamento.
- `usuarios.login` e `pilotos.matricula` sao unicos e usados como chaves operacionais.
- `usuarios.permissao_modulos_json` e `perfil` alimentam RBAC/capabilities e nao podem ser normalizados sem contrato.
- `sistema_controle` e residual; policy permite apenas cache legado e compatibilidade de notificacao.
- `background_jobs.idempotency_key` e locks de fila sao contratos operacionais.
- `request_error_events.request_id` e unico e suporta diagnostico de erro por request.
- `backups_execucoes` nao substitui artefato de backup; registra evidencia operacional.

## 13. Testes existentes por tabela

| Tabela(s) | Testes existentes encontrados |
| --- | --- |
| `usuarios` | `tests/unit/test_login_resilience.py`; `tests/unit/test_auth_permissions.py`; `tests/unit/test_auth_session_touch_policy.py`; `tests/unit/test_session_cookie_config.py`; `tests/unit/test_endpoint_permission_coverage.py`; `tests/contract/test_api_session_contract.py`; `tests/contract/test_session_lifecycle_contract.py` |
| `tripulantes` | `tests/contract/test_api_tripulantes_contract.py`; `tests/unit/test_tripulante_status_normalization.py`; `tests/unit/test_tripulante_operational_status_owner.py`; `tests/ops/test_sync_tripulantes_snapshot.py` |
| `tripulante_periodos_operacionais` | `tests/unit/test_tripulante_operational_periods.py` |
| `tripulante_arquivos_pdf` | `tests/contract/test_api_tripulante_media_contract.py`; `tests/integration/test_tripulante_file_routes_resilience.py`; `tests/integration/test_tripulante_file_repository.py`; `tests/unit/test_file_access_policy.py`; `tests/unit/test_document_repository_policy.py`; `tests/unit/test_document_storage_policy.py`; `tests/unit/test_media_storage.py` |
| `pilotos`, `historico_status_piloto`, `bases` | `tests/contract/test_bases_api_contract.py`; dashboard/base coverage indireta |
| `treinamentos` | `tests/contract/test_api_treinamentos_contract.py`; `tests/integration/test_treinamentos_ssr_routes.py`; `tests/unit/test_services_expiry.py`; `tests/unit/test_training_completeness_matrix.py` |
| `tipos_treinamento`, `segmentos_teoricos`, `horas_voo_aeronave` | `tests/contract/test_api_training_program_contract.py`; `tests/contract/test_training_root_release_gate.py`; `tests/contract/test_training_root_canonical_reentry.py`; `tests/unit/test_training_program_periodicity.py`; `tests/unit/test_training_aircraft_model_semantics.py`; `tests/unit/test_training_aircraft_model_rules.py` |
| `treinamento_anexos_pdf` | `tests/integration/test_training_pdf_attachments.py`; `tests/integration/test_treinamentos_ssr_attachments_exports.py`; `tests/architecture/test_ssr_treinamentos_attachments_exports_boundaries.py` |
| `notificacoes_treinamento`, `notificacoes_email`, `sistema_controle` | `tests/unit/test_mailer_notifications.py`; `tests/unit/test_notification_payload_cache_policy.py`; `tests/unit/test_sistema_controle_policy.py` |
| `auditoria_eventos` | `tests/unit/test_financeiro_audit_events.py`; `tests/unit/test_audit_utils_tripulante_payload.py`; `tests/unit/test_audit_hardening.py`; `tests/unit/test_business_audit_utils.py`; `tests/contract/test_financeiro_observabilidade_http.py` |
| `request_error_events` | `tests/unit/test_http_request_logging_policy.py`; `tests/contract/test_http_error_contract.py`; `tests/integration/test_error_diagnostics_persistence.py` |
| `backups_execucoes` | `tests/unit/test_backup_operation_lock.py`; `tests/ops/test_backup_integrity_guards.py`; `tests/unit/test_restore_validation.py` |
| `background_jobs`, `background_job_executions` | `tests/unit/test_jobs_queue.py`; `tests/integration/test_monitoring_snapshot.py` |
| `pernoites_operacionais` | `tests/contract/test_operacoes_contract.py`; `tests/architecture/test_operacoes_cutover_pernoites.py` |
| `financeiro_missoes_operacionais`, `financeiro_missao_tripulantes` | `tests/unit/test_financeiro_missoes_repository.py`; `tests/unit/test_financeiro_missoes_application.py`; `tests/integration/test_financeiro_missoes_repository_integration.py`; `tests/integration/test_financeiro_missoes_http.py`; `tests/contract/test_financeiro_missoes_preview_http.py`; `tests/contract/test_financeiro_missoes_recalculo_http.py` |
| `financeiro_calculos_horarios` | `tests/unit/test_financeiro_calculos_horarios_repository.py`; `tests/unit/test_financeiro_hourly_schema_precision.py`; `tests/unit/test_financeiro_bonificacao_horaria_engine.py`; `tests/contract/test_financeiro_bonificacoes_horaria_http.py` |
| `financeiro_calculos_produtividade` | `tests/unit/test_financeiro_calculos_produtividade_repository.py`; `tests/unit/test_financeiro_bonificacao_produtividade_engine.py`; `tests/unit/test_financeiro_produtividade_application.py`; `tests/contract/test_financeiro_bonificacoes_produtividade_http.py` |
| `financeiro_competencias` | `tests/unit/test_financeiro_competencias_repository.py`; `tests/unit/test_financeiro_competencias_application.py`; `tests/contract/test_financeiro_competencias_http.py` |
| `financeiro_parametros` | `tests/unit/test_financeiro_parametros_repository.py`; `tests/unit/test_financeiro_parametros_application.py`; `tests/unit/test_financeiro_parametros_governanca.py`; `tests/contract/test_financeiro_parametros_http.py` |
| `financeiro_feriados` | `tests/unit/test_financeiro_feriados_repository.py`; `tests/unit/test_financeiro_feriados_application.py`; `tests/contract/test_financeiro_feriados_http.py` |
| `financeiro_divergencias` | `tests/unit/test_financeiro_observabilidade_read_only.py`; `tests/contract/test_financeiro_observabilidade_http.py`; competencia/preflight tests |
| `equipamentos` | `tests/unit/test_equipamentos_schema.py`; `tests/integration/test_catalogos_ssr_routes.py`; `tests/architecture/test_ssr_catalogos_boundaries.py`; `tests/contract/test_api_equipamentos_options_contract.py` |

## 14. Lacunas de teste por tabela

| Tabela(s) | Lacuna |
| --- | --- |
| Todas | Testes existentes nao liberam reorganizacao se nao forem executados dentro deste gate. Baseline P0 anterior registrou decisao vermelha/bloqueada. |
| `usuarios` | Falta snapshot explicito tabela -> permissao -> endpoint para todos os consumidores SSR/API alem do endpoint-permission coverage. |
| `tripulantes` | Dependencias financeiras/documentais tornam delete/inativacao de alto risco; precisa teste integrado de bloqueio por dependencia. |
| `pilotos`, `historico_status_piloto` | Necessario teste de sincronizacao piloto/tripulante/base/historico apos reorganizacao. |
| `treinamentos`, `notificacoes_treinamento`, `treinamento_anexos_pdf` | Necessario teste de cascade, anexos, relatorios PDF/CSV e notificacoes no mesmo gate. |
| `tipos_treinamento`, `segmentos_teoricos`, `horas_voo_aeronave` | Necessario teste contract + repository para cascade de treinamento raiz e reentrada canonica. |
| `tripulante_arquivos_pdf` | Necessario teste de substituicao/remocao com hash ativo unico e download SSR/API. |
| `auditoria_eventos` | Logger generico nao e suficiente; cada operacao sensivel precisa before/after/ator/origem/request id validado. |
| `request_error_events` | Falta matriz completa de 401/403/404/500 por path/endpoint depois de reorganizacao. |
| `backups_execucoes` | Backup history depende de execucao operacional segura; nao ha liberacao sem ambiente isolado. |
| `background_jobs`, `background_job_executions` | Requeue, dead-letter, cleanup e lock precisam teste de retencao e idempotencia. |
| `sistema_controle` | Toda nova chave deve falhar pela policy; precisa snapshot contra ressurgimento de uso generico. |
| Financeiro | Necessario teste integrado de competencia fechada/reaberta, recalculo, parametros, feriados, missoes, participantes, calcs e PDFs antes de mover arquivos. |
| `pernoites_operacionais` | Necessario teste de impacto financeiro em produtividade/pernoite. |
| `notificacoes_email` | Sem contract dedicado de schema/rota; cobertura e parcial por mailer/admin. |

## 15. Bloqueios por tabela

| Tabela(s) | Bloqueio |
| --- | --- |
| `financeiro_*`, `pernoites_operacionais`, `equipamentos` | Bloqueio critico por financeiro sensivel, competencias, valores monetarios, relatorios e fechamento. |
| `usuarios`, `auditoria_eventos`, `request_error_events` | Bloqueio critico por sessao, RBAC, capabilities, auditoria e diagnostico de erro. |
| `tripulantes`, `pilotos`, `historico_status_piloto`, `bases` | Bloqueio por sincronizacao operacional, CPF/matricula, base/status e historico. |
| `treinamentos`, `tipos_treinamento`, `segmentos_teoricos`, `horas_voo_aeronave`, `notificacoes_treinamento` | Bloqueio por treinamento raiz, vencimentos, relatorios, notificacoes e cascade. |
| `treinamento_anexos_pdf`, `tripulante_arquivos_pdf` | Bloqueio por documentos, hashes, status, downloads, PDF e auditoria. |
| `backups_execucoes`, `background_jobs`, `background_job_executions`, `sistema_controle` | Bloqueio operacional por backup, fila, lock, dead-letter, cleanup e cache residual. |
| `notificacoes_email` | Bloqueio por notificacao operacional e configuracao residual. |

Decisao de bloqueio: nenhuma tabela critica pode ser movida, renomeada, ter repository reorganizado, query alterada, schema alterado ou contrato inferido como seguro sem execucao P0 verde, teste de contrato e validacao humana.

## 16. Proximo passo recomendado

Executar uma rodada P0 nao destrutiva em ambiente isolado, com foco em:

1. Contract tests HTTP/API/SSR para financeiro, RBAC, tripulantes, treinamentos, documentos, audit e jobs.
2. Repository tests por tabela critica, incluindo readers, writers, deleters, soft deletes, locks e cascades.
3. Snapshot table-map automatizado para detectar mudanca de SQL, rota, service, contract ou teste antes de qualquer reorganizacao.
4. Validacao humana de financeiro, auditoria, backup/jobs e documentos.

Ate essa rodada ficar verde, este mapa deve ser tratado como gate bloqueante e fonte de verdade para impedir reorganizacao fisica.
