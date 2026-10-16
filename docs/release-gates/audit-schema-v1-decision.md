# AUDIT-SCHEMA-V1 Decision

Data da deliberacao: 2026-06-07T15:26:16-03:00  
Status: PENDENTE  
Decisao: PENDENTE  
Escopo: deliberacao formal sobre `AUDIT-SCHEMA-V1`, sem aplicar migration, sem alterar banco real e sem executar operacoes sensiveis.

Este documento nao aprova migration, alteracao de schema, backfill, restore, backup real, cleanup, seed, repair, script operacional, endpoint destrutivo, reorganizacao fisica ou promocao de release.

## 1. Resumo executivo

`AUDIT-SCHEMA-V1` e tecnicamente necessario para completar a auditabilidade nativa de operacoes sensiveis. A remediacao sem schema ja melhorou a trilha via JSONB `audit_metadata`, mas permanece parcial para consultas de compliance, ator anonimo/tecnico, scripts, restore, cleanup, migration, seed, backup final, jobs e artefatos com checksum consultavel.

A decisao desta deliberacao e `PENDENTE`.

Justificativa:

- O plano e necessario e conceitualmente alinhado ao gate de auditabilidade.
- A migration ainda nao existe como artefato versionado aplicado/testado.
- O rollback ainda e diretriz futura, nao procedimento ensaiado.
- A baseline P0 consolidada esta `VERMELHA`.
- A validacao humana final esta `PENDENTE`.
- Nenhum risco foi aceito por owner humano.

Conclusao operacional: `AUDIT-SCHEMA-V1` nao esta aprovado para aplicacao. Operacoes sensiveis reais continuam bloqueadas. A reorganizacao fisica tambem permanece bloqueada pelo conjunto de gates aberto; a ausencia de decisao/aprovacao de `AUDIT-SCHEMA-V1` nao pode ser usada como excecao para avancar.

## 2. Fontes revisadas

- `docs/release-gates/auditability-schema-upgrade-plan.md`
- `docs/release-gates/auditability-remediation.md`
- `docs/release-gates/auditability-gate-register.md`
- `docs/release-gates/human-validation-register-final.md`
- `docs/release-gates/baseline-p0-consolidated-reexecution.md`

## 3. Plano AUDIT-SCHEMA-V1 avaliado

O plano propoe adicionar colunas nullable em `auditoria_eventos`, sem backfill obrigatorio na primeira etapa:

- `actor_kind`
- `actor_ref`
- `request_id`
- `correlation_id`
- `origin`
- `source_endpoint`
- `source_path`
- `http_method`
- `ip_address`
- `user_agent`
- `result`
- `success`
- `artifact_checksum`
- `artifact_name`
- `artifact_size_bytes`
- `script_name`
- `host`
- `audit_schema_version`

Indices propostos:

- `idx_auditoria_eventos_request_id`
- `idx_auditoria_eventos_correlation_id`
- `idx_auditoria_eventos_result`
- `idx_auditoria_eventos_origin`
- `idx_auditoria_eventos_artifact_checksum`

A estrategia proposta tambem exige migration idempotente, banco isolado, dual-write entre JSONB e colunas nativas, backfill controlado e testes de contrato antes de qualquer aplicacao real.

## 4. Classificacao da necessidade

| Pergunta | Decisao | Justificativa |
| --- | --- | --- |
| Obrigatorio antes da reorganizacao fisica? | Bloqueio atual: sim, como gate pendente; aplicacao automatica: nao | A migration nao deve ser aplicada automaticamente, mas tambem nao ha risco aceito para adiar o schema. Como baseline e validacao humana estao pendentes/vermelhas, a reorganizacao continua bloqueada. |
| Obrigatorio antes de operacoes sensiveis? | Sim | Restore, cleanup, migration, seed, repair, backup final, jobs criticos e scripts precisam ator tecnico/anonimo, origem, resultado e checksum nativos. |
| Pode ser adiado com risco aceito? | Nao nesta rodada | Nenhum owner humano aceitou risco, prazo, escopo ou compensacao. |
| Deve ser rejeitado? | Nao | O plano resolve lacunas reais e preserva abordagem aditiva/nullable. |
| Precisa de refinamento? | Sim | Falta migration versionada concreta, rollback ensaiavel, estrategia de mascaramento por coluna, testes completos e validacao humana. |

## 5. Lacunas que o plano resolve

