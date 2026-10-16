# Auditability Schema Upgrade Plan

Data: 2026-06-06
Status: proposta versionada; nao aplicada.
Escopo: evolucao futura de `auditoria_eventos` e trilhas operacionais para
auditabilidade minima nativa.

## 1. Decisao

O schema atual de `auditoria_eventos` nao deve ser alterado nesta remediacao. A
correcao imediata usa `payload_anterior` e `payload_novo` JSONB para carregar
`audit_metadata` operacional sem migration.

Campos nativos continuam necessarios para liberar completamente operacoes
sensiveis, consultas de compliance, restore/cleanup/migration/seed e auditoria
anonima de falha de login.

## 2. Lacunas que exigem schema

- Falha de login sem usuario conhecido: `realizado_por` e `NOT NULL` com FK para
  `usuarios`; nao ha ator anonimo/tecnico nativo seguro.
- Consulta eficiente por `request_id`, `correlation_id`, IP, user-agent, origem,
  resultado e checksum sem varrer JSONB.
- Ligacao nativa entre `auditoria_eventos`, `backups_execucoes`,
  `background_jobs` e artefatos externos.
- Execucao de scripts operacionais sem request HTTP: restore, cleanup, repair,
  migration, seed e bootstrap precisam ator tecnico, host, comando mascarado,
  dry-run/confirmacao, resultado e checksums.
- Checksum e metadata de artefato precisam campos consultaveis para PDF, CSV,
  download, backup e restore.

## 3. Proposta AUDIT-SCHEMA-V1

Adicionar colunas nullable, sem backfill obrigatorio na primeira etapa:

- `actor_kind TEXT`: `user`, `anonymous`, `system`, `script`, `job`.
- `actor_ref TEXT`: login mascarado, service account ou identificador tecnico.
- `request_id TEXT`.
- `correlation_id TEXT`.
- `origin TEXT`.
- `source_endpoint TEXT`.
- `source_path TEXT`.
- `http_method TEXT`.
- `ip_address TEXT`.
- `user_agent TEXT`.
- `result TEXT`: `success`, `failure`, `blocked`, `requested`, `skipped`.
- `success BOOLEAN`.
- `artifact_checksum TEXT`.
- `artifact_name TEXT`.
- `artifact_size_bytes BIGINT`.
- `script_name TEXT`.
- `host TEXT`.
- `audit_schema_version TEXT DEFAULT 'audit-schema-v1'`.

Indices propostos:

- `idx_auditoria_eventos_request_id`.
- `idx_auditoria_eventos_correlation_id`.
- `idx_auditoria_eventos_result`.
- `idx_auditoria_eventos_origin`.
- `idx_auditoria_eventos_artifact_checksum`.

## 4. Estrategia de migracao futura

1. Criar migration idempotente em arquivo versionado dedicado.
2. Rodar somente em banco isolado autorizado.
3. Adicionar colunas nullable primeiro.
4. Manter dual-write: JSONB `audit_metadata` e colunas nativas.
5. Backfill controlado a partir de `payload_novo->audit_metadata` e
   `payload_anterior->audit_metadata`.
6. Adicionar testes de contrato para colunas e indices.
7. So depois avaliar constraints adicionais.

## 5. Testes obrigatorios antes de aplicar

- Unitarios de `record_audit_event` com JSONB e colunas nativas.
- Contrato de schema de `auditoria_eventos`.
- Login sucesso, logout e falha anonima com ator `anonymous`.
- RBAC/admin para role, permissao e desativacao.
- Financeiro para fechamento, reabertura, parametro, recalculo e relatorios.
- PDF/CSV/download com checksum.
- Backup enqueue, execucao final e manifest/checksum.
- Jobs requeue/dead-letter.
- Restore dry-run e restore real controlado em ambiente isolado.
- Cleanup dry-run, confirmacao e preservacao de auditoria.
- Migration/seed com checksum de script e ator tecnico.

## 6. Rollback futuro da migration

Rollback real nao deve ser automatico. Em caso de falha:

- Parar operacao sensivel.
- Preservar dump/log/evidencias.
- Validar se houve escrita parcial.
- Reverter somente em banco isolado ou janela aprovada.
- Nunca apagar `auditoria_eventos` sem evidencia externa imutavel.

## 7. Operacoes nao executadas

- Migration real: NAO EXECUTADA.
- Backfill real: NAO EXECUTADO.
- Restore real: NAO EXECUTADO.
- Cleanup real: NAO EXECUTADO.
- Seed real: NAO EXECUTADO.
- Banco real: NAO USADO.

## 8. Proximo passo

Manter esta proposta como dependencia para liberar operacoes bloqueadas. A
remediacao atual e suficiente apenas para desbloqueio parcial via JSONB e testes
nao destrutivos.