- Ator anonimo/tecnico sem depender de FK obrigatoria para `usuarios`.
- Consulta nativa por `request_id` e `correlation_id`.
- Consulta nativa por origem, endpoint, path e metodo HTTP.
- Consulta nativa por resultado/sucesso/falha/bloqueio.
- Captura estruturada de IP e user-agent para requests HTTP.
- Captura estruturada de script, host e origem para operacoes nao HTTP.
- Checksum, nome e tamanho de artefatos para PDF, CSV, downloads, backups e restore.
- Ligacao mais forte entre auditoria, jobs, backups e artefatos externos.
- Base para compliance e investigacao sem varrer JSONB.

## 6. Lacunas que permanecem

Mesmo com `AUDIT-SCHEMA-V1`, permanecem pendentes:

- Migration versionada concreta ainda nao criada nesta deliberacao.
- Rollback da migration ainda nao ensaiado.
- Backfill real ainda nao planejado por lote, janela e owner.
- Politica de retencao e minimizacao de IP/user-agent ainda precisa decisao de Security/Compliance.
- Mascaramento de `actor_ref`, IP, user-agent, artifact name e script args precisa testes dedicados.
- Contratos de helper precisam garantir dual-write sem quebrar JSONB existente.
- Operacoes sensiveis ainda precisam testes por fluxo, nao apenas schema.
- Validacao humana de Security, Ops, Data/DB, QA, Release e Product segue pendente.

## 7. Impacto em schema/migrations

Impacto esperado:

- Alteracao aditiva em `auditoria_eventos`.
- Colunas nullable na primeira etapa.
- Indices novos para consultas de compliance.
- Sem remocao, rename ou alteracao de semantica das colunas existentes.
- Sem constraint adicional ate os testes e backfill serem validados.
- Dual-write obrigatorio para manter compatibilidade entre `payload_anterior`/`payload_novo` JSONB e campos nativos.

Regras para futura migration:

- Deve ser idempotente.
- Deve ser versionada em arquivo dedicado.
- Deve rodar primeiro em banco descartavel/isolado.
- Nao pode usar producao como ambiente de validacao.
- Nao pode executar backfill irreversivel sem plano proprio.
- Nao pode registrar senha, token, CPF completo, telefone completo, email completo, foto, arquivo bruto ou PDF bruto.

## 8. Impacto em backend/auditoria

Areas afetadas:

- `record_audit_event`
- `audit_event`
- `audit_document_generation`
- `audit_relevant_download`
- Helpers de mascaramento e normalizacao de payload.
- Eventos financeiros.
- Eventos RBAC/admin.
- Eventos de documentos, downloads e exports.

Impacto esperado:

- Helpers passam a preencher JSONB e colunas nativas em dual-write.
- Eventos existentes devem preservar contratos atuais.
- Mascaramento nao pode ser reduzido.
- `actor_kind` deve diferenciar `user`, `anonymous`, `system`, `script` e `job`.
- `actor_ref` deve ser sempre mascarado quando puder conter login/email/identificador sensivel.
- IP e user-agent devem ser tratados como dados pessoais operacionais e protegidos.
- `artifact_checksum` deve registrar hash, nunca conteudo bruto.

## 9. Impacto em jobs/scripts

Impacto esperado:

- Jobs de backup, notificacao, requeue/dead-letter e execucao final precisam evento mestre com origem, ator, resultado e correlation.
- Scripts de restore, cleanup, migration, repair, seed e bootstrap precisam envelope padrao de auditoria.
- Argumentos de script devem ser mascarados.
- `script_name`, `host`, `result`, `success` e checksums devem ser persistidos quando aplicavel.
- Dry-run, confirmacao e bloqueio devem ser auditaveis como resultado, nao apenas como stdout.

Status atual: nao liberado. Nenhum script operacional sensivel foi executado ou aprovado por esta decisao.

## 10. Impacto em financeiro/documentos/RBAC

### Financeiro

`AUDIT-SCHEMA-V1` e relevante para fechamento, reabertura, parametros, feriados, recalculo, relatorios, PDFs e missoes. A captura nativa de request/correlation/origem/resultado reduz risco de investigacao incompleta em operacoes monetarias.

Status: operacoes financeiras sensiveis continuam bloqueadas para mudanca estrutural ate testes e aceite funcional.

### Documentos/downloads

O plano melhora rastreabilidade de PDF, CSV, download relevante, preview quando aplicavel e artefatos por checksum/nome/tamanho. Conteudo bruto, foto e arquivo nao devem ser persistidos em auditoria.

Status: alteracoes em politica, rota, renderer, nome de arquivo, filtros ou payload continuam bloqueadas sem testes.

### RBAC/usuarios

O plano permite diferenciar ator usuario, anonimo, system, script e job. Tambem melhora auditoria de login/logout/falha, role change, permission change e desativacao.

Status: mudancas em usuarios/RBAC continuam bloqueadas sem eventos especificos, diff seguro e testes.

## 11. Testes necessarios

Antes de aprovar aplicacao de `AUDIT-SCHEMA-V1`, sao obrigatorios:

- Teste de contrato do schema de `auditoria_eventos`.
- Teste da migration idempotente em banco isolado.
- Teste de indices esperados.
- Testes unitarios de `record_audit_event` com dual-write JSONB + colunas nativas.
- Testes unitarios de `audit_event`.
- Testes unitarios de `audit_document_generation`.
- Testes unitarios de `audit_relevant_download`.
- Testes de mascaramento para senha, token, CPF, telefone, email, foto, arquivo bruto e PDF bruto.
- Testes auth para login, logout e falha anonima.
- Testes RBAC/admin para create/update/deactivate/role/permission.
- Testes financeiros para fechamento, reabertura, parametro, feriado, recalculo, relatorios e PDFs.
- Testes de documentos/downloads com checksum e policy.
- Testes de backup enqueue, execucao final, manifest e checksum.
- Testes de jobs requeue/dead-letter.
- Testes de restore dry-run em ambiente isolado.
- Testes de cleanup dry-run e confirmacao.
- Testes de migration/seed/repair com ator tecnico, script checksum e resultado.
- Reexecucao da baseline P0 consolidada segura apos implementacao.

## 12. Rollback necessario

`AUDIT-SCHEMA-V1` nao pode ser aprovado para aplicacao sem rollback especifico.

Rollback futuro minimo exigido:

- Migration reversivel ou estrategia de forward-fix documentada.
- Ensaio em banco descartavel.
- Evidencia antes/depois do schema.
- Validacao de que writes parciais nao corrompem `auditoria_eventos`.
- Plano para pausar operacoes sensiveis se a migration falhar.
- Preservacao de logs, dumps e evidencias.
- Proibicao de apagar `auditoria_eventos` como atalho de rollback.
- Plano de compatibilidade para codigo que faz dual-write.
- Aprovacao humana de Security, Ops, Data/DB, QA e Release antes de qualquer execucao real.

Nenhum rollback foi executado nesta deliberacao.

## 13. Decisao

Decisao: PENDENTE.

Motivos:

- Plano tecnicamente adequado como direcao, mas incompleto para aprovacao operacional.
- Rollback ainda nao esta ensaiado.
- Migration versionada concreta nao foi aplicada nem testada.
- Baseline P0 consolidada esta `VERMELHA`.
- Human validation final esta `PENDENTE`.
- Nenhum risco de adiamento foi aceito formalmente.

## 14. Riscos aceitos

Nenhum risco aceito.

Riscos observados, nao aceitos:

- Executar operacoes sensiveis sem ator tecnico/anonimo nativo.
- Depender apenas de JSONB para consultas de compliance.
- Nao conseguir correlacionar request, job, backup, artifact e auditoria.
- Registrar IP/user-agent sem politica de minimizacao e retencao.
- Aplicar migration sem rollback testado.
- Adiar schema sem owner, prazo e risco formal.
- Avancar reorganizacao com baseline vermelha e validacao humana pendente.

## 15. Operacoes que continuam bloqueadas

Continuam bloqueadas por esta decisao:

- Aplicacao real de `AUDIT-SCHEMA-V1`.
- Migration real.
- Backfill real.
- Restore real.
- Cleanup real.
- Repair real.
- Seed real.
- Bootstrap real.
- Backup real como validacao de release.
- Scripts operacionais sensiveis.
- Endpoints destrutivos.
- Operacoes de DB real/schema sem ambiente descartavel autorizado.
- Mudancas estruturais em financeiro, RBAC/usuarios, documentos/downloads, jobs, backup e auditoria.
- Reorganizacao fisica enquanto baseline/human validation/gates permanecerem bloqueados.

## 16. Proximo passo recomendado

1. Refinar `AUDIT-SCHEMA-V1` em uma proposta executavel com migration idempotente versionada, dual-write, testes e rollback.
2. Definir politica Security/Compliance para IP, user-agent, actor_ref, artifact metadata e retencao.
3. Criar ambiente descartavel de banco para ensaio de migration, rollback e testes de contrato.
4. Corrigir ou formalizar as falhas P0 remanescentes da baseline consolidada.
5. Coletar validacao humana real de Security, Ops, Data/DB, QA, Release, Product e Financeiro funcional.
6. Reavaliar a decisao somente depois de rollback testado, baseline aceitavel e risco formalmente aceito ou removido.
